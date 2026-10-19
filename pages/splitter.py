import os

import streamlit as st

from pdftools import core, ui
from pdftools.ui import t

ui.header("split_title", "split_caption")

uploaded = st.file_uploader(t("upload_pdf"), type=["pdf"])
MODES = ["every", "ranges", "size"]
mode = st.radio(t("split_mode"), MODES, format_func=lambda k: t(f"split_{k}"))
if mode == "every":
    n = st.number_input(t("pages_per_file"), 1, 10_000, 1)
elif mode == "ranges":
    spec = st.text_area(t("ranges_input"), "1-3\n4-")
else:
    max_mb = st.number_input(t("max_mb_per_file"), 0.5, 1000.0, 10.0, 0.5)

if st.button(t("split_button"), type="primary", disabled=not uploaded):
    with ui.workdir() as wd, st.spinner(t("splitting")):
        try:
            src = ui.save_upload(uploaded, wd)
            base = ui.stem(uploaded)
            oversize: list[int] = []
            with ui.timed("split", mode=mode):
                if mode == "every":
                    parts = core.split_every(src, int(n), wd, base)
                elif mode == "ranges":
                    doc = core.open_pdf(src)
                    groups = core.parse_groups(spec, doc.page_count)
                    doc.close()
                    parts = core.split_groups(src, groups, wd, base)
                else:
                    parts, oversize = core.split_by_size(src, int(max_mb * 1e6), wd, base)
            zip_path = os.path.join(wd, "result.zip")
            core.zip_files(parts, zip_path)
            ui.set_result("split", uploaded, bytes=ui.read_bytes(zip_path), filename=f"{base}_split.zip",
                          mime="application/zip", count=len(parts), oversize=oversize,
                          sizes=[(os.path.basename(p), os.path.getsize(p)) for p in parts[:50]])
        except Exception as e:
            ui.show_error(e, "split")

res = ui.get_result("split", uploaded)
if res:
    st.success(t("split_ok", n=res["count"]))
    if res["oversize"]:
        st.warning(t("split_oversize", pages=", ".join(map(str, res["oversize"]))))
    with st.expander(t("file_list")):
        for name, size in res["sizes"]:
            st.write(f"- {name}: {size / 1e6:.2f} MB")
    ui.download(res, t("download_zip"))
