import streamlit as st
from PyPDF2 import PdfMerger
import tempfile
import os

if st.button("⬅ Home"):
    st.switch_page("app.py")

st.markdown("---")

st.set_page_config(page_title="PDF Merger", layout="centered")

st.title("📄 PDF Merger")
st.write("Upload multiple PDF files and merge them into one.")

uploaded_files = st.file_uploader(
    "Upload PDF files",
    type="pdf",
    accept_multiple_files=True
)

if uploaded_files:
    st.write("### Files to merge:")
    for file in uploaded_files:
        st.write(f"- {file.name}")

    if st.button("Merge PDF"):
        merger = PdfMerger()

        try:
            for pdf in uploaded_files:
                merger.append(pdf)

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                merger.write(tmp_file.name)
                merged_path = tmp_file.name

            merger.close()

            with open(merged_path, "rb") as f:
                st.download_button(
                    label="⬇ Download Merged PDF",
                    data=f,
                    file_name="merged.pdf",
                    mime="application/pdf"
                )

        except Exception as e:
            st.error(f"Error: {e}")

        finally:
            if os.path.exists(merged_path):
                os.remove(merged_path)
