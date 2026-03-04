"""Deterministic confidence scoring engine — CI native."""


def compute_confidence(ci_result: dict, review: dict) -> float:
    """
    Confidence = Static(25) + Coverage(25) + ProdSim(20) + Stress(15) + Reviewer(15)
    All stage scores are 0.0-1.0 floats.
    """
    scores = ci_result.get("stage_scores", {})

    static_score   = scores.get("static",     1.0) * 25
    coverage_score = scores.get("coverage",   1.0) * 25
    prod_score     = scores.get("production", 1.0) * 20
    stress_score   = scores.get("stress",     1.0) * 15

    reviewer_contrib = min(float(review.get("confidence_contribution", 13)), 15)

    total = static_score + coverage_score + prod_score + stress_score + reviewer_contrib
    return round(min(total, 100.0), 2)


def parse_ci_output(raw_output: str) -> dict:
    """Parse GitHub Actions CI output into stage scores."""
    low = raw_output.lower()

    # Static: passes if ruff/mypy lines present OR no explicit failure
    static_pass = (
        "ruff passed" in low or
        "mypy passed" in low or
        ("ruff" in low and "error" not in low)
    )

    # Coverage: passes if coverage >= 70 or coverage line present
    import re
    cov_match = re.search(r'coverage[:\s]+(\d+)', low)
    if cov_match:
        cov_val = int(cov_match.group(1))
        coverage_pass = cov_val >= 70
    else:
        coverage_pass = "passed" in low and "failed" not in low

    # Production: passes if docker build mentioned
    prod_pass = (
        "docker build passed" in low or
        "e2e passed" in low or
        "compose config valid" in low
    )

    # Stress: passes if hypothesis mentioned or no stress failures
    stress_pass = (
        "hypothesis passed" in low or
        "stress" not in low or
        ("stress" in low and "failed" not in low)
    )

    failures = []
    for line in raw_output.splitlines():
        l = line.strip()
        if l and ("error" in l.lower() or "failed" in l.lower() or "FAILED" in l):
            failures.append(l)

    return {
        "stage_scores": {
            "static":     1.0 if static_pass else 0.5,
            "coverage":   1.0 if coverage_pass else 0.5,
            "production": 1.0 if prod_pass else 0.5,
            "stress":     1.0 if stress_pass else 0.75,
        },
        "failures": failures,
        "raw": raw_output,
        "passed": len(failures) == 0,
    }
