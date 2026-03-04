"""FastAPI interface for the Autonomous Engineer."""
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from agent.graph import autonomous_graph
import uvicorn, asyncio

app = FastAPI(title="Autonomous Engineer", version="1.0.0")


class BuildRequest(BaseModel):
    request: str


class BuildResponse(BaseModel):
    run_id: int
    status: str
    message: str


@app.get("/health")
def health():
    return {"status": "ok", "service": "autonomous-engineer"}


@app.post("/build", response_model=BuildResponse)
async def build(req: BuildRequest, background_tasks: BackgroundTasks):
    initial_state = {
        "request": req.request,
        "spec": None, "tasks": None, "generated_files": None,
        "pr_number": None, "ci_result": None, "confidence": None,
        "iteration": 0, "run_id": None, "status": "starting"
    }
    background_tasks.add_task(run_pipeline, initial_state)
    return BuildResponse(run_id=0, status="started", message="Pipeline started. Monitor GitHub for PRs.")


async def run_pipeline(state: dict):
    result = await asyncio.to_thread(autonomous_graph.invoke, state)
    print(f"[AE] Pipeline complete. Status: {result['status']} | Confidence: {result['confidence']}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
