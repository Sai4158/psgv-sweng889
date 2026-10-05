import json

from bug_hunter.demos import load_cases
from evaluation.run_evaluation import evaluate, export_results


def test_dataset_has_twelve_complete_unique_cases():
    cases = load_cases()
    assert len(cases) >= 12
    assert len({case["id"] for case in cases}) == len(cases)
    assert all(case["expected_behavior"] and case["tests"] and case["reference"] and case["source"] for case in cases)


def test_all_dataset_originals_fail_and_references_pass():
    from bug_hunter.analysis.test_runner import run_tests
    for case in load_cases():
        original = run_tests(case["source"], case["tests"])
        reference = run_tests(case["reference"], case["tests"])
        assert original.status == "failed" and original.failed > 0, case["id"]
        assert reference.all_passed, (case["id"], reference.stdout)


def test_evaluation_export_contains_real_baseline_and_no_fabricated_ai(monkeypatch, tmp_path):
    from bug_hunter.models import PylintResult
    monkeypatch.setattr("evaluation.run_evaluation.run_pylint", lambda source: PylintResult("ok"))
    rows, evidence = evaluate(load_cases()[:1], "local", baseline_only=True)
    row = rows[0]
    assert row["original_tests_failed"] > 0
    assert row["reference_tests_passed"] == 3
    assert row["ai_fix_successful"] is None
    assert row["ai_status"] == "not_run"
    assert row["ai_detected_intended_bug"] == "Unreviewed"
    assert row["prompt_tokens"] is None
    csv_file, json_file = export_results(rows, evidence, tmp_path)
    assert csv_file.exists()
    assert json.loads(json_file.read_text())["results"][0] == row


def test_model_results_can_be_serialized_for_full_evidence(tmp_path):
    from bug_hunter.models import AIAnalysis
    rows = [{"case_id": "one"}]
    evidence = [{"analysis": AIAnalysis(summary="Observed", findings=[], corrected_code="x=1")}]
    _, output = export_results(rows, evidence, tmp_path)
    assert json.loads(output.read_text())["evidence"][0]["analysis"]["corrected_code"] == "x=1"


def test_judgements_are_tied_to_exact_saved_response():
    import pytest
    from evaluation.review_results import apply_annotations
    data = {"results": [{"case_id": "one", "ai_response_sha256": "actual"}],
            "evidence": [{"case": {"id": "one"}}]}
    with pytest.raises(ValueError, match="hash"):
        apply_annotations(data, {"one": {"ai_detected_intended_bug": True, "response_sha256": "wrong"}})
    rows, _ = apply_annotations(data, {"one": {"ai_detected_intended_bug": True, "response_sha256": "actual"}})
    assert rows[0]["ai_detected_intended_bug"] == "Yes"
