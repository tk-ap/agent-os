# Milchik → Hermes Kanban → AgentOS Control Contract

> Status: proposal/build spec for Hermes reconciliation. Not canonical until reviewed and merged.

## Purpose

Make the Hermes Kanban board the canonical executable backlog for autonomous workforce management initiated through Milchik, including Telegram.

Milchik may discuss, summarize, recommend, prioritize, assign, pause, resume, or report on work, but autonomous backlog execution must be grounded in a governed Hermes Kanban item and dispatched through AgentOS.

## Core invariant

> **No governed Hermes Kanban item = no autonomous backlog execution.**

Telegram or any other chat surface is an operator interface, not a parallel backlog or authority source.

## Intended path

```text
Telegram / operator surface
        ↓
Milchik
        ↓
Hermes Kanban
        ↓
AgentOS work-item / task
        ↓
authorization / consensus / human escalation
        ↓
selected harness
        ↓
execution
        ↓
verification + evidence
        ↓
persistent AgentOS task state
        ↓
Hermes Kanban state update
        ↓
Milchik status/report
```

## Role boundaries

### Milchik

Milchik is the human-facing workforce operator.

Milchik may:
- query the board;
- recommend priorities;
- reorder work within explicitly delegated limits;
- create/propose board items from operator requests;
- assign eligible work;
- surface authorization/escalation state;
- pause, resume, or request cancellation through AgentOS;
- report progress and blockers.

Milchik must not:
- create a private execution queue outside the board;
- treat a Telegram message as executable authority by itself;
- bypass AgentOS authorization;
- invent board IDs or task state;
- execute an autonomous backlog task with no canonical board provenance;
- manufacture approval because the operator requested execution in chat.

### Hermes Kanban

The Hermes Kanban board is the canonical backlog/prioritization surface for autonomous backlog work.

It should hold or resolve at minimum:
- board item ID;
- title / work intent;
- source/product/repository;
- priority;
- status;
- dependencies / blockers;
- risk / impact class where available;
- assigned AgentOS role;
- selected harness when assigned;
- AgentOS work-item/task ID;
- authorization state;
- verification/result state.

### AgentOS

AgentOS remains the control plane.

It must enforce board provenance at dispatch for autonomous backlog work. Milchik and Hermes do not expand authority.

### Harness

Hermes or another selected harness executes only after AgentOS resolves the task envelope and authorization state.

## Required state flow

Recommended minimum board states:

```text
BACKLOG
  ↓
READY
  ↓
ASSIGNED
  ↓
IN_PROGRESS
  ↓
VERIFYING
  ↓
DONE
```

Alternate terminal/interruption states should include at least:
- BLOCKED
- PAUSED
- DENIED
- FAILED
- CANCELLED

State transitions should be driven by canonical task/runtime events, not only conversational summaries.

## Dispatch provenance requirement

Every autonomous backlog task should carry canonical provenance similar to:

```yaml
origin: autonomous_backlog
backlog_system: hermes-kanban
board_item_id: HK-142
```

Names may change to match existing contracts, but the invariant must remain machine-checkable.

AgentOS should reject an autonomous backlog dispatch when:
- there is no board item ID;
- the referenced item does not exist;
- the item is not in an executable/assignable state;
- required priority/assignment metadata is absent;
- the task's requested scope conflicts with the board item;
- authorization is not valid for the requested action.

Conceptual enforcement:

```python
if task.origin == "autonomous_backlog":
    require(task.backlog_system == "hermes-kanban")
    require(task.board_item_id)
    item = board.get(task.board_item_id)
    require(item is not None)
    require(item.status in EXECUTABLE_BOARD_STATES)
    require(task.scope <= item.approved_scope)
```

The implementation should use existing AgentOS contracts/policies where possible instead of introducing redundant state models.

## Telegram behavior

Telegram should function as command/control over canonical state.

Examples:

- `status` → read live AgentOS/Kanban state.
- `what should we work on next?` → rank eligible board items using board priority/dependencies/policy.
- `prioritize ALVIRA today` → propose or apply board-priority changes within delegated limits.
- `assign the top two ready items` → assign eligible board items and create/link AgentOS tasks.
- `run HK-142` → dispatch that existing board item through AgentOS.
- `pause HK-142` → request a runtime/board pause.
- `stop HK-142` → cancel/revoke through AgentOS according to policy.
- `approve <task>` / `deny <task>` → interact with the real approval lifecycle, not a chat-local flag.

