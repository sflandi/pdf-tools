import os

import streamlit as st

from pdftools import core, ui
from pdftools.ui import t

ui.header("word_title", "word_caption")

uploaded = st.file_uploader(t("upload_pdf"), type=["pdf"])
pages_spec = st.text_input(t("pages_input"), "", placeholder=t("pages_placeholder"))

if st.button(t("word_button"), type="primary", disabled=not uploaded):
    with ui.workdir() as wd, st.status(t("converting"), expanded=True) as status:
        try:
            src = ui.save_upload(uploaded, wd)
            doc = core.open_pdf(src)
            pages = core.parse_pages(pages_spec, doc.page_count)
            doc.close()
            out = os.path.join(wd, "result.docx")
            args = ["pdf2docx", src, out, "--pages", ",".join(map(str, pages))]
            with ui.heavy_job(status), ui.timed("pdf2docx", pages=len(pages)):
                ui.run_worker(args, timeout=max(180, 10 * len(pages)))
            ui.set_result("pdf2docx", uploaded, bytes=ui.read_bytes(out), filename=f"{ui.stem(uploaded)}.docx",
                          mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            status.update(label=t("done"), state="complete", expanded=False)
        except Exception as e:
            status.update(label=t("failed"), state="error")
            ui.show_error(e, "pdf2docx")

res = ui.get_result("pdf2docx", uploaded)
if res:
    st.success(t("word_ok"))
    ui.download(res)
