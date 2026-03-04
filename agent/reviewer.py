"""Reviewer Module — scores diffs using GLM-4 via LiteLLM."""
import os, json
from litellm import completion

LITELLM_BASE_URL = os.getenv("LITELLM_BASE_URL", "http://localhost:4000")
REVIEWER_MODEL = os.getenv("REVIEWER_MODEL", "glm4")


def review_diff(diff: str, spec: dict) -> dict:
    """Analyze a git diff and return structured scoring JSON."""
    system = (
        "You are a senior code reviewer. Analyze the diff and return ONLY valid JSON with keys: "
        "risk_score (0-100, lower is better), maintainability_score (0-100), "
        "confidence_contribution (0-15), issues (list of strings), approved (bool)."
    )
    prompt = f"Spec:\n{json.dumps(spec, indent=2)}\n\nDiff to review:\n{diff}"
    response = completion(
        model=f"openai/{REVIEWER_MODEL}",
        messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        api_base=LITELLM_BASE_URL,
        max_tokens=1024,
    )
    raw = response.choices[0].message.content
    return json.loads(raw)


def fix_ci_failure(failure_report: str, current_code: str, past_fixes: str = "") -> dict:
    """Generate a patch to fix a CI failure."""
    system = (
        "You are an expert debugger. Return ONLY valid JSON with keys: "
        "patch_description (str), files (dict of filepath->content)."
    )
    prompt = f"CI Failure:\n{failure_report}\n\nCurrent code:\n{current_code}"
    if past_fixes:
        prompt += f"\n\nPreviously successful fixes:\n{past_fixes}"
    response = completion(
        model=f"openai/{REVIEWER_MODEL}",
        messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        api_base=LITELLM_BASE_URL,
        max_tokens=4096,
    )
    return json.loads(response.choices[0].message.content)
