"""
Ultra Lean AE — FastAPI Server
Fix: proper exception capture and error surfacing in run status.
"""
import os, logging, threading, traceback
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("ae.server")

app = FastAPI(title="Ultra Lean Autonomous Software Engineer", version="1.0.0")

_runs: dict = {}
_run_counter = 0
_lock = threading.Lock()


class BuildRequest(BaseModel):
    request: str


def _run_pipeline(run_id: int, request: str):
    try:
        from agent.graph import autonomous_graph
        logger.info(f"[AE] Run {run_id} starting pipeline...")
        result = autonomous_graph.invoke({
            "request": request, "spec": None, "tasks": None,
            "generated_files": None, "pr_number": None,
            "ci_result": None, "confidence": None,
            "iteration": 0, "run_id": run_id, "status": "starting",
        })
        with _lock:
            _runs[run_id].update({
                "status":     result.get("status", "unknown"),
                "confidence": result.get("confidence"),
                "pr_number":  result.get("pr_number"),
                "iterations": result.get("iteration", 0),
            })
        logger.info(f"[AE] Run {run_id} complete: "
                    f"status={result.get('status')} confidence={result.get('confidence')}")
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"[AE] Run {run_id} CRASHED: {e}\n{tb}")
        with _lock:
            _runs[run_id]["status"] = "error"
            _runs[run_id]["error"]  = str(e)


@app.post("/build")
def build(req: BuildRequest):
    global _run_counter
    with _lock:
        _run_counter += 1
        run_id = _run_counter
        _runs[run_id] = {
            "run_id": run_id, "status": "running",
            "request": req.request, "confidence": None,
            "pr_number": None, "iterations": 0,
        }
    thread = threading.Thread(target=_run_pipeline,
                              args=(run_id, req.request), daemon=True)
    thread.start()
    logger.info(f"[AE] Run {run_id} launched: {req.request[:80]}")
    return {"run_id": run_id, "status": "started"}


@app.get("/status/{run_id}")
def status(run_id: int):
    with _lock:
        run = _runs.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return run


@app.get("/runs")
def list_runs():
    with _lock:
        return list(_runs.values())


@app.get("/health")
def health():
    return {"status": "ok", "service": "autonomous-engineer", "version": "1.0.0"}


@app.get("/")
def root():
    return {"service": "Ultra Lean AE", "docs": "/docs",
            "build": "POST /build", "status": "GET /status/{id}", "runs": "GET /runs"}
