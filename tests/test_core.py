import os

import pymupdf
import pytest

from conftest import SECRET_EMAIL, SECRET_NIK
from pdftools import core


def test_parse_pages():
    assert core.parse_pages("1-3, 5, 8-", 10) == [0, 1, 2, 4, 7, 8, 9]
    assert core.parse_pages("3-1", 5) == [2, 1, 0]
    assert core.parse_pages("", 3) == [0, 1, 2]
    with pytest.raises(core.InvalidInput):
        core.parse_pages("0-2", 5)
    with pytest.raises(core.InvalidInput):
        core.parse_pages("abc", 5)
    assert core.parse_groups("1-2; 3-", 5) == [[0, 1], [2, 3, 4]]


def test_open_rejects_non_pdf(tmp_path):
    bad = tmp_path / "not.pdf"
    bad.write_bytes(b"MZ\x90\x00 not a pdf")
    with pytest.raises(core.InvalidInput):
        core.open_pdf(str(bad))


def test_merge_keeps_bookmarks(text_pdf, tmp_path):
    out = str(tmp_path / "m.pdf")
    n = core.merge([text_pdf, text_pdf], ["a.pdf", "b.pdf"], out)
    assert n == 10
    toc = pymupdf.open(out).get_toc()
    assert [1, "a", 1] in toc and [1, "b", 6] in toc
    assert [2, "Chapter 2", 8] in toc  # bookmarks of the second file are shifted by 5 pages


def test_split_modes(text_pdf, tmp_path):
    assert len(core.split_every(text_pdf, 1, str(tmp_path), "x")) == 5
    assert len(core.split_every(text_pdf, 2, str(tmp_path), "y")) == 3
    parts = core.split_groups(text_pdf, [[0, 1], [4]], str(tmp_path), "z")
    assert [pymupdf.open(p).page_count for p in parts] == [2, 1]


def test_split_by_size(image_pdf, tmp_path):
    limit = int(os.path.getsize(image_pdf) / 2.5)
    parts, oversize = core.split_by_size(image_pdf, limit, str(tmp_path), "s")
    assert len(parts) >= 3
    assert sum(pymupdf.open(p).page_count for p in parts) == 6
    for p in parts:
        assert os.path.getsize(p) <= limit or pymupdf.open(p).page_count == 1


def test_reorganize(text_pdf, tmp_path):
    out = str(tmp_path / "r.pdf")
    assert core.reorganize(text_pdf, out, "3, 1-2", "1", 90) == 3
    doc = pymupdf.open(out)
    assert "Page 3" in doc[0].get_text() and doc[0].rotation == 90
    assert "Page 1" in doc[1].get_text() and doc[1].rotation == 0


def test_protect_then_unlock(text_pdf, tmp_path):
    locked = str(tmp_path / "locked.pdf")
    core.protect(text_pdf, locked, "rahasia123", allow_print=True, allow_copy=False)
    doc = pymupdf.open(locked)
    assert doc.needs_pass
    assert doc.authenticate("rahasia123")
    assert doc.permissions & pymupdf.PDF_PERM_PRINT
    assert not doc.permissions & pymupdf.PDF_PERM_COPY
    with pytest.raises(core.PdfLocked):
        core.unlock(locked, "salah", str(tmp_path / "x.pdf"))
    out = str(tmp_path / "open.pdf")
    assert core.unlock(locked, "rahasia123", out) is True
    assert not pymupdf.open(out).needs_pass


def test_metadata_removes_xmp(text_pdf, tmp_path):
    meta, has_xmp = core.read_metadata(text_pdf)
    assert meta["author"] == "Penulis Asli" and has_xmp
    out = str(tmp_path / "meta.pdf")
    core.write_metadata(text_pdf, out, {"author": "Tim IT", "title": "Baru"})
    doc = pymupdf.open(out)
    assert doc.metadata["author"] == "Tim IT"
    assert "Penulis XMP" not in doc.get_xml_metadata()
    out2 = str(tmp_path / "strip.pdf")
    core.write_metadata(text_pdf, out2, {}, strip_all=True)
    doc2 = pymupdf.open(out2)
    assert not doc2.metadata.get("author") and not doc2.get_xml_metadata().strip()


def test_redact_removes_text(text_pdf, tmp_path):
    out = str(tmp_path / "red.pdf")
    patterns = [core.REDACT_PRESETS[k] for k in ("nik", "email", "phone")]
    r = core.redact(text_pdf, out, [], patterns)
    assert r.hits == 3 and r.pages == 1
    text = "".join(p.get_text() for p in pymupdf.open(out))
    assert SECRET_NIK not in text and SECRET_EMAIL not in text and "0812" not in text
    assert "Page 3" in text  # other text is kept


def test_watermark_and_numbers(text_pdf, tmp_path):
    wm = str(tmp_path / "wm.pdf")
    core.watermark(text_pdf, wm, "RAHASIA")
    assert all("RAHASIA" in p.get_text() for p in pymupdf.open(wm))
    num = str(tmp_path / "num.pdf")
    core.page_numbers(wm, num, "bottom-right", "Page {n} of {total}", skip_first=True)
    doc = pymupdf.open(num)
    assert "Page 1 of 5" not in doc[0].get_text()
    assert "Page 2 of 5" in doc[1].get_text()


def test_images_to_pdf_keeps_original_jpeg(jpeg_plain, jpeg_rotated, tmp_path):
    out = str(tmp_path / "img.pdf")
    assert core.images_to_pdf([jpeg_plain, jpeg_rotated], out, "a4") == 2
    doc = pymupdf.open(out)
    xref = doc[0].get_images()[0][0]
    with open(jpeg_plain, "rb") as f:
        assert doc.xref_stream_raw(xref) == f.read()  # original bytes, not recompressed
    # photo with EXIF orientation 6 (400x200) must become upright (200x400) -> portrait page
    info = doc[1].get_images(full=True)[0]
    assert (info[2], info[3]) == (200, 400)
    assert doc[1].rect.height > doc[1].rect.width


def test_pdf_to_images(text_pdf, tmp_path):
    files = core.pdf_to_images(text_pdf, str(tmp_path), "t", dpi=72, fmt="png", pages_spec="2-3")
    assert [os.path.basename(f) for f in files] == ["t_page_2.png", "t_page_3.png"]
