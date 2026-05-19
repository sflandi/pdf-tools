import streamlit as st
from PyPDF2 import PdfReader, PdfWriter
from io import BytesIO
import os

st.set_page_config(page_title="Unlock PDF", layout="centered")

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
st.title("🔓 Unlock PDF")
st.caption("Remove password protection from PDF")

# ---------------------------
# Upload
# ---------------------------
uploaded_file = st.file_uploader(
    "Upload protected PDF",
    type=["pdf"],
    disabled=st.session_state.processing
)

# ---------------------------
# Password input
# ---------------------------
password = st.text_input(
    "Password",
    type="password",
    disabled=st.session_state.processing
)

# ---------------------------
# Button
# ---------------------------
unlock_clicked = st.button(
    "🔓 Unlock PDF",
    use_container_width=True,
    disabled=st.session_state.processing or not uploaded_file
)

# ---------------------------
# Logic
# ---------------------------
if unlock_clicked:
    st.session_state.processing = True

    try:
        with st.spinner("⏳ Unlocking PDF..."):
            reader = PdfReader(uploaded_file)

            # cek apakah encrypted
            if reader.is_encrypted:
                if not password:
                    raise ValueError("Password required")

                result = reader.decrypt(password)

                if result == 0:
                    raise ValueError("Wrong password")
            else:
                st.info("ℹ️ PDF is not password protected")

            writer = PdfWriter()

            # copy semua halaman
            for page in reader.pages:
                writer.add_page(page)

            # simpan ke memory
            buffer = BytesIO()
            writer.write(buffer)
            buffer.seek(0)

            # nama file
            original_name = os.path.splitext(uploaded_file.name)[0]
            output_filename = f"{original_name}_unlocked.pdf"

        st.success("✅ PDF unlocked successfully!")

        st.download_button(
            "⬇ Download Unlocked PDF",
            buffer,
            file_name=output_filename,
            mime="application/pdf"
        )

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

    finally:
        st.session_state.processing = False