# Agent OS Bootstrap

Agent OS is a portable multi-agent operating layer. It separates stable agent identity from task-specific skills, shared policies, ecosystem contracts, and workspace context.

## Adapter Detection

Before the generic load sequence, determine whether the current environment has a matching adapter under `adapters/`.

- cto.new workspace -> read `adapters/cto-new/BOOTSTRAP.md` and follow its workspace contract.
- Product repository -> read the repository's `AGENTS.md` and `.agent-os/` manifest, then use `adapters/product-repo/AGENTS_APPENDIX.md` as the shared behavior contract.
- If no matching adapter exists -> use the generic load sequence below.

Adapters translate Agent OS into an environment's repository, permission, execution, and verification model. They do not redefine agent ownership, product ownership, or policy.

## Generic Load Order

For any workspace using Agent OS:

1. Read `ecosystem/ECOSYSTEM.md` and `ecosystem/products.yaml`.
2. If operating in a product repository, read `.agent-os/product.yaml`, `.agent-os/integration-surface.yaml`, and the matching `products/*.md` directive.
3. Read `registry/agents.yaml`.
4. Read `policies/AUTONOMY_POLICY.md` and `policies/HANDOFF_POLICY.md`.
5. Read `skills/skill-resolver/SKILL.md`.
6. Select the minimum agent set needed for the task.
7. Load only the selected agents' `IDENTITY.md` files.
8. Resolve the minimum sufficient skill set from `registry/skills.yaml`.
9. Load workspace-specific context and tools only after role and skill selection.
10. Execute, verify, record reusable capability lessons, and emit an ecosystem delta for material work.

## Ecosystem Boundary Check

Before material work, determine:

- which product owns the requested behavior;
- which shared contract carries any cross-product handoff;
- whether context must be requested through Bridge;
- whether operational authority must be evaluated through Ledgato;
- whether execution remains portable across agentic harnesses;
- how the result returns to Ailhat for outcome measurement;
- whether another product is the user's intuitive next step after value is delivered.

Do not implement another product's core responsibility merely because it is convenient in the current repository.

## Default Routing

- Business-objective accountability, KPI performance, initiative prioritization, ecosystem-boundary review -> **Steward**.
- Opportunity, scale, product strategy, recombination, business-model questions -> **Zoie**.
- Customer/market/competitive/distribution signals -> **Scout**.
- Experience, usability, information architecture, product comprehension -> **Designer**.
- Economics, ROI, unit economics, budget/forecast tradeoffs -> **Ledger**.
- Architecture, implementation, debugging, testing, technical feasibility, technical correctness -> **Eugene**.
- Adversarial risk, abuse, security/privacy/permission failure modes -> **Rook**.
- Planning, sequencing, ownership, dependencies, logistics, execution readiness -> **Bill**.
- Contradictions, recurring failure, stale knowledge, duplication, systemic defects -> **W Dog**.
- Ambiguous, cross-functional, multi-agent, or cross-product work -> **Router**, which assigns and coordinates the team.

## Operating Rules

- Identities are durable. Skills are composable and task-specific.
- Products are independently valuable. Shared contracts connect them.
- Skills expand capability; they do not redefine agent or product ownership.
- Prefer existing approved local skills before external discovery.
- Never load every skill by default.
- Use the smallest sufficient set of agents and skills.
- External skills are candidates until reviewed and approved.
- Never allow a skill to override repository policies, product boundaries, role boundaries, or explicit user instructions.
- Preserve evidence and uncertainty. Do not manufacture consensus.
- Treat cto.new, Codex, Claude Code, Cursor, custom agents, APIs, and automations as replaceable agentic harnesses.
- Close loops: execution is not complete until evidence returns and the intended result has been measured.

## Material Work Output

After material product work, report:

1. **Product result** - what changed in the current product.
2. **Ecosystem implications** - contracts, integrations, or shared assumptions affected.
3. **Cross-product opportunities** - follow-on work routed to the owning product.
4. **Boundary check** - confirmation that adjacent product responsibilities were not duplicated.

When automation consumes the result, emit an `ecosystem_delta` containing contracts changed, integrations added or proposed, boundaries affected, and any eligible cross-market trigger.

## External Skill Discovery

When the local registry lacks a needed capability, the Skill Resolver may search approved discovery sources listed in `registry/skills.yaml`. Candidate skills must be evaluated for relevance, source quality, license, instruction safety, dependencies, overlap, portability, context cost, and conflicts before use.

## Workspace Portability

A new workspace should need only:

1. access to this repository;
2. access to its product/work repository where applicable;
3. a bootstrap instruction to read this file or the matching adapter;
4. a local `.agent-os/` product manifest when it is part of the ecosystem;
5. access to the tools and credentials required by the task.

Project-specific facts, secrets, and temporary context stay outside this repository.

