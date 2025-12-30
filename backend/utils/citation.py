from pathlib import Path
from backend.utils.retrieval_context import get_last_retrieved_chunks


def extract_sources() -> list[str]:
    """
    Returns unique document names based on retrieved chunks.
    """

    chunks = get_last_retrieved_chunks()
    if not chunks:
        return []

    sources = set()

    for c in chunks:
        src = c.get("source")
        if not src:
            continue

        sources.add(Path(src).name)

    return sorted(sources)