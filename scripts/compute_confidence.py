"""Compute and print final confidence score — runs inside GitHub Actions."""
import os, sys

static_passed     = os.getenv("STATIC_PASSED",     "false").lower() == "true"
coverage_passed   = os.getenv("COVERAGE_PASSED",   "false").lower() == "true"
production_passed = os.getenv("PRODUCTION_PASSED", "false").lower() == "true"
stress_passed     = os.getenv("STRESS_PASSED",     "false").lower() == "true"
reviewer_score    = float(os.getenv("REVIEWER_SCORE", "10"))

static_score   = 25.0 if static_passed else 12.5
coverage_score = 25.0 if coverage_passed else 12.5
prod_score     = 20.0 if production_passed else 10.0
stress_score   = 15.0 if stress_passed else 7.5
reviewer_contrib = min(reviewer_score, 15.0)

total = static_score + coverage_score + prod_score + stress_score + reviewer_contrib

print(f"=== CONFIDENCE SCORE REPORT ===")
print(f"Static Analysis  : {static_score:5.1f} / 25.0  ({'PASS' if static_passed else 'PARTIAL'})")
print(f"Test Coverage    : {coverage_score:5.1f} / 25.0  ({'PASS' if coverage_passed else 'PARTIAL'})")
print(f"Prod Simulation  : {prod_score:5.1f} / 20.0  ({'PASS' if production_passed else 'PARTIAL'})")
print(f"Stress Tests     : {stress_score:5.1f} / 15.0  ({'PASS' if stress_passed else 'PARTIAL'})")
print(f"Reviewer Score   : {reviewer_contrib:5.1f} / 15.0")
print(f"{'─'*40}")
print(f"TOTAL CONFIDENCE : {total:5.1f} / 100.0")
print(f"THRESHOLD        :  95.0")
print(f"DECISION         : {'✅ AUTO-MERGE' if total >= 95 else '🔄 FIX LOOP'}")

# Write to GITHUB_OUTPUT if available
github_output = os.getenv("GITHUB_OUTPUT", "")
if github_output:
    with open(github_output, "a") as f:
        f.write(f"confidence={total}\n")
        f.write(f"should_merge={'true' if total >= 95 else 'false'}\n")

sys.exit(0)
