# Morning live deployment brief — 2026-09-07

Use this as the execution brief for Hermes when deploying the work completed this morning.

## Goal

Deploy everything completed this morning to the live environment, carefully and with explicit verification at each step.

## Instructions

Start by pulling the latest canonical `main` branches for the affected repositories and identify exactly what changed today. Do not deploy anything unrelated.

For each affected product or service:

1. Confirm the intended branch and current live target.
2. Run the relevant tests/checks first.
3. Verify there are no uncommitted or conflicting local changes.
4. Deploy only the reviewed changes.
5. Verify the live result after deployment.
6. Report anything that did not deploy cleanly instead of forcing it through.

### AgentOS / Milchik

Make sure the newly merged human-first Telegram runtime is actually loaded on the workstation.

- Pull the latest `main` for `tk-ap/agent-os`.
- Run the existing Telegram E2E path.
- Restart the Milchik listener if needed so the new runtime is loaded.
- Confirm that new review messages use the updated human-first format.
- Confirm the primary controls behave as intended: **Approve / Needs work / Pause / Explain** where applicable.
- Confirm **Explain** is read-only and does not approve, resume, publish, deploy, or widen authority.
- Confirm approval confirmations use plain language rather than raw queue/task/runtime terminology.

### ALVIRA / LEDGATo / ailhat / ASHWOOD

For any changes from this morning, apply the same rule:

- test first;
- deploy only the intended reviewed changes;
- verify the live surface after deployment;
- verify the relevant core regression boundaries;
- do not infer that a commit or merge means the change is live.

## Final deployment report

Return a final report with these exact sections:

### Deployed and verified

Changes confirmed live and working as intended.

### Deployed but not yet verified

Changes that were deployed but for which live verification is incomplete.

### Blocked / needs TK's decision

Anything requiring a human decision before continuing.

### Not deployed

Anything intentionally skipped, failed, or found outside the reviewed scope.

## Stop conditions

Stop and ask TK before proceeding if any step would:

- publish something unexpected;
- overwrite newer work;
- widen permissions or authority;
- force-push or otherwise bypass a safety check;
- touch a production surface outside the reviewed scope;
- deploy work whose intended live target is ambiguous;
- mix unrelated local changes into the deployment.

Do not treat **commit exists**, **PR merged**, or **code pulled** as equivalent to **live and verified**.
