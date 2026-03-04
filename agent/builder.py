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
    """Robustly extract and parse JSON from LLM output — handles all GLM-4 quirks."""
    raw = raw.strip()
    # Strip markdown fences
    raw = re.sub(r"```(?:json)?", "", raw).strip().strip("`").strip()
    # Fix double-escaped quotes from GLM-4: \\\" -> \"
    raw = raw.replace('\\\\"', '\\"').replace("\\\\'", "\\'")
    # Try direct parse first
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    # Extract outermost JSON object or array
    for start_char, end_char in [('{', '}'), ('[', ']')]:
        start = raw.find(start_char)
        end = raw.rfind(end_char)
        if start != -1 and end != -1 and end > start:
            chunk = raw[start:end+1]
            try:
                return json.loads(chunk)
            except json.JSONDecodeError:
                # Try fixing common issues: unescaped newlines inside strings
                try:
                    fixed = re.sub(r'(?<!\\)\n', '\\n', chunk)
                    return json.loads(fixed)
                except Exception:
                    pass
    # Last resort: extract key-value pairs manually for code generation
    files = {}
    tests = {}
    file_matches = re.findall(r'"([^"]+\.py)"\s*:\s*"((?:[^"\\]|\\.)*)"', raw)
    for fname, content in file_matches:
        content = content.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
        if 'test' in fname.lower():
            tests[fname] = content
        else:
            files[fname] = content
    if files or tests:
        return {"files": files, "tests": tests}
    raise ValueError(f"Could not parse JSON from GLM output:\n{raw[:500]}")

def formalize_spec(request: str) -> dict:
    system = (
        "You are a software architect. Respond with ONLY valid JSON. "
        "No markdown. No explanation. No code fences. Just raw JSON.\n"
        'Structure: {"title":"string","description":"string",'
        '"acceptance_criteria":["string"],"tech_stack":["string"]}'
    )
    result = _call_glm(system, f"Formalize this software request:\n{request}")
    return _parse_json(result)


def plan_tasks(spec: dict) -> list:
    system = (
        "You are a senior engineer. Respond with ONLY a valid JSON array. "
        "No markdown. No explanation. No code fences. Just raw JSON array.\n"
        'Each item: {"id":"1","description":"string","files_to_modify":["filepath"],"test_required":true}'
    )
    result = _call_glm(system, f"Break into coding tasks:\n{json.dumps(spec, indent=2)}")
    parsed = _parse_json(result)
    return parsed if isinstance(parsed, list) else [parsed]


def generate_code(task: dict, repo_context: str = "", past_failures: str = "") -> dict:
    system = (
        "You are an expert Python developer. Respond with ONLY valid JSON. "
        "No markdown. No code fences. Just raw JSON.\n"
        'Structure: {"files":{"filepath":"full file content"},"tests":{"test_filepath":"test content"}}\n'
        "IMPORTANT: Inside JSON string values, escape newlines as \\n and quotes as \\\"."
    )
    prompt = f"Generate complete working Python code for this task:\n{json.dumps(task, indent=2)}"
    if repo_context:
        prompt += f"\n\nExisting repo context:\n{repo_context}"
    if past_failures:
        prompt += f"\n\nAvoid these past failures:\n{past_failures}"
    result = _call_glm(system, prompt, max_tokens=8192)
    parsed = _parse_json(result)
    parsed.setdefault("files", {})
    parsed.setdefault("tests", {})
    return parsed


def fix_ci_failure_code(failure_report: str, current_code: str, past_fixes: str = "") -> dict:
    system = (
        "You are an expert debugger. Respond with ONLY valid JSON. "
        "No markdown. No code fences.\n"
        'Structure: {"files":{"filepath":"fixed content"},"explanation":"string"}'
    )
    prompt = f"Fix these CI failures:\n{failure_report}\n\nCurrent code:\n{current_code}"
    if past_fixes:
        prompt += f"\n\nPast successful fixes:\n{past_fixes}"
    result = _call_glm(system, prompt, max_tokens=8192)
    parsed = _parse_json(result)
    parsed.setdefault("files", {})
    return parsed
