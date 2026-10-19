"""OCR using the Tesseract engine built into PyMuPDF (only the *.traineddata language files are needed)."""

from __future__ import annotations

import glob
import os
from typing import Callable, Optional

import pymupdf
from docx import Document

from .core import open_pdf

# Supported language codes; labels live in i18n ("lang_<code>").
LANG_CODES = ["ind", "eng", "ind+eng"]

_TESSDATA_GUESSES = [
    "/usr/share/tesseract-ocr/5/tessdata",
    "/usr/share/tesseract-ocr/4.00/tessdata",
    "/usr/share/tessdata",
    "/usr/local/share/tessdata",
    r"C:\Program Files\Tesseract-OCR\tessdata",
]


def tessdata_dir() -> Optional[str]:
    env = os.environ.get("TESSDATA_PREFIX")
    for d in ([env] if env else []) + _TESSDATA_GUESSES:
        if d and glob.glob(os.path.join(d, "*.traineddata")):
            return d
    try:
        return pymupdf.get_tessdata()
    except Exception:
        return None


def available_languages() -> list[str]:
    d = tessdata_dir()
    if not d:
        return []
    have = {os.path.basename(p)[: -len(".traineddata")] for p in glob.glob(os.path.join(d, "*.traineddata"))}
    return [code for code in LANG_CODES if all(part in have for part in code.split("+"))]


def _ocr_textpage(page: pymupdf.Page, lang: str, dpi: int) -> pymupdf.TextPage:
    return page.get_textpage_ocr(language=lang, dpi=dpi, full=True, tessdata=tessdata_dir())


def ocr_to_searchable_pdf(in_path: str, out_path: str, lang: str = "ind+eng", dpi: int = 300,
                          skip_text_pages: bool = True, progress: Optional[Callable[[float], None]] = None) -> int:
    """Add an invisible text layer on top of scanned pages (like OCRmyPDF).
    The page looks exactly the same; the text becomes searchable, copyable and screen-reader friendly.
    Returns the number of pages that were OCR'd."""
    doc = open_pdf(in_path)
    done = 0
    for page in doc:
        if skip_text_pages and page.get_text("text").strip():
            if progress:
                progress((page.number + 1) / doc.page_count)
            continue
        tp = _ocr_textpage(page, lang, dpi)
        for x0, y0, x1, y1, word, *_ in page.get_text("words", textpage=tp):
            r = pymupdf.Rect(x0, y0, x1, y1)
            if r.is_empty or not word.strip():
                continue
            fs = max(1.0, r.height * 0.85)
            tw = pymupdf.get_text_length(word, fontname="helv", fontsize=fs) or 1
            start = pymupdf.Point(r.x0, r.y1 - r.height * 0.2)
            page.insert_text(
                start * page.derotation_matrix, word, fontsize=fs, fontname="helv", render_mode=3,
                morph=(start * page.derotation_matrix, pymupdf.Matrix(r.width / tw, 1)), rotate=page.rotation,
            )
        done += 1
        if progress:
            progress((page.number + 1) / doc.page_count)
    doc.save(out_path, garbage=3, deflate=True, use_objstms=1)
    doc.close()
    return done


def ocr_to_docx(in_path: str, out_path: str, lang: str = "ind+eng", dpi: int = 300,
                progress: Optional[Callable[[float], None]] = None) -> int:
    """OCR to Word: text per paragraph (block); each PDF page becomes one section of the document."""
    doc = open_pdf(in_path)
    word = Document()
    for page in doc:
        tp = _ocr_textpage(page, lang, dpi)
        blocks = page.get_text("blocks", textpage=tp, sort=True)
        for b in blocks:
            text = " ".join(b[4].split())
            if text:
                word.add_paragraph(text)
        if page.number < doc.page_count - 1:
            word.add_page_break()
        if progress:
            progress((page.number + 1) / doc.page_count)
    n = doc.page_count
    doc.close()
    word.save(out_path)
    return n
