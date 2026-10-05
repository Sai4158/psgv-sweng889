import json

import pytest
import requests

from bug_hunter.ai.ollama_provider import OllamaProvider, parse_ai_response


def payload():
    return {"summary": "The function misses the last value.", "findings": [{
        "title": "Off-by-one", "category": "off-by-one", "line": 2, "location": None,
        "severity": "Medium", "explanation": "The last value is excluded.",
        "why_incorrect": "It should include all values.", "suggested_fix": "Use sum(values).",
    }], "corrected_code": "def total(values):\n    return sum(values)\n"}


def test_valid_json_is_validated_without_recovery():
    result, recovered = parse_ai_response(json.dumps(payload()))
    assert result.findings[0].line == 2
    assert result.findings[0].severity == "Medium"
    assert recovered is False


@pytest.mark.parametrize("wrapper", ["```json\n{}\n```", "Response:\n{}\nEnd."])
def test_safe_recovery_accepts_only_a_valid_json_object(wrapper):
    result, recovered = parse_ai_response(wrapper.format(json.dumps(payload())))
    assert result.corrected_code.endswith("sum(values)")
    assert recovered is True


@pytest.mark.parametrize("raw", ["", "not JSON", "{bad}", "[]", '{"summary":"missing fields"}',
                                 '{"summary": "x"} {"summary": "y"}'])
def test_malformed_outputs_are_rejected(raw):
    with pytest.raises(ValueError):
        parse_ai_response(raw)


@pytest.mark.parametrize("field,value", [("line", 0), ("line", True), ("severity", "Critical"),
                                        ("explanation", " "), ("suggested_fix", 12)])
def test_invalid_finding_fields_are_rejected(field, value):
    data = payload()
    data["findings"][0][field] = value
    with pytest.raises(ValueError):
        parse_ai_response(json.dumps(data))


def test_empty_findings_is_valid_and_not_a_failure():
    data = payload()
    data["findings"] = []
    assert parse_ai_response(json.dumps(data))[0].findings == []


@pytest.mark.parametrize("url", ["https://example.com", "http://ollama.com", "http://localhost@evil.com",
                                "http://localhost/api", "http://localhost/?x=1"])
def test_hosted_or_ambiguous_provider_urls_are_rejected(url):
    with pytest.raises(ValueError, match="loopback"):
        OllamaProvider(url)


class FakeResponse:
    status_code = 200

    def __init__(self, data):
        self.data = data

    def json(self):
        return self.data


def provider_with_models(monkeypatch):
    provider = OllamaProvider()
    monkeypatch.setattr(provider.session, "get", lambda *a, **k: FakeResponse({"models": [{"name": "local:1b"}]}))
    return provider


def test_local_model_discovery_excludes_cloud_models(monkeypatch):
    provider = OllamaProvider()
    monkeypatch.setattr(provider.session, "get", lambda *a, **k: FakeResponse({"models": [
        {"name": "local:1b"}, {"name": "large-cloud"},
        {"name": "remote", "remote_host": "https://ollama.com"},
    ]}))
    assert provider.list_models() == (["local:1b"], None)
    assert provider.session.trust_env is False


def test_unavailable_server_does_not_raise(monkeypatch):
    provider = OllamaProvider()
    def disconnected(*args, **kwargs):
        raise requests.ConnectionError()
    monkeypatch.setattr(provider.session, "get", disconnected)
    assert provider.analyze("x=1", "", "", "local:1b").status == "unavailable"


def test_no_model_installed_is_clear(monkeypatch):
    provider = OllamaProvider()
    monkeypatch.setattr(provider.session, "get", lambda *a, **k: FakeResponse({"models": []}))
    names, error = provider.list_models()
    assert names == [] and "no local model" in error


def test_missing_selected_model_is_not_sent_to_server(monkeypatch):
    provider = provider_with_models(monkeypatch)
    monkeypatch.setattr(provider.session, "post", lambda *a, **k: pytest.fail("must not call missing model"))
    assert provider.analyze("x=1", "", "", "missing").status == "unavailable"


def test_model_timeout_is_reported(monkeypatch):
    provider = provider_with_models(monkeypatch)
    def timeout(*args, **kwargs):
        raise requests.Timeout()
    monkeypatch.setattr(provider.session, "post", timeout)
    assert provider.analyze("x=1", "", "", "local:1b").status == "timeout"


def test_request_is_local_structured_and_tracks_only_real_tokens(monkeypatch):
    provider = provider_with_models(monkeypatch)
    def post(url, **kwargs):
        assert url == "http://localhost:11434/api/chat"
        assert kwargs["json"]["stream"] is False
        assert kwargs["json"]["format"]["type"] == "object"
        assert kwargs["allow_redirects"] is False
        return FakeResponse({"done": True, "message": {"content": json.dumps(payload())}, "eval_count": 42})
    monkeypatch.setattr(provider.session, "post", post)
    result = provider.analyze("def total(x):\n    return sum(x[:-1])", "", "", "local:1b")
    assert result.status == "ok"
    assert result.completion_tokens == 42
    assert result.prompt_tokens is None


def test_out_of_range_model_line_is_rejected(monkeypatch):
    provider = provider_with_models(monkeypatch)
    monkeypatch.setattr(provider.session, "post", lambda *a, **k: FakeResponse({
        "done": True, "message": {"content": json.dumps(payload())},
    }))
    assert provider.analyze("x=1", "", "", "local:1b").status == "malformed"


@pytest.mark.parametrize("response", [[], None])
def test_non_object_generation_response_is_a_graceful_failure(monkeypatch, response):
    provider = provider_with_models(monkeypatch)
    monkeypatch.setattr(provider.session, "post", lambda *a, **k: FakeResponse(response))
    result = provider.analyze("x=1", "", "", "local:1b")
    assert result.status == "malformed"
    assert "JSON object" in result.error
