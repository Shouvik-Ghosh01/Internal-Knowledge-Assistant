import pinecone
from backend.config import *

pinecone.init(
    api_key=PINECONE_API_KEY,
    environment=PINECONE_ENV
)

def get_index():
    if PINECONE_INDEX not in pinecone.list_indexes():
        pinecone.create_index(
            name=PINECONE_INDEX,
            dimension=3072,
            metric="cosine"
        )
    return pinecone.Index(PINECONE_INDEX)
