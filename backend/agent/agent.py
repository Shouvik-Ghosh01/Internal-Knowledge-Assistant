from langchain_openai import ChatOpenAI
from langchain_core.tools import Tool
from langchain.agents import create_agent

from backend.config import (
    LLM_MODEL,
    DEEPSEEK_API_KEY,
    DEEPSEEK_API_BASE,
)
from backend.agent.prompts import SYSTEM_PROMPT
from backend.rag.retriever import retrieve_chunks
from backend.utils.citation import extract_sources
from backend.safety.output_filter import is_safe_output


# -------------------------------------------------
# LLM SETUP
# -------------------------------------------------
llm = ChatOpenAI(
    model=LLM_MODEL,
    api_key=DEEPSEEK_API_KEY,
    api_base=DEEPSEEK_API_BASE,
    temperature=0
)


# -------------------------------------------------
# RETRIEVER TOOL
# -------------------------------------------------
def retriever_tool(query: str) -> str:
    """
    Tool used by the agent to retrieve relevant internal knowledge.
    Returns formatted context or the sentinel value 'NO_CONTEXT'.
    """

    results = retrieve_chunks(query)

    if not results:
        return "NO_CONTEXT"

    context_parts = []
    for r in results:
        context_parts.append(
            f"""
Source: {r['source']} (Page {r.get('page', 'N/A')})
Content:
{r['text']}
""".strip()
        )

    return "\n\n".join(context_parts)


tools = [
    Tool(
        name="InternalKnowledgeRetriever",
        func=retriever_tool,
        description=(
            "Retrieve relevant internal company documents. "
            "Use this tool whenever factual or procedural information is required."
        ),
    )
]


# -------------------------------------------------
# AGENT INITIALIZATION
# -------------------------------------------------
agent = create_agent(
    model=llm,
    tools=tools
)


# -------------------------------------------------
# MAIN AGENT EXECUTION
# -------------------------------------------------
def run_agent(query: str) -> dict:
    """
    Executes the agentic RAG pipeline and returns a grounded response.

    Safety assumptions:
    - Input validation and prompt-injection detection
      are already handled BEFORE this function is called.
    """

    response = agent.run(query)

    # -------------------------
    # NO CONTEXT FALLBACK
    # -------------------------
    if "NO_CONTEXT" in response:
        return {
            "answer": "I don't know based on the available knowledge base.",
            "sources": [],
        }

    # -------------------------
    # OUTPUT SAFETY FILTER
    # -------------------------
    if not is_safe_output(response):
        return {
            "answer": "Unable to provide a safe answer based on the available information.",
            "sources": [],
        }

    # -------------------------
    # FINAL GROUNDED ANSWER
    # -------------------------
    return {
        "answer": response,
        "sources": extract_sources(),
    }