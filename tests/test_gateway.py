from __future__ import annotations

import json
import socket
import traceback
import urllib.error
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import evidence_inspector.gateway as gateway_module
from evidence_inspector.api import create_app
from evidence_inspector.cli import run
from evidence_inspector.engine import EvaluationService
from evidence_inspector.errors import ProviderTimeout, ProviderUnavailable
from evidence_inspector.gateway import (
    GATEWAY_MODE_ENV,
    MAX_PROVIDER_RESPONSE_BYTES,
    MODEL_ALLOWED_HOSTS_ENV,
    MODEL_API_KEY_ENV,
    MODEL_API_KEY_HEADER_ENV,
    MODEL_ENDPOINT_ENV,
    MODEL_NAME_ENV,
    MODEL_TIMEOUT_ENV,
    FixtureModelGateway,
    OpenAICompatibleConfig,
    OpenAICompatibleModelGateway,
    build_gateway_from_environment,
)
from evidence_inspector.schemas import Claim, EvidenceMatch, SupportLabel


SECRET = "test-secret-never-log"


class FakeResponse:
    def __init__(self, body: bytes, status: int = 200) -> None:
        self.body = body
        self.status = status

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def read(self, size: int = -1) -> bytes:
        return self.body if size < 0 else self.body[:size]


def _provider_body(
    label: str = "SUPPORTED",
    confidence: float = 0.91,
    rationale: str = "Supplied evidence supports the claim.",
) -> bytes:
    decision = json.dumps(
        {"label": label, "confidence": confidence, "rationale": rationale},
        sort_keys=True,
    )
    return json.dumps({"choices": [{"message": {"content": decision}}]}).encode("utf-8")


def _deeply_nested_provider_body(depth: int = 1200) -> bytes:
    body = b"[" * depth + b"0" + b"]" * depth
    assert len(body) < MAX_PROVIDER_RESPONSE_BYTES
    return body


def _config(**overrides) -> OpenAICompatibleConfig:
    values = {
        "endpoint": "https://provider.example/v1/chat/completions",
        "api_key": SECRET,
        "model": "course-model-v1",
        "approved_hosts": frozenset({"provider.example"}),
        "timeout_seconds": 3.5,
        "api_key_header": "Authorization",
    }
    values.update(overrides)
    return OpenAICompatibleConfig(**values)


def _environment(**overrides: str) -> dict[str, str]:
    values = {
        GATEWAY_MODE_ENV: "openai-compatible",
        MODEL_ENDPOINT_ENV: "https://provider.example/v1/chat/completions",
        MODEL_API_KEY_ENV: SECRET,
        MODEL_NAME_ENV: "course-model-v1",
        MODEL_TIMEOUT_ENV: "3.5",
        MODEL_API_KEY_HEADER_ENV: "Authorization",
        MODEL_ALLOWED_HOSTS_ENV: "provider.example",
    }
    values.update(overrides)
    return values


def _claim_and_matches() -> tuple[Claim, list[EvidenceMatch]]:
    return (
        Claim(id="c001", text="The audit is append-only [E1]."),
        [EvidenceMatch(evidence_id="E1", score=0.9, excerpt="The audit is append-only.")],
    )


def _formatted_exception(exc: BaseException) -> str:
    return "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))


def test_environment_factory_defaults_to_fixture_even_with_provider_values() -> None:
    gateway = build_gateway_from_environment(
        {
            MODEL_ENDPOINT_ENV: "https://provider.example/v1/chat/completions",
            MODEL_API_KEY_ENV: SECRET,
            MODEL_NAME_ENV: "unused-model",
        }
    )
    assert isinstance(gateway, FixtureModelGateway)


