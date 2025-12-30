def pick_namespaces(query: str, all_namespaces: list[str]) -> list[str]:
    q = query.lower()

    if "pr" in q or "review" in q:
        return ["pr_review"]

    if "validation" in q or "error" in q or "rule" in q:
        return ["validation"]

    if "locator" in q or "xpath" in q or "css" in q:
        return ["locators"]

    if "sop" in q or "onboarding" in q or "procedure" in q:
        return ["fresher_sop"]

    return all_namespaces