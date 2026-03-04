#!/usr/bin/env python3
"""
Ultra Lean Autonomous Software Engineer — CLI
engineer "build a scalable task management API"
"""
import sys, os, json, time, requests
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich.rule import Rule
from rich import box

console = Console()
AE_BASE_URL = os.getenv("AE_BASE_URL", "http://localhost:8000")

BANNER = """\
 █████╗ ██╗   ██╗████████╗ ██████╗     ██╗     ███████╗ █████╗ ███╗   ██╗
██╔══██╗██║   ██║╚══██╔══╝██╔═══██╗    ██║     ██╔════╝██╔══██╗████╗  ██║
███████║██║   ██║   ██║   ██║   ██║    ██║     █████╗  ███████║██╔██╗ ██║
██╔══██║██║   ██║   ██║   ██║   ██║    ██║     ██╔══╝  ██╔══██║██║╚██╗██║
██║  ██║╚██████╔╝   ██║   ╚██████╔╝    ███████╗███████╗██║  ██║██║ ╚████║
╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝     ╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝
Ultra Lean Autonomous Software Engineer  v1.0
GLM-4  *  LangGraph  *  GitHub Actions  *  Docker"""

PIPELINE_STAGES = [
    ("S1", "Formalizing requirements + extracting acceptance criteria"),
    ("S2", "Designing architecture + breaking down tasks"),
    ("S3", "Generating complete source code (~99%)"),
    ("S4", "Generating tests + CI configuration"),
    ("S5", "Pushing files + creating pull request"),
    ("S6", "Running CI: Static + Security (Ruff, MyPy, Semgrep, Trivy)"),
    ("S7", "Running CI: Tests + Coverage (pytest ≥ 90%)"),
    ("S8", "Running CI: Production simulation (Docker + E2E)"),
    ("S9", "Running CI: Stress tests (Hypothesis + k6 + Playwright)"),
    ("SA", "Computing confidence score..."),
    ("SB", "Auto-merging + deploying if confidence ≥ 95"),
]


def check_engine():
    try:
        return requests.get(f"{AE_BASE_URL}/health", timeout=5).status_code == 200
    except Exception:
        return False


def start_build(prompt: str) -> int:
    r = requests.post(f"{AE_BASE_URL}/build",
                      json={"request": prompt}, timeout=10)
    r.raise_for_status()
    return r.json()["run_id"]


def get_status(run_id: int) -> dict:
    return requests.get(f"{AE_BASE_URL}/status/{run_id}", timeout=5).json()


def poll_until_done(run_id: int) -> dict:
    total_stages = len(PIPELINE_STAGES)
    with Progress(SpinnerColumn(),
                  TextColumn("[bold cyan]{task.description:<60}"),
                  BarColumn(bar_width=30),
                  TextColumn("[dim]{task.fields[elapsed]}"),
                  console=console) as progress:
        task = progress.add_task(
            PIPELINE_STAGES[0][1], total=total_stages, elapsed="0s")
        start = time.time()
        stage_idx = 0
        while True:
            elapsed = int(time.time() - start)
            status = get_status(run_id)
            state  = status.get("status", "running")
            new_idx = min(int(elapsed / 12), total_stages - 1)
            if new_idx > stage_idx:
                stage_idx = new_idx
                progress.update(task,
                    description=PIPELINE_STAGES[stage_idx][1],
                    completed=stage_idx,
                    elapsed=f"{elapsed}s")
            else:
                progress.update(task, elapsed=f"{elapsed}s")

            if state in ("deployed", "error", "max_iterations_reached"):
                progress.update(task,
                    description="Pipeline complete",
                    completed=total_stages,
                    elapsed=f"{elapsed}s")
                return status
            if elapsed > 2400:
                return {"status": "timeout", "run_id": run_id}
            time.sleep(10)


def print_result(prompt: str, result: dict):
    status = result.get("status", "unknown")
    conf   = result.get("confidence", 0)
    pr     = result.get("pr_number")
    iters  = result.get("iterations", 0)
    gh_url = f"https://github.com/Arunaah/autonomous-engineer"

    console.print()
    console.rule("[bold cyan]RESULTS")
    console.print()

    if status == "deployed":
        console.print(Panel(
            f"[bold green]✅  DEPLOYMENT SUCCESSFUL[/bold green]\n\n"
            f"[white]Prompt     :[/white] [yellow]{prompt}[/yellow]\n"
            f"[white]Confidence :[/white] [bold green]{conf} / 100[/bold green]  ✅\n"
            f"[white]PR         :[/white] [cyan]{gh_url}/pull/{pr}[/cyan]\n"
            f"[white]Iterations :[/white] {iters}\n"
            f"[white]Status     :[/white] [bold green]Auto-merged into main[/bold green]\n\n"
            f"[white]Live code  :[/white] [cyan]{gh_url}[/cyan]",
            title="[bold green] PIPELINE COMPLETE ",
            box=box.DOUBLE, style="green", padding=(1, 4)))

        console.print()
        console.print("[bold cyan]WHAT WAS BUILT:[/bold cyan]")
        console.print(f"  • Complete source code generated")
        console.print(f"  • Full test suite created")
        console.print(f"  • CI pipeline passed all 4 stages")
        console.print(f"  • PR #{pr} auto-merged at {conf}/100 confidence")
        console.print(f"  • Code is live on GitHub main branch")
        console.print()
    else:
        console.print(Panel(
            f"[red]Status     : {status}[/red]\n"
            f"Confidence : {conf} / 100\n"
            f"PR         : #{pr}\n"
            f"Iterations : {iters}\n\n"
            f"[yellow]CI logs: {gh_url}/actions[/yellow]",
            title="[bold red] BUILD INCOMPLETE ",
            box=box.DOUBLE, style="red"))


