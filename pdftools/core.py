"""PDF operations (no Streamlit). Every function takes file paths and writes to an output path."""

from __future__ import annotations

import io
import os
import re
import secrets
import zipfile
from dataclasses import dataclass
from typing import Callable, Iterable, Optional

import pymupdf
from PIL import Image, ImageOps

from .i18n import UserError

# Pixel limit for uploaded images (protects the server against "decompression bombs")
Image.MAX_IMAGE_PIXELS = int(os.environ.get("PDFTOOLS_MAX_IMAGE_PIXELS", 200_000_000))

MM = 72 / 25.4  # 1 mm in points
# id -> page size in points (None = use the image's own size). Labels live in i18n ("paper_<id>").
PAPER_SIZES: dict[str, Optional[tuple[float, float]]] = {
    "original": None,
    "a4": (595.28, 841.89),
    "f4": (215 * MM, 330 * MM),
    "letter": (612.0, 792.0),
    "legal": (612.0, 1008.0),
}


class InvalidInput(UserError):
    """Invalid user input; the message is safe to show."""


class PdfLocked(UserError):
    """The PDF is password-protected (or the password is wrong)."""


# ---------------------------------------------------------------------------
# General
# ---------------------------------------------------------------------------
def is_pdf(path: str) -> bool:
    with open(path, "rb") as f:
        return b"%PDF-" in f.read(1024)


def open_pdf(path: str, password: Optional[str] = None) -> pymupdf.Document:
    if not is_pdf(path):
        raise InvalidInput("not_pdf")
    try:
        doc = pymupdf.open(path)
    except Exception as e:
        raise InvalidInput("pdf_corrupt") from e
    if doc.needs_pass:
        if not password or not doc.authenticate(password):
            doc.close()
            raise PdfLocked("pdf_locked")
    return doc


def save(doc: pymupdf.Document, out: str, **kw) -> None:
    doc.save(out, garbage=3, deflate=True, use_objstms=1, **kw)


def parse_pages(spec: str, page_count: int) -> list[int]:
    """'1-3, 5, 8-' -> [0,1,2,4,7,8,...] (0-based). Order and duplicates are kept (used for reordering)."""
    spec = (spec or "").strip().lower().replace(" ", "")
    if not spec or spec in ("all", "semua"):
        return list(range(page_count))
    pages: list[int] = []
    for part in spec.split(","):
        if not part:
            continue
        m = re.fullmatch(r"(\d*)-(\d*)|(\d+)", part)
        if not m:
            raise InvalidInput("bad_page_format", part=part)
        if m.group(3):
            a = b = int(m.group(3))
        else:
            a = int(m.group(1)) if m.group(1) else 1
            b = int(m.group(2)) if m.group(2) else page_count
        if a < 1 or b < 1 or a > page_count or b > page_count:
            raise InvalidInput("page_out_of_range", part=part, n=page_count)
        step = 1 if b >= a else -1
        pages.extend(p - 1 for p in range(a, b + step, step))
    if not pages:
        raise InvalidInput("no_pages_selected")
    return pages


def parse_groups(spec: str, page_count: int) -> list[list[int]]:
    """'1-3; 4-6; 7-' -> several page groups (for splitting by range)."""
    groups = [parse_pages(g, page_count) for g in re.split(r"[;\n]+", spec or "") if g.strip()]
    if not groups:
        raise InvalidInput("no_ranges")
    return groups


def zip_files(files: list[str], out_zip: str) -> None:
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_STORED) as z:  # PDF/JPG are already compressed
        for f in files:
            z.write(f, os.path.basename(f))


# ---------------------------------------------------------------------------
# Merge & split
# ---------------------------------------------------------------------------
def merge(paths: list[str], names: list[str], out: str, bookmark_per_file: bool = True) -> int:
    """Merge PDFs in the given order. Original bookmarks are kept; optionally one bookmark per file."""
    result = pymupdf.open()
    toc: list[list] = []
    for path, name in zip(paths, names):
        src = open_pdf(path)
        start = result.page_count
        result.insert_pdf(src)
        if bookmark_per_file:
            toc.append([1, os.path.splitext(name)[0], start + 1])
        for level, title, page, *_ in src.get_toc(simple=False):
            if page > 0:
                toc.append([level + (1 if bookmark_per_file else 0), title, page + start])
        src.close()
    try:
        result.set_toc(toc)
    except Exception:
        pass  # broken bookmarks in one input: the pages are still merged
    save(result, out)
    n = result.page_count
    result.close()
    return n


