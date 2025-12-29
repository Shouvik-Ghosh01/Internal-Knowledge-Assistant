
UNSAFE_OUTPUT_PHRASES = [
    "i assume",
    "i think",
    "probably",
    "might be",
    "not sure but",
    "you could try hacking",
    "one way to bypass",
    "i don't have the document but"
]

FABRICATION_SIGNALS = [
    "according to general knowledge",
    "based on my training data",
    "from the internet",
    "widely known that"
]


def is_safe_output(text: str) -> bool:
    """
    Returns True if output is safe, False otherwise
    """

    if not text:
        return False

    t = text.lower()

    # Detect speculative / hallucinated language
    for phrase in UNSAFE_OUTPUT_PHRASES:
        if phrase in t:
            return False

    # Detect fabricated source claims
    for signal in FABRICATION_SIGNALS:
        if signal in t:
            return False

    return True