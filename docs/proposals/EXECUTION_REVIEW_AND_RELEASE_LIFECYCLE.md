# AgentOS Execution, Review, and Release Lifecycle

## Purpose

AgentOS exists to convert useful work signals into verified product progress without requiring the founder to act as orchestration glue.

For the current ecosystem, a major input is ailhat portfolio intelligence: findings about Opportunity, Risk, Drift, or Work that may help ALVIRA, ailhat, LEDGATo, or other governed products reach customer-test readiness. Those findings are proposals for work, not commands.

The canonical lifecycle is:

```text
DISCOVER / RECEIVE WORK
→ REVALIDATE
→ DEFINE DONE
→ AUTHORIZE
→ EXECUTE
→ SELF-VERIFY
→ INDEPENDENT REVIEW
→ REMEDIATE IF NEEDED
→ INDEPENDENT RE-VERIFY
→ RELEASE-READINESS CHECK
→ MILCHIK FOUNDER BRIEF
→ TK APPROVAL WHEN REQUIRED
→ SHIP / FINAL EXTERNAL ACTION
→ VERIFY LIVE RESULT
→ CLOSE + LEARN
```

## Core invariant

> **No work is complete because an agent says it is complete. Completion requires evidence, independent review, and verification of the actual resulting state.**

A merged PR, passing local test, or successful command is not by itself proof that the customer-facing outcome is correct.

---

## 1. Discover / receive work

Work may originate from:

- ailhat finding;
- explicit founder directive;
- existing backlog item;
- customer evidence;
- product telemetry or failure evidence;
- recurring-work output;
- governed cross-product handoff.

Normalize the signal into a governed work item/task with at minimum:

- owning product;
- intended outcome;
- source signal and evidence;
- urgency / timing context;
- known constraints;
- known human gates.

ailhat intelligence may propose work but does not grant execution authority.

---

## 2. Revalidate before execution

Before spending meaningful execution effort, confirm the work is still needed against current ecosystem conditions.

Revalidation should consider:

- current product state;
- current founder priorities / objective lease;
- customer and market evidence;
- recent product decisions;
- dependencies and blockers;
- duplicate or superseding work;
- opportunity cost and expected value;
- whether the original finding is stale;
- whether another product or agent already resolved the underlying issue.

Possible outcomes:

- `ACCEPT`
- `DEFER`
- `REJECT`
- `SUPERSEDED`
- `ALREADY_RESOLVED`

Do not execute stale ailhat findings merely because they remain in a queue.

---

## 3. Define done before execution

Every material task must have explicit acceptance criteria before implementation begins.

Acceptance criteria should define:

- intended user/business outcome;
- required functional behavior;
- protected behavior that must not regress;
- tests/checks required;
- evidence required;
- customer-readiness target where applicable;
- deployment or release expectation;
- known non-goals / scope boundaries.

Reviewers must be able to test the result against a defined target rather than asking whether the work merely “looks okay.”

---

## 4. Authorize

Confirm that execution is allowed within the task envelope.

Authorization may include:

- product/workspace scope;
- mutable surfaces;
- tool/harness access;
- budget/cost limit;
- external-action boundary;
- required human approval;
- release/deploy authority.

Context and intelligence do not grant authority.

---

## 5. Assign minimum sufficient team

Every task has one accountable owner.

Supporting roles are selected only when they materially improve:

- quality;
- speed;
- risk control;
- verification;
- context fit;
- tool fit.

Reviewer selection should be driven by the primary failure risk, not a fixed reviewer sequence.

Examples:

```text
UI / onboarding:
Eugene → Designer → W Dog or TK

authorization / security:
Eugene → Rook → W Dog or TK

economics / pricing:
Scout or Zoie → Ledger → Steward or TK

workflow architecture:
Bill → Eugene → W Dog or TK
```

---

## 6. Execute

The accountable owner performs the work inside an explicit execution context.

Requirements:

- isolated workspace / branch where mutation occurs;
- no silent widening of scope;
- evidence captured during execution;
- failures classified and recovered through the self-healing/reconciliation path where possible;
- original objective preserved across retries and recovery.

---

## 7. Primary self-verification

The executor must verify their own work before independent review.

Self-verification should include all acceptance criteria that the executor can reasonably test, including relevant:

- tests;
- builds;
- previews;
- browser checks;
- API checks;
- data checks;
- regression checks;
- evidence capture.

The independent reviewer is not a substitute for basic executor QA.

---

## 8. Independent secondary review

A second agent performs a meaningful independent review.

The review must be capable of finding defects, drift, missing requirements, unsafe assumptions, regressions, or misleading evidence.

The reviewer should receive:

- task intent;
- acceptance criteria;
- implementation/change evidence;
- verification evidence;
- relevant product/context constraints.

The reviewer should not simply echo the executor's conclusion.

When safe and authorized, the reviewer may remediate issues they find.

---

## 9. Remediation loop

If the secondary reviewer changes the work, they now share authorship of the resulting state.

Therefore the reviewer who remediated must not be the final approver of their own remediation.

Required pattern:

```text
A executes
→ B independently reviews
→ B finds issue and remediates
→ tests/evidence rerun
→ C or human independently re-verifies
```

Never:

```text
B finds issue
→ B fixes it
→ B declares final success
```

After remediation:

- rerun affected tests;
- regenerate relevant evidence;
- verify no new drift was introduced;
- preserve review/remediation lineage.

---

## 10. Independent final re-review

