# Agent OS

Portable multi-agent operating system for an autonomous business workforce: Router, Steward, Zoie, Scout, Designer, Ledger, Eugene, Rook, Bill, and W Dog.

## Structure

- `BOOTSTRAP.md` — universal workspace entry point, product-boundary check, and adapter detection.
- `agents/` — stable agent identities and organizational ownership.
- `registry/agents.yaml` — routing, ownership, and capability domains.
- `registry/skills.yaml` — approved/planned skill catalog, trust model, provenance, and discovery sources.
- `registry/product-routing.yaml` — canonical product roles, constraints, default agents, shared workforce capabilities, and skill routing.
- `registry/vendor-acquisition.yaml` — pinned, non-executable candidate acquisition plan.
- `contracts/` — portable work-item, capability, context, authorization, and outcome schemas for cross-product or cross-workspace handoffs.
- `skills/skill-resolver/SKILL.md` — just-in-time skill selection, acquisition, and external discovery policy.
- `skills/owned/` — ecosystem-specific procedures maintained by Agent OS.
- `skills/vendor/` — reviewed third-party skills adapted/pinned for Agent OS runtime.
- `policies/AUTONOMY_POLICY.md` — autonomous action, control-check, and human-escalation rules.
- `policies/HANDOFF_POLICY.md` — agent and cross-product ownership transitions.
- `policies/CROSS_MARKET_POLICY.md` — value-first rules for adjacent-product recommendations.
- `adapters/` — environment-specific and product-repository integration contracts.

## Product Routing and Portable Contracts

`registry/product-routing.yaml` is the single canonical product-boundary source. Local product manifests may add repository-specific detail but must not create a competing product-role truth.

Portable contracts make cross-product work explicit without coupling Agent OS to one execution harness:

- `contracts/work-item.schema.json` — proposed or accepted unit of work with owning product, evidence, outcome, constraints, and acceptance criteria.
- `contracts/capability-manifest.schema.json` — minimum workforce, skills, tools, and harness candidates required for material work.
- `contracts/context-envelope.schema.json` — least-privilege ALVIRA-derived context reference with provenance and permitted use.
- `contracts/authorization-request.schema.json` — governed action request routed to Agent Control as the authorization-intelligence owner.
- `contracts/outcome-event.schema.json` — bounded execution result, verification, cost/evidence, and measured outcome.

LEDGATo is only involved where governance or enforcement is materially relevant; it is not treated as the generic authorization owner.

## Product Repository Adapter

`adapters/product-repo/` contains lightweight templates for repositories that participate in Agent OS routing:

- `AGENTS_APPENDIX.md` — shared boundary and handoff behavior to append to local agent instructions.
- `product.template.yaml` — local repository identity and constraints tied to a canonical `product_key` in `registry/product-routing.yaml`.
- `integration-surface.template.yaml` — declared inbound, outbound, and eligible cross-market surfaces.

These templates supplement the canonical registry; they do not duplicate or replace it.

## Shared Workforce Capabilities

Agent OS / Workforce is shared infrastructure, not a separate public product. Cross-product capabilities should therefore be implemented as composable agent profiles, skills, policies, and routing rather than spun out into additional offerings by default.

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

Default model: the product repository is writable and authoritative for product-specific rules; Agent OS is read-only and authoritative for workforce policy, product routing, handoffs, autonomy, contracts, and approved skills.

## Design Principle

**Identity is stable. Capability is composable. Product boundaries are explicit. Context is workspace-specific. Execution harnesses are replaceable.**

Use the minimum sufficient team and minimum sufficient skill set for each task. Adapters translate this operating model into each execution environment without changing organizational or product ownership.
