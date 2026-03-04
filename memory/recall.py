"""Retrieve past failure patterns to inject into fix prompts."""
from sqlalchemy.orm import sessionmaker
from memory.store import engine, text

Session = sessionmaker(bind=engine)


def get_similar_failures(error_type: str, limit: int = 5) -> list[dict]:
    with Session() as session:
        result = session.execute(
            text("SELECT f.error_type, f.stack_trace, f.stage, fx.patch_diff, fx.success "
                 "FROM failures f LEFT JOIN fixes fx ON f.id = fx.failure_id "
                 "WHERE f.error_type = :error_type AND fx.success = TRUE "
                 "ORDER BY f.created_at DESC LIMIT :limit"),
            {"error_type": error_type, "limit": limit}
        )
        return [dict(row._mapping) for row in result.fetchall()]


def store_run(request: str, pr_number: int) -> int:
    with Session() as session:
        result = session.execute(
            text("INSERT INTO runs (request, pr_number) VALUES (:request, :pr) RETURNING id"),
            {"request": request, "pr": pr_number}
        )
        session.commit()
        return result.fetchone()[0]


def complete_run(run_id: int, confidence: float, iterations: int, status: str):
    with Session() as session:
        session.execute(
            text("UPDATE runs SET final_confidence=:conf, iterations_used=:iters, "
                 "status=:status, completed_at=NOW() WHERE id=:id"),
            {"conf": confidence, "iters": iterations, "status": status, "id": run_id}
        )
        session.commit()
