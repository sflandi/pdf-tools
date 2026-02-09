import streamlit as st
from PyPDF2 import PdfReader, PdfWriter
from io import BytesIO
import zipfile

if st.button("⬅ Home"):
    st.switch_page("app.py")

st.markdown("---")

st.set_page_config(page_title="PDF Splitter", layout="centered")
st.title("✂️ PDF Splitter → ZIP")

uploaded_file = st.file_uploader(
    "Upload a PDF file",
    type="pdf"
)

if uploaded_file:
    reader = PdfReader(uploaded_file)
    total_pages = len(reader.pages)
    base_name = uploaded_file.name.rsplit(".", 1)[0]

    st.success(f"Total pages detected: {total_pages}")

    if st.button("Split PDF to ZIP"):
        zip_buffer = BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for i, page in enumerate(reader.pages, start=1):
                writer = PdfWriter()
                writer.add_page(page)

                pdf_buffer = BytesIO()
                writer.write(pdf_buffer)
                pdf_buffer.seek(0)

                file_name = f"{base_name}_page_{i:02d}.pdf"
                zip_file.writestr(
                    file_name,
                    pdf_buffer.read()
                )

        zip_buffer.seek(0)

        st.download_button(
            label="⬇ Download ZIP",
            data=zip_buffer,
            file_name="split_pages.zip",
            mime="application/zip"
        )
