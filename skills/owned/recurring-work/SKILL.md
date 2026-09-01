---
name: recurring-work
description: Define recurring or scheduled agent work as a governed, bounded routine with explicit trigger, skip conditions, authority, cost limits, failure controls, verification, and termination. Use before implementing repeated automation.
---

# Recurring Work

Turn repeated work into a safe, inspectable routine without coupling Agent OS to one scheduler, host, model provider, or orchestration platform.

This skill defines the routine contract. It does not itself schedule jobs, grant authority, hold credentials, or execute production mutations.

## Ownership

- **Bill** is primary owner for routine design, sequencing, dependencies, and operational readiness.
- **Rook** reviews failure modes, permissions, irreversible effects, abuse paths, and escalation boundaries.
- **Ledger** owns cost assumptions, run budgets, spend caps, and economic thresholds.
- **W Dog** owns independent verification design, anomaly/recurrence checks, and evidence of closure.
- **Router** decides when recurring-work is required and coordinates the minimum sufficient reviewers.

## Required Routine Contract

Every routine must define:

- purpose and expected outcome;
- originating objective or task-envelope reference;
- trigger type and cadence/event condition;
- explicit skip/no-op condition;
- data/context sources and provenance expectations;
- processing steps at the level required for verification;
- output destination and externally visible side effects;
- authority class and approvals required before mutation or delivery;
- concurrency and duplicate-execution policy;
- idempotency or reconciliation strategy where repeated effects are possible;
- dry-run/staging path for new or materially changed routines;
- validation rules for generated output;
- retry policy and retry ceiling;
- circuit breakers for steps, tokens, time, cost, or side-effect count as applicable;
- anomaly conditions that pause or escalate rather than continue silently;
- per-run and recurring-period cost assumptions and caps when material;
- human review requirements and the criteria for reducing or restoring review;
- success criteria and verification method;
- evidence destination and audit trail;
- stop conditions, suspension path, rollback/reversal path where possible;
- loop termination and human escalation conditions.

## Composition With Task Envelope

Recurring work must compose with `skills/owned/task-envelope/SKILL.md` rather than replace it.

The task envelope defines **what governed work is permitted**. Recurring-work defines **how that permitted work may repeat safely**.

If the routine would mutate an external system, send/publish content, spend money, access sensitive data, or touch production, it must also compose with `skills/owned/authorization-policy/SKILL.md`.

## Guardrails

- A schedule is not authority. Repetition never upgrades permissions.
- Previous successful delivery does not imply indefinite authorization for a changed target, audience, scope, or sensitivity level.
- Every routine needs a skip/no-op path; absence of work must not produce filler output or unnecessary side effects.
- New routines default to dry-run, draft, preview, or human-review mode when the consequence of a false positive is material.
- Retries must be bounded and must not duplicate externally visible effects after an ambiguous timeout.
- Repeated agent-to-agent review must have a maximum cycle count and a named escalation owner.
- A routine must pause when cost, volume, output shape, target scope, or evidence materially departs from its expected envelope.
- Secrets and credentials remain in the host/provider secret system; routine specs may reference required credentials but never store them.
- Scheduler-specific configuration belongs in an adapter or product environment, not in this core skill.

## Host-Agnostic Execution

The same routine contract should be implementable through different execution environments, for example a local host scheduler, GitHub Actions, Vercel/cloud scheduling, or another approved automation platform.

Choosing the scheduler is an implementation decision owned by the relevant host/product adapter and does not change the routine's governance requirements.

## Review Flow

Use the minimum sufficient review path:

1. Router identifies recurring-work need.
2. Bill drafts the routine contract.
3. Rook reviews material failure/permission risk.
4. Ledger reviews material recurring cost/budget exposure.
5. W Dog defines independent verification and anomaly evidence.
6. Authorization is resolved before consequential execution.
7. Implementation occurs in the appropriate host/product adapter.
8. Verification evidence determines continue / change / suspend / stop.

Skip reviewers whose domain is immaterial, but never skip a required authority gate.

## Output

Return:

- the routine contract;
- missing fields and assumptions;
- authority state;
- required reviewers;
- implementation environment still to be selected or confirmed;
- verification and evidence plan;
- the next permitted action.

## Source Note

This owned capability was informed in part by user-supplied `agent-routine-builder` reference material. The source package remains non-executable reference material in Agent OS until provenance, license, referenced-file layout, and external claims are independently resolved. Agent OS policy, ownership, authorization, and verification rules are authoritative when the source material conflicts or overreaches.
