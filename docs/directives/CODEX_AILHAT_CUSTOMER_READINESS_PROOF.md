# Codex execution directive — ailhat customer-readiness proof

## Purpose

Execute the approved AgentOS proof work item:

`ailhat-live-scan-customer-readiness-proof`

This is the first real proof of the intended lifecycle from ailhat finding → governed AgentOS execution → independent review → remediation → independent re-review → Milchik founder brief → TK final approval → live verification.

Use AgentOS as the operating layer. Do not replace the lifecycle with an ad hoc Codex workflow.

## Source finding

The work originates from ailhat portfolio intelligence. The current source finding is:

> Restore production reliability/auth and validate the complete live scan loop.

Treat the finding as intelligence, not authority. Re-read the live/current product state before acting and close/defer the work if the finding is no longer valid.

## Required execution sequence

1. Pull the latest `main` for `tk-ap/agent-os` and the relevant product repository.
2. Locate the approved AgentOS backlog item `ailhat-live-scan-customer-readiness-proof`.
3. Re-read the originating ailhat finding and confirm the work is still needed against current ecosystem conditions, current product state, dependencies, and founder priorities.
4. Define explicit acceptance criteria before mutation. Acceptance criteria must describe the intended customer-test-ready outcome and the relevant regression boundaries.
5. Resolve the correct product workspace, one accountable AgentOS owner, and the minimum sufficient support/reviewer set.
6. Execute only the approved work required to satisfy the acceptance criteria.
7. The executor must self-verify before asking another agent to review. A successful CLI exit, code change, commit, or passing narrow test is not sufficient by itself.
8. Hand the completed work to a distinct secondary AgentOS reviewer selected for the primary risk surface.
9. The secondary review must be meaningful. It must check for defects, regressions, drift, unsupported claims, incomplete acceptance criteria, missing verification, and product/customer-readiness issues.
10. If issues are found, remediate them. Do not ignore valid findings merely to preserve the original implementation.
11. If the secondary reviewer authors or directs remediation that materially changes the result, that reviewer may not provide the final independent approval. Route the remediated result to a distinct third AgentOS reviewer or human verification.
12. Re-run relevant verification after remediation.
13. Perform a release/customer-test-readiness check before requesting a final push.
14. Route the final founder-facing readiness brief through Milchik to TK.
15. Do not push, merge, deploy, publish, widen permissions, make a purchase, change credentials, or take another protected consequential action without the required scoped approval.
16. After any approved final action, verify the actual live/user-facing state before marking the work DONE.
17. Return outcome evidence to the AgentOS task/board and preserve what was learned for future ailhat/AgentOS decisions.

## Milchik final brief

Before TK is asked to approve the final action, Milchik's plain-language brief must state:

- what changed;
- why the work was still needed;
- the acceptance criteria used;
- who executed the work;
- who independently reviewed it;
- issues the reviewer found;
- what was remediated;
- who independently re-verified the remediated result when required;
- tests/checks/live verification already completed;
- remaining risks or limitations;
- whether the result is `BUILD_COMPLETE`, `CUSTOMER_TEST_READY`, or neither;
- the exact final action requiring TK approval.

## Non-negotiable rules

- ailhat proposes work; ailhat does not authorize work.
- Revalidate before execution even though the backlog item is approved.
- Define done before building.
- Maintain one accountable owner.
- Use the minimum sufficient workforce.
- Do not let the same reviewer both remediate and provide final independent approval when reviewer-authored remediation occurred.
- Do not report completion because code changed, a PR exists, tests passed, or a deployment completed.
- Completion requires evidence of the intended resulting state.
- Preserve the distinction between proposed, attempted, implemented, reviewed, remediated, re-verified, deployed, live-verified, and customer-test-ready.
- Do not widen authority because Codex has access to more tools.

## Runtime-gap behavior

This proof is also intended to expose missing AgentOS runtime behavior.

If AgentOS cannot represent or enforce a required lifecycle stage cleanly — especially reviewer remediation, distinct third review, customer-test-readiness state, or final founder routing — do **not** silently bypass AgentOS and simulate the step in prose.

Instead:

1. stop at the exact unsupported transition;
2. record what the runtime currently supports;
3. identify the missing state/transition/contract;
4. propose the smallest implementation needed to close that gap;
5. preserve the original task and evidence so it can resume after the runtime fix.

## First response to TK

Before substantive mutation, report these five items:

1. the current source ailhat finding;
2. whether it is still valid and why;
3. the explicit acceptance criteria;
4. the planned accountable owner → secondary reviewer → final verifier chain;
5. the exact first execution step.

Do not ask TK to restate this directive. This file is the execution directive.