def _write_pages(src: pymupdf.Document, pages: list[int], out: str) -> None:
    part = pymupdf.open()
    for p in pages:
        part.insert_pdf(src, from_page=p, to_page=p)
    save(part, out)
    part.close()


def split_groups(path: str, groups: list[list[int]], out_dir: str, base: str) -> list[str]:
    src = open_pdf(path)
    outs = []
    width = len(str(len(groups)))
    for i, pages in enumerate(groups, 1):
        out = os.path.join(out_dir, f"{base}_part_{i:0{width}d}.pdf")
        _write_pages(src, pages, out)
        outs.append(out)
    src.close()
    return outs


def split_every(path: str, n: int, out_dir: str, base: str) -> list[str]:
    if n < 1:
        raise InvalidInput("pages_per_file_min")
    src = open_pdf(path)
    total = src.page_count
    if n == 1:
        width = len(str(total))
        outs = []
        for p in range(total):
            out = os.path.join(out_dir, f"{base}_page_{p + 1:0{width}d}.pdf")
            _write_pages(src, [p], out)
            outs.append(out)
        src.close()
        return outs
    src.close()
    groups = [list(range(i, min(i + n, total))) for i in range(0, total, n)]
    return split_groups(path, groups, out_dir, base)


def split_by_size(path: str, max_bytes: int, out_dir: str, base: str) -> tuple[list[str], list[int]]:
    """Split into files that are each <= max_bytes where possible.

    Returns (output files, 1-based page numbers that exceed max_bytes even on their own).
    """
    src = open_pdf(path)
    n = src.page_count

    def build(a: int, b: int) -> bytes:
        part = pymupdf.open()
        part.insert_pdf(src, from_page=a, to_page=b)
        data = part.tobytes(garbage=4, deflate=True, use_objstms=1)
        part.close()
        return data

    parts: list[bytes] = []
    oversize: list[int] = []
    start = 0
    while start < n:
        data = build(start, start)
        if len(data) > max_bytes:
            parts.append(data)
            oversize.append(start + 1)
            start += 1
            continue
        good_end, good = start, data
        step = 1
        bad = n  # smallest end page known NOT to fit
        # gallop (1, 2, 4, ...) then narrow down (binary search)
        while good_end + 1 < bad:
            cand = min(good_end + step, bad - 1, n - 1)
            if cand <= good_end:
                break
            d = build(start, cand)
            if len(d) <= max_bytes:
                good_end, good = cand, d
                step *= 2
            else:
                bad = cand
                step = max(1, (bad - good_end) // 2)
        parts.append(good)
        start = good_end + 1
    src.close()

    width = len(str(len(parts)))
    outs = []
    for i, data in enumerate(parts, 1):
        out = os.path.join(out_dir, f"{base}_part_{i:0{width}d}.pdf")
        with open(out, "wb") as f:
            f.write(data)
        outs.append(out)
    return outs, oversize


# ---------------------------------------------------------------------------
# Organize pages
# ---------------------------------------------------------------------------
def reorganize(path: str, out: str, order_spec: str, rotate_spec: str = "", rotate_angle: int = 0) -> int:
    """Select / reorder / delete pages (order_spec), then rotate given pages (rotate_spec, numbered as
    in the RESULT). Example: order '3,1-2,5-'; rotate '1,4' by 90."""
    doc = open_pdf(path)
    order = parse_pages(order_spec, doc.page_count)
    doc.select(order)
    if rotate_spec.strip() and rotate_angle % 360:
        for p in parse_pages(rotate_spec, doc.page_count):
            page = doc[p]
            page.set_rotation((page.rotation + rotate_angle) % 360)
    save(doc, out)
    n = doc.page_count
    doc.close()
    return n


def thumbnails(path: str, max_pages: int = 60, width_px: int = 160) -> list[bytes]:
    doc = open_pdf(path)
    out = []
    for page in doc.pages(0, min(doc.page_count, max_pages)):
        zoom = width_px / page.rect.width
        out.append(page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom)).tobytes("png"))
    doc.close()
    return out


