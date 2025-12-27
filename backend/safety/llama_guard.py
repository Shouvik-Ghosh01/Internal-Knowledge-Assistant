from openai import OpenAI
from backend.config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

LLAMA_GUARD_MODEL = "llama-guard-2"

def is_safe_content(text: str, content_type: str) -> bool:
    """
    content_type: 'user_input' or 'assistant_output'
    """

    prompt = f"""
You are a safety classifier.

Classify the following {content_type} as SAFE or UNSAFE.
If unsafe, it includes harmful, illegal, malicious, or sensitive content.

Content:
{text}

Respond with only one word: SAFE or UNSAFE
"""

    response = client.chat.completions.create(
        model=LLAMA_GUARD_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    verdict = response.choices[0].message.content.strip()
    return verdict == "SAFE"