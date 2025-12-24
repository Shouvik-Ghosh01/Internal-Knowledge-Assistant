import uuid
from langchain.document_loaders import PyPDFLoader
from backend.rag.chunking import chunk_documents
from backend.rag.embeddings import embed_texts
from backend.rag.pinecone_client import get_index

index = get_index()

def ingest_pdf(path):
    docs = PyPDFLoader(path).load()
    chunks = chunk_documents(docs)

    texts = [c.page_content for c in chunks]
    embeds = embed_texts(texts)

    vectors = []
    for c, e in zip(chunks, embeds):
        vectors.append({
            "id": str(uuid.uuid4()),
            "values": e,
            "metadata": {
                "text": c.page_content,
                "source": c.metadata.get("source"),
                "page": c.metadata.get("page")
            }
        })

    index.upsert(vectors)

if __name__ == "__main__":
    ingest_pdf("data/raw_docs/sample.pdf")
