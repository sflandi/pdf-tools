import os

import streamlit as st

from pdftools import core, ui
from pdftools.ui import t

ui.header("wm_title", "wm_caption")

uploaded = st.file_uploader(t("upload_pdf"), type=["pdf"])
text = st.text_input(t("wm_text"), t("wm_default"))
c1, c2, c3 = st.columns(3)
opacity = c1.slider(t("opacity"), 0.05, 0.6, 0.15, 0.05, help=t("opacity_help"))
color = c2.color_picker(t("color"), "#808080")
angle = c3.slider(t("tilt"), 0, 90, 45, 5)
size = st.slider(t("wm_size"), 0.03, 0.2, 0.08, 0.01)
pages_spec = st.text_input(t("pages_input"), "", placeholder=t("pages_placeholder"))

if st.button(t("wm_button"), type="primary", disabled=not uploaded):
    with ui.workdir() as wd, st.spinner(t("processing")):
        try:
            src = ui.save_upload(uploaded, wd)
            out = os.path.join(wd, "result.pdf")
            with ui.timed("watermark"):
                core.watermark(src, out, text, opacity, color, angle, size, pages_spec)
            ui.set_result("watermark", uploaded, bytes=ui.read_bytes(out),
                          filename=f"{ui.stem(uploaded)}_watermarked.pdf", mime="application/pdf")
        except Exception as e:
            ui.show_error(e, "watermark")

res = ui.get_result("watermark", uploaded)
if res:
    st.success(t("wm_ok"))
    ui.download(res)
