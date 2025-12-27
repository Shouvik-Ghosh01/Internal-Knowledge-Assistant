# Explicitly forbidden intent
BANNED_KEYWORDS = [
    "password", "credentials", "token", "secret",
    "hack", "exploit", "bypass", "sql injection",
    "malware", "phishing"
]

# Topics outside assistant scope
OUT_OF_SCOPE_TOPICS = [
    "politics", "election", "religion",
    "medical advice", "legal advice",
    "stock market", "crypto", "finance tips"
]

MAX_QUERY_LENGTH = 500


def is_query_allowed(query: str) -> bool:
    """
    Deterministic, rule-based input validation.
    Returns True if query is allowed, False otherwise.
    """

    if not query:
        return False

    q = query.strip().lower()

    # Length validation
    if len(q) == 0 or len(q) > MAX_QUERY_LENGTH:
        return False

    # Explicit forbidden keywords
    for word in BANNED_KEYWORDS:
        if word in q:
            return False

    # Scope validation
    for topic in OUT_OF_SCOPE_TOPICS:
        if topic in q:
            return False

    return True