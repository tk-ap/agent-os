"""Fail-closed bridge between Codex browser facts and Agent OS policy."""

from dataclasses import dataclass
from typing import Any

from runtime.browser_security import (
    BrowserExecutionRequest,
    BrowserRuntimeAttestation,
    evaluate_browser_execution,
    verify_browser_execution,
)


BASE_ATTESTATION_CAPABILITIES = frozenset(
    {
        "runtime-attestation",
        "native-sandbox-state",
        "ephemeral-profile-cleanup",
        "credential-isolation",
        "destination-locked-egress",
    }
)
ONE_TIME_APPROVAL_CAPABILITY = "one-time-approval"
AUTHENTICATION_UNAVAILABLE = "provider receipt authentication is not implemented; caller trust flags are insufficient"
ATTESTATION_FIELDS = frozenset(
    {
        "provider",
        "session_id",
        "collected_at",
        "native_sandbox_active",
        "profile_ephemeral",
        "profile_cleanup_verified",
        "ambient_credential_keys",
        "observed_network_origins",
        "network_enforcement",
        "approval_scope",
        "approval_id",
        "approval_expires_at",
        "evidence_refs",
    }
)


@dataclass(frozen=True)
class CodexBrowserSurface:
    provider_id: str
    capabilities: tuple[str, ...]
    authenticated_attestation_transport: bool


def surface_from_manifest(manifest: dict[str, Any] | None) -> CodexBrowserSurface:
    """Parse a provider capability manifest; absence or malformed data is unavailable."""

    if not isinstance(manifest, dict):
        return CodexBrowserSurface("", (), False)
    provider_id = manifest.get("provider_id")
    capabilities = manifest.get("capabilities")
    authenticated = manifest.get("authenticated_attestation_transport")
    if (
        not isinstance(provider_id, str)
        or not isinstance(capabilities, list)
        or any(not isinstance(item, str) for item in capabilities)
        or type(authenticated) is not bool
    ):
        return CodexBrowserSurface("", (), False)
    # Capability discovery is untrusted data, never proof of transport identity.
    return CodexBrowserSurface(provider_id, tuple(sorted(set(capabilities))), False)


def prepare_codex_browser_execution(
    request: BrowserExecutionRequest,
    surface: CodexBrowserSurface,
) -> dict:
    """Admit only requests a Codex provider can later prove it enforced."""

    result = evaluate_browser_execution(request)
    reasons = list(result["reasons"])
    required = set(BASE_ATTESTATION_CAPABILITIES)
    if request.approval_scope == "one-time":
        required.add(ONE_TIME_APPROVAL_CAPABILITY)
    missing = sorted(required.difference(surface.capabilities))

    if not surface.provider_id:
        reasons.append("Codex browser provider identity is unavailable")
    if missing:
        reasons.append("Codex browser provider lacks required attestations: " + ", ".join(missing))
    if not surface.authenticated_attestation_transport:
        reasons.append("Codex browser attestation transport is not authenticated")
    # No authenticated provider integration exists. Even a directly constructed
    # surface with a True flag must not authorize execution.
    reasons.append(AUTHENTICATION_UNAVAILABLE)

    return {
        **result,
        "decision": "BLOCKED" if reasons else "READY",
        "reasons": reasons,
        "adapter": "codex-browser",
        "provider": surface.provider_id or None,
        "required_capabilities": sorted(required),
        "missing_capabilities": missing,
    }


def verify_codex_browser_execution(
    request: BrowserExecutionRequest,
    payload: dict[str, Any] | None,
    *,
    authenticated_transport: bool,
) -> dict:
    """Translate provider evidence without trusting provider-supplied trust labels."""

    if not authenticated_transport:
        result = verify_browser_execution(request, None)
        result["reasons"].append("Codex browser attestation transport is not authenticated")
        result["adapter"] = "codex-browser"
        return result
    try:
        attestation = _parse_attestation(payload)
    except (TypeError, ValueError) as exc:
        result = verify_browser_execution(request, None)
        result["reasons"].append(f"invalid Codex browser attestation: {exc}")
        result["adapter"] = "codex-browser"
        return result

    # Parsing and policy consistency are not authentication. Keep diagnostic
    # evidence, but never promote a caller assertion into a verified receipt.
    result = verify_browser_execution(request, attestation)
    result["decision"] = "DENY"
    result["reasons"].append(AUTHENTICATION_UNAVAILABLE)
    result["evidence"]["trusted_source"] = False
    result["adapter"] = "codex-browser"
    return result


def _parse_attestation(payload: dict[str, Any] | None) -> BrowserRuntimeAttestation:
    if not isinstance(payload, dict):
        raise TypeError("payload must be an object")
    unknown = sorted(set(payload).difference(ATTESTATION_FIELDS))
    missing = sorted(ATTESTATION_FIELDS.difference(payload))
    if unknown:
        raise ValueError("unexpected fields: " + ", ".join(unknown))
    if missing:
        raise ValueError("missing fields: " + ", ".join(missing))

    string_fields = ("provider", "session_id", "collected_at", "network_enforcement", "approval_scope")
    boolean_fields = ("native_sandbox_active", "profile_ephemeral", "profile_cleanup_verified")
    sequence_fields = ("ambient_credential_keys", "observed_network_origins", "evidence_refs")
    for field in string_fields:
        if not isinstance(payload[field], str):
            raise TypeError(f"{field} must be a string")
    for field in boolean_fields:
        if type(payload[field]) is not bool:
            raise TypeError(f"{field} must be a boolean")
    for field in sequence_fields:
        value = payload[field]
        if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
            raise TypeError(f"{field} must be an array of strings")
    for field in ("approval_id", "approval_expires_at"):
        if payload[field] is not None and not isinstance(payload[field], str):
            raise TypeError(f"{field} must be a string or null")

    return BrowserRuntimeAttestation(
        provider=payload["provider"],
        session_id=payload["session_id"],
        collected_at=payload["collected_at"],
        collector_trust="self-reported",
        native_sandbox_active=payload["native_sandbox_active"],
        profile_ephemeral=payload["profile_ephemeral"],
        profile_cleanup_verified=payload["profile_cleanup_verified"],
        ambient_credential_keys=tuple(payload["ambient_credential_keys"]),
        observed_network_origins=tuple(payload["observed_network_origins"]),
        network_enforcement=payload["network_enforcement"],
        approval_scope=payload["approval_scope"],
        approval_id=payload["approval_id"],
        approval_expires_at=payload["approval_expires_at"],
        evidence_refs=tuple(payload["evidence_refs"]),
    )
