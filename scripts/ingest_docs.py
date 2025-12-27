"""
Run all ingestion pipelines for the Internal Knowledge Assistant.

This script should be run:
- Once during initial setup
- Whenever source documents are updated
"""

from backend.rag.ingestion.pr_review_ingest import ingest_pr_review
from backend.rag.ingestion.common_keyword_locator_ingest import ingest_common_keyword_locators
from backend.rag.ingestion.validation_checklist_ingest import ingest_validation_checklist
from backend.rag.ingestion.sop_ingest import ingest_sop


def main():
    total = 0

    print("Starting ingestion...\n")

    # 1️⃣ PR Review Checklist
    count = ingest_pr_review()
    print(f"PR Review Checklist: {count} chunks ingested")
    total += count

    # 2️⃣ UI Locators & Keywords
    count = ingest_common_keyword_locators()
    print(f"UI Locators Reference: {count} chunks ingested")
    total += count

    # 3️⃣ Validation Checklist
    count = ingest_validation_checklist()
    print(f"Validation Checklist: {count} chunks ingested")
    total += count

    # 4️⃣ Fresher SOP / Guidelines
    count = ingest_sop()
    print(f"Fresher SOP: {count} chunks ingested")
    total += count

    print("\nIngestion complete.")
    print(f"Total chunks ingested: {total}")


if __name__ == "__main__":
    main()
