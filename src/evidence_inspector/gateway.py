"""Model gateway boundary and deterministic fixture implementation."""

from __future__ import annotations

import http.client
import ipaddress
import json
import math
import os
import re
import socket
import urllib.error
import urllib.parse
import urllib.request
from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass, field

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .errors import ProviderTimeout, ProviderUnavailable
from .retrieval import tokens
from .schemas import Claim, EvidenceMatch, SupportLabel


GATEWAY_MODE_ENV = "EVIDENCE_INSPECTOR_GATEWAY"
MODEL_ENDPOINT_ENV = "EVIDENCE_INSPECTOR_MODEL_ENDPOINT"
MODEL_API_KEY_ENV = "EVIDENCE_INSPECTOR_MODEL_API_KEY"
MODEL_NAME_ENV = "EVIDENCE_INSPECTOR_MODEL"
MODEL_API_KEY_HEADER_ENV = "EVIDENCE_INSPECTOR_MODEL_API_KEY_HEADER"
MODEL_TIMEOUT_ENV = "EVIDENCE_INSPECTOR_MODEL_TIMEOUT_SECONDS"
MODEL_ALLOWED_HOSTS_ENV = "EVIDENCE_INSPECTOR_MODEL_ALLOWED_HOSTS"
MAX_PROVIDER_RESPONSE_BYTES = 65_536
_ALLOWED_API_KEY_HEADERS = {
    "authorization": "Authorization",
    "api-key": "api-key",
}
_ALLOWED_ENDPOINT_QUERY_KEY = "api-version"
_AZURE_API_VERSION = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}(?:-preview)?$")
_DNS_LABEL = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$")


class GatewayDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    label: SupportLabel
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str = Field(min_length=1, max_length=2000)


