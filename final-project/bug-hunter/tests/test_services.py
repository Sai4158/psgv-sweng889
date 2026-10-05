import pytest

from bug_hunter.models import AIAnalysis, AIResult, PylintResult, TestResult
from bug_hunter.services import analyze_code, validate_source


@pytest.mark.parametrize("source", ["", " ", "def broken(:", "return 1"])
def test_invalid_python_is_rejected_before_execution(source):
    with pytest.raises(ValueError):
        validate_source(source)


class UnavailableAI:
    def analyze(self, source, error, tests, model):
        return AIResult("unavailable", model, error="Ollama is stopped.")


def test_ollama_failure_preserves_original_test_evidence(monkeypatch):
    monkeypatch.setattr("bug_hunter.services.run_pylint", lambda source: PylintResult("ok"))
    report = analyze_code("def value():\n    return 1", "", "from candidate import value\ndef test_value():\n    assert value() == 2", "local", UnavailableAI())
    assert report.ai.status == "unavailable"
    assert report.original_tests.failed == 1
    assert report.corrected_tests.status == "not_run"
    assert not report.fix_verified


def test_service_reuses_identical_tests_for_both_versions(monkeypatch):
    seen = []
    tests = "def test_value():\n    assert True"
    source = "x=1"
    monkeypatch.setattr("bug_hunter.services.run_pylint", lambda source: PylintResult("ok"))
    def run(code, test_code, timeout):
        seen.append(test_code)
        if code == source:
            return TestResult(status="failed", failed=1, collected=1, exit_code=1)
        return TestResult(status="passed", passed=1, collected=1, exit_code=0)
    monkeypatch.setattr("bug_hunter.services.run_tests", run)
    class FixedAI:
        def analyze(self, *args):
            return AIResult("ok", "local", AIAnalysis(summary="Fix", findings=[], corrected_code="x=2"))
    report = analyze_code(source, "", tests, "local", FixedAI())
    assert seen == [tests, tests]
    assert report.fix_verified
    assert any("without reporting structured findings" in warning for warning in report.warnings)


def test_invalid_pytest_input_is_a_clear_validation_error():
    with pytest.raises(ValueError, match="Invalid pytest input"):
        analyze_code("x=1", tests="def test_bad(:")
