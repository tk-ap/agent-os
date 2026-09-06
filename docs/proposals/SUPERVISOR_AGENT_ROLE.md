# Proposal: Supervisor Role for Agent OS

> Status: **PROPOSAL — requires Claude review / modification / approval before adoption**
>
> Working internal metaphor: **“Mr. Milchick”** from *Severance*.
>
> The metaphor is not intended as public naming and should not constrain implementation.

## Proposal in one sentence

Agent OS should add an explicit **Supervisor** role responsible for runtime supervision of consequential agent work: checking authority, pausing or denying execution, escalating to a human when required, resuming approved work, revoking authority, and verifying that completed actions stayed inside the approved boundary.

## Why this role is being proposed

Agent OS already has orchestration primitives: tasks, workflows, harnesses, hosts, durable roles, evidence contracts, authorization requests, and product integrations.

That does not automatically answer a different operational question:

> **While work is executing, who or what is responsible for determining whether a consequential action is still authorized and whether reality matches the approved intent?**

The distinction is:

- **Orchestration** decides what work should happen and where it should run.
- **Supervision** decides whether consequential work may continue, must stop, needs escalation, or must be verified before being considered complete.

This proposal exists because those functions should not be allowed to blur together accidentally.

## Proposed responsibility boundary

The Supervisor would own the following responsibilities at the Agent OS layer:

1. **Authority check**
   - Confirm the acting agent/workload identity.
   - Confirm the task and delegated authority attached to the work.
   - Determine whether the requested action is inside that authority.

2. **Runtime decision**
   - **ALLOW** — continue when the action is inside declared authority.
   - **DENY** — block when the action is outside authority or violates policy.
   - **APPROVE** — pause and request a human or higher-order approval when policy requires it.

3. **Escalation and approval lifecycle**
   - Surface what action is blocked, why, what authority is missing, and what approving it would permit.
   - Resume the original work after a valid approval without requiring the task to be manually reconstructed.

4. **Revocation**
   - Stop or prevent future execution when delegated authority is revoked or expires.
   - Respect parent/child grant relationships and revocation propagation.

5. **Post-action verification**
   - Compare actual outcome/evidence against the approved action and expected result.
   - Refuse to treat execution success alone as proof that the intended outcome was achieved.

6. **Evidence production**
   - Preserve the request, applicable policy, decision, approval if any, execution result, verification result, and relevant provenance.

7. **Workforce visibility for consequential state**
   - Make it possible to answer which agents are running, paused, blocked, awaiting approval, revoked, failed verification, or complete.
   - This is supervisory state, not a mandate to build generic surveillance/observability into Agent OS.

## Proposed architecture

```text
                    HUMAN
                      │
                intent / policy
                      │
                      ▼
                AGENT OS
          tasks / workflows / routing
                      │
                      ▼
               SUPERVISOR ROLE
        ┌─────────────┼─────────────┐
        │             │             │
     authorize       deny       escalate
        │                           │
        │                       human approval
        │                           │
        └─────────────┬─────────────┘
                      │
                 resume / revoke
                      │
                      ▼
                  EXECUTION
                      │
                      ▼
                  EVIDENCE
                      │
                      ▼
                  VERIFY
```

## Critical implementation guardrail

The strongest version of this proposal is **not** “add another LLM agent that watches the other agents.”

Where a supervisory decision can be deterministic, it should be deterministic.

Examples:

- no production-delete permission → **DENY**;
- delegated grant expired → **DENY**;
- policy marks external publish as human-approved → **APPROVE**;
- action fits active task grant → **ALLOW**.

AI may be useful for interpretation, explanation, evidence synthesis, ambiguous-intent analysis, or risk classification, but it should not replace enforceable policy for decisions that can be expressed as explicit rules.

This matters because an unconstrained LLM “supervisor” would itself become another autonomous actor whose judgment and authority require supervision.

## Relationship to Ledgato / khrystal

This proposal should **not duplicate Ledgato/khrystal**.

The current product boundary is:

- **Agent OS** — execution infrastructure and workforce control plane.
- **Ledgato / khrystal** — independent Agent Assurance: evaluate, test, record, and where integrated enforce consequential authority boundaries.
- **Supervisor role** — the Agent OS responsibility that consumes assurance decisions and controls execution state accordingly.

A likely interaction is:

```text
Agent requests consequential action
        ↓
Agent OS Supervisor
        ↓
Ledgato/khrystal assurance check
        ↓
ALLOW / DENY / APPROVE + evidence
        ↓
Agent OS enforces execution state
        ↓
execution
        ↓
verification + evidence
```

Ledgato/khrystal should remain independent assurance rather than becoming a second runtime. Agent OS should remain the runtime/control plane rather than reimplementing the assurance engine.

## Relationship to existing Agent OS contracts

The proposal should reuse and extend existing contracts rather than create parallel concepts where possible, including:

