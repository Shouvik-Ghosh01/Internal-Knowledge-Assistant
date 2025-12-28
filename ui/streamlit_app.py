import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000/ask"

st.title("Internal Knowledge Assistant")

query = st.text_input("Ask a question")

if st.button("Submit") and query:
    try:
        res = requests.post(
            API_URL,
            json={"query": query},  # ✅ JSON body
            timeout=30
        )
        data = res.json()
        print(data)
        st.subheader("Answer")
        st.write(data.get("answer", "No answer returned"))

        if data.get("sources"):
            st.subheader("Sources")
            for s in data["sources"]:
                st.write(s)

    except requests.exceptions.ConnectionError:
        st.error("Backend is not running. Start FastAPI first.")