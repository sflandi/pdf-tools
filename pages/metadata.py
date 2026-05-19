import streamlit as st
from PyPDF2 import PdfReader, PdfWriter
from io import BytesIO
import os

st.set_page_config(page_title="Edit PDF Metadata", layout="centered")

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
st.title("📝 Edit PDF Metadata")
st.caption("Modify Title, Author, Subject, etc.")

# ---------------------------
# Upload
# ---------------------------
uploaded_file = st.file_uploader(
    "Upload PDF file",
    type=["pdf"],
    disabled=st.session_state.processing
)

if uploaded_file:
    reader = PdfReader(uploaded_file)

    # Ambil metadata lama (jika ada)
    meta = reader.metadata or {}

    def get_meta(key):
        return meta.get(key, "") if meta.get(key) else ""

    def get_meta_safe(meta, key):
        val = meta.get(key)

        if val is None:
            return ""

        try:
            # resolve IndirectObject
            if hasattr(val, "get_object"):
                val = val.get_object()

            return str(val)
        except:
            return ""
    # ---------------------------
    # Form metadata
    # ---------------------------
    st.subheader("Edit Metadata")

    # title = st.text_input("Title", get_meta("/Title"))
    # author = st.text_input("Author", get_meta("/Author"))
    # subject = st.text_input("Subject", get_meta("/Subject"))
    # keywords = st.text_input("Keywords", get_meta("/Keywords"))
    # creator = st.text_input("Creator", get_meta("/Creator"))
    # producer = st.text_input("Producer", get_meta("/Producer"))
    
    title = st.text_input("Title", get_meta_safe(meta, "/Title"))
    author = st.text_input("Author", get_meta_safe(meta, "/Author"))
    subject = st.text_input("Subject", get_meta_safe(meta, "/Subject"))
    keywords = st.text_input("Keywords", get_meta_safe(meta, "/Keywords"))
    creator = st.text_input("Creator", get_meta_safe(meta, "/Creator"))
    producer = st.text_input("Producer", get_meta_safe(meta, "/Producer"))

    # ---------------------------
    # Button
    # ---------------------------
    save_clicked = st.button(
        "💾 Save Metadata",
        use_container_width=True,
        disabled=st.session_state.processing
    )

    if save_clicked:
        st.session_state.processing = True

        try:
            with st.spinner("⏳ Updating metadata..."):
                writer = PdfWriter()

                # copy semua halaman
                for page in reader.pages:
                    writer.add_page(page)

                # set metadata baru
                new_metadata = {
                    "/Title": title,
                    "/Author": author,
                    "/Subject": subject,
                    "/Keywords": keywords,
                    "/Creator": creator,
                    "/Producer": producer,
                }

                writer.add_metadata(new_metadata)

                # simpan ke memory
                output_buffer = BytesIO()
                writer.write(output_buffer)
                output_buffer.seek(0)

                # nama file output
                original_name = os.path.splitext(uploaded_file.name)[0]
                output_filename = f"{original_name}_metadata.pdf"

            st.success("✅ Metadata updated successfully!")

            st.download_button(
                "⬇ Download PDF",
                output_buffer,
                file_name=output_filename,
                mime="application/pdf"
            )

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

        finally:
            st.session_state.processing = False