# Feature request: verifiable browser execution receipts

Submitted: https://github.com/openai/codex/issues/43001

## What variant of Codex are you using?

Desktop app on Linux, with the connected Brave browser extension.

## What feature would you like to see?

Verifiable browser execution receipts and optional isolated browser sessions,
as detailed below.

## Problem and evidence

We are building Agent OS, a host-independent execution control plane that records
authorization and evidence for bounded tasks. On an Omarchy Linux workstation,
the connected Brave extension and native messaging host work: we used them to
inspect public website routes. The observed interface identifies the browser,
profile, and tabs. We have not found an authenticated receipt describing the
effective sandbox, storage, credential, and network boundaries of an individual
run. This is an observation about our available interface, not a claim that every
Codex backend lacks these controls.

Our connected session uses an existing Personal profile. It cannot be presumed
ephemeral or free of cookies and credentials. A connected extension and successful
page inspection do not establish those properties.

## Requested capability

Please provide a documented capability-discovery API and an optional isolated
browser-session mode with authenticated execution receipts. If an equivalent API
already exists, please identify its supported integration path and trust model.

Before navigation, a session should report the controls actually established:

- Native browser sandbox state and how it was measured.
- Task-specific storage/profile isolation and credential exposure policy,
  including cookies, password stores, mounted files, and environment variables.
- Effective destination restrictions and enforcement mechanism, covering
  redirects, DNS, WebSockets, QUIC, service workers, and background traffic.
- The authorized action scope and approval identity/expiry where applicable.

After execution, a receipt should record completion, violations, teardown, and
profile cleanup. Cleanup cannot be attested before it happens. Unsupported or
unmeasurable controls should be explicitly unknown rather than inferred.

Bind evidence to the provider, session, exact request digest, a verifier-issued
nonce, issue/expiry times, and policy version. Document authenticated transport
or signature validation, trust anchors, rotation/revocation, and replay defenses.
Exported receipts need independently verifiable provenance if downstream systems
cannot rely on the live authenticated connection. Signing alone does not prove
containment; the issuer and measurement mechanism must be described.

## Acceptance scenario

1. Request an isolated session limited to a test origin.
2. Inspect the pre-execution controls before allowing navigation.
3. Render the approved page and exercise harmless UI interactions.
4. Attempt controlled off-scope requests against test endpoints and observe
   enforcement across the supported protocols.
5. Close the session and validate cleanup evidence.
6. Reject tampered, stale, replayed, wrong-session, and wrong-request receipts.
7. Report unsupported controls explicitly; never equate a successful UI test
   with a successful security evaluation.

## Integration readiness and limits

Agent OS has draft payload contracts, policy checks, and browser task evidence.
These are prototypes, not a finished cryptographic verifier or an enforcement
hook in Codex. Local integration still needs authenticated receipt validation,
request/session binding, replay protection, and enforcement at dispatch time.
There is no live LEDGATo/khrystal evidence delivery in this implementation yet.

No private URLs, profile identifiers, account details, tokens, or core dumps are
needed to discuss this request. Functional browser checks can remain useful while
security verification is separately unavailable.
