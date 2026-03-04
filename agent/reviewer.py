"""
Reviewer Module
Primary:  MiniMax (diff analysis, risk scoring, maintainability)
Fallback: GLM-4
Returns structured JSON confidence contribution.
"""
import os, json, re, logging
import requests

logger = logging.getLogger("ae.reviewer")

LITELLM_BASE_URL = os.getenv("LITELLM_BASE_URL", "http://ae-litellm:4000")
LITELLM_API_KEY  = os.getenv("LITELLM_API_KEY", "ae-litellm-master-key-2024")
REVIEWER_MODEL   = os.getenv("REVIEWER_MODEL", "glm4-reviewer")
GLM_MODEL        = os.getenv("GLM_MODEL", "glm4")


def _llm(model: str, system: str, user: str) -> str:
    try:
        r = requests.post(
            f"{LITELLM_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {LITELLM_API_KEY}",
                     "Content-Type": "application/json"},
            json={"model": model,
                  "messages": [{"role": "system", "content": system},
                                {"role": "user",   "content": user}],
                  "max_tokens": 1000, "temperature": 0.1},
            timeout=120
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logger.warning(f"Model {model} failed: {e}. Falling back to {GLM_MODEL}")
        r = requests.post(
            f"{LITELLM_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {LITELLM_API_KEY}",
                     "Content-Type": "application/json"},
            json={"model": GLM_MODEL,
                  "messages": [{"role": "system", "content": system},
                                {"role": "user",   "content": user}],
                  "max_tokens": 1000, "temperature": 0.1},
            timeout=120
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]


def _parse_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r'\{.*\}', text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except Exception:
                pass
    return {"confidence_contribution": 10, "risk": "medium",
            "maintainability": 7, "issues": [], "summary": text[:200]}


def review_diff(diff: str, spec: dict) -> dict:
    """
    Analyze PR diff and return structured review.
    Returns confidence contribution (0-15).
    """
    if not diff or len(diff.strip()) < 10:
        return {
            "confidence_contribution": 12,
            "risk": "low",
            "maintainability": 8,
            "issues": [],
            "summary": "No diff to review - using baseline score"
        }

    system = """You are an expert code reviewer (MiniMax-style analyzer).
Analyze the code diff and return ONLY valid JSON:
{
  "confidence_contribution": <integer 0-15>,
  "risk": "low|medium|high",
  "maintainability": <integer 1-10>,
  "issues": ["issue1", "issue2"],
  "summary": "one sentence summary"
}

Scoring guide:
- 13-15: excellent code, low risk, high maintainability
- 10-12: good code, minor issues
- 7-9:   acceptable, some concerns
- 4-6:   significant issues
- 0-3:   critical problems

Return ONLY JSON, no explanation."""

    user = f"""Spec: {json.dumps(spec.get('acceptance_criteria', []))}

Diff to review:
{diff[:3000]}"""

    result = _llm(REVIEWER_MODEL, system, user)
    review = _parse_json(result)

    # Validate and clamp
    review["confidence_contribution"] = max(0, min(15, int(
        review.get("confidence_contribution", 10))))
    review.setdefault("risk", "medium")
    review.setdefault("maintainability", 7)
    review.setdefault("issues", [])
    review.setdefault("summary", "Review complete")

    logger.info(f"Review: contribution={review['confidence_contribution']}/15 "
                f"risk={review['risk']} maintainability={review['maintainability']}/10")
    return review


def fix_ci_failure(failure_report: str, current_code: str, past_fixes: str = "") -> dict:
    """Generate a targeted fix for a CI failure."""
    system = """You are an expert debugger and software engineer.
Analyze the CI failure and generate a COMPLETE fix.

Return ONLY valid JSON:
{
  "files": {
    "path/to/fixed_file.py": "complete fixed file content"
  },
  "explanation": "what was wrong and how it was fixed",
  "fix_type": "syntax|import|logic|test|config"
}

Rules:
- Return COMPLETE file contents, not patches
- Fix must address the root cause
- No placeholders or TODOs"""

    past_context = f"\nPast successful fixes:\n{past_fixes}" if past_fixes else ""

    user = f"""CI FAILURE REPORT:
{failure_report}

CURRENT CODE:
{current_code[:2000]}
{past_context}

Generate a complete fix."""

    result = _llm(GLM_MODEL, system, user)

    try:
        parsed = _parse_json(result)
        if isinstance(parsed, dict) and "files" in parsed:
            return parsed
    except Exception:
        pass

    return {
        "files": {},
        "explanation": "Fix generation failed - manual review needed",
        "fix_type": "unknown"
    }
