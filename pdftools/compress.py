"""Compress a PDF to a target size with the best possible quality.

Steps (stops at the first one that meets the target):
  1. Lossless   : remove duplicate objects (e.g. the same image stored many times), subset fonts,
                  clean up content streams. Quality does not change at all.
  2. Images     : every image is resized (Lanczos) to exactly its displayed size at a given DPI and
                  stored as JPEG. A binary search picks the HIGHEST DPI/quality level that still fits.
                  Text and vector graphics are untouched, so they stay sharp.
  3. MRC        : only for pages with very heavy vector graphics (e.g. PowerPoint halftone dot
                  backgrounds): the background is rendered into one image, text stays vector on top.
  4. Aggressive : (if allowed) images go down to 72 DPI.
  5. Split      : (optional, outside this module: pdftools.core.split_by_size) if it still doesn't fit.

1-bit black-and-white images (text scans, already tiny with FAX/JBIG2) are left alone.
Every attempt runs in a separate process: it can be timed out, and a broken PDF cannot crash the server.

CLI:
  python -m pdftools.compress compress in.pdf out.pdf --target-mb 10 [--gray] [--aggressive]
"""

from __future__ import annotations

import argparse
import io
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

import pymupdf
from PIL import Image

try:  # imported as part of the package (app) ...
    from .i18n import tr
except ImportError:  # ... or run directly as the worker script
    from i18n import tr  # type: ignore

# (DPI, JPEG quality) from highest to lowest quality. 100 DPI is still comfortable to read on screen.
LEVELS: list[tuple[int, int]] = [(200, 85), (170, 80), (150, 75), (130, 70), (115, 65), (100, 60)]
# Below 100 DPI only when allowed. Vector text stays sharp; photos/screenshots get softer.
AGGRESSIVE_LEVELS: list[tuple[int, int]] = [(90, 50), (80, 50), (72, 50), (72, 40)]

MRC_MIN_VECTOR_BYTES = 250_000  # pages with this much vector data or more are MRC candidates
MRC_MIN_DPI = 100  # MRC page backgrounds are never rendered below this

# progress(i18n_key, fraction, **params); the caller translates the key (see pdftools.i18n)
ProgressFn = Callable[..., None]

ORIGINAL_LABEL = "Original"  # shown in the UI via the i18n key "label_original"


@dataclass
class Analysis:
    pages: int
    file_size: int
    image_count: int
    image_bytes: int
    scanned_pages_sampled: int
    sampled_pages: int
    heavy_vector_pages: int
    encrypted: bool

    @property
    def image_share(self) -> float:
        return self.image_bytes / self.file_size if self.file_size else 0.0

    @property
    def looks_scanned(self) -> bool:
        return self.sampled_pages > 0 and self.scanned_pages_sampled / self.sampled_pages >= 0.6


@dataclass
class Attempt:
    label: str
    size: int
    path: str
    dpi: Optional[int] = None
    quality: Optional[int] = None
    mrc: bool = False
    seconds: float = 0.0


@dataclass
class Result:
    original_size: int
    target_size: int
    best: Attempt
    attempts: list[Attempt] = field(default_factory=list)
    met_target: bool = False
    kept_original: bool = False


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------
def _key(doc: pymupdf.Document, xref: int, name: str) -> str:
    return doc.xref_get_key(xref, name)[1]


def _vector_bytes(doc: pymupdf.Document, page: pymupdf.Page) -> int:
    """Size of the page content streams + every Form XObject it uses (recursively)."""
    total = sum(len(doc.xref_stream_raw(c) or b"") for c in page.get_contents())
    stack = [x[0] for x in page.get_xobjects()]
    seen: set[int] = set()
    while stack:
        xref = stack.pop()
        if xref in seen or _key(doc, xref, "Subtype") != "/Form":
            continue
        seen.add(xref)
        total += len(doc.xref_stream_raw(xref) or b"")
        sub = doc.xref_get_key(xref, "Resources/XObject")
        if sub[0] == "dict":
            stack += [int(r) for r in re.findall(r"(\d+) 0 R", sub[1])]
    return total


