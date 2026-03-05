"""GitHub API utilities — create PRs, push files, wait for CI."""
import os, time, logging
from github import Github

logger = logging.getLogger("ae.github")

GITHUB_TOKEN    = os.getenv("GITHUB_TOKEN")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME", "arunaah")
GITHUB_REPO     = os.getenv("GITHUB_REPO", "autonomous-engineer")

# The check names that belong to the NEW Ultra Lean AE workflow
AE_STAGE_NAMES = {
    "Stage 1",   # Stage 1 · Static + Security
    "Stage 2",   # Stage 2 · Tests + Coverage
    "Stage 3",   # Stage 3 · Production Simulation
    "Stage 4",   # Stage 4 · Stress Tests
    "Stage 5",   # Stage 5 · Confidence Engine
}

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
            repo.update_file(filepath, f"ae: update {filepath}",
                             content, existing.sha, branch=branch)
        except Exception:
            repo.create_file(filepath, f"ae: create {filepath}",
                             content, branch=branch)
    return {"branch": branch}


def create_pull_request(branch: str, spec: dict) -> int:
    repo = get_repo()
    title = f"[AE] {spec.get('title', 'Auto-generated')}"
    body  = (
        f"## Autonomous Engineer PR\n\n"
        f"{spec.get('description', '')}\n\n"
        f"### Acceptance Criteria\n" +
        "\n".join(f"- {c}" for c in spec.get("acceptance_criteria", []))
    )
    try:
        pr = repo.create_pull(title=title, body=body,
                              head=branch, base=repo.default_branch)
        logger.info(f"Created PR #{pr.number}: {title}")
        return pr.number
    except Exception as e:
        logger.error(f"PR creation error: {e}")
        raise


def _is_ae_check(check_name: str) -> bool:
    """Only process checks from the new Ultra Lean AE workflow."""
    name = check_name.strip()
    # Match "Stage 1 · ..." or "Stage 1 — ..." patterns
    for prefix in AE_STAGE_NAMES:
        if name.startswith(prefix):
            return True
    return False


def wait_for_ci(pr_number: int, timeout: int = 1800) -> dict:
    """Poll GitHub Actions until the AE workflow checks complete."""
    repo  = get_repo()
    start = time.time()
    logger.info(f"Waiting for CI on PR #{pr_number}...")

    while time.time() - start < timeout:
        try:
            pr     = repo.get_pull(pr_number)
            commit = repo.get_commit(pr.head.sha)
            all_checks = list(commit.get_check_runs())

            if not all_checks:
                logger.info("No checks yet, waiting...")
                time.sleep(30)
                continue

            # Filter: only the new AE workflow stages
            ae_checks = [c for c in all_checks if _is_ae_check(c.name)]

            if not ae_checks:
                # Workflow hasn't started yet — wait
                done = sum(1 for c in all_checks if c.status == "completed")
                logger.info(f"AE workflow not started yet. "
                            f"Total checks: {done}/{len(all_checks)}")
                time.sleep(30)
                continue

            all_done = all(c.status == "completed" for c in ae_checks)
            if not all_done:
                done = sum(1 for c in ae_checks if c.status == "completed")
                logger.info(f"CI progress: {done}/{len(ae_checks)} AE checks done")
                time.sleep(30)
                continue

            # All AE checks done — parse results
            # "skipped" = success (stage was intentionally skipped)
            PASS = ("success", "neutral", "skipped")
            results = []
            raw_parts = []
            for c in ae_checks:
                conclusion  = c.conclusion or "failure"
                output_text = (c.output.text or "") if c.output else ""
                results.append({
                    "name":       c.name,
                    "conclusion": conclusion,
                    "output":     output_text,
                })
                raw_parts.append(
                    f"=== {c.name} === {conclusion}\n{output_text}")

            raw_output   = "\n".join(raw_parts)
            passed       = all(r["conclusion"] in PASS for r in results)
            failed_names = [r["name"] for r in results
                            if r["conclusion"] not in PASS]

            from confidence.engine import parse_ci_output
            parsed = parse_ci_output(raw_output)
            parsed["passed"]   = passed
            parsed["diff"]     = get_pr_diff(pr_number)
            parsed["stage"]    = failed_names[0] if failed_names else "all_passed"
            parsed["failures"] = failed_names

            logger.info(f"CI complete. Passed: {passed}. "
                        f"Failed AE stages: {failed_names}")
            return parsed

        except Exception as e:
            logger.error(f"CI polling error: {e}")
            time.sleep(30)

    logger.warning(f"CI timeout after {timeout}s for PR #{pr_number}")
    return {
        "passed": False,
        "stage_scores": {"static": 0.5, "coverage": 0.5,
                         "production": 0.5, "stress": 0.5},
        "failures": ["CI timeout"], "diff": "",
    }


def get_pr_diff(pr_number: int) -> str:
    try:
        repo  = get_repo()
        pr    = repo.get_pull(pr_number)
        files = pr.get_files()
        return "\n".join(f.patch or "" for f in files if f.patch)
    except Exception:
        return ""


def merge_pr(pr_number: int):
    repo = get_repo()
    pr   = repo.get_pull(pr_number)
    pr.merge(merge_method="squash",
             commit_message=f"[AE] Auto-merged PR #{pr_number}")
    logger.info(f"PR #{pr_number} merged successfully!")


def close_stale_prs():
    repo = get_repo()
    for pr in repo.get_pulls(state="open"):
        if pr.title.startswith("[AE]"):
            pr.edit(state="closed")
            logger.info(f"Closed stale PR #{pr.number}")
