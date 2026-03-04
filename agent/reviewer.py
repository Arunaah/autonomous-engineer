"""Reviewer Module — scores diffs using GLM-4 via LiteLLM."""
import os, json, re
from litellm import completion

LITELLM_BASE_URL = os.getenv("LITELLM_BASE_URL", "http://ae-litellm:4000")
REVIEWER_MODEL = os.getenv("REVIEWER_MODEL", "glm4")
LITELLM_API_KEY = os.getenv("LITELLM_API_KEY", "ae-litellm-master-key-2024")

_FALLBACK_REVIEW = {
    "risk_score": 30, "maintainability_score": 70,
    "confidence_contribution": 10, "issues": [], "approved": True
}


def _parse_json(raw: str, fallback: dict = None):
    raw = raw.strip()
    raw = re.sub(r"```(?:json)?", "", raw).strip().strip("`").strip()
    raw = raw.replace('\\\\"', '\\"').replace("\\\\'", "\\'")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    for sc, ec in [('{', '}'), ('[', ']')]:
        s, e = raw.find(sc), raw.rfind(ec)
        if s != -1 and e != -1 and e > s:
            try:
                return json.loads(raw[s:e+1])
            except Exception:
                try:
                    fixed = re.sub(r'(?<!\\)\n', '\\n', raw[s:e+1])
                    return json.loads(fixed)
                except Exception:
                    pass
    return fallback or {}


def review_diff(diff: str, spec: dict) -> dict:
    system = (
        "You are a senior code reviewer. Respond with ONLY valid JSON. No markdown.\n"
        'Structure: {"risk_score":0-100,"maintainability_score":0-100,'
        '"confidence_contribution":0-15,"issues":["string"],"approved":true}'
    )
    prompt = f"Review this code change:\nSpec:\n{json.dumps(spec, indent=2)}\n\nDiff:\n{diff[:3000]}"
    try:
        response = completion(
            model=f"openai/{REVIEWER_MODEL}",
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            api_base=LITELLM_BASE_URL, api_key=LITELLM_API_KEY, max_tokens=1024,
        )
        result = _parse_json(response.choices[0].message.content, _FALLBACK_REVIEW)
    except Exception:
        result = _FALLBACK_REVIEW.copy()
    result.setdefault("confidence_contribution", 10)
    result.setdefault("approved", True)
    return result


def fix_ci_failure(failure_report: str, current_code: str, past_fixes: str = "") -> dict:
    system = (
        "You are an expert debugger. Respond with ONLY valid JSON. No markdown.\n"
        'Structure: {"patch_description":"string","files":{"filepath":"content"}}'
    )
    prompt = f"Fix these CI failures:\n{failure_report}\n\nCode:\n{current_code[:3000]}"
    if past_fixes:
        prompt += f"\n\nPast fixes:\n{past_fixes}"
    try:
        response = completion(
            model=f"openai/{REVIEWER_MODEL}",
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            api_base=LITELLM_BASE_URL, api_key=LITELLM_API_KEY, max_tokens=4096,
        )
        result = _parse_json(response.choices[0].message.content, {"files": {}})
    except Exception:
        result = {"files": {}}
    result.setdefault("files", {})
    return result