def test_environment_factory_requires_explicit_complete_opt_in() -> None:
    with pytest.raises(ProviderUnavailable, match="requires endpoint, API key, and model") as exc:
        build_gateway_from_environment({GATEWAY_MODE_ENV: "openai-compatible"})
    assert SECRET not in str(exc.value)
    with pytest.raises(ProviderUnavailable, match="must be fixture or openai-compatible"):
        build_gateway_from_environment({GATEWAY_MODE_ENV: "automatic"})
    with pytest.raises(ProviderUnavailable, match="must be numeric"):
        build_gateway_from_environment(_environment(**{MODEL_TIMEOUT_ENV: "soon"}))
    with pytest.raises(ProviderUnavailable, match="approved-host allowlist"):
        build_gateway_from_environment(
            _environment(**{MODEL_ALLOWED_HOSTS_ENV: ""})
        )


def test_environment_factory_builds_azure_header_configuration() -> None:
    gateway = build_gateway_from_environment(
        _environment(
            **{
                MODEL_API_KEY_HEADER_ENV: "API-KEY",
                MODEL_ENDPOINT_ENV: (
                    "https://azure.example/openai/deployments/course/chat/completions"
                    "?api-version=2025-01-01-preview"
                ),
                MODEL_ALLOWED_HOSTS_ENV: "azure.example",
            }
        )
    )
    assert isinstance(gateway, OpenAICompatibleModelGateway)
    assert gateway.name == "openai-compatible:course-model-v1"
    assert gateway._config.api_key_header == "api-key"
    assert gateway._config.approved_hosts == frozenset({"azure.example"})
    assert "api-version=" in gateway._config.endpoint
    assert SECRET not in repr(gateway._config)
    assert SECRET not in repr(gateway)


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://provider.example/v1/chat/completions",
        "https://user:password@provider.example/v1/chat/completions",
        "https://provider.example/v1/chat/completions#secret-fragment",
        "https://provider.example/v1/chat/completions?api-version=1&api-key=secret",
        "https://provider.example/v1/chat/completions?client_secret=secret",
        "https://provider.example/v1/chat/completions?password=secret",
        "https://provider.example/v1/chat/completions?x-api-key=secret",
        "https://provider.example/v1/chat/completions?subscription-key=secret",
        "https://provider.example/v1/chat/completions?api-version=",
        (
            "https://provider.example/v1/chat/completions"
            "?api-version=2025-01-01-preview;client_secret=secret"
        ),
        "https://provider.example/v1/chat/completions?api-version=1&api-version=2",
        "https://provider example/v1/chat/completions",
        "https://provider.example:notaport/v1/chat/completions",
        "https:///v1/chat/completions",
        "https://provider.example",
    ],
)
def test_config_rejects_unsafe_endpoints_without_echoing_values(endpoint: str) -> None:
    with pytest.raises(ProviderUnavailable, match="approved HTTPS URL") as exc:
        _config(endpoint=endpoint)
    assert endpoint not in str(exc.value)
    assert SECRET not in str(exc.value)


def test_config_allows_only_api_version_query_and_hides_the_endpoint_from_repr() -> None:
    marker = "SYNTHETIC-ENDPOINT-MARKER"
    config = _config(
        endpoint=(
            f"https://provider.example/v1/chat/completions/{marker}"
            "?api-version=2025-01-01-preview"
        )
    )
    assert marker in config.endpoint
    assert marker not in repr(config)
    assert "provider.example" not in repr(config)


def test_malformed_endpoint_suppresses_query_secret_from_formatted_traceback() -> None:
    marker = "SYNTHETIC-QUERY-SECRET"
    with pytest.raises(ProviderUnavailable, match="approved HTTPS URL") as captured:
        _config(
            endpoint=(
                "https://provider.example/v1/chat/completions?"
                f"{marker}"
            )
        )
    assert captured.value.__cause__ is None
    assert captured.value.__suppress_context__ is True
    assert marker not in _formatted_exception(captured.value)


def test_config_requires_an_exact_approved_host_but_allows_explicit_private_hosts() -> None:
    with pytest.raises(ProviderUnavailable, match="not in the approved-host allowlist"):
        _config(approved_hosts=frozenset({"other.example"}))

    private = _config(
        endpoint="https://127.0.0.1/v1/chat/completions",
        approved_hosts=frozenset({"127.0.0.1"}),
    )
    assert private.approved_hosts == frozenset({"127.0.0.1"})


