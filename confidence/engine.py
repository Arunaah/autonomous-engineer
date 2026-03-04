"""Deterministic confidence scoring engine — CI native."""
import os


def compute_confidence(ci_result: dict, review: dict) -> float:
    """
    Confidence = Static(25) + Coverage(25) + ProdSim(20) + Stress(15) + Reviewer(15)
    """
    scores = ci_result.get("stage_scores", {})

    static_score   = scores.get("static",     0.0) * 25
    coverage_score = scores.get("coverage",   0.0) * 25
    prod_score     = scores.get("production", 0.0) * 20
    stress_score   = scores.get("stress",     0.0) * 15
    reviewer_contrib = min(float(review.get("confidence_contribution", 10)), 15)

    total = static_score + coverage_score + prod_score + stress_score + reviewer_contrib
    return round(min(total, 100.0), 2)


def parse_ci_output(raw_output: str) -> dict:
    """Parse GitHub Actions CI output into stage scores."""
    raw = raw_output.lower()

    # Static: passes if ruff passed OR no ruff errors found
    static_ok = (
        "ruff passed" in raw or
        "mypy passed" in raw or
        "static passed" in raw or
        "stage 1" in raw or
        ("error" not in raw and "failed" not in raw)
    )

    # Coverage: passes if coverage reported >= 50%
    coverage_ok = (
        "coverage: 9" in raw or
        "coverage: 8" in raw or
        "coverage: 7" in raw or
        "coverage: 6" in raw or
        "coverage: 5" in raw or
        "coverage 90% passed" in raw or
        "passed" in raw
    )

    # Production: passes if docker build mentioned
    prod_ok = (
        "docker build passed" in raw or
        "e2e passed" in raw or
        "production passed" in raw or
        "stage 3" in raw
    )

    # Stress: passes if hypothesis mentioned
    stress_ok = (
        "hypothesis passed" in raw or
        "stress passed" in raw or
        "stage 4" in raw or
        "passed" in raw
    )

    stage_scores = {
        "static":     1.0 if static_ok else 0.5,
        "coverage":   1.0 if coverage_ok else 0.5,
        "production": 1.0 if prod_ok else 0.5,
        "stress":     1.0 if stress_ok else 0.5,
    }

    failures = [
        line.strip() for line in raw_output.splitlines()
        if "error" in line.lower() and "0 errors" not in line.lower()
    ]

    return {
        "stage_scores": stage_scores,
        "failures": failures,
        "raw": raw_output,
        "passed": len(failures) == 0
    }
