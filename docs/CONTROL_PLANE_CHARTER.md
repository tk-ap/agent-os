# Agent OS Control-Plane Charter

## Purpose

Agent OS is the **host-agnostic control plane for a governed agent workforce**.

Its purpose is to take an authorized unit of work and determine:

1. what product/workspace the task belongs to;
2. what context is required;
3. what authorization and policy boundaries apply;
4. which organizational agent owns the work;
5. which minimum skills are required;
6. which execution harness can perform the work;
7. which host can safely run it;
8. how the result must be verified; and
9. what evidence must return to the human owner or upstream system.

Agent OS is therefore not defined by a particular model, agent harness, workstation, cloud provider, or public product surface.

## North Star

> **Agent OS is the control plane for the governed execution environment.**

The architectural resolution chain is:

**intent → task → product/context → authorization/policy → agent + skills → harness → host → execution → verification → evidence**

The control plane should make this chain progressively more explicit and machine-readable while preserving the ability to operate with simple files and existing tools during migration.

## Why This Reframe Exists

The repository began by defining stable agents, skills, policies, adapters, and product routing. Those remain useful, but they are subsystems of a larger execution architecture.

The previous mental model was approximately:

**agent → skills → work**

The target model is:

**task → product/context → governance → agent + skills → execution environment → verified evidence**

The primary object becomes the **task**. Agent identity remains durable, but it is resolved after the task's product, constraints, and authority are understood.

## System Boundaries

### ALVIRA / MeOS — context intelligence

ALVIRA / MeOS may supply durable personal, company, product, decision, or workspace context relevant to a task.

It answers: **What should the worker understand?**

Context never grants execution authority.

### ailhat — portfolio intelligence

ailhat may observe portfolio/product signals and propose Opportunity, Risk, Drift, or Work.

It answers: **What may deserve attention?**

A proposal is not authorization. ailhat should be able to create or enrich a proposed task envelope without silently executing it.

### Agent Control — authorization intelligence

Agent Control owns the decision boundary for governed actions where integrated.

It answers: **May this action happen, under what scope, and what requires human approval?**

Agent Control does not need to decide how the task is technically executed.

### Agent OS / Workforce — execution orchestration

Agent OS resolves the authorized task into the appropriate product context, organizational ownership, skills, workflow, harness, host, verification steps, and evidence return.

It answers: **Given this authorized task, how should the work actually get done?**

### Host — execution location

A host is the environment where work can physically execute.

Examples include:

- a user's existing macOS workstation;
- a Linux workstation;
- GitHub Actions or another CI runner;
- a cloud VM/runtime;
- a future sovereign workstation profile such as Omarchy.

Agent OS must remain host-agnostic. A host is a replaceable execution dependency, not the control plane itself.

### Harness — agentic executor

A harness is the model/tool environment that performs agentic execution.

Examples may include Codex, Claude Code, OpenCode, cto.new, or a local model stack.

The organizational agent is not the harness. A durable role such as Eugene or Designer may execute through different harnesses over time.

### Evidence — execution truth

Evidence closes the loop. It should record enough information to distinguish:

- proposed;
- simulated;
- attempted;
- implemented;
- previewed;
- verified;
- deployed; and
- user-validated states.

An agent saying "done" is not sufficient evidence.

## First-Class Object Model

The target control plane should make the following objects explicit.

### `task`

The governed unit of requested work.

Minimum conceptual fields:

```yaml
task:
  id: ashwood-mobile-hotspot
  type: bug-fix
  outcome: restore usable mobile hotspot section without blocking static links
  product: ashwood
  constraints: []
  human_gates: [merge, production]
```

### `product`

Product/workspace truth required to route safely.

May include:

- repository identity;
- product role/category;
- relevant surfaces;
- protected regression boundaries;
- product-specific context sources;
- default skills/agents;
- environment/deployment notes; and
- human approval requirements.

### `agent`

Durable organizational role and accountability boundary.

An agent should not be equated with a specific model provider.

### `skill`

Composable capability loaded only when needed.

Skills do not redefine organizational ownership or override policy.

### `workflow`

Repeatable task-class sequence such as:

- fix bug;
- ship feature;
- research question;
- deploy preview;
- validate product claim;
- conduct bounded growth experiment.

### `policy`

Explicit allowed, denied, and approval-required actions.

Policy should remain separate from capability. Being technically able to perform an action does not mean the action is authorized.

### `harness`

Agentic execution provider/toolchain.

Selection may depend on task class, available tools, cost, privacy, model capability, or environment compatibility, but cannot expand authority.

### `host`

Physical/virtual execution environment and its capabilities.

Selection may depend on filesystem access, browser access, local model availability, CI capability, secrets boundary, persistence, network rules, or owner control.

