---
name: quality-railguards
description: Run a bounded post-production anti-slop inspection for generic, fabricated, overbuilt, incomplete, superficially verified, or machine-sloppy work. Use after the primary implementation exists and the relevant functional/mechanical checks have run.
---

# Quality Railguards

## Purpose

Run a focused post-production anti-slop quality pass without replacing product direction, technical review, security review, or end-to-end verification.

The goal is not to make everything minimal or stylistically uniform. The goal is to make generated work intentional, specific, grounded, proportionate, complete, and honestly verified.

Read `policies/QUALITY_RAILGUARDS.md` before applying this skill.

## Phase Boundary

This full skill is primarily a **post-production inspection**.

During implementation, producers apply only the applicable hard preventative gates from `policies/QUALITY_RAILGUARDS.md`: truth, working behavior, protected direction, security/authorization boundaries, and promised completeness.

After the bounded implementation exists and relevant functional/mechanical checks have run, invoke this skill against the changed scope. Do not force the producer to carry every optional taste heuristic while solving the primary task.

## When to use

Use this skill when:

- an implementation was substantially agent-generated and is ready for a bounded quality inspection;
- work technically functions but feels generic, bloated, performative, or oddly overengineered;
- UI/copy needs a pre-delivery specificity and craftsmanship pass;
- code needs a check for hallucinated APIs, noisy abstractions, generic naming, duplicate generated patterns, or test theater;
- a requested complete artifact may contain skipped sections, placeholder code, or implied-but-undelivered work;
- a release is about to be declared complete;
- a prior attempt produced no-op changes, disconnected UI, placeholder interactions, false verification, or repeated patches without root improvement.

## When not to use alone

This skill does not replace:

- correctness/debugging review;
- security/privacy/threat modeling;
- product or market judgment;
- accessibility expertise;
- rendered visual inspection;
- `end-to-end-verification` for cross-boundary outcomes.

Compose with the appropriate owner/skill instead of stretching anti-slop beyond its decision domain.

## Workflow

### 1. Freeze the preserve contract and changed scope

Read the active task, acceptance criteria, repository-local instructions, product art direction, protected regression boundaries, and changed files/artifacts.

For visual work, derive a concise design read from the actual product, audience, existing assets, and user references before applying any aesthetic recipe. Existing brand/type/interaction direction is evidence, not optional inspiration.

State the actual review scope. Default to the changed diff/files/artifacts, not a gratuitous whole-repository cleanup.

Write the preserve contract before proposing changes. Unless the task explicitly says otherwise, preserve:

- intended behavior and accepted outcome;
- product/repository direction and public voice;
- facts, examples, evidence, and source-grounded claims;
- accepted architecture and ownership boundaries;
- protected routes, assets, integrations, data contracts, and regression boundaries;
- security, authorization, validation, observability, and failure-handling boundaries.

If a proposed change would alter one of those items, it is not an anti-slop correction; route it as a separate product/technical decision.

### 2. Classify the artifact

Select only the applicable dimensions:

- `ui-visual`
- `copy-prose`
- `code-implementation`
- `tests-verification`
- `docs-execution-guidance`
- `deliverable-completeness`

Do not run irrelevant specialist checks.

### 3. Run the hard-gate scan

Check for:

- invented or unverified claims;
- dead/placeholder shippable interactions;
- generic template structure disconnected from content;
- unnecessary files, dependencies, abstractions, fallbacks, or agents;
- implementation-mirroring tests with little behavioral value;
- claims of mobile, visual, runtime, or production success without evidence;
- product-local direction being overwritten by generic taste;
- responsive/accessibility/failure states ignored when they are part of the promise;
- security or validation removed merely for brevity;
- no-op commits or revision churn that do not change the failing behavior;
- requested full files, components, sections, or deliverables replaced by `TODO`, `...`, placeholder comments, skipped middle sections, or prose that merely describes missing implementation.

Any applicable hard-gate failure blocks a clean pass.

If a platform/output boundary genuinely prevents complete delivery, report the exact partial state and remaining deliverables. Do not label the work complete.

### 4. Inspect the changed work for generated-work slop

