import os

import streamlit as st

from pdftools import core, ui
from pdftools.ui import t

ui.header("img_title", "img_caption")

uploads = st.file_uploader(t("img_upload"), type=["png", "jpg", "jpeg", "bmp", "tif", "tiff", "webp"],
                           accept_multiple_files=True)
c1, c2 = st.columns(2)
paper = c1.selectbox(t("paper"), list(core.PAPER_SIZES), index=1, format_func=lambda p: t(f"paper_{p}"))
original_size = core.PAPER_SIZES[paper] is None
margin = c2.number_input(t("margin"), 0, 50, 10, disabled=original_size)
auto = st.checkbox(t("auto_landscape"), value=True, disabled=original_size)

if st.button(t("img_button"), type="primary", disabled=not uploads):
    with ui.workdir() as wd, st.spinner(t("creating_pdf")):
        try:
            paths = [ui.save_upload(u, wd, f"img_{i:04d}{os.path.splitext(u.name)[1].lower()}")
                     for i, u in enumerate(uploads)]
            out = os.path.join(wd, "images.pdf")
            with ui.timed("images_to_pdf", files=len(paths)):
                n = core.images_to_pdf(paths, out, paper, margin, auto)
            ui.set_result("img2pdf", uploads, bytes=ui.read_bytes(out), filename="images.pdf",
                          mime="application/pdf", pages=n)
        except Exception as e:
            ui.show_error(e, "images_to_pdf")

res = ui.get_result("img2pdf", uploads)
if res:
    st.success(t("img_ok", pages=res["pages"]))
    ui.download(res)
