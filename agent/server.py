"""
Agent server — FastAPI endpoint for receiving coding requests.
"""
from __future__ import annotations

import asyncio
import os

import structlog
import uvicorn
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel

from agent.graph import agent_graph
from retrieval.indexer import build_index

log = structlog.get_logger()
app = FastAPI(title="Autonomous Engineer", version="1.0.0")


class CodingRequest(BaseModel):
    repo: str
    request: str
    repo_path: str = "."
    rebuild_index: bool = False


class CodingResponse(BaseModel):
    job_id: str
    status: str
    message: str


jobs: dict = {}


async def run_agent(job_id: str, req: CodingRequest) -> None:
    jobs[job_id] = {"status": "running", "result": None}
    try:
        if req.rebuild_index:
            build_index(req.repo_path)

        state = await agent_graph.ainvoke({
            "repo": req.repo,
            "pr_number": 0,
            "user_request": req.request,
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
        })
        jobs[job_id] = {"status": "complete", "result": state}
    except Exception as e:
        log.error("agent_error", error=str(e))
        jobs[job_id] = {"status": "error", "error": str(e)}


@app.post("/run", response_model=CodingResponse)
async def run_coding_request(req: CodingRequest, background: BackgroundTasks):
    import uuid
    job_id = str(uuid.uuid4())
    background.add_task(run_agent, job_id, req)
    return CodingResponse(job_id=job_id, status="started", message="Agent running")


@app.get("/status/{job_id}")
async def get_status(job_id: str):
    return jobs.get(job_id, {"status": "not_found"})


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
