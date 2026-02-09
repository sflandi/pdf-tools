import streamlit as st

st.set_page_config(page_title="PDF Tools", layout="centered")

st.title("📄 PDF Tools")
st.subheader("Choose your tool")

col1, col2 = st.columns(2)
col3, col4 = st.columns(2)

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
    # st.page_link("pages/merger.py", label="🔗 PDF Merger", use_container_width=True)
    if st.button("🔗 PDF Merger", use_container_width=True):
        st.switch_page("pages/merger.py")

with col2:
    # st.page_link("pages/splitter.py", label="✂️ PDF Splitter", use_container_width=True)
    if st.button("✂️ PDF Splitter", use_container_width=True):
        st.switch_page("pages/splitter.py")

with col3:
    # st.page_link("pages/compress.py", label="🗜 PDF Compress", use_container_width=True)
    if st.button("🗜 PDF Compress", use_container_width=True):
        st.switch_page("pages/compress.py")

with col4:
    # st.page_link("pages/image.py", label="🖼 Image → PDF", use_container_width=True)
    if st.button("🖼 Image → PDF", use_container_width=True):
        st.switch_page("pages/image.py")
