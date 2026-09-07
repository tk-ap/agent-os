# Context Release, Agent-Instance Pinning, and Decommissioning

> Status: proposal/build spec for Agent OS onboarding and Hermes reconciliation.
>
> Purpose: close the final three guardrail gaps before scaling multi-harness autonomous work: selective context release, reproducible agent-instance execution identity, and active-state garbage collection/decommissioning.

## Core invariants

1. **Shared organizational awareness does not imply shared raw context.** A harness or agent receives only the minimum context required and permitted for the task.
2. **A durable agent role is not enough to reproduce an execution.** Each material run records the effective role, identity version, skills, harness, model/provider, policy version, product-context version, and relevant tool/runtime versions.
3. **Persistent systems must retire stale operating state.** Expired, superseded, abandoned, or duplicate artifacts must be classified and removed from active operating context rather than accumulating indefinitely.

---

## 1. Context release policy

### Goal

Allow TK to move between ChatGPT, Hermes, Codex, Claude Code, other harnesses, and Agent OS tasks without making every surface omniscient.

### Default

Context is least-privilege and task-scoped. Knowing that a fact or conversation exists does not grant access to its contents.

### Release decision

Before transmitting context to a harness/agent instance, resolve:

- requested task and product;
- minimum context needed;
- source/provenance;
- sensitivity/data class;
- permitted recipient/harness;
- permitted use;
- retention/freshness bounds when applicable;
- whether a summary/reference is sufficient instead of raw content.

### Preferred release order

1. structured fact/reference;
2. bounded summary;
3. selected excerpt;
4. raw source only when materially required and permitted.

### Example

Agent OS may expose:

`TK has an active human_exploration workspace touching ALVIRA onboarding.`

without exposing the private conversation that produced the idea.

### Failure behavior

- Missing permission or unclear sensitivity => withhold/reduce context, never silently widen.
- Context unavailable => task may continue only if the task contract permits reduced-context execution; otherwise block/escalate.
- Context freshness unknown => mark `UNKNOWN/STALE`, do not present as current truth.

### Relationship to ALVIRA

ALVIRA/MeOS may supply durable context when relevant. Context never grants authority. Agent OS remains responsible for minimum-necessary release to each execution context/harness.

---

## 2. Agent-instance/version pinning

### Goal

Make execution evidence reproducible enough to answer: "What actually performed this work?"

### Minimum execution identity

For material runs, record:

```yaml
agent_instance:
  instance_id:
  role:
  identity_version:
  skills:
  skill_versions:
  harness:
  harness_version:
  model_provider:
  model:
  policy_version:
  product_context_version:
  repository_ref:
  host:
  toolchain_versions:
  started_at:
```

Use stable hashes/refs where practical rather than free-form labels.

### Rules

- Role identity is durable; instances are task/session scoped.
- Two instances of Eugene may run concurrently and remain distinct.
- A retry that materially changes model/harness/skills/policy creates a new instance/evidence identity even if it remains the same task.
- Workforce Health comparisons should group only comparable runs or explicitly account for changed execution identity.
- Human consultation instances remain distinct from governed execution instances and do not inherit mutation authority.

### Why this matters

Without pinning, statements such as "Eugene performed better last week" are not operationally meaningful if the underlying model, harness, policy, skills, or context changed.

---

## 3. Decommissioning and garbage collection

### Goal

Prevent stale state from becoming active context, routing noise, cost, or architectural drift.

### Lifecycle states

```text
ACTIVE
SUPERSEDED
ARCHIVED
EXPIRED
DECOMMISSIONED
PURGE_ELIGIBLE
```

`PURGE_ELIGIBLE` does not imply immediate deletion. Retention/evidence rules still apply.

### Candidate surfaces

- expired objective leases;
- stale workspace leases/worktrees;
- abandoned branches;
- obsolete grants/tokens/revocation records beyond required retention;
- superseded proposal docs;
- duplicate registries/contracts;
- old task checkpoints and retry state;
- unused skills;
- dormant routines;
- stale candidate work items;
- obsolete evidence summaries whose canonical evidence remains preserved;
- superseded agent-instance metadata;
- open PRs whose responsibility has already been implemented elsewhere.

### Classification before deletion

W Dog/Bill may flag candidates, but destructive cleanup must respect authority and retention policy.

For each candidate record:

```yaml
cleanup_candidate:
  object_id:
  object_type:
  current_state:
  proposed_state:
  reason:
  superseded_by:
  evidence_retention_required:
  destructive_action_required:
  approval_required:
```

### Active-context rule

Objects in `SUPERSEDED`, `ARCHIVED`, `EXPIRED`, or `DECOMMISSIONED` must not be loaded as current operating truth unless the task explicitly asks for historical evidence.

### Recurring hygiene

A bounded control-plane hygiene routine should eventually inspect:

- orphaned actionable docs not reachable from canonical load paths;
- duplicate responsibility/registry claims;
- stale open PRs/branches;
- expired leases/grants;
- unbound/dormant routines;
- abandoned worktrees;
- stale candidate work;
- stale evidence without freshness metadata.

This routine should flag and propose cleanup first. Automatic destructive cleanup should remain narrowly scoped and separately authorized.

---

## Hermes reconciliation/build order

For each section classify existing support as:

`IMPLEMENTED / PARTIAL / DOCUMENTED_ONLY / MISSING / DUPLICATE_OF_EXISTING`

Then implement the smallest canonical changes.

### Priority A — context release

1. Reuse `contracts/context-envelope.schema.json` where possible.
2. Add harness/recipient release constraints only if genuinely missing.
3. Enforce minimum-context release at execution-context/harness handoff.
4. Preserve provenance and reduced-context/withheld-context evidence.

### Priority B — instance pinning

1. Identify existing task/evidence/harness metadata that can carry these fields.
2. Avoid creating a second task identity system.
3. Persist effective execution identity for each material attempt.
4. Make Workforce Health consume comparable instance metadata.

### Priority C — decommissioning

1. Add lifecycle/state semantics without deleting historical evidence.
2. Mark superseded proposals/PRs and stale operational objects.
3. Add a non-destructive hygiene audit before any automatic cleanup.
4. Keep cleanup proposals out of executable backlog until promoted/authorized.

---

## Acceptance tests

1. **Minimum context:** a harness receives only task-required context while remaining aware that additional private context exists.
2. **Withheld context:** unavailable/not-permitted context is explicitly marked and does not silently appear in prompts/logs.
3. **Instance reproducibility:** a completed task records role + effective identity/skills/harness/model/policy/context refs.
4. **Concurrent same-role instances:** two Eugene instances can coexist with distinct instance IDs and authority/workspace contexts.
5. **Changed execution stack:** retrying on another harness/model creates distinguishable evidence.
6. **Superseded state exclusion:** archived/superseded objects are not loaded as current operating truth.
7. **Hygiene audit:** stale branch/PR/workspace/lease/doc candidates are flagged without destructive mutation.
8. **Retention safety:** cleanup never deletes evidence required by policy/history/audit.
9. **Canonical path:** relevant onboarding/bootstrap flows automatically load these rules; no manual doc-discovery step is required.

## Stop condition

After these controls are implemented or reconciled into canonical runtime/contracts/policies, do not add additional architectural layers without a demonstrated failure mode from real Agent OS operation.

The next priority becomes measured execution against product and revenue objectives, not further conceptual expansion.
