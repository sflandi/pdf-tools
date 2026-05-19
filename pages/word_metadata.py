import streamlit as st
import subprocess
import tempfile
import os
from io import BytesIO
from PyPDF2 import PdfReader, PdfWriter

st.set_page_config(page_title="Word to PDF", layout="centered")

# ---------------------------
# Session state
# ---------------------------
if "processing" not in st.session_state:
    st.session_state.processing = False

# ---------------------------
# Back button
# ---------------------------
if st.button("⬅ Kembali ke Halaman Utama", disabled=st.session_state.processing):
    st.switch_page("app.py")

st.markdown("---")
st.title("📄 Word → PDF (Custom Metadata)")
st.caption("Convert DOCX to PDF and set metadata")

# ---------------------------
# Upload DOCX
# ---------------------------
uploaded_file = st.file_uploader(
    "Upload Word file (.docx)",
    type=["docx"],
    disabled=st.session_state.processing
)

# ---------------------------
# Metadata input
# ---------------------------
st.subheader("Custom Metadata")

title = st.text_input("Title", disabled=st.session_state.processing)
author = st.text_input("Author", disabled=st.session_state.processing)
subject = st.text_input("Subject", disabled=st.session_state.processing)
keywords = st.text_input("Keywords", disabled=st.session_state.processing)
creator = st.text_input("Creator", disabled=st.session_state.processing)
producer = st.text_input("Producer", disabled=st.session_state.processing)

# ---------------------------
# Convert Button
# ---------------------------
convert_clicked = st.button(
    "📄 Convert to PDF",
    use_container_width=True,
    disabled=st.session_state.processing or not uploaded_file
)

# ---------------------------
# Logic
# ---------------------------
if convert_clicked:
    st.session_state.processing = True

    try:
        with st.spinner("⏳ Converting Word to PDF..."):
            original_name = os.path.splitext(uploaded_file.name)[0]
            output_filename = f"{original_name}.pdf"

            with tempfile.TemporaryDirectory() as tmpdir:
                input_docx = os.path.join(tmpdir, "input.docx")

                # save docx
                with open(input_docx, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                # convert via LibreOffice
                subprocess.run([
                    "soffice",
                    "--headless",
                    "--convert-to", "pdf",
                    "--outdir", tmpdir,
                    input_docx
                ], check=True)

                pdf_path = os.path.join(tmpdir, "input.pdf")

                if not os.path.exists(pdf_path):
                    raise FileNotFoundError("PDF not generated")

                # ---------------------------
                # Add metadata
                # ---------------------------
                reader = PdfReader(pdf_path)
                writer = PdfWriter()

                for page in reader.pages:
                    writer.add_page(page)

                metadata = {
                    "/Title": title,
                    "/Author": author,
                    "/Subject": subject,
                    "/Keywords": keywords,
                    "/Creator": creator,
                    "/Producer": producer,
                }

                writer.add_metadata(metadata)

                buffer = BytesIO()
                writer.write(buffer)
                buffer.seek(0)

                pdf_bytes = buffer.getvalue()

        st.success("✅ Conversion successful!")

        st.download_button(
            "⬇ Download PDF",
            pdf_bytes,
            file_name=output_filename,
            mime="application/pdf"
        )

    except subprocess.CalledProcessError:
        st.error("❌ LibreOffice conversion failed")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

    finally:
        st.session_state.processing = False