import os
from dotenv import load_dotenv

load_dotenv()

# -------------------------------------------------
# LLM CONFIGURATION (DeepSeek - OpenAI compatible)
# -------------------------------------------------
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_BASE = "https://openrouter.ai/api/v1"
LLM_MODEL = "gpt-5-nano-2025-08-07"

# -------------------------------------------------
# EMBEDDING CONFIGURATION (1536-dim)
# -------------------------------------------------
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION: int = 1536
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_BASE = "https://api.openai.com/v1"

# -------------------------------------------------
# PINECONE CONFIGURATION
# -------------------------------------------------
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV")
PINECONE_INDEX = "internal-knowledge-assistant"

# -------------------------------------------------
# RETRIEVAL CONFIGURATION
# -------------------------------------------------
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
