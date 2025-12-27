from langchain.chat_models import ChatOpenAI
from langchain.agents import Tool, initialize_agent
from backend.config import *
from backend.agent.prompts import SYSTEM_PROMPT
from backend.rag.retriever import retrieve_chunks
from backend.utils.citation import extract_sources
from backend.safety.output_filter import is_safe_output
from backend.safety.llama_guard import is_safe_content


# -----------------------------
# LLM SETUP
# -----------------------------
llm = ChatOpenAI(
    model=LLM_MODEL,
    openai_api_key=OPENAI_API_KEY,
    openai_api_base=OPENAI_API_BASE,
    temperature=0
)

# -----------------------------
# RETRIEVER TOOL
# -----------------------------
def retriever_tool(query: str):
    results = retrieve_chunks(query)

    if not results:
        return "NO_CONTEXT"

    context = ""
    for r in results:
        context += f"""
Source: {r['source']} (Page {r.get('page', 'N/A')})
Content:
{r['text']}
"""

    return context


tools = [
    Tool(
        name="InternalKnowledgeRetriever",
        func=retriever_tool,
        description="Retrieves internal company documents for answering user queries"
    )
]

# -----------------------------
# AGENT INITIALIZATION
# -----------------------------
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent="zero-shot-react-description",
    verbose=True,
    system_message=SYSTEM_PROMPT
)

# -----------------------------
# MAIN AGENT EXECUTION
# -----------------------------
def run_agent(query: str):
    response = agent.run(query)

    # ---- No context fallback ----
    if "NO_CONTEXT" in response:
        return {
            "answer": "I don't know based on the available knowledge base.",
            "sources": []
        }

    # ---- Rule-based output filter ----
    if not is_safe_output(response):
        return {
            "answer": "Unable to provide a safe answer based on the available information.",
            "sources": []
        }

    # ---- LLaMA Guard output validation ----
    if not is_safe_content(response, content_type="assistant_output"):
        return {
            "answer": "Response blocked due to safety policy.",
            "sources": []
        }

    # ---- Final grounded answer ----
    return {
        "answer": response,
        "sources": extract_sources()
    }