import os

import streamlit as st

from pdftools import core, ui
from pdftools.ui import t

ui.header("pdf2img_title", "pdf2img_caption")

uploaded = st.file_uploader(t("upload_pdf"), type=["pdf"])
c1, c2 = st.columns(2)
fmt = c1.selectbox(t("format"), ["png", "jpg"], format_func=str.upper)
dpi = c2.selectbox(t("resolution"), [100, 150, 200, 300], index=1, format_func=lambda d: f"{d} DPI")
st.caption(t("dpi_hint"))
pages_spec = st.text_input(t("pages_input"), "", placeholder=t("pages_placeholder"))

if st.button(t("pdf2img_button"), type="primary", disabled=not uploaded):
    with ui.workdir() as wd, st.status(t("rendering"), expanded=True) as status:
        try:
            src = ui.save_upload(uploaded, wd)
            bar = st.progress(0.0)
            base = ui.stem(uploaded)
            with ui.heavy_job(status), ui.timed("pdf_to_images", dpi=dpi):
                files = core.pdf_to_images(src, wd, base, dpi, fmt, pages_spec, bar.progress)
            if len(files) == 1:
                data = dict(bytes=ui.read_bytes(files[0]), filename=os.path.basename(files[0]),
                            mime="image/png" if fmt == "png" else "image/jpeg")
            else:
                zip_path = os.path.join(wd, "images.zip")
                core.zip_files(files, zip_path)
                data = dict(bytes=ui.read_bytes(zip_path), filename=f"{base}_images.zip", mime="application/zip")
            ui.set_result("pdf2img", uploaded, count=len(files), **data)
            status.update(label=t("done"), state="complete", expanded=False)
        except Exception as e:
            status.update(label=t("failed"), state="error")
            ui.show_error(e, "pdf_to_images")

res = ui.get_result("pdf2img", uploaded)
if res:
    st.success(t("pdf2img_ok", n=res["count"], mb=f"{len(res['bytes']) / 1e6:.1f}"))
    ui.download(res)
