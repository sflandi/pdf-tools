import os

import streamlit as st

from pdftools import core, ui
from pdftools.ui import t

ui.header("organize_title", "organize_caption")

uploaded = st.file_uploader(t("upload_pdf"), type=["pdf"])

if uploaded:
    # thumbnails are made once per file (not again every time an input changes)
    cache = ui.get_result("organize_thumbs", uploaded)
    if not cache:
        with ui.workdir() as wd, st.spinner(t("making_preview")):
            try:
                src = ui.save_upload(uploaded, wd)
                doc = core.open_pdf(src)
                total = doc.page_count
                doc.close()
                ui.set_result("organize_thumbs", uploaded, total=total, thumbs=core.thumbnails(src))
            except Exception as e:
                ui.show_error(e, "organize")
                st.stop()
        cache = ui.get_result("organize_thumbs", uploaded)
    total = cache["total"]
    st.caption(t("organize_preview", n=total))
    cols = st.columns(6)
    for i, thumb in enumerate(cache["thumbs"]):
        cols[i % 6].image(thumb, caption=str(i + 1), width="stretch")

    order = st.text_input(t("organize_order"), value=f"1-{total}", help=t("organize_order_help"))
    c1, c2 = st.columns([3, 1])
    rot_pages = c1.text_input(t("rotate_pages"), "", placeholder=t("rotate_placeholder"))
    angle = c2.selectbox(t("angle"), [90, 180, 270], format_func=lambda a: t("angle_fmt", a=a))

    if st.button(t("apply"), type="primary"):
        with ui.workdir() as wd, st.spinner(t("processing")):
            try:
                src = ui.save_upload(uploaded, wd)
                out = os.path.join(wd, "result.pdf")
                with ui.timed("organize"):
                    n = core.reorganize(src, out, order, rot_pages, angle)
                ui.set_result("organize", uploaded, bytes=ui.read_bytes(out),
                              filename=f"{ui.stem(uploaded)}_organized.pdf", mime="application/pdf", pages=n)
            except Exception as e:
                ui.show_error(e, "organize")

res = ui.get_result("organize", uploaded)
if res:
    st.success(t("organize_ok", pages=res["pages"]))
    ui.download(res)
