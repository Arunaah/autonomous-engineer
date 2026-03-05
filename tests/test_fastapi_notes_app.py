"""Tests for fastapi_notes_app"""
import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi_notes_app import run, main


def test_run_returns_dict():
    result = run("test")
    assert isinstance(result, dict)


def test_run_success_status():
    result = run("hello")
    assert result["status"] == "success"


def test_run_with_none():
    result = run(None)
    assert result is not None


def test_main_runs():
    result = main()
    assert result is not None


def test_task_name():
    result = run("x")
    assert "task" in result
