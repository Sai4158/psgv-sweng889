"""Run unchanged user tests against candidate.py in a fresh temporary directory."""

import ast
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

from bug_hunter.analysis.execution import run_process
from bug_hunter.models import TestResult

# A small pytest observer gives real counts without scraping terminal wording.
_REPORT_PLUGIN = '''
import json
from pathlib import Path
counts = {"passed": 0, "failed": 0, "errors": 0, "skipped": 0}
def pytest_runtest_logreport(report):
    if report.when == "call":
        if report.passed: counts["passed"] += 1
        elif report.failed: counts["failed"] += 1
        elif report.skipped: counts["skipped"] += 1
    elif report.failed: counts["errors"] += 1
    elif report.skipped: counts["skipped"] += 1
def pytest_collectreport(report):
    if report.failed: counts["errors"] += 1
def pytest_sessionfinish(session, exitstatus):
    counts["collected"] = session.testscollected
    Path("test_results.json").write_text(json.dumps(counts), encoding="utf-8")
'''


def run_tests(code: str, tests: str, timeout: float = 10) -> TestResult:
    if not tests.strip():
        return TestResult(message="No tests supplied. A fix cannot be verified.")
    try:
        ast.parse(tests, filename="test_candidate.py")
        compile(code, "candidate.py", "exec")
    except (SyntaxError, ValueError) as exc:
        return TestResult(status="invalid", message=f"Invalid Python/test input: {exc}")
    if importlib.util.find_spec("pytest") is None:
        return TestResult(status="error", message="pytest is not installed; install requirements.txt.")
    with tempfile.TemporaryDirectory(prefix="bug-hunter-tests-") as folder:
        path = Path(folder)
        (path / "candidate.py").write_text(code, encoding="utf-8")
        (path / "test_candidate.py").write_text(tests, encoding="utf-8")
        (path / "conftest.py").write_text(_REPORT_PLUGIN, encoding="utf-8")
        try:
            process = run_process(
                [sys.executable, "-m", "pytest", "test_candidate.py", "-v", "--tb=short",
                 "--color=no", "-p", "no:cacheprovider", "--confcutdir", str(path)],
                path, timeout,
            )
        except OSError as exc:
            return TestResult(status="error", message=f"Could not start pytest: {exc}")
        if process.timed_out:
            return TestResult(status="timeout", stdout=process.stdout, stderr=process.stderr,
                              duration=process.duration, message=f"Execution stopped after {timeout:g}s.")
        report_path = path / "test_results.json"
        try:
            data = json.loads(report_path.read_text(encoding="utf-8"))
            counts = {key: int(data[key]) for key in ("passed", "failed", "errors", "skipped", "collected")}
        except (OSError, ValueError, KeyError, TypeError):
            return TestResult(status="error", exit_code=process.returncode,
                              stdout=process.stdout, stderr=process.stderr,
                              duration=process.duration, message="pytest did not produce a valid result report.")
        status = {0: "passed", 1: "failed", 5: "no_tests"}.get(process.returncode, "error")
        return TestResult(status=status, **counts, exit_code=process.returncode,
                          stdout=process.stdout, stderr=process.stderr, duration=process.duration,
                          message="No tests collected." if status == "no_tests" else "")
