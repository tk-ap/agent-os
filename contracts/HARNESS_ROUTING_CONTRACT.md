# Harness Routing Persistence Contract

## Separation of concerns

- Task lifecycle state is durable and owned by persistence.
- Agent ownership is durable workforce identity.
- Harness selection is an execution-time routing decision.
- A harness outage or replacement must not mutate or erase task intent/state.

## Required routing record

Each routing decision must be persistable with:
- task id
- agent
- harness
- intelligence tier
- reason
- fallback candidates
- timestamp

## Required attempt record

Each execution attempt must be persistable with:
- task id
- attempt number
- agent
- harness
- intelligence tier
- outcome
- timestamp
- evidence/reference payload when available

## Verifier independence

Agent-level verifier independence remains mandatory. Harness-level independence is additive. A harness that materially authored, remediated, or participated in the work is ineligible to independently verify it when another eligible harness exists. If independence cannot be satisfied, verification remains blocked.

## Continuation guarantee

A failed or unavailable harness must not complete, cancel, or forget a durable task. The task remains in its lifecycle state until a later eligible execution attempt changes that state through normal evidence-backed workflow transitions.
