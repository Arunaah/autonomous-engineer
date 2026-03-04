"""GitHub API utilities — create PRs, push files, wait for CI."""
import os, time, base64, logging
from github import Github

logger = logging.getLogger("ae.github")

GITHUB_TOKEN    = os.getenv("GITHUB_TOKEN")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME", "arunaah")
GITHUB_REPO     = os.getenv("GITHUB_REPO", "autonomous-engineer")

gh = Github(GITHUB_TOKEN)


def get_repo():
    return gh.get_repo(f"{GITHUB_USERNAME}/{GITHUB_REPO}")


def push_files(files: dict, title: str, iteration: int) -> dict:
    repo = get_repo()
    safe_title = title.lower().replace(" ", "-")[:30]
    branch = f"ae/{safe_title}-iter{iteration}-{int(time.time())}"
    default = repo.get_branch(repo.default_branch)
    try:
        repo.create_git_ref(ref=f"refs/heads/{branch}", sha=default.commit.sha)
    except Exception:
        pass

    for filepath, content in files.items():
        if not isinstance(content, str):
            content = str(content)
        try:
            existing = repo.get_contents(filepath, ref=branch)
            repo.update_file(filepath, f"ae: update {filepath}", content,
                             existing.sha, branch=branch)
        except Exception:
            repo.create_file(filepath, f"ae: create {filepath}", content, branch=branch)

    return {"branch": branch}


def create_pull_request(branch: str, spec: dict) -> int:
    repo = get_repo()
    # Close any existing open PRs from same spec to avoid clutter
    try:
        title = f"[AE] {spec.get('title', 'Auto-generated')}"
        body = (
            f"## Autonomous Engineer PR\n\n"
            f"{spec.get('description', '')}\n\n"
            f"### Acceptance Criteria\n" +
            "\n".join(f"- {c}" for c in spec.get("acceptance_criteria", []))
        )
        pr = repo.create_pull(title=title, body=body,
                              head=branch, base=repo.default_branch)
        logger.info(f"Created PR #{pr.number}: {title}")
        return pr.number
    except Exception as e:
        logger.error(f"PR creation error: {e}")
        raise


def wait_for_ci(pr_number: int, timeout: int = 1800) -> dict:
    """Poll GitHub Actions until all checks complete."""
    repo = get_repo()
    start = time.time()
    logger.info(f"Waiting for CI on PR #{pr_number}...")

    while time.time() - start < timeout:
        try:
            pr = repo.get_pull(pr_number)
            commit = repo.get_commit(pr.head.sha)
            checks = list(commit.get_check_runs())

            if not checks:
                logger.info("No checks yet, waiting...")
                time.sleep(30)
                continue

            all_done = all(c.status == "completed" for c in checks)
            if not all_done:
                done = sum(1 for c in checks if c.status == "completed")
                logger.info(f"CI progress: {done}/{len(checks)} checks done")
                time.sleep(30)
                continue

            # All checks done — parse results
            results = []
            raw_output_parts = []
            for c in checks:
                conclusion = c.conclusion or "failure"
                output_text = c.output.text if c.output and c.output.text else ""
                results.append({
                    "name": c.name,
                    "conclusion": conclusion,
                    "output": output_text
                })
                raw_output_parts.append(f"=== {c.name} === {conclusion}\n{output_text}")

            raw_output = "\n".join(raw_output_parts)
            passed = all(r["conclusion"] in ("success", "neutral") for r in results)
            failed_stages = [r["name"] for r in results
                             if r["conclusion"] not in ("success", "neutral")]

            from confidence.engine import parse_ci_output
            parsed = parse_ci_output(raw_output)
            parsed["passed"] = passed
            parsed["diff"] = get_pr_diff(pr_number)
            parsed["stage"] = failed_stages[0] if failed_stages else "all_passed"
            parsed["failures"] = failed_stages

            logger.info(f"CI complete. Passed: {passed}. Failed: {failed_stages}")
            return parsed

        except Exception as e:
            logger.error(f"CI polling error: {e}")
            time.sleep(30)

    logger.warning(f"CI timeout after {timeout}s for PR #{pr_number}")
    return {
        "passed": False,
        "stage_scores": {"static": 0.5, "coverage": 0.5,
                         "production": 0.5, "stress": 0.5},
        "failures": ["CI timeout"],
        "diff": ""
    }


def get_pr_diff(pr_number: int) -> str:
    try:
        repo = get_repo()
        pr = repo.get_pull(pr_number)
        files = pr.get_files()
        return "\n".join(f.patch or "" for f in files if f.patch)
    except Exception:
        return ""


def merge_pr(pr_number: int):
    repo = get_repo()
    pr = repo.get_pull(pr_number)
    pr.merge(merge_method="squash",
             commit_message=f"[AE] Auto-merged PR #{pr_number} ✅")
    logger.info(f"PR #{pr_number} merged successfully!")


def close_stale_prs():
    """Close all open AE PRs to clean up."""
    repo = get_repo()
    prs = repo.get_pulls(state="open")
    for pr in prs:
        if pr.title.startswith("[AE]"):
            pr.edit(state="closed")
            logger.info(f"Closed stale PR #{pr.number}")
