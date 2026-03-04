"""Confidence Engine — deterministic scoring inside GitHub Actions CI."""
import os, sys

def get_score(env_var: str, max_val: float, passed_var: str = None) -> float:
    if passed_var:
        passed = os.getenv(passed_var, "false").lower() == "true"
        return max_val if passed else max_val * 0.5
    val = os.getenv(env_var)
    if val is not None:
        return min(float(val), max_val)
    return max_val * 0.5


static_score     = get_score("STATIC_SCORE",     25.0, "STATIC_PASSED")
coverage_score   = get_score("COVERAGE_SCORE",   25.0, "COVERAGE_PASSED")
production_score = get_score("PRODUCTION_SCORE", 20.0, "PRODUCTION_PASSED")
stress_score     = get_score("STRESS_SCORE",     15.0, "STRESS_PASSED")
reviewer_raw     = float(os.getenv("REVIEWER_SCORE", "10"))
reviewer_score   = min(reviewer_raw, 15.0)

total = static_score + coverage_score + production_score + stress_score + reviewer_score
total = round(min(total, 100.0), 2)

print("=" * 50)
print("   CONFIDENCE SCORE REPORT")
print("=" * 50)
print(f"Static Analysis    : {static_score:5.1f} / 25.0")
print(f"Test Coverage      : {coverage_score:5.1f} / 25.0")
print(f"Prod Simulation    : {production_score:5.1f} / 20.0")
print(f"Stress Tests       : {stress_score:5.1f} / 15.0")
print(f"Reviewer Score     : {reviewer_score:5.1f} / 15.0")
print("-" * 50)
print(f"TOTAL              : {total:5.1f} / 100.0")
print(f"THRESHOLD          :  95.0")
decision = "AUTO-MERGE" if total >= 95 else "FIX LOOP"
print(f"DECISION           : {decision}")
print("=" * 50)

# Write GitHub Actions outputs
github_output = os.getenv("GITHUB_OUTPUT", "")
if github_output:
    with open(github_output, "a") as f:
        f.write(f"confidence={total}\n")
        f.write(f"should_merge={'true' if total >= 95 else 'false'}\n")

sys.exit(0)
