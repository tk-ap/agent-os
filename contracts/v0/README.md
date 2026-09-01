# Agent OS control-plane contracts — v0alpha1

This directory contains the first machine-readable contracts for the Agent OS control plane defined by `docs/CONTROL_PLANE_CHARTER.md`.

These files are **declarative contracts, not runtime code**. They do not execute tasks, select agents, invoke models, open branches, deploy software, access secrets, or authorize actions.

## Contracts

- `task.schema.yaml` — the governed unit of requested work. Authorization state is explicit; a task cannot authorize itself.
- `workflow.schema.yaml` — task-class stages, governance gates, and evidence expectations. v0alpha1 deliberately contains no command/script fields.
- `harness.schema.yaml` — capabilities and trust boundary of an agentic executor such as Codex, Claude Code, OpenCode, cto.new, or a future local stack. Capability never expands authority.
- `host.schema.yaml` — capabilities, ownership, persistence, and trust boundary of the environment where work may execute. A host is replaceable and does not grant authority.
- `evidence.schema.yaml` — structured record of task state, verification, artifacts, and unresolved gates.

The registry entry is `registry/control-plane-contracts.yaml`.

## v0alpha1 invariants

1. **Task first.** The task is the primary governed object.
2. **Authorization is explicit.** Proposed work is not authorized work.
3. **Capability is not authority.** A harness or host being able to do something does not permit it to do so.
4. **Workflow is declarative.** These schemas describe stages and gates only; they are not executable plans.
5. **Evidence is stateful.** Proposed, attempted, implemented, previewed, verified, deployed, and user-validated states remain distinguishable.
6. **No secrets.** Contracts may reference credential classes or authorization decisions but never contain secret values.
7. **Human gates remain visible.** Merge, production, destructive operations, secrets access, spending, and any other policy-defined privileged action remain explicitly governed.

## Relationship to existing Agent OS objects

These contracts extend rather than replace the current registries:

- `registry/agents.yaml` remains authoritative for durable organizational roles.
- `registry/skills.yaml` remains authoritative for composable capabilities.
- `registry/product-routing.yaml` remains the current source for product roles, constraints, default agents, skills, and environment notes.
- policy documents remain authoritative for autonomy and handoff boundaries.

A later phase may normalize `product` and `policy` into stronger machine-readable contracts, but Phase 1 intentionally avoids duplicating existing truth.

## What this PR does not build

There is no router implementation, execution engine, autonomous loop, scheduler, background process, model invocation, host connection, Agent Control API, production workflow, or secret-management mechanism in v0alpha1.

The next proof point after these contracts are reviewed should be one bounded ASHWOOD reference workflow that can populate these objects while keeping merge and production human-gated.
