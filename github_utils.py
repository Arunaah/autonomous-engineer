"""GitHub API utilities — create PRs, push files, wait for CI."""
import os, time, base64
from github import Github

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME", "arunaah")
GITHUB_REPO = os.getenv("GITHUB_REPO", "autonomous-engineer")

gh = Github(GITHUB_TOKEN)


def get_repo():
    return gh.get_repo(f"{GITHUB_USERNAME}/{GITHUB_REPO}")


def push_files(files: dict, title: str, iteration: int) -> dict:
    repo = get_repo()
    branch = f"ae/auto-{title.lower().replace(' ', '-')[:30]}-iter{iteration}"
    default = repo.get_branch(repo.default_branch)
    try:
        repo.create_git_ref(ref=f"refs/heads/{branch}", sha=default.commit.sha)
    except Exception:
        pass  # branch already exists

    for filepath, content in files.items():
        try:
            existing = repo.get_contents(filepath, ref=branch)
            repo.update_file(filepath, f"ae: update {filepath}", content, existing.sha, branch=branch)
        except Exception:
            repo.create_file(filepath, f"ae: create {filepath}", content, branch=branch)

    return {"branch": branch}


def create_pull_request(branch: str, spec: dict) -> int:
    repo = get_repo()
    pr = repo.create_pull(
        title=f"[AE] {spec.get('title', 'Auto-generated')}",
        body=f"## Autonomous Engineer PR\n\n{spec.get('description', '')}\n\n### Acceptance Criteria\n" +
             "\n".join(f"- {c}" for c in spec.get("acceptance_criteria", [])),
        head=branch,
        base=repo.default_branch
    )
    return pr.number

def wait_for_ci(pr_number: int, timeout: int = 1800) -> dict:
    """Poll GitHub Actions until CI completes or timeout."""
    repo = get_repo()
    start = time.time()
    while time.time() - start < timeout:
        pr = repo.get_pull(pr_number)
        commit = repo.get_commit(pr.head.sha)
        checks = commit.get_check_runs()
        all_done = all(c.status == "completed" for c in checks)
        if all_done:
            results = []
            for c in checks:
                results.append({"name": c.name, "conclusion": c.conclusion, "output": c.output.text or ""})
            passed = all(r["conclusion"] == "success" for r in results)
            raw_output = "\n".join(r["output"] for r in results)
            from confidence.engine import parse_ci_output
            parsed = parse_ci_output(raw_output)
            parsed["passed"] = passed
            parsed["diff"] = get_pr_diff(pr_number)
            parsed["stage"] = next((r["name"] for r in results if r["conclusion"] != "success"), "all_passed")
            return parsed
        time.sleep(30)
    return {"passed": False, "stage_scores": {}, "failures": ["CI timeout"], "diff": ""}


def get_pr_diff(pr_number: int) -> str:
    repo = get_repo()
    pr = repo.get_pull(pr_number)
    files = pr.get_files()
    return "\n".join(f.patch or "" for f in files)


def merge_pr(pr_number: int):
    repo = get_repo()
    pr = repo.get_pull(pr_number)
    pr.merge(merge_method="squash", commit_message=f"[AE] Auto-merged PR #{pr_number}")
