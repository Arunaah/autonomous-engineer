"""
GitHub Integration — PR creation, commit pushing, CI polling.
"""
from __future__ import annotations

import os
import time
from typing import Optional

import structlog
from github import Github, GithubException
from github.Repository import Repository

log = structlog.get_logger()

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
GITHUB_REPO = os.environ["GITHUB_REPO"]

_gh = Github(GITHUB_TOKEN)


def get_repo() -> Repository:
    return _gh.get_repo(GITHUB_REPO)


def create_or_update_pr(
    branch: str,
    title: str,
    body: str,
    base: str = "main",
) -> int:
    repo = get_repo()
    # Check if PR already exists
    prs = repo.get_pulls(state="open", head=f"{repo.owner.login}:{branch}")
    for pr in prs:
        pr.edit(title=title, body=body)
        log.info("pr_updated", pr_number=pr.number)
        return pr.number

    pr = repo.create_pull(title=title, body=body, head=branch, base=base)
    log.info("pr_created", pr_number=pr.number, url=pr.html_url)
    return pr.number


def merge_pr(pr_number: int, commit_message: str = "Auto-merge: confidence ≥ 95%") -> bool:
    repo = get_repo()
    pr = repo.get_pull(pr_number)
    try:
        pr.merge(commit_message=commit_message, merge_method="squash")
        log.info("pr_merged", pr_number=pr_number)
        return True
    except GithubException as e:
        log.error("pr_merge_failed", error=str(e))
        return False


def poll_ci_status(
    pr_number: int,
    timeout: int = 1800,
    poll_interval: int = 30,
) -> dict:
    """
    Poll GitHub Actions CI status for a PR.
    Returns structured CI report consumed by the fix loop.
    """
    repo = get_repo()
    pr = repo.get_pull(pr_number)
    start = time.time()

    while time.time() - start < timeout:
        commit = repo.get_commit(pr.head.sha)
        check_runs = commit.get_check_runs()

        statuses = {}
        all_complete = True

        for run in check_runs:
            statuses[run.name] = {
                "status": run.status,
                "conclusion": run.conclusion,
                "details_url": run.details_url,
            }
            if run.status != "completed":
                all_complete = False

        if all_complete:
            failed = [
                name for name, s in statuses.items()
                if s["conclusion"] not in ("success", "skipped", "neutral")
            ]
            log.info("ci_complete", failed_checks=failed)
            return {
                "complete": True,
                "passed": len(failed) == 0,
                "failed_checks": failed,
                "statuses": statuses,
            }

        log.info("ci_polling", elapsed=int(time.time() - start))
        time.sleep(poll_interval)

    return {"complete": False, "passed": False, "error": "CI timeout"}
