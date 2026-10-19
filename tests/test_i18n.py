"""Every UI text key used in the code must exist in pdftools.i18n with both an English and an
Indonesian translation, so no page can show a raw key or fall back to one language only."""

import glob
import os
import re

from conftest import ROOT
from pdftools import core, ocr
from pdftools.i18n import STRINGS, tr

SOURCES = [os.path.join(ROOT, "app.py")] + glob.glob(os.path.join(ROOT, "pages", "*.py")) + \
    glob.glob(os.path.join(ROOT, "pdftools", "*.py"))


def _used_keys() -> set[str]:
    keys: set[str] = set()
    pattern = re.compile(r"""\b(?:t|tr|say|header|InvalidInput|PdfLocked|UserError)\(\s*"([a-z0-9_+\-]+)"(?:\s*,\s*"([a-z0-9_+\-]+)")?""")
    for path in SOURCES:
        with open(path, encoding="utf-8") as f:
            for m in pattern.finditer(f.read()):
                keys.update(k for k in m.groups() if k)
    # keys built from ids at runtime
    keys.update(f"paper_{p}" for p in core.PAPER_SIZES)
    keys.update(f"pos_{p}" for p in core.PAGE_NUMBER_POSITIONS)
    keys.update(f"preset_{p}" for p in core.REDACT_PRESETS)
    keys.update(f"lang_{c}" for c in ocr.LANG_CODES)
    keys.update(f"fallback_{k}" for k in ("single", "split", "stop"))
    keys.update(f"split_{k}" for k in ("every", "ranges", "size"))
    keys.update(f"meta_{k}" for k in core.META_FIELDS + ["edit", "strip"])
    keys.update(f"{kind}_{k}" for kind in ("nav", "desc") for k in (
        "compress", "pdf2img", "img2pdf", "word", "ocrdocx", "ocrpdf", "office",
        "merge", "split", "organize", "numbers", "watermark", "unlock", "protect", "redact", "metadata"))
    return keys


def test_every_used_key_is_translated():
    missing = sorted(k for k in _used_keys() if k not in STRINGS)
    assert not missing, f"keys without translation: {missing}"


def test_both_languages_filled():
    empty = [k for k, (en, id_) in STRINGS.items() if not en.strip() or not id_.strip()]
    assert not empty, empty


def test_placeholders_match_between_languages():
    bad = []
    for key, (en, id_) in STRINGS.items():
        if set(re.findall(r"\{(\w+)\}", en)) != set(re.findall(r"\{(\w+)\}", id_)):
            bad.append(key)
    assert not bad, bad


def test_tr():
    assert tr("merge_ok", "en", pages=3) == "✅ Merged: 3 pages."
    assert tr("merge_ok", "id", pages=3) == "✅ Berhasil digabung: 3 halaman."
    assert tr("page_number_format", "en").count("{n}") == 2  # literal placeholders stay
    assert tr("does_not_exist") == "does_not_exist"
