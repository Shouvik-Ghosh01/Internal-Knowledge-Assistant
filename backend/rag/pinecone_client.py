from __future__ import annotations
from backend.config import *
import os
from functools import lru_cache
from typing import Optional

from pinecone import Pinecone, ServerlessSpec

from backend.config import (
    PINECONE_API_KEY,
    PINECONE_ENV,
    PINECONE_INDEX,
    EMBEDDING_DIMENSION
)


@lru_cache(maxsize=1)
def _get_pinecone_client() -> Pinecone:
    """
    Create and cache the Pinecone client.
    """
    if not PINECONE_API_KEY:
        raise RuntimeError("PINECONE_API_KEY is not set")

    return Pinecone(api_key=PINECONE_API_KEY)


@lru_cache(maxsize=1)
def get_index():
    pc = _get_pinecone_client()

    existing_indexes = {idx.name for idx in pc.list_indexes()}

    if PINECONE_INDEX not in existing_indexes:
        pc.create_index(
            name=PINECONE_INDEX,
            dimension=EMBEDDING_DIMENSION,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region=PINECONE_ENV,
            ),
        )

    return pc.Index(PINECONE_INDEX)
