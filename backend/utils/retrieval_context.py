# Stores the last retrieved chunks for citation purposes

_LAST_RETRIEVED_CHUNKS: list[dict] = []


def set_last_retrieved_chunks(chunks: list[dict]) -> None:
    global _LAST_RETRIEVED_CHUNKS
    _LAST_RETRIEVED_CHUNKS = chunks or []


def get_last_retrieved_chunks() -> list[dict]:
    return _LAST_RETRIEVED_CHUNKS
