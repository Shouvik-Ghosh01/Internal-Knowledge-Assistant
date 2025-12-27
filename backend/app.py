from fastapi import FastAPI
from backend.agent.agent import run_agent
from backend.safety.input_guard import is_query_allowed
from backend.safety.llama_guard import is_safe_content

app = FastAPI()

@app.post("/ask")
def ask(query: str):

    # Rule-based input validation
    if not is_query_allowed(query):
        return {
            "answer": "This query is outside the allowed scope.",
            "sources": []
        }

    # LLaMA Guard (semantic safety)
    if not is_safe_content(query, content_type="user_input"):
        return {
            "answer": "Query blocked due to safety concerns.",
            "sources": []
        }

    return run_agent(query)