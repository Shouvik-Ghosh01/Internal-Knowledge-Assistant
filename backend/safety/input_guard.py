import re

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

# Prompt-injection patterns
INJECTION_PATTERNS = [
    r"ignore previous instructions",
    r"disregard the system prompt",
    r"act as",
    r"you are no longer",
    r"override",
    r"jailbreak"
]

MAX_QUERY_LENGTH = 500


def is_query_allowed(query: str) -> bool:
    """
    Returns True if query is allowed, False otherwise
    """

    if not query:
        return False

    q = query.strip().lower()

    # Length validation
    if len(q) == 0 or len(q) > MAX_QUERY_LENGTH:
        return False

    # Keyword-based blocking
    for word in BANNED_KEYWORDS:
        if word in q:
            return False

    # Scope validation
    for topic in OUT_OF_SCOPE_TOPICS:
        if topic in q:
            return False

    # Prompt injection detection
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, q):
            return False

    return True