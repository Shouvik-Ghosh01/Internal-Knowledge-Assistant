import streamlit as st
import requests
from requests.exceptions import ConnectionError, Timeout

# Backend endpoint (same /ask contract).
# If you want to run locally, change this to: "http://127.0.0.1:8000/ask"
API_URL = "https://internal-knowledge-assistant-9v2j.onrender.com/ask"

# -------------------------------
# PAGE CONFIG
# -------------------------------
st.set_page_config(
    # Browser tab title
    page_title="Spotline Knowledge Assistant",
    page_icon="📘",
        layout="wide",
)

# Hero header (modern, theme-aware). Keeps the app readable on wide screens.
st.markdown(
        """
        <style>
            /* Keep content from stretching too wide */
            .block-container {
                max-width: 1100px;
                padding-top: 1.25rem;
            }

            .ska-hero {
                border: 1px solid color-mix(in srgb, var(--text-color) 18%, transparent);
                background: var(--secondary-background-color);
                border-radius: 18px;
                padding: 14px 16px;
                margin-bottom: 0.75rem;
            }
            .ska-hero h1 {
                margin: 0;
                font-size: 1.65rem;
                line-height: 1.25;
            }
            .ska-muted {
                opacity: 0.82;
                margin-top: 0.25rem;
            }
            .ska-small {
                opacity: 0.78;
                margin-top: 0.35rem;
                font-size: 0.9rem;
            }

            /* Sidebar cards */
            section[data-testid="stSidebar"] .ska-sidecard {
                border: 1px solid color-mix(in srgb, var(--text-color) 14%, transparent);
                background: var(--secondary-background-color);
                border-radius: 14px;
                padding: 10px 12px;
                margin-bottom: 0.75rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
)

st.markdown(
        """
        <div class="ska-hero">
            <h1>📘 Spotline Knowledge Assistant</h1>
            <div class="ska-muted">Ask questions from Spotline SOPs, PR review checklist, validation checklist, and UI locators.</div>
            <div class="ska-small"><b>Tip:</b> Ask specific questions like “before raising PR” or “locator for login button”.</div>
            <div class="ska-small"><b>Try:</b> “What checks should I do before raising a PR?” · “How to verify a report?” · “Locator for submit button?”</div>
        </div>
        """,
        unsafe_allow_html=True,
)

# Chat "bubble" styling (theme-aware).
# Uses Streamlit theme variables instead of hard-coded colors.
st.markdown(
        """
        <style>
            /* Chat bubble styling.
                 Streamlit has changed its internal DOM a few times, so we target both
                 stChatMessage and stChatMessageContent. */
            :root {
                --ska-bubble-border: color-mix(in srgb, var(--text-color) 22%, transparent);
                /* Slight tint from theme variables so it looks like a bubble even when
                     secondary background matches the page background. */
                --ska-bubble-bg: color-mix(in srgb, var(--background-color) 92%, var(--text-color) 8%);
            }

            @keyframes ska-bubble-in {
                from { opacity: 0; transform: translateY(6px); }
                to { opacity: 1; transform: translateY(0); }
            }

            /* Apply bubble styling to the *content* block (best visual result). */
            div[data-testid="stChatMessageContent"] {
                border: 1px solid var(--ska-bubble-border) !important;
                border-radius: 18px !important;
                padding: 12px 14px !important;
                margin: 6px 0 !important;
                background: var(--ska-bubble-bg) !important;
                animation: ska-bubble-in 160ms ease-out;
            }

            /* Reduce extra vertical whitespace inside bubble */
            div[data-testid="stChatMessageContent"] > div {
                padding-top: 0.25rem !important;
                padding-bottom: 0.25rem !important;
            }

            /* Keep captions compact inside bubbles */
            div[data-testid="stChatMessage"] small,
            div[data-testid="stChatMessageContent"] small {
                opacity: 0.85 !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
)


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def _display_source(src: str) -> tuple[str, str]:
    """Return (label, full_src).

    The backend currently returns sources as strings. We display a compact label
    (e.g., filename) while still allowing users to see the full string.
    """

    s = (src or "").strip()
    if not s:
        return ("Unknown source", "")

    # If it looks like a path/URL, show the last segment as label.
    for sep in ["/", "\\"]:
        if sep in s:
            label = s.rstrip(sep).split(sep)[-1]
            return (label or s, s)

    return (s, s)


def _call_backend(api_url: str, query: str) -> dict:
    """Call the backend /ask endpoint.

    Backend contract (unchanged): POST {"query": "..."} -> {"answer": "...", "sources": [...]}
    """

    payload = {"query": query}

    try:
        res = requests.post(api_url, json=payload, timeout=30)
        if res.status_code != 200:
            return {
                "answer": f"Backend error (status {res.status_code}). Please try again.",
                "sources": [],
                "_error": True,
            }
        data = res.json() if res.content else {}
        return {
            "answer": data.get("answer", "No answer returned."),
            "sources": data.get("sources", []) or [],
        }
    except Timeout:
        return {"answer": "⏳ The request timed out. Please try again.", "sources": [], "_error": True}
    except ConnectionError:
        return {
            "answer": "🚫 Backend is not reachable. Please try again.",
            "sources": [],
            "_error": True,
        }


api_url = API_URL

# Simple in-memory chat history stored in Streamlit session state.
# Note: This is UI history only. The backend still receives only the latest user query.
if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.markdown('<div class="ska-sidecard">', unsafe_allow_html=True)
    st.subheader("Spotline")
    st.caption("Internal Q&A over SOPs, checklists, and UI locators.")
    st.markdown("**Try asking**")
    st.markdown(
        "\n".join(
            [
                "- What checks should I do before raising a PR?",
                "- How to verify a report?",
                "- Locator for the login button?",
                "- What is the expected result for <scenario>?",
            ]
        )
    )

    if st.button("Clear chat"):
        st.session_state.messages = []
        st.rerun()

    st.caption(f"Backend: {api_url}")
    st.markdown("</div>", unsafe_allow_html=True)

# Render chat message history (user + assistant messages).
for idx, message in enumerate(st.session_state.messages):
    role = message.get("role", "assistant")
    with st.chat_message(role):
        st.write(message.get("content", ""))

        sources = message.get("sources") or []
        if role == "assistant":
            sources = [str(s) for s in sources if s is not None and str(s).strip()]
            sources = _dedupe_preserve_order(sources)

            if sources:
                with st.expander("Sources"):
                    for src in sources:
                        label, full_src = _display_source(src)
                        st.markdown(f"- **{label}**")
                        if full_src and full_src != label:
                            st.caption(full_src)
            else:
                st.caption("No sources returned.")


# Chat input (sends the latest prompt to backend).
prompt = st.chat_input("Ask a question…")
if prompt:
    user_query = prompt.strip()
    if not user_query:
        st.warning("Please enter a question.")
    else:
        st.session_state.messages.append({"role": "user", "content": user_query})

        with st.spinner("🔍 Searching internal knowledge..."):
            try:
                data = _call_backend(api_url, user_query)
            except Exception as exc:
                data = {"answer": f"Unexpected error: {exc}", "sources": [], "_error": True}

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": data.get("answer", "No answer returned."),
                "sources": data.get("sources", []) or [],
                "_error": bool(data.get("_error")),
            }
        )

        st.rerun()
