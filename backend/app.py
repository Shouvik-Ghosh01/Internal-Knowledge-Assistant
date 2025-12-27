from fastapi import FastAPI
from backend.agent.agent import run_agent
from backend.safety.input_guard import is_query_allowed
from backend.safety.prompt_guard import is_prompt_safe

app = FastAPI()

@app.post("/ask")
def ask(query: str):

    # Rule-based input validation (fast, deterministic)
    if not is_query_allowed(query):
        return {
            "answer": "This query is outside the allowed scope.",
            "sources": []
        }

    # Semantic prompt-injection & jailbreak detection (Groq Prompt Guard)
    if not is_prompt_safe(query):
        return {
            "answer": "Query blocked due to unsafe or malicious intent.",
            "sources": []
        }

    # Run the agentic RAG pipeline
    return run_agent(query)