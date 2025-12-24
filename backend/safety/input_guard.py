def is_safe_query(query: str) -> bool:
    banned = ["hack", "attack", "illegal", "password"]
    return not any(word in query.lower() for word in banned)
