"""Streamlit helpers shared by every page: language, login, job queue, temp files, results, errors, logging."""

from __future__ import annotations

import contextlib
import hmac
import json
import os
import subprocess
import sys
import threading
import time
from typing import Callable, Iterator, Optional

import streamlit as st

from . import compress as engine
from .core import PdfLocked
from .i18n import DEFAULT_LANG, LANGUAGES, UserError, tr

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAX_JOBS = int(os.environ.get("PDFTOOLS_MAX_JOBS", max(1, (os.cpu_count() or 2) // 2)))


# ---------------------------------------------------------------------------
# Language
# ---------------------------------------------------------------------------
def lang() -> str:
    """Current UI language: session > ?lang= in the URL > PDFTOOLS_LANG > English."""
    current = st.session_state.get("lang")
    if current not in LANGUAGES:
        current = st.query_params.get("lang")
        current = current if current in LANGUAGES else DEFAULT_LANG
        st.session_state["lang"] = current
    return current


def t(key: str, **params) -> str:
    """Translate a pdftools.i18n key into the current UI language."""
    return tr(key, lang(), **params)


def language_selector() -> None:
    """Sidebar language switch. The choice is also kept in the URL (?lang=id), so it survives a reload
    and links can be shared in a given language.

    The label is deliberately not translated and the widget has no key: the selection is applied by
    storing it and rerunning, so the widget is simply rebuilt with the new language preselected."""
    codes = list(LANGUAGES)
    current = lang()
    choice = st.sidebar.selectbox("🌐 Language / Bahasa", codes, index=codes.index(current), format_func=LANGUAGES.get)
    if st.query_params.get("lang") != current:
        st.query_params["lang"] = current
    if choice != current:
        st.session_state["lang"] = choice
        st.query_params["lang"] = choice
        st.rerun()


# ---------------------------------------------------------------------------
# Login (optional): enabled when the PDFTOOLS_PASSWORD environment variable is set
# ---------------------------------------------------------------------------
def require_auth() -> None:
    expected = os.environ.get("PDFTOOLS_PASSWORD", "")
    if not expected or st.session_state.get("_auth_ok"):
        return
    st.title(t("login_title"))
    with st.form("login"):
        pw = st.text_input(t("password"), type="password")
        ok = st.form_submit_button(t("login"), type="primary")
    if ok:
        if hmac.compare_digest(pw.encode(), expected.encode()):
            st.session_state["_auth_ok"] = True
            st.rerun()
        time.sleep(1.5)  # slow down password guessing
        log("login_failed")
        st.error(t("login_wrong"))
    st.stop()


# ---------------------------------------------------------------------------
# Queue for heavy jobs
# ---------------------------------------------------------------------------
@st.cache_resource
def _slots() -> threading.BoundedSemaphore:
    return threading.BoundedSemaphore(MAX_JOBS)


@contextlib.contextmanager
def heavy_job(status=None) -> Iterator[None]:
    """Limit how many heavy jobs run at once (the server is shared by many people)."""
    slots = _slots()
    waited = False
    while not slots.acquire(timeout=2):
        if status is not None and not waited:
            status.update(label=t("queue_wait"))
        waited = True
    try:
        yield
    finally:
        slots.release()


# ---------------------------------------------------------------------------
# Temporary files
# ---------------------------------------------------------------------------
@contextlib.contextmanager
def workdir() -> Iterator[str]:
    path = engine.make_workdir()
    try:
        yield path
    finally:
        engine.cleanup(path)


def save_upload(uploaded, folder: str, name: Optional[str] = None) -> str:
    # never use the uploaded file name as a path (it is user input)
    safe = name or "input" + os.path.splitext(uploaded.name)[1].lower()
    path = os.path.join(folder, safe)
    with open(path, "wb") as f:
        f.write(uploaded.getbuffer())
    return path


def stem(uploaded) -> str:
    return os.path.splitext(os.path.basename(uploaded.name))[0] or "document"


# ---------------------------------------------------------------------------
# Results: kept in the session so they survive the rerun triggered by the download button
# ---------------------------------------------------------------------------
def _signature(uploads) -> str:
    items = uploads if isinstance(uploads, list) else [uploads]
    return "|".join(f"{u.name}:{u.size}" for u in items if u is not None)


def set_result(key: str, uploads, **data) -> None:
    st.session_state[f"_result_{key}"] = {"sig": _signature(uploads), **data}


def get_result(key: str, uploads) -> Optional[dict]:
    res = st.session_state.get(f"_result_{key}")
    if not res or not uploads or res["sig"] != _signature(uploads):
        return None
    return res


def download(res: dict, label: Optional[str] = None) -> None:
    st.download_button(label or t("download"), res["bytes"], file_name=res["filename"], mime=res["mime"],
                       type="primary", width="stretch")


def read_bytes(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


# ---------------------------------------------------------------------------
# Separate worker process (OCR, PDF -> Word)
# ---------------------------------------------------------------------------
def run_worker(args: list[str], timeout: int, on_progress: Optional[Callable[[float], None]] = None) -> list[str]:
    """Run `python -m pdftools.worker ...`; progress is read from stdout. Returns the RESULT lines."""
    # stderr is merged into stdout: kept separate, a chatty child (e.g. pdf2docx logging) can fill the
    # stderr pipe and deadlock while we are reading stdout.
    proc = subprocess.Popen(
        [sys.executable, "-m", "pdftools.worker", *args], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
    )
    results: list[str] = []
    tail: list[str] = []
    deadline = time.monotonic() + timeout
    timer = threading.Timer(timeout, proc.kill)
    timer.start()
    try:
        assert proc.stdout is not None
        for line in proc.stdout:
            if line.startswith("PROGRESS ") and on_progress:
                on_progress(float(line.split()[1]))
            elif line.startswith("RESULT "):
                results.append(line[7:].strip())
            elif line.strip():
                tail = (tail + [line.strip()])[-5:]
        proc.wait()
    finally:
        timer.cancel()
    if time.monotonic() >= deadline and proc.returncode != 0:
        raise subprocess.TimeoutExpired(args, timeout)
    if proc.returncode != 0:
        raise RuntimeError(tail[-1] if tail else f"process failed (exit code {proc.returncode})")
    return results


# ---------------------------------------------------------------------------
# Layout & errors
# ---------------------------------------------------------------------------
def header(title_key: str, caption_key: str) -> None:
    st.title(t(title_key))
    st.caption(t(caption_key))


def show_error(e: Exception, tool: str) -> None:
    if isinstance(e, PdfLocked):
        st.error(t("err_locked", msg=t(e.key, **e.params)))
    elif isinstance(e, UserError):
        st.error(t("err_invalid", msg=t(e.key, **e.params)))
    elif isinstance(e, subprocess.TimeoutExpired):
        st.error(t("err_timeout"))
    else:
        st.error(t("err_generic", err=e))
    log("error", tool=tool, kind=type(e).__name__)


def log(event: str, **fields) -> None:
    """Log to stdout (visible in `docker logs`). Deliberately without file names or document content."""
    print(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "event": event, **fields}), flush=True)


@contextlib.contextmanager
def timed(tool: str, **fields) -> Iterator[None]:
    t0 = time.monotonic()
    yield
    log("done", tool=tool, seconds=round(time.monotonic() - t0, 1), **fields)
