"""Office document -> PDF conversion with headless LibreOffice.

Every conversion uses its own LibreOffice profile (a temporary folder), so several users can convert at
the same time without locking each other out, and a time limit keeps odd files from hanging the server.
"""

from __future__ import annotations

import os
import shutil
import signal
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from .i18n import UserError

OFFICE_TYPES = ["docx", "doc", "odt", "rtf", "xlsx", "xls", "ods", "pptx", "ppt", "odp"]

_CANDIDATES = [
    "soffice",
    "libreoffice",
    r"C:\Program Files\LibreOffice\program\soffice.exe",
    "/Applications/LibreOffice.app/Contents/MacOS/soffice",
]


def find_soffice() -> Optional[str]:
    env = os.environ.get("PDFTOOLS_SOFFICE")
    for c in ([env] if env else []) + _CANDIDATES:
        path = shutil.which(c) or (c if os.path.isfile(c) else None)
        if path:
            return path
    return None


def office_to_pdf(in_path: str, out_dir: str, timeout: int = 180) -> str:
    soffice = find_soffice()
    if not soffice:
        raise UserError("libreoffice_missing")
    profile = tempfile.mkdtemp(prefix="lo_profile_")
    cmd = [
        soffice,
        f"-env:UserInstallation={Path(profile).as_uri()}",
        "--headless", "--norestore", "--nolockcheck", "--nodefault",
        "--convert-to", "pdf", "--outdir", out_dir, in_path,
    ]
    popen_kw = {"start_new_session": True} if os.name != "nt" else {
        "creationflags": subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]
    }
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **popen_kw)
    try:
        proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        if os.name != "nt":
            os.killpg(proc.pid, signal.SIGKILL)  # also kill the child process (soffice.bin)
        else:
            proc.kill()
        proc.communicate()
        raise
    finally:
        shutil.rmtree(profile, ignore_errors=True)
    out = os.path.join(out_dir, Path(in_path).stem + ".pdf")
    if not os.path.exists(out):
        raise UserError("office_convert_failed")
    return out