@pytest.mark.parametrize(
    "approved_hosts",
    [
        frozenset(),
        frozenset({"https://provider.example"}),
        frozenset({"provider.example/path"}),
        frozenset({"provider example"}),
    ],
)
def test_config_rejects_empty_or_url_shaped_approved_hosts(approved_hosts) -> None:
    with pytest.raises(ProviderUnavailable, match="approved-host allowlist"):
        _config(approved_hosts=approved_hosts)


@pytest.mark.parametrize(
    ("override", "message"),
    [
        ({"model": "  "}, "model name"),
        ({"model": "bad\nmodel"}, "model name"),
        ({"api_key": "  "}, "API key"),
        ({"api_key": "secret\nheader"}, "API key"),
        ({"api_key_header": None}, "API key header"),
        ({"api_key_header": "X-Api-Key"}, "API key header"),
        ({"timeout_seconds": 0.0}, "model timeout"),
        ({"timeout_seconds": 60.1}, "model timeout"),
        ({"timeout_seconds": float("nan")}, "model timeout"),
        ({"timeout_seconds": True}, "model timeout"),
    ],
)
def test_config_rejects_unsafe_model_key_header_and_timeout(override, message: str) -> None:
    with pytest.raises(ProviderUnavailable, match=message) as exc:
        _config(**override)
    assert SECRET not in str(exc.value)


