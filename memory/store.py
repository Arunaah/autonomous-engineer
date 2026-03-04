"""PostgreSQL memory store for failure/fix patterns."""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://ae_user:ae_secure_pass_2024@localhost:5432/autonomous_engineer")

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


def store_failure(iteration: int, pr_number: int, error_type: str, stack_trace: str, stage: str) -> int:
    with Session() as session:
        result = session.execute(
            text("INSERT INTO failures (iteration, pr_number, error_type, stack_trace, stage) "
                 "VALUES (:iteration, :pr_number, :error_type, :stack_trace, :stage) RETURNING id"),
            {"iteration": iteration, "pr_number": pr_number, "error_type": error_type,
             "stack_trace": stack_trace, "stage": stage}
        )
        session.commit()
        return result.fetchone()[0]


def store_fix(failure_id: int, patch_diff: str, confidence_before: float, confidence_after: float, success: bool):
    with Session() as session:
        session.execute(
            text("INSERT INTO fixes (failure_id, patch_diff, confidence_before, confidence_after, success) "
                 "VALUES (:fid, :diff, :before, :after, :success)"),
            {"fid": failure_id, "diff": patch_diff, "before": confidence_before,
             "after": confidence_after, "success": success}
        )
        session.commit()
