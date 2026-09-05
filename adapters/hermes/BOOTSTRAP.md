# Hermes Adapter Bootstrap

Use this adapter when Agent OS is available alongside a Hermes agentic execution harness. Hermes is a model-provider-agnostic CLI agent that can act as the execution layer for governed Agent OS tasks. It is an execution harness, not the owner of product priority, workforce identity, context, authorization, or governance.

## Workspace Contract

- **Product repository:** primary working tree; read/write according to workspace permissions and the task envelope.
- **Agent OS repository:** shared operating layer; treat as read-only unless the task explicitly concerns Agent OS itself.
- **Product-local instructions:** authoritative for product-specific architecture, conventions, design system, deployment, secrets, and acceptance criteria.
- **Agent OS:** authoritative for product routing, role routing, handoffs, autonomy policy, portable contracts, skill resolution, and reusable capability procedures.
- **Hermes:** execution harness. Loads prompts, resolves tools within the task authorization, uses the configured model provider, and returns results. Hermes's model-provider key and tool access are execution dependencies; none implies broader authority.

## Load Order

1. Read product-repository instructions first (`AGENTS.md`, README, project docs, or equivalent).
2. Read Agent OS `BOOTSTRAP.md`.
3. Read `registry/product-routing.yaml` and establish the owning product/shared capability before selecting agents.
4. Read `.agent-os/product.yaml` and `.agent-os/integration-surface.yaml` when present; local metadata may add detail but must not redefine canonical product roles.
5. Read `registry/agents.yaml`.
6. Read `policies/AUTONOMY_POLICY.md` and `policies/HANDOFF_POLICY.md`.
7. Read `skills/skill-resolver/SKILL.md`.
8. Select the minimum sufficient agent roles and approved skills.
9. Work only in the product repository unless explicitly authorized otherwise.
10. Choose and configure the Hermes model provider for the task (e.g. via `OPENROUTER_API_KEY` or another configured provider).
11. Execute within the task envelope; Hermes may use terminal, file, web, and GitHub tools only within the task's authorized scope.
12. Verify the result in the product environment and return material outcome evidence before declaring completion.

## Product Boundary Check

Before material implementation:

- confirm the requested behavior belongs to the current product or a shared workforce capability;
- preserve the constraints in `registry/product-routing.yaml`;
- propose a portable work item when another product owns the next decision layer;
- request ALVIRA-derived context only when needed and preserve provenance;
- route authorization-intelligence decisions to Agent Control when required;
- involve Rook only when governance or enforcement is materially in scope;
- do not turn Agent OS / Workforce into a standalone public offering.

## Single-Runner Multi-Agent Mode

Hermes typically exposes one executing agent per session. To simulate an Agent OS team, run Hermes sequentially per specialist role without pretending they are independent processes.

Recommended flow for a PR review task:

1. **Router** classifies the task, product boundary, and needed handoffs.
2. **Eugene** performs the technical review pass (correctness, architecture, testing, security, performance).
3. **Designer** performs the editorial/visual/experience review pass (tone, information architecture, mobile/desktop, accessibility, asset fidelity).
4. **Synthesis** produces a concise PR comment with blockers separated from nice-to-haves, and flags anything requiring visual verification or human judgment.
5. When material, serialize the accepted work to `contracts/work-item.schema.json` and the required workforce to `contracts/capability-manifest.schema.json`.
6. Request context and authorization only when the task requires them.
7. Return an `outcome-event` or equivalent evidence and close the handoff.

Do not load every role. Skip any perspective or contract that would not materially improve the outcome.

## Repository Permissions

Preferred access model:

```yaml
product_repo:
  read: true
  write: true
  pull_requests: true
  issues: true

agent_os:
  read: true
  write: false
```

If Agent OS is writable in the environment, still treat it as read-only by policy unless the task explicitly requests an Agent OS change.

Cross-product repository writes are not implied by access. Default to a handoff/work item; direct mutation requires explicit task authorization.

## Skill Use

- Resolve skills from `registry/skills.yaml`.
- Prefer `owned` and `approved` vendored skills.
- Do not execute candidate external skills merely because they are discoverable.
- Load only capabilities needed for the current task.
- Product-specific instructions override generic skill preferences when they conflict, unless doing so would violate higher-order safety, product-boundary, authorization, or security policy.

## Execution Pattern

For review tasks:

`REQUEST → PRODUCT BOUNDARY → ROUTE → SPECIALIST PASSES → SYNTHESIS → PR COMMENT → EVIDENCE`

For implementation tasks:

`REQUEST → PRODUCT BOUNDARY → ROUTE → SPECIALIST ANALYSIS → TASK ENVELOPE → CONTEXT/AUTHORIZATION IF NEEDED → EXECUTE → TEST/VERIFY → OUTCOME EVIDENCE → PR/DELIVERY`

For analysis-only work:

`REQUEST → PRODUCT BOUNDARY → ROUTE → MINIMUM SPECIALISTS → SYNTHESIS → RECOMMENDATION`

## Model Provider and Tool Access

Hermes requires a model provider for reasoning. Common paths:

- OpenRouter API key (`OPENROUTER_API_KEY`) — model-agnostic, per-token billing.
- Another OpenAI-compatible or direct provider key.
- A locally available model endpoint, if one is reachable from the host.

The model provider key is an execution dependency. It does not grant Agent OS authority, product ownership, or any permission beyond what the task and Agent OS policy already authorize.

Hermes may use tools such as terminal, file, web, and GitHub (`gh`) within the task envelope. GitHub actions typically use the run-provided `GITHUB_TOKEN` or a configured GitHub App token; either way, the token is scoped to the task and does not imply standing authority.

## Human Escalation

Follow `policies/AUTONOMY_POLICY.md`. Do not interrupt merely because uncertainty exists. Escalate only when the action exceeds delegated authority or crosses a defined human-approval threshold.

For ASHWOOD specifically: merge and production promotion remain human-gated. A preview deploy or a successful build is evidence that deployment built, not proof that the experience passed human or visual verification.

## Completion Standard

A Hermes task is not complete merely because output was produced. Completion requires:

- requested outcome addressed;
- canonical product boundaries and local constraints honored;
- relevant checks run where available (build, tests, visual check where the environment permits);
- material security/permission/irreversibility concerns reviewed;
- no known unresolved blocker hidden from the user;
- resulting product behavior verified when the environment permits it;
- material execution evidence returned to the appropriate owner or portfolio loop.
