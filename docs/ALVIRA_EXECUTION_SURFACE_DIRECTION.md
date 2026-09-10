# ALVIRA Execution Surface Direction

**Status:** product/architecture direction for validation — 2026-09-10

## Decision

Agent OS remains **host-agnostic shared execution infrastructure**, not a standalone public product or customer SKU.

ALVIRA may become the first major commercial surface through which customers access governed agentic execution. The user-facing value is not "buy Agent OS." It is closer to:

> Use what ALVIRA understands about me and the current job to carry approved work through execution and return evidence.

The paid-capability hypothesis is therefore:

**ALVIRA Context + ALVIRA working intent → governed Agent OS execution → verified outcome evidence → ALVIRA Reflect review**

This is a packaging and integration direction, not authorization to change ALVIRA pricing, naming, UI, entitlements, or production behavior.

## Product boundary

### ALVIRA owns

- durable human/project context;
- context capture, maintenance, correction, and reflection;
- selecting and packaging the minimum relevant context for a job;
- the ALVIRA user experience through which a person may request or approve execution;
- any eventual customer-facing packaging, entitlement, and billing experience for an ALVIRA execution capability.

### Agent OS owns

- converting accepted intent into governed executable work;
- organizational agent and skill routing;
- execution-harness and host selection;
- bounded delegation;
- persistence of routing decisions, attempted executions, blockers, retries, evidence, and terminal state;
- verification orchestration and return of execution evidence.

### Authorization/enforcement remains separate

Commercial entitlement is **not** execution authority.

A user may be entitled to an ALVIRA execution feature while a specific action is still denied, approval-gated, or outside delegated authority. Agent Control and/or LEDGATo participate where their defined authorization/enforcement layer is required.

## Independence requirements

Embedding Agent OS beneath ALVIRA must not turn it into ALVIRA-only infrastructure.

Agent OS must remain capable of:

- consuming context from another approved context provider through portable contracts;
- executing work that does not require ALVIRA context at all;
- routing across different models, harnesses, hosts, and workspaces;
- preserving product-local ownership and policy;
- operating without exposing Agent OS terminology to an end user.

ALVIRA should receive the deepest native integration, not exclusive architectural ownership.

## Context contract

Do not reproduce the "read my whole About Me folder before every task" pattern.

For each task, Agent OS should request only the context materially required for that work. ALVIRA should return a bounded context envelope with provenance and use restrictions. Subagents receive only the subset required for their delegated task.

Execution may produce evidence that ALVIRA context is stale, contradicted, ambiguous, missing, or over-broad. That evidence returns as a context signal or outcome event. It must **not** directly mutate durable ALVIRA context.

ALVIRA Reflect decides whether an observation deserves consolidation, a user question, verification, supersession, or no change.

The intended loop is:

**Interview / Capture → Context → Work → Evidence → Reflect → Better Context → Better Work**

## Routing and persistence

This commercial direction does not merge routing with persistence.

- Routing decides the appropriate product, accountable agent, minimum sufficient support, harness, and host.
- Persistence records what routing decided and what execution actually attempted.

A persistent execution record should retain at minimum the work reference, context envelope/reference, selected route, selected harness/host, delegated children where material, authority lineage, execution attempts, blockers/retries, verification result, evidence, and next eligible action.

## Candidate ALVIRA user flow

This is a product hypothesis, not an approved UI specification:

1. ALVIRA understands the person/project and current intent.
2. ALVIRA identifies or asks only for material missing context.
3. The user reviews/accepts the job to be done.
4. ALVIRA emits a bounded work item and least-privilege context envelope.
5. Agent OS resolves ownership, policy, authority, harness, host, and minimum sufficient workforce.
6. Governed execution occurs.
7. Independent verification closes the execution loop where required.
8. Outcome evidence returns to ALVIRA.
9. ALVIRA Reflect evaluates whether anything learned should become durable context.

A future UI could expose this as an ALVIRA paid execution capability without ever exposing Agent OS as a separate product.

## Commercial hypothesis, not pricing decision

There is a plausible reason to monetize execution separately from core context: execution consumes external resources and can deliver direct operational value. That does **not** imply that durable Context or Reflect should be weakened or withheld merely to force an upgrade.

Possible future packaging should be validated around outcomes such as:

- verified work completed;
- time or corrective iterations avoided;
- reduced re-explanation;
- successful use of relevant context without over-sharing;
- execution reliability across harness/provider changes.

Do not finalize names, quotas, prices, plan boundaries, or marketing claims from this document alone.

## Current implementation posture

For now:

- preserve Agent OS as infrastructure;
- preserve existing verifier-independence and authority rules;
- use `contracts/work-item.schema.json`, `contracts/context-envelope.schema.json`, `contracts/context-signal.schema.json`, and `contracts/outcome-event.schema.json` as the portable boundary;
- evolve contracts only when an implementation requires a missing field or object;
- keep ALVIRA context selection least-privilege;
- keep execution observations out of confirmed ALVIRA context until Reflect review;
- do not make Agent OS a public SKU;
- do not change any live ALVIRA site, pricing page, entitlement, or customer-visible feature from this direction document.

## Explicit anti-patterns

Do not:

- sell infrastructure complexity instead of user outcomes;
- make ALVIRA the only context source Agent OS can ever consume;
- make an ALVIRA subscription grant blanket action authority;
- send the entire ALVIRA profile to every task or subagent;
- let execution evidence silently rewrite durable context;
- let Agent OS absorb ALVIRA's Context/Reflect responsibility;
- let ALVIRA absorb workforce routing, harness selection, or execution persistence;
- conflate LEDGATo enforcement with generic workforce routing;
- change production UI or pricing before this direction is separately validated and approved.
