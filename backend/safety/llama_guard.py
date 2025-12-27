from openai import OpenAI
import os

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

LLAMA_GUARD_MODEL = "llama-guard-2"

def is_safe_content(text: str, content_type: str) -> bool:
    prompt = f"""
Classify the following {content_type} as SAFE or UNSAFE.

Content:
{text}

Respond with only SAFE or UNSAFE.
"""

    response = client.chat.completions.create(
        model=LLAMA_GUARD_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    return response.choices[0].message.content.strip() == "SAFE"