class ModelGateway(ABC):
    """A narrow provider boundary; providers never write artifacts."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def classify(self, claim: Claim, matches: list[EvidenceMatch]) -> GatewayDecision: ...


_NEGATIONS = {"no", "not", "never", "cannot", "neither", "nor"}


class FixtureModelGateway(ModelGateway):
    """Deterministic local baseline used by tests, CI, and the sample demo."""

    def __init__(
        self,
        rules: dict[str, SupportLabel] | None = None,
        fail_mode: str | None = None,
        *,
        name: str = "fixture-v1",
    ) -> None:
        self._rules = rules or {}
        self._fail_mode = fail_mode
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def classify(self, claim: Claim, matches: list[EvidenceMatch]) -> GatewayDecision:
        if self._fail_mode == "timeout":
            raise ProviderTimeout("fixture provider timed out")
        if self._fail_mode == "unavailable":
            raise ProviderUnavailable("fixture provider unavailable")
        if claim.text in self._rules:
            return GatewayDecision(
                label=self._rules[claim.text],
                confidence=1.0,
                rationale="Exact deterministic fixture rule.",
            )
        if not matches or matches[0].score < 0.03:
            return GatewayDecision(
                label=SupportLabel.INSUFFICIENT_EVIDENCE,
                confidence=0.9,
                rationale="No retrieved evidence passed the minimum lexical signal.",
            )

        claim_tokens = tokens(_strip_audit_markup(claim.text))
        evidence_tokens = tokens(matches[0].excerpt)
        overlap = len(claim_tokens & evidence_tokens) / max(1, len(claim_tokens))
        claim_negated = bool(claim_tokens & _NEGATIONS)
        evidence_negated = bool(evidence_tokens & _NEGATIONS)
        if overlap >= 0.45 and claim_negated != evidence_negated:
            return GatewayDecision(
                label=SupportLabel.CONTRADICTED,
                confidence=min(0.95, 0.55 + overlap / 2),
                rationale="Claim and best evidence have high lexical overlap but opposing negation.",
            )
        if (
            re.search(r"\bboth\b.+\band\b", claim.text, re.IGNORECASE)
            and claim_tokens - evidence_tokens
            and overlap >= 0.20
        ):
            return GatewayDecision(
                label=SupportLabel.PARTIALLY_SUPPORTED,
                confidence=min(0.9, 0.55 + overlap / 2),
                rationale="A coordinated claim has evidence for only part of its stated terms.",
            )
        if overlap >= 0.70:
            label, rationale = SupportLabel.SUPPORTED, "Best evidence covers most claim terms."
        elif overlap >= 0.40:
            label, rationale = (
                SupportLabel.PARTIALLY_SUPPORTED,
                "Best evidence covers only part of the claim.",
            )
        elif overlap >= 0.10:
            label, rationale = SupportLabel.UNSUPPORTED, "Retrieved evidence lacks key claim terms."
        else:
            label, rationale = (
                SupportLabel.INSUFFICIENT_EVIDENCE,
                "Retrieved evidence has no meaningful claim-level lexical overlap.",
            )
        return GatewayDecision(label=label, confidence=min(0.95, 0.5 + overlap / 2), rationale=rationale)


def _strip_audit_markup(text: str) -> str:
    text = re.sub(r"\[(?:evidence:)?[A-Za-z0-9_.-]+\]", " ", text, flags=re.IGNORECASE)
    return re.sub(r"[\"“”]", " ", text)


@dataclass(frozen=True)
class OpenAICompatibleConfig:
    """Configuration for a full chat-completions URL, including Azure endpoints."""

    endpoint: str = field(repr=False)
    api_key: str = field(repr=False)
    model: str
    approved_hosts: frozenset[str] = field(default_factory=frozenset, repr=False)
    timeout_seconds: float = 20.0
    api_key_header: str = "Authorization"

    def __post_init__(self) -> None:
        try:
            parsed = urllib.parse.urlsplit(self.endpoint)
            hostname = parsed.hostname
            _ = parsed.port
            query_pairs = urllib.parse.parse_qsl(
                parsed.query,
                keep_blank_values=True,
                strict_parsing=True,
                max_num_fields=2,
            )
        except (TypeError, ValueError):
            raise ProviderUnavailable(
                "model endpoint must be an approved HTTPS URL with only an optional "
                "api-version query"
            ) from None
        if (
            parsed.scheme.lower() != "https"
            or not hostname
            or parsed.path in {"", "/"}
            or parsed.username is not None
            or parsed.password is not None
            or bool(parsed.fragment)
            or len(query_pairs) > 1
            or any(
                key != _ALLOWED_ENDPOINT_QUERY_KEY
                or not _AZURE_API_VERSION.fullmatch(value)
                for key, value in query_pairs
            )
            or len(self.endpoint) > 2048
            or any(character.isspace() or ord(character) < 32 for character in self.endpoint)
        ):
            raise ProviderUnavailable(
                "model endpoint must be an approved HTTPS URL with only an optional "
                "api-version query"
            )
        canonical_endpoint_host = _canonical_approved_host(hostname)
        if isinstance(self.approved_hosts, (str, bytes)):
            raise ProviderUnavailable("model approved-host allowlist is invalid")
        try:
            canonical_approved_hosts = frozenset(
                _canonical_approved_host(item) for item in self.approved_hosts
            )
        except TypeError:
            raise ProviderUnavailable("model approved-host allowlist is invalid") from None
        if not canonical_approved_hosts or canonical_endpoint_host not in canonical_approved_hosts:
            raise ProviderUnavailable("model endpoint host is not in the approved-host allowlist")
        if (
            not isinstance(self.model, str)
            or not self.model.strip()
            or len(self.model) > 200
            or any(ord(character) < 32 for character in self.model)
        ):
            raise ProviderUnavailable("model name must be a non-empty safe string")
        if (
            not isinstance(self.api_key, str)
            or not self.api_key.strip()
            or len(self.api_key) > 4096
            or any(ord(character) < 32 or ord(character) == 127 for character in self.api_key)
        ):
            raise ProviderUnavailable("model API key is missing or invalid")
        if not isinstance(self.api_key_header, str):
            raise ProviderUnavailable("model API key header is not supported")
        canonical_header = _ALLOWED_API_KEY_HEADERS.get(self.api_key_header.lower())
        if canonical_header is None:
            raise ProviderUnavailable(
                "model API key header must be Authorization or api-key"
            )
        if (
            isinstance(self.timeout_seconds, bool)
            or not isinstance(self.timeout_seconds, (int, float))
            or not math.isfinite(float(self.timeout_seconds))
            or not 0.1 <= float(self.timeout_seconds) <= 60.0
        ):
            raise ProviderUnavailable("model timeout must be between 0.1 and 60.0 seconds")
        object.__setattr__(self, "api_key_header", canonical_header)
        object.__setattr__(self, "timeout_seconds", float(self.timeout_seconds))
        object.__setattr__(self, "approved_hosts", canonical_approved_hosts)


def _canonical_approved_host(value: object) -> str:
    """Return one comparison-safe hostname without accepting URL-shaped values."""

    if not isinstance(value, str) or not value or value != value.strip():
        raise ProviderUnavailable("model approved-host allowlist contains an invalid host")
    candidate = value[:-1] if value.endswith(".") else value
    if candidate.startswith("[") and candidate.endswith("]"):
        candidate = candidate[1:-1]
    try:
        return ipaddress.ip_address(candidate).compressed.lower()
    except ValueError:
        pass
    if (
        not candidate
        or not candidate.isascii()
        or len(candidate) > 253
        or any(not _DNS_LABEL.fullmatch(label) for label in candidate.split("."))
    ):
        raise ProviderUnavailable("model approved-host allowlist contains an invalid host")
    return candidate.lower()


def _parse_approved_hosts(raw_value: str | None) -> frozenset[str]:
    if raw_value is None or not raw_value.strip():
        raise ProviderUnavailable(
            "openai-compatible gateway requires a non-empty approved-host allowlist"
        )
    raw_hosts = raw_value.split(",")
    if any(not host.strip() for host in raw_hosts):
        raise ProviderUnavailable("model approved-host allowlist contains an invalid host")
    return frozenset(_canonical_approved_host(host.strip()) for host in raw_hosts)


def build_gateway_from_environment(
    environ: Mapping[str, str] | None = None,
) -> ModelGateway:
    """Build the explicitly selected gateway without exposing configuration secrets.

    Fixture mode is the default even if unrelated provider variables are present.
    A network-capable gateway is constructed only when the mode is exactly
    ``openai-compatible``.
    """

    values = os.environ if environ is None else environ
    mode = values.get(GATEWAY_MODE_ENV, "fixture").strip().lower()
    if mode in {"", "fixture"}:
        return FixtureModelGateway()
    if mode != "openai-compatible":
        raise ProviderUnavailable(
            f"{GATEWAY_MODE_ENV} must be fixture or openai-compatible"
        )

    endpoint = values.get(MODEL_ENDPOINT_ENV)
    api_key = values.get(MODEL_API_KEY_ENV)
    model = values.get(MODEL_NAME_ENV)
    missing = [
        name
        for name, value in (
            (MODEL_ENDPOINT_ENV, endpoint),
            (MODEL_API_KEY_ENV, api_key),
            (MODEL_NAME_ENV, model),
        )
        if value is None or not value.strip()
    ]
    if missing:
        raise ProviderUnavailable(
            "openai-compatible gateway requires endpoint, API key, and model environment variables"
        )
    raw_timeout = values.get(MODEL_TIMEOUT_ENV, "20.0")
    try:
        timeout_seconds = float(raw_timeout)
    except (TypeError, ValueError):
        raise ProviderUnavailable("model timeout environment variable must be numeric") from None
    return OpenAICompatibleModelGateway(
        OpenAICompatibleConfig(
            endpoint=endpoint,
            api_key=api_key,
            model=model,
            approved_hosts=_parse_approved_hosts(values.get(MODEL_ALLOWED_HOSTS_ENV)),
            timeout_seconds=timeout_seconds,
            api_key_header=values.get(MODEL_API_KEY_HEADER_ENV, "Authorization"),
        )
    )


class OpenAICompatibleModelGateway(ModelGateway):
    """Minimal JSON-only Chat Completions adapter.

    `endpoint` is the full HTTPS URL. For Azure, pass its deployment-specific
    chat/completions URL and set `api_key_header="api-key"`.
    """

    def __init__(self, config: OpenAICompatibleConfig):
        self._config = config

    @property
    def name(self) -> str:
        return f"openai-compatible:{self._config.model}"

    def classify(self, claim: Claim, matches: list[EvidenceMatch]) -> GatewayDecision:
        prompt = {
            "claim": claim.text,
            "evidence": [match.model_dump(mode="json") for match in matches],
            "labels": [label.value for label in SupportLabel],
        }
        payload = json.dumps(
            {
                "model": self._config.model,
                "temperature": 0,
                "response_format": {"type": "json_object"},
                "messages": [
                    {
                        "role": "system",
                        "content": "Classify the claim using only supplied evidence. Return JSON with label, confidence, rationale.",
                    },
                    {"role": "user", "content": json.dumps(prompt, sort_keys=True)},
                ],
            }
        ).encode("utf-8")
        value = self._config.api_key
        if self._config.api_key_header.lower() == "authorization":
            value = f"Bearer {value}"
        request = urllib.request.Request(
            self._config.endpoint,
            data=payload,
            method="POST",
            headers={"Content-Type": "application/json", self._config.api_key_header: value},
        )
        try:
            with _open_request(request, timeout=self._config.timeout_seconds) as response:
                status = getattr(response, "status", 200)
                if not isinstance(status, int) or not 200 <= status < 300:
                    raise ProviderUnavailable("model provider request failed")
                raw_body = response.read(MAX_PROVIDER_RESPONSE_BYTES + 1)
            if len(raw_body) > MAX_PROVIDER_RESPONSE_BYTES:
                raise ProviderUnavailable("model provider response exceeded the safe size limit")
            body = json.loads(raw_body.decode("utf-8"))
            content = body["choices"][0]["message"]["content"]
            return GatewayDecision.model_validate_json(content)
        except (TimeoutError, socket.timeout):
            raise ProviderTimeout("model provider timed out") from None
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, (TimeoutError, socket.timeout)):
                raise ProviderTimeout("model provider timed out") from None
            raise ProviderUnavailable("model provider request failed") from None
        except (OSError, http.client.HTTPException):
            raise ProviderUnavailable("model provider request failed") from None
        except (
            KeyError,
            IndexError,
            TypeError,
            ValueError,
            RecursionError,
            ValidationError,
        ):
            raise ProviderUnavailable("model provider returned an invalid decision") from None


class _FailClosedRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Refuse redirects so credentials never follow a changed destination."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _open_request(request: urllib.request.Request, timeout: float):
    """Open one provider request without following redirects."""

    opener = urllib.request.build_opener(_FailClosedRedirectHandler())
    return opener.open(request, timeout=timeout)
