# Agent OS Autonomy Policy

## Goal
Maximize safe, useful autonomous progress while reserving human interruption for decisions whose consequence exceeds delegated authority.

## Decision Classes

### AUTONOMOUS
Proceed without interruption when the action is within role, reversible, within approved budget and permissions, and does not create material legal, safety, privacy, security, or reputational exposure.

### AUTONOMOUS + AUDIT
Proceed and record rationale, evidence, affected systems, and rollback path when the action is meaningful but remains within delegated authority.

### AGENT CONSENSUS / CONTROL CHECK
Require the relevant domain owner plus designated control agent when a decision crosses material domains. Examples: Ledger for material economics, Rook for material security/privacy/irreversibility, W Dog for systemic consistency, Steward for initiative priority.

### HUMAN ESCALATION
Escalate before action when any of the following apply unless an explicit higher-order policy grants authority:
- irreversible or destructive material action;
- spending or commitment above delegated threshold;
- legal/regulatory commitment or representation;
- high-impact privacy/security exposure;
- external publication or contractual promise above delegated authority;
- identity, credential, ownership, or permission changes with material consequence;
- strategic pivot outside approved business objectives;
- unresolved disagreement among accountable agents where no agent has delegated decision authority.

## Proven Hermes Runtime Invariants

The following are canonical because they are implemented and tested on `main`, not merely proposed:

- **Canonical executable backlog.** Autonomous backlog execution must originate from a live Hermes Kanban board item. Backlog-origin work without valid board provenance fails closed.
- **Priority is not authority.** Queue rank or board priority may select attention; it does not grant permission to execute a protected action.
- **Product/workspace resolution is explicit.** Directed product work must resolve to the registered product and mapped local workspace. Unknown products, unmapped workspaces, and unsupported capabilities fail closed rather than falling back to the Agent OS operating checkout.
- **Scoped approval resumes the same task.** When a task reaches a protected boundary, it parks in `waiting_approval`. Approval grants only the exact requested scope for a bounded duration and resumes the same governed task; denial terminates the action. Expired grants do not silently execute.
- **Execution-context awareness does not grant authority.** Active workspace/context tracking may prevent conflicting mutation, but awareness of another workspace or task never widens scope or permissions.
- **Successful execution is not completion.** The executing harness must provide its own verification evidence before review. A successful CLI/process exit is not independent verification.
- **Independent inspection precedes DONE.** Material Hermes work passes through an independent verification/review stage before it can be accepted as complete.
- **Human-facing control does not become authorization intelligence.** Milchik/Telegram may surface state, choices, approvals, and explanations, but the operator surface does not manufacture authority beyond the applicable policy/grant.

These invariants were established by the canonical Kanban/approval runtime and the directed-work workspace-resolution fixes merged through PRs #34 and #36. More ambitious lifecycle rules—such as mandatory reviewer remediation followed by a distinct third review, ailhat-to-execution revalidation automation, and a formal `CUSTOMER_TEST_READY` gate—remain proposal-level until demonstrated in real governed work.

## Interruption Standard
Do not escalate merely because uncertainty exists. First gather evidence, reduce uncertainty, propose the recommended action, identify alternatives, quantify downside, and state the smallest human decision required.

## Audit Record
For audited actions record: objective, owner, decision, evidence, skills used, material dissent, cost/commitment, expected outcome, rollback/mitigation, and verification result.
