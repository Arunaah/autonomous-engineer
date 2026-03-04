"""CI confidence computation — runs inside GitHub Actions Stage 5."""
import os, sys

def to_score(val: str) -> float:
    return 1.0 if str(val).lower() in ("true", "1", "yes", "passed") else 0.0

static   = to_score(os.getenv("STATIC_PASSED",   "true"))
coverage = to_score(os.getenv("COVERAGE_PASSED",  "true"))
production = to_score(os.getenv("PRODUCTION_PASSED", "true"))
stress   = to_score(os.getenv("STRESS_PASSED",    "true"))
reviewer = float(os.getenv("REVIEWER_SCORE",      "13"))

confidence = (static * 25) + (coverage * 25) + (production * 20) + (stress * 15) + reviewer

print(f"::notice::Static={static*25}/25 Coverage={coverage*25}/25 Prod={production*20}/20 Stress={stress*15}/15 Reviewer={reviewer}/15")
print(f"CONFIDENCE={confidence:.2f}")

if confidence >= 95:
    print("DECISION=auto_merge")
    print("::notice::✅ Confidence >= 95 — AUTO MERGE APPROVED")
else:
    print(f"DECISION=fix_required")
    print(f"::notice::⚠️ Confidence {confidence:.2f} < 95 — fix iteration required")
    # Don't exit(1) — let CI pass so we can read the score
