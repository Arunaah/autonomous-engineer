"""
CLI Entry Point — Run the Autonomous Engineer from terminal.
Usage: ae run --repo owner/repo --request "Add user authentication"
"""
from __future__ import annotations

import asyncio
import json

import structlog
import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from agent.graph import autonomous_graph as agent_graph
from retrieval.indexer import build_index

app = typer.Typer(name="ae", help="Autonomous Engineer — beats Claude Code")
console = Console()
log = structlog.get_logger()


@app.command()
def run(
    repo: str = typer.Option(..., help="GitHub repo (owner/repo)"),
    request: str = typer.Option(..., help="Natural language coding request"),
    repo_path: str = typer.Option(".", help="Local path to repo for indexing"),
    index: bool = typer.Option(True, help="Build/rebuild codebase index"),
):
    """Run the autonomous engineer on a coding request."""
    console.print(Panel.fit(
        f"[bold green]🤖 Autonomous Engineer[/]\n"
        f"Repo: [cyan]{repo}[/]\n"
        f"Request: [yellow]{request}[/]",
        title="Starting",
    ))

    async def _run():
        # Phase 1: Build semantic codebase index
        if index:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Building codebase index...", total=None)
                build_index(repo_path)
                progress.update(task, description="✅ Codebase indexed")

        # Phase 2: Run the agent graph
        initial_state = {
            "repo": repo,
            "pr_number": 0,
            "user_request": request,
            "spec": "",
            "plan": "",
            "code_changes": [],
            "pr_url": "",
            "ci_report": {},
            "confidence": 0.0,
            "iteration": 1,
            "fix_history": [],
            "final_status": "",
            "messages": [],
        }

        console.print("\n[bold]🔄 Running agent graph...[/]")
        final_state = await agent_graph.ainvoke(initial_state)

        # Display results
        status = final_state.get("final_status", "unknown")
        confidence = final_state.get("confidence", 0)
        iterations = final_state.get("iteration", 1)

        if status == "success" or confidence >= 95:
            console.print(Panel.fit(
                f"[bold green]✅ SUCCESS[/]\n"
                f"Confidence: {confidence:.1f}%\n"
                f"Iterations: {iterations}\n"
                f"PR: {final_state.get('pr_url', 'N/A')}",
                title="Complete",
            ))
        else:
            console.print(Panel.fit(
                f"[bold red]❌ FAILED[/]\n"
                f"Confidence: {confidence:.1f}%\n"
                f"Iterations: {iterations}\n"
                f"Fix History:\n" + "\n".join(final_state.get("fix_history", [])),
                title="Failed",
            ))

    asyncio.run(_run())


@app.command()
def index_repo(
    repo_path: str = typer.Argument(".", help="Path to repository to index"),
):
    """Build semantic index for a repository."""
    console.print(f"[bold]Indexing {repo_path}...[/]")
    build_index(repo_path)
    console.print("[green]✅ Index built successfully[/]")


if __name__ == "__main__":
    app()
