# Harness routing test plan

Required checks before merge:

1. Implementation tasks select Codex/premium by default.
2. Routine inspection/status selects Hermes/low by default.
3. Verification prefers Claude/premium when independent.
4. Verification excludes agent authors/remediators/material participants under the existing verifier rule.
5. Verification excludes materially participating harnesses and chooses another eligible harness.
6. If no independent verifier/harness is eligible, verification remains BLOCKED.
7. Routing decisions append history without changing task lifecycle status.
8. Execution attempts append history without changing task lifecycle status unless the normal workflow transition explicitly does so.
9. Task state, routing history, execution history, and evidence survive TaskStore reopen/restart.
10. Harness outage/quota failure records an attempt and leaves the task eligible for retry/fallback.
