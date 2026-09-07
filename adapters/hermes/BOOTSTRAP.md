# Hermes Harness Adapter Bootstrap

Use this adapter when Hermes acts as the executing harness for Agent OS governed work. Hermes is an agentic execution environment (the harness), not an Agent OS organizational agent. It orchestrates durable roles and may delegate implementation to sub-harnesses (Codex CLI, Claude Code, OpenCode) without ever becoming the owner of product priority, workforce identity, context, authorization, or governance.

## What Hermes is, and is not

- **Harness.** Hermes is the model/tool environment performing agentic execution. It runs local on the operator's workstation and drives filesystem, git, shell, browser, network, and MCP tools.
- **Operator harness.** Hermes can simulate the Agent OS team sequentially in a single runner and can orchestrate sub-harnesses for concrete implementation. Orchestration does not widen authority.
- **Not an agent.** Hermes never appears in `registry/agents.yaml`. A durable role such as Eugene or Designer executes *through* Hermes; it is not Hermes.
- **Not a host.** The workstation is the host. Hermes runs on it but does not collapse the host/target boundary.

## Workspace Contract

- **Product repository:** primary working tree; read/write according to task authorization.
- **Agent OS repository:** shared operating layer; read-only unless the task explicitly concerns Agent OS itself.
- **Product-local instructions:** authoritative for product-specific architecture, conventions, design system, deployment, secrets, and acceptance criteria.
- **Agent OS:** authoritative for product routing, role routing, handoffs, autonomy policy, portable contracts, harness selection, skill resolution, and reusable capability procedures.

## Load Order

1. Read product-repository instructions first (`AGENTS.md`, README, project docs, or equivalent).
2. Read Agent OS `BOOTSTRAP.md`.
3. If the session is human-started and not already attached to a governed task, default to `human_exploration` and read `docs/proposals/EXECUTION_CONTEXT_AND_WORKSPACE_ISOLATION.md` before any mutation. Human exploration may be context-aware but does not silently acquire backlog/task authority.
4. If the task can create, select, interrupt, reprioritize, continue, or recover autonomous work, read `docs/proposals/AUTONOMOUS_OPERATING_GUARDRAILS.md` before planning or implementation.
5. If work is decomposed, more than one Agent OS role is considered, a child/subtask is spawned, parallel work is planned, or a sub-harness is delegated concrete execution, read `docs/proposals/MINIMUM_SUFFICIENT_TEAM_AND_DELEGATION.md` before dispatch. Preserve one accountable owner and enforce bounded child authority/context/budget/depth.
6. Read `registry/product-routing.yaml` and establish the owning product/shared capability before selecting agents.
7. Read `.agent-os/product.yaml` and `.agent-os/integration-surface.yaml` when present; local metadata may add detail but may not redefine canonical product roles.
8. Read `registry/agents.yaml`.
9. Read `policies/AUTONOMY_POLICY.md` and `policies/HANDOFF_POLICY.md`.
10. Read `skills/skill-resolver/SKILL.md`.
11. Read `registry/harnesses.yaml` only when the task requires harness selection or sub-harness delegation.
12. **Autonomous-workforce reconciliation/build tasks:** when the task concerns persistence, recurring/background execution, Milchik, Telegram control, Hermes Kanban, backlog dispatch, workforce health, autonomous business operations, or multi-agent delegation, automatically read all of the following before planning or implementation:
   - `docs/proposals/MILCHIK_HERMES_KANBAN_CONTROL.md`
   - `docs/proposals/AUTONOMOUS_WORKFORCE_GAP_PLAN.md`
   - `docs/proposals/WORKFORCE_HEALTH_AND_DEGRADATION.md`
   - `docs/proposals/EXECUTION_CONTEXT_AND_WORKSPACE_ISOLATION.md`
   - `docs/proposals/AUTONOMOUS_OPERATING_GUARDRAILS.md`
   - `docs/proposals/MINIMUM_SUFFICIENT_TEAM_AND_DELEGATION.md`
   Reconcile each requirement against current `main`, open PRs, and live-host behavior. Prefer existing runtime/contracts over duplicate infrastructure.
13. Select the minimum sufficient agent roles and approved skills.
14. Work only in the product repository unless explicitly authorized otherwise.
15. Verify the result in the product environment and return material outcome evidence before declaring completion.

## Human exploration and governed work

Hermes must distinguish a human exploratory session from Agent OS governed execution.

