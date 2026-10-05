"""Readable comparison of source changes and independent test evidence."""

import difflib

from bug_hunter.models import TestResult


def source_diff(original: str, corrected: str) -> str:
    return "".join(difflib.unified_diff(
        original.splitlines(keepends=True), corrected.splitlines(keepends=True),
        fromfile="original.py", tofile="suggested.py",
    ))


def compare_results(original: TestResult, corrected: TestResult, changed: bool) -> tuple[bool, str]:
    if original.status == "not_run":
        return False, "Unverified: supply tests to check the proposed fix."
    if not changed:
        return False, "No code change was proposed; no repair was verified."
    if corrected.all_passed and original.status == "failed" and original.failed > 0:
        return True, "Fix verified for supplied tests: original assertions failed and the same tests now pass."
    if corrected.all_passed:
        return False, "Suggested code passes supplied tests, but an original failing assertion was not reproduced."
    return False, "Fix not verified: corrected tests failed, errored, skipped, were absent, or timed out."
