"""Pull GLM-4 model into Ollama — run once after docker-compose up."""
import httpx, time, sys

OLLAMA_URL = "http://localhost:11435"


def pull_glm4():
    print("[AE] Pulling GLM-4 open source model via Ollama...")
    with httpx.stream("POST", f"{OLLAMA_URL}/api/pull", json={"name": "glm4"}, timeout=None) as r:
        for line in r.iter_lines():
            if line:
                print(line)
    print("[AE] GLM-4 pull complete!")


def wait_for_ollama(retries=30):
    for i in range(retries):
        try:
            r = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=5)
            if r.status_code == 200:
                print("[AE] Ollama is ready.")
                return True
        except Exception:
            pass
        print(f"[AE] Waiting for Ollama... ({i+1}/{retries})")
        time.sleep(5)
    return False


if __name__ == "__main__":
    if wait_for_ollama():
        pull_glm4()
    else:
        print("[AE] ERROR: Ollama not reachable. Is docker-compose up?")
        sys.exit(1)
