import os

import streamlit as st

from pdftools import core, ui
from pdftools.ui import t

ui.header("protect_title", "protect_caption")

uploaded = st.file_uploader(t("upload_pdf"), type=["pdf"])
pw1 = st.text_input(t("pw_open"), type="password")
pw2 = st.text_input(t("pw_repeat"), type="password")
st.write(t("permissions"))
c1, c2, c3 = st.columns(3)
allow_print = c1.checkbox(t("allow_print"), value=True)
allow_copy = c2.checkbox(t("allow_copy"), value=False)
allow_edit = c3.checkbox(t("allow_edit"), value=False)
owner = st.text_input(t("owner_pw"), type="password", help=t("owner_pw_help"))

if pw1 and len(pw1) < 8:
    st.warning(t("pw_short"))

if st.button(t("protect_button"), type="primary", disabled=not uploaded or not pw1):
    if pw1 != pw2:
        st.error(t("pw_mismatch"))
    else:
        with ui.workdir() as wd, st.spinner(t("locking")):
            try:
                src = ui.save_upload(uploaded, wd)
                out = os.path.join(wd, "result.pdf")
                with ui.timed("protect"):
                    core.protect(src, out, pw1, owner, allow_print, allow_copy, allow_edit)
                ui.set_result("protect", uploaded, bytes=ui.read_bytes(out),
                              filename=f"{ui.stem(uploaded)}_locked.pdf", mime="application/pdf")
            except Exception as e:
                ui.show_error(e, "protect")

res = ui.get_result("protect", uploaded)
if res:
    st.success(t("protect_ok"))
    ui.download(res)
