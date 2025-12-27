from typing import List
import os

from openai import OpenAI
from backend.config import (
    OPENAI_API_KEY,
    OPENAI_API_BASE,
    EMBEDDING_MODEL,
)

# Initialize OpenAI-compatible client once
client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_API_BASE
)


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Convert a list of text chunks into embedding vectors.

    This function is used ONLY during ingestion.
    It returns one vector per input text.

    Args:
        texts: List of chunk texts

    Returns:
        List of embedding vectors (List[float])
    """

    if not texts:
        return []

    # Defensive cleanup (avoid empty / None strings)
    clean_texts = [t.strip() for t in texts if t and t.strip()]

    if not clean_texts:
        return []

    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=clean_texts
    )

    # Each item in response.data corresponds to one input text
    embeddings = [item.embedding for item in response.data]

    return embeddings