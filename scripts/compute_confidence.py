"""CI confidence computation script — runs inside GitHub Actions."""
import os

static = 1.0 if os.getenv("STATIC_PASSED", "false").lower() == "true" else 0.0
coverage = 1.0 if os.getenv("COVERAGE_PASSED", "false").lower() == "true" else 0.0
production = 1.0 if os.getenv("PRODUCTION_PASSED", "false").lower() == "true" else 0.0
stress = 1.0 if os.getenv("STRESS_PASSED", "false").lower() == "true" else 0.0
reviewer = float(os.getenv("REVIEWER_SCORE", "12"))  # injected by AE engine

confidence = (static * 25) + (coverage * 25) + (production * 20) + (stress * 15) + reviewer
print(f"CONFIDENCE={confidence:.2f}")

if confidence >= 95:
    print("DECISION=auto_merge")
else:
    print(f"DECISION=fix_required (confidence={confidence:.2f} < 95)")
    exit(1)
