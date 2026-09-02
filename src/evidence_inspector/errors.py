"""Typed errors used to fail closed at system boundaries."""


class EvidenceInspectorError(Exception):
    """Base class for expected domain failures."""


class UnsafeInputError(EvidenceInspectorError):
    """Raised when untrusted content contains a prompt-injection pattern."""


class TokenBudgetExceeded(EvidenceInspectorError):
    """Raised before a provider call would exceed the configured budget."""


class NoAuditableClaims(EvidenceInspectorError):
    """Raised when generated Markdown contains no auditable prose/list claims."""


class GroundTruthAlignmentError(EvidenceInspectorError):
    """Raised when supplied ground truth does not cover segmented claims exactly."""


class ProviderUnavailable(EvidenceInspectorError):
    """Raised when a model provider cannot return a trustworthy decision."""


class ProviderTimeout(ProviderUnavailable):
    """Raised when a provider exceeds its deadline."""


class RunNotFound(EvidenceInspectorError):
    """Raised when a requested immutable run does not exist."""


class InvalidRunId(EvidenceInspectorError):
    """Raised when a run identifier could escape the artifact root."""


class ArtifactIntegrityError(EvidenceInspectorError):
    """Raised when a stored run or review target is aliased or inconsistent."""


class CompareIncompleteError(EvidenceInspectorError):
    """Raised when a comparison cannot publish a complete report."""
