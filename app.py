import streamlit as st

st.set_page_config(page_title="PDF Tools", layout="centered")

st.title("📄 PDF Tools")
st.subheader("Choose your tool")

col1, col2 = st.columns(2)
col3, col4 = st.columns(2)
col5, col6 = st.columns(2)
col7, col8 = st.columns(2)
col9, col10 = st.columns(2)

st.markdown("""
<style>
div.stButton > button {
    height: 20px;
    font-size: 22px;
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)

with col1:
    if st.button("🔗 PDF Merger", use_container_width=True):
        st.switch_page("pages/merger.py")

with col2:
    if st.button("✂️ PDF Splitter", use_container_width=True):
        st.switch_page("pages/splitter.py")

with col3:
    if st.button("🗜 PDF Compress", use_container_width=True):
        st.switch_page("pages/compress.py")

with col4:
    if st.button("🗜 PDF Compress PyMuPDF", use_container_width=True):
        st.switch_page("pages/compress_pymupdf.py")

with col5:
    if st.button("🖼 Image → PDF", use_container_width=True):
        st.switch_page("pages/image.py")

with col6:
    if st.button("📄 PDF → Word", use_container_width=True):
        st.switch_page("pages/word.py")

with col7:
    if st.button("📄 PDF → Word + OCR", use_container_width=True):
        st.switch_page("pages/word_ocr.py")

with col8:
    if st.button("📄 PDF Metadata", use_container_width=True):
        st.switch_page("pages/metadata.py")
        
with col9:
    if st.button("📄 Word → PDF + metadata", use_container_width=True):
        st.switch_page("pages/word_metadata.py")
        
with col10:
    if st.button("📄 PDF Unlock", use_container_width=True):
        st.switch_page("pages/unlock.py")
        