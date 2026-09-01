import streamlit as st
import pymupdf
import tempfile
import os

st.set_page_config(
    page_title="PDF Compress PyMuPDF",
    layout="centered"
)

if st.button("⬅ Home"):
    st.switch_page("app.py")

st.markdown("---")

st.title("🗜 PDF Compress (PyMuPDF)")

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
            output_filename = f"{original_name}_pymu_compressed.pdf"

            # ---------------------------
            # Temporary directory
            # ---------------------------
            with tempfile.TemporaryDirectory() as tmpdir:

                input_pdf = os.path.join(tmpdir, "input.pdf")
                output_pdf = os.path.join(tmpdir, output_filename)

                # Save uploaded file
                with open(input_pdf, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                # Original size
                original_size = os.path.getsize(input_pdf)

                # ---------------------------
                # PyMuPDF compression
                # ---------------------------
                doc = pymupdf.open(input_pdf)

                doc.save(
                    output_pdf,
                    garbage=4,
                    clean=True,
                    deflate=True,
                )

                doc.close()

                # Check output
                if not os.path.exists(output_pdf):
                    raise FileNotFoundError(
                        "Compressed PDF not generated"
                    )

                compressed_size = os.path.getsize(output_pdf)

                # Read file BEFORE tempdir destroyed
                with open(output_pdf, "rb") as f:
                    pdf_bytes = f.read()

        # ---------------------------
        # UI Output
        # ---------------------------

        st.success("✅ Compression successful!")

        st.write(
            f"📄 Original size: "
            f"**{original_size / 1024:.2f} KB**"
        )

        st.write(
            f"🗜 Compressed size: "
            f"**{compressed_size / 1024:.2f} KB**"
        )

        reduction = (
            100 - (compressed_size / original_size * 100)
        )

        if reduction > 0:
            st.write(
                f"📉 Reduction: **{reduction:.1f}%**"
            )
        else:
            st.warning(
                f"⚠️ File became larger by "
                f"{abs(reduction):.1f}%"
            )

        st.download_button(
            "⬇ Download Compressed PDF",
            pdf_bytes,
            file_name=output_filename,
            mime="application/pdf"
        )

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

    finally:
        st.session_state.processing = False