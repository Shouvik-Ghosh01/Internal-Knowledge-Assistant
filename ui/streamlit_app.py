import streamlit as st
import requests
from requests.exceptions import ConnectionError, Timeout

API_URL = "https://internal-knowledge-assistant-9v2j.onrender.com/ask"

# -------------------------------
# PAGE CONFIG
# -------------------------------
st.set_page_config(
    page_title="Internal Knowledge Assistant",
    page_icon="📘",
    layout="centered",
)

st.title("📘 Internal Knowledge Assistant")
st.caption("Ask questions based on internal SOPs, PR checklists, validations, and locators.")

# -------------------------------
# INPUT SECTION
# -------------------------------
with st.form(key="query_form", clear_on_submit=False):
    query = st.text_input(
        "Your question",
        placeholder="e.g. What checks should I do before raising a PR?",
    )
    submitted = st.form_submit_button("Submit")

# -------------------------------
# RESPONSE SECTION
# -------------------------------
if submitted:
    if not query.strip():
        st.warning("Please enter a question.")
    else:
        with st.spinner("🔍 Searching internal knowledge..."):
            try:
                res = requests.post(
                    API_URL,
                    json={"query": query},
                    timeout=30,
                )

                if res.status_code != 200:
                    st.error(
                        f"Backend error (status {res.status_code}). Please try again."
                    )
                else:
                    data = res.json()

                    # -------------------------------
                    # ANSWER
                    # -------------------------------
                    st.subheader("✅ Answer")
                    st.write(data.get("answer", "No answer returned."))

                    # -------------------------------
                    # SOURCES
                    # -------------------------------
                    sources = data.get("sources", [])
                    if sources:
                        st.subheader("📚 Sources")
                        for src in sources:
                            st.markdown(f"- **{src}**")
                    else:
                        st.info("No sources were used for this response.")

            except Timeout:
                st.error("⏳ The request timed out. Please try again.")
            except ConnectionError:
                st.error(
                    "🚫 Backend is not running.\n\n"
                    "Start FastAPI using:\n\n"
                    "`uvicorn backend.app:app --reload`"
                )
            except Exception as e:
                st.error(f"Unexpected error: {e}")