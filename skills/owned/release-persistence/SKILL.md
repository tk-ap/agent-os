---
name: release-persistence
description: Persist approved release work across temporary capacity, CI, source-control, provider, or deployment blockers; safely recheck and resume the same authorized action until live verification or another explicit terminal state. Use for approved-but-not-live work, rate-limit recovery, deployment retry, ambiguous release reconciliation, and release continuity.
---

# Release Persistence

Keep already-approved release work from disappearing between implementation and verified production state.

This skill defines **safe persistence and resume semantics**. It does not grant deployment authority, create credentials, choose product priority, or replace independent verification.

## Ownership

- **Polly** is primary owner of release persistence and terminal-state continuity.
- **Milchik** detects/surfaces meaningful approved work that is stalled or falsely treated as complete and receives progress/terminal evidence.
- **Bill** owns execution sequencing and recurring-work design where scheduling is required.
- **Eugene** owns implementation and provider/adapter engineering.
- **W Dog** owns independent live-state verification.
- **Rook** reviews material replay, permission, irreversibility, and ambiguous-mutation risk.

## Trigger Conditions

Use this skill when all are true:

1. a work item already exists;
2. the relevant next action is approved or has an explicit scoped authorization path;
3. the intended outcome includes release, publish, push, promotion, deployment, or another externally visible state;
4. the work is not yet terminal because of a transient blocker, pending availability, ambiguous external result, or missing live verification.

Do not use it to invent new work or convert a proposal into approval.

## Required Recovery Record

Create/update a record conforming to `contracts/release-recovery.schema.json` containing:

- recovery id + originating work/task id;
- product, repository, environment, and target live URL when applicable;
- expected artifact/commit/deployment identity;
- exact action scope and authority reference;
- authorization expiry/revocation facts;
- current recovery state;
- blocker classification and evidence;
- retry policy, mutation attempts, availability checks, and next eligible check;
- reconciliation/idempotency information;
- verification method and verifier;
- notification destination;
- terminal evidence.

Persist this record outside model conversation state.

## State Machine

Permitted non-terminal states:

- `ready`
- `checking`
- `waiting_availability`
- `executing`
- `reconciling`
- `verifying`

Terminal states:

- `live_verified`
- `superseded`
- `cancelled`
- `human_required`

A generic `done` state is intentionally absent.

## Blocker Classification

Classify blockers before deciding to retry:

### Transient / retryable

Examples: documented rate limit/cooldown, temporary provider outage, recoverable CI infrastructure failure, temporary deployment quota, unavailable eligible harness.

Action: persist blocker evidence + next eligible check; return later.

### Ambiguous external result

Examples: connection timeout after push/deploy request, provider accepted request but response was lost, CI trigger returned uncertain state.

Action: enter `reconciling`; perform read-only reconciliation. **Never repeat the mutation until the external state is known.**

### Non-transient / human or owner required

Examples: invalid credentials, changed target, authorization expiry/revocation, merge conflict requiring new implementation judgment, policy denial, persistent configuration defect, retry ceiling.

Action: `human_required` or handoff to the owning domain. Persistence is not permission to redesign the fix.

## Resume Gate

Before every mutation retry/resume, verify:

- the original work item still exists and is not cancelled/superseded;
- authorization remains valid and unrevoked;
- action kind, target, artifact/commit, scope, and material risk/cost remain inside the grant;
- no equivalent external mutation already succeeded;
- the blocker condition has cleared or retry time has arrived;
- mutation-attempt ceiling remains available.

If any check fails, do not mutate.

## Retry Policy

- Prefer provider-declared reset/retry times.
- Otherwise use bounded exponential backoff with jitter appropriate to the provider and urgency.
- Availability checks and mutation attempts are different counters.
- Pure read-only/no-op checks should be cheap and should not consume model tokens when deterministic code can perform them.
- Every mutation requires an idempotency or reconciliation strategy when the provider supports one.
- Set a retry ceiling and an elapsed-time ceiling before autonomous operation.
- Repeated identical failure after the threshold is evidence of a non-transient blocker; stop looping.

## Scheduler / Clock

Compose with `skills/owned/recurring-work/SKILL.md` when future rechecks are required.

The clock should execute a deterministic due-check first:

1. Is any recovery record due?
2. Is it still authorized and non-terminal?
3. Can a read-only availability/reconciliation probe determine the next state?
4. Only invoke an agent/harness when judgment or an authorized mutation is actually needed.

Scheduler-specific binding belongs in the host adapter. A scheduler never supplies authority.

## Verification

A successful mutation moves to `verifying`, not completion.

Compose with `skills/owned/end-to-end-verification/SKILL.md`. The verifier must prove the intended state at the canonical live/user-facing target and identify the artifact/commit/deployment being observed.

Only verified evidence may set `live_verified`.

## Notification

Send progress to the operational owner (normally Milchik) on meaningful transitions only:

- newly blocked;
- next-check time materially changes;
- availability recovered and resume began;
- human decision required;
- live verification succeeded;
- cancellation/supersession.

Do not emit a message for every no-op poll.

## Guardrails

- Priority is not authority.
- Approval of code changes does not automatically authorize push/deploy unless that scope was included.
- Persistence never widens authorization.
- A provider outage is not permission to switch targets/providers if that changes scope.
- Do not mark work complete when evidence explicitly says it is not deployed/live.
- Do not treat preview as production.
- Do not retry ambiguous mutations blindly.
- Do not let an LLM become the polling loop when deterministic state/availability checks suffice.
- Do not retain secrets in recovery records or evidence.

## Output

Return:

- recovery record/state;
- blocker classification;
- authority/resume eligibility;
- next eligible check or terminal state;
- reconciliation result when needed;
- independent verification status;
- notification summary;
- exact next permitted action.