# ---------------------------------------------------------------------------
# Security: unlock, protect, metadata, redact
# ---------------------------------------------------------------------------
def unlock(path: str, password: str, out: str) -> bool:
    """Remove the password (requires the correct one). Returns False if the PDF wasn't locked."""
    if not is_pdf(path):
        raise InvalidInput("not_pdf")
    doc = pymupdf.open(path)
    was_locked = doc.needs_pass or doc.is_encrypted
    if doc.needs_pass and not doc.authenticate(password or ""):
        doc.close()
        raise PdfLocked("wrong_password")
    save(doc, out, encryption=pymupdf.PDF_ENCRYPT_NONE)
    doc.close()
    return bool(was_locked)


def protect(
    path: str, out: str, user_pw: str, owner_pw: str = "",
    allow_print: bool = True, allow_copy: bool = False, allow_edit: bool = False,
) -> None:
    """Encrypt with AES-256. Without an owner password a random one is used, so the permissions
    cannot be lifted by someone who only knows the user password."""
    if not user_pw:
        raise InvalidInput("password_required")
    doc = open_pdf(path)
    perm = pymupdf.PDF_PERM_ACCESSIBILITY
    if allow_print:
        perm |= pymupdf.PDF_PERM_PRINT | pymupdf.PDF_PERM_PRINT_HQ
    if allow_copy:
        perm |= pymupdf.PDF_PERM_COPY
    if allow_edit:
        perm |= pymupdf.PDF_PERM_MODIFY | pymupdf.PDF_PERM_ANNOTATE | pymupdf.PDF_PERM_FORM | pymupdf.PDF_PERM_ASSEMBLE
    save(
        doc, out,
        encryption=pymupdf.PDF_ENCRYPT_AES_256,
        user_pw=user_pw,
        owner_pw=owner_pw or secrets.token_urlsafe(24),
        permissions=perm,
    )
    doc.close()


META_FIELDS = ["title", "author", "subject", "keywords", "creator", "producer"]


def read_metadata(path: str) -> tuple[dict[str, str], bool]:
    """Return (Info dictionary metadata, whether XMP metadata exists)."""
    doc = open_pdf(path)
    meta = {k: (doc.metadata or {}).get(k) or "" for k in META_FIELDS}
    has_xmp = bool(doc.get_xml_metadata().strip())
    doc.close()
    return meta, has_xmp


def write_metadata(path: str, out: str, meta: dict[str, str], strip_all: bool = False) -> None:
    """Write new metadata. Old XMP is always removed (many viewers prefer it over the Info dictionary).
    strip_all=True: clear all metadata and remove thumbnails / hidden attachments / JavaScript."""
    doc = open_pdf(path)
    doc.del_xml_metadata()
    if strip_all:
        doc.set_metadata({})
        doc.scrub(
            attached_files=True, clean_pages=False, embedded_files=True, hidden_text=False,
            javascript=True, metadata=True, redactions=False, redact_images=0,
            remove_links=False, reset_fields=False, reset_responses=True,
            thumbnails=True, xml_metadata=True,
        )
    else:
        doc.set_metadata({k: meta.get(k, "") for k in META_FIELDS})
    save(doc, out)
    doc.close()


# id -> regex. Labels live in i18n ("preset_<id>").
REDACT_PRESETS: dict[str, str] = {
    "nik": r"(?<!\d)\d{16}(?!\d)",
    "npwp": r"(?<!\d)\d{2}\.\d{3}\.\d{3}\.\d-\d{3}\.\d{3}(?!\d)|(?<!\d)\d{15,16}(?!\d)",
    "email": r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    "phone": r"(?:\+62|62|0)8\d{1,2}[-\s.]?\d{3,4}[-\s.]?\d{3,5}",
}


