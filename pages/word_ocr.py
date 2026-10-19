import os

import streamlit as st

from pdftools import ocr, ui
from pdftools.ui import t

ui.header("ocrdocx_title", "ocrdocx_caption")

langs = ocr.available_languages()
if not langs:
    st.error(t("ocr_missing"))
    st.stop()

uploaded = st.file_uploader(t("upload_pdf"), type=["pdf"])
lang = st.selectbox(t("doc_language"), langs, format_func=lambda code: t(f"lang_{code}"))

if st.button(t("ocrdocx_button"), type="primary", disabled=not uploaded):
    with ui.workdir() as wd, st.status(t("reading_text"), expanded=True) as status:
        try:
            src = ui.save_upload(uploaded, wd)
            out = os.path.join(wd, "result.docx")
            bar = st.progress(0.0)
            with ui.heavy_job(status), ui.timed("ocr_docx"):
                ui.run_worker(["ocr-docx", src, out, "--lang", lang], timeout=3600, on_progress=bar.progress)
            ui.set_result("ocr_docx", uploaded, bytes=ui.read_bytes(out), filename=f"{ui.stem(uploaded)}_ocr.docx",
                          mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            status.update(label=t("done"), state="complete", expanded=False)
        except Exception as e:
            status.update(label=t("failed"), state="error")
            ui.show_error(e, "ocr_docx")

res = ui.get_result("ocr_docx", uploaded)
if res:
    st.success(t("ocrdocx_ok"))
    ui.download(res)
