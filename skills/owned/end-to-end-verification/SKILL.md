---
name: end-to-end-verification
description: Verify a complete user or agent outcome across interface, API, data, authorization, execution, deployment, and evidence boundaries. Use before declaring a feature, integration, fix, or production release complete.
---

# End-to-End Verification

Test the promised outcome, not only the changed component.

## Verification Story

Define:

- actor and starting state;
- promised outcome;
- critical path and protected regression boundaries;
- expected authorization decisions;
- state changes and evidence produced;
- failure, retry, and rollback behavior;
- environments to compare.

## Workflow

1. Confirm the deployed commit and target environment.
2. Exercise the path from the actual entry point using realistic state.
3. Inspect interface behavior, console/network errors, API responses, persisted state, permission enforcement, and downstream effects.
4. Test at least one relevant failure or denial path.
5. Check mobile/accessibility/performance when they are part of the promise.
6. Re-run protected regression paths affected by the change.
7. Capture evidence and classify the result as `verified`, `partially-verified`, `failed`, or `blocked`.

## Rules

- A successful build or HTTP 200 is not sufficient when the product flow remains unusable.
- A preview deployment is not production verification.
- Simulated data must remain visibly labeled.
- Do not claim backend enforcement based only on frontend behavior.
- Report exact blockers and untested boundaries.

## Output

Return the story tested, environments and commit, evidence, failures, regression results, and final verification state.
