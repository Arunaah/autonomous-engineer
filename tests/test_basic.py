"""Core tests for Autonomous Engineer — ensures CI coverage passes."""
import pytest, json, os
os.environ.setdefault("DATABASE_URL", "postgresql://ae_user:ae_secure_pass_2024@localhost:5432/autonomous_engineer")
os.environ.setdefault("LITELLM_BASE_URL", "http://localhost:4000")
os.environ.setdefault("LITELLM_API_KEY", "ae-litellm-master-key-2024")
os.environ.setdefault("GLM_MODEL", "glm4")


# ── Confidence Engine Tests ───────────────────────────────────────────────────

def test_confidence_all_passing():
    from confidence.engine import compute_confidence
    ci = {"stage_scores": {"static": 1.0, "coverage": 1.0, "production": 1.0, "stress": 1.0}}
    review = {"confidence_contribution": 15}
    score = compute_confidence(ci, review)
    assert score == 100.0


def test_confidence_all_partial():
    from confidence.engine import compute_confidence
    ci = {"stage_scores": {"static": 0.5, "coverage": 0.5, "production": 0.5, "stress": 0.5}}
    review = {"confidence_contribution": 7}
    score = compute_confidence(ci, review)
    assert score == 49.5


def test_confidence_threshold():
    from confidence.engine import compute_confidence
    ci = {"stage_scores": {"static": 1.0, "coverage": 1.0, "production": 1.0, "stress": 1.0}}
    review = {"confidence_contribution": 15}
    score = compute_confidence(ci, review)
    assert score >= 95.0


def test_parse_ci_output_passing():
    from confidence.engine import parse_ci_output
    raw = "ruff passed\nmypy passed\ncoverage 90% passed\ndocker build passed\ne2e passed\nhypothesis passed"
    result = parse_ci_output(raw)
    assert result["stage_scores"]["static"] == 1.0
    assert result["stage_scores"]["production"] == 1.0


def test_parse_ci_output_empty():
    from confidence.engine import parse_ci_output
    result = parse_ci_output("")
    assert "stage_scores" in result
    assert "failures" in result


# ── Builder Tests (mocked) ────────────────────────────────────────────────────

def test_parse_json_valid():
    from agent.builder import _parse_json
    result = _parse_json('{"title": "test", "description": "desc"}')
    assert result["title"] == "test"


def test_parse_json_with_fences():
    from agent.builder import _parse_json
    result = _parse_json('```json\n{"title": "test"}\n```')
    assert result["title"] == "test"


def test_parse_json_array():
    from agent.builder import _parse_json
    result = _parse_json('[{"id": "1"}, {"id": "2"}]')
    assert isinstance(result, list)
    assert len(result) == 2


def test_parse_json_invalid_raises():
    from agent.builder import _parse_json
    with pytest.raises(ValueError):
        _parse_json("this is not json at all !!")


# ── GitHub Utils Tests (no network) ──────────────────────────────────────────

def test_get_pr_diff_fallback(monkeypatch):
    """get_pr_diff returns empty string on error."""
    import github_utils
    def mock_get_repo():
        raise Exception("no network")
    monkeypatch.setattr(github_utils, "get_repo", mock_get_repo)
    result = github_utils.get_pr_diff(999)
    assert result == ""


# ── Memory Tests ─────────────────────────────────────────────────────────────

def test_store_format_fix_context_empty():
    from memory.store import format_fix_context
    result = format_fix_context([])
    assert "No historical" in result


def test_store_format_fix_context_with_data():
    from memory.store import format_fix_context
    fixes = [{"error_type": "pytest", "stage": "test",
               "stack_trace": "AssertionError", "patch_diff": "fix code",
               "confidence_before": 30, "confidence_after": 60}]
    result = format_fix_context(fixes)
    assert "pytest" in result


# ── Hypothesis Tests ─────────────────────────────────────────────────────────

from hypothesis import given, settings
import hypothesis.strategies as st


@given(st.floats(min_value=0, max_value=1), st.floats(min_value=0, max_value=15))
@settings(max_examples=50)
def test_confidence_always_bounded(stage_score, reviewer):
    from confidence.engine import compute_confidence
    ci = {"stage_scores": {
        "static": stage_score, "coverage": stage_score,
        "production": stage_score, "stress": stage_score
    }}
    review = {"confidence_contribution": reviewer}
    score = compute_confidence(ci, review)
    assert 0.0 <= score <= 100.0


@given(st.text(max_size=200))
@settings(max_examples=50)
def test_parse_ci_never_crashes(raw):
    from confidence.engine import parse_ci_output
    result = parse_ci_output(raw)
    assert isinstance(result, dict)
    assert "stage_scores" in result
