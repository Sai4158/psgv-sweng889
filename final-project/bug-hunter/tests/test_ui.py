from pathlib import Path
import pytest

from streamlit.testing.v1 import AppTest

from bug_hunter.ai.ollama_provider import OllamaProvider
from bug_hunter.demos import load_cases
from bug_hunter.models import AIAnalysis, AIResult

APP = Path(__file__).resolve().parents[1] / "app.py"


def button(app, label):
    return next(item for item in app.button if item.label == label)


def test_initial_ui_survives_ollama_unavailability(monkeypatch):
    monkeypatch.setattr(OllamaProvider, "list_models", lambda self: ([], "Ollama is unavailable."))
    app = AppTest.from_file(str(APP)).run()
    assert not app.exception
    assert app.title[0].value == "Bug Hunter"
    assert any("Ollama is unavailable" in item.value for item in app.warning)
    assert button(app, "Analyze Code")


def test_customer_header_is_compact_and_execution_consent_stays_clear(monkeypatch):
    monkeypatch.setattr(OllamaProvider, "list_models", lambda self: (["qwen2.5-coder:3b"], None))
    app = AppTest.from_file(str(APP)).run()
    assert not app.exception
    hero = next(item.proto.body for item in app.get("html") if 'class="product-intro"' in item.proto.body)
    assert "Python analysis &amp; fix validation" in hero
    assert "100% Local AI" not in hero
    assert "API" not in hero
    assert "electricity" not in hero
    assert not any("CPU/GPU" in item.value for item in app.caption)
    assert any("not a security sandbox" in item.value for item in app.caption)
    assert app.checkbox(key="trusted").label == "I trust this code and allow local execution."
    assert not app.checkbox(key="trusted").value


def test_demo_loader_and_reset_work(monkeypatch):
    monkeypatch.setattr(OllamaProvider, "list_models", lambda self: (["local:1b"], None))
    app = AppTest.from_file(str(APP)).run()
    button(app, "Load Example").click().run()
    assert app.text_area(key="source").value == load_cases()[0]["source"]
    assert "from candidate import average" in app.text_area(key="test_source").value
    button(app, "Reset").click().run()
    assert app.text_area(key="source").value == ""
    assert app.text_area(key="test_source").value == ""
    assert not app.exception


def test_ui_invalid_python_is_clear(monkeypatch):
    monkeypatch.setattr(OllamaProvider, "list_models", lambda self: (["local:1b"], None))
    app = AppTest.from_file(str(APP)).run()
    app.text_area(key="source").set_value("def invalid(:")
    button(app, "Analyze Code").click().run()
    assert any("syntax error" in item.value for item in app.error)
    assert not app.exception


def test_ui_displays_independent_before_after_evidence(monkeypatch):
    case = load_cases()[0]
    monkeypatch.setattr(OllamaProvider, "list_models", lambda self: (["local:1b"], None))
    monkeypatch.setattr(OllamaProvider, "analyze", lambda self, *args: AIResult(
        "ok", "local:1b", AIAnalysis(summary="Mocked test response", findings=[], corrected_code=case["reference"]),
    ))
    app = AppTest.from_file(str(APP)).run()
    button(app, "Load Example").click().run()
    button(app, "Analyze Code").click().run()
    assert any("Confirm" in item.value for item in app.error)
    app.checkbox(key="trusted").check()
    button(app, "Analyze Code").click().run(timeout=30)
    assert not app.exception
    assert [tab.label for tab in app.tabs] == ["Overview", "AI Findings", "Pylint Baseline", "Suggested Fix", "Test Validation", "Technical Details"]
    assert any(item.label == "Fix Verified" and item.value == "Yes" for item in app.metric)
    report = app.session_state["report"]
    assert report.original_tests.failed == 3
    assert report.corrected_tests.passed == 3


def test_selecting_demo_automatically_populates_both_inputs(monkeypatch):
    monkeypatch.setattr(OllamaProvider, "list_models", lambda self: (["local:1b"], None))
    app = AppTest.from_file(str(APP)).run()
    app.selectbox(key="demo_choice").set_value("02-comparison").run()
    case = next(case for case in load_cases() if case["id"] == "02-comparison")
    assert app.text_area(key="source").value == case["source"]
    assert app.text_area(key="test_source").value == case["tests"]
    assert not app.checkbox(key="trusted").value


