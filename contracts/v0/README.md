# Agent OS control-plane contracts — v0alpha1

This directory contains the first machine-readable execution-control contracts for the Agent OS control plane defined by `docs/CONTROL_PLANE_CHARTER.md`.

These files are **declarative contracts, not runtime code**. They do not execute tasks, select agents, invoke models, open branches, deploy software, access secrets, authorize actions, or schedule recurring work.

## Contract layers

Agent OS has two complementary contract layers:

1. **Portable interoperability contracts** in `contracts/*.schema.json` carry intent/context/authorization/outcome across product or workspace boundaries.
2. **Control-plane execution contracts** in `contracts/v0/` describe a governed execution instance and the environment/evidence required to perform it.

The distinction is deliberate:

**portable `work-item` → governed `task`**

A `work-item` can propose or hand off work without granting execution authority. A `task` is the control-plane execution instance after product, policy, authority, ownership, and human gates are resolved. A task may reference a source work item, but not every local task needs one.

## v0 Contracts

- `task.schema.yaml` — governed execution instance. Authorization state is explicit; a task cannot authorize itself and may reference a portable work item.
- `workflow.schema.yaml` — task-class stages, governance gates, and evidence expectations. v0alpha1 deliberately contains no command/script fields.
- `harness.schema.yaml` — capabilities/trust boundary of an agentic executor such as Codex, Claude Code, OpenCode, cto.new, or a future local stack. Capability never expands authority.
- `host.schema.yaml` — capabilities, ownership, persistence, and trust boundary of the environment where work may execute. Host profiles such as Omarchy remain optional and do not grant authority.
- `evidence.schema.yaml` — structured record of task state, verification, artifacts, and unresolved gates.

The registry entry is `registry/control-plane-contracts.yaml`.

## Portable contracts composed by v0

Where applicable, v0 tasks/workflows should reference rather than duplicate:

- `contracts/work-item.schema.json` — portable cross-boundary intent/handoff;
- `contracts/capability-manifest.schema.json` — minimum workforce/tool/harness requirements;
- `contracts/context-envelope.schema.json` — ALVIRA-derived context/provenance and permitted use;
- `contracts/authorization-request.schema.json` — governed authorization request where Agent Control is integrated;
- `contracts/outcome-event.schema.json` — portable return of bounded execution outcome/evidence.

`registry/product-routing.yaml` remains the canonical product/shared-capability truth. Neither layer creates another product-role registry.

## v0alpha1 invariants

1. **Task first for execution.** A task is the primary governed execution object; a portable work item may precede it.
2. **Authorization is explicit.** Proposed work is not authorized work.
3. **Capability is not authority.** A harness or host being able to do something does not permit it to do so.
4. **Workflow is declarative.** These schemas describe stages and gates only; they are not executable plans.
5. **Recurring work is separately governed.** A workflow or schedule reference does not replace `skills/owned/recurring-work/SKILL.md` or authorize repetition.
6. **Evidence is stateful.** Proposed, attempted, implemented, previewed, verified, deployed, and user-validated states remain distinguishable.
7. **No secrets.** Contracts may reference credential classes or authorization decisions but never contain secret values.
8. **Human gates remain visible.** Merge, production, destructive operations, secrets access, spending, and other policy-defined privileged actions remain governed.
9. **Agents remain organizational identities.** Harness/provider identity is not agent identity; new persistent agents remain human-gated.

## Relationship to existing Agent OS objects

These contracts extend rather than replace current sources of truth:

- `registry/agents.yaml` remains authoritative for durable organizational roles;
- `registry/skills.yaml` remains authoritative for composable capabilities;
- `registry/product-routing.yaml` remains authoritative for product roles, constraints, shared workforce capabilities, default routing, and environment notes;
- `policies/AUTONOMY_POLICY.md` and `policies/HANDOFF_POLICY.md` remain authoritative for governance and handoff boundaries;
- `HOST_PROFILES.md` describes optional host profiles beneath the `host` object;
- `skills/owned/recurring-work/SKILL.md` defines safety requirements for repeated execution.

Phase 1 intentionally avoids duplicating existing truth.

## What v0alpha1 does not build

There is no router implementation, execution engine, autonomous loop, scheduler, background process, model invocation, host connection, Agent Control API integration, production workflow, or secret-management mechanism in these schemas.

The reference proof point is the bounded ASHWOOD pilot. Its evidence must remain distinct from the contracts themselves, and `previewed` must not be promoted to `verified` without human/user verification.
