import streamlit as st
from PyPDF2 import PdfReader, PdfWriter
from io import BytesIO

if st.button("⬅ Home"):
    st.switch_page("app.py")

st.markdown("---")

st.set_page_config(page_title="PDF Compress", layout="centered")
st.title("🗜 PDF Compress")

uploaded_file = st.file_uploader("Upload PDF file", type="pdf")

if uploaded_file:
    reader = PdfReader(uploaded_file)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    # Optional compression (version-safe)
    if hasattr(writer, "compress_content_streams"):
        writer.compress_content_streams()

    output_buffer = BytesIO()
    writer.write(output_buffer)
    output_buffer.seek(0)

    original_size = uploaded_file.size / 1024
    compressed_size = len(output_buffer.getvalue()) / 1024

    st.write(f"📄 Original size: **{original_size:.2f} KB**")
    st.write(f"🗜 Compressed size: **{compressed_size:.2f} KB**")

    st.download_button(
        "⬇ Download Compressed PDF",
        output_buffer,
        file_name=f"compressed_{uploaded_file.name}",
        mime="application/pdf"
    )