If a user requests work that is not on the board, Milchik should first create/propose a board item and then operate on that canonical item.

## Priority versus execution authority

Priority management and execution authority must remain separate.

Milchik may be delegated authority to reprioritize low-risk work, but moving an item higher in the queue must never itself grant permission to perform consequential actions.

A high-priority item may still require:
- deterministic authorization;
- agent consensus/control checks;
- human escalation;
- scoped approval;
- later revocation.

## Assignment contract

Before execution, the canonical board item should record:
- assigned AgentOS role;
- selected harness if already known;
- AgentOS task/work-item ID;
- authorization state;
- assignment timestamp;
- current execution state.

If the router changes the selected role or harness, that update should be reflected back onto the board or represented as authoritative AgentOS-linked state.

## Completion contract

Execution completion is not sufficient by itself.

Recommended path:

```text
harness output
→ verifier
→ evidence/result record
→ AgentOS terminal state
→ Hermes Kanban update
→ Milchik report
```

A board item should only become `DONE` when the AgentOS completion/verification contract says the work is complete. Failed verification should result in `BLOCKED`, `FAILED`, or another explicit non-DONE state.

## Build/reconciliation checklist for Hermes

Hermes should compare current live behavior against this contract and mark each item:

- IMPLEMENTED
- PARTIAL
- DOCUMENTED_ONLY
- MISSING

Specifically inspect:

1. Where the Hermes Kanban board is stored and what system is currently authoritative.
2. Whether Milchik reads from the board for prioritization.
3. Whether Milchik writes assignment and status changes back to the board.
4. Whether chat-originated work can bypass the board.
5. Whether autonomous AgentOS tasks contain a canonical board item reference.
6. Whether dispatch fails closed when board provenance is absent/invalid.
7. Whether board priority is consulted before autonomous selection.
8. Whether AgentOS authorization remains independent from board priority.
9. Whether pause/stop causes real task cancellation/revocation rather than a conversational acknowledgement.
10. Whether approval/deny/resume acts on the canonical AgentOS approval lifecycle.
11. Whether harness completion flows through verifier/evidence before `DONE`.
12. Whether final task state is written back to the board and visible to Milchik/Telegram.
13. Whether Telegram identity is bound to an authorized AgentOS principal/operator context.
14. Whether the live bot currently duplicates or bypasses canonical AgentOS state.

## Acceptance tests

Do not call this integration complete until at least these tests pass end-to-end:

### A. No-board rejection

Send Milchik a request to autonomously execute a backlog task with no board item.

Expected: no execution begins. Milchik creates/proposes a board item or asks for the work to be admitted to the board.

### B. Board-driven assignment

Create two READY items with known priority.

Ask Milchik to `assign the next item`.

Expected: the highest eligible item is selected from board state, receives an AgentOS task ID/assignment, and execution uses that task.

### C. Scope mismatch rejection

Modify a chat instruction so it requests more authority/scope than the board item declares.

Expected: dispatch is denied/escalated; chat text does not silently widen scope.

### D. Approval/resume

Run a board item that requires human approval.

Expected: task pauses in canonical AgentOS state; approving from Milchik/Telegram creates the scoped approval/grant and resumes the same task.

### E. Stop/revocation

Start an eligible task, then issue `stop` from Milchik.

Expected: canonical execution is cancelled/revoked and the board reflects the terminal/interrupted state.

### F. Verification before DONE

Have a harness return apparent success while verification fails.

Expected: the board does not move to DONE; Milchik reports the verification failure.

## Non-goals

This proposal does not:
- make Milchik the authorization engine;
- make Telegram a source of truth for backlog state;
- require Hermes to be the only execution harness;
- grant autonomous mutation authority by default;
- replace existing AgentOS authorization, routing, task, verification, or evidence contracts where they already fit;
- require a new product surface if the existing Hermes board already satisfies the canonical-board role.

## Architectural shorthand

> **Milchik is the workforce manager. Hermes Kanban is the operating queue. AgentOS is the control plane. Hermes/other harnesses execute. Authorization and verification stay below the conversational layer.**

## Review request

Hermes should use this document during the current repo/live-state reconciliation and either:

1. implement the missing contract pieces;
2. modify this proposal where existing canonical mechanisms already solve the requirement; or
3. explicitly reject individual requirements with evidence from the current runtime.

Prefer adapting existing AgentOS contracts over building parallel infrastructure.