def analyze(path: str, sample_pages: int = 20) -> Analysis:
    size = os.path.getsize(path)
    doc = pymupdf.open(path)
    try:
        if doc.needs_pass:
            return Analysis(doc.page_count, size, 0, 0, 0, 0, 0, True)
        xrefs: set[int] = set()
        img_bytes = 0
        heavy = 0
        for page in doc:
            for img in page.get_images(full=True):
                if img[0] in xrefs:
                    continue
                xrefs.add(img[0])
                length = doc.xref_get_key(img[0], "Length")
                if length[0] == "int":
                    img_bytes += int(length[1])
            if _vector_bytes(doc, page) >= MRC_MIN_VECTOR_BYTES:
                heavy += 1
        step = max(1, doc.page_count // sample_pages)
        sampled = scanned = 0
        for pno in range(0, doc.page_count, step):
            page = doc[pno]
            sampled += 1
            if not page.get_text("text").strip() and page.get_images():
                scanned += 1
        return Analysis(doc.page_count, size, len(xrefs), img_bytes, scanned, sampled, heavy, False)
    finally:
        doc.close()


# ---------------------------------------------------------------------------
# Operations (run inside the worker process)
# ---------------------------------------------------------------------------
def _save(doc: pymupdf.Document, out_path: str) -> None:
    doc.save(
        out_path,
        garbage=4,  # includes removing duplicate objects
        deflate=True,
        deflate_images=True,
        deflate_fonts=True,
        use_objstms=1,
        clean=True,  # clean up content streams (appearance unchanged)
        compression_effort=100,  # maximum zlib level for text, vectors, fonts
    )


def _lossless(in_path: str, out_path: str) -> None:
    doc = pymupdf.open(in_path)
    try:
        try:
            doc.subset_fonts()
        except Exception:
            pass  # font subsetting fails on some PDFs; continue without it
        doc.scrub(
            attached_files=False, clean_pages=False, embedded_files=False, hidden_text=False,
            javascript=False, metadata=False, redactions=False, redact_images=0,
            remove_links=False, reset_fields=False, reset_responses=False,
            thumbnails=True, xml_metadata=False,
        )
        _save(doc, out_path)
    finally:
        doc.close()


def _display_sizes(doc: pymupdf.Document) -> dict[int, tuple[float, float]]:
    """Largest displayed size (points) of every image, across all places where it is used."""
    sizes: dict[int, tuple[float, float]] = {}
    for page in doc:
        for info in page.get_image_info(xrefs=True):
            xref = info.get("xref") or 0
            if not xref:
                continue  # inline image, left alone
            a, b, c, d, _, _ = info["transform"]
            w, h = math.hypot(a, b), math.hypot(c, d)
            ow, oh = sizes.get(xref, (0.0, 0.0))
            sizes[xref] = (max(ow, w), max(oh, h))
    return sizes


def _pix_to_pil(pix: pymupdf.Pixmap, gray: bool) -> Image.Image:
    if pix.alpha:
        pix = pymupdf.Pixmap(pix, 0)  # transparency lives in a separate SMask
    if pix.colorspace is None or pix.colorspace.n not in (1, 3):
        pix = pymupdf.Pixmap(pymupdf.csRGB, pix)  # CMYK / Lab / etc. -> RGB
    if gray and pix.colorspace.n == 3:
        pix = pymupdf.Pixmap(pymupdf.csGRAY, pix)
    mode = "L" if pix.colorspace.n == 1 else "RGB"
    return Image.frombytes(mode, (pix.width, pix.height), pix.samples)


def _jpeg(img: Image.Image, quality: int) -> bytes:
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=quality, optimize=True, progressive=True, subsampling=2)
    return buf.getvalue()


