# Browser Execution Security Acceptance

## Purpose

Browser execution is a privileged capability. This acceptance gate converts the Chromium `SIGTRAP` incident observed on the Omarchy host on 2026-09-04 into a reusable fail-closed control-plane test.

The incident proved that direct Chromium execution inside the Codex restricted shell could not create Crashpad's credential socket because `setsockopt(..., SO_PASSCRED, ...)` was denied. A later retry escaped the restricted sandbox under a broad persistent `chromium --headless` approval and also supplied `--no-sandbox`. The screenshots completed, but that recovery path weakened both containment layers.

## Policy decision

Agent OS must deny browser execution when any of these conditions is true:

- Chromium's native sandbox is disabled, including use of `--no-sandbox` or component-specific sandbox-disabling switches;
- the profile is persistent rather than task-ephemeral;
- ambient credentials are available to the browser;
- the destination origin is outside the explicit network scope;
- direct shell execution is attempted inside the known-incompatible restricted sandbox;
- execution outside the default sandbox lacks one-time human approval; or
- approval would persist beyond the individual action.

A browser request may proceed only when the full capability envelope is satisfied. A compatible host or harness does not widen task authorization.

## Automated acceptance evidence

`runtime/browser_security.py` now separates request admission from proof. Preflight produces `READY` or `DENY`; post-run verification produces `VERIFIED` only when a trusted provider or host attests the effective controls. It performs no browser launch and stores no credential values. Its tests cover:

1. a declared controlled, destination-scoped, secretless request reaching `READY` preflight;
2. rejection of `--no-sandbox`;
3. rejection of direct restricted-shell execution;
4. one-time approval for execution outside the default sandbox;
5. rejection of persistent approvals;
6. origin-scoped network policy and rejection of credentials embedded in destination URLs;
7. rejection of ambient credentials and persistent profiles; and
8. non-secret decision evidence;
9. fail-closed behavior when runtime attestation is absent or self-reported;
10. verified native sandbox, task-ephemeral profile cleanup, and credential isolation;
11. rejection of observed origins outside the authorized scope; and
12. rejection of application-level provider policy as a substitute for kernel or destination-locked proxy egress enforcement.

`adapters/codex/browser.py` is the Codex-specific fail-closed bridge. It checks that the provider advertises every required attestation capability before execution, requires an authenticated evidence transport, rejects unknown or malformed fields, and assigns trust at the transport boundary rather than accepting a trust label inside the payload. The portable payload shape is defined by `contracts/browser-runtime-attestation.schema.json`.

`runtime/browser_evidence.py` attaches connected-browser route and interaction checks to the normal Agent OS `Task` execution and verification records. A connected transport is recorded as `PREVIEWED`; only a runtime-attested run can become `VERIFIED`.

Run:

```bash
python -m unittest tests.test_browser_security
```

The implementation evidence for this incident is recorded in `docs/security/evidence/browser-execution-2026-09-04.json`.

## Current host evidence

Verified on the affected Omarchy/Codex host:

- the restricted shell denies Crashpad's `SO_PASSCRED` setup and fails closed;
- the broad persistent `chromium --headless` and `agent-browser` command approvals were removed;
- workspace instructions prohibit `--no-sandbox`, silent containment escape, and broad persistent browser approvals; and
- the user's global Chromium flags do not disable Chromium's native sandbox.

The crash is not currently an Omarchy-upstream report candidate. The evidence points to a one-off direct Chromium invocation from the Codex restricted shell and a subsequent unsafe `--no-sandbox` workaround; no stock Omarchy launcher, configuration, or package behavior is implicated. Reclassify only if the same failure reproduces through an unmodified Omarchy browser launch.

## Evidence limits and remaining gate

This implementation verifies the policy decision layer and defines the machine-readable runtime evidence contract. It does **not** manufacture evidence that the connected browser provider does not expose. The Brave provider is now connected and exposes a browser/profile/tab surface, but it still exposes no fields attesting ephemeral storage, credential stripping, effective egress enforcement, or Chromium native-sandbox state.

Until the Codex adapter can collect those runtime facts from the browser provider, `READY` means only that the request is admissible. It is not production-proven LEDGATo/khrystal enforcement. A run reaches `VERIFIED` only with trusted runtime attestations for:

- native sandbox state;
- profile lifetime and cleanup;
- credential/environment isolation;
- effective destination/network scope; and
- one-time approval identity and expiration when execution leaves default containment.

For the security bar established here, UI request routing alone is not egress containment. The attestation must identify kernel enforcement or a destination-locked proxy that the browser cannot bypass. Missing, self-reported, or weaker evidence is denied.

LEDGATo may consume the resulting evidence because this is materially a governance/enforcement boundary. Agent Control remains the owner of authorization intelligence where integrated; Agent OS remains the execution control plane.
