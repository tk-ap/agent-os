# cto.new Adapter Bootstrap

Use this adapter when Agent OS is available alongside a cto.new product workspace.

## Workspace Contract

- **Product repository:** primary working tree; read/write according to workspace permissions.
- **Agent OS repository:** shared operating layer; treat as read-only unless the task explicitly concerns Agent OS itself.
- **Product-local instructions:** authoritative for product-specific architecture, conventions, design system, deployment, secrets, and acceptance criteria.
- **Agent OS:** authoritative for role routing, handoffs, autonomy policy, skill resolution, and reusable capability procedures.

## Load Order

1. Read product-repository instructions first (`AGENTS.md`, README, project docs, or equivalent).
2. Read Agent OS `BOOTSTRAP.md`.
3. Read `registry/agents.yaml`.
4. Read `policies/AUTONOMY_POLICY.md` and `policies/HANDOFF_POLICY.md`.
5. Read `skills/skill-resolver/SKILL.md`.
6. Select the minimum sufficient agent roles.
7. Load only the selected identities and approved skills.
8. Work only in the product repository unless explicitly authorized otherwise.
9. Verify the result in the product environment before declaring completion.

## Single-Runner Multi-Agent Mode

If cto.new exposes one executing agent rather than separate concurrent workers, simulate the Agent OS team sequentially without pretending they are independent processes.

Recommended flow:

1. **Router** classifies the task and selects roles.
2. Relevant specialists analyze only their decision layer.
3. **Bill** converts accepted decisions into an execution sequence when needed.
4. The executing technical role performs product-repo changes.
5. **Rook** performs adversarial/control review when material.
6. **W Dog** performs systemic verification/recurrence checks when material.
7. **Steward** reviews outcome against initiative/KPI when the task is initiative-level.
8. Router synthesizes unresolved issues and closes the task.

Do not load every role. Skip any perspective that would not materially improve the outcome.

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

## Skill Use

- Resolve skills from `registry/skills.yaml`.
- Prefer `owned` and `approved` vendored skills.
- Do not execute candidate external skills merely because they are discoverable.
- Load only capabilities needed for the current task.
- Product-specific instructions override generic skill preferences when they conflict, unless doing so would violate higher-order safety or security policy.

## cto.new Execution Pattern

For implementation work:

`REQUEST → ROUTE → SPECIALIST ANALYSIS → PLAN → MODIFY PRODUCT REPO → TEST/VERIFY → CONTROL CHECK → PR/DELIVERY`

For analysis-only work:

`REQUEST → ROUTE → MINIMUM SPECIALISTS → SYNTHESIS → RECOMMENDATION`

## Human Escalation

Follow `policies/AUTONOMY_POLICY.md`. Do not interrupt merely because uncertainty exists. Escalate only when the action exceeds delegated authority or crosses a defined human-approval threshold.

## Completion Standard

A cto.new task is not complete merely because code changed. Completion requires:

- requested outcome addressed;
- relevant product-local constraints honored;
- tests/checks run where available;
- material security/permission/irreversibility concerns reviewed;
- no known unresolved blocker hidden from the user;
- resulting product behavior verified when the environment permits it.
