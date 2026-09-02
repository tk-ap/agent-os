# AgenticSkills design source review — 2026-09-02

## Purpose

Evaluate AgenticSkills design/UI resources as discovery inputs for Agent OS without increasing active-context noise or treating a directory ranking as trust or quality proof.

AgenticSkills is a discovery index only. Canonical review happens against the upstream repository at an immutable commit. No catalog install command grants runtime authority.

## Acquisition posture

The design workforce now has enough overlapping capability that additional acquisition is frozen by default.

A new design skill may enter the shortlist only when it:

1. fills a demonstrated capability gap;
2. replaces or clearly outperforms an existing candidate; or
3. supplies a materially different verification method rather than another aesthetic opinion.

Discovery library size may grow. Candidate and active task sets should not grow by default.

## Shortlist

### 1. Interface Review — evaluate first

- Upstream: `jakubkrehel/skills`
- Pinned commit: `267330e1adfc66a718fb65fa6918c1f06d0a689e`
- Path: `skills/interface-review/SKILL.md`
- Pinned blob: `a5c47e5e94ec170f1ea2df4ab536c1034e376aa7`
- License: MIT
- Proposed agents: Designer, W Dog; Eugene when implementation context is needed
- Proposed role: read-only post-change interface inspector

Useful concepts:

- review the change rather than performing an unsolicited whole-codebase critique;
- compare both sides of the diff and distinguish `Introduced`, `Regression`, and `Pre-existing` findings;
- expand changed files to affected UI surfaces with an explicit bound;
- hold the change to its stated intent;
- keep correctness, tests, security, and performance in their existing review domains;
- never mutate the working tree during review;
- mark rendered/runtime claims unverified when they were not actually checked.

Risks / adaptation required:

- upstream depends on its own `better-interface` and other `better-*` domain skills plus referenced support files;
- Git/shell assumptions need to match the active harness and authorization model;
- its severity/verdict model must not displace Agent OS `quality-railguards` or end-to-end verification;
- zero-trust admission from PR #17 is required before any execution.

Disposition: **P0 evaluation candidate**. Adapt the change-scope/regression concepts into Agent OS if they benchmark well; do not install the full bundle by default.

### 2. Emil Design Engineering — conditional specialist

- Upstream: `emilkowalski/skills`
- Pinned commit: `d23d7f88a2e21c9e4b1418c7abe420f5c1052ba7`
- Path: `skills/emil-design-eng/SKILL.md`
- License: MIT
- Proposed agents: Designer; Eugene for implementation-specific interaction work
- Proposed role: interaction and motion judgment specialist

Useful concepts:

- ask whether an interaction should animate before choosing how it animates;
- reduce or remove motion for frequently repeated actions;
- use animation for spatial consistency, state indication, explanation, feedback, or preventing jarring state changes;
- treat small interaction details as cumulative quality rather than decorative spectacle.

Risks / adaptation required:

- contains highly prescriptive timing/easing/component rules that are heuristics, not universal product policy;
- contains author/course promotional initial-response behavior that is irrelevant to Agent OS;
- framework/library examples must not imply dependency installation;
- must remain subordinate to reduced-motion/accessibility requirements, actual performance evidence, and product-local art direction.

Disposition: **P1 conditional specialist**. Benchmark on ALVIRA/ailhat interaction work; do not load for static/editorial work unless motion is actually relevant.

### 3. Impeccable — reference / replacement candidate, not wholesale install

- Upstream: `pbakaus/impeccable`
- Pinned commit: `0330f61cef1c88291755beb373c81bef5f15be70`
- Representative Agent skill path: `.agents/skills/impeccable/SKILL.md`
- Observed skill version: `4.1.3`
- License: Apache-2.0
- Proposed agents: Designer and W Dog for evaluation only

Useful concepts:

- brief and incumbent product truth outrank generic aesthetic defaults;
- explicit surface modes (`Persuade`, `Operate`, `Read`, `Experience`) are a useful framing device;
- bounded visual verification rather than endless polish loops;
- separation between refinement and true redesign;
- broad references for responsive, interaction, typography, motion, color, UX writing, and hardening.

Risks / adaptation required:

- this is a larger tool ecosystem, not a single passive markdown reference;
- it includes scripts, command routing, hooks, doctor/repair flows, generated provider builds, CLI installation/update behavior, and network/install surfaces;
- substantial overlap exists with Taste Skill, owned quality railguards, anti-slop candidates, and existing design direction;
- any activation therefore requires full zero-trust package inspection, capability declaration, sandboxing, and comparison against simpler alternatives.

Disposition: **P1 reference/replacement candidate**. Mine or benchmark specific concepts first. Do not run the CLI installer or activate hooks as part of this PR.

## Not shortlisted

The remainder of the AgenticSkills design catalog stays discovery-only unless a concrete gap appears. Large bundles and overlapping style/aesthetic skills should not be added merely to increase coverage.

## Decision

The design capability problem has shifted from acquisition to selection and evidence.

Next action is benchmarking, not additional broad discovery. See `docs/quality/DESIGN_SKILL_BENCHMARK.md` and `registry/design-skill-evaluation.yaml`.
