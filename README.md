# Agent OS

Agent OS is the **host-agnostic control plane for a governed agent workforce**.

It is shared execution infrastructure, not a separate public product, a model provider, or merely a collection of agent and skill definitions. Its job is to turn authorized intent into bounded execution: resolve product/context and governance, select the responsible organizational agent and minimum skills, choose a compatible harness and host, verify the result, and return evidence.

> **North star:** Agent OS is the control plane for the governed execution environment.

## Control-Plane Model

The primary execution object is the **task**, not the agent.

A task resolves through:

**intent → work-item when crossing boundaries → task → product/context → authorization/policy → agent + skills → harness → host → execution → verification → evidence**

A portable `work-item` and a control-plane `task` are deliberately distinct:

- **work-item** — portable proposal/accepted handoff that carries intent across a product or workspace boundary without granting execution authority;
- **task** — governed execution instance after product, context, policy, authority, ownership, and human gates are resolved.

This keeps organizational roles and product truth stable while models, tools, hosts, and execution environments can change independently.

### System boundaries

- **ALVIRA / MeOS** supplies durable context when relevant. Context does not grant authority.
- **ailhat** interprets portfolio/product signals and may propose Opportunity, Risk, Drift, or Work. Intelligence does not grant authority.
- **Agent Control** owns authorization intelligence where integrated: whether a requested action is permitted, gated, or requires human approval.
- **Agent OS / Workforce** resolves and executes authorized work through the appropriate agents, skills, workflows, harnesses, hosts, and policies.
- **LEDGATo** participates only when governance/enforcement is materially relevant; it is not the generic authorization owner.
- **Hosts** are environments where execution can occur: local workstation, CI, cloud runtime, or an optional sovereign workstation profile such as Omarchy.
- **Evidence** records what was attempted, where it ran, what changed, how it was verified, and what remains gated.

## Repository Structure

- `BOOTSTRAP.md` — universal workspace entry point, task-first load order, product-boundary check, and adapter detection.
- `HOST_PROFILES.md` — optional host-profile rules and the Omarchy workstation hypothesis; host profiles remain subordinate to the control-plane charter.
- `agents/` — stable agent identities and organizational ownership.
- `registry/agents.yaml` — routing, ownership, and capability domains.
- `registry/skills.yaml` — owned/approved/planned skill catalog, trust model, provenance, reviewed reference material, and discovery sources.
- `registry/product-routing.yaml` — canonical product roles, constraints, default agents, shared workforce capabilities, and skill routing.
- `registry/vendor-acquisition.yaml` — pinned/non-executable candidate acquisition plan for skill sources.
- `registry/vendor-evaluation.yaml` — governed decisions about external products and services that are not skills.
- `contracts/` — portable work-item, capability, context, authorization, outcome, and vendor-evaluation schemas for cross-product/workspace handoffs.
- `skills/skill-resolver/SKILL.md` — just-in-time skill selection, acquisition, and external discovery policy.
- `skills/owned/` — ecosystem-specific procedures maintained by Agent OS, including task envelope, recurring work, identity design, authorization, provenance, and verification.
- `skills/vendor/` — reviewed third-party skills adapted/pinned for Agent OS runtime.
- `policies/AUTONOMY_POLICY.md` — autonomous action, control-check, and human-escalation rules.
- `policies/HANDOFF_POLICY.md` — agent/cross-product ownership transitions, bounded producer/inspector loops, and recurring-work handoffs.
- `policies/CROSS_MARKET_POLICY.md` — value-first rules for adjacent-product recommendations.
- `adapters/` — environment-specific and product-repository integration contracts.
- `docs/CONTROL_PLANE_CHARTER.md` — target architecture, object model, boundaries, and staged migration plan.

## Portable Contracts

`registry/product-routing.yaml` is the single canonical product-boundary source. Local product manifests may add repository-specific detail but must not create a competing product-role truth.

Portable contracts make cross-product work explicit without coupling Agent OS to one execution harness:

