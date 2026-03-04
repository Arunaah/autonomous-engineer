"""Hypothesis property-based tests for the Autonomous Engineer."""
from hypothesis import given, settings, strategies as st
from confidence.engine import compute_confidence, parse_ci_output
from memory.store import format_fix_context


@given(
    static=st.floats(min_value=0.0, max_value=1.0),
    coverage=st.floats(min_value=0.0, max_value=1.0),
    production=st.floats(min_value=0.0, max_value=1.0),
    stress=st.floats(min_value=0.0, max_value=1.0),
    reviewer=st.floats(min_value=0.0, max_value=15.0),
)
@settings(max_examples=200)
def test_confidence_always_bounded(static, coverage, production, stress, reviewer):
    ci_result = {
        "stage_scores": {
            "static": static,
            "coverage": coverage,
            "production": production,
            "stress": stress,
        }
    }
    review = {"confidence_contribution": reviewer}
    score = compute_confidence(ci_result, review)
    assert 0.0 <= score <= 100.0, f"Score out of bounds: {score}"


@given(st.floats(min_value=0.0, max_value=1.0))
def test_full_static_gives_max_static_contribution(v):
    ci = {"stage_scores": {"static": 1.0, "coverage": 0.0, "production": 0.0, "stress": 0.0}}
    review = {"confidence_contribution": 0.0}
    score = compute_confidence(ci, review)
    assert score == 25.0


@given(st.lists(st.fixed_dictionaries({
    "error_type": st.text(min_size=1, max_size=30),
    "stage": st.sampled_from(["static", "testing", "production", "stress"]),
    "stack_trace": st.text(max_size=100),
    "patch_diff": st.text(max_size=100),
    "fix_strategy": st.text(max_size=50),
    "confidence_delta": st.floats(min_value=0.0, max_value=20.0),
    "usage_count": st.integers(min_value=1, max_value=100),
}), max_size=10))
def test_format_fix_context_never_crashes(fixes):
    result = format_fix_context(fixes)
    assert isinstance(result, str)
    assert len(result) > 0


@given(st.text())
def test_parse_ci_output_always_returns_dict(raw):
    result = parse_ci_output(raw)
    assert "stage_scores" in result
    assert "failures" in result
    assert isinstance(result["stage_scores"], dict)
    assert isinstance(result["failures"], list)
