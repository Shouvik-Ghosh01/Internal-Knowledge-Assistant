from openai import OpenAI
import os

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

PROMPT_GUARD_MODEL = "meta-llama/llama-prompt-guard-2-86m"


def is_prompt_safe(text: str) -> bool:
    """
    Returns True if prompt is SAFE, False if it is a prompt-injection or jailbreak attempt.
    """

    response = client.chat.completions.create(
        model=PROMPT_GUARD_MODEL,
        messages=[
            {
                "role": "user",
                "content": text
            }
        ],
        temperature=0
    )

    verdict = response.choices[0].message.content.strip().lower()

    # Prompt Guard outputs things like:
    # "SAFE"
    # "UNSAFE_PROMPT_INJECTION"
    return verdict.startswith("safe")
