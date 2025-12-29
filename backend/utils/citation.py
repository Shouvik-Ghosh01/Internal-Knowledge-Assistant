import re
from typing import List, Dict

SOURCE_PATTERN = re.compile(
    r"\[Source:\s*(?P<source>[^,\]]+),\s*Page\s*(?P<page>[^\]]+)\]",
    re.IGNORECASE,
)


def extract_sources(text: str) -> tuple[str, List[Dict[str, str]]]:
    """
    Extracts sources from the text and removes them from the answer.

    Returns:
        clean_answer: str
        sources: List[{"source": ..., "page": ...}]
    """

    matches = SOURCE_PATTERN.findall(text)

    seen = set()
    sources = []

    for source, page in matches:
        key = (source.strip(), page.strip())
        if key not in seen:
            seen.add(key)
            sources.append(
                {
                    "source": source.strip(),
                    "page": page.strip(),
                }
            )

    # Remove all source blocks from the text
    clean_text = SOURCE_PATTERN.sub("", text)

    # Cleanup extra whitespace left behind
    clean_text = re.sub(r"\n{3,}", "\n\n", clean_text).strip()

    return clean_text, sources
