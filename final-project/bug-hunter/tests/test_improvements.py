import hashlib
import json
from copy import deepcopy
import pytest
from bug_hunter.ai.ollama_provider import OllamaProvider
from bug_hunter.demos import load_cases
from bug_hunter.models import AIAnalysis, AIResult, PylintResult, TestResult
from bug_hunter.presentation import readable_time, recommended_model
from bug_hunter.services import analyze_code
from evaluation.run_evaluation import evaluate, export_results
from evaluation.storage import load_reviews, metrics, read_run, recorded_bool, save_review


@pytest.mark.parametrize("seconds,expected", [(0, "0s"), (53.3, "53s"), (106.9, "1m 47s"), (3600, "60m 00s")])
def test_human_readable_time(seconds, expected):
    assert readable_time(seconds) == expected


def test_mode_recommendations_keep_quality_and_fast_options():
    models = ["qwen2.5-coder:1.5b", "qwen2.5-coder:3b", "qwen2.5-coder:7b"]
    assert recommended_model(models, "Fast Demo") == "qwen2.5-coder:3b"
    assert recommended_model(models, "Higher Quality") == "qwen2.5-coder:7b"


def test_new_ollama_url_variable_and_legacy_fallback(monkeypatch):
    monkeypatch.setenv("BUG_HUNTER_OLLAMA_URL", "http://127.0.0.1:11435")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")
    assert OllamaProvider().base_url == "http://localhost:11434"
    monkeypatch.delenv("OLLAMA_BASE_URL")
    assert OllamaProvider().base_url == "http://127.0.0.1:11435"


def test_exactly_one_generation_request_and_loaded_model_reuse(monkeypatch):
    provider = OllamaProvider(known_models=["local:1b"])
    seen = []
    class Response:
        status_code = 200
        def json(self):
            return {"done": True, "done_reason": "stop", "message": {"content": json.dumps(
                {"summary": "No bugs", "findings": [], "corrected_code": "x=1"})}, "eval_count": 42,
                "load_duration": 2_000_000, "eval_duration": 1_000_000_000}
    def post(*args, **kwargs):
        seen.append(kwargs["json"])
        return Response()
    monkeypatch.setattr(provider.session, "post", post)
    monkeypatch.setattr(provider.session, "get", lambda *a, **k: pytest.fail("cached discovery should be reused"))
    result = provider.analyze("x=1", "", "", "local:1b")
    assert len(seen) == 1
    assert seen[0]["keep_alive"] == "30m"
    assert seen[0]["options"] == {"temperature": 0, "num_predict": 1536, "num_ctx": 4096}
    assert result.diagnostics["load_duration_seconds"] == .002
    assert result.diagnostics["analysis_calls"] == 1
    user = json.loads(seen[0]["messages"][1]["content"])
    assert user["source_code"] == "x=1" and "numbered_source" not in user


def test_context_limit_does_not_silently_drop_input(monkeypatch):
    provider = OllamaProvider(known_models=["local"])
    monkeypatch.setattr(provider.session, "post", lambda *a, **k: pytest.fail("oversize request must not be sent"))
    result = provider.analyze("x=" + "1" * 20000, "", "", "local")
    assert result.status == "error" and "context" in result.error.lower()


def test_real_progress_stages_preserve_identical_test_inputs(monkeypatch):
    stages, test_inputs = [], []
    monkeypatch.setattr("bug_hunter.services.run_pylint", lambda source: PylintResult("ok"))
    def tests(code, test_code, timeout):
        test_inputs.append(test_code)
        return TestResult(status="failed", failed=1, collected=1, exit_code=1) if code == "x=1" else TestResult(status="passed", passed=1, collected=1, exit_code=0)
    monkeypatch.setattr("bug_hunter.services.run_tests", tests)
    class AI:
        def analyze(self, *args):
            return AIResult("ok", "local", AIAnalysis(summary="Fix", findings=[], corrected_code="x=2"))
    report = analyze_code("x=1", tests="def test_it(): pass", provider=AI(), progress=stages.append)
    assert stages == ["Validating code", "Running Pylint", "Running original tests", "Asking local AI model",
                      "Parsing findings", "Validating suggested fix", "Preparing results"]
    assert test_inputs == ["def test_it(): pass"] * 2
    assert report.fix_verified and report.stage_seconds["local_ai"] >= 0