def _set_jpeg_image(doc: pymupdf.Document, xref: int, data: bytes, w: int, h: int, gray: bool) -> None:
    doc.update_stream(xref, data, compress=False)
    for key, val in (
        ("Filter", "/DCTDecode"), ("DecodeParms", "null"), ("Decode", "null"),
        ("Width", str(w)), ("Height", str(h)), ("BitsPerComponent", "8"),
        ("ColorSpace", "/DeviceGray" if gray else "/DeviceRGB"),
    ):
        doc.xref_set_key(xref, key, val)


def _rewrite_images(doc: pymupdf.Document, dpi: int, quality: int, gray: bool) -> None:
    sizes = _display_sizes(doc)
    smasks = set()
    for xref in sizes:
        v = doc.xref_get_key(xref, "SMask")
        if v[0] == "xref":
            smasks.add(int(v[1].split()[0]))
    for xref, (wpt, hpt) in sizes.items():
        if xref in smasks:
            continue
        if _key(doc, xref, "ImageMask") == "true" or _key(doc, xref, "BitsPerComponent") == "1":
            continue
        try:
            width, height = int(_key(doc, xref, "Width")), int(_key(doc, xref, "Height"))
        except ValueError:
            continue
        scale = min(1.0, max(wpt / 72 * dpi / width, hpt / 72 * dpi / height))
        new_w, new_h = max(1, round(width * scale)), max(1, round(height * scale))
        resized = (new_w, new_h) != (width, height)
        old_len = len(doc.xref_stream_raw(xref) or b"")
        try:
            img = _pix_to_pil(pymupdf.Pixmap(doc, xref), gray)
        except Exception:
            continue  # unreadable image format: leave it
        if resized:
            img = img.resize((new_w, new_h), Image.LANCZOS)
        data = _jpeg(img, quality)
        if len(data) >= old_len and not resized:
            continue  # not smaller: keep the original image
        _set_jpeg_image(doc, xref, data, new_w, new_h, img.mode == "L")

        # SMask: drop it if fully opaque, otherwise resize it to match
        v = doc.xref_get_key(xref, "SMask")
        if v[0] != "xref":
            continue
        sx = int(v[1].split()[0])
        try:
            mpix = pymupdf.Pixmap(doc, sx)
            mask = Image.frombytes("L", (mpix.width, mpix.height), mpix.samples[: mpix.width * mpix.height])
            if mask.getextrema()[0] == 255:
                doc.xref_set_key(xref, "SMask", "null")
                continue
            if not resized:
                continue
            mask = mask.resize((new_w, new_h), Image.LANCZOS)
            # soft (anti-aliased) mask: JPEG at a higher quality than the image itself
            _set_jpeg_image(doc, sx, _jpeg(mask, min(92, quality + 20)), new_w, new_h, True)
        except Exception:
            pass  # the PDF stays valid even if mask and image sizes differ


def _mrc_page(doc: pymupdf.Document, pno: int, dpi: int, quality: int, gray: bool) -> bool:
    """Mixed Raster Content: the background (images + vectors, no text) becomes one JPEG and the
    original text stays vector on top. The page object is kept, so links/bookmarks/annotations stay valid."""
    page = doc[pno]
    if page.rotation:
        return False  # rotated page: rare, leave it alone to be safe
    rect = page.rect

    bg = pymupdf.open()
    bg.insert_pdf(doc, from_page=pno, to_page=pno, links=False, annots=False)
    bp = bg[0]
    bp.add_redact_annot(bp.rect, fill=False)
    bp.apply_redactions(
        images=pymupdf.PDF_REDACT_IMAGE_NONE,
        graphics=pymupdf.PDF_REDACT_LINE_ART_NONE,
        text=pymupdf.PDF_REDACT_TEXT_REMOVE,
    )
    bg_jpeg = _jpeg(_pix_to_pil(bp.get_pixmap(dpi=dpi, annots=False), gray), quality)

    tx = pymupdf.open()
    tx.insert_pdf(doc, from_page=pno, to_page=pno, links=False, annots=False)
    tp = tx[0]
    tp.add_redact_annot(tp.rect, fill=False)
    tp.apply_redactions(
        images=pymupdf.PDF_REDACT_IMAGE_REMOVE,
        graphics=pymupdf.PDF_REDACT_LINE_ART_REMOVE_IF_TOUCHED,
        text=pymupdf.PDF_REDACT_TEXT_NONE,
    )

    empty = doc.get_new_xref()
    doc.update_object(empty, "<<>>")
    doc.update_stream(empty, b" ")
    doc.xref_set_key(page.xref, "Contents", f"{empty} 0 R")
    doc.xref_set_key(page.xref, "Resources", "<<>>")
    page = doc[pno]
    page.insert_image(rect, stream=bg_jpeg)
    page.show_pdf_page(rect, tx, 0)
    bg.close()
    tx.close()
    return True


