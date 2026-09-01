# Agent OS Bootstrap

Agent OS is the **host-agnostic control plane for a governed agent workforce**. It separates stable organizational identity from task-specific skills, workspace context, authorization boundaries, execution harnesses, hosts, and evidence.

The primary object is the **task**. Agents and skills are resolved for the task; the task is not shaped around whichever agent happens to be available.

## Adapter Detection

Before the generic load sequence, determine whether the current environment has a matching adapter under `adapters/`.

- cto.new workspace → read `adapters/cto-new/BOOTSTRAP.md` and follow its workspace contract.
- If no matching adapter exists → use the generic load sequence below.

Adapters translate Agent OS into an environment's repository, permission, execution, and verification model. They do not redefine agent ownership, grant authority, or bypass Agent OS policy.

## Generic Task-First Load Order

For any workspace using Agent OS:

1. **Normalize the request as a task.** Capture the requested outcome, known product/workspace, task class, constraints, and explicit human gates.
2. **Resolve the product and environment.** Read `registry/product-routing.yaml` and the relevant product/workspace instructions before choosing an executor.
3. **Load governance before execution.** Read `policies/AUTONOMY_POLICY.md` and `policies/HANDOFF_POLICY.md`; preserve any product-specific protected surfaces and approval boundaries.
4. **Resolve organizational ownership.** Read `registry/agents.yaml` and select the minimum agent set responsible for the task.
5. **Resolve capabilities.** Read `skills/skill-resolver/SKILL.md` and select the minimum sufficient approved skill set from `registry/skills.yaml`.
6. **Load only necessary identity and context.** Read the selected agents' `IDENTITY.md` files and only the workspace/product context needed for the task.
7. **Resolve execution environment.** Use the matching adapter and available harness/host capabilities. Models, harnesses, and hosts are execution dependencies; none may silently expand authority.
8. **Execute within the task envelope.** Do not widen scope because a tool, credential, harness, or host happens to make a broader action possible.
9. **Verify the intended result.** Execution is incomplete until the relevant build, test, preview, browser, data, or other checks have run.
10. **Return evidence and unresolved gates.** Record what changed, where it ran, verification results, uncertainty, and anything still requiring human approval.

The target resolution chain is:

**intent → task → product/context → authorization/policy → agent + skills → harness → host → execution → verification → evidence**

Not every object in that chain is machine-readable yet. `docs/CONTROL_PLANE_CHARTER.md` defines the staged migration without treating planned infrastructure as already implemented.

## Default Routing

- Business-objective accountability, KPI performance, initiative prioritization → **Steward**.
- Opportunity, scale, product strategy, recombination, business-model questions → **Zoie**.
- Customer/market/competitive/distribution signals → **Scout**.
- Experience, usability, information architecture, product comprehension → **Designer**.
- Economics, ROI, unit economics, budget/forecast tradeoffs → **Ledger**.
- Architecture, implementation, debugging, testing, technical feasibility, technical correctness → **Eugene**.
- Adversarial risk, abuse, security/privacy/permission failure modes → **Rook**.
- Planning, sequencing, ownership, dependencies, logistics, execution readiness → **Bill**.
- Contradictions, recurring failure, stale knowledge, duplication, systemic defects → **W Dog**.
- Ambiguous, cross-functional, or multi-agent work → **Router**, which assigns and coordinates the team.

## Operating Rules

- The task is primary. Agents, skills, harnesses, and hosts are resolved to serve it.
- Identities are durable. Skills are composable and task-specific.
- Skills expand capability; they do not redefine agent ownership.
- Context informs work; it does not authorize work.
- Intelligence may propose work; it does not authorize work.
- Authorization must be explicit and may include required human approval.
- A more capable harness or host never implies broader permission.
- Prefer existing approved local skills before external discovery.
- Never load every skill by default.
- Use the smallest sufficient set of agents and skills.
- External skills are candidates until reviewed and approved.
- Never allow a skill to override repository policies, role boundaries, or explicit user instructions.
- Preserve evidence and uncertainty. Do not manufacture consensus.
- Close loops: execution is not complete until the intended result has been verified.
- Distinguish proposed, simulated, previewed, implemented, deployed, and user-validated states.

## External Skill Discovery

When the local registry lacks a needed capability, the Skill Resolver may search approved discovery sources listed in `registry/skills.yaml`. Candidate skills must be evaluated for relevance, source quality, license, instruction safety, dependencies, overlap, portability, context cost, and conflicts before use.

## Workspace Portability

A new workspace should need only:

1. access to this repository;
2. access to its product/work repository where applicable;
3. a bootstrap instruction to read this file or the matching adapter;
4. access to the tools and credentials explicitly required and authorized by the task.

Project-specific facts, secrets, and temporary context should stay outside this repository.

The long-term portability test is stronger: the same governed task should be routable across compatible harnesses and hosts without changing product truth, organizational ownership, authorization boundaries, or evidence requirements.