- `contracts/work-item.schema.json` — proposed or accepted cross-boundary unit of work with owner, evidence, outcome, constraints, and acceptance criteria;
- `contracts/capability-manifest.schema.json` — minimum workforce, skills, tools, and harness candidates required for material work;
- `contracts/context-envelope.schema.json` — least-privilege ALVIRA-derived context reference with provenance and permitted use;
- `contracts/authorization-request.schema.json` — governed action request routed to Agent Control as authorization-intelligence owner where integrated;
- `contracts/outcome-event.schema.json` — bounded execution result, verification, cost/evidence, and measured outcome.

These interoperability contracts complement the control-plane task/workflow/harness/host/evidence model. They do not replace task authorization or create a second product registry.

## Target First-Class Control-Plane Objects

The control plane progressively makes these concepts explicit and machine-readable without requiring them all to be implemented at once:

- `task` — governed execution instance and requested outcome;
- `product` — product-specific repository/context/constraints/regression boundaries;
- `agent` — durable organizational role responsible for a decision layer;
- `skill` — composable capability loaded only when needed;
- `workflow` — repeatable execution sequence for a task class;
- `policy` — allowed, denied, and approval-required actions;
- `harness` — agentic execution provider/toolchain;
- `host` — physical/virtual execution environment;
- `evidence` — verifiable execution/check/artifact/gate record.

Agents and skills are registries **inside** Agent OS; they are not the definition of Agent OS itself.

## Host Profiles

Host profiles describe optional workstation/runtime-environment conventions without becoming control-plane dependencies. `HOST_PROFILES.md` defines the host-versus-target boundary and the first candidate profile: **Omarchy as an optional Linux workstation host**.

A host profile may improve local tooling, sessions, browser/editor/terminal ergonomics, and human supervision. It may not grant production authority, store secrets in Agent OS, weaken provider protections, or redefine product/workforce ownership. Host-specific implementation belongs in an adapter/profile layer and must remain reversible.

## Product Repository Adapter

`adapters/product-repo/` contains lightweight templates for repositories that participate in Agent OS routing. They supplement the canonical product registry rather than replacing it.

## Shared Workforce Capabilities

Agent OS / Workforce is shared infrastructure, not a standalone public product. Cross-product capabilities should be composable agent profiles, skills, policies, workflows, routing, and host/harness bindings rather than spun out into additional offerings by default.

### Growth / Marketing Engineering

Growth is a shared workforce capability owned operationally by Scout, with strategic, portfolio, economics, experience, authorization, execution, and verification support from specialists as needed.

The first operating profile is `agents/scout/MARKET_TRUTH_PROFILE.md`, backed by `skills/owned/market-truth-growth-intelligence/SKILL.md` and `skills/owned/opportunity-triage/SKILL.md`.

Its decision loop is:

**external signal → evidence → portfolio relevance → interpretation → bounded experiment → governed execution → success signal → learning**

ailhat is the first internal pilot. ALVIRA / MeOS supplies relevant durable context; ailhat consumes and interprets portfolio/market intelligence; Agent Control owns authorization intelligence where integrated; Agent OS / Workforce executes approved work; ASHWOOD may selectively document validated learning as public evidence.

## cto.new Adapter

`adapters/cto-new/` defines how Agent OS operates when a cto.new project has access to both a product repository and this repository. The product repository remains authoritative for product-specific rules; Agent OS is authoritative for shared workforce policy, routing, handoffs, governance contracts, and approved skills.

## Design Principles

**Task is primary. Identity is stable. Capability is composable. Product boundaries are explicit. Context is least-privilege. Authority is explicit. Execution is host-agnostic. Evidence closes the loop.**

Use the minimum sufficient team and minimum sufficient skill set. Prefer an existing owner plus a reusable skill over unnecessary persistent-agent proliferation. Repeated work requires bounded routine controls; producer/inspector loops require termination and escalation. Adapters and host profiles translate the operating model into execution environments without changing organizational/product ownership or widening authority.
