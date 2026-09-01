# Agent OS Bootstrap

Agent OS is a portable multi-agent operating layer. It separates stable agent identity from task-specific skills, shared policies, product routing, portable contracts, and workspace context.

## Adapter Detection

Before the generic load sequence, determine whether the current environment has a matching adapter under `adapters/`.

- cto.new workspace → read `adapters/cto-new/BOOTSTRAP.md` and follow its workspace contract.
- Product repository with local Agent OS metadata → read the repository instructions plus `.agent-os/product.yaml` and `.agent-os/integration-surface.yaml` when present.
- If no matching adapter exists → use the generic load sequence below.

Adapters translate Agent OS into an environment's repository, permission, execution, and verification model. They do not redefine agent ownership, product ownership, or bypass Agent OS policy.

## Generic Load Order

For any workspace using Agent OS:

1. Read `registry/product-routing.yaml` to establish the owning product or shared capability, boundaries, constraints, and default routing.
2. Read local product/workspace instructions and `.agent-os/` metadata when present. Local metadata may add implementation detail but must not redefine canonical product roles.
3. Read `registry/agents.yaml`.
4. Read `policies/AUTONOMY_POLICY.md`, `policies/HANDOFF_POLICY.md`, and `policies/CROSS_MARKET_POLICY.md` when cross-product recommendation is relevant.
5. Read `skills/skill-resolver/SKILL.md`.
6. Select the minimum agent set needed for the task.
7. Load only the selected agents' `IDENTITY.md` files.
8. Resolve the minimum sufficient skill set from `registry/skills.yaml`.
9. Load workspace-specific context and tools only after product boundary, role, and skill selection.
10. Execute, verify, and record reusable capability lessons and outcome evidence.

## Product Boundary Check

Before material work:

- identify the owning product or shared workforce capability from `registry/product-routing.yaml`;
- confirm that the requested behavior fits that owner's role and constraints;
- do not turn shared Agent OS / Workforce capability into a separate public offering;
- if another product owns the next decision layer, create a portable handoff instead of duplicating the capability locally;
- use `contracts/work-item.schema.json` for cross-product or cross-workspace work;
- request ALVIRA-derived context through `contracts/context-envelope.schema.json` when context is needed;
- use `contracts/authorization-request.schema.json` when an action requires authorization intelligence from Agent Control;
- use `contracts/capability-manifest.schema.json` to describe the minimum workforce/tools required when material;
- return `contracts/outcome-event.schema.json` after bounded execution when a machine-readable outcome is useful.

LEDGATo participates only when the work materially intersects its defined governance or enforcement scope. It is not the owner of generic authorization intelligence.

## Default Routing

- Business-objective accountability, KPI performance, initiative prioritization → **Steward**.
- Opportunity, scale, product strategy, recombination, business-model questions → **Zoie**.
- Customer/market/competitive/distribution signals and Growth / Marketing Engineering → **Scout**.
- Experience, usability, information architecture, product comprehension → **Designer**.
- Economics, ROI, unit economics, budget/forecast tradeoffs → **Ledger**.
- Architecture, implementation, debugging, testing, technical feasibility, technical correctness → **Eugene**.
- Adversarial risk, abuse, security/privacy/permission failure modes → **Rook**.
- Planning, sequencing, ownership, dependencies, logistics, execution readiness → **Bill**.
- Contradictions, recurring failure, stale knowledge, duplication, systemic defects → **W Dog**.
- Ambiguous, cross-functional, multi-agent, or cross-product work → **Router**, which assigns and coordinates the minimum sufficient team.

## Operating Rules

- Identities are durable. Skills are composable and task-specific.
- `registry/product-routing.yaml` is the canonical source for product roles and shared-capability boundaries.
- Skills expand capability; they do not redefine agent or product ownership.
- Prefer existing approved local skills before external discovery.
- Never load every skill by default.
- Use the smallest sufficient set of agents and skills.
- External skills are candidates until reviewed and approved.
- Never allow a skill to override repository policies, product boundaries, role boundaries, or explicit user instructions.
- Preserve evidence and uncertainty. Do not manufacture consensus.
- Close loops: execution is not complete until the intended result has been verified and material outcome evidence has a destination.

## External Skill Discovery

When the local registry lacks a needed capability, the Skill Resolver may search approved discovery sources listed in `registry/skills.yaml`. Candidate skills must be evaluated for relevance, source quality, license, instruction safety, dependencies, overlap, portability, context cost, and conflicts before use.

## Workspace Portability

A new workspace should need only:

1. access to this repository;
2. access to its product/work repository where applicable;
3. a bootstrap instruction to read this file or the matching adapter;
4. optional local `.agent-os/` metadata for product-specific routing and integration surfaces;
5. access to the tools and credentials required by the task.

Project-specific facts, secrets, and temporary context should stay outside this repository.
