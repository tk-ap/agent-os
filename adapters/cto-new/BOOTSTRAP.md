# cto.new Adapter Bootstrap

Use this adapter when Agent OS is available alongside a cto.new product workspace. cto.new is an agentic execution harness; it does not become the ecosystem's portfolio, workforce, context, or authorization owner.

## Workspace Contract

- **Product repository:** primary working tree; read/write according to workspace permissions.
- **Agent OS repository:** shared operating layer; treat as read-only unless the task explicitly concerns Agent OS itself.
- **Product-local instructions:** authoritative for product-specific architecture, conventions, design system, deployment, secrets, and acceptance criteria.
- **Agent OS:** authoritative for ecosystem boundaries, role routing, handoffs, autonomy policy, shared contracts, skill resolution, and reusable capability procedures.

## Load Order

1. Read product-repository instructions (`AGENTS.md`, README, project docs, or equivalent).
2. Read Agent OS `BOOTSTRAP.md`, `ecosystem/ECOSYSTEM.md`, and `ecosystem/products.yaml`.
3. If present, read the product repository's `.agent-os/product.yaml`, `.agent-os/integration-surface.yaml`, and matching `products/*.md` directive.
4. Read `registry/agents.yaml`.
5. Read `policies/AUTONOMY_POLICY.md` and `policies/HANDOFF_POLICY.md`.
6. Read `skills/skill-resolver/SKILL.md`.
7. Select the minimum sufficient agent roles and approved skills.
8. Work only in the product repository unless explicitly authorized otherwise.
9. Verify the result in the product environment.
10. Report product result, ecosystem implications, cross-product opportunities, and boundary check.

## Single-Runner Multi-Agent Mode

If cto.new exposes one executing agent rather than separate concurrent workers, simulate the Agent OS team sequentially without pretending they are independent processes.

1. **Router** classifies the task, product owner, and required contracts.
2. Relevant specialists analyze only their decision layer.
3. **Bill** converts accepted decisions into an execution sequence and confirms harness fit.
4. The executing technical role performs product-repo changes.
5. **Rook** performs adversarial/control review when material.
6. **W Dog** performs systemic verification/recurrence checks when material.
7. **Steward** reviews outcome and ecosystem-boundary impact when material.
8. Router synthesizes unresolved issues and closes the task.

Do not load every role. Skip any perspective or cross-product call that would not materially improve the outcome.

## Repository Permissions

```yaml
product_repo:
  read: true
  write: true
  pull_requests: true

agent_os:
  read: true
  write: false
```

If Agent OS is writable, still treat it as read-only unless the task explicitly requests an Agent OS change.

## Ecosystem Boundary Rules

- Keep ALVIRA context authorship, Bridge context distribution, Ailhat portfolio priority, Agent OS workforce routing, and Ledgato operational authority distinct.
- Use contracts under `contracts/` for cross-product handoffs.
- Do not hard-code cto.new into portable work items or product contracts; record it as the selected harness on the outcome event.
- Propose cross-product work to the owning product rather than editing another product repository without authorization.
- Promote another product only after the current value moment and only when it solves the next visible user need.

## Skill Use

- Resolve skills from `registry/skills.yaml`.
- Prefer `owned` and `approved` vendored skills.
- Do not execute candidate external skills merely because they are discoverable.
- Load only capabilities needed for the current task.
- Product-specific instructions override generic skill preferences when they conflict, unless doing so would violate higher-order safety, security, authority, or ecosystem-boundary policy.

## Execution Pattern

Implementation:

`REQUEST -> BOUNDARY CHECK -> ROUTE -> SPECIALIST ANALYSIS -> PLAN -> AUTHORITY CHECK -> MODIFY PRODUCT REPO -> TEST/VERIFY -> EVIDENCE -> OUTCOME EVENT`

Analysis only:

`REQUEST -> BOUNDARY CHECK -> ROUTE -> MINIMUM SPECIALISTS -> SYNTHESIS -> RECOMMENDATION`

## Human Escalation

Follow `policies/AUTONOMY_POLICY.md`. Do not interrupt merely because uncertainty exists. Escalate only when the action exceeds delegated authority or crosses a defined human-approval threshold.

## Completion Standard

A cto.new task is not complete merely because code changed. Completion requires the requested outcome addressed; product-local constraints honored; relevant checks run; material authority and risk concerns reviewed; blockers disclosed; product behavior verified where possible; cross-product implications reported; and evidence returned for outcome measurement.

