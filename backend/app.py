from fastapi import FastAPI
from pydantic import BaseModel
from backend.agent.agent import run_agent
from backend.safety.input_guard import is_query_allowed
from backend.safety.prompt_guard import is_prompt_safe

app = FastAPI()

class AskRequest(BaseModel):
    query: str

@app.post("/ask")
def ask(req: AskRequest):
    query = req.query

    # Rule-based input validation
    if not is_query_allowed(query):
        return {
            "answer": "This query is outside the allowed scope.",
            "sources": []
        }

    # Prompt injection / jailbreak detection
    if is_prompt_safe(query):
        return {
            "answer": "Query blocked due to unsafe or malicious intent.",
            "sources": []
        }
    
    # print(query)
    return run_agent(query)