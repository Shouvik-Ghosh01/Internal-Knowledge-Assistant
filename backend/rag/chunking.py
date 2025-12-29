from __future__ import annotations

from typing import Iterable, List


def chunk_documents(docs: Iterable[object], *, chunk_size: int = 1000, chunk_overlap: int = 150):
    """Split LangChain Documents into smaller chunks.

    This helper is used by optional PDF ingestion.
    """

    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("langchain is required for chunking") from exc

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""],
    )

    # `split_documents` expects a list of LangChain Document-like objects.
    return splitter.split_documents(list(docs))
