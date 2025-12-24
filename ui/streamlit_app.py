import streamlit as st
import requests

st.title("Internal Knowledge Assistant")

query = st.text_input("Ask a company question")

if query:
    res = requests.post("http://localhost:8000/ask", params={"query": query})
    data = res.json()

    st.write("### Answer")
    st.write(data["answer"])

    st.write("### Sources")
    for s in data["sources"]:
        st.write(s)
