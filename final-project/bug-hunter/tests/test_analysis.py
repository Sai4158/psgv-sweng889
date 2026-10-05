import json

import pytest

from bug_hunter.analysis.diff_utils import compare_results, source_diff
from bug_hunter.analysis.pylint_runner import parse_pylint_output, run_pylint
from bug_hunter.analysis.test_runner import run_tests
from bug_hunter.models import TestResult


def test_pylint_json2_parses_messages_and_score():
    result = parse_pylint_output(json.dumps({"messages": [{
        "message": "Undefined variable 'missing'", "type": "error", "line": 2,
        "column": 4, "symbol": "undefined-variable", "messageId": "E0602",
    }], "statistics": {"score": 3.5}}))
    assert result.status == "ok"
    assert result.messages[0].message_id == "E0602"
    assert result.score == 3.5


@pytest.mark.parametrize("raw", ["not json", "[]", '{"messages": {}}', '{"messages": [{}]}'])
def test_malformed_pylint_output_is_graceful(raw):
    assert parse_pylint_output(raw).status == "error"


def test_real_pylint_finds_undefined_variable():
    result = run_pylint("def example():\n    return missing\n")
    assert result.status == "ok"
    assert any(message.symbol == "undefined-variable" and message.line == 2 for message in result.messages)


def test_missing_pylint_returns_unavailable(monkeypatch):
    monkeypatch.setattr("bug_hunter.analysis.pylint_runner.importlib.util.find_spec", lambda name: None)
    assert run_pylint("x=1").status == "unavailable"


def test_unchanged_tests_produce_real_before_after_results():
    tests = "from candidate import add\ndef test_add():\n    assert add(2, 3) == 5\n"
    original = run_tests("def add(a, b):\n    return a - b\n", tests)
    corrected = run_tests("def add(a, b):\n    return a + b\n", tests)
    assert original.failed == 1 and original.passed == 0 and original.status == "failed"
    assert corrected.passed == 1 and corrected.failed == 0 and corrected.all_passed
    assert compare_results(original, corrected, True)[0] is True


def test_pytest_missing_import_is_error_not_verified():
    result = run_tests("x=1", "from candidate import missing\ndef test_x():\n    assert missing()\n")
    assert result.errors >= 1 and not result.all_passed


def test_pytest_runtime_exception_is_a_failed_test():
    result = run_tests("def fail():\n    raise ValueError('bad')", "from candidate import fail\ndef test_it():\n    fail()\n")
    assert result.failed == 1 and result.status == "failed"


def test_invalid_tests_are_not_executed():
    result = run_tests("x=1", "def test_x(:")
    assert result.status == "invalid" and "Invalid" in result.message


def test_no_collected_tests_does_not_verify_a_fix():
    result = run_tests("x=1", "x=1\n")
    assert result.status == "no_tests"
    assert not result.all_passed


def test_skipped_tests_do_not_verify_a_fix():
    result = run_tests("x=1", "import pytest\n@pytest.mark.skip\ndef test_x():\n    assert False\n")
    assert result.skipped == 1 and not result.all_passed


def test_infinite_loop_is_terminated():
    result = run_tests("def hang():\n    while True:\n        pass\n", "from candidate import hang\ndef test_hang():\n    hang()\n", timeout=1.5)
    assert result.status == "timeout" and result.duration < 8
    assert not result.all_passed


def test_empty_tests_are_not_run():
    assert run_tests("x=1", "").status == "not_run"


def test_diff_shows_correct_change():
    diff = source_diff("return 1\n", "return 2\n")
    assert "-return 1" in diff and "+return 2" in diff
    assert "original.py" in diff and "suggested.py" in diff
    assert source_diff("x=1\n", "x=1\n") == ""


def test_passed_original_or_unchanged_code_is_not_a_verified_repair():
    passing = TestResult(status="passed", passed=1, collected=1, exit_code=0)
    assert compare_results(passing, passing, True)[0] is False
    assert compare_results(TestResult(status="failed", failed=1), passing, False)[0] is False


def test_timeout_or_error_never_verifies():
    original = TestResult(status="failed", failed=1)
    for status in ("timeout", "error", "no_tests", "invalid", "not_run"):
        assert compare_results(original, TestResult(status=status), True)[0] is False
