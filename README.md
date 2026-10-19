# PDF Tools

A self-hosted web app (Streamlit) for everyday PDF work: compress, merge, split, convert, OCR, lock/unlock, redact and more. Files are processed on your own server and deleted right after processing. The interface is available in **English** and **Bahasa Indonesia** (switch in the sidebar).

## Features

| Group | Features |
|---|---|
| Size & format | **Compress to a target size**, PDF → images, images → PDF, PDF → Word, scanned PDF → Word (OCR), OCR to searchable PDF, Office → PDF |
| Organize pages | Merge, split (every N pages / by page range / by file size), reorder/delete/rotate pages, page numbers, watermark |
| Security | Unlock, lock (AES-256 + print/copy/edit permissions), redact (ID numbers, tax IDs, emails, phone numbers, free text), edit/remove metadata |

### How compression works

You enter a target size (e.g. 10 MB). The engine (`pdftools/compress.py`) stops at the first step that meets it:

1. **Lossless**: remove duplicate objects (the same image stored many times), subset fonts, clean up the structure. Quality does not change.
2. **Images**: every image is resized (Lanczos) to exactly its displayed size on the page and stored as JPEG. A binary search picks the **highest** DPI/quality level that still fits. Text and vector graphics are never turned into images, so they stay sharp and copyable.
3. **MRC** (Mixed Raster Content): only for pages with very heavy vector graphics (e.g. PowerPoint halftone dot backgrounds). The background is rendered into one image while the text stays vector on top.
4. If it still doesn't fit, the user chooses: lower the image quality down to 72 DPI (one file), or split into several files that are each under the target.

Example (77-slide presentation): 129.7 MB → 9.7 MB as one file, or two files (9.9 MB + 4.3 MB) at 100 DPI.

The result and a before/after preview are shown so the quality can be checked before downloading.

## Running

### Docker (recommended for servers)

```bash
docker compose up -d --build
```

Open `http://<server>:8502`. The image includes LibreOffice (Office → PDF) and Tesseract language data for Indonesian and English (OCR).

### Locally (Windows / Linux / macOS)

Requires Python 3.11 or newer. Run all commands from the repository folder.

**Windows (PowerShell)**

```powershell
git clone https://github.com/opisboy29/pdf-tools.git
cd pdf-tools
py -m venv venv-pdf-tools
.\venv-pdf-tools\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py --server.port 8502
```

If `Activate.ps1` is blocked ("running scripts is disabled"), first run `Set-ExecutionPolicy -Scope Process Bypass` in the same PowerShell window.

**Linux / macOS**

```bash
git clone https://github.com/opisboy29/pdf-tools.git
cd pdf-tools
python3 -m venv venv-pdf-tools
source venv-pdf-tools/bin/activate
pip install -r requirements.txt
streamlit run app.py --server.port 8502
```

Then open `http://localhost:8502`. Stop it with `Ctrl+C`. To run it again later, go to the repository folder, activate the venv and run `streamlit run app.py --server.port 8502`. If port 8502 is taken, pick another one (e.g. `--server.port 8503`).

Compress, merge, split, image conversion, PDF → Word, lock/unlock, redact and metadata work without any extra programs. Two features need programs outside Python:

- **OCR**: Tesseract language files (`ind.traineddata`, `eng.traineddata`). On Debian/Ubuntu: `sudo apt install tesseract-ocr-ind tesseract-ocr-eng`. Another location can be set with `TESSDATA_PREFIX`.
- **Office → PDF**: LibreOffice. On Debian/Ubuntu: `sudo apt install libreoffice-writer libreoffice-calc libreoffice-impress`.

If they are missing, the related pages show a message and everything else keeps working.

## Configuration (environment variables)

| Variable | Default | Purpose |
|---|---|---|
| `PDFTOOLS_LANG` | `en` | Default UI language (`en` or `id`); users can still switch in the sidebar |
| `PDFTOOLS_PASSWORD` | empty | When set, the app asks for this password before it can be used |
| `PDFTOOLS_MAX_JOBS` | half the CPU count | How many heavy jobs (compression, OCR, conversion) may run at once; the rest wait in a queue |
| `PDFTOOLS_TMP` | system temp folder | Where temporary files go (point it to a roomy disk for large files) |
| `PDFTOOLS_MAX_RENDER_PIXELS` | 60,000,000 | Pixel limit per page for PDF → images |
| `PDFTOOLS_MAX_IMAGE_PIXELS` | 200,000,000 | Pixel limit for uploaded images (decompression-bomb protection) |
| `TESSDATA_PREFIX` | auto-detected | Folder with the Tesseract language files |
| `PDFTOOLS_SOFFICE` | auto-detected | Path to `soffice` if it is not on the PATH |

The upload limit (1 GB) is set in `.streamlit/config.toml`.

## Security

- Files only live in a temporary folder while they are processed and are deleted afterwards. Logs record the feature, size and duration only, never file names or document content.
- Heavy work runs in separate processes with time limits, so a broken or huge PDF cannot hang the server.
- LibreOffice uses a separate profile per conversion and is killed when it exceeds its time limit.
- Streamlit usage statistics are disabled; the developer menu and error details are hidden.
- The container runs as a non-root user, without extra Linux capabilities, with memory and CPU limits.
- Locking a PDF without an owner password uses a random one, so the permissions cannot be lifted with the user password.
- The app does **not** provide HTTPS itself. If it is reachable outside your internal network, put it behind a reverse proxy with HTTPS and set `PDFTOOLS_PASSWORD`.

## Project layout

```
app.py               navigation, language switch & home page
pages/               one file per feature (UI only)
pdftools/core.py     PDF operations (merge, split, redact, protect, ...)
pdftools/compress.py compression engine (also usable from the command line)
pdftools/ocr.py      OCR (Tesseract built into PyMuPDF)
pdftools/office.py   Office -> PDF (LibreOffice)
pdftools/worker.py   separate process for OCR & PDF -> Word
pdftools/i18n.py     all UI text in English and Indonesian
pdftools/ui.py       Streamlit helpers: language, login, queue, results, errors, logging
tests/               pytest
```

To add a UI language or a new string, edit `pdftools/i18n.py`; `tests/test_i18n.py` fails if any text key used in the code is missing a translation.

Compress from the command line (e.g. for many files at once):

```bash
python -m pdftools.compress compress input.pdf output.pdf --target-mb 10 --aggressive
```

## Tests

```bash
pip install -r requirements-dev.txt
pytest -q
```

The tests generate their own sample PDFs (no real documents needed). The OCR and Office → PDF tests only run when Tesseract / LibreOffice are installed.

## Library licenses

PyMuPDF is licensed under AGPL-3.0. That is fine for an internal tool, but review it before distributing the app or offering it to outside users.
