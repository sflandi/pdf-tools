import os

import streamlit as st

from pdftools import compress as engine
from pdftools import core, ui
from pdftools.ui import t

ui.header("compress_title", "compress_caption")

uploaded = st.file_uploader(t("upload_pdf"), type=["pdf"])

target_mb = st.number_input(t("target_mb"), min_value=0.5, max_value=1000.0, value=10.0, step=0.5)
FALLBACKS = ["single", "split", "stop"]
fallback = st.radio(t("fallback_label"), FALLBACKS, format_func=lambda k: t(f"fallback_{k}"))
gray = st.checkbox(t("gray_label"), help=t("gray_help"))


def label_text(label: str) -> str:
    return t("label_original") if label == engine.ORIGINAL_LABEL else label


if st.button(t("compress_button"), type="primary", disabled=not uploaded):
    with ui.workdir() as wd, st.status(t("preparing"), expanded=True) as status:
        try:
            src = ui.save_upload(uploaded, wd)
            info = engine.analyze(src)
            if info.encrypted:
                raise core.PdfLocked("pdf_locked")
            st.write(
                t("pdf_summary", pages=info.pages, mb=f"{info.file_size / 1e6:.1f}", images=info.image_count,
                  share=f"{info.image_share:.0%}") + (t("scanned_suffix") if info.looks_scanned else "")
            )
            bar = st.progress(0.0)

            def progress(key: str, frac: float, **params) -> None:
                status.update(label=t(key, **params))
                bar.progress(min(1.0, frac))

            target = int(target_mb * 1e6)
            with ui.heavy_job(status), ui.timed("compress", mb=round(info.file_size / 1e6, 1)):
                result = engine.compress_to_target(
                    src, target, wd, gray=gray, aggressive=(fallback == "single"),
                    progress=progress, analysis=info,
                )
                parts: list[str] = []
                oversize: list[int] = []
                if fallback == "split" and not result.met_target:
                    status.update(label=t("splitting_to_target"))
                    parts, oversize = core.split_by_size(result.best.path, target, wd, ui.stem(uploaded))
            bar.progress(1.0)
            status.update(label=t("done"), state="complete", expanded=False)

            preview_page = engine.pick_preview_page(src)
            data = dict(
                original=result.original_size, label=result.best.label, met=result.met_target,
                kept_original=result.kept_original, target=target_mb,
                attempts=[(a.label, a.size, a.seconds) for a in result.attempts],
                preview_page=preview_page,
                before=engine.render_preview(src, preview_page),
                after=engine.render_preview(result.best.path, preview_page),
            )
            if parts:
                zip_path = os.path.join(wd, "result.zip")
                core.zip_files(parts, zip_path)
                data.update(
                    bytes=ui.read_bytes(zip_path), filename=f"{ui.stem(uploaded)}_compressed.zip",
                    mime="application/zip", size=result.best.size,
                    parts=[(os.path.basename(p), os.path.getsize(p)) for p in parts], oversize=oversize,
                )
            else:
                data.update(
                    bytes=ui.read_bytes(result.best.path), filename=f"{ui.stem(uploaded)}_compressed.pdf",
                    mime="application/pdf", size=result.best.size,
                )
            ui.set_result("compress", uploaded, **data)
        except Exception as e:
            status.update(label=t("failed"), state="error")
            ui.show_error(e, "compress")

res = ui.get_result("compress", uploaded)
if res:
    c1, c2, c3 = st.columns(3)
    c1.metric(t("metric_original"), f"{res['original'] / 1e6:.1f} MB")
    c2.metric(t("metric_result"), f"{res['size'] / 1e6:.1f} MB")
    c3.metric(t("metric_saved"), f"{100 - res['size'] / res['original'] * 100:.0f}%")

    label = label_text(res["label"])
    if res.get("parts"):
        st.success(t("split_to_target_ok", n=len(res["parts"]), target=f"{res['target']:g}", label=label))
        for name, size in res["parts"]:
            st.write(f"- {name}: {size / 1e6:.2f} MB")
        if res["oversize"]:
            st.warning(t("oversize_pages", pages=", ".join(map(str, res["oversize"]))))
    elif res["kept_original"]:
        st.info(t("kept_original"))
    elif res["met"]:
        st.success(t("target_met", target=f"{res['target']:g}", label=label))
    else:
        st.warning(t("target_missed", target=f"{res['target']:g}", label=label))

    ui.download(res)

    st.subheader(t("compare_title", page=res["preview_page"] + 1))
    st.caption(t("compare_caption"))
    b1, b2 = st.columns(2)
    b1.image(res["before"], caption=t("before"), width="stretch")
    b2.image(res["after"], caption=t("after"), width="stretch")

    with st.expander(t("attempt_details")):
        for att_label, size, secs in res["attempts"]:
            st.write(f"- {label_text(att_label)}: {size / 1e6:.2f} MB ({secs:.0f} {t('seconds')})")
