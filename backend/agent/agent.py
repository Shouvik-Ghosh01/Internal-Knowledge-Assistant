from langchain.chat_models import ChatOpenAI
from langchain.agents import Tool, initialize_agent
from backend.config import *
from backend.agent.prompts import SYSTEM_PROMPT
from backend.rag.retriever import retrieve_chunks
from backend.utils.citation import extract_sources

llm = ChatOpenAI(
    model=LLM_MODEL,
    openai_api_key=OPENAI_API_KEY,
    openai_api_base=OPENAI_API_BASE,
    temperature=0
)

def retriever_tool(query: str):
    results = retrieve_chunks(query)
    if not results:
        return "NO_CONTEXT"

    context = ""
    for r in results:
        context += f"""
Source: {r['source']} (Page {r['page']})
Content: {r['text']}
"""
    return context

tools = [
    Tool(
        name="InternalKnowledgeRetriever",
        func=retriever_tool,
        description="Retrieves internal company documents"
    )
]

agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent="zero-shot-react-description",
    verbose=True,
    system_message=SYSTEM_PROMPT
)

def run_agent(query: str):
    response = agent.run(query)

    if "NO_CONTEXT" in response:
        return {
            "answer": "I don't know based on the available knowledge base.",
            "sources": []
        }

    return {
        "answer": response,
        "sources": extract_sources()
    }
