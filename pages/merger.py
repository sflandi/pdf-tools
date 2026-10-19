import os

import streamlit as st

from pdftools import core, ui
from pdftools.ui import t

ui.header("merge_title", "merge_caption")

uploads = st.file_uploader(t("merge_upload"), type=["pdf"], accept_multiple_files=True)

order: list = []
if uploads:
    st.write(t("merge_order"))
    ranks = {}
    for i, u in enumerate(uploads):
        c1, c2 = st.columns([1, 5])
        ranks[i] = c1.number_input(t("order"), 1, len(uploads), i + 1, key=f"rank_{i}_{u.name}",
                                   label_visibility="collapsed")
        c2.write(f"{u.name} ({u.size / 1e6:.1f} MB)")
    order = [uploads[i] for i in sorted(ranks, key=lambda i: (ranks[i], i))]
bookmark = st.checkbox(t("bookmark_per_file"), value=True)

if st.button(t("merge_button"), type="primary", disabled=not uploads or len(uploads) < 2):
    with ui.workdir() as wd, st.spinner(t("merging")):
        try:
            paths = [ui.save_upload(u, wd, f"in_{i:03d}.pdf") for i, u in enumerate(order)]
            out = os.path.join(wd, "merged.pdf")
            with ui.timed("merge", files=len(paths)):
                pages = core.merge(paths, [u.name for u in order], out, bookmark)
            ui.set_result("merge", uploads, bytes=ui.read_bytes(out), filename="merged.pdf",
                          mime="application/pdf", pages=pages)
        except Exception as e:
            ui.show_error(e, "merge")

res = ui.get_result("merge", uploads)
if res:
    st.success(t("merge_ok", pages=res["pages"]))
    ui.download(res)
