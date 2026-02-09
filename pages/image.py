import streamlit as st
from PIL import Image
from io import BytesIO

if st.button("⬅ Home"):
    st.switch_page("app.py")

st.markdown("---")

st.set_page_config(page_title="Image to PDF", layout="centered")
st.title("🖼 Image → PDF (Print Ready)")

uploaded_images = st.file_uploader(
    "Upload image files",
    type=["png", "jpg", "jpeg", "bmp", "tiff"],
    accept_multiple_files=True
)

PAGE_SIZES = {
    "Original (image size)": None,
    "A4": (595, 842),
    "Letter": (612, 792)
}

page_size_option = st.selectbox(
    "PDF Page Size",
    list(PAGE_SIZES.keys())
)

# Standard print margin (25 mm ≈ 72 pt)
MARGIN = 72

if uploaded_images:
    images = []

    for img_file in uploaded_images:
        img = Image.open(img_file)

        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        images.append(img)

    st.success(f"{len(images)} image(s) ready")

    if st.button("Convert to PDF"):
        processed_images = []

        target_size = PAGE_SIZES[page_size_option]

        for img in images:
            if target_size:
                page_w, page_h = target_size

                # Printable area
                printable_w = page_w - 2 * MARGIN
                printable_h = page_h - 2 * MARGIN

                img_ratio = img.width / img.height
                printable_ratio = printable_w / printable_h

                if img_ratio > printable_ratio:
                    new_w = printable_w
                    new_h = int(printable_w / img_ratio)
                else:
                    new_h = printable_h
                    new_w = int(printable_h * img_ratio)

                img_resized = img.resize((new_w, new_h), Image.LANCZOS)

                page = Image.new("RGB", (page_w, page_h), "white")

                x = MARGIN + (printable_w - new_w) // 2
                y = MARGIN + (printable_h - new_h) // 2

                page.paste(img_resized, (x, y))
                processed_images.append(page)
            else:
                processed_images.append(img)

        pdf_buffer = BytesIO()
        processed_images[0].save(
            pdf_buffer,
            format="PDF",
            save_all=True,
            append_images=processed_images[1:]
        )

        pdf_buffer.seek(0)

        st.download_button(
            "⬇ Download PDF",
            pdf_buffer,
            file_name="images_to_pdf_print_ready.pdf",
            mime="application/pdf"
        )
