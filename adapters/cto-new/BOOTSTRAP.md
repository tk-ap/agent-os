# cto.new Adapter Bootstrap

Use this adapter when Agent OS is available alongside a cto.new product workspace. cto.new is a generalized agentic execution harness, not the owner of product priority, workforce identity, context, authorization, or governance.

## Workspace Contract

- **Product repository:** primary working tree; read/write according to workspace permissions.
- **Agent OS repository:** shared operating layer; treat as read-only unless the task explicitly concerns Agent OS itself.
- **Product-local instructions:** authoritative for product-specific architecture, conventions, design system, deployment, secrets, and acceptance criteria.
- **Agent OS:** authoritative for product routing, role routing, handoffs, autonomy policy, portable contracts, skill resolution, and reusable capability procedures.

## Load Order

1. Read product-repository instructions first (`AGENTS.md`, README, project docs, or equivalent).
2. Read Agent OS `BOOTSTRAP.md`.
3. Read `registry/product-routing.yaml` and establish the owning product/shared capability before selecting agents.
4. Read `.agent-os/product.yaml` and `.agent-os/integration-surface.yaml` when present; local metadata may add detail but may not redefine canonical product roles.
5. Read `registry/agents.yaml`.
6. Read `policies/AUTONOMY_POLICY.md` and `policies/HANDOFF_POLICY.md`.
7. Read `skills/skill-resolver/SKILL.md`.
8. Select the minimum sufficient agent roles and approved skills.
9. Work only in the product repository unless explicitly authorized otherwise.
10. Verify the result in the product environment and return material outcome evidence before declaring completion.

## Product Boundary Check

Before material implementation:

- confirm the requested behavior belongs to the current product or a shared workforce capability;
- preserve the constraints in `registry/product-routing.yaml`;
- propose a portable work item when another product owns the next decision layer;
- request ALVIRA-derived context only when needed and preserve provenance;
- route authorization-intelligence decisions to Agent Control when required;
- involve LEDGATo only when governance or enforcement is materially in scope;
- do not turn Agent OS / Workforce into a standalone public offering.

## Single-Runner Multi-Agent Mode

If cto.new exposes one executing agent rather than separate concurrent workers, simulate the Agent OS team sequentially without pretending they are independent processes.

Recommended flow:

1. **Router** classifies the task, product boundary, and needed handoffs.
2. Relevant specialists analyze only their decision layer.
3. **Bill** converts accepted decisions into an execution sequence when needed.
4. When material, serialize the accepted work to `contracts/work-item.schema.json` and the required workforce to `contracts/capability-manifest.schema.json`.
5. Request context and authorization only when the task requires them.
6. The executing technical role performs product-repo changes.
7. **Rook** performs adversarial/control review when material.
8. **W Dog** performs systemic verification/recurrence checks when material.
9. **Steward** reviews outcome against initiative/KPI when the task is initiative-level.
10. Return an `outcome-event` or equivalent evidence and close the handoff.

Do not load every role. Skip any perspective or contract that would not materially improve the outcome.

## Repository Permissions

Preferred access model:

```yaml
product_repo:
  read: true
  write: true
  pull_requests: true

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

For implementation work:

`REQUEST → PRODUCT BOUNDARY → ROUTE → SPECIALIST ANALYSIS → TASK ENVELOPE → CONTEXT/AUTHORIZATION IF NEEDED → EXECUTE → TEST/VERIFY → OUTCOME EVIDENCE → PR/DELIVERY`

For analysis-only work:

`REQUEST → PRODUCT BOUNDARY → ROUTE → MINIMUM SPECIALISTS → SYNTHESIS → RECOMMENDATION`

## Human Escalation

Follow `policies/AUTONOMY_POLICY.md`. Do not interrupt merely because uncertainty exists. Escalate only when the action exceeds delegated authority or crosses a defined human-approval threshold.

## Completion Standard

A cto.new task is not complete merely because code changed. Completion requires:

- requested outcome addressed;
- canonical product boundaries and local constraints honored;
- tests/checks run where available;
- material security/permission/irreversibility concerns reviewed;
- no known unresolved blocker hidden from the user;
- resulting product behavior verified when the environment permits it;
- material execution evidence returned to the appropriate owner or portfolio loop.
