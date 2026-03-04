"""FastAPI interface for the Autonomous Engineer."""
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from agent.graph import autonomous_graph
import uvicorn, asyncio, logging

logger = logging.getLogger("ae")
app = FastAPI(title="Autonomous Engineer", version="1.0.0")

# In-memory run tracker
_runs: dict = {}
_run_counter = {"n": 0}


class BuildRequest(BaseModel):
    request: str


class BuildResponse(BaseModel):
    run_id: int
    status: str
    message: str


@app.get("/health")
def health():
    return {"status": "ok", "service": "autonomous-engineer"}


@app.get("/status/{run_id}")
def get_status(run_id: int):
    return _runs.get(run_id, {"status": "not_found"})


@app.get("/runs")
def list_runs():
    return list(_runs.values())


@app.post("/build", response_model=BuildResponse)
async def build(req: BuildRequest, background_tasks: BackgroundTasks):
    _run_counter["n"] += 1
    run_id = _run_counter["n"]
    _runs[run_id] = {"run_id": run_id, "status": "started", "request": req.request}
    initial_state = {
        "request": req.request,
        "spec": None, "tasks": None, "generated_files": None,
        "pr_number": None, "ci_result": None, "confidence": None,
        "iteration": 0, "run_id": run_id, "status": "starting"
    }
    background_tasks.add_task(run_pipeline, initial_state, run_id)
    return BuildResponse(run_id=run_id, status="started",
                         message="Pipeline started. Check /status/{run_id} for progress.")


async def run_pipeline(state: dict, run_id: int):
    try:
        _runs[run_id]["status"] = "running"
        result = await asyncio.to_thread(autonomous_graph.invoke, state)
        _runs[run_id].update({
            "status": result.get("status", "done"),
            "confidence": result.get("confidence"),
            "pr_number": result.get("pr_number"),
            "iterations": result.get("iteration"),
        })
        logger.info(f"[AE] Run {run_id} complete. Status: {result['status']} | Confidence: {result.get('confidence')}")
    except Exception as e:
        _runs[run_id]["status"] = "error"
        _runs[run_id]["error"] = str(e)
        logger.error(f"[AE] Run {run_id} failed: {e}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
