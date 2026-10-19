import os

import streamlit as st

from pdftools import core, ui
from pdftools.ui import t

ui.header("redact_title", "redact_caption")
st.info(t("redact_scan_info"))

uploaded = st.file_uploader(t("upload_pdf"), type=["pdf"])
presets = st.multiselect(t("redact_presets"), list(core.REDACT_PRESETS), default=["nik"],
                         format_func=lambda p: t(f"preset_{p}"))
terms = st.text_area(t("redact_terms"), placeholder="John Doe\n221B Baker Street")
strip = st.checkbox(t("strip_meta"), value=True)

if st.button(t("redact_button"), type="primary", disabled=not uploaded or not (presets or terms.strip())):
    with ui.workdir() as wd, st.spinner(t("redacting")):
        try:
            src = ui.save_upload(uploaded, wd)
            out = os.path.join(wd, "result.pdf")
            with ui.timed("redact", presets=len(presets)):
                r = core.redact(src, out, terms.splitlines(), [core.REDACT_PRESETS[p] for p in presets], strip)
            ui.set_result("redact", uploaded, bytes=ui.read_bytes(out),
                          filename=f"{ui.stem(uploaded)}_redacted.pdf", mime="application/pdf",
                          hits=r.hits, pages=r.pages)
        except Exception as e:
            ui.show_error(e, "redact")

res = ui.get_result("redact", uploaded)
if res:
    if res["hits"]:
        st.success(t("redact_ok", hits=res["hits"], pages=res["pages"]))
    else:
        st.warning(t("redact_none"))
    ui.download(res)
