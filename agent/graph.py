"""
LangGraph — autonomous engineering pipeline.
Root fix: every node wrapped in try/except, errors logged not crashed.
"""
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
import os, json, logging

logger = logging.getLogger("ae.graph")

MAX_ITERATIONS       = int(os.getenv("MAX_ITERATIONS", 9))
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", 95))


class EngineState(TypedDict):
    request:         str
    spec:            Optional[dict]
    tasks:           Optional[list]
    generated_files: Optional[dict]
    pr_number:       Optional[int]
    ci_result:       Optional[dict]
    confidence:      Optional[float]
    iteration:       int
    run_id:          Optional[int]
    status:          str


def _safe_import_builder():
    from agent.builder import formalize_spec, plan_tasks, generate_code
    return formalize_spec, plan_tasks, generate_code


def _safe_import_reviewer():
    from agent.reviewer import review_diff, fix_ci_failure
    return review_diff, fix_ci_failure


def node_formalize(state: EngineState) -> EngineState:
    logger.info("[AE] Formalizing spec...")
    try:
        from memory.recall import store_run
        run_id = store_run(state["request"], pr_number=0)
    except Exception as e:
        logger.warning(f"store_run failed: {e}")
        run_id = state.get("run_id", 0)

    try:
        formalize_spec, _, _ = _safe_import_builder()
        spec = formalize_spec(state["request"])
        logger.info(f"[AE] Spec: {spec.get('title', 'unknown')}")
    except Exception as e:
        logger.error(f"[AE] Formalize failed: {e}")
        spec = {
            "title":               state["request"][:60],
            "description":         state["request"],
            "tech_stack":          ["python"],
            "acceptance_criteria": ["code runs without errors"],
            "files_to_create":     ["main.py", "tests/test_main.py"],
            "architecture":        "Python application"
        }
    return {**state, "spec": spec, "run_id": run_id, "status": "spec_ready"}


def node_plan(state: EngineState) -> EngineState:
    logger.info("[AE] Planning tasks...")
    try:
        _, plan_tasks, _ = _safe_import_builder()
        tasks = plan_tasks(state["spec"])
        logger.info(f"[AE] {len(tasks)} tasks planned")
    except Exception as e:
        logger.error(f"[AE] Plan failed: {e}")
        tasks = [
            {"id": "task_1", "title": state["spec"].get("title", "implementation"),
             "description": state["request"], "files": ["main.py"], "type": "implementation"},
            {"id": "task_2", "title": "tests",
             "description": "unit tests", "files": ["tests/test_main.py"], "type": "test"}
        ]
    return {**state, "tasks": tasks, "status": "planned"}


def node_generate(state: EngineState) -> EngineState:
    logger.info("[AE] Generating code...")
    try:
        from memory.recall import get_similar_failures
        _, _, generate_code = _safe_import_builder()
        all_files = {}
        all_tests = {}
        for task in state["tasks"]:
            try:
                past = get_similar_failures(error_type="pytest", limit=3)
                past_str = json.dumps(past) if past else ""
                result = generate_code(task, past_failures=past_str)
                all_files.update(result.get("files", {}))
                all_tests.update(result.get("tests", {}))
            except Exception as e:
                logger.error(f"[AE] Code gen for task {task.get('id')} failed: {e}")
        generated = {**all_files, **all_tests}
        if not generated:
            raise ValueError("No files generated")
        logger.info(f"[AE] Generated {len(generated)} files")
    except Exception as e:
        logger.error(f"[AE] Generate failed: {e}, using fallback")
        from agent.builder import _fallback_code
        fallback = _fallback_code({"title": state["request"][:30], "description": state["request"]})
        generated = {**fallback.get("files", {}), **fallback.get("tests", {})}

    return {**state, "generated_files": generated, "status": "code_generated"}


def node_create_pr(state: EngineState) -> EngineState:
    logger.info(f"[AE] Creating PR (iteration {state['iteration']})...")
    try:
        from github_utils import push_files, create_pull_request
        pr_data   = push_files(state["generated_files"],
                               state["spec"]["title"], state["iteration"])
        pr_number = create_pull_request(pr_data["branch"], state["spec"])
        logger.info(f"[AE] PR #{pr_number} created")
        return {**state, "pr_number": pr_number, "status": "pr_created"}
    except Exception as e:
        logger.error(f"[AE] PR creation failed: {e}")
        return {**state, "status": "error", "pr_number": None}


def node_wait_ci(state: EngineState) -> EngineState:
    if not state.get("pr_number"):
        logger.error("[AE] No PR number — skipping CI wait")
        return {**state, "ci_result": {
            "passed": False, "failures": ["No PR created"],
            "stage_scores": {"static": 0.5, "coverage": 0.5,
                             "production": 0.5, "stress": 0.5}
        }, "status": "ci_done"}

    logger.info(f"[AE] Waiting for CI on PR #{state['pr_number']}...")
    try:
        from github_utils import wait_for_ci
        ci_result = wait_for_ci(state["pr_number"])
        logger.info(f"[AE] CI done. Passed: {ci_result.get('passed')}")
    except Exception as e:
        logger.error(f"[AE] CI wait failed: {e}")
        ci_result = {
            "passed": False, "failures": [str(e)],
            "stage_scores": {"static": 0.5, "coverage": 0.5,
                             "production": 0.5, "stress": 0.5}
        }
    return {**state, "ci_result": ci_result, "status": "ci_done"}


