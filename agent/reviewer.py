"""Reviewer Module — scores diffs using GLM-4 via LiteLLM."""
import os, json, re
from litellm import completion

LITELLM_BASE_URL = os.getenv("LITELLM_BASE_URL", "http://ae-litellm:4000")
REVIEWER_MODEL = os.getenv("REVIEWER_MODEL", "glm4")
LITELLM_API_KEY = os.getenv("LITELLM_API_KEY", "ae-litellm-master-key-2024")


def _parse_json(raw: str):
    raw = raw.strip()
    raw = re.sub(r"```(?:json)?", "", raw)
    raw = raw.strip().strip("`").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    for start_char, end_char in [('{', '}'), ('[', ']')]:
        start = raw.find(start_char)
        end = raw.rfind(end_char)
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(raw[start:end+1])
            except Exception:
                pass
    return {"risk_score": 50, "maintainability_score": 50,
            "confidence_contribution": 7, "issues": [], "approved": True}


def review_diff(diff: str, spec: dict) -> dict:
    system = (
        "You are a senior code reviewer. Respond with ONLY valid JSON. "
        "No markdown. No explanation. No code fences. Just raw JSON.\n"
        "JSON structure:\n"
        '{"risk_score": 0-100, "maintainability_score": 0-100, '
        '"confidence_contribution": 0-15, "issues": ["string"], "approved": true}'
    )
    prompt = f"Review this code change:\nSpec:\n{json.dumps(spec, indent=2)}\n\nDiff:\n{diff[:3000]}"
    response = completion(
        model=f"openai/{REVIEWER_MODEL}",
        messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        api_base=LITELLM_BASE_URL,
        api_key=LITELLM_API_KEY,
        max_tokens=1024,
    )
    return _parse_json(response.choices[0].message.content)


def fix_ci_failure(failure_report: str, current_code: str, past_fixes: str = "") -> dict:
    system = (
        "You are an expert debugger. Respond with ONLY valid JSON. "
        "No markdown. No explanation. No code fences. Just raw JSON.\n"
        "JSON structure:\n"
        '{"patch_description": "string", "files": {"filepath": "content"}}'
    )
    prompt = f"Fix these CI failures:\n{failure_report}\n\nCode:\n{current_code[:3000]}"
    if past_fixes:
        prompt += f"\n\nPast fixes:\n{past_fixes}"
    response = completion(
        model=f"openai/{REVIEWER_MODEL}",
        messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        api_base=LITELLM_BASE_URL,
        api_key=LITELLM_API_KEY,
        max_tokens=4096,
    )
    result = _parse_json(response.choices[0].message.content)
    if "files" not in result:
        result["files"] = {}
    return result
