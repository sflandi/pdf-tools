import os

import streamlit as st

from pdftools import core, ui
from pdftools.ui import t

ui.header("unlock_title", "unlock_caption")

uploaded = st.file_uploader(t("unlock_upload"), type=["pdf"])
password = st.text_input(t("pdf_password"), type="password")

if st.button(t("unlock_button"), type="primary", disabled=not uploaded):
    with ui.workdir() as wd, st.spinner(t("processing")):
        try:
            src = ui.save_upload(uploaded, wd)
            out = os.path.join(wd, "result.pdf")
            with ui.timed("unlock"):
                was_locked = core.unlock(src, password, out)
            ui.set_result("unlock", uploaded, bytes=ui.read_bytes(out),
                          filename=f"{ui.stem(uploaded)}_unlocked.pdf", mime="application/pdf",
                          was_locked=was_locked)
        except core.PdfLocked as e:
            st.error(t("err_invalid", msg=t(e.key)))
        except Exception as e:
            ui.show_error(e, "unlock")

res = ui.get_result("unlock", uploaded)
if res:
    if res["was_locked"]:
        st.success(t("unlock_ok"))
    else:
        st.info(t("unlock_not_locked"))
    ui.download(res)
