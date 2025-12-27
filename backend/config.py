import os
from dotenv import load_dotenv

load_dotenv()

# -------------------------------------------------
# LLM CONFIGURATION (DeepSeek - OpenAI compatible)
# -------------------------------------------------
OPENAI_API_KEY = os.getenv("DEEPSEEK_API_KEY")
OPENAI_API_BASE = "https://api.deepseek.com"
LLM_MODEL = "deepseek-chat"

# -------------------------------------------------
# EMBEDDING CONFIGURATION (1536-dim)
# -------------------------------------------------
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION: int = 1536

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