@dataclass
class RedactResult:
    hits: int
    pages: int


def redact(path: str, out: str, terms: Iterable[str], patterns: Iterable[str], strip_metadata: bool = True) -> RedactResult:
    """True redaction: matching text is DELETED from the file (not just covered by a black box).
    Works on digital text only; scanned PDFs need OCR first."""
    doc = open_pdf(path)
    terms = [t.strip() for t in terms if t and t.strip()]
    regexes = [re.compile(p) for p in patterns if p]
    hits = pages_hit = 0
    for page in doc:
        found: list[pymupdf.Rect] = []
        for t in terms:
            found += page.search_for(t)
        if regexes:
            text = page.get_text("text")
            for rx in regexes:
                for m in set(rx.findall(text)):
                    s = m if isinstance(m, str) else next((g for g in m if g), "")
                    if s:
                        found += page.search_for(s)
        if found:
            pages_hit += 1
            hits += len(found)
            for r in found:
                page.add_redact_annot(r, fill=(0, 0, 0))
            page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_PIXELS)
    if strip_metadata:
        doc.set_metadata({})
        doc.del_xml_metadata()
    save(doc, out)
    doc.close()
    return RedactResult(hits, pages_hit)


# ---------------------------------------------------------------------------
# Watermark & page numbers
# ---------------------------------------------------------------------------
def _hex_to_rgb(color: str) -> tuple[float, float, float]:
    color = color.lstrip("#")
    return tuple(int(color[i:i + 2], 16) / 255 for i in (0, 2, 4))  # type: ignore[return-value]


def watermark(path: str, out: str, text: str, opacity: float = 0.15, color: str = "#808080",
              angle: int = 45, size_ratio: float = 0.08, pages_spec: str = "") -> None:
    """Diagonal text watermark in the middle of the page (on top of the content, semi-transparent)."""
    if not text.strip():
        raise InvalidInput("watermark_text_required")
    doc = open_pdf(path)
    rgb = _hex_to_rgb(color)
    for pno in parse_pages(pages_spec, doc.page_count):
        page = doc[pno]
        r = page.rect
        fontsize = max(12, min(r.width, r.height) * size_ratio)
        tw = pymupdf.get_text_length(text, fontname="helv", fontsize=fontsize)
        center = pymupdf.Point(r.width / 2, r.height / 2)
        start = pymupdf.Point(center.x - tw / 2, center.y + fontsize / 3)
        mat = pymupdf.Matrix(angle)  # positive angle = rising to the right (all page orientations)
        page.insert_text(
            start * page.derotation_matrix, text, fontsize=fontsize, fontname="helv", color=rgb,
            fill_opacity=opacity, morph=(center * page.derotation_matrix, mat), overlay=True,
            rotate=page.rotation,
        )
    save(doc, out)
    doc.close()


# Labels live in i18n ("pos_<id>").
PAGE_NUMBER_POSITIONS = ["bottom-center", "bottom-right", "bottom-left", "top-center", "top-right", "top-left"]


def page_numbers(path: str, out: str, position: str = "bottom-center", fmt: str = "{n} / {total}",
                 start_at: int = 1, fontsize: float = 10, margin_mm: float = 10, skip_first: bool = False) -> None:
    if "{n}" not in fmt:
        raise InvalidInput("page_number_format")
    vertical, horizontal = position.split("-")
    doc = open_pdf(path)
    total = doc.page_count + start_at - 1
    m = margin_mm * MM
    for page in doc:
        if skip_first and page.number == 0:
            continue
        label = fmt.replace("{n}", str(page.number + start_at)).replace("{total}", str(total))
        r = page.rect
        tw = pymupdf.get_text_length(label, fontname="helv", fontsize=fontsize)
        x = {"center": (r.width - tw) / 2, "right": r.width - m - tw, "left": m}[horizontal]
        y = r.height - m if vertical == "bottom" else m + fontsize
        p = pymupdf.Point(x, y) * page.derotation_matrix
        page.insert_text(p, label, fontsize=fontsize, fontname="helv", color=(0, 0, 0), rotate=page.rotation)
    save(doc, out)
    doc.close()


