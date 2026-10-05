"""Run Pylint's JSON reporter, keeping lint messages separate from AI findings."""

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

from bug_hunter.analysis.execution import run_process
from bug_hunter.models import PylintMessage, PylintResult


def parse_pylint_output(text: str) -> PylintResult:
    try:
        data = json.loads(text)
        rows = data["messages"]
        if not isinstance(rows, list):
            raise ValueError("messages must be a list")
        messages = [PylintMessage(
            message=row["message"], category=row["type"], line=int(row["line"]),
            column=int(row["column"]), symbol=row["symbol"], message_id=row["messageId"],
        ) for row in rows]
        score = data.get("statistics", {}).get("score")
        return PylintResult("ok", messages, None if score is None else float(score), output=text)
    except (ValueError, TypeError, KeyError, AttributeError) as exc:
        return PylintResult("error", error=f"Could not parse Pylint output: {exc}", output=text)


def run_pylint(code: str, timeout: float = 20) -> PylintResult:
    if importlib.util.find_spec("pylint") is None:
        return PylintResult("unavailable", error="Pylint is not installed; install requirements.txt.")
    with tempfile.TemporaryDirectory(prefix="bug-hunter-lint-") as folder:
        path = Path(folder)
        (path / "candidate.py").write_text(code, encoding="utf-8")
        try:
            result = run_process([sys.executable, "-m", "pylint", "candidate.py",
                                  "--output-format=json2", "--persistent=no", "--jobs=1"], path, timeout)
        except OSError as exc:
            return PylintResult("error", error=f"Could not start Pylint: {exc}")
        if result.timed_out:
            return PylintResult("timeout", error="Pylint exceeded its execution timeout.")
        parsed = parse_pylint_output(result.stdout)
        if parsed.status != "ok" and result.stderr:
            parsed.error = f"{parsed.error}\n{result.stderr}"
        return parsed