def test_original_failure_feedback_is_observed_not_a_reference_answer(monkeypatch):
    monkeypatch.setattr("bug_hunter.services.run_pylint", lambda source: PylintResult("ok"))
    monkeypatch.setattr("bug_hunter.services.run_tests", lambda *a, **k:
                        TestResult(status="failed", failed=1, stdout="assert 3 == 4"))
    seen = []
    class AI:
        def analyze(self, source, context, tests, model):
            seen.append((source, context, tests))
            return AIResult("unavailable", model)
    analyze_code("x=3", "Expected four", "def test_it(): pass", provider=AI())
    assert seen == [("x=3", "Expected four\nObserved ORIGINAL pytest result: failed; 0 passed, 1 failed, 0 errors.\nassert 3 == 4", "def test_it(): pass")]


def saved_run(tmp_path):
    case = load_cases()[1]
    raw = '{"summary":"actual saved response"}'
    row = {"case_id": case["id"], "ai_status": "ok", "ai_response_sha256": hashlib.sha256(raw.encode()).hexdigest(),
           "ai_produced_fix": True, "ai_fix_successful": False, "analysis_seconds": 12,
           "pylint_detected_functional_issue": "No"}
    evidence = [{"case": case, "report": {"ai": {"raw_response": raw, "analysis": None}}}]
    return export_results([row], evidence, tmp_path)[1]


def judgement(**kwargs):
    return {"reviewer": "Test reviewer", "intended_bug_detected": "Unclear", "explanation_correct": "Partially",
            "suggested_fix_correct": "No", "false_positive_findings": 0, "notes": "Unit-test fixture only", **kwargs}


def test_human_review_is_separate_hash_bound_and_raw_file_unchanged(tmp_path):
    run = saved_run(tmp_path)
    before = run.read_bytes()
    saved = save_review(run, "02-comparison", judgement(), tmp_path / "reviews")
    assert run.read_bytes() == before
    reviews, issues = load_reviews(run, tmp_path / "reviews")
    assert not issues
    assert reviews["02-comparison"]["judgement"]["intended_bug_detected"] == "Unclear"
    summary = metrics(read_run(run)["results"], reviews)
    assert summary["human_reviewed"] == 1 and summary["intended_bug_yes"] == 0
    assert json.loads(saved.read_text())["run_sha256"] == hashlib.sha256(before).hexdigest()


@pytest.mark.parametrize("changes", [{"reviewer": " "}, {"false_positive_findings": -1},
                                     {"false_positive_findings": True}, {"explanation_correct": "Maybe"}])
def test_invalid_human_judgements_are_not_saved(tmp_path, changes):
    run = saved_run(tmp_path)
    with pytest.raises(ValueError):
        save_review(run, "02-comparison", judgement(**changes), tmp_path / "reviews")


def test_response_tampering_and_fake_verified_claims_are_rejected(tmp_path):
    run = saved_run(tmp_path)
    data = json.loads(run.read_text())
    tampered = deepcopy(data)
    tampered["evidence"][0]["report"]["ai"]["raw_response"] = "rewritten"
    run.write_text(json.dumps(tampered))
    with pytest.raises(ValueError, match="hash"):
        read_run(run)
    data["results"][0]["ai_fix_successful"] = True
    run.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="verified"):
        read_run(run)


def test_csv_false_is_not_truthy_and_unreviewed_is_not_no():
    assert recorded_bool("False") is False
    result = metrics([{"case_id": "one", "ai_status": "malformed", "ai_produced_fix": "False",
                       "ai_fix_successful": "False", "analysis_seconds": "2"}], {})
    assert result["fixes_generated"] == 0 and result["human_reviewed"] == 0


def test_legacy_explicit_human_annotation_is_not_lost_or_double_counted():
    rows = [{"case_id": "one", "ai_detected_intended_bug": "Yes"}]
    assert metrics(rows, {})["intended_bug_yes"] == 1
    review = {"one": {"judgement": judgement(intended_bug_detected="No")}}
    assert metrics(rows, review)["intended_bug_yes"] == 0
    assert metrics(rows, review)["human_reviewed"] == 1


def test_launcher_uses_current_interpreter_and_no_shell(monkeypatch):
    import launch
    import sys
    from types import SimpleNamespace
    monkeypatch.setattr(OllamaProvider, "list_models", lambda self: ([], "Offline"))
    seen = []
    monkeypatch.setattr(launch.subprocess, "run", lambda *args, **kwargs: seen.append((args, kwargs)) or SimpleNamespace(returncode=0))
    assert launch.main([]) == 0
    assert seen[0][0][0][0] == sys.executable
    assert seen[0][1]["shell"] is False and seen[0][1]["cwd"] == launch.ROOT
