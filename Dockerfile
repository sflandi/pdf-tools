FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata

# Tesseract: OCR language data (the OCR engine itself is built into PyMuPDF)
# LibreOffice: Office -> PDF. Carlito/Caladea fonts replace Calibri/Cambria so Office layouts do not shift.
RUN apt-get update && apt-get install -y --no-install-recommends \
        tesseract-ocr-ind tesseract-ocr-eng \
        libreoffice-writer libreoffice-calc libreoffice-impress \
        fonts-dejavu fonts-liberation fonts-crosextra-carlito fonts-crosextra-caladea \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --uid 10001 app
WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY --chown=app:app . .
USER app

EXPOSE 8502
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8502/_stcore/health', timeout=4)" || exit 1

CMD ["streamlit", "run", "app.py", "--server.port=8502", "--server.address=0.0.0.0"]