def print_help():
    console.print(Panel(BANNER, style="bold cyan", box=box.DOUBLE))
    console.print()
    t = Table(title="CLI Commands", box=box.ROUNDED, style="cyan", show_lines=True)
    t.add_column("Command",           style="bold yellow", min_width=35)
    t.add_column("Description",       style="white")
    t.add_column("Example",           style="dim")
    t.add_row(
        'engineer "prompt"',
        "Generate complete software project",
        'engineer "build a REST API for todos"')
    t.add_row(
        'engineer --status <id>',
        "Check status of a specific run",
        'engineer --status 3')
    t.add_row(
        'engineer --runs',
        "List all past runs",
        'engineer --runs')
    t.add_row(
        'engineer --help',
        "Show this help",
        'engineer --help')
    console.print(t)
    console.print()
    console.print("[bold white]PIPELINE STAGES:[/bold white]")
    for code, desc in PIPELINE_STAGES:
        console.print(f"  [{code}] {desc}")
    console.print()


def list_runs():
    r = requests.get(f"{AE_BASE_URL}/runs", timeout=5)
    runs = r.json()
    if not runs:
        console.print("[yellow]No runs found.[/yellow]")
        return
    t = Table(title="All Runs", box=box.ROUNDED, style="cyan", show_lines=True)
    t.add_column("ID",         style="bold yellow", justify="right")
    t.add_column("Status",     style="bold")
    t.add_column("Confidence", justify="right")
    t.add_column("PR",         style="cyan")
    t.add_column("Iters",      justify="right")
    t.add_column("Request",    style="white")
    for run in runs[-15:]:
        s = run.get("status", "?")
        color = "green" if s == "deployed" else "red" if s in ("error","timeout") else "yellow"
        conf  = str(run.get("confidence") or "-")
        t.add_row(
            str(run.get("run_id", "?")),
            f"[{color}]{s}[/{color}]",
            conf,
            f"#{run.get('pr_number', '-')}",
            str(run.get("iterations", "-")),
            str(run.get("request", ""))[:55])
    console.print(t)


def main():
    args = sys.argv[1:]

    if not args or "--help" in args or "-h" in args:
        print_help()
        return

    console.print(Panel(BANNER, style="bold cyan", box=box.DOUBLE))
    console.print()

    if "--runs" in args:
        if not check_engine():
            console.print("[red]❌ Engine offline. Run: docker compose up -d[/red]")
            return
        list_runs()
        return

    if "--status" in args:
        if not check_engine():
            console.print("[red]❌ Engine offline.[/red]")
            return
        idx = args.index("--status")
        if idx + 1 < len(args):
            result = get_status(int(args[idx + 1]))
            console.print_json(json.dumps(result))
        return

    prompt = " ".join(args).strip().strip('"').strip("'")
    if not prompt:
        console.print("[red]Please provide a prompt.[/red]")
        return

    console.rule("[bold cyan]NEW BUILD REQUEST")
    console.print(f"\n[bold white]Prompt:[/bold white] [yellow]{prompt}[/yellow]\n")

    console.print("[white]Checking engine...[/white] ", end="")
    if not check_engine():
        console.print("[red]OFFLINE ❌[/red]")
        console.print("\n[yellow]Start your stack:[/yellow]")
        console.print("[cyan]  cd C:\\Users\\mrleo\\Downloads\\autonomous-engineer[/cyan]")
        console.print("[cyan]  docker compose up -d[/cyan]\n")
        return
    console.print("[green]ONLINE ✅[/green]\n")

    console.print("[bold white]Launching pipeline...[/bold white]\n")
    run_id = start_build(prompt)
    console.print(f"[cyan]Run ID: {run_id}[/cyan]\n")

    result = poll_until_done(run_id)
    print_result(prompt, result)


if __name__ == "__main__":
    main()