def _rewrite(in_path: str, out_path: str, dpi: int, quality: int, gray: bool, mrc: bool) -> None:
    doc = pymupdf.open(in_path)
    try:
        _rewrite_images(doc, dpi, quality, gray)
        if mrc:
            for page in doc:
                if _vector_bytes(doc, page) >= MRC_MIN_VECTOR_BYTES:
                    _mrc_page(doc, page.number, max(dpi, MRC_MIN_DPI), quality, gray)
        _save(doc, out_path)
    finally:
        doc.close()


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------
def _run_worker(args: list[str], timeout: int) -> None:
    """One attempt in a separate process (can be timed out; a crash does not spread)."""
    cmd = [sys.executable, os.path.abspath(__file__), *args]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if proc.returncode != 0:
        msg = (proc.stderr or proc.stdout).strip().splitlines()
        raise RuntimeError(msg[-1] if msg else f"compression process failed (exit code {proc.returncode})")


def compress_to_target(
    in_path: str,
    target_bytes: int,
    workdir: str,
    gray: bool = False,
    aggressive: bool = False,
    progress: Optional[ProgressFn] = None,
    timeout: Optional[int] = None,
    analysis: Optional[Analysis] = None,
) -> Result:
    say = progress or (lambda key, frac, **kw: None)
    original = os.path.getsize(in_path)
    if timeout is None:
        timeout = int(min(1200, max(120, original / 1e6 * 3)))  # per attempt
    info = analysis or analyze(in_path)
    attempts: list[Attempt] = []

    def run(label: str, args: list[str], out: str, **kw) -> Attempt:
        t0 = time.monotonic()
        _run_worker(args, timeout)
        a = Attempt(label, os.path.getsize(out), out, seconds=time.monotonic() - t0, **kw)
        attempts.append(a)
        return a

    say("progress_lossless", 0.03)
    base = os.path.join(workdir, "lossless.pdf")
    lossless = run("Lossless", ["lossless", in_path, base], base)
    if not gray and lossless.size <= target_bytes:
        return _finish(original, target_bytes, attempts, lossless, in_path)

    phases: list[tuple[bool, list[tuple[int, int]]]] = [(False, LEVELS)]
    if info.heavy_vector_pages:
        phases.append((True, LEVELS + (AGGRESSIVE_LEVELS if aggressive else [])))
    elif aggressive:
        phases.append((False, AGGRESSIVE_LEVELS))

    est_steps = sum(max(1, len(l).bit_length()) for _, l in phases)
    step = 0
    for mrc, ladder in phases:
        lo, hi = 0, len(ladder) - 1
        fits: dict[int, Attempt] = {}
        while lo <= hi:
            mid = (lo + hi) // 2
            dpi, q = ladder[mid]
            step += 1
            label = f"{dpi} DPI, JPEG {q}" + (" + MRC" if mrc else "")
            say("progress_attempt", min(0.95, 0.08 + 0.87 * step / (est_steps + 1)), step=step, label=label)
            out = os.path.join(workdir, f"try_{dpi}_{q}_{int(mrc)}.pdf")
            a = run(label, ["attempt", base, out, str(dpi), str(q), str(int(gray)), str(int(mrc))],
                    out, dpi=dpi, quality=q, mrc=mrc)
            if a.size <= target_bytes:
                fits[mid] = a
                hi = mid - 1  # fits: try a higher quality
            else:
                lo = mid + 1  # doesn't fit: go lower
        if fits:
            return _finish(original, target_bytes, attempts, fits[min(fits)], in_path)

    return _finish(original, target_bytes, attempts, min(attempts, key=lambda x: x.size), in_path)