@pytest.mark.parametrize(
    ("header", "expected_header", "expected_value"),
    [
        ("Authorization", "authorization", f"Bearer {SECRET}"),
        ("api-key", "api-key", SECRET),
    ],
)
def test_compatible_gateway_builds_safe_request_and_parses_response(
    monkeypatch,
    header: str,
    expected_header: str,
    expected_value: str,
) -> None:
    captured: dict[str, object] = {}

    def fake_urlopen(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return FakeResponse(_provider_body())

    monkeypatch.setattr(gateway_module, "_open_request", fake_urlopen)
    gateway = OpenAICompatibleModelGateway(_config(api_key_header=header))
    claim, matches = _claim_and_matches()
    decision = gateway.classify(claim, matches)

    request = captured["request"]
    request_headers = {name.lower(): value for name, value in request.header_items()}
    payload = json.loads(request.data.decode("utf-8"))
    prompt = json.loads(payload["messages"][1]["content"])
    assert request.full_url == "https://provider.example/v1/chat/completions"
    assert request.get_method() == "POST"
    assert captured["timeout"] == 3.5
    assert request_headers[expected_header] == expected_value
    assert payload["model"] == "course-model-v1"
    assert payload["temperature"] == 0
    assert payload["response_format"] == {"type": "json_object"}
    assert prompt["claim"] == claim.text
    assert prompt["evidence"][0]["evidence_id"] == "E1"
    assert prompt["labels"] == [label.value for label in SupportLabel]
    assert decision.label == SupportLabel.SUPPORTED
    assert decision.confidence == 0.91


def test_provider_request_uses_a_fail_closed_redirect_handler(monkeypatch) -> None:
    captured: dict[str, object] = {}
    response = FakeResponse(_provider_body())

    class FakeOpener:
        def open(self, request, timeout):
            captured["request"] = request
            captured["timeout"] = timeout
            return response

    def fake_build_opener(handler):
        captured["handler"] = handler
        return FakeOpener()

    monkeypatch.setattr(gateway_module.urllib.request, "build_opener", fake_build_opener)
    request = gateway_module.urllib.request.Request("https://provider.example/v1/test")

    assert gateway_module._open_request(request, 2.0) is response
    assert captured["request"] is request
    assert captured["timeout"] == 2.0
    handler = captured["handler"]
    assert isinstance(handler, gateway_module._FailClosedRedirectHandler)
    assert (
        handler.redirect_request(
            request,
            None,
            302,
            "Found",
            {},
            "http://other.example/downgrade",
        )
        is None
    )


def test_compatible_gateway_maps_socket_timeout(monkeypatch) -> None:
    def fail_urlopen(request, timeout):
        raise socket.timeout("synthetic timeout")

    monkeypatch.setattr(gateway_module, "_open_request", fail_urlopen)
    claim, matches = _claim_and_matches()
    with pytest.raises(ProviderTimeout, match="provider timed out") as exc:
        OpenAICompatibleModelGateway(_config()).classify(claim, matches)
    assert SECRET not in str(exc.value)


def test_compatible_gateway_maps_urlerror_timeout(monkeypatch) -> None:
    def fail_urlopen(request, timeout):
        raise urllib.error.URLError(socket.timeout("synthetic wrapped timeout"))

    monkeypatch.setattr(gateway_module, "_open_request", fail_urlopen)
    claim, matches = _claim_and_matches()
    with pytest.raises(ProviderTimeout, match="provider timed out"):
        OpenAICompatibleModelGateway(_config()).classify(claim, matches)


@pytest.mark.parametrize("failure", ["http", "url", "os", "status"])
def test_compatible_gateway_maps_provider_failures(monkeypatch, failure: str) -> None:
    def fail_urlopen(request, timeout):
        if failure == "http":
            raise urllib.error.HTTPError(request.full_url, 429, "rate limited", {}, None)
        if failure == "url":
            raise urllib.error.URLError("synthetic connection failure")
        if failure == "os":
            raise OSError("synthetic read failure")
        return FakeResponse(_provider_body(), status=503)

    monkeypatch.setattr(gateway_module, "_open_request", fail_urlopen)
    claim, matches = _claim_and_matches()
    with pytest.raises(ProviderUnavailable, match="provider request failed") as exc:
        OpenAICompatibleModelGateway(_config()).classify(claim, matches)
    assert SECRET not in str(exc.value)


def test_provider_transport_error_suppresses_endpoint_from_formatted_traceback(
    monkeypatch,
) -> None:
    marker = "SYNTHETIC-ENDPOINT-PATH-SECRET"
    config = _config(
        endpoint=f"https://provider.example/v1/{marker}/chat/completions"
    )

    def fail_urlopen(request, timeout):
        raise urllib.error.HTTPError(request.full_url, 503, "unavailable", {}, None)

    monkeypatch.setattr(gateway_module, "_open_request", fail_urlopen)
    claim, matches = _claim_and_matches()
    with pytest.raises(ProviderUnavailable, match="provider request failed") as captured:
        OpenAICompatibleModelGateway(config).classify(claim, matches)
    assert captured.value.__cause__ is None
    assert captured.value.__suppress_context__ is True
    assert marker not in _formatted_exception(captured.value)


@pytest.mark.parametrize(
    "body",
    [
        b"{not-json",
        json.dumps({"choices": []}).encode("utf-8"),
        json.dumps({"choices": [{"message": {"content": "not-json"}}]}).encode("utf-8"),
        _provider_body(label="NOT_A_LABEL"),
    ],
)
def test_compatible_gateway_rejects_malformed_decisions(monkeypatch, body: bytes) -> None:
    monkeypatch.setattr(
        gateway_module,
        "_open_request",
        lambda request, timeout: FakeResponse(body),
    )
    claim, matches = _claim_and_matches()
    with pytest.raises(ProviderUnavailable, match="invalid decision") as exc:
        OpenAICompatibleModelGateway(_config()).classify(claim, matches)
    assert SECRET not in str(exc.value)


def test_compatible_gateway_rejects_oversized_response(monkeypatch) -> None:
    body = b"x" * (MAX_PROVIDER_RESPONSE_BYTES + 1)
    monkeypatch.setattr(
        gateway_module,
        "_open_request",
        lambda request, timeout: FakeResponse(body),
    )
    claim, matches = _claim_and_matches()
    with pytest.raises(ProviderUnavailable, match="safe size limit"):
        OpenAICompatibleModelGateway(_config()).classify(claim, matches)


def test_compatible_gateway_maps_deeply_nested_json_to_provider_unavailable(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        gateway_module,
        "_open_request",
        lambda request, timeout: FakeResponse(_deeply_nested_provider_body()),
    )
    claim, matches = _claim_and_matches()
    with pytest.raises(ProviderUnavailable, match="invalid decision") as exc:
        OpenAICompatibleModelGateway(_config()).classify(claim, matches)
    assert type(exc.value) is ProviderUnavailable
    assert SECRET not in str(exc.value)


@pytest.mark.parametrize(
    "failure",
    ["timeout", "http", "malformed", "deeply-nested", "oversized"],
)
def test_compatible_provider_failures_create_no_completed_run(
    monkeypatch,
    tmp_path,
    sample_bundle,
    failure: str,
) -> None:
    def fail_urlopen(request, timeout):
        if failure == "timeout":
            raise socket.timeout("synthetic timeout")
        if failure == "http":
            raise urllib.error.HTTPError(request.full_url, 500, "failure", {}, None)
        if failure == "oversized":
            return FakeResponse(b"x" * (MAX_PROVIDER_RESPONSE_BYTES + 1))
        if failure == "deeply-nested":
            return FakeResponse(_deeply_nested_provider_body())
        return FakeResponse(b"{not-json")

    monkeypatch.setattr(gateway_module, "_open_request", fail_urlopen)
    service = EvaluationService(tmp_path, gateway=OpenAICompatibleModelGateway(_config()))
    with pytest.raises(ProviderUnavailable):
        service.evaluate(sample_bundle)
    assert list(tmp_path.iterdir()) == []


def test_cli_evaluate_uses_explicit_environment_gateway(
    monkeypatch,
    tmp_path,
    capsys,
) -> None:
    project = Path(__file__).resolve().parents[1]
    for name, value in _environment().items():
        monkeypatch.setenv(name, value)
    monkeypatch.setattr(
        gateway_module,
        "_open_request",
        lambda request, timeout: FakeResponse(_provider_body()),
    )
    runs_dir = tmp_path / "cli-runs"
    assert run(
        [
            "evaluate",
            str(project / "examples" / "sample_bundle.json"),
            "--out",
            str(runs_dir),
        ]
    ) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["gateway"] == "openai-compatible:course-model-v1"
    assert (runs_dir / report["run_id"] / "report.json").is_file()


def test_api_create_app_uses_explicit_environment_gateway(tmp_path, sample_bundle, monkeypatch) -> None:
    monkeypatch.setattr(
        gateway_module,
        "_open_request",
        lambda request, timeout: FakeResponse(_provider_body()),
    )
    client = TestClient(create_app(runs_dir=tmp_path, environ=_environment()))
    response = client.post("/v1/evaluations", json=sample_bundle.model_dump(mode="json"))
    assert response.status_code == 201
    assert response.json()["gateway"] == "openai-compatible:course-model-v1"


def test_cli_maps_deeply_nested_provider_json_without_creating_a_run(
    monkeypatch,
    tmp_path,
    capsys,
) -> None:
    project = Path(__file__).resolve().parents[1]
    for name, value in _environment().items():
        monkeypatch.setenv(name, value)
    monkeypatch.setattr(
        gateway_module,
        "_open_request",
        lambda request, timeout: FakeResponse(_deeply_nested_provider_body()),
    )
    runs_dir = tmp_path / "cli-deep-json-runs"

    assert run(
        [
            "evaluate",
            str(project / "examples" / "sample_bundle.json"),
            "--out",
            str(runs_dir),
        ]
    ) == 2
    captured = capsys.readouterr()
    assert "invalid decision" in captured.err
    assert SECRET not in captured.err
    assert not runs_dir.exists()


def test_api_maps_deeply_nested_provider_json_to_503_without_a_run(
    monkeypatch,
    tmp_path,
    sample_bundle,
) -> None:
    monkeypatch.setattr(
        gateway_module,
        "_open_request",
        lambda request, timeout: FakeResponse(_deeply_nested_provider_body()),
    )
    client = TestClient(
        create_app(runs_dir=tmp_path, environ=_environment()),
        raise_server_exceptions=False,
    )

    response = client.post("/v1/evaluations", json=sample_bundle.model_dump(mode="json"))
    assert response.status_code == 503
    assert response.json()["detail"] == "model provider returned an invalid decision"
    assert SECRET not in response.text
    assert list(tmp_path.iterdir()) == []
