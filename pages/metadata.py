import os

import streamlit as st

from pdftools import core, ui
from pdftools.ui import t

ui.header("metadata_title", "metadata_caption")

uploaded = st.file_uploader(t("upload_pdf"), type=["pdf"])

if uploaded:
    cache = ui.get_result("meta_read", uploaded)
    if not cache:
        with ui.workdir() as wd:
            try:
                meta, has_xmp = core.read_metadata(ui.save_upload(uploaded, wd))
                ui.set_result("meta_read", uploaded, meta=meta, has_xmp=has_xmp)
            except Exception as e:
                ui.show_error(e, "metadata")
                st.stop()
        cache = ui.get_result("meta_read", uploaded)
    if cache["has_xmp"]:
        st.caption(t("meta_xmp_note"))

    mode = st.radio(t("action"), ["edit", "strip"], horizontal=True, format_func=lambda m: t(f"meta_{m}"))
    new_meta = {}
    if mode == "edit":
        for k in core.META_FIELDS:
            new_meta[k] = st.text_input(t(f"meta_{k}"), cache["meta"].get(k, ""), key=f"meta_{k}")

    if st.button(t("save"), type="primary"):
        with ui.workdir() as wd, st.spinner(t("saving")):
            try:
                src = ui.save_upload(uploaded, wd)
                out = os.path.join(wd, "result.pdf")
                with ui.timed("metadata", strip=mode == "strip"):
                    core.write_metadata(src, out, new_meta, strip_all=mode == "strip")
                ui.set_result("metadata", uploaded, bytes=ui.read_bytes(out),
                              filename=f"{ui.stem(uploaded)}_metadata.pdf", mime="application/pdf")
            except Exception as e:
                ui.show_error(e, "metadata")

res = ui.get_result("metadata", uploaded)
if res:
    st.success(t("meta_ok"))
    ui.download(res)