After any remediation, a third agent or human independently verifies the final state.

This check should answer:

- were the discovered issues actually fixed?;
- were acceptance criteria still satisfied?;
- did remediation introduce new regressions?;
- is the evidence current and sufficient?;
- is there material residual risk?

A third agent can verify correctness/readiness. It does not automatically own final release authority.

---

## 11. Release-readiness check

Before requesting final founder approval for a material push, confirm readiness.

Minimum checks where applicable:

- required tests pass;
- deployment state is known;
- product/context documentation is current enough for the change;
- customer-facing claims match real capability;
- unresolved risks are explicit;
- rollback/recovery path exists where consequential;
- relevant telemetry/evidence exists;
- known limitations are documented;
- no blocker-level defect remains.

### Customer-test readiness state

For work whose objective is to prepare a product for real customer testing, distinguish:

```text
BUILD_COMPLETE
→ CUSTOMER_TEST_READY
```

`CUSTOMER_TEST_READY` means the core promise is demonstrably usable by a real test customer, not merely implemented in code.

It should normally require:

- core promise works end-to-end;
- critical user flows pass;
- onboarding is usable;
- no known blocker-level defect;
- public/product claims match actual capability;
- basic observability/feedback capture exists;
- test-user instructions or guidance exist;
- known limitations are explicit;
- consequential changes have rollback/recovery coverage.

---

## 12. Milchik founder brief

Milchik is the human↔fleet operational liaison for the final push decision.

Milchik does not independently decide product strategy, correctness, authorization, or release priority.

For material final approval, Milchik should present TK with a concise founder brief containing:

- what changed;
- why the work was still worth doing;
- which acceptance criteria were satisfied;
- who executed;
- who independently reviewed;
- issues found;
- remediation performed;
- who re-verified the remediated state;
- current deployment/release state;
- residual risk / known limitations;
- exact action requiring TK's approval.

The founder should not need to reconstruct the agent history to make the decision.

---

## 13. Final approval and release

Final review and final approval are distinct.

- **Final review** asks: is this result correct, safe, and ready?
- **Final approval** asks: should we actually ship / deploy / publish / commit the consequential external action now?

TK retains approval for material pushes unless authority has been explicitly delegated within policy.

Milchik routes the approval request; Milchik does not manufacture approval.

---

## 14. Post-action verification

After deploy/publish/release/external action, verify the actual resulting state.

Examples:

- live product behavior;
- production route availability;
- customer-facing experience;
- deployed API behavior;
- entitlement behavior;
- observable external effect.

Do not treat merged code or successful deployment commands as equivalent to a verified live result.

---

## 15. Close and learn

After successful post-action verification:

- update Hermes Kanban / governed task state;
- record evidence;
- update product state;
- update relevant ALVIRA/AgentOS context or canonical product instructions when needed;
- record repeated defects for W Dog/systemic prevention;
- return useful outcome evidence to ailhat when relevant;
- retire obsolete findings and duplicate backlog items;
- preserve lessons that should alter future routing, repair, or review.

Completion should reduce future ambiguity and repeated work.

---

## Reviewer independence rules

1. An executor may self-verify but may not serve as the only independent reviewer.
2. A reviewer who materially remediates the implementation may not give the final independent approval of that remediated state.
3. Reviewer selection should align with the dominant risk surface.
4. Review must use current evidence, not stale screenshots/tests/claims.
5. Consensus is not evidence; preserve disagreement and unresolved uncertainty.
6. Low-risk trivial changes may use a lighter path if policy explicitly permits it, but the system must not silently downgrade material work to avoid review.

---

## Relationship to existing AgentOS layers

This lifecycle composes with, rather than replaces:

- `EXECUTION_CONTEXT_AND_WORKSPACE_ISOLATION.md` for mutation/workspace safety;
- `MINIMUM_SUFFICIENT_TEAM_AND_DELEGATION.md` for team composition and bounded delegation;
- `AUTONOMOUS_OPERATING_GUARDRAILS.md` for objective leases, rollback, evidence freshness, and autonomy controls;
- `SELF_HEALING_RECONCILIATION_AND_FOUNDER_MODE.md` for automatic recovery from menial operational failures;
- authorization/governance policy for consequential actions;
- ailhat Portfolio Intelligence as a source of proposed work;
- Milchik as founder-facing operational liaison.

Do not create a new persistent “QA agent” or “release manager” solely to implement this lifecycle. Use existing role ownership plus task-state/reviewer-selection policy.

---

## Canonical state progression

A detailed implementation may use more granular states, but it should preserve the semantics of:

```text
PROPOSED
→ REVALIDATING
→ ACCEPTED / DEFERRED / REJECTED / SUPERSEDED
→ READY
→ RUNNING
→ SELF_VERIFYING
→ INDEPENDENT_REVIEW
→ REMEDIATING (if needed)
→ FINAL_REVIEW
→ RELEASE_READY
→ AWAITING_FOUNDER_APPROVAL (when required)
→ RELEASING
→ LIVE_VERIFYING
→ DONE
```

Recovery may temporarily enter `RECOVERING` / `RESUMING` without losing the original task identity.

---

## Success condition

The lifecycle is functioning when AgentOS can take a still-valid ailhat finding, execute it against current product reality, independently review and remediate it, obtain independent re-verification after remediation, present TK with a compact Milchik approval brief, ship only with required authority, verify the real live result, and close the loop with evidence — without TK acting as the workflow coordinator.