"""Separate process for heavy jobs (OCR, PDF -> Word).

Started from the UI via pdftools.ui.run_worker. Progress is reported on stdout as "PROGRESS 0.42" lines.
A separate process can be timed out, gives its memory back as soon as it ends, and a crash on a
broken PDF cannot take the Streamlit server down with it.
"""

from __future__ import annotations

import argparse
import sys


def _progress(frac: float) -> None:
    print(f"PROGRESS {frac:.3f}", flush=True)


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("pdf2docx")
    s.add_argument("inp"); s.add_argument("out")
    s.add_argument("--pages", default="", help="comma-separated 0-based page indexes; empty = all")
    s = sub.add_parser("ocr-pdf")
    s.add_argument("inp"); s.add_argument("out"); s.add_argument("--lang", default="ind+eng")
    s.add_argument("--dpi", type=int, default=300); s.add_argument("--all-pages", action="store_true")
    s = sub.add_parser("ocr-docx")
    s.add_argument("inp"); s.add_argument("out"); s.add_argument("--lang", default="ind+eng")
    s.add_argument("--dpi", type=int, default=300)
    a = p.parse_args(argv)

    if a.cmd == "pdf2docx":
        from pdf2docx import Converter

        cv = Converter(a.inp)
        try:
            pages = [int(x) for x in a.pages.split(",") if x.strip()] or None
            cv.convert(a.out, pages=pages)
        finally:
            cv.close()
    elif a.cmd == "ocr-pdf":
        from pdftools.ocr import ocr_to_searchable_pdf

        n = ocr_to_searchable_pdf(a.inp, a.out, a.lang, a.dpi, not a.all_pages, _progress)
        print(f"RESULT {n}", flush=True)
    else:
        from pdftools.ocr import ocr_to_docx

        ocr_to_docx(a.inp, a.out, a.lang, a.dpi, _progress)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
