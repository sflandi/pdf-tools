import os

import streamlit as st

from pdftools import ocr, ui
from pdftools.ui import t

ui.header("ocrpdf_title", "ocrpdf_caption")

langs = ocr.available_languages()
if not langs:
    st.error(t("ocr_missing"))
    st.stop()

uploaded = st.file_uploader(t("ocrpdf_upload"), type=["pdf"])
lang = st.selectbox(t("doc_language"), langs, format_func=lambda code: t(f"lang_{code}"))
all_pages = st.checkbox(t("ocr_all_pages"), value=False, help=t("ocr_all_help"))

if st.button(t("ocrpdf_button"), type="primary", disabled=not uploaded):
    with ui.workdir() as wd, st.status(t("reading_text"), expanded=True) as status:
        try:
            src = ui.save_upload(uploaded, wd)
            out = os.path.join(wd, "result.pdf")
            bar = st.progress(0.0)
            args = ["ocr-pdf", src, out, "--lang", lang] + (["--all-pages"] if all_pages else [])
            with ui.heavy_job(status), ui.timed("ocr_pdf"):
                done = ui.run_worker(args, timeout=3600, on_progress=bar.progress)
            ui.set_result("ocr_pdf", uploaded, bytes=ui.read_bytes(out), filename=f"{ui.stem(uploaded)}_ocr.pdf",
                          mime="application/pdf", pages=int(done[0]) if done else 0)
            status.update(label=t("done"), state="complete", expanded=False)
        except Exception as e:
            status.update(label=t("failed"), state="error")
            ui.show_error(e, "ocr_pdf")

res = ui.get_result("ocr_pdf", uploaded)
if res:
    if res["pages"]:
        st.success(t("ocrpdf_ok", n=res["pages"]))
    else:
        st.info(t("ocrpdf_none"))
    ui.download(res)
