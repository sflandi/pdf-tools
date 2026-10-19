import os

import pymupdf

from pdftools import compress as engine


def _text(path):
    return [p.get_text().split() for p in pymupdf.open(path)]


def test_compress_meets_target_and_keeps_text(image_pdf, tmp_path):
    original = os.path.getsize(image_pdf)
    target = original // 8
    r = engine.compress_to_target(image_pdf, target, str(tmp_path))
    assert r.met_target and r.best.size <= target
    assert _text(r.best.path) == _text(image_pdf)  # text unchanged
    # picks the HIGHEST quality that fits: no higher level may also fit
    tried = {a.label: a.size for a in r.attempts}
    assert r.best.dpi is not None and r.best.dpi >= 100
    assert all(size > target for label, size in tried.items() if "DPI" in label and int(label.split()[0]) > r.best.dpi)


def test_lossless_when_target_is_generous(image_pdf, tmp_path):
    r = engine.compress_to_target(image_pdf, os.path.getsize(image_pdf) * 2, str(tmp_path))
    assert r.best.label in ("Lossless", engine.ORIGINAL_LABEL)


def test_images_are_resampled_to_display_size(image_pdf, tmp_path):
    out = str(tmp_path / "o.pdf")
    engine._rewrite(image_pdf, out, 100, 70, gray=False, mrc=False)
    doc = pymupdf.open(out)
    info = doc[0].get_images(full=True)[0]
    # displayed 523 pt wide -> 100 DPI = ~726 px (originally 2480 px)
    assert 700 <= info[2] <= 760


def test_mrc_shrinks_heavy_vector_page_but_keeps_text(heavy_vector_pdf, tmp_path):
    info = engine.analyze(heavy_vector_pdf)
    assert info.heavy_vector_pages == 1
    plain, mrc = str(tmp_path / "plain.pdf"), str(tmp_path / "mrc.pdf")
    engine._rewrite(heavy_vector_pdf, plain, 100, 70, gray=False, mrc=False)
    engine._rewrite(heavy_vector_pdf, mrc, 100, 70, gray=False, mrc=True)
    assert os.path.getsize(mrc) < os.path.getsize(plain) / 2
    assert _text(mrc) == _text(heavy_vector_pdf)
    doc = pymupdf.open(mrc)
    assert len(doc[0].get_images()) == 1  # background became one image
    assert not doc[1].get_images()  # light page untouched


def test_gray(image_pdf, tmp_path):
    out = str(tmp_path / "g.pdf")
    engine._rewrite(image_pdf, out, 100, 70, gray=True, mrc=False)
    doc = pymupdf.open(out)
    assert doc.xref_get_key(doc[0].get_images()[0][0], "ColorSpace")[1] == "/DeviceGray"
