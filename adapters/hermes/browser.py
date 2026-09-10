"""Fail-closed bridge between Hermes browser facts and Agent OS policy.

Hermes is a local operator harness. Its browser capability has two surfaces:

- ``connected-browser`` -- a Hermes-managed copy of the operator's real
  browser, running on the workstation. This surface could eventually be
  attested by a *host-verified* transport (the host observes native sandbox
  state, ephemeral profile cleanup, and kernel/destination-locked network
  enforcement), because Hermes runs on the host itself.
- ``cloud-browser`` -- a remote browser backend. This surface is
  provider-attested at best and is subject to the same fail-closed rule as any
  remote harness provider.

The rule is identical to the Codex adapter: capability discovery and caller
flags are untrusted data, never proof of transport identity. Until a
host-verified attestation transport is actually implemented, Hermes cannot
authorize browser execution on the strength of its own report. A self-reported
attestation is ``collector_trust="self-reported"`` and fails closed in
``verify_browser_execution``.

When Hermes delegates browser work to a sub-harness (e.g. Codex), that
delegated path is governed by the sub-harness's own adapter, not this one.
Delegation creates no new authority and never relaxes this boundary.
"""

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
HOST_VERIFICATION_UNAVAILABLE = (
    "host-verified attestation transport is not established; "
    "harness self-reporting is insufficient"
)
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
class HermesBrowserSurface:
    surface_kind: str
    capabilities: tuple[str, ...]
    host_verified_transport: bool


def surface_from_manifest(manifest: dict[str, Any] | None) -> HermesBrowserSurface:
    """Parse a Hermes browser surface manifest; absence or malformed data is unavailable."""

    if not isinstance(manifest, dict):
        return HermesBrowserSurface("", (), False)
    surface_kind = manifest.get("surface_kind")
    capabilities = manifest.get("capabilities")
    host_verified = manifest.get("host_verified_transport")
    if (
        not isinstance(surface_kind, str)
        or not isinstance(capabilities, list)
        or any(not isinstance(item, str) for item in capabilities)
        or type(host_verified) is not bool
    ):
        return HermesBrowserSurface("", (), False)
    # Capability discovery is untrusted data, never proof of transport identity.
    return HermesBrowserSurface(surface_kind, tuple(sorted(set(capabilities))), False)


def prepare_hermes_browser_execution(
    request: BrowserExecutionRequest,
    surface: HermesBrowserSurface,
) -> dict:
    """Admit only requests a host-verified transport can later prove it enforced."""

    result = evaluate_browser_execution(request)
    reasons = list(result["reasons"])
    required = set(BASE_ATTESTATION_CAPABILITIES)
    if request.approval_scope == "one-time":
        required.add(ONE_TIME_APPROVAL_CAPABILITY)
    missing = sorted(required.difference(surface.capabilities))

    if not surface.surface_kind:
        reasons.append("Hermes browser surface identity is unavailable")
    if missing:
        reasons.append("Hermes browser surface lacks required attestations: " + ", ".join(missing))
    if not surface.host_verified_transport:
        reasons.append("Hermes browser attestation transport is not host-verified")
    # No host-verified transport integration exists. Even a directly constructed
    # surface with a True flag must not authorize execution.
    reasons.append(HOST_VERIFICATION_UNAVAILABLE)

    return {
        **result,
        "decision": "BLOCKED" if reasons else "READY",
        "reasons": reasons,
        "adapter": "hermes-browser",
        "surface": surface.surface_kind or None,
        "required_capabilities": sorted(required),
        "missing_capabilities": missing,
    }


def verify_hermes_browser_execution(
    request: BrowserExecutionRequest,
    payload: dict[str, Any] | None,
    *,
    host_verified_transport: bool,
) -> dict:
    """Translate host evidence without trusting harness-supplied trust labels."""

    if not host_verified_transport:
        result = verify_browser_execution(request, None)
        result["reasons"].append("Hermes browser attestation transport is not host-verified")
        result["adapter"] = "hermes-browser"
        return result
    try:
        attestation = _parse_attestation(payload)
    except (TypeError, ValueError) as exc:
        result = verify_browser_execution(request, None)
        result["reasons"].append(f"invalid Hermes browser attestation: {exc}")
        result["adapter"] = "hermes-browser"
        return result

    # Parsing and policy consistency are not host verification. Keep diagnostic
    # evidence, but never promote a harness assertion into a verified receipt.
    result = verify_browser_execution(request, attestation)
    result["decision"] = "DENY"
    result["reasons"].append(HOST_VERIFICATION_UNAVAILABLE)
    result["evidence"]["trusted_source"] = False
    result["adapter"] = "hermes-browser"
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
