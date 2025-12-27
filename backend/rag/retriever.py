from backend.rag.embeddings import embed_texts
from backend.rag.pinecone_client import get_index
from backend.config import TOP_K, SIMILARITY_THRESHOLD

index = get_index()


def retrieve_chunks(query: str) -> list[dict]:
    """
    Retrieves relevant document chunks from Pinecone using vector similarity.

    Returns:
        List of chunks with text, source, and page metadata.
        Returns an empty list if no relevant chunks meet the similarity threshold.
    """

    # Convert query to embedding
    q_embed = embed_texts([query])[0]

    # Query Pinecone
    res = index.query(
        vector=q_embed,
        top_k=TOP_K,
        include_metadata=True
    )

    chunks = []

    for match in res.matches or []:
        if match.score >= SIMILARITY_THRESHOLD:
            metadata = match.metadata or {}

            chunks.append({
                "text": metadata.get("text", ""),
                "source": metadata.get("source", "unknown"),
                "page": metadata.get("page"),
                "score": match.score,  # useful for debugging & evaluation
            })

    return chunks
