"""Core tests for autonomous engineer — runs in CI without needing live LLM."""
import pytest, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


# ── JSON Parser Tests ────────────────────────────────────────────────────────
class TestJsonParser:
    def test_parse_clean_json(self):
        from agent.builder import _parse_json
        result = _parse_json('{"title": "test", "description": "desc"}')
        assert result["title"] == "test"

    def test_parse_markdown_fenced(self):
        from agent.builder import _parse_json
        result = _parse_json('```json\n{"title": "test"}\n```')
        assert result["title"] == "test"

    def test_parse_double_escaped(self):
        from agent.builder import _parse_json
        raw = '{"files": {"main.py": "def hello():\\n    return \\\\"hello\\\\""}}'
        result = _parse_json(raw)
        assert "files" in result

    def test_parse_array(self):
        from agent.builder import _parse_json
        result = _parse_json('[{"id": "1", "description": "task"}]')
        assert isinstance(result, list)
        assert result[0]["id"] == "1"

    def test_parse_json_with_extra_text(self):
        from agent.builder import _parse_json
        raw = 'Here is the JSON:\n{"title": "test"}\nDone.'
        result = _parse_json(raw)
        assert result["title"] == "test"


# ── Confidence Engine Tests ──────────────────────────────────────────────────
class TestConfidenceEngine:
    def test_full_score(self):
        from confidence.engine import compute_confidence
        ci = {"stage_scores": {"static": 1.0, "coverage": 1.0, "production": 1.0, "stress": 1.0}}
        review = {"confidence_contribution": 15}
        score = compute_confidence(ci, review)
        assert score == 100.0

    def test_zero_score(self):
        from confidence.engine import compute_confidence
        ci = {"stage_scores": {"static": 0.0, "coverage": 0.0, "production": 0.0, "stress": 0.0}}
        review = {"confidence_contribution": 0}
        score = compute_confidence(ci, review)
        assert score == 0.0

    def test_partial_score(self):
        from confidence.engine import compute_confidence
        ci = {"stage_scores": {"static": 1.0, "coverage": 1.0, "production": 0.0, "stress": 0.0}}
        review = {"confidence_contribution": 10}
        score = compute_confidence(ci, review)
        assert score == 60.0

    def test_parse_ci_output_pass(self):
        from confidence.engine import parse_ci_output
        raw = "ruff passed\nmypy passed\ncoverage: 95%\ndocker build passed\ne2e passed\nhypothesis passed"
        result = parse_ci_output(raw)
        assert result["stage_scores"]["static"] == 1.0

    def test_parse_ci_output_fail(self):
        from confidence.engine import parse_ci_output
        raw = "ERROR: test failed\nFAILED test_main.py"
        result = parse_ci_output(raw)
        assert len(result["failures"]) > 0


# ── API Tests ────────────────────────────────────────────────────────────────
class TestAPI:
    def test_health_endpoint(self):
        from fastapi.testclient import TestClient
        from api.main import app
        client = TestClient(app)
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_build_endpoint_accepts_request(self):
        from fastapi.testclient import TestClient
        from api.main import app
        client = TestClient(app)
        resp = client.post("/build", json={"request": "test task"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "started"
        assert "run_id" in data

    def test_status_endpoint(self):
        from fastapi.testclient import TestClient
        from api.main import app
        client = TestClient(app)
        resp = client.get("/status/999")
        assert resp.status_code == 200

    def test_runs_endpoint(self):
        from fastapi.testclient import TestClient
        from api.main import app
        client = TestClient(app)
        resp = client.get("/runs")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
