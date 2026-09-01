# Agent OS Control-Plane Charter

## Purpose

Agent OS is the **host-agnostic control plane for a governed agent workforce**.

Its purpose is to take authorized intent and determine:

1. what product/workspace the work belongs to;
2. what context is required;
3. what authorization and policy boundaries apply;
4. which organizational agent owns each decision layer;
5. which minimum skills are required;
6. whether repeated work requires a governed routine;
7. which execution harness can perform the work;
8. which host can safely run it;
9. how the result must be verified; and
10. what evidence must return to the human owner or upstream system.

Agent OS is not defined by a particular model, agent harness, workstation, cloud provider, or public product surface.

## North Star

> **Agent OS is the control plane for the governed execution environment.**

The architectural resolution chain is:

**intent → work-item when crossing boundaries → task → product/context → authorization/policy → agent + skills → harness → host → execution → verification → evidence**

The control plane should make this chain progressively more explicit and machine-readable while preserving the ability to operate with simple files and existing tools during migration.

## Work Item vs. Task

Agent OS already has portable interoperability contracts under `contracts/`. They are part of the control plane, but they are not identical to the control-plane execution objects planned under `contracts/v0/`.

### `work-item` — portable intent/handoff

`contracts/work-item.schema.json` carries a proposed or accepted unit of work across a product, workspace, or system boundary. It preserves intent, evidence, constraints, outcome, ownership references, and acceptance criteria without granting execution authority.

Typical sources include an ailhat signal, a human request being handed to another product owner, or a cross-workspace proposal.

### `task` — governed execution instance

A task is the control-plane instance created/resolved when work is being prepared for execution. It binds the relevant product/context, authorization state, organizational ownership, skills, human gates, execution environment requirements, and evidence expectations.

A work item may become or enrich a task. A task does not require a work item when the request originates and remains inside one already-resolved product/workspace boundary.

This distinction prevents two competing models:

**portable proposal/handoff (`work-item`) → governed execution instance (`task`)**

## Existing Contract Layers

The following portable contracts are already established and remain authoritative for cross-boundary interoperability:

- `contracts/work-item.schema.json` — proposed/accepted portable work intent;
- `contracts/capability-manifest.schema.json` — minimum workforce/skill/tool/harness capability statement;
- `contracts/context-envelope.schema.json` — least-privilege ALVIRA-derived context reference and provenance;
- `contracts/authorization-request.schema.json` — governed action request to authorization intelligence where integrated;
- `contracts/outcome-event.schema.json` — bounded execution result and evidence return.

Phase 1 control-plane contracts should add machine-readable `task`, `workflow`, `harness`, `host`, and `evidence` objects. They must reference or compose with the portable contracts instead of redefining their responsibilities.

`registry/product-routing.yaml` remains the canonical product-role source. Neither portable nor control-plane contracts may create a second product-ownership registry.

## Why This Reframe Exists

The repository began by defining stable agents, skills, policies, adapters, product routing, and handoff contracts. Those remain useful, but they are subsystems of a larger execution architecture.

The earlier mental model was approximately:

**agent → skills → work**

The target model is:

**task → product/context → governance → agent + skills → execution environment → verified evidence**

The primary execution object becomes the **task**. Agent identity remains durable, but it is resolved after product, constraints, and authority are understood.

## System Boundaries

### ALVIRA / MeOS — context intelligence

Supplies durable personal, company, product, decision, or workspace context relevant to a task.

It answers: **What should the worker understand?**

Context never grants execution authority. ALVIRA Bridge may transport approved context but does not become a canonical context store or authorization system.

### ailhat — portfolio intelligence

Observes/interprets portfolio and product signals and may propose Opportunity, Risk, Drift, or Work.

It answers: **What may deserve attention?**

A proposal is not authorization. ailhat may create or enrich a portable work item or proposed task without silently executing it.

### Agent Control — authorization intelligence

Owns the decision boundary for governed actions where integrated.

It answers: **May this action happen, under what scope, and what requires human approval?**

Authorization does not decide the technical execution mechanism.

### Agent OS / Workforce — governed execution control plane

Resolves authorized work into product context, organizational ownership, skills, workflow/routine, harness, host, verification, and evidence return.

It answers: **Given this governed work, how should it actually get done?**

Agent OS / Workforce is shared infrastructure, not a separate public product.

### LEDGATo — governance/enforcement scope

Participates where work materially intersects its defined governance or enforcement role. It is not the generic authorization-intelligence owner and must not absorb unrelated product responsibilities.

### Host — execution location

A host is where work physically executes: a user's workstation, Linux host, CI runner, cloud runtime, or optional sovereign workstation profile such as Omarchy.

Agent OS remains host-agnostic. Host capability never expands authority.

### Harness — agentic executor

A harness is the model/tool environment performing agentic execution, such as Codex, Claude Code, OpenCode, cto.new, or a local model stack.

The organizational agent is not the harness. A durable role such as Eugene or Designer may execute through different harnesses over time.

### Evidence — execution truth

Evidence distinguishes at least:

- proposed;
- simulated;
- attempted;
- implemented;
- previewed;
- verified;
- deployed; and
- user-validated.

An agent saying "done" is not sufficient evidence.

## First-Class Control-Plane Object Model

### `task`

The governed execution instance. It should capture outcome, product/workspace, source work-item when present, authorization state, constraints, human gates, ownership, execution requirements, verification, and evidence expectations.

### `product`

Product/workspace truth required to route safely: repository identity, role/category, relevant surfaces, protected regression boundaries, context sources, default agents/skills, environment notes, and human approval requirements.

### `agent`

Durable organizational role/accountability boundary, independent of model provider.