def test_performance_and_presentation_settings_do_not_change_inputs(monkeypatch):
    monkeypatch.setattr(OllamaProvider, "list_models", lambda self: (["qwen2.5-coder:3b", "qwen2.5-coder:7b"], None))
    app = AppTest.from_file(str(APP)).run()
    button(app, "Load Example").click().run()
    source, tests = app.text_area(key="source").value, app.text_area(key="test_source").value
    assert app.selectbox(key="selected_model").value == "qwen2.5-coder:3b"
    app.radio(key="performance_mode").set_value("Higher Quality").run()
    assert app.selectbox(key="selected_model").value == "qwen2.5-coder:7b"
    app.checkbox(key="presentation").check().run()
    assert not app.exception
    assert "Advanced Settings" not in [item.label for item in app.expander]
    assert app.text_area(key="source").value == source
    assert app.text_area(key="test_source").value == tests


def test_consent_required_even_without_tests(monkeypatch):
    monkeypatch.setattr(OllamaProvider, "list_models", lambda self: (["local:1b"], None))
    monkeypatch.setattr(OllamaProvider, "analyze", lambda *args: pytest.fail("must not analyze without consent"))
    app = AppTest.from_file(str(APP)).run()
    app.text_area(key="source").set_value("x=1")
    button(app, "Analyze Code").click().run()
    assert any("Confirm" in item.value for item in app.error)


def test_evaluation_dashboard_reads_recorded_data_without_an_ai_call(monkeypatch, tmp_path):
    from evaluation.run_evaluation import export_results
    from bug_hunter import evaluation_dashboard
    case = load_cases()[0]
    row = {"case_id": case["id"], "ollama_model": "unit-test fixture", "ai_status": "ok",
           "ai_produced_fix": False, "ai_fix_successful": False, "analysis_seconds": 12,
           "ai_detected_intended_bug": "Unreviewed", "pylint_detected_functional_issue": "No"}
    _, run = export_results([row], [{"case": case, "report": {"ai": {
        "raw_response": "Unit-test fixture, not evaluation evidence", "analysis": None}}}], tmp_path)
    monkeypatch.setattr(evaluation_dashboard, "list_runs", lambda: [run])
    monkeypatch.setattr(OllamaProvider, "list_models", lambda self: (["local:1b"], None))
    monkeypatch.setattr(OllamaProvider, "analyze", lambda *a: pytest.fail("dashboard must not invoke AI"))
    app = AppTest.from_file(str(APP)).run()
    app.radio(key="workspace").set_value("Evaluation").run()
    assert not app.exception
    assert any(item.label == "AI Responses Valid" and item.value == "1" for item in app.metric)
    assert any(item.label == "Intended Bug: Yes (Reviewed)" and item.value == "Unreviewed" for item in app.metric)


def test_refresh_models_recovers_after_ollama_was_offline(monkeypatch):
    response = [[], "Ollama is unavailable."]
    monkeypatch.setattr(OllamaProvider, "list_models", lambda self: tuple(response))
    app = AppTest.from_file(str(APP)).run()
    response[:] = [["qwen2.5-coder:3b"], None]
    button(app, "Refresh Models").click().run()
    assert not app.exception
    assert app.selectbox(key="selected_model").value == "qwen2.5-coder:3b"
    assert not any("unavailable" in item.value.lower() for item in app.warning)


def test_failed_ai_connection_keeps_baselines_and_updates_offline_status(monkeypatch):
    monkeypatch.setattr(OllamaProvider, "list_models", lambda self: (["local:1b"], None))
    monkeypatch.setattr(OllamaProvider, "analyze", lambda self, *args:
                        AIResult("unavailable", "local:1b", error="Ollama is unavailable."))
    app = AppTest.from_file(str(APP)).run()
    button(app, "Load Example").click().run()
    app.checkbox(key="trusted").check()
    button(app, "Analyze Code").click().run(timeout=30)
    assert not app.exception
    report = app.session_state["report"]
    assert report.pylint.status == "ok" and report.original_tests.failed == 3
    assert not report.fix_verified
    assert any("unavailable" in item.value.lower() for item in app.warning)
    assert app.session_state["model_discovery"][0] == []