def _finish(original: int, target: int, attempts: list[Attempt], best: Attempt, in_path: str) -> Result:
    if best.size >= original:
        orig = Attempt(ORIGINAL_LABEL, original, in_path)
        return Result(original, target, orig, attempts, original <= target, kept_original=True)
    return Result(original, target, best, attempts, best.size <= target)


def pick_preview_page(path: str) -> int:
    """The page most affected by compression: the one holding the largest image."""
    doc = pymupdf.open(path)
    try:
        best_size, best_page = -1, 0
        for page in doc:
            for img in page.get_images():
                length = doc.xref_get_key(img[0], "Length")
                size = int(length[1]) if length[0] == "int" else 0
                if size > best_size:
                    best_size, best_page = size, page.number
        return best_page
    finally:
        doc.close()


def render_preview(path: str, page_no: int, dpi: int = 110) -> bytes:
    doc = pymupdf.open(path)
    try:
        page = doc[min(max(page_no, 0), doc.page_count - 1)]
        return page.get_pixmap(dpi=dpi).tobytes("png")
    finally:
        doc.close()


def make_workdir() -> str:
    """Temporary work folder; can be redirected with the PDFTOOLS_TMP environment variable."""
    return tempfile.mkdtemp(prefix="pdftools_", dir=os.environ.get("PDFTOOLS_TMP") or None)


def cleanup(path: str) -> None:
    shutil.rmtree(path, ignore_errors=True)


# ---------------------------------------------------------------------------
# CLI / worker
# ---------------------------------------------------------------------------
def _main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Compress a PDF to a target size")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("lossless")
    s.add_argument("inp"); s.add_argument("out")
    s = sub.add_parser("attempt")
    s.add_argument("inp"); s.add_argument("out")
    s.add_argument("dpi", type=int); s.add_argument("quality", type=int)
    s.add_argument("gray", type=int); s.add_argument("mrc", type=int)
    s = sub.add_parser("compress")
    s.add_argument("inp"); s.add_argument("out")
    s.add_argument("--target-mb", type=float, default=10)
    s.add_argument("--gray", action="store_true")
    s.add_argument("--aggressive", action="store_true")
    a = p.parse_args(argv)

    if a.cmd == "lossless":
        _lossless(a.inp, a.out)
    elif a.cmd == "attempt":
        _rewrite(a.inp, a.out, a.dpi, a.quality, bool(a.gray), bool(a.mrc))
    else:
        info = analyze(a.inp)
        print(f"{info.pages} pages, {info.file_size / 1e6:.1f} MB, {info.image_count} images "
              f"({info.image_share:.0%}), heavy vector pages: {info.heavy_vector_pages}, scanned={info.looks_scanned}")
        if info.encrypted:
            print("The PDF is password-protected.")
            return 2
        work = make_workdir()
        try:
            r = compress_to_target(a.inp, int(a.target_mb * 1e6), work, a.gray, a.aggressive,
                                   progress=lambda key, f, **kw: print(f"  [{f:4.0%}] {tr(key, 'en', **kw)}", flush=True), analysis=info)
            for t in r.attempts:
                print(f"  - {t.label:24s} {t.size / 1e6:8.2f} MB  {t.seconds:6.1f} s")
            shutil.copyfile(r.best.path, a.out)
            print(f"Result: {r.best.label}, {r.best.size / 1e6:.2f} MB "
                  f"({'meets' if r.met_target else 'does NOT meet'} the {a.target_mb} MB target)")
        finally:
            cleanup(work)
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
