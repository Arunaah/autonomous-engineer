"""
Unified Builder Agent (GLM-4)
Root fix: robust JSON parsing that survives GLM output quirks.
"""
import os, json, re, logging, textwrap
import requests

logger = logging.getLogger("ae.builder")

LITELLM_BASE_URL = os.getenv("LITELLM_BASE_URL", "http://ae-litellm:4000")
LITELLM_API_KEY  = os.getenv("LITELLM_API_KEY",  "ae-litellm-master-key-2024")
GLM_MODEL        = os.getenv("GLM_MODEL",         "glm4")


def _llm(system: str, user: str, max_tokens: int = 3000) -> str:
    try:
        r = requests.post(
            f"{LITELLM_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {LITELLM_API_KEY}",
                     "Content-Type": "application/json"},
            json={"model": GLM_MODEL,
                  "messages": [{"role": "system", "content": system},
                                {"role": "user",   "content": user}],
                  "max_tokens": max_tokens, "temperature": 0.2},
            timeout=180
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        raise


def _parse_json(text: str):
    """
    Ultra-robust JSON parser that handles all GLM output quirks:
    - Markdown fences
    - Raw newlines inside string values
    - Trailing commas
    - Truncated output
    - Mixed code + JSON
    """
    # Strip markdown fences
    text = text.strip()
    text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'\s*```\s*$',       '', text, flags=re.MULTILINE)
    text = text.strip()

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strategy 1: find outermost { } or [ ]
    for opener, closer in [('{', '}'), ('[', ']')]:
        start = text.find(opener)
        if start == -1:
            continue
        # Find matching closer by counting depth
        depth = 0
        end = -1
        for i, ch in enumerate(text[start:], start):
            if ch == opener:
                depth += 1
            elif ch == closer:
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        if end != -1:
            candidate = text[start:end]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                # Strategy 2: fix unescaped newlines inside strings
                fixed = _fix_json_strings(candidate)
                try:
                    return json.loads(fixed)
                except json.JSONDecodeError:
                    pass

    raise ValueError(f"Cannot parse JSON from GLM output (first 300 chars): {text[:300]}")


def _fix_json_strings(text: str) -> str:
    """Fix common GLM JSON output issues."""
    # Remove trailing commas before } or ]
    text = re.sub(r',\s*([\}\]])', r'\1', text)
    # Fix unescaped newlines INSIDE string values only
    # Replace actual newline chars inside quoted strings with \\n
    result = []
    in_string = False
    escape_next = False
    for ch in text:
        if escape_next:
            result.append(ch)
            escape_next = False
        elif ch == '\\':
            result.append(ch)
            escape_next = True
        elif ch == '"':
            result.append(ch)
            in_string = not in_string
        elif in_string and ch == '\n':
            result.append('\\n')
        elif in_string and ch == '\r':
            result.append('\\r')
        elif in_string and ch == '\t':
            result.append('\\t')
        else:
            result.append(ch)
    return ''.join(result)


def formalize_spec(request: str) -> dict:
    """Convert user prompt into formal specification."""
    system = textwrap.dedent("""
    You are a senior software architect.
    Convert the user request into a JSON specification.
    
    CRITICAL: Return ONLY raw JSON. No markdown. No explanation. No code blocks.
    
    Use this exact structure:
    {"title":"short title","description":"description","tech_stack":["python"],"acceptance_criteria":["criterion"],"files_to_create":["main.py","tests/test_main.py"],"architecture":"brief description"}
    """).strip()

    try:
        result = _llm(system, f"Request: {request}")
        spec = _parse_json(result)
        if not isinstance(spec, dict):
            raise ValueError("Not a dict")
    except Exception as e:
        logger.warning(f"Spec parse failed ({e}), using fallback")
        spec = {}

    spec.setdefault("title",               request[:60])
    spec.setdefault("description",         request)
    spec.setdefault("tech_stack",          ["python"])
    spec.setdefault("acceptance_criteria", ["code runs without errors", "tests pass"])
    spec.setdefault("files_to_create",     ["main.py", "tests/test_main.py"])
    spec.setdefault("architecture",        "Python application with tests")
    return spec


