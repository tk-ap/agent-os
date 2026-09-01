# User-Supplied Agent Skills Suite — Source Review

Date reviewed: 2026-09-01
Status: reviewed reference material; non-executable
Trust: candidate/reference
License: unresolved
Runtime approval: none

## Supplied Artifacts

- `Agent Routine Builder Skill-20260901T213926Z-1-001.zip`
- `Agent Persona SKILL-20260901T213924Z-1-001.zip`
- `Agent Org Chart SKILL-20260901T213921Z-1-001.zip`
- `AI Agent INSTRUCTIONS.md`

The accompanying instructions describe three portable skills:

- `agent-routine-builder`
- `agent-persona-builder`
- `agent-org-planner`

The guide presents them as usable with Claude Code, Codex CLI, Paperclip, Cursor, OpenClaw, or other prompt-capable orchestrators.

## Review Findings

### 1. Useful design material

The suite contains concepts that materially strengthen Agent OS:

- recurring-work specifications with schedules/triggers, skip conditions, output validation, dry runs, bounded retries, circuit breakers, cost caps, and human review;
- persistent-agent identity design with explicit boundaries, decision rules, continuity, handoffs, and first-task validation;
- an agents-vs-skills distinction;
- smallest-sufficient-team guidance;
- producer/inspector review loops;
- explicit ownership and handoff design;
- budget/cost awareness as part of autonomous-work design rather than an afterthought.

### 2. Packaging mismatch

The installation guide says each skill follows this shape:

```text
skill-name/
├── SKILL.md
└── references/
```

The supplied ZIPs instead contain skill and reference Markdown files together within a named folder, while the skill Markdown refers to paths such as `references/memory-systems.md`, `references/org-patterns.md`, and `references/failure-patterns.md`.

A literal install may therefore fail reference resolution depending on the host harness unless the package layout is normalized.

### 3. Provenance and license are not sufficient for vendoring

The supplied guide describes the research chain as a podcast plus Perplexity Deep Research and recent community intelligence. The package includes quantitative and anecdotal claims about coordination, review effectiveness, production failures, and costs.

Those claims may be useful as hypotheses or design prompts, but the supplied files do not establish enough primary-source provenance here to make the numeric claims normative Agent OS policy.

No repository/source license was established during this review. `license: unresolved` therefore remains mandatory until independently verified.

### 4. Platform-specific assumptions

The source material includes Paperclip, Claude Code, OpenClaw, Cursor, cron, GitHub Actions, n8n, and other platform assumptions. Agent OS core must remain host- and orchestrator-agnostic.

Platform-specific implementation belongs in adapters or product environments. Source instructions must not override Agent OS authorization, ownership, supply-chain, verification, secret-handling, or production-access policies.

## Integration Decision

Do **not** copy the three supplied skills into `skills/vendor/` unchanged.

Instead:

1. adapt recurring-work safety into the owned `recurring-work` capability at P0;
2. adapt identity-design principles into the owned `agent-identity-design` capability at P1;
3. strengthen Router/Handoff policy with agents-vs-skills selection, producer/inspector review loops, bounded loop termination, and structured handoffs;
4. retain all three supplied skills as non-executable candidate/reference source material.

## Extracted Ownership

### recurring-work

- Bill — primary routine design and operational readiness
- Rook — failure/permission review
- Ledger — cost boundaries
- W Dog — independent verification
- Router — routing/minimum sufficient review team

### agent-identity-design

Used to create/review persistent identities only when a durable decision or trust boundary justifies one. It must not become a runtime agent factory.

Persistent agent activation remains human-gated.

## Candidate Source Records

### `agent-routine-builder-reference`

- source: user-supplied local package
- trust: candidate/reference
- executable: false
- license: unresolved
- disposition: adapt selected concepts into owned `recurring-work`
- known risks: unverified external claims; platform-specific configuration; package path mismatch; consequential automation examples

### `agent-persona-builder-reference`

- source: user-supplied local package
- trust: candidate/reference
- executable: false
- license: unresolved
- disposition: adapt selected concepts into owned `agent-identity-design`
- known risks: persona conventions may overfit one orchestrator; memory/heartbeat patterns require product/host review; package path mismatch

### `agent-org-planner-reference`

- source: user-supplied local package
- trust: candidate/reference
- executable: false
- license: unresolved
- disposition: adapt agents-vs-skills and bounded review-loop principles into Router/workforce policy
- known risks: numeric coordination claims not independently verified; generic org generation can conflict with existing Agent OS ownership; package path mismatch

## Approval Boundary

This review authorizes documentation/adaptation only. It does not authorize:

- installing the uploaded skills into a runtime;
- adding a new persistent agent;
- enabling a recurring scheduler;
- granting external mutation authority;
- production access or deployment;
- secrets or credential changes;
- treating quantitative source claims as verified Agent OS facts.
