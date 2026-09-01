# Agent OS

Agent OS is the **host-agnostic control plane for a governed agent workforce**.

It is not a public product, a model provider, or merely a collection of agent and skill definitions. Its job is to turn an authorized piece of work into a bounded execution plan: resolve the product and context, select the responsible agent and minimum skills, apply policy, choose an execution harness and host, verify the result, and return evidence for review.

> **North star:** Agent OS is the control plane for the governed execution environment.

## Control-Plane Model

The primary object is the **task**, not the agent.

A task should resolve through the following chain:

**intent → task → product/context → authorization/policy → agent + skills → harness → host → execution → verification → evidence**

This keeps organizational roles stable while allowing models, tools, hosts, and product environments to change independently.

### System boundaries

- **ALVIRA / MeOS** supplies durable context when relevant. Context does not grant authority.
- **ailhat** interprets portfolio/product signals and may propose Opportunity, Risk, Drift, or Work. Intelligence does not grant authority.
- **Agent Control** owns authorization intelligence where integrated: whether a requested action is permitted, gated, or requires human approval.
- **Agent OS / Workforce** resolves and executes authorized work through the appropriate agents, skills, harnesses, hosts, and workflows.
- **Hosts** are the environments where execution can occur: a local workstation, CI, cloud runtime, or an optional sovereign workstation such as Omarchy.
- **Evidence** records what was attempted, where it ran, what changed, how it was verified, and what remains gated.

## Current Repository Structure

- `BOOTSTRAP.md` — universal workspace entry point, task-first load order, and adapter detection.
- `agents/` — stable agent identities and organizational ownership.
- `registry/agents.yaml` — routing, ownership, and capability domains.
- `registry/skills.yaml` — approved/planned skill catalog, trust model, provenance, and discovery sources.
- `registry/product-routing.yaml` — product roles, constraints, default agents, shared workforce capabilities, and skill routing.
- `registry/vendor-acquisition.yaml` — pinned, non-executable candidate acquisition plan.
- `skills/skill-resolver/SKILL.md` — just-in-time skill selection, acquisition, and external discovery policy.
- `skills/owned/` — ecosystem-specific procedures maintained by Agent OS.
- `skills/vendor/` — reviewed third-party skills adapted/pinned for Agent OS runtime.
- `policies/AUTONOMY_POLICY.md` — autonomous action, control-check, and human-escalation rules.
- `policies/HANDOFF_POLICY.md` — ownership transitions and multi-agent council behavior.
- `adapters/` — environment-specific integration contracts.
- `docs/CONTROL_PLANE_CHARTER.md` — target architecture, object model, boundaries, and staged migration plan.

## Target First-Class Objects

The control plane should progressively make these concepts explicit and machine-readable without requiring all of them to be implemented at once:

- `task` — the authorized unit of work and its requested outcome.
- `product` — product-specific repository, context, constraints, and regression boundaries.
- `agent` — durable organizational role responsible for the work.
- `skill` — composable capability loaded only when needed.
- `workflow` — repeatable execution sequence for a task class.
- `policy` — what is allowed, denied, or requires human approval.
- `harness` — the agentic execution provider, such as Codex, Claude Code, OpenCode, or a local model stack.
- `host` — the environment where execution actually occurs.
- `evidence` — verifiable record of execution, checks, artifacts, and unresolved gates.

Agents and skills are therefore registries **inside** Agent OS; they are not the definition of Agent OS itself.

## Shared Workforce Capabilities

Agent OS / Workforce is shared infrastructure, not a separate public product. Cross-product capabilities should therefore be implemented as composable agent profiles, skills, policies, workflows, routing, and host/harness bindings rather than spun out into additional offerings by default.

### Growth / Marketing Engineering

Growth is a shared workforce capability owned operationally by Scout, with strategic, portfolio, economics, experience, authorization, execution, and verification support from the other specialists as needed.

The first operating profile is `agents/scout/MARKET_TRUTH_PROFILE.md`, backed by `skills/owned/market-truth-growth-intelligence/SKILL.md`.

Its decision loop is:

**external signal → evidence → portfolio relevance → interpretation → bounded experiment → governed execution → success signal → learning**

ailhat is the first internal pilot. ALVIRA / MeOS supplies relevant durable context; ailhat consumes and interprets portfolio/market intelligence; Agent Control owns authorization intelligence where integrated; Agent OS / Workforce executes approved work; ASHWOOD may selectively document validated learning as public evidence. Growth itself is not a standalone public offering.

## cto.new Adapter

`adapters/cto-new/` defines how Agent OS operates when a cto.new project has access to both a product repository and this repository.

- `BOOTSTRAP.md` — execution model and load order.
- `WORKSPACE_CONTRACT.yaml` — machine-readable repository/precedence/permission contract.
- `PRODUCT_REPO_INSTRUCTIONS.md` — template to copy or adapt into a product repository as `AGENTS.md` or equivalent.

Default model: the product repository is writable and authoritative for product-specific rules; Agent OS is read-only and authoritative for workforce policy, routing, handoffs, autonomy, and approved skills.

## Design Principles

**Identity is stable. Capability is composable. Context is workspace-specific. Execution is host-agnostic. Authority is explicit. Evidence closes the loop.**

Use the minimum sufficient team and minimum sufficient skill set for each task. Adapters translate this operating model into each execution environment without changing organizational ownership. Models and hosts are replaceable execution dependencies; product truth, governance boundaries, and evidence remain portable.
