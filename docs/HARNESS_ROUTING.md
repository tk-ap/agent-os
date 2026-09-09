# Harness routing and autonomous persistence

AgentOS routes work across two independent dimensions:

1. **Agent ownership** — which durable workforce identity owns the task.
2. **Execution harness / intelligence tier** — which replaceable execution resource should perform the current step.

## Core rule

Tasks persist. Agent identities persist. Workflows persist. Harnesses do not.

A Hermes, Codex, Claude, or future harness outage, quota limit, crash, or replacement must not erase task intent, lifecycle state, evidence, routing history, or prior attempts.

## Default harness roles

- **Hermes / low tier**: coordination, status, summarization, classification, routine inspection, explanation.
- **Codex / premium tier**: implementation, debugging, testing, repository changes.
- **Claude / premium tier**: independent verification, architecture review, adversarial review, security review.

These are policy defaults, not permanent product bindings. Harnesses remain replaceable through the registry/policy layer.

## Independence

Existing agent-level verifier independence remains mandatory. Harness-level independence is additive: a harness that materially authored or remediated work is ineligible to independently verify that same work when an alternative eligible harness exists. If no eligible independent verifier is available, verification remains blocked rather than being self-attested.

## Persistence boundary

Routing must never be the source of durable task state. The task store remains the source of truth for lifecycle state and evidence. Routing decisions and execution attempts are appended as durable history alongside, but separate from, task status.

For each routing decision persist at least:

- selected agent
- selected harness
- intelligence tier
- reason
- fallback candidates
- timestamp

For each execution attempt persist at least:

- attempt number
- selected agent
- selected harness
- intelligence tier
- outcome
- timestamp
- relevant execution payload/evidence reference

This allows a task to survive process restarts, model/harness failures, quota exhaustion, or provider substitution and continue from its durable lifecycle state.

## Example

```text
TASK: Fix LEDGATo issue
STATE: IMPLEMENTATION_REQUIRED
agent: eugene
preferred harness: codex

-> Codex attempt recorded
-> implementation evidence saved

STATE: VERIFICATION_REQUIRED
preferred verifier harness: claude

-> Claude unavailable
-> task remains VERIFICATION_REQUIRED
-> failed/unavailable attempt is recorded
-> retry later or select another eligible independent verifier
```

Hermes Desktop, Terminal Velocity, Telegram, schedulers, or future interfaces should consume this AgentOS policy rather than owning their own routing logic.
