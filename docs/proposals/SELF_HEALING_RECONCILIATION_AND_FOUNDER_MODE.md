# Self-Healing Reconciliation and Founder Mode

> Status: proposal/build spec for Agent OS runtime reconciliation.
>
> Goal: eliminate founder babysitting for operational failures Agent OS can deterministically diagnose and repair, while preserving human control over authority, intent, irreversibility, material economics, and strategic trade-offs.

## Core outcome

Agent OS should converge from observed failure back to desired state without requiring TK to notice the failure first.

Target loop:

`DESIRED STATE → OBSERVE ACTUAL STATE → DIFF → CLASSIFY → REPAIR IF AUTHORIZED → RESUME SAME TASK → VERIFY → RECORD INCIDENT → LEARN`

The system is not considered self-healing merely because an agent can explain a failure or open a repair PR. The original governed objective/task must recover or escalate with a specific non-repairable reason.

## 1. Deterministic reconciler, not a new agent

Implement self-healing as control-plane/runtime capability. Do not add a durable `self-healing`, `supervisor`, or similar agent solely to own recovery.

Existing roles participate only when specialist judgment is required:

- Bill: workflow/sequencing failures
- W Dog: recurrence/systemic defects/root cause
- Eugene: implementation/runtime repair
- Router: unresolved ownership/routing
- Steward: objective/priority conflict
- Ledger: economics/cost runaway
- Rook: security/authority/irreversibility
- Milchik: founder-facing status/escalation

LLM judgment may diagnose or propose a repair, but deterministic state/authority checks decide whether that repair may run.

## 2. Desired-state record

For governed execution, capture the minimum expected operating state needed to continue safely, including where applicable:

```yaml
desired_state:
  product:
  task_id:
  accountable_owner:
  execution_mode:
  workspace:
  required_capabilities: []
  required_context_refs: []
  authorization_state:
  objective_lease:
  evidence_destination:
  verification_required: true
```

The reconciler compares this record with actual runtime state before and after repair attempts.

## 3. Failure taxonomy

Failures must be machine-readable. Minimum classes:

### Infrastructure
- `HARNESS_UNAVAILABLE`
- `HOST_UNAVAILABLE`
- `CAPACITY_EXHAUSTED`
- `CONNECTOR_UNAVAILABLE`
- `WORKSPACE_MISSING`
- `PERSISTENCE_FAILURE`

### Workflow
- `WRONG_WORKSPACE`
- `WRONG_HARNESS`
- `MISSING_CAPABILITY`
- `STALE_LOCK`
- `ORPHANED_TASK`
- `INVALID_STATE_TRANSITION`
- `ROUTING_LOOP`
- `MISSING_BOARD_PROVENANCE`

### Context
- `MISSING_PRODUCT_CONTEXT`
- `STALE_CONTEXT`
- `WRONG_PRODUCT_CONTEXT`
- `BOOTSTRAP_NOT_LOADED`
- `CANONICAL_PATH_UNREACHABLE`
- `CONTEXT_SCOPE_INSUFFICIENT`

### Clarity
- `AMBIGUOUS_OUTCOME`
- `CONTRADICTORY_REQUIREMENTS`
- `MISSING_ACCEPTANCE_CRITERIA`
- `UNKNOWN_PRODUCT_OWNER`
- `UNRESOLVED_DEPENDENCY`

### Authority
- `MISSING_GRANT`
- `EXPIRED_GRANT`
- `SCOPE_MISMATCH`
- `HUMAN_APPROVAL_REQUIRED`
- `REVOKED`

### Product/result
- `TEST_FAILURE`
- `BUILD_FAILURE`
- `REGRESSION`
- `DEPLOYMENT_FAILURE`
- `VERIFICATION_FAILURE`

Failure classes should compose with concrete evidence and root-cause detail; prose alone is insufficient for recoverable runtime faults.

## 4. Repair catalog

Known recoverable failure classes should map to versioned deterministic repair plans.

Example:

```yaml
repair_rule:
  failure_class: WRONG_WORKSPACE
  version: 1
  auto_eligible: true
  steps:
    - resolve product from canonical routing
    - resolve registered workspace
    - verify workspace exists
    - rebind task execution context
    - retry same task
  human_required: false
```

Rules:

- repair may never widen authority, context release, budget, mutable surfaces, or credentials;
- fallback must come from declared eligible paths;
- every automatic repair has bounded attempts/cost/time;
- failed repair falls back to another approved rule or escalates;
- authorization failures are never healed by self-granting authority;
- strategic ambiguity is never healed by inventing founder intent.

## 5. Same-task recovery lifecycle

Operational repair should preserve the original task and objective lineage.

Required lifecycle extension:

`RUNNING → RECOVERING → RESUMING → RUNNING/VERIFYING → DONE`

or

`RUNNING → RECOVERING → BLOCKED/WAITING_APPROVAL`

A repair should not silently create a replacement task unless recovery requires a distinct governed work item. Recovery records must reference the original task, incident, repair version, attempt count, and resulting state.

## 6. Context and clarity resolver

Before escalating a context/clarity failure to TK, Agent OS must attempt deterministic resolution from canonical sources:

