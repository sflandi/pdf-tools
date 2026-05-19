import streamlit as st
import tempfile
import os
from pdf2image import convert_from_path
import pytesseract
from docx import Document
import re
import cv2
import numpy as np

if st.button("⬅ Home"):
    st.switch_page("app.py")

st.markdown("---")

st.set_page_config(page_title="PDF to Word OCR Converter", page_icon="📄", layout="centered")
st.title("🗜 PDF to Word + OCR")

if "processing" not in st.session_state:
    st.session_state.processing = False

uploaded_file = st.file_uploader(
    "Upload PDF file",
    type=["pdf"],
    disabled=st.session_state.processing
)

ocr_lang = st.selectbox(
    "OCR Language",
    ["eng", "ind"],
    index=1,
    disabled=st.session_state.processing
)

convert_clicked = st.button(
    "📄 Convert to Word with OCR",
    disabled=st.session_state.processing or not uploaded_file
)

def preprocess_image(pil_img):
    img = np.array(pil_img)

    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    # remove noise
    img = cv2.medianBlur(img, 3)

    # adaptive threshold (SUPER IMPORTANT)
    img = cv2.adaptiveThreshold(
        img, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31, 10
    )

    return img

def hard_clean(text):
    clean_lines = []
    for line in text.splitlines():
        line = line.strip()

        if not line:
            clean_lines.append("")
            continue

        # skip if too many symbols
        if len(re.findall(r"[A-Za-z0-9]", line)) < len(line) * 0.5:
            continue

        # skip garbage patterns
        if re.search(r"[|£€¥]{2,}", line):
            continue

        clean_lines.append(line)

    return "\n".join(clean_lines)

def paragraphs(text):
    blocks = []
    buffer = []

    for line in text.splitlines():
        if line.strip() == "":
            if buffer:
                blocks.append(" ".join(buffer))
                buffer = []
        else:
            buffer.append(line)

    if buffer:
        blocks.append(" ".join(buffer))

    return blocks

custom_config = r"""
--oem 3
--psm 4
-c textord_heavy_nr=1
-c textord_min_linesize=2.5
"""

if convert_clicked:
  st.session_state.processing = True

  try:
    with st.spinner("⏳ Converting PDF to Word with OCR..."):
      original_name = os.path.splitext(uploaded_file.name)[0]
      output_filename = f"{original_name}_ocr.docx"

      with tempfile.TemporaryDirectory() as temp_dir:
        input_pdf = os.path.join(temp_dir, "input.pdf")
        output_word_ocr = os.path.join(temp_dir, output_filename)

        with open(input_pdf, "wb") as f:
          f.write(uploaded_file.getbuffer())

        images = convert_from_path(
            input_pdf,
            dpi=300,
            fmt="png",
            grayscale=True
        )

        if not images:
          raise ValueError("❌ No images generated from PDF")

        doc = Document()
        for page in images:
            img = preprocess_image(page)
            raw = pytesseract.image_to_string(
                img,
                lang='eng' if ocr_lang == "English" else 'ind',
                config=custom_config
            )

            cleaned = hard_clean(raw)
            paras = paragraphs(cleaned)

            for p in paras:
                doc.add_paragraph(p)

        doc.save(output_word_ocr)

        if not os.path.exists(output_word_ocr):
          raise FileNotFoundError("❌ Word file is not generated.")

        with open(output_word_ocr, "rb") as f:
          docx_bytes = f.read()

    st.success("✅ Conversion successful!")
    st.download_button(
        label="📥 Download Word file",
        data=docx_bytes,
        file_name=output_filename,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

  except Exception as e:
    st.error(f"❌ Error: {str(e)}")

  finally:
    st.session_state.processing = False