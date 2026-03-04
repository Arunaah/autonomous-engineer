"""Unified Builder Agent — GLM-5 via LiteLLM/Ollama."""
import os, json
from litellm import completion

LITELLM_BASE_URL = os.getenv("LITELLM_BASE_URL", "http://localhost:4000")
GLM_MODEL = os.getenv("GLM_MODEL", "glm4")


def _call_glm(system: str, user: str, max_tokens: int = 4096) -> str:
    response = completion(
        model=f"openai/{GLM_MODEL}",
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        api_base=LITELLM_BASE_URL,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content


def formalize_spec(request: str) -> dict:
    system = "You are a software architect. Return ONLY valid JSON with keys: title, description, acceptance_criteria (list), tech_stack (list)."
    result = _call_glm(system, f"Formalize this request into a spec:\n{request}")
    return json.loads(result)


def plan_tasks(spec: dict) -> list[dict]:
    system = "You are a senior engineer. Return ONLY a JSON array of tasks with keys: id, description, files_to_modify (list), test_required (bool)."
    result = _call_glm(system, f"Break this spec into tasks:\n{json.dumps(spec, indent=2)}")
    return json.loads(result)


def generate_code(task: dict, repo_context: str = "", past_failures: str = "") -> dict:
    system = "You are an expert Python developer. Return ONLY valid JSON with keys: files (dict of filepath->content), tests (dict of filepath->content)."
    prompt = f"Task:\n{json.dumps(task, indent=2)}\n\nRepo context:\n{repo_context}"
    if past_failures:
        prompt += f"\n\nAvoid these past failures:\n{past_failures}"
    result = _call_glm(system, prompt, max_tokens=8192)
    return json.loads(result)
