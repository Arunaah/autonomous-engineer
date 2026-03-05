"""
Ultra Lean AE — FastAPI Server
Fix: runs persisted to PostgreSQL (survive Docker restarts).
"""
import os, logging, threading, traceback
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("ae.server")

app = FastAPI(title="Ultra Lean Autonomous Software Engineer", version="1.0.0")

_lock = threading.Lock()


class BuildRequest(BaseModel):
    request: str


def _db():
    """Get a PostgreSQL connection."""
    import psycopg2
    return psycopg2.connect(os.getenv(
        "DATABASE_URL",
        "postgresql://ae_user:ae_secure_pass_2024@ae-postgres:5432/autonomous_engineer"))


def _init_runs_table():
    """Ensure runs table exists."""
    try:
        conn = _db()
        cur  = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ae_runs (
                run_id     SERIAL PRIMARY KEY,
                status     TEXT DEFAULT 'running',
                request    TEXT,
                confidence FLOAT,
                pr_number  INT,
                iterations INT DEFAULT 0,
                error      TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        conn.commit()
        cur.close()
        conn.close()
        logger.info("ae_runs table ready")
    except Exception as e:
        logger.warning(f"DB init warning (non-fatal): {e}")


def _db_create_run(request: str) -> int:
    try:
        conn = _db()
        cur  = conn.cursor()
        cur.execute(
            "INSERT INTO ae_runs (request, status) VALUES (%s, 'running') RETURNING run_id",
            (request,))
        run_id = cur.fetchone()[0]
        conn.commit(); cur.close(); conn.close()
        return run_id
    except Exception as e:
        logger.warning(f"DB create_run failed: {e}")
        return int(time.time()) % 100000


def _db_update_run(run_id: int, **kwargs):
    if not kwargs:
        return
    try:
        conn = _db()
        cur  = conn.cursor()
        sets = ", ".join(f"{k} = %s" for k in kwargs)
        sets += ", updated_at = NOW()"
        vals = list(kwargs.values()) + [run_id]
        cur.execute(f"UPDATE ae_runs SET {sets} WHERE run_id = %s", vals)
        conn.commit(); cur.close(); conn.close()
    except Exception as e:
        logger.warning(f"DB update_run failed: {e}")


def _db_get_run(run_id: int) -> dict | None:
    try:
        conn = _db()
        cur  = conn.cursor()
        cur.execute("""SELECT run_id, status, request, confidence,
                              pr_number, iterations, error
                       FROM ae_runs WHERE run_id = %s""", (run_id,))
        row = cur.fetchone()
        cur.close(); conn.close()
        if not row:
            return None
        return {"run_id": row[0], "status": row[1], "request": row[2],
                "confidence": row[3], "pr_number": row[4],
                "iterations": row[5], "error": row[6]}
    except Exception as e:
        logger.warning(f"DB get_run failed: {e}")
        return None


def _db_list_runs() -> list:
    try:
        conn = _db()
        cur  = conn.cursor()
        cur.execute("""SELECT run_id, status, request, confidence,
                              pr_number, iterations
                       FROM ae_runs ORDER BY run_id DESC LIMIT 50""")
        rows = cur.fetchall()
        cur.close(); conn.close()
        return [{"run_id": r[0], "status": r[1], "request": r[2],
                 "confidence": r[3], "pr_number": r[4], "iterations": r[5]}
                for r in rows]
    except Exception as e:
        logger.warning(f"DB list_runs failed: {e}")
        return []


import time

def _run_pipeline(run_id: int, request: str):
    try:
        from agent.graph import autonomous_graph
        logger.info(f"[AE] Run {run_id} starting...")
        result = autonomous_graph.invoke({
            "request": request, "spec": None, "tasks": None,
            "generated_files": None, "pr_number": None,
            "ci_result": None, "confidence": None,
            "iteration": 0, "run_id": run_id, "status": "starting",
        })
        status     = result.get("status", "unknown")
        confidence = result.get("confidence")
        pr_number  = result.get("pr_number")
        iterations = result.get("iteration", 0)
        _db_update_run(run_id, status=status, confidence=confidence,
                       pr_number=pr_number, iterations=iterations)
        logger.info(f"[AE] Run {run_id} complete: status={status} confidence={confidence}")
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"[AE] Run {run_id} CRASHED: {e}\n{tb}")
        _db_update_run(run_id, status="error", error=str(e)[:500])


@app.on_event("startup")
def startup():
    _init_runs_table()


@app.post("/build")
def build(req: BuildRequest):
    run_id = _db_create_run(req.request)
    thread = threading.Thread(target=_run_pipeline,
                              args=(run_id, req.request), daemon=True)
    thread.start()
    logger.info(f"[AE] Run {run_id} launched: {req.request[:80]}")
    return {"run_id": run_id, "status": "started"}


@app.get("/status/{run_id}")
def status(run_id: int):
    run = _db_get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return run


@app.get("/runs")
def list_runs():
    return _db_list_runs()


@app.get("/health")
def health():
    return {"status": "ok", "service": "autonomous-engineer", "version": "1.0.0"}


@app.get("/")
def root():
    return {"service": "Ultra Lean AE", "docs": "/docs",
            "build": "POST /build", "status": "GET /status/{id}", "runs": "GET /runs"}
