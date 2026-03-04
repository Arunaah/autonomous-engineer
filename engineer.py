#!/usr/bin/env python3
"""Ultra Lean Autonomous Software Engineer - CLI"""
import sys, os, json, time, requests
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich import box

console = Console()
AE_BASE_URL = os.getenv("AE_BASE_URL", "http://localhost:8000")

BANNER = """
Ultra Lean Autonomous Software Engineer  v1.0
GLM-4 * LangGraph * GitHub Actions * Docker
"""

def print_banner():
    console.print(Panel(BANNER.strip(), style="bold cyan", box=box.DOUBLE))

def check_engine():
    try:
        r = requests.get(f"{AE_BASE_URL}/health", timeout=5)
        return r.status_code == 200
    except Exception:
        return False

def start_build(prompt: str) -> int:
    r = requests.post(f"{AE_BASE_URL}/build", json={"request": prompt}, timeout=10)
    r.raise_for_status()
    return r.json()["run_id"]

def get_status(run_id: int) -> dict:
    r = requests.get(f"{AE_BASE_URL}/status/{run_id}", timeout=5)
    return r.json()

def poll_until_done(run_id: int) -> dict:
    stages = [
        "Formalizing requirements...",
        "Planning architecture...",
        "Generating source code...",
        "Creating pull request...",
        "Running CI pipeline...",
        "Computing confidence score...",
        "Auto-merging and deploying...",
    ]
    stage_idx = 0
    with Progress(SpinnerColumn(), TextColumn("[bold cyan]{task.description}"),
                  BarColumn(), TextColumn("[bold white]{task.fields[status]}"),
                  console=console) as progress:
        task = progress.add_task(stages[0], total=len(stages), status="running")
        start = time.time()
        while True:
            elapsed = time.time() - start
            status = get_status(run_id)
            state = status.get("status", "running")
            new_idx = min(int(elapsed / 15), len(stages) - 1)
            if new_idx > stage_idx:
                stage_idx = new_idx
                progress.update(task, description=stages[stage_idx],
                                completed=stage_idx, status=state)
            if state in ("deployed", "error", "max_iterations_reached"):
                progress.update(task, description="Complete!",
                                completed=len(stages), status=state)
                return status
            if elapsed > 1800:
                return {"status": "timeout", "run_id": run_id}
            time.sleep(10)

def print_result(prompt: str, result: dict):
    status = result.get("status", "unknown")
    conf   = result.get("confidence", 0)
    pr     = result.get("pr_number")
    iters  = result.get("iterations", 0)
    if status == "deployed":
        console.print(Panel(
            f"[bold green]SUCCESSFULLY DEPLOYED[/bold green]\n\n"
            f"Prompt    : [yellow]{prompt}[/yellow]\n"
            f"PR        : [cyan]https://github.com/Arunaah/autonomous-engineer/pull/{pr}[/cyan]\n"
            f"Confidence: [bold green]{conf}/100[/bold green]\n"
            f"Iterations: {iters}\n"
            f"Status    : [bold green]Auto-merged[/bold green]",
            title="DEPLOYMENT SUCCESSFUL", box=box.DOUBLE, style="green"))
        console.print(f"\n[bold cyan]Your generated code is live at:[/bold cyan]")
        console.print(f"   https://github.com/Arunaah/autonomous-engineer\n")
    else:
        console.print(Panel(
            f"[red]Status: {status}[/red]\n"
            f"Confidence: {conf}/100  |  Iterations: {iters}\n"
            f"[yellow]Check GitHub Actions for CI logs.[/yellow]",
            title="BUILD INCOMPLETE", box=box.DOUBLE, style="red"))

def print_help():
    table = Table(title="CLI Commands", box=box.ROUNDED, style="cyan")
    table.add_column("Command", style="bold yellow")
    table.add_column("Description", style="white")
    table.add_row('engineer "your prompt"',  "Build a complete software project")
    table.add_row('engineer --status <id>',  "Check status of a run")
    table.add_row('engineer --runs',         "List all past runs")
    table.add_row('engineer --help',         "Show this help")
    console.print(table)

def list_runs():
    r = requests.get(f"{AE_BASE_URL}/runs", timeout=5)
    runs = r.json()
    table = Table(title="All Runs", box=box.ROUNDED, style="cyan")
    table.add_column("ID",         style="bold yellow")
    table.add_column("Status",     style="bold")
    table.add_column("Confidence", style="bold green")
    table.add_column("PR",         style="cyan")
    table.add_column("Request",    style="white")
    for run in runs[-10:]:
        s = run.get("status", "?")
        color = "green" if s == "deployed" else "red" if s == "error" else "yellow"
        table.add_row(str(run.get("run_id","?")),
            f"[{color}]{s}[/{color}]",
            str(run.get("confidence", "-")),
            f"#{run.get('pr_number','-')}",
            str(run.get("request",""))[:60])
    console.print(table)

def main():
    print_banner()
    args = sys.argv[1:]
    if not args or "--help" in args or "-h" in args:
        print_help()
        return
    if "--runs" in args:
        if not check_engine():
            console.print("[red]Engine not running. Start Docker first.[/red]")
            return
        list_runs()
        return
    if "--status" in args:
        idx = args.index("--status")
        if idx + 1 < len(args):
            result = get_status(int(args[idx + 1]))
            console.print_json(json.dumps(result))
        return

    prompt = " ".join(args).strip().strip('"').strip("'")
    if not prompt:
        console.print("[red]Please provide a prompt.[/red]")
        return

    console.print(f"\n[bold cyan]Prompt:[/bold cyan] [yellow]{prompt}[/yellow]\n")
    console.print("[white]Checking engine...[/white]", end=" ")
    if not check_engine():
        console.print("[red]OFFLINE[/red]")
        console.print("\n[yellow]Start Docker stack first:[/yellow]")
        console.print("[cyan]  cd C:\\Users\\mrleo\\Downloads\\autonomous-engineer[/cyan]")
        console.print("[cyan]  docker compose up -d[/cyan]\n")
        return
    console.print("[green]ONLINE[/green]\n")

    console.print("[bold white]Launching autonomous engineering pipeline...[/bold white]\n")
    run_id = start_build(prompt)
    console.print(f"[cyan]Run ID: {run_id}[/cyan]\n")
    result = poll_until_done(run_id)
    print_result(prompt, result)

if __name__ == "__main__":
    main()