For UI/copy, ask whether each major changed section, component, visual treatment, interaction, and claim serves the specific product and reader.

For code, inspect changed files first. Search adjacent same-role files only when needed to determine whether the new work duplicates an existing helper, type, abstraction, implementation, or convention.

Look for:

- hallucinated/stale APIs or schema assumptions;
- a new abstraction with one caller or one concrete implementation that adds no meaningful boundary;
- generic names that hide domain meaning;
- duplicated near-twin logic;
- defensive overkill or fallback laundering;
- comment noise and boilerplate;
- unrequested dependency, configuration, platform-support, or fallback expansion;
- tests that prove implementation shape rather than user/system behavior.

Do not flag justified framework conventions, external-boundary validation, security controls, or intentional product-specific patterns as slop.

### 5. Decide whether a specialist skill is worth the context

Use `skill-resolution` and load only an approved specialist skill when it materially improves this review. Candidate external anti-slop/taste skills are non-executable until separately approved and pinned.

Possible specialist domains include UI, copywriting, human/accessibility, mobile layout, visual-reference generation, brand exploration, redesign audit, and polyglot code-quality auditing.

Do not load multiple overlapping style recipes merely to create variance. Pick the minimum capability that matches the brief.

### 6. Report findings without preference theater

Classify findings as:

- `BLOCKER` — violates truth, working behavior, explicit acceptance, security boundary, evidence integrity, or promised completeness;
- `FIX` — concrete quality defect with a clear improvement;
- `CONSIDER` — legitimate judgment call; do not change without a reason;
- `ACCEPTABLE` — pattern reviewed and intentionally retained.

Each non-trivial finding should identify the artifact/location, why it matters, and the smallest reasonable correction.

Collapse repeated instances into one finding when they share the same cause.

### 7. Fix the minimum sufficient set

Prefer deletion, simplification, specificity, completion, or a direct correction over adding another abstraction or review layer.

Do not create cleanup work outside the authorized scope merely because adjacent code could be prettier.

After corrections, review the diff again. Confirm that every correction is tied to an accepted finding, preserves the preserve contract, and did not create unrelated churn.

### 8. Verify the actual promise

If the result is user-visible, runtime-affecting, deployable, or cross-system, compose with `end-to-end-verification`.

A passing quality scan is not proof that the feature works. A successful deployment is not proof that the experience is good.

### 9. Record quality-learning evidence

When useful, classify the inspection outcome signals:

- `useful-catch` — a railguard finding was accepted and corrected;
- `false-positive` — a finding was rejected because the pattern was justified or product-specific;
- `missed-issue` — a later human/reviewer finding should reasonably have been caught;
- `reverted-correction` — an accepted anti-slop correction was later undone because it made the result worse.

Do not rewrite this skill from one run. Repeated evidence may support a later reviewed change to the owned quality model. Vendor heuristics do not automatically graduate into policy.

## Output

Return:

- scope reviewed;
- preserve contract;
- applicable dimensions;
- hard-gate result;
- blocker/fix/consider findings;
- specialist skills used, if any;
- changes made;
- post-fix diff/scope check;
- verification evidence;
- requested-deliverable count and completed count when completeness is material;
- quality-learning signals when useful;
- final state: `pass`, `partial`, `failed`, or `blocked`;
- human acceptance still required, when applicable.

## Rules

- Product-specific direction beats generic anti-slop or Taste Skill preferences.
- Review changed scope first; do not turn a bounded task into a repository cleanup.
- Preserve behavior and accepted direction unless the task explicitly authorizes changing them.
- Never ban a technique solely because it is common.
- Never invent evidence to make a quality report look complete.
- Never call a visual/mobile/runtime state verified without actually checking that state.
- Never remove security or external-boundary validation solely to reduce code volume.
- Never turn quality review into an unbounded producer/inspector loop.
- Never load all anti-slop or taste skills by default.
- Never substitute placeholders or omitted implementation for a requested complete deliverable and still call it done.
- Never allow the skill to self-modify or promote a vendor preference into policy from a single run.
- Image-first design is optional and task-driven; user-provided references and real assets outrank generated references.
- Prefer one concrete correction over another layer of abstraction.
