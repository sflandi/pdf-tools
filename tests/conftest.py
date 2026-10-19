import io
import os
import sys

import pymupdf
import pytest
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

SECRET_NIK = "3174012345678901"
SECRET_EMAIL = "budi.santoso@contoh.co.id"


def photo(w: int, h: int, seed: int = 0) -> Image.Image:
    """Photo-like image (gradients + soft noise) that compresses like a real photo."""
    import random

    rnd = random.Random(seed)
    small = Image.new("RGB", (max(2, w // 40), max(2, h // 40)))
    small.putdata([(rnd.randrange(256), rnd.randrange(256), rnd.randrange(256)) for _ in range(small.width * small.height)])
    img = small.resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(2))
    d = ImageDraw.Draw(img)
    for i in range(0, h, 60):
        d.text((20, i + 10), f"Screenshot line {i // 60}", fill=(0, 0, 0))
    return img


@pytest.fixture
def text_pdf(tmp_path) -> str:
    doc = pymupdf.open()
    for i in range(5):
        p = doc.new_page()
        p.insert_text((72, 100), f"Page {i + 1}", fontsize=20)
        if i == 2:
            p.insert_text((72, 150), f"NIK: {SECRET_NIK}", fontsize=12)
            p.insert_text((72, 170), f"Email: {SECRET_EMAIL}", fontsize=12)
            p.insert_text((72, 190), "HP: 0812-3456-7890", fontsize=12)
    doc.set_toc([[1, "Chapter 1", 1], [1, "Chapter 2", 3]])
    doc.set_metadata({"author": "Penulis Asli", "title": "Judul Asli"})
    doc.set_xml_metadata('<?xpacket begin=""?><x:xmpmeta xmlns:x="adobe:ns:meta/"><dc:creator>Penulis XMP</dc:creator></x:xmpmeta><?xpacket end="w"?>')
    path = str(tmp_path / "text.pdf")
    doc.save(path)
    return path


@pytest.fixture
def image_pdf(tmp_path) -> str:
    """6 A4 pages, each with a 2480x1600 PNG photo (lossless, large) + text."""
    doc = pymupdf.open()
    for i in range(6):
        p = doc.new_page()
        buf = io.BytesIO()
        photo(2480, 1600, i).save(buf, "PNG")
        p.insert_image(pymupdf.Rect(36, 36, 559, 373), stream=buf.getvalue())
        p.insert_text((72, 420), f"Important text on page {i + 1}", fontsize=14)
    path = str(tmp_path / "images.pdf")
    doc.save(path, deflate=True)
    return path


@pytest.fixture
def heavy_vector_pdf(tmp_path) -> str:
    """Page 1 holds thousands of vector dots (like a PowerPoint halftone background) + text."""
    doc = pymupdf.open()
    p = doc.new_page(width=1440, height=810)
    shape = p.new_shape()
    for y in range(0, 810, 6):
        for x in range(0, 1440, 6):
            shape.draw_circle((x + 0.123, y + 0.456), 1.7 + (x * y % 7) / 10)
    shape.finish(color=None, fill=(0.6, 0.7, 0.9))
    shape.commit()
    p.insert_text((100, 400), "Title Stays Sharp", fontsize=60)
    q = doc.new_page(width=1440, height=810)
    q.insert_text((100, 400), "Regular page", fontsize=40)
    path = str(tmp_path / "vector.pdf")
    doc.save(path, deflate=True)
    return path


@pytest.fixture
def jpeg_rotated(tmp_path) -> str:
    """400x200 JPEG with EXIF orientation=6 (a phone photo that must be rotated 90°)."""
    img = photo(400, 200, 7)
    exif = Image.Exif()
    exif[0x0112] = 6
    path = str(tmp_path / "rotated.jpg")
    img.save(path, "JPEG", exif=exif)
    return path


@pytest.fixture
def jpeg_plain(tmp_path) -> str:
    path = str(tmp_path / "plain.jpg")
    photo(600, 800, 3).save(path, "JPEG", quality=90)
    return path
