import os

import streamlit as st

from pdftools import core, office, ui
from pdftools.ui import t

ui.header("office_title", "office_caption")

if not office.find_soffice():
    st.error(t("lo_missing"))
    st.stop()

uploaded = st.file_uploader(t("office_upload"), type=office.OFFICE_TYPES)
with st.expander(t("meta_optional")):
    meta = {k: st.text_input(t(f"meta_{k}")) for k in ("title", "author", "subject", "keywords")}
    st.caption(t("meta_empty_hint"))

if st.button(t("office_button"), type="primary", disabled=not uploaded):
    with ui.workdir() as wd, st.status(t("converting"), expanded=True) as status:
        try:
            src = ui.save_upload(uploaded, wd)
            with ui.heavy_job(status), ui.timed("office_to_pdf"):
                pdf = office.office_to_pdf(src, wd)
            out = os.path.join(wd, "result.pdf")
            core.write_metadata(pdf, out, {**meta, "creator": "", "producer": ""})
            ui.set_result("office", uploaded, bytes=ui.read_bytes(out), filename=f"{ui.stem(uploaded)}.pdf",
                          mime="application/pdf")
            status.update(label=t("done"), state="complete", expanded=False)
        except Exception as e:
            status.update(label=t("failed"), state="error")
            ui.show_error(e, "office_to_pdf")

res = ui.get_result("office", uploaded)
if res:
    st.success(t("office_ok"))
    ui.download(res)
