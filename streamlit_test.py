import streamlit as st

st.set_page_config(page_title="Test App", page_icon="🧪")

st.title("🧪 Streamlit Test")
st.write("If you can see this, Streamlit is working!")

if st.button("Test Button"):
    st.success("Button works!")