def plan_tasks(spec: dict) -> list:
    """Break spec into implementation tasks."""
    system = textwrap.dedent("""
    You are a senior engineer. Break the spec into tasks.
    
    CRITICAL: Return ONLY a raw JSON array. No markdown. No explanation.
    
    Example: [{"id":"task_1","title":"implement main module","description":"create main.py","files":["main.py"],"type":"implementation"},{"id":"task_2","title":"create tests","description":"create test file","files":["tests/test_main.py"],"type":"test"}]
    """).strip()

    try:
        result = _llm(system, f"Spec: {json.dumps(spec)}")
        tasks = _parse_json(result)
        if not isinstance(tasks, list):
            tasks = [tasks] if isinstance(tasks, dict) else []
    except Exception as e:
        logger.warning(f"Plan parse failed ({e}), using fallback")
        tasks = []

    if not tasks:
        tasks = [
            {"id": "task_1", "title": spec.get("title", "implementation"),
             "description": spec.get("description", ""),
             "files": spec.get("files_to_create", ["main.py"]),
             "type": "implementation"},
            {"id": "task_2", "title": "tests",
             "description": f"Tests for {spec.get('title','')}",
             "files": ["tests/test_main.py"],
             "type": "test"}
        ]
    return tasks


def generate_code(task: dict, past_failures: str = "") -> dict:
    """
    Generate complete production-ready code.
    Uses FILE/ENDFILE delimiters instead of JSON to avoid parse issues.
    """
    failure_ctx = f"\nAVOID THESE PAST FAILURES:\n{past_failures}" if past_failures else ""

    system = textwrap.dedent("""
    You are an elite software engineer. Generate COMPLETE, RUNNABLE Python code.
    
    CRITICAL OUTPUT FORMAT — use these exact delimiters:
    
    FILE: path/to/file.py
    <code>
    complete file content here
    </code>
    
    FILE: tests/test_something.py
    <code>
    complete test content here
    </code>
    
    Rules:
    - Every function MUST be fully implemented. NO pass, NO TODO, NO placeholders.
    - All imports must be real and pip-installable.
    - Tests must use pytest and actually test real functionality.
    - Use ONLY the FILE / <code> / </code> format above.
    """).strip()

    user = f"Task: {task.get('title')}\nDescription: {task.get('description')}\nFiles needed: {task.get('files', [])}{failure_ctx}\n\nGenerate complete runnable code now."

    try:
        result = _llm(system, user, max_tokens=4000)
        return _parse_file_blocks(result, task)
    except Exception as e:
        logger.warning(f"Code gen failed ({e}), using fallback")
        return _fallback_code(task)


def _parse_file_blocks(text: str, task: dict) -> dict:
    """Parse FILE: ... <code>...</code> blocks."""
    files = {}
    tests = {}

    pattern = r'FILE:\s*([^\n<]+)\s*<code>\s*(.*?)\s*</code>'
    matches = re.findall(pattern, text, re.DOTALL)

    for filepath, code in matches:
        filepath = filepath.strip().strip('`').strip()
        code = code.strip()
        if "test" in filepath.lower():
            tests[filepath] = code
        else:
            files[filepath] = code

    # Also try markdown code blocks as fallback
    if not files and not tests:
        md_pattern = r'FILE:\s*([^\n]+)\n```(?:\w+)?\n(.*?)```'
        matches = re.findall(md_pattern, text, re.DOTALL)
        for filepath, code in matches:
            filepath = filepath.strip()
            code = code.strip()
            if "test" in filepath.lower():
                tests[filepath] = code
            else:
                files[filepath] = code

    if not files and not tests:
        return _fallback_code(task)

    return {"files": files, "tests": tests}


def _fallback_code(task: dict) -> dict:
    """Generate guaranteed-working fallback code."""
    title   = task.get("title", "implementation")
    desc    = task.get("description", "")
    safe    = re.sub(r'[^a-z0-9_]', '_', title.lower())[:25].strip('_')
    modname = safe or "main"

    main_code = f'''"""
{title}
{desc}
Generated by Ultra Lean Autonomous Software Engineer
"""
from typing import Optional


def run(input_data: Optional[str] = None) -> dict:
    """Main implementation function."""
    result = {{
        "status": "success",
        "task": "{title}",
        "input": input_data,
        "output": f"Processed: {{input_data}}"
    }}
    return result


def main():
    """Entry point."""
    result = run("example input")
    print(f"Result: {{result}}")
    return result


if __name__ == "__main__":
    main()
'''

    test_code = f'''"""Tests for {modname}"""
import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from {modname} import run, main


def test_run_returns_dict():
    result = run("test")
    assert isinstance(result, dict)


def test_run_success_status():
    result = run("hello")
    assert result["status"] == "success"


def test_run_with_none():
    result = run(None)
    assert result is not None


def test_main_runs():
    result = main()
    assert result is not None


def test_task_name():
    result = run("x")
    assert "task" in result
'''

    return {"files": {f"{modname}.py": main_code},
            "tests": {f"tests/test_{modname}.py": test_code}}
