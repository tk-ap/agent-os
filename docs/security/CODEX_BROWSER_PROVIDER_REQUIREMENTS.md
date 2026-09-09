# Codex Browser Provider Requirements

Agent OS can use Codex browser execution only through a provider that exposes a
trusted capability handshake and post-run attestation for security verification.
Brave connectivity was verified on 2026-09-05. Connectivity does not establish
these proposed attestation capabilities, which have not been observed.

The current Python adapter is a policy prototype. Its legacy transport-authentication
boolean is supplied by the caller, not established cryptographically, and cannot
authorize execution or verify a receipt. Manifest claims are normalized to
unauthenticated; adapter preparation remains BLOCKED and verification DENY even
when a caller supplies true. Receipt
authentication, request/session binding, freshness, and replay protection remain
local integration work. The task evidence pipeline therefore cannot promote a
caller-supplied runtime status to VERIFIED.

## Activation handshake

The provider must return a manifest equivalent to:

```json
{
  "provider_id": "codex-connected-browser",
  "capabilities": [
    "runtime-attestation",
    "native-sandbox-state",
    "ephemeral-profile-cleanup",
    "credential-isolation",
    "destination-locked-egress"
  ],
  "authenticated_attestation_transport": true
}
```

Agent OS adds `one-time-approval` when a request leaves default containment.
The manifest is capability discovery only; it never grants authorization.
Missing, malformed, or unauthenticated manifests are blocked.

## Required run evidence

After the browser closes, the provider must return the payload defined by
`contracts/browser-runtime-attestation.schema.json`. The adapter assigns trust
from the authenticated transport and ignores any self-declared trust field.
`network_enforcement` must be `kernel` or `destination-locked-proxy`; browser
request routing or an allowlist alone is not sufficient.

## Enablement test

The provider is eligible only when `prepare_codex_browser_execution` returns
`READY` and `verify_codex_browser_execution` returns `VERIFIED` for the same
request/session. Until then the operational state is `BLOCKED`, not “best
effort.”
