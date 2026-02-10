import streamlit as st
import tempfile
import os
from pdf2docx import Converter

if st.button("⬅ Home"):
    st.switch_page("app.py")

st.markdown("---")

st.set_page_config(page_title="PDF to Word Converter", page_icon="📄", layout="centered")
st.title("🗜 PDF to Word")

if "processing" not in st.session_state:
    st.session_state.processing = False

uploaded_file = st.file_uploader(
    "Upload PDF file",
    type=["pdf"],
    disabled=st.session_state.processing
)

convert_clicked = st.button(
    "📄 Convert to Word",
    disabled=st.session_state.processing or not uploaded_file
)

if convert_clicked:
  st.session_state.processing = True

  try:
    with st.spinner("⏳ Converting PDF to Word..."):
      original_name = os.path.splitext(uploaded_file.name)[0]
      output_filename = f"{original_name}.docx"

      with tempfile.TemporaryDirectory() as temp_dir:
        input_pdf = os.path.join(temp_dir, "input.pdf")
        output_word = os.path.join(temp_dir, output_filename)

        with open(input_pdf, "wb") as f:
          f.write(uploaded_file.getbuffer())

        cv = Converter(input_pdf)
        cv.convert(output_word, start=0, end=None)
        cv.close()

        if not os.path.exists(output_word):
          raise FileNotFoundError("Word file is not generated.")

        with open(output_word, "rb") as f:
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