1. applicable bootstrap/load path;
2. product routing/metadata;
3. current objective lease and intent version;
4. active execution context/workspace registry;
5. relevant fresh evidence;
6. accepted task/work-item and acceptance criteria.

Only ask TK when required information cannot be established from canonical state or when multiple valid interpretations require founder preference.

## 7. Incident memory

Every recovery attempt creates or updates a durable incident record:

```yaml
incident:
  incident_id:
  task_id:
  failure_class:
  symptom:
  root_cause:
  repair_rule:
  repair_version:
  attempts:
  recovered:
  recurrence_key:
  first_seen:
  last_seen:
  evidence_refs: []
```

The record is operational evidence, not agent self-report.

## 8. Recurrence escalation

Repeated successful repair is not success if the same defect keeps recurring.

Default progression:

`FIRST OCCURRENCE → repair`

`REPEAT → repair + recurrence increment`

`THRESHOLD EXCEEDED → W Dog root-cause work item`

A recurring defect should become systemic repair work when recurrence/cost/intervention thresholds are crossed. The root-cause fix must be verified against the recurrence key before the system marks the defect retired.

## 9. Founder Mode

Define an operator profile `FOUNDER_MODE` for TK.

Agent OS should interrupt the founder only when one of these is true:

1. **Authority** — required action is not authorized or requires human approval.
2. **Intent** — current desired outcome cannot be resolved from canonical intent/objective state.
3. **Irreversibility** — material action cannot be safely reversed and policy requires a human gate.
4. **Material economics** — spend/exposure crosses configured threshold.
5. **Strategic trade-off** — multiple valid paths require founder preference.
6. **Safety/security** — policy requires explicit human judgment.

Operational failures such as wrong workspace, stale lock, known harness fallback, missing known context, retry mechanics, recoverable capacity issues, and routine state reconciliation should not interrupt TK before self-recovery is attempted.

Milchik should classify founder messages as:

- `FYI_RECOVERED`
- `FYI_DEGRADED`
- `DECISION_REQUIRED`
- `APPROVAL_REQUIRED`
- `STRATEGIC_INPUT_REQUIRED`

Default after successful self-heal: notify after recovery, not before.

## 10. Founder Intervention Rate

Track:

`Founder Intervention Rate = governed tasks requiring TK intervention / governed tasks`

Also classify intervention cause:

### Legitimate
- founder intent/strategy
- authorization/approval
- material spend
- irreversible action
- safety/security gate

### Avoidable system failure
- wrong workspace/harness
- missing canonical context
- stale/orphaned task state
- known retry/fallback mechanics
- missing load-path resolution
- previously known repair not applied

Primary target: **zero founder interruptions for failures Agent OS could have deterministically resolved itself.**

## 11. Repair promotion lifecycle

Do not let the system permanently self-author repair authority from one successful improvisation.

Use:

`UNKNOWN FAILURE → diagnose → proposed repair → verified repair → incident evidence → candidate repair rule → shadow validation → approved automatic repair`

Known low-risk deterministic repairs may be approved directly when evidence and policy justify it. New high-impact repair behavior should use shadow mode before automatic activation.

## 12. Workforce Health integration

Self-healing telemetry feeds workforce health. Flag at minimum:

- unrecovered incidents;
- repeated recurrence keys;
- repair-loop exhaustion;
- mean recovery attempts/time;
- repair cost;
- context-resolution failures;
- avoidable founder interventions;
- repair rules with falling success rates;
- degradation requiring fallback too frequently.

`UNKNOWN` remains distinct from `HEALTHY` when observability is insufficient.

## 13. Acceptance tests

1. Wrong product workspace is detected, repaired, and the same task resumes without TK intervention.
2. Eligible harness capacity failure rotates to an approved compatible harness and resumes without widening authority.
3. Missing canonical product context is resolved through the load path before execution continues.
4. Missing founder intent cannot be inferred and correctly escalates instead of inventing an objective.
5. Missing/expired authorization pauses for approval rather than self-granting.
6. Successful automatic repair records an incident and repair evidence.
7. Repeated recurrence crosses a threshold and creates W Dog root-cause work instead of endlessly repairing.
8. Failed repair attempt is bounded and escalates with a named reason.
9. Founder Mode sends `FYI_RECOVERED` only after a recoverable menial incident is resolved.
10. Founder Intervention Rate distinguishes legitimate founder decisions from avoidable system interruptions.

## 14. Immediate real-world proof target

Use a real ALVIRA, ailhat, or LEDGATo governed task. Demonstrate:

1. task begins normally;
2. a real operational fault occurs;
3. Agent OS detects/classifies it before TK intervenes;
4. reconciler applies an approved repair;
5. original task resumes;
6. verification passes;
7. incident/evidence persist;
8. TK receives an after-the-fact recovery summary.

This proof is more important than additional control-plane abstraction.

## Non-goals

Do not add:

- another supervisor/self-healing persona;
- unconstrained autonomous self-modification;
- permission self-escalation;
- hidden retries with no evidence;
- infinite repair loops;
- a parallel backlog for incidents;
- continuous model sessions solely to appear self-aware.
