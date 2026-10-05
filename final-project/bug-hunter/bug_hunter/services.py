"""Coordinate independent lint, AI advice, and unchanged before/after tests."""

import ast
import time
from collections.abc import Callable

from bug_hunter.ai.ollama_provider import DEFAULT_MODEL, OllamaProvider
from bug_hunter.analysis.diff_utils import compare_results
from bug_hunter.analysis.pylint_runner import run_pylint
from bug_hunter.analysis.test_runner import run_tests
from bug_hunter.models import AnalysisReport, TestResult


def validate_source(source: str) -> None:
    if not source.strip():
        raise ValueError("Paste Python source code before analyzing.")
    if len(source) > 50_000:
        raise ValueError("This proof of concept accepts at most 50,000 source characters.")
    try:
        compile(source, "candidate.py", "exec")
    except (SyntaxError, ValueError) as exc:
        raise ValueError(f"Python syntax error: {exc}") from exc


def analyze_code(source: str, error: str = "", tests: str = "", model: str = DEFAULT_MODEL,
                 provider: OllamaProvider | None = None, test_timeout: float = 10,
                 progress: Callable[[str], None] | None = None) -> AnalysisReport:
    started = time.perf_counter()
    notify = progress or (lambda stage: None)
    notify("Validating code")
    validate_source(source)
    if len(tests) > 50_000 or len(error) > 20_000:
        raise ValueError("Tests must be at most 50,000 characters and error context at most 20,000.")
    if tests.strip():
        try:
            ast.parse(tests, filename="test_candidate.py")
        except (SyntaxError, ValueError) as exc:
            raise ValueError(f"Invalid pytest input: {exc}") from exc
    stages = {}
    notify("Running Pylint")
    stage_start = time.perf_counter()
    lint = run_pylint(source)
    stages["pylint"] = time.perf_counter() - stage_start
    notify("Running original tests")
    stage_start = time.perf_counter()
    original = run_tests(source, tests, timeout=test_timeout)
    stages["original_tests"] = time.perf_counter() - stage_start
    notify("Asking local AI model")
    ai_provider = provider or OllamaProvider()
    if isinstance(ai_provider, OllamaProvider):
        ai_provider.on_parse = lambda: notify("Parsing findings")
    stage_start = time.perf_counter()
    # Actual failures ground the explanation; reference solutions are never supplied.
    ai_context = error
    if original.status in {"failed", "error", "timeout"}:
        output = (original.stdout + "\n" + original.stderr).strip()
        if len(output) > 3500:
            output = "[Earlier output omitted; full log remains in results]\n" + output[-3500:]
        ai_context += (f"\nObserved ORIGINAL pytest result: {original.status}; "
                       f"{original.passed} passed, {original.failed} failed, {original.errors} errors.\n"
                       + (output or original.message))
    ai = ai_provider.analyze(source, ai_context, tests, model)
    stages["local_ai"] = time.perf_counter() - stage_start
    if not isinstance(ai_provider, OllamaProvider) or ai.analysis is None:
        notify("Parsing findings")
    fixed = TestResult(message="No validated AI correction is available.")
    warnings = []
    changed = False
    notify("Validating suggested fix")
    stage_start = time.perf_counter()
    if ai.analysis is not None:
        changed = ai.analysis.corrected_code.strip() != source.strip()
        if changed and not ai.analysis.findings:
            warnings.append("The model changed source without reporting structured findings. Review its explanation carefully.")
        fixed = run_tests(ai.analysis.corrected_code, tests, timeout=test_timeout)
        if fixed.status == "invalid":
            warnings.append("The proposed correction contains invalid Python and must be reviewed.")
        if ai.recovered:
            warnings.append("Recovered JSON from surrounding model text; review the output carefully.")
    stages["corrected_tests"] = time.perf_counter() - stage_start
    notify("Preparing results")
    verified, comparison = compare_results(original, fixed, changed)
    return AnalysisReport(source, tests, model, lint, ai, original, fixed,
                          time.perf_counter() - started, verified, comparison, warnings, stages)
