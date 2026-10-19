import os

import streamlit as st

from pdftools import core, ui
from pdftools.ui import t

ui.header("numbers_title", "numbers_caption")

uploaded = st.file_uploader(t("upload_pdf"), type=["pdf"])
c1, c2 = st.columns(2)
position = c1.selectbox(t("position"), core.PAGE_NUMBER_POSITIONS, format_func=lambda p: t(f"pos_{p}"))
fmt = c2.text_input(t("format"), "{n} / {total}", help=t("format_help"))
c3, c4, c5 = st.columns(3)
start_at = c3.number_input(t("start_at"), 1, 100_000, 1)
fontsize = c4.number_input(t("font_size"), 6, 48, 10)
margin = c5.number_input(t("margin_edge"), 3, 50, 10)
skip_first = st.checkbox(t("skip_first"))

if st.button(t("numbers_button"), type="primary", disabled=not uploaded):
    with ui.workdir() as wd, st.spinner(t("processing")):
        try:
            src = ui.save_upload(uploaded, wd)
            out = os.path.join(wd, "result.pdf")
            with ui.timed("page_numbers"):
                core.page_numbers(src, out, position, fmt, int(start_at), fontsize, margin, skip_first)
            ui.set_result("numbers", uploaded, bytes=ui.read_bytes(out),
                          filename=f"{ui.stem(uploaded)}_numbered.pdf", mime="application/pdf")
        except Exception as e:
            ui.show_error(e, "page_numbers")

res = ui.get_result("numbers", uploaded)
if res:
    st.success(t("numbers_ok"))
    ui.download(res)
