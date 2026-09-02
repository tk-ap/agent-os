# Anti-Slop Skill Source Review — 2026-09-02

## Purpose

Evaluate external anti-slop skill sources as capability supply for Agent OS without allowing upstream instructions to redefine Agent OS ownership, tool authority, skill-loading policy, or product art direction.

## Source A — miqdadbadjuber/anti-slop

- Repository: `miqdadbadjuber/anti-slop`
- Pinned commit reviewed: `d9c341673ae28d3b8d0cab6ef6b968e49c72705c`
- Observed release line: v3.2.3
- License: MIT
- Relevant upstream skills:
  - `skills/antislop-ui/SKILL.md` — blob `109eb85ad570b3c3ceb988e715e0aeb15c0b8f42`
  - `skills/antislop-copywriting/SKILL.md` — blob `84d8ffceebffb911d0703bded921a17c699c460d`
  - `skills/antislop-human/SKILL.md` — blob `028795128b9ddb3cdf9ff44373ddd553ed6596a0`
  - `skills/antislop-layoutmobile/SKILL.md` — blob `7a143b17845a3f7ec839f63e2606fbee3f287eb4`
  - core `skills/antislop/SKILL.md` / `antislop.md`

### Useful concepts

- technique should have a product/hierarchy/readability purpose rather than being used as a generic model default;
- anti-slop is a filter, not a substitute for design direction;
- fabricated claims, dead interactions, weak responsive behavior, and unverified accessibility are delivery defects;
- mobile should be treated as an intentional layout state rather than a squeezed desktop;
- copy should preserve supplied voice and remove empty claims rather than manufacture specificity;
- human/accessibility checks belong inside craftsmanship, not as decorative compliance after the fact;
- a delivery gate is more useful than a loose style critique.

### Conflicts / adaptation required

Do **not** vendor or activate the core verbatim yet.

The upstream core contains assumptions that conflict with Agent OS:

- it says the core should be loaded always, while Agent OS requires the minimum sufficient skill set;
- it includes an install wizard that can modify project entry files; Agent OS skill acquisition is governed centrally and must not self-install at runtime;
- it requires a blocking user choice between DURING/AFTER modes before UI work; Agent OS should infer the appropriate quality phase from the active task unless user choice is genuinely needed;
- it declares tool access in upstream frontmatter; external skill tool declarations do not grant Agent OS authority;
- specialist skills expect the upstream core and numbered rule system, which adds significant context cost and coupling;
- some numeric visual prescriptions are useful heuristics but must not override project-specific art direction or become universal design law.

### Disposition

- Adapt core principles into owned `policies/QUALITY_RAILGUARDS.md` and `skills/owned/quality-railguards/SKILL.md`.
- Register UI, copywriting, human/accessibility, and mobile-layout skills as **candidate** specialist skills.
- Before approval/vendor copy: remove install/runtime-authority assumptions, decide whether to preserve rule-number dependencies, verify any scripts/references, run a forward test on real product work, and measure whether the skill improves outcomes without flattening product identity.

## Source B — iuliandita/skills / anti-slop

- Repository: `iuliandita/skills`
- Pinned commit reviewed: `9bc8aaaaa18954c29c293828071aa4fdb50baf60`
- Release observed: 1.45.1
- License: MIT
- Skill: `skills/anti-slop/SKILL.md`
- Pinned blob: `4dd8351050513652d90cf864e0bd5e8e0b31735d`

### Useful concepts

This is materially different from the design-focused source. It audits implementation quality across multiple languages for:

- hallucinated/stale APIs and schema assumptions;
- over-abstraction;
- generic naming;
- defensive overkill;
- duplicated near-twin logic;
- comment noise and boilerplate;
- dependency creep;
- test theater and implementation-mirroring tests.

It explicitly distinguishes anti-slop review from correctness, security, prose review, and deletion-only code slimming. It also warns reviewers to preserve framework idioms and repository conventions and to verify suspicious API claims before calling them hallucinations.

### Conflicts / adaptation required

- references other skills in its source collection (`code-review`, `security-audit`, `anti-ai-prose`, `code-slimming`) that do not map one-to-one to Agent OS names;
- recommends mechanical tools that may not be installed in a target repository and must not trigger unapproved dependency installation;
- contains collection-specific output contracts/references that must be inspected if vendored;
- broad polyglot context cost may be excessive for narrow changes.

### Disposition

Register as a **candidate** code-quality audit skill for Eugene and W Dog. Approval requires path/reference inspection, Agent OS skill-name adaptation, a realistic forward test, and confirmation that it adds value beyond normal technical review and `end-to-end-verification`.

## Agent OS Decision

Create an owned quality layer now; keep external specialist skills quarantined as candidates until explicit approval.

The owned railguard must remain stable even if external anti-slop projects change or disappear. External skills may deepen specific reviews, but they do not become the source of truth for what quality means inside Agent OS.
