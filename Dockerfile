FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-ind \
    poppler-utils \
    libreoffice \
    libreoffice-writer \
    libreoffice-core \
    fonts-dejavu \
    fonts-liberation \
    fonts-freefont-ttf \
    ghostscript \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*
    
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8502

CMD ["streamlit", "run", "app.py", "--server.port=8502", "--server.address=0.0.0.0"]