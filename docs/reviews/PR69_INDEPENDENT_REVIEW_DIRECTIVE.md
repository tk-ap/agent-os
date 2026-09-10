# PR #69 Independent Review Directive

Review **AgentOS PR #69** as the independent verifier. Do not implement changes unless TK explicitly asks you to after the review.

## Scope

Review the following requirements against the actual implementation and tests:

- second routing dimension: **execution harness / intelligence tier**
- preserve existing **verifier-independence**
- keep **routing and persistence separate**
- persistence must store **routing decisions and execution attempts**, not only task status
- verify that harnesses are replaceable execution resources and do not become the source of durable task state
- verify that Codex / Claude / Hermes routing does not weaken autonomous persistence
- verify that a harness outage, quota exhaustion, crash, or restart does not cause task loss
- verify that self-review is blocked at both the **agent** and **harness** level where materially applicable

Also inspect the test setup changes around:

- `make test`
- dependency installation
- CI
- the ASHWOOD canonical repository binding

## Required classification

Distinguish findings as:

1. code defects
2. test-environment/setup defects
3. stale configuration/data
4. architectural risks

## Required output

Return:

- **PASS / PASS WITH CONDITIONS / FAIL**
- blocking findings
- non-blocking findings
- exact files/lines involved
- whether PR #69 is safe to merge
- any follow-up tests required before merge

## Review standard

Do not approve based on intent, comments, or documentation alone. Verify implementation against the code and tests.

The reviewer should remain independent. If the reviewer materially participates in remediation after this review, a fresh independent verification pass is required before merge.
