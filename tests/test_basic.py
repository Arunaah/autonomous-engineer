"""
Basic tests for memory store and retrieval layer.
"""
import pytest


def test_format_fix_context_empty():
    from memory.store import format_fix_context
    result = format_fix_context([])
    assert "No historical fix patterns" in result


def test_format_fix_context_with_data():
    from memory.store import format_fix_context
    fixes = [{
        "error_type": "TypeError",
        "stage": "testing",
        "stack_trace": "line 42",
        "patch_diff": "-old\n+new",
        "fix_strategy": "Fixed type mismatch",
        "confidence_delta": 5.0,
        "usage_count": 3,
    }]
    result = format_fix_context(fixes)
    assert "TypeError" in result
    assert "Fixed type mismatch" in result
    assert "+5.0%" in result


def test_code_extensions():
    from retrieval.indexer import CODE_EXTENSIONS
    assert ".py" in CODE_EXTENSIONS
    assert ".ts" in CODE_EXTENSIONS
    assert ".go" in CODE_EXTENSIONS
