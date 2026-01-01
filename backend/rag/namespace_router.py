def pick_namespaces(query: str, all_namespaces: list[str]) -> list[str]:
    q = query.lower()

    selected = set()

    if any(k in q for k in ["spotline", "company", "about", "overview"]):
        selected.add("company_profile")

    if any(k in q for k in ["pr", "pull request", "review"]):
        selected.add("pr_review")

    if any(k in q for k in ["sop", "onboarding", "procedure", "guideline"]):
        selected.add("sop")

    if any(k in q for k in ["validation", "checklist", "rules"]):
        selected.add("validation")

    if any(k in q for k in ["locator", "xpath", "selector", "ui"]):
        selected.add("locators")

    # Fallback: search everything
    if not selected:
        return all_namespaces

    return list(selected)