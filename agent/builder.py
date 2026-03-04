"""Unified Builder Agent — GLM-4 via LiteLLM/Ollama."""
import os, json, re
from litellm import completion

LITELLM_BASE_URL = os.getenv("LITELLM_BASE_URL", "http://ae-litellm:4000")
GLM_MODEL = os.getenv("GLM_MODEL", "glm4")
LITELLM_API_KEY = os.getenv("LITELLM_API_KEY", "ae-litellm-master-key-2024")


def _call_glm(system: str, user: str, max_tokens: int = 4096) -> str:
    response = completion(
        model=f"openai/{GLM_MODEL}",
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        api_base=LITELLM_BASE_URL,
        api_key=LITELLM_API_KEY,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content


def _parse_json(raw: str):
    """Robustly extract and parse JSON from LLM output."""
    raw = raw.strip()
    # Strip markdown fences
    raw = re.sub(r"```(?:json)?", "", raw)
    raw = raw.strip().strip("`").strip()
    # Try direct parse
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    # Find outermost JSON object
    for start_char, end_char in [('{', '}'), ('[', ']')]:
        start = raw.find(start_char)
        end = raw.rfind(end_char)
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(raw[start:end+1])
            except json.JSONDecodeError:
                pass
    # Final fallback — fix common escape issues
    try:
        fixed = raw.replace('\\"', '"').replace('\\n', '\n')
        return json.loads(fixed)
    except Exception:
        pass
    raise ValueError(f"Could not parse JSON from GLM output:\n{raw[:300]}")


def formalize_spec(request: str) -> dict:
    system = (
        "You are a software architect. Respond with ONLY valid JSON. "
        "No markdown. No explanation. No code fences. Just raw JSON.\n"
        "JSON structure:\n"
        '{"title": "string", "description": "string", '
        '"acceptance_criteria": ["string"], "tech_stack": ["string"]}'
    )
    result = _call_glm(system, f"Formalize this request:\n{request}")
    return _parse_json(result)


def plan_tasks(spec: dict) -> list:
    system = (
        "You are a senior engineer. Respond with ONLY a valid JSON array. "
        "No markdown. No explanation. No code fences. Just raw JSON array.\n"
        "Each item:\n"
        '{"id": "1", "description": "string", '
        '"files_to_modify": ["filepath"], "test_required": true}'
    )
    result = _call_glm(system, f"Break into coding tasks:\n{json.dumps(spec, indent=2)}")
    parsed = _parse_json(result)
    return parsed if isinstance(parsed, list) else [parsed]


def generate_code(task: dict, repo_context: str = "", past_failures: str = "") -> dict:
    system = (
        "You are an expert Python developer. Respond with ONLY valid JSON. "
        "No markdown. No explanation. No code fences. Just raw JSON.\n"
        "JSON structure:\n"
        '{"files": {"filepath": "file content as string"}, '
        '"tests": {"test_filepath": "test content as string"}}\n'
        "Use \\n for newlines inside file content strings."
    )
    prompt = f"Generate complete working code for:\n{json.dumps(task, indent=2)}"
    if repo_context:
        prompt += f"\n\nRepo context:\n{repo_context}"
    if past_failures:
        prompt += f"\n\nAvoid these past failures:\n{past_failures}"
    result = _call_glm(system, prompt, max_tokens=8192)
    parsed = _parse_json(result)
    if "files" not in parsed:
        parsed["files"] = {}
    if "tests" not in parsed:
        parsed["tests"] = {}
    return parsed


def fix_ci_failure_code(failure_report: str, current_code: str, past_fixes: str = "") -> dict:
    system = (
        "You are an expert debugger. Respond with ONLY valid JSON. "
        "No markdown. No explanation. No code fences.\n"
        "JSON structure:\n"
        '{"files": {"filepath": "fixed file content"}, "explanation": "string"}'
    )
    prompt = (
        f"Fix these CI failures:\n{failure_report}\n\n"
        f"Current code:\n{current_code}"
    )
    if past_fixes:
        prompt += f"\n\nPast successful fixes:\n{past_fixes}"
    result = _call_glm(system, prompt, max_tokens=8192)
    parsed = _parse_json(result)
    if "files" not in parsed:
        parsed["files"] = {}
    return parsed
