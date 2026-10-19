import streamlit as st

from pdftools import ui
from pdftools.ui import t

st.set_page_config(page_title="PDF Tools", page_icon="📄", layout="centered")
ui.language_selector()
ui.require_auth()

# section key -> [(page file, i18n key suffix, icon)]; titles are "nav_<key>", descriptions "desc_<key>"
SECTIONS: dict[str, list[tuple[str, str, str]]] = {
    "sec_format": [
        ("pages/compress.py", "compress", "🗜"),
        ("pages/pdf_image.py", "pdf2img", "🖼"),
        ("pages/image.py", "img2pdf", "📷"),
        ("pages/word.py", "word", "📝"),
        ("pages/word_ocr.py", "ocrdocx", "🔎"),
        ("pages/ocr_pdf.py", "ocrpdf", "🔤"),
        ("pages/word_metadata.py", "office", "📄"),
    ],
    "sec_pages": [
        ("pages/merger.py", "merge", "🔗"),
        ("pages/splitter.py", "split", "✂"),
        ("pages/organize.py", "organize", "🗂"),
        ("pages/page_numbers.py", "numbers", "🔢"),
        ("pages/watermark.py", "watermark", "💧"),
    ],
    "sec_security": [
        ("pages/unlock.py", "unlock", "🔓"),
        ("pages/protect.py", "protect", "🔒"),
        ("pages/redact.py", "redact", "⬛"),
        ("pages/metadata.py", "metadata", "🏷"),
    ],
}

PAGES = {
    section: [st.Page(path, title=t(f"nav_{key}"), icon=icon) for path, key, icon in items]
    for section, items in SECTIONS.items()
}


def home() -> None:
    st.title(t("home_title"))
    st.caption(t("home_caption"))
    for section, items in SECTIONS.items():
        st.subheader(t(section))
        cols = st.columns(2)
        for idx, (page, (_, key, icon)) in enumerate(zip(PAGES[section], items)):
            with cols[idx % 2].container(border=True):
                st.page_link(page, label=f"**{t(f'nav_{key}')}**", icon=icon)
                st.caption(t(f"desc_{key}"))


nav = st.navigation({"": [st.Page(home, title=t("nav_home"), icon="🏠", default=True)],
                     **{t(section): pages for section, pages in PAGES.items()}})
nav.run()
