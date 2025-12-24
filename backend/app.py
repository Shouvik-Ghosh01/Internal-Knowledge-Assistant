from fastapi import FastAPI
from backend.agent.agent import run_agent
from backend.safety.input_guard import is_safe_query

app = FastAPI()

@app.post("/ask")
def ask(query: str):
    if not is_safe_query(query):
        return {"answer": "Query not allowed.", "sources": []}

    return run_agent(query)