def node_compute_confidence(state: EngineState) -> EngineState:
    logger.info("[AE] Computing confidence...")
    try:
        from confidence.engine import compute_confidence
        from agent.reviewer import review_diff
        diff   = state["ci_result"].get("diff", "")
        review = review_diff(diff, state["spec"])
        confidence = compute_confidence(state["ci_result"], review)
    except Exception as e:
        logger.error(f"[AE] Confidence compute failed: {e}")
        # Fallback: use stage scores directly
        scores = state["ci_result"].get("stage_scores", {})
        confidence = (scores.get("static", 0.5) * 25 +
                      scores.get("coverage", 0.5) * 25 +
                      scores.get("production", 0.5) * 20 +
                      scores.get("stress", 0.5) * 15 + 10)
    logger.info(f"[AE] Confidence: {confidence}/100 (need {CONFIDENCE_THRESHOLD})")
    return {**state, "confidence": confidence, "status": "confidence_computed"}


def node_fix(state: EngineState) -> EngineState:
    logger.info(f"[AE] Fixing CI failure (iteration {state['iteration']})...")
    try:
        from agent.reviewer import fix_ci_failure
        from memory.store import store_failure, store_fix
        from memory.recall import get_similar_failures

        failure_report = json.dumps(state["ci_result"].get("failures", []))
        current_code   = json.dumps(list(state["generated_files"].keys()))
        past_fixes     = json.dumps(get_similar_failures(
            state["ci_result"].get("stage", "pytest")))

        fix = fix_ci_failure(failure_report, current_code, past_fixes)

        try:
            fail_id = store_failure(
                state["iteration"], state.get("pr_number", 0),
                state["ci_result"].get("stage", "unknown"),
                failure_report,
                state["ci_result"].get("stage", "unknown"))
            store_fix(fail_id, json.dumps(fix),
                      state.get("confidence") or 0.0, 0.0, False)
        except Exception as e:
            logger.warning(f"Memory store failed: {e}")

        updated = {**state["generated_files"], **fix.get("files", {})}
    except Exception as e:
        logger.error(f"[AE] Fix failed: {e}")
        updated = state["generated_files"]

    return {**state, "generated_files": updated,
            "iteration": state["iteration"] + 1, "status": "fixing"}


def node_deploy(state: EngineState) -> EngineState:
    logger.info(f"[AE] Auto-merging PR #{state['pr_number']}...")
    try:
        from github_utils import merge_pr
        merge_pr(state["pr_number"])
        try:
            from memory.recall import complete_run
            complete_run(state["run_id"], state["confidence"],
                         state["iteration"], "deployed")
        except Exception:
            pass
        logger.info(f"[AE] DEPLOYED! Confidence: {state['confidence']}")
    except Exception as e:
        logger.error(f"[AE] Deploy failed: {e}")
    return {**state, "status": "deployed"}


def should_fix_or_deploy(state: EngineState) -> str:
    if state["status"] == "error":
        return "end"
    if (state.get("confidence") or 0) >= CONFIDENCE_THRESHOLD:
        return "deploy"
    if state["iteration"] >= MAX_ITERATIONS:
        try:
            from memory.recall import complete_run
            complete_run(state["run_id"], state.get("confidence", 0),
                         state["iteration"], "max_iterations_reached")
        except Exception:
            pass
        logger.warning(f"[AE] Max iterations reached. Final confidence: {state.get('confidence')}")
        return "end"
    return "fix"


def build_graph():
    g = StateGraph(EngineState)
    g.add_node("formalize",          node_formalize)
    g.add_node("plan",               node_plan)
    g.add_node("generate",           node_generate)
    g.add_node("create_pr",          node_create_pr)
    g.add_node("wait_ci",            node_wait_ci)
    g.add_node("compute_confidence", node_compute_confidence)
    g.add_node("fix",                node_fix)
    g.add_node("deploy",             node_deploy)

    g.set_entry_point("formalize")
    g.add_edge("formalize",          "plan")
    g.add_edge("plan",               "generate")
    g.add_edge("generate",           "create_pr")
    g.add_edge("create_pr",          "wait_ci")
    g.add_edge("wait_ci",            "compute_confidence")
    g.add_conditional_edges("compute_confidence", should_fix_or_deploy,
                             {"deploy": "deploy", "fix": "fix", "end": END})
    g.add_edge("fix",    "create_pr")
    g.add_edge("deploy", END)
    return g.compile()


autonomous_graph = build_graph()