- `authorization-request.schema.json`
- `capability-manifest.schema.json`
- `continuity-grant.schema.json`
- `outcome-event.schema.json`
- task/work-item and evidence contracts

Claude should specifically review whether the Supervisor role is already implicit in these contracts and runtime paths and therefore only needs to be named/documented, or whether a missing explicit state machine / interface genuinely exists.

## Is this actually a new agent?

This is intentionally unresolved for review.

### Option A — durable Supervisor agent

Register a new durable Agent OS role with a human-readable identity and responsibility set.

**Pros**
- clear ownership;
- easy routing/escalation target;
- intuitive mental model for workforce operations;
- can synthesize ambiguous evidence and explain decisions.

**Cons**
- risks implying the LLM is the source of enforcement authority;
- another agent introduces failure modes, latency, cost, and possible self-supervision loops;
- may duplicate deterministic control-plane/runtime responsibilities.

### Option B — Supervisor as control-plane function, not an agent

Treat supervision as an architectural/runtime responsibility with no durable agent identity.

**Pros**
- cleaner security boundary;
- deterministic enforcement remains primary;
- avoids another autonomous actor;
- maps naturally to policy/state-machine code.

**Cons**
- less legible to humans operating a workforce;
- ambiguous cases still need an intelligent interpretation/escalation surface;
- responsibility may become scattered across runtime modules.

### Option C — hybrid (current recommendation)

Make **supervision a control-plane capability first**, with an optional durable Supervisor agent/persona as the human-facing interpretation and escalation interface.

The agent does not grant itself authority and does not replace policy enforcement. It explains, synthesizes, escalates, and coordinates the supervisory lifecycle around deterministic controls.

This preserves the useful organizational role without making an LLM the security boundary.

## Why add a named role at all?

The case for a role is not that the *Severance* analogy sounds good.

The case is that a multi-agent workforce has a recurring organizational responsibility that otherwise has no obvious owner:

> **Who is accountable for the live state of delegated machine work when execution becomes consequential?**

A named role can make that ownership explicit across:

- active tasks;
- blocked actions;
- approvals;
- expired/revoked authority;
- execution failures;
- verification failures;
- handoffs between humans and agents.

If existing Agent OS architecture already assigns this responsibility cleanly, adding the role would be unnecessary abstraction and should be rejected.

## Risks / reasons to reject this proposal

Claude should reject or substantially modify this proposal if any of the following are true:

1. **The role duplicates an existing Agent OS durable role.**
2. **The runtime already has a clear supervision state machine and owner**, making a named role cosmetic.
3. **Adding the role causes Agent OS to duplicate Ledgato/khrystal assurance logic.**
4. **The role encourages LLM judgment where deterministic enforcement should be authoritative.**
5. **A new agent adds coordination cost without improving safety, accountability, or operator clarity.**
6. **The role violates the existing principle that harnesses execute for durable roles but are not themselves agents.**
7. **The same value can be achieved with a smaller contract/state-model change.**

## Minimum proof before treating this as a major Agent OS pillar

Do not elevate the Supervisor concept based on naming alone.

Require an end-to-end proof of three behaviors:

### 1. Real blocked action

An agent attempts an action outside its authority and cannot execute it through the governed path.

### 2. Human approval + continuation

The blocked operation can obtain narrowly scoped temporary authority and the original work can resume safely.

### 3. Post-action verification

The system independently verifies that the actual outcome remained within the approved boundary and records evidence.

If Agent OS + Ledgato already satisfy all three, the review should document where those guarantees currently live and determine whether the proposed role adds operational clarity rather than duplicate implementation.

## Proposed role language if approved

**Supervisor**

> Maintains the live supervisory state of delegated agent work. Coordinates authority checks, enforcement decisions, approval/escalation, revocation, resume, and post-action verification. The Supervisor does not supersede deterministic policy enforcement and does not grant itself authority.

Possible internal shorthand: `supervisor`.

Do **not** use `milchick` as the canonical role ID unless deliberately chosen later; “Mr. Milchick” is only the design metaphor that exposed the missing responsibility.

## Review request for Claude

Please review this proposal in truth mode and return one of:

- **APPROVE** — the role/capability fills a real architectural gap;
- **MODIFY** — preserve the need but change role boundaries, implementation, naming, or agent-vs-control-plane placement;
- **REJECT** — existing Agent OS architecture already assigns the responsibility adequately or the proposal adds needless abstraction.

Review specifically:

1. Is runtime supervision actually missing, or merely unnamed?
2. Should `Supervisor` be a durable agent, a deterministic control-plane function, or a hybrid?
3. Which existing roles/contracts/runtime modules already overlap?
4. What is the cleanest boundary with Ledgato/khrystal?
5. What is the minimum implementation needed to prove the role is useful?
6. What failure modes would introducing this role create?
7. If approved, where should the canonical contract/state machine live?

No production behavior, role registry, or canonical architecture should change solely because this proposal exists.
