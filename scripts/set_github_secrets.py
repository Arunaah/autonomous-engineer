"""Set all required GitHub Actions secrets for the autonomous engineer."""
import os, requests, base64
from nacl import encoding, public

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
REPO = "arunaah/autonomous-engineer"
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}

SECRETS = {
    "LITELLM_API_KEY": "ae-litellm-master-key-2024",
    "DATABASE_URL": "postgresql://ae_user:ae_secure_pass_2024@ae-postgres:5432/autonomous_engineer",
    "GLM_MODEL": "glm4",
}

def encrypt_secret(public_key_str: str, secret_value: str) -> str:
    pk = public.PublicKey(public_key_str.encode("utf-8"), encoding.Base64Encoder())
    box = public.SealedBox(pk)
    return base64.b64encode(box.encrypt(secret_value.encode("utf-8"))).decode("utf-8")

def set_secret(name, value, key_id, pub_key):
    encrypted = encrypt_secret(pub_key, value)
    url = f"https://api.github.com/repos/{REPO}/actions/secrets/{name}"
    resp = requests.put(url, headers=HEADERS, json={"encrypted_value": encrypted, "key_id": key_id})
    print(f"  {'OK' if resp.status_code in (201,204) else 'FAIL '+str(resp.status_code)} {name}")

r = requests.get(f"https://api.github.com/repos/{REPO}/actions/secrets/public-key", headers=HEADERS)
r.raise_for_status()
k = r.json()
print(f"Setting {len(SECRETS)} secrets for {REPO}...")
for name, value in SECRETS.items():
    set_secret(name, value, k["key_id"], k["key"])
print("Done.")
