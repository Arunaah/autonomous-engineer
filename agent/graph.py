"""LangGraph — main autonomous engineering pipeline."""
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from agent.builder import formalize_spec, plan_tasks, generate_code
from agent.reviewer import review_diff, fix_ci_failure
from memory import store_failure, store_fix, get_similar_failures, store_run, complete_run
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


def node_formalize(state: EngineState) -> EngineState:
    logger.info("[AE] Formalizing spec...")
    spec   = formalize_spec(state["request"])
    run_id = store_run(state["request"], pr_number=0)
    logger.info(f"[AE] Spec: {spec.get('title')}")
    return {**state, "spec": spec, "run_id": run_id, "status": "spec_ready"}


def node_plan(state: EngineState) -> EngineState:
    logger.info("[AE] Planning tasks...")
    tasks = plan_tasks(state["spec"])
    logger.info(f"[AE] {len(tasks)} tasks planned")
    return {**state, "tasks": tasks, "status": "planned"}


def node_generate(state: EngineState) -> EngineState:
    logger.info("[AE] Generating code...")
    all_files = {}
    for task in state["tasks"]:
        past     = get_similar_failures(error_type="pytest", limit=3)
        past_str = json.dumps(past) if past else ""
        result   = generate_code(task, past_failures=past_str)
        all_files.update(result.get("files", {}))
        all_files.update(result.get("tests", {}))
    logger.info(f"[AE] Generated {len(all_files)} files")
    return {**state, "generated_files": all_files, "status": "code_generated"}


def node_create_pr(state: EngineState) -> EngineState:
    logger.info(f"[AE] Creating PR (iteration {state['iteration']})...")
    from github_utils import create_pull_request, push_files
    pr_data    = push_files(state["generated_files"], state["spec"]["title"], state["iteration"])
    pr_number  = create_pull_request(pr_data["branch"], state["spec"])
    logger.info(f"[AE] PR #{pr_number} created")
    return {**state, "pr_number": pr_number, "status": "pr_created"}


def node_wait_ci(state: EngineState) -> EngineState:
    logger.info(f"[AE] Waiting for CI on PR #{state['pr_number']}...")
    from github_utils import wait_for_ci
    ci_result = wait_for_ci(state["pr_number"])
    logger.info(f"[AE] CI done. Passed: {ci_result.get('passed')}")
    return {**state, "ci_result": ci_result, "status": "ci_done"}


def node_compute_confidence(state: EngineState) -> EngineState:
    logger.info("[AE] Computing confidence...")
    from confidence.engine import compute_confidence
    diff       = state["ci_result"].get("diff", "")
    review     = review_diff(diff, state["spec"])
    confidence = compute_confidence(state["ci_result"], review)
    logger.info(f"[AE] Confidence: {confidence}/100 (threshold: {CONFIDENCE_THRESHOLD})")
    return {**state, "confidence": confidence, "status": "confidence_computed"}


def node_fix(state: EngineState) -> EngineState:
    logger.info(f"[AE] Fixing CI failure (iteration {state['iteration']})...")
    failure_report = json.dumps(state["ci_result"].get("failures", []))
    current_code   = json.dumps(state["generated_files"])
    past_fixes     = json.dumps(get_similar_failures(
        state["ci_result"].get("stage", "pytest")))

    fix = fix_ci_failure(failure_report, current_code, past_fixes)

    fail_id = store_failure(
        state["iteration"], state["pr_number"],
        state["ci_result"].get("stage", "unknown"),
        failure_report,
        state["ci_result"].get("stage", "unknown")
    )
    store_fix(fail_id, json.dumps(fix), state["confidence"] or 0.0, 0.0, False)

    updated_files = {**state["generated_files"], **fix.get("files", {})}
    return {
        **state,
        "generated_files": updated_files,
        "iteration": state["iteration"] + 1,
        "status": "fixing"
    }


def node_deploy(state: EngineState) -> EngineState:
    logger.info(f"[AE] ✅ Auto-merging PR #{state['pr_number']}...")
    from github_utils import merge_pr
    merge_pr(state["pr_number"])
    complete_run(state["run_id"], state["confidence"], state["iteration"], "deployed")
    logger.info(f"[AE] 🚀 DEPLOYED! Confidence: {state['confidence']}")
    return {**state, "status": "deployed"}


def should_fix_or_deploy(state: EngineState) -> str:
    if state["confidence"] >= CONFIDENCE_THRESHOLD:
        return "deploy"
    if state["iteration"] >= MAX_ITERATIONS:
        complete_run(state["run_id"], state["confidence"],
                     state["iteration"], "max_iterations_reached")
        logger.warning(f"[AE] Max iterations reached. Final confidence: {state['confidence']}")
        return "end"
    return "fix"


def build_graph() -> StateGraph:
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
    g.add_conditional_edges(
        "compute_confidence",
        should_fix_or_deploy,
        {"deploy": "deploy", "fix": "fix", "end": END}
    )
    g.add_edge("fix",    "create_pr")
    g.add_edge("deploy", END)
    return g.compile()


autonomous_graph = build_graph()