- A human may use Hermes, Codex, Claude Code, OpenCode, or another compatible harness to explore ideas while Agent OS continues autonomous work.
- Exploration should use an isolated branch/worktree when mutation is possible.
- Before mutation, inspect active Agent OS work for overlapping mutable surfaces.
- Exploration does not automatically create backlog, reprioritize work, interrupt running tasks, or alter canonical task state.
- Explicit promotion language such as `capture this`, `add this to backlog`, `build this`, `send this to Steward`, or an equivalent governed transition may create a candidate/work item according to policy.
- If human exploration materially invalidates an active task, create a structured intervention/handoff rather than silently editing that task's state.

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

Hermes is a single runner today. It may simulate selected Agent OS roles sequentially and may delegate concrete implementation to sub-harnesses while staying inside the task envelope. This is a runtime limitation, not the long-term organizational model.

Recommended flow:

1. **Router** classifies the task, product boundary, and needed handoffs.
2. Establish exactly one accountable task owner.
3. Add only the minimum supporting roles whose decision layer materially improves the outcome.
4. **Bill** converts accepted decisions into an execution sequence when needed.
5. When material, serialize the accepted work to `contracts/work-item.schema.json` and the required workforce to `contracts/capability-manifest.schema.json`.
6. Request context and authorization only when the task requires them.
7. If a bounded child/subtask is useful, create it under the parent task using the delegation contract; children may narrow but never widen scope, authority, context, budget, tools, or time.
8. The accountable executing role performs product-repo changes directly or through a selected sub-harness. Sub-harness delegation does not transfer organizational ownership.
9. **Rook** performs adversarial/control review when material.
10. **W Dog** performs systemic verification/recurrence checks when material.
11. **Steward** reviews outcome against initiative/KPI when the task is initiative-level.
12. Return child evidence to the parent lineage, synthesize the result, and return an `outcome-event` or equivalent evidence before closing the parent task.

Do not load every role. Skip any perspective, child, or contract that would not materially improve the outcome.

## Delegation Boundary

Hermes must distinguish:

- **organizational delegation** — another Agent OS role owns a bounded specialist decision layer;
- **temporary sub-agent delegation** — an ephemeral child instance performs a bounded subtask under a parent task;
- **sub-harness delegation** — Codex/Claude Code/OpenCode performs concrete execution while the Agent OS role remains accountable.

Delegation must obey configured depth, child-count, parallelism, cost, authority, context-release, and workspace-isolation limits. A child or sub-harness cannot acquire authority that the parent task does not possess.

## Harness Selection

When implementation is delegated, select the minimum sub-harness for the task class from `registry/harnesses.yaml`. Selection may weigh tools, cost, privacy, and model capability, but cannot expand authority and cannot bypass a human gate.

Selection is advisory, not policy. No selection hint in the registry authorizes execution; authorization is resolved before the harness is chosen.

Security-sensitive capability (notably browser execution) requires the fail-closed adapter bridge for that harness. See `adapters/codex/browser.py` and `runtime/browser_security.py` for the working pattern: a harness that cannot prove it enforced the required attestations is blocked, not trusted.

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

`REQUEST → EXECUTION CONTEXT → PRODUCT BOUNDARY → ACCOUNTABLE OWNER → MINIMUM SUPPORT/CHILDREN IF NEEDED → TASK ENVELOPE → CONTEXT/AUTHORIZATION → EXECUTE (DIRECT OR VIA SUB-HARNESS) → CHILD EVIDENCE → TEST/VERIFY → PARENT SYNTHESIS → OUTCOME EVIDENCE → PR/DELIVERY`

For analysis-only work:

`REQUEST → EXECUTION CONTEXT → PRODUCT BOUNDARY → ACCOUNTABLE OWNER → MINIMUM SPECIALISTS → SYNTHESIS → RECOMMENDATION`

## Reference Task Class: PR Review

The first governed task class run through Hermes is pull-request review:

1. **Router** selects the minimum team (technical reviewer + editorial reviewer); **Rook** joins only when the change is material.
2. Reviewers analyze their own decision layer in sequence.
3. Findings are delivered as a GitHub comment; no merge is performed.
4. Merge remains human-gated regardless of review outcome.
5. Material evidence (the review comment, the PR reference) returns to the task owner.

## Human Escalation

Follow `policies/AUTONOMY_POLICY.md`. Do not interrupt merely because uncertainty exists. Escalate only when the action exceeds delegated authority or crosses a defined human-approval threshold.

## Completion Standard

A Hermes task is not complete merely because code changed, a child returned, or a sub-harness reported success. Completion requires:

- requested outcome addressed;
- accountable parent owner retained;
- child evidence returned to parent lineage when delegation occurred;
- canonical product boundaries and local constraints honored;
- tests/checks run where available;
- material security/permission/irreversibility concerns reviewed;
- no known unresolved blocker hidden from the user;
- resulting product behavior verified when the environment permits it;
- material execution evidence returned to the appropriate owner or portfolio loop.
