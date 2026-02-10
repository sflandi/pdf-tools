import streamlit as st
import subprocess
import tempfile
import os
from io import BytesIO

if st.button("⬅ Home"):
    st.switch_page("app.py")

st.markdown("---")

st.set_page_config(page_title="PDF Compress", layout="centered")
st.title("🗜 PDF Compress (Ghostscript)")

# ---------------------------
# Session state
# ---------------------------
if "processing" not in st.session_state:
    st.session_state.processing = False

# ---------------------------
# Upload
# ---------------------------
uploaded_file = st.file_uploader(
    "Upload PDF file",
    type=["pdf"],
    disabled=st.session_state.processing
)

# ---------------------------
# Presets
# ---------------------------
PDF_PRESETS = {
    "High compression (smallest size)": "/screen",
    "Medium compression (recommended)": "/ebook",
    "Print quality": "/printer",
    "High quality (prepress)": "/prepress"
}

preset_label = st.selectbox(
    "Compression level",
    list(PDF_PRESETS.keys()),
    index=1,
    disabled=st.session_state.processing
)

# ---------------------------
# Button
# ---------------------------
compress_clicked = st.button(
    "🗜 Compress PDF",
    disabled=st.session_state.processing or not uploaded_file
)

# ---------------------------
# Compress logic
# ---------------------------
if compress_clicked:
    st.session_state.processing = True

    try:
        with st.spinner("⏳ Compressing PDF, please wait..."):
            # Ambil nama file asli TANPA .pdf
            original_name = os.path.splitext(uploaded_file.name)[0]
            output_filename = f"{original_name}_compressed.pdf"
            # === TEMP DIR START ===
            with tempfile.TemporaryDirectory() as tmpdir:

                input_pdf = os.path.join(tmpdir, "input.pdf")
                output_pdf = os.path.join(tmpdir, output_filename)

                # Save uploaded file
                with open(input_pdf, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                original_size = os.path.getsize(input_pdf)

                # Ghostscript command
                command = [
                    "gs",
                    "-sDEVICE=pdfwrite",
                    "-dCompatibilityLevel=1.4",
                    f"-dPDFSETTINGS={PDF_PRESETS[preset_label]}",
                    "-dNOPAUSE",
                    "-dQUIET",
                    "-dBATCH",
                    f"-sOutputFile={output_pdf}",
                    input_pdf
                ]

                subprocess.run(command, check=True)

                if not os.path.exists(output_pdf):
                    raise FileNotFoundError("Compressed PDF not generated")

                compressed_size = os.path.getsize(output_pdf)

                # 🔥 CRITICAL FIX:
                # Read file into memory BEFORE temp dir is destroyed
                with open(output_pdf, "rb") as f:
                    pdf_bytes = f.read()

            # === TEMP DIR END (SAFE) ===

        # ---------------------------
        # UI Output (AFTER tempdir)
        # ---------------------------
        st.success("✅ Compression successful!")
        st.write(f"📄 Original size: **{original_size / 1024:.2f} KB**")
        st.write(f"🗜 Compressed size: **{compressed_size / 1024:.2f} KB**")
        st.write(
            f"📉 Reduction: **{100 - (compressed_size / original_size * 100):.1f}%**"
        )

        st.download_button(
            "⬇ Download Compressed PDF",
            pdf_bytes,
            file_name=output_filename,
            mime="application/pdf"
        )

    except subprocess.CalledProcessError as e:
        st.error("❌ Ghostscript failed")
        st.code(" ".join(e.cmd))

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

    finally:
        st.session_state.processing = False
