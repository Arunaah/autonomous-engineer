"""
Ultra Lean Autonomous Software Engineer — FastAPI Server
Endpoints: /build  /status/{run_id}  /runs  /health
"""
import os, logging, threading
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("ae.server")

app = FastAPI(
    title="Ultra Lean Autonomous Software Engineer",
    description="GLM-4 + LangGraph + GitHub Actions autonomous coding engine",
    version="1.0.0"
)

# In-memory run store (also persisted to PostgreSQL)
_runs: dict[int, dict] = {}
_run_counter = 0
_lock = threading.Lock()


class BuildRequest(BaseModel):
    request: str


def _run_pipeline(run_id: int, request: str):
    """Execute the full LangGraph pipeline in a background thread."""
    try:
        from agent.graph import autonomous_graph
        result = autonomous_graph.invoke({
            "request":         request,
            "spec":            None,
            "tasks":           None,
            "generated_files": None,
            "pr_number":       None,
            "ci_result":       None,
            "confidence":      None,
            "iteration":       0,
            "run_id":          run_id,
            "status":          "starting",
        })
        with _lock:
            _runs[run_id].update({
                "status":     result.get("status", "unknown"),
                "confidence": result.get("confidence"),
                "pr_number":  result.get("pr_number"),
                "iterations": result.get("iteration", 0),
            })
        logger.info(f"Run {run_id} complete: {result.get('status')} "
                    f"confidence={result.get('confidence')}")
    except Exception as e:
        logger.error(f"Run {run_id} error: {e}", exc_info=True)
        with _lock:
            _runs[run_id]["status"] = "error"
            _runs[run_id]["error"]  = str(e)


@app.post("/build")
def build(req: BuildRequest):
    """Submit a new autonomous engineering request."""
    global _run_counter
    with _lock:
        _run_counter += 1
        run_id = _run_counter
        _runs[run_id] = {
            "run_id":    run_id,
            "status":    "running",
            "request":   req.request,
            "confidence": None,
            "pr_number":  None,
            "iterations": 0,
        }
    thread = threading.Thread(
        target=_run_pipeline, args=(run_id, req.request), daemon=True)
    thread.start()
    logger.info(f"Started run {run_id}: {req.request[:80]}")
    return {"run_id": run_id, "status": "started", "message": "Pipeline launched"}


@app.get("/status/{run_id}")
def status(run_id: int):
    """Get status of a specific run."""
    with _lock:
        run = _runs.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return run


@app.get("/runs")
def list_runs():
    """List all runs."""
    with _lock:
        return list(_runs.values())


@app.get("/health")
def health():
    return {"status": "ok", "service": "autonomous-engineer", "version": "1.0.0"}


@app.get("/")
def root():
    return {
        "service": "Ultra Lean Autonomous Software Engineer",
        "docs": "/docs",
        "health": "/health",
        "build": "POST /build",
        "status": "GET /status/{run_id}",
        "runs": "GET /runs"
    }
