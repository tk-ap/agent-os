---
name: task-envelope
description: Turn a signal, objective, or request into a governed unit of work with ownership, context, authority, budget, success criteria, and verification. Use before cross-agent or externally mutating execution.
---

# Task Envelope

Create the smallest complete work packet an agent can execute safely.

## Required Fields

- objective and expected user/business outcome;
- originating signal and evidence;
- accountable owner and executing agent(s);
- repositories, environments, and exact targets;
- relevant context plus provenance;
- constraints and protected regression boundaries;
- permitted actions and required approvals;
- estimated execution cost and human oversight;
- success criteria, verification method, and evidence destination;
- stop conditions, rollback, and handoff state.

## Rules

- Missing authority is not an implementation detail. Pause before the mutation.
- Keep inferred context distinguishable from supplied or verified context.
- Do not broaden the target because adjacent work appears useful.
- Prefer reversible steps and preview branches for uncertain public-facing changes.
- A task is not complete when code exists; it is complete when the intended result is verified.
- ailhat findings enter the workforce as proposed task envelopes, not direct commands.

## Routing

Router classifies and coordinates. Steward owns objective priority. Bill owns sequencing. Ledger owns budget analysis. Rook owns adversarial and permission review. Eugene owns implementation. W Dog owns independent verification and contradiction detection.

## Output

Return the task envelope, missing fields, authorization state, and the next permitted action.
