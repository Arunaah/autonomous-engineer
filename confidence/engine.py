"""Deterministic confidence scoring engine — CI native."""


def compute_confidence(ci_result: dict, review: dict) -> float:
    """
    Confidence = Static(25) + Coverage(25) + ProdSim(20) + Stress(15) + Reviewer(15)
    """
    scores = ci_result.get("stage_scores", {})

    static_score = scores.get("static", 0.0) * 25      # Ruff + MyPy + Semgrep
    coverage_score = scores.get("coverage", 0.0) * 25   # pytest coverage >= 90%
    prod_score = scores.get("production", 0.0) * 20     # Docker + migrations + e2e
    stress_score = scores.get("stress", 0.0) * 15       # Hypothesis + k6

    reviewer_contrib = min(review.get("confidence_contribution", 0), 15)

    total = static_score + coverage_score + prod_score + stress_score + reviewer_contrib
    return round(min(total, 100.0), 2)


def parse_ci_output(raw_output: str) -> dict:
    """Parse GitHub Actions CI output into stage scores."""
    stage_scores = {
        "static": 1.0 if "ruff passed" in raw_output.lower() and "mypy passed" in raw_output.lower() else 0.0,
        "coverage": 1.0 if "coverage: 9" in raw_output.lower() or "coverage: 100" in raw_output.lower() else 0.5,
        "production": 1.0 if "docker build" in raw_output.lower() and "e2e passed" in raw_output.lower() else 0.0,
        "stress": 1.0 if "hypothesis passed" in raw_output.lower() else 0.5,
    }
    failures = []
    for line in raw_output.splitlines():
        if "error" in line.lower() or "failed" in line.lower():
            failures.append(line.strip())

    return {"stage_scores": stage_scores, "failures": failures, "raw": raw_output}
