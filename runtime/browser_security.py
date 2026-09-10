"""Fail-closed policy for privileged browser execution requests."""

from dataclasses import asdict, dataclass, field
from datetime import datetime
from urllib.parse import urlsplit


POLICY_VERSION = "browser-execution/v2"
ALLOWED_PATHS = {"connected-browser", "shell"}
ALLOWED_APPROVAL_SCOPES = {"none", "one-time", "persistent"}
TRUSTED_ATTESTATION_SOURCES = {"host-verified", "provider-attested"}
ACCEPTABLE_NETWORK_ENFORCEMENT = {"kernel", "destination-locked-proxy"}
SANDBOX_WEAKENING_ARGUMENTS = {
    "--disable-gpu-sandbox",
    "--disable-namespace-sandbox",
    "--disable-seccomp-filter-sandbox",
    "--disable-setuid-sandbox",
    "--no-sandbox",
}


@dataclass(frozen=True)
class BrowserExecutionRequest:
    execution_path: str
    destination: str
    network_scope: tuple[str, ...]
    ephemeral_profile: bool
    ambient_credentials: bool
    native_sandbox: bool
    outside_default_sandbox: bool = False
    approval_scope: str = "none"
    arguments: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class BrowserRuntimeAttestation:
    """Post-run facts supplied by a trusted host or browser provider."""

    provider: str
    session_id: str
    collected_at: str
    collector_trust: str
    native_sandbox_active: bool
    profile_ephemeral: bool
    profile_cleanup_verified: bool
    ambient_credential_keys: tuple[str, ...]
    observed_network_origins: tuple[str, ...]
    network_enforcement: str
    approval_scope: str
    approval_id: str | None
    approval_expires_at: str | None
    evidence_refs: tuple[str, ...]


def _origin(value: str) -> str | None:
    try:
        parsed = urlsplit(value)
    except ValueError:
        return None
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
    ):
        return None
    try:
        port = parsed.port
    except ValueError:
        return None
    default_port = 80 if parsed.scheme == "http" else 443
    authority = parsed.hostname if port in {None, default_port} else f"{parsed.hostname}:{port}"
    return f"{parsed.scheme}://{authority}"


def _timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def evaluate_browser_execution(request: BrowserExecutionRequest) -> dict:
    """Return an auditable READY or DENY preflight decision without executing."""

    reasons: list[str] = []
    destination_origin = _origin(request.destination)
    allowed_origins = {_origin(item) for item in request.network_scope}
    malformed_network_scope = None in allowed_origins
    allowed_origins.discard(None)
    weakening_arguments = sorted(
        argument
        for argument in request.arguments
        if argument.split("=", 1)[0] in SANDBOX_WEAKENING_ARGUMENTS
    )

    if request.execution_path not in ALLOWED_PATHS:
        reasons.append("unknown execution path")
    if request.approval_scope not in ALLOWED_APPROVAL_SCOPES:
        reasons.append("unknown approval scope")
    if not destination_origin:
        reasons.append("destination must be an explicit HTTP(S) URL")
    elif destination_origin not in allowed_origins:
        reasons.append("destination origin is outside the declared network scope")
    if malformed_network_scope:
        reasons.append("network scope contains an invalid origin")
    if not request.ephemeral_profile:
        reasons.append("browser profile is not ephemeral")
    if request.ambient_credentials:
        reasons.append("ambient credentials would be exposed to the browser")
    if not request.native_sandbox or weakening_arguments:
        reasons.append("Chromium native sandbox must remain enabled")
    if request.approval_scope == "persistent":
        reasons.append("persistent browser execution approvals are prohibited")
    if request.outside_default_sandbox and request.approval_scope != "one-time":
        reasons.append("execution outside the default sandbox requires one-time approval")
    if request.execution_path == "shell" and not request.outside_default_sandbox:
        reasons.append("direct shell browser execution is incompatible with the restricted sandbox")

    decision = "DENY" if reasons else "READY"
    return {
        "policy_version": POLICY_VERSION,
        "decision": decision,
        "reasons": reasons,
        "request": asdict(request),
        "evidence": {
            "destination_origin": destination_origin,
            "allowed_origins": sorted(allowed_origins),
            "native_sandbox": request.native_sandbox and not weakening_arguments,
            "sandbox_weakening_arguments": weakening_arguments,
            "ephemeral_profile": request.ephemeral_profile,
            "ambient_credentials": request.ambient_credentials,
            "approval_scope": request.approval_scope,
        },
    }


def verify_browser_execution(
    request: BrowserExecutionRequest,
    attestation: BrowserRuntimeAttestation | None,
) -> dict:
    """Verify post-run enforcement; missing or self-reported evidence fails closed."""

    preflight = evaluate_browser_execution(request)
    reasons = list(preflight["reasons"])

    if attestation is None:
        reasons.append("trusted runtime attestation is required")
        return {
            "policy_version": POLICY_VERSION,
            "decision": "DENY",
            "reasons": reasons,
            "request": preflight["request"],
            "attestation": None,
        }

    observed_origins = {_origin(item) for item in attestation.observed_network_origins}
    malformed_observations = None in observed_origins
    observed_origins.discard(None)
    allowed_origins = {_origin(item) for item in request.network_scope}
    allowed_origins.discard(None)

    if attestation.collector_trust not in TRUSTED_ATTESTATION_SOURCES:
        reasons.append("runtime evidence is not from a trusted attestation source")
    collected_at = _timestamp(attestation.collected_at)
    if not attestation.provider or not attestation.session_id or collected_at is None:
        reasons.append("runtime attestation identity is incomplete")
    if not attestation.native_sandbox_active:
        reasons.append("runtime did not attest an active Chromium native sandbox")
    if not attestation.profile_ephemeral:
        reasons.append("runtime profile was not task-ephemeral")
    if not attestation.profile_cleanup_verified:
        reasons.append("runtime profile cleanup was not verified")
    if attestation.ambient_credential_keys:
        reasons.append("runtime exposed ambient credential keys")
    if malformed_observations or not observed_origins.issubset(allowed_origins):
        reasons.append("observed network origin is outside the declared network scope")
    if attestation.network_enforcement not in ACCEPTABLE_NETWORK_ENFORCEMENT:
        reasons.append("network scope lacks kernel or destination-locked proxy enforcement")
    if attestation.approval_scope != request.approval_scope:
        reasons.append("runtime approval scope does not match the authorized request")
    if request.approval_scope == "one-time" and (
        not attestation.approval_id or not attestation.approval_expires_at
    ):
        reasons.append("one-time approval identity or expiration is missing")
    if request.approval_scope == "one-time" and attestation.approval_expires_at:
        expires_at = _timestamp(attestation.approval_expires_at)
        if expires_at is None or (collected_at is not None and expires_at <= collected_at):
            reasons.append("one-time approval expiration is invalid or expired")
    if request.approval_scope == "none" and (
        attestation.approval_id is not None or attestation.approval_expires_at is not None
    ):
        reasons.append("runtime supplied approval metadata for an unapproved request")
    if not attestation.evidence_refs:
        reasons.append("runtime attestation has no evidence references")

    return {
        "policy_version": POLICY_VERSION,
        "decision": "DENY" if reasons else "VERIFIED",
        "reasons": reasons,
        "request": preflight["request"],
        "attestation": asdict(attestation),
        "evidence": {
            "allowed_origins": sorted(allowed_origins),
            "observed_origins": sorted(observed_origins),
            "trusted_source": attestation.collector_trust
            in TRUSTED_ATTESTATION_SOURCES,
            "effective_network_enforcement": attestation.network_enforcement,
        },
    }
