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
    NAMESPACE_COMPANY,
)

# -------------------------------------------------
# OPTIONAL PDF INGESTION (generic utility)
# -------------------------------------------------
def ingest_pdf(path: str | Path, *, namespace: str, batch_size: int = 64) -> int:
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

    for start in range(0, len(texts), batch_size):
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
            meta = {k: v for k, v in meta.items() if v}
            vectors.append((str(uuid.uuid4()), e, meta))

        index.upsert(vectors=vectors, namespace=namespace)
        upserted += len(vectors)

    return upserted


# -------------------------------------------------
# MAIN INGESTION RUNNER
# -------------------------------------------------
def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Ingest Internal Knowledge Assistant documents into Pinecone"
    )

    parser.add_argument("--batch-size", type=int, default=64)

    parser.add_argument("--all", action="store_true", help="Ingest all document sources")
    parser.add_argument("--locators", action="store_true")
    parser.add_argument("--validation", action="store_true")
    parser.add_argument("--pr-review", action="store_true")
    parser.add_argument("--sop", action="store_true")
    parser.add_argument("--company", action="store_true", help="Ingest company profile")
    parser.add_argument("--pdf", default=None, help="Optional PDF path to ingest")

    parser.add_argument(
        "--locators-path",
        default=str(Path("data/common_keywords_locators/SAF_Common_Keywords_Locators_v1.0.xlsx")),
    )
    parser.add_argument(
        "--validation-path",
        default=str(Path("data/validation_checklist/Report Verification Checklist.xlsx")),
    )
    parser.add_argument(
        "--pr-review-path",
        default=str(Path("data/pr_review/PR Review Checklist.docx")),
    )
    parser.add_argument(
        "--sop-path",
        default=str(Path("data/guidelines/Standard Operating procedure.docx")),
    )
    parser.add_argument(
        "--company-path",
        default=str(Path("data/company/spotline_profile.docx")),
    )

    args = parser.parse_args(argv)

    if not any([
        args.all,
        args.locators,
        args.validation,
        args.pr_review,
        args.sop,
        args.company,
        args.pdf,
    ]):
        args.all = True

    total = 0

    if args.all or args.locators:
        from backend.rag.ingestion.common_keyword_locator_ingest import ingest_common_keyword_locators

        n = ingest_common_keyword_locators(
            args.locators_path,
            namespace=NAMESPACE_LOCATORS,
            batch_size=args.batch_size,
        )
        print(f"Locators upserted: {n}")
        total += n

    if args.all or args.validation:
        from backend.rag.ingestion.validation_checklist_ingest import ingest_validation_checklist

        n = ingest_validation_checklist(
            args.validation_path,
            namespace=NAMESPACE_VALIDATION,
            batch_size=args.batch_size,
        )
        print(f"Validation rules upserted: {n}")
        total += n

    if args.all or args.pr_review:
        from backend.rag.ingestion.pr_review_ingest import ingest_pr_review

        n = ingest_pr_review(
            args.pr_review_path,
            namespace=NAMESPACE_PR_REVIEW,
            batch_size=args.batch_size,
        )
        print(f"PR review items upserted: {n}")
        total += n

    if args.all or args.sop:
        from backend.rag.ingestion.sop_ingest import ingest_sop

        n = ingest_sop(
            args.sop_path,
            namespace=NAMESPACE_SOP,
            batch_size=args.batch_size,
        )
        print(f"SOP steps upserted: {n}")
        total += n

    if args.all or args.company:
        from backend.rag.ingestion.sop_ingest import ingest_sop

        n = ingest_sop(
            args.company_path,
            namespace=NAMESPACE_COMPANY,
            batch_size=args.batch_size,
        )
        print(f"Company profile upserted: {n}")
        total += n

    if args.pdf:
        n = ingest_pdf(args.pdf, namespace="pdf", batch_size=args.batch_size)
        print(f"PDF chunks upserted: {n}")
        total += n

    print(f"\nTotal vectors upserted: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))