from backend.rag.embeddings import embed_texts
from backend.rag.pinecone_client import get_index
from backend.config import ALL_NAMESPACES, TOP_K, SIMILARITY_THRESHOLD

index = get_index()

def retrieve_chunks(query: str):
    q_embed = embed_texts([query])[0]

    # We query the same vector across multiple namespaces (doc types) and then
    # merge results.
    matches = []
    for ns in ALL_NAMESPACES:
        res = index.query(
            vector=q_embed,
            top_k=TOP_K,
            include_metadata=True,
            namespace=ns,
        )
        for m in getattr(res, "matches", []) or []:
            if m.score >= SIMILARITY_THRESHOLD:
                md = m.metadata or {}
                matches.append(
                    {
                        "score": float(m.score),
                        "text": md.get("text", ""),
                        "source": md.get("source"),
                        "page": md.get("page"),
                        "namespace": ns,
                    }
                )

    # Sort globally and keep TOP_K overall.
    # (Example: if TOP_K=4, we return the best 4 matches across ALL namespaces.)
    matches.sort(key=lambda x: x["score"], reverse=True)

    chunks = []
    seen = set()
    for item in matches:
        # De-dupe identical content across namespaces/sheets/pages.
        sig = (item.get("source"), item.get("page"), " ".join((item.get("text") or "").split()).lower())
        if sig in seen:
            continue
        seen.add(sig)
        chunks.append(
            {
                "text": item["text"],
                "source": item["source"],
                "page": item.get("page"),
                "namespace": item.get("namespace"),
                "score": item.get("score"),
            }
        )
        if len(chunks) >= TOP_K:
            break

    return chunks