### `evidence`

Structured record of what happened and how it was verified.

Example:

```yaml
evidence:
  task: ashwood-mobile-hotspot
  product: ashwood
  host: local-workstation
  harness: codex
  changes: []
  verification:
    build: passed
    mobile-browser: passed
    desktop-regression: passed
  artifacts:
    branch: fix/mobile-hotspot
    pull_request: pending
  gates:
    merge: requires-human
    production: requires-human
```

## Reference Execution Flow

A bug-fix task should conceptually follow:

1. receive intent;
2. normalize a task envelope;
3. resolve product and workspace truth;
4. load authorization/policy boundaries;
5. select responsible agent(s);
6. resolve minimum skills;
7. choose compatible harness and host;
8. create bounded execution workspace/branch;
9. implement;
10. run relevant verification;
11. create review artifact such as a PR where applicable;
12. return evidence and unresolved human gates.

Production mutation, destructive changes, secrets access, spending, and other privileged operations remain explicitly gated unless a later policy grants a narrower authority.

## Host-Agnostic Rule

Agent OS must not require Omarchy, macOS, Vercel, GitHub Actions, cto.new, Codex, Claude, OpenCode, or any other single execution environment in order to remain conceptually valid.

The same governed task should be portable across compatible hosts/harnesses without changing:

- product truth;
- organizational ownership;
- authorization boundaries;
- required verification; or
- evidence semantics.

A sovereign Omarchy workstation may become a valuable reference host because it can provide user-owned local execution, storage, networking, and local-model capability. It remains optional and separately scoped.

## Initial Reference Pilot

ASHWOOD should be the first end-to-end reference product because it provides a real, low-risk workflow with observable verification boundaries.

Reference task class:

**frontend bug → branch → implementation → build/test → browser verification → PR → evidence → human merge gate**

A suitable first pilot is the known mobile hotspot/capabilities rendering issue.

Success for Agent OS v0.1 is not autonomous production deployment. Success is that the control plane can reliably answer:

- Which product?
- Which repository/workspace?
- Which context?
- Which organizational agent?
- Which skills?
- Which policy/gates?
- Which harness?
- Which host?
- Which verification?
- Which evidence must return?

## Staged Migration

### Phase 0 — Charter and vocabulary

Documentation-only.

- reframe Agent OS as a control plane;
- establish task-first bootstrap;
- define system boundaries and target object model;
- keep Omarchy as an optional host proposal.

### Phase 1 — Machine-readable contracts

Separate implementation PR(s).

- define minimal schemas/registries for task, workflow, harness, host, and evidence;
- extend product routing without duplicating product-specific truth unnecessarily;
- preserve current agent/skill registries.

### Phase 2 — One executable workflow

Use ASHWOOD as the reference pilot.

- request → route → branch → execute → verify → PR → evidence;
- keep merge and production gated;
- measure whether routing and evidence are actually useful before expanding abstraction.

### Phase 3 — Governance hardening

- scoped credentials;
- explicit approval gates;
- execution/audit records;
- secret boundaries;
- destructive-action policy;
- host/harness capability constraints.

Agent Control can progressively replace static authorization policy with dynamic authorization intelligence where appropriate.

### Phase 4 — Intelligence loop

Connect optional upstream intelligence:

- ALVIRA / MeOS supplies relevant context;
- ailhat proposes prioritized work from portfolio intelligence;
- Agent Control authorizes;
- Agent OS executes;
- evidence returns to portfolio/context systems.

The loop remains:

**observe/understand → propose → authorize → execute → verify → learn**

not:

**observe → act without governance**

## Non-Goals

This charter does not authorize or require:

- building a new public Agent OS product;
- building a custom Linux distribution;
- forking Omarchy;
- creating a new foundation model;
- replacing GitHub, Vercel, or existing secret managers;
- implementing a giant autonomous swarm;
- merging documentation or implementation automatically;
- granting production access;
- exposing or modifying secrets;
- relaxing protected product regression boundaries.

The intellectual property should live primarily in the control-plane architecture, routing, governance contracts, context/evidence interfaces, and reusable execution workflows—not in reinventing every primitive below them.

## Decision Test

A proposed Agent OS feature belongs in the control plane when it materially improves the system's ability to answer one or more of these questions for an authorized task:

1. What are we trying to accomplish?
2. What product/workspace truth applies?
3. What context is necessary?
4. What is permitted?
5. Who owns the work?
6. What capabilities are needed?
7. What harness should execute it?
8. Where should it run?
9. How will success be verified?
10. What evidence must return?

If a feature does not improve this resolution/execution loop, it should not be added to Agent OS merely because it involves agents.
