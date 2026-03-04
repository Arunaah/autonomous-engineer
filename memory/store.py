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


def format_fix_context(fixes: list) -> str:
    """Format past fix patterns into a prompt-injectable string."""
    if not fixes:
        return "No historical fix patterns available."
    lines = []
    for f in fixes:
        delta = f.get("confidence_delta") or (f.get("confidence_after", 0) - f.get("confidence_before", 0))
        lines.append(
            f"[{f.get('error_type', 'unknown')} | stage={f.get('stage', '?')}]\n"
            f"  Trace: {f.get('stack_trace', '')[:200]}\n"
            f"  Fix: {f.get('fix_strategy') or f.get('patch_diff', '')[:300]}\n"
            f"  Result: +{delta:.1f}% confidence | used {f.get('usage_count', 1)}x"
        )
    return "\n\n".join(lines)
