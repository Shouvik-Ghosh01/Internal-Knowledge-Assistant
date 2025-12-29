from __future__ import annotations

import argparse
import sys
import uuid
from pathlib import Path

from backend.config import (
    NAMESPACE_LOCATORS,
    NAMESPACE_PR_REVIEW,
    NAMESPACE_SOP,
    NAMESPACE_VALIDATION,
)

# Simple ingestion runner.
#
# Usage examples:
#   python scripts/ingest_docs.py                # ingest all 4 doc types
#   python scripts/ingest_docs.py --locators     # only locators
#   python scripts/ingest_docs.py --validation   # only validation
#   python scripts/ingest_docs.py --pr-review --sop
#
# Note: Make sure your env vars are set (see backend/config.py):
#   DEEPSEEK_API_KEY, PINECONE_API_KEY, PINECONE_ENV


def ingest_pdf(path: str | Path, *, namespace: str, batch_size: int = 64) -> int:
    """Optional: Ingest a PDF via LangChain loader + chunker."""

    from langchain.document_loaders import PyPDFLoader

    from backend.rag.chunking import chunk_documents
    from backend.rag.embeddings import embed_texts
    from backend.rag.pinecone_client import get_index

    docs = PyPDFLoader(str(path)).load()
    chunks = chunk_documents(docs)
    if not chunks:
        return 0

    texts = [c.page_content for c in chunks]
    index = get_index()

    upserted = 0
    for start in range(0, len(texts), max(1, batch_size)):
        batch_chunks = chunks[start : start + batch_size]
        batch_texts = texts[start : start + batch_size]
        embeds = embed_texts(batch_texts)

        vectors = []
        for c, e in zip(batch_chunks, embeds):
            meta = {
                "text": c.page_content,
                "source": c.metadata.get("source"),
                "page": c.metadata.get("page"),
            }
            meta = {k: v for k, v in meta.items() if v is not None and v != ""}
            vectors.append(
                (
                    str(uuid.uuid4()),
                    e,
                    meta,
                )
            )

        index.upsert(vectors=vectors, namespace=namespace)
        upserted += len(vectors)

    return upserted


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Ingest Internal Knowledge Assistant docs into Pinecone")
    parser.add_argument("--batch-size", type=int, default=64, help="Embedding/upsert batch size")

    parser.add_argument("--all", action="store_true", help="Ingest all curated sources")
    parser.add_argument("--locators", action="store_true", help=f"Ingest locators XLSX into namespace '{NAMESPACE_LOCATORS}'")
    parser.add_argument("--validation", action="store_true", help=f"Ingest validation checklist XLSX into namespace '{NAMESPACE_VALIDATION}'")
    parser.add_argument("--pr-review", action="store_true", help=f"Ingest PR review DOCX into namespace '{NAMESPACE_PR_REVIEW}'")
    parser.add_argument("--sop", action="store_true", help=f"Ingest SOP DOCX into namespace '{NAMESPACE_SOP}'")
    parser.add_argument("--pdf", default=None, help="Optional: ingest a PDF at this path")

    parser.add_argument(
        "--locators-path",
        default=str(Path("data") / "common_keywords_locators" / "SAF_Common_Keywords_Locators_v1.0.xlsx"),
    )
    parser.add_argument(
        "--validation-path",
        default=str(Path("data") / "validation_checklist" / "Report Verification Checklist.xlsx"),
    )
    parser.add_argument(
        "--pr-review-path",
        default=str(Path("data") / "pr_review" / "PR Review Checklist.docx"),
    )
    parser.add_argument(
        "--sop-path",
        default=str(Path("data") / "guidelines" / "Standard Operating procedure.docx"),
    )

    args = parser.parse_args(argv)

    selected_any = any([args.all, args.locators, args.validation, args.pr_review, args.sop, bool(args.pdf)])
    if not selected_any:
        args.all = True

    total = 0

    if args.all or args.locators:
        from backend.rag.ingestion.common_keyword_locator_ingest import ingest_common_keyword_locators

        n = ingest_common_keyword_locators(args.locators_path, namespace=NAMESPACE_LOCATORS, batch_size=args.batch_size)
        print(f"Locators upserted: {n} (namespace={NAMESPACE_LOCATORS})")
        total += n

    if args.all or args.validation:
        from backend.rag.ingestion.validation_checklist_ingest import ingest_validation_checklist

        n = ingest_validation_checklist(args.validation_path, namespace=NAMESPACE_VALIDATION, batch_size=args.batch_size)
        print(f"Validation rules upserted: {n} (namespace={NAMESPACE_VALIDATION})")
        total += n

    if args.all or args.pr_review:
        from backend.rag.ingestion.pr_review_ingest import ingest_pr_review

        n = ingest_pr_review(args.pr_review_path, namespace=NAMESPACE_PR_REVIEW, batch_size=args.batch_size)
        print(f"PR review items upserted: {n} (namespace={NAMESPACE_PR_REVIEW})")
        total += n

    if args.all or args.sop:
        from backend.rag.ingestion.sop_ingest import ingest_sop

        n = ingest_sop(args.sop_path, namespace=NAMESPACE_SOP, batch_size=args.batch_size)
        print(f"SOP steps upserted: {n} (namespace={NAMESPACE_SOP})")
        total += n

    if args.pdf:
        n = ingest_pdf(args.pdf, namespace="pdf", batch_size=args.batch_size)
        print(f"PDF chunks upserted: {n} (namespace=pdf)")
        total += n

    print(f"Total upserted: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