### `skill`

Composable capability loaded only when needed. Skills do not redefine organizational/product ownership or override policy.

### `workflow`

Repeatable task-class sequence such as bug fix, feature delivery, research, preview deployment, claim validation, or bounded growth experiment.

### `routine`

Governed repeated execution for recurring work. Routine definitions compose with tasks and authorization; schedules never grant authority. Core routine policy is defined by `skills/owned/recurring-work/SKILL.md`, while scheduler-specific implementation belongs in adapters or product environments.

### `policy`

Explicit allowed, denied, and approval-required actions. Capability and authority remain separate.

### `harness`

Agentic execution provider/toolchain. Selection may consider task class, tools, cost, privacy, model capability, or environment compatibility, but cannot expand authority.

### `host`

Physical/virtual execution environment and capabilities. Selection may consider filesystem/browser access, local models, CI, persistence, network rules, secret boundaries, and owner control.

### `evidence`

Structured record of what happened, where it ran, artifacts produced, checks performed, unresolved gates, and user validation when applicable.

## Reference Execution Flow

A bounded implementation task should conceptually follow:

1. receive intent or portable work item;
2. normalize/resolve a task envelope;
3. resolve product and workspace truth;
4. load authorization/policy boundaries;
5. select the minimum responsible agent set;
6. resolve minimum skills;
7. define recurring-work controls if repetition is required;
8. choose compatible harness and host;
9. create bounded execution workspace/branch when needed;
10. implement;
11. run relevant verification, including an independent inspector when material;
12. create review artifact such as a PR where applicable;
13. return evidence and unresolved human gates.

Production mutation, destructive changes, secrets access, spending, and other privileged operations remain explicitly gated unless a narrower authority is separately granted.

## Agent and Review Discipline

The control plane uses the minimum sufficient workforce.

Prefer **existing owner + reusable skill** over creating a new persistent agent. New persistent identities require a durable ownership/trust boundary and explicit human approval.

Producer/inspector loops must define acceptance criteria, a maximum cycle count, and escalation. Repeated disagreement without new evidence is a termination condition, not an invitation to cycle indefinitely.

## Host-Agnostic Rule

Agent OS must not require Omarchy, macOS, Vercel, GitHub Actions, cto.new, Codex, Claude, OpenCode, or any other single execution environment to remain conceptually valid.

The same governed task should be portable across compatible hosts/harnesses without changing product truth, organizational ownership, authorization boundaries, required verification, or evidence semantics.

A sovereign Omarchy workstation may become a valuable reference host because it can provide user-owned local execution and tooling. It remains optional and separately scoped.

## Initial Reference Pilot

ASHWOOD is the first end-to-end reference product because it provides a real, comparatively low-risk workflow with observable verification boundaries.

Reference task class:

**frontend bug → branch → implementation → build/test → browser verification → PR → evidence → human merge gate**

The mobile hotspot/capabilities issue is the current pilot. A preview is not equivalent to verification; the pilot must remain unmerged while evidence is `previewed` rather than `verified`.

## Staged Migration

### Phase 0 — Charter and vocabulary

- establish Agent OS as a governed execution control plane;
- establish task-first bootstrap;
- define system boundaries and object relationships;
- retain portable interoperability contracts;
- keep Omarchy optional.

### Phase 1 — Machine-readable control-plane contracts

- define minimal schemas/registry for `task`, `workflow`, `harness`, `host`, and `evidence`;
- explicitly compose with existing portable work/context/authorization/outcome contracts;
- preserve `registry/product-routing.yaml` as canonical product truth;
- preserve current agent/skill registries;
- do not add an executor, daemon, or scheduler merely by defining schemas.

### Phase 2 — One bounded reference workflow

Use ASHWOOD to prove request → resolve → branch → execute → verify → PR → evidence. Merge and production stay human-gated; failed verification is durable evidence.

### Phase 3 — Governance hardening

- scoped credentials;
- explicit approval gates;
- execution/audit records;
- secret boundaries;
- destructive-action policy;
- host/harness capability constraints.

Agent Control may progressively replace static authorization policy with dynamic authorization intelligence where appropriate.

### Phase 4 — Intelligence loop

- ALVIRA / MeOS supplies relevant context;
- ailhat proposes prioritized work;
- Agent Control authorizes where integrated;
- Agent OS executes;
- evidence returns to portfolio/context systems.

The loop remains:

**observe/understand → propose → authorize → execute → verify → learn**

not:

**observe → act without governance**

## Non-Goals

This charter does not authorize or require:

- a new public Agent OS product;
- a custom Linux distribution or Omarchy fork;
- a new foundation model;
- replacing GitHub, Vercel, or existing secret managers;
- a giant autonomous swarm;
- background daemons/schedulers merely because routines are defined;
- autonomous production deployment or merging;
- production access;
- secrets exposure/modification;
- protected-regression-boundary relaxation.

The intellectual property should live primarily in control-plane architecture, routing, governance contracts, context/evidence interfaces, recurring-work safety, and reusable execution workflows—not in reinventing every primitive beneath them.

## Decision Test

A proposed Agent OS feature belongs in the control plane when it materially improves the system's ability to answer one or more of these questions for governed work:

1. What are we trying to accomplish?
2. Is this portable intent or an execution task?
3. What product/workspace truth applies?
4. What context is necessary?
5. What is permitted?
6. Who owns the work?
7. What capabilities are needed?
8. Does repeated work need a governed routine?
9. What harness should execute it?
10. Where should it run?
11. How will success be verified?
12. What evidence must return?

If a feature does not improve this resolution/execution loop, it should not be added merely because it involves agents.
