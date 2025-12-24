from backend.rag.embeddings import embed_texts
from backend.rag.pinecone_client import get_index
from backend.config import TOP_K, SIMILARITY_THRESHOLD

index = get_index()

def retrieve_chunks(query: str):
    q_embed = embed_texts([query])[0]

    res = index.query(
        vector=q_embed,
        top_k=TOP_K,
        include_metadata=True
    )

    chunks = []
    for m in res.matches:
        if m.score >= SIMILARITY_THRESHOLD:
            chunks.append({
                "text": m.metadata["text"],
                "source": m.metadata["source"],
                "page": m.metadata.get("page")
            })
    return chunks
