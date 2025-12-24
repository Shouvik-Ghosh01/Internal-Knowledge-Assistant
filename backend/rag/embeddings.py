from openai import OpenAI
from backend.config import OPENAI_API_KEY, OPENAI_API_BASE

client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_API_BASE
)

def embed_texts(texts):
    res = client.embeddings.create(
        model="text-embedding-3-large",
        input=texts
    )
    return [d.embedding for d in res.data]
