"""Smoke test: every Streamlit page renders without errors (no upload), in both languages."""

import glob
import os

import pytest
from streamlit.testing.v1 import AppTest

from conftest import ROOT

PAGES = sorted(glob.glob(os.path.join(ROOT, "pages", "*.py")))


@pytest.mark.parametrize("lang", ["en", "id"])
@pytest.mark.parametrize("path", PAGES, ids=[os.path.basename(p) for p in PAGES])
def test_page_renders(path, lang):
    at = AppTest.from_file(path, default_timeout=30)
    at.session_state["lang"] = lang
    at.run()
    assert not at.exception, at.exception


def test_home_renders():
    at = AppTest.from_file(os.path.join(ROOT, "app.py"), default_timeout=30).run()
    assert not at.exception, at.exception


def test_login_required_when_password_set(monkeypatch):
    monkeypatch.setenv("PDFTOOLS_PASSWORD", "rahasia")
    at = AppTest.from_file(os.path.join(ROOT, "app.py"), default_timeout=30).run()
    assert not at.exception
    assert any("Password" in t.label for t in at.text_input)
    at.text_input[0].input("salah")
    at.button[0].click().run()
    assert any("Wrong password" in e.value for e in at.error)


def test_language_switch_sticks_and_is_kept_in_url():
    at = AppTest.from_file(os.path.join(ROOT, "app.py"), default_timeout=30).run()
    assert at.sidebar.selectbox[0].value == "en"
    at.sidebar.selectbox[0].select("id").run()
    at.run()  # an extra rerun must not undo the switch
    assert at.sidebar.selectbox[0].value == "id"
    assert at.query_params["lang"] == ["id"] or at.query_params["lang"] == "id"
    assert at.subheader[0].value == "Ukuran & format"


def test_language_from_url():
    at = AppTest.from_file(os.path.join(ROOT, "app.py"), default_timeout=30)
    at.query_params["lang"] = "id"
    at.run()
    assert at.subheader[0].value == "Ukuran & format"
