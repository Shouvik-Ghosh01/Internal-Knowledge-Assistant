import os
from dotenv import load_dotenv

load_dotenv()

# DeepSeek (OpenAI-compatible)
OPENAI_API_KEY = os.getenv("DEEPSEEK_API_KEY")
OPENAI_API_BASE = "https://api.deepseek.com"
LLM_MODEL = "deepseek-chat"

# Pinecone
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV")
PINECONE_INDEX = "internal-knowledge-assistant"

# Retrieval
TOP_K = 4
SIMILARITY_THRESHOLD = 0.75

# Pinecone namespaces (one per doc type).
#
# We keep these as simple strings so:
# - ingestion can upsert into a predictable namespace
# - retrieval can query across all namespaces
# - the app can be extended with new doc-types by adding a constant here
NAMESPACE_LOCATORS = "locators"
NAMESPACE_VALIDATION = "validation"
NAMESPACE_PR_REVIEW = "pr_review"
NAMESPACE_SOP = "sop"

# List of namespaces that the retriever queries.
# If you add a new namespace above, also add it here.
ALL_NAMESPACES = [
	NAMESPACE_LOCATORS,
	NAMESPACE_VALIDATION,
	NAMESPACE_PR_REVIEW,
	NAMESPACE_SOP,
]
