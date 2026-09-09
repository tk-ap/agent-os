# PR 69 implementation checklist

- [x] Add second routing dimension: execution harness / intelligence tier.
- [x] Preserve existing agent-level independent-verifier selection.
- [x] Add harness-level independence metadata and selection.
- [x] Keep task persistence separate from routing logic.
- [x] Persist routing decisions separately from task lifecycle status.
- [x] Persist execution attempts separately from task lifecycle status.
- [x] Document harness replaceability and continuation guarantees.
- [x] Add policy defaults for Hermes / Codex / Claude.
- [x] Add tests/test plan covering routing, independence, persistence, and restart behavior.
- [ ] Run repository test suite and independent review before merge.
