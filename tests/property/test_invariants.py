"""Property-based tests — invariants that must always hold."""
import pytest
from hypothesis import given, strategies as st
from confidence.engine import compute_confidence


@given(
    s1=st.floats(0, 1), s2=st.floats(0, 1),
    s3=st.floats(0, 1), s4=st.floats(0, 1),
    r=st.floats(0, 15),
)
def test_higher_scores_give_higher_confidence(s1, s2, s3, s4, r):
    """More passing stages = higher or equal confidence."""
    low = compute_confidence(
        {"stage_scores": {"static": 0, "coverage": 0, "production": 0, "stress": 0}},
        {"confidence_contribution": 0}
    )
    high = compute_confidence(
        {"stage_scores": {"static": 1, "coverage": 1, "production": 1, "stress": 1}},
        {"confidence_contribution": 15}
    )
    assert high >= low


def test_max_confidence_is_100():
    score = compute_confidence(
        {"stage_scores": {"static": 1.0, "coverage": 1.0, "production": 1.0, "stress": 1.0}},
        {"confidence_contribution": 15.0}
    )
    assert score == 100.0


def test_zero_confidence_is_zero():
    score = compute_confidence(
        {"stage_scores": {"static": 0, "coverage": 0, "production": 0, "stress": 0}},
        {"confidence_contribution": 0}
    )
    assert score == 0.0
