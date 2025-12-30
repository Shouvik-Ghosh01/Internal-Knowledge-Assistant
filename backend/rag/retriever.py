from backend.rag.embeddings import embed_texts
from backend.rag.pinecone_client import get_index
from backend.config import ALL_NAMESPACES, TOP_K
from backend.utils.retrieval_context import set_last_retrieved_chunks
from backend.rag.namespace_router import pick_namespaces

index = get_index()

MIN_ABSOLUTE_SCORE = 0.45
RELATIVE_DROP = 0.15  # keep chunks close to best score


def retrieve_chunks(query: str) -> list[dict]:
    q_embed = embed_texts([query])[0]

    matches = []

    namespaces = pick_namespaces(query, ALL_NAMESPACES)
    for ns in namespaces:
        res = index.query(
            vector=q_embed,
            top_k=TOP_K,
            include_metadata=True,
            namespace=ns,
        )

        for m in getattr(res, "matches", []) or []:
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

    if not matches:
        set_last_retrieved_chunks([])
        return []

    # Sort by score
    matches.sort(key=lambda x: x["score"], reverse=True)
    best_score = matches[0]["score"]

    # Dynamic filtering
    filtered = []
    seen = set()

    for item in matches:
        if item["score"] < MIN_ABSOLUTE_SCORE:
            continue
        if (best_score - item["score"]) > RELATIVE_DROP:
            continue

        sig = (
            item.get("source"),
            item.get("page"),
            " ".join((item.get("text") or "").split()).lower(),
        )
        if sig in seen:
            continue
        seen.add(sig)

        filtered.append(item)

        if len(filtered) >= 5:  # final context size
            break

    set_last_retrieved_chunks(filtered)
    return filtered