# ---------------------------------------------------------------------------
# Images <-> PDF
# ---------------------------------------------------------------------------
def _image_bytes_for_pdf(path: str) -> tuple[bytes, int, int, tuple[float, float]]:
    """Prepare an image for the PDF without losing quality.
    JPEG/PNG files that don't need rotating are embedded byte-for-byte (no recompression)."""
    with Image.open(path) as im:
        im.load()
        fmt = (im.format or "").upper()
        dpi = im.info.get("dpi", (150, 150))
        dpi = tuple(float(d) if d and d > 1 else 150.0 for d in dpi[:2])  # type: ignore[assignment]
        orientation = im.getexif().get(0x0112, 1)
        if fmt in ("JPEG", "PNG") and orientation == 1 and im.mode in ("RGB", "L", "RGBA", "LA", "P", "1"):
            with open(path, "rb") as f:
                return f.read(), im.width, im.height, dpi  # type: ignore[return-value]
        im = ImageOps.exif_transpose(im)  # phone photos: rotate as the camera intended
        buf = io.BytesIO()
        if fmt == "JPEG" or im.mode == "CMYK":
            im.convert("RGB").save(buf, "JPEG", quality=95, subsampling=0)
        else:
            if im.mode not in ("RGB", "RGBA", "L", "LA"):
                im = im.convert("RGBA" if "A" in im.getbands() else "RGB")
            im.save(buf, "PNG", optimize=True)
        return buf.getvalue(), im.width, im.height, dpi  # type: ignore[return-value]


def images_to_pdf(paths: list[str], out: str, paper: str = "a4", margin_mm: float = 10,
                  auto_orientation: bool = True) -> int:
    """Images -> PDF. Images are not resampled (original quality), only placed proportionally on the page."""
    size = PAPER_SIZES.get(paper)
    doc = pymupdf.open()
    for path in paths:
        data, w, h, (dx, dy) = _image_bytes_for_pdf(path)
        if size is None:
            page = doc.new_page(width=w / dx * 72, height=h / dy * 72)
            page.insert_image(page.rect, stream=data)
            continue
        pw, ph = size
        if auto_orientation and (w > h) != (pw > ph):
            pw, ph = ph, pw
        page = doc.new_page(width=pw, height=ph)
        m = margin_mm * MM
        page.insert_image(pymupdf.Rect(m, m, pw - m, ph - m), stream=data, keep_proportion=True)
    if doc.page_count == 0:
        raise InvalidInput("no_images")
    save(doc, out)
    n = doc.page_count
    doc.close()
    return n


MAX_RENDER_PIXELS = int(os.environ.get("PDFTOOLS_MAX_RENDER_PIXELS", 60_000_000))  # per page


def pdf_to_images(path: str, out_dir: str, base: str, dpi: int = 150, fmt: str = "png",
                  pages_spec: str = "", progress: Optional[Callable[[float], None]] = None) -> list[str]:
    """Render pages to PNG/JPG one at a time (low memory use)."""
    doc = open_pdf(path)
    pages = parse_pages(pages_spec, doc.page_count)
    width = len(str(doc.page_count))
    outs = []
    for i, pno in enumerate(pages):
        page = doc[pno]
        d = dpi
        px = (page.rect.width / 72 * d) * (page.rect.height / 72 * d)
        if px > MAX_RENDER_PIXELS:
            d = int(d * (MAX_RENDER_PIXELS / px) ** 0.5)  # huge page: lower the DPI automatically
        pix = page.get_pixmap(dpi=d, alpha=False)
        out = os.path.join(out_dir, f"{base}_page_{pno + 1:0{width}d}.{fmt}")
        if fmt == "jpg":
            pix.save(out, jpg_quality=92)
        else:
            pix.save(out)
        outs.append(out)
        if progress:
            progress((i + 1) / len(pages))
    doc.close()
    return outs
