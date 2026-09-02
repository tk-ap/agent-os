# Design Skill Benchmark

## Goal

Determine which design/anti-slop skills measurably improve Agent OS output without increasing instruction conflict, generic aesthetic convergence, regressions, context cost, or security surface.

The benchmark is for selection, not for proving one skill is universally best.

## Freeze rule

Until this benchmark produces evidence, broad design-skill acquisition is frozen by default.

A new resource may still be discovered and recorded, but it does not enter the evaluation shortlist unless it fills a demonstrated gap, replaces an overlapping candidate, or introduces a materially different verification method.

## Baseline

Every benchmark starts with the same authoritative inputs:

- user request and acceptance criteria;
- repository-local product direction;
- real brand assets and existing UI patterns;
- protected regression boundaries;
- owned Agent OS `quality-railguards`;
- required functional/end-to-end verification.

No candidate may overwrite these inputs.

## Representative tasks

### ASHWOOD — editorial/public experience

Use a bounded existing-surface refinement, not a greenfield mockup.

Evaluate whether the candidate improves:

- visual specificity and composition;
- fidelity to ASHWOOD photography/editorial direction;
- responsive behavior;
- restraint and hierarchy;
- first-pass human acceptance;

without introducing generic premium-design recipes or unnecessary implementation churn.

### ALVIRA — beginner-friendly product/onboarding UI

Use a bounded comprehension or onboarding task.

Evaluate whether the candidate improves:

- immediate understanding for a non-expert AI user;
- information density;
- CTA and interaction clarity;
- accessible/mobile behavior;
- preservation of application regression boundaries;

without turning the app into a marketing page or hiding important product state.

### ailhat — operational/intelligence product UI

Use a bounded intelligence/action surface.

Evaluate whether the candidate improves:

- scanability and prioritization;
- distinction between observation, recommendation, and action;
- interaction polish where it has purpose;
- operational credibility;
- responsiveness and state handling;

without adding decorative motion, generic dashboard cards, or false live/system signals.

## Candidate configurations

Do not load all candidates together.

Test small configurations against the same task where practical:

1. **Baseline:** product direction + owned quality railguards only.
2. **Producer candidate:** one primary production/design skill.
3. **Specialist candidate:** baseline producer + one narrow specialist where the task has that need.
4. **Inspector candidate:** baseline producer + one independent post-change reviewer.

Default active set target:

- one primary producer skill;
- zero or one narrow specialist;
- zero or one independent reviewer.

Any larger set needs a recorded reason.

## Metrics

Record for each run:

| Metric | Meaning |
| --- | --- |
| Human acceptance | Did the owner actually prefer/accept the result? |
| First-pass usefulness | How close was the first bounded result to acceptable? |
| Useful catches | Concrete defects found that the baseline missed |
| False positives | Suggested changes rejected as preference theater or wrong for the product |
| Missed issues | Defects later found by human or verification that the candidate should reasonably have caught |
| Reverted corrections | Candidate-driven changes later removed or undone |
| Functional regressions | Broken behavior introduced by following the skill |
| Mobile/responsive defects | New or uncaught responsive problems |
| Generic-slop findings | Template UI/copy/motion patterns remaining after the pass |
| Churn | Unnecessary files, dependencies, abstractions, or unrelated edits |
| Context cost | Additional instructions/references needed relative to gain |
| Security surface | Shell/network/package/hooks/credential capabilities requested |

Use qualitative scoring when exact numbers are not available, but preserve the evidence behind the score.

## Promotion / demotion

Promote a candidate only when it shows repeatable material gain over baseline on the tasks it claims to improve.

Do not promote because:

- one output looked attractive;
- a directory ranks it highly;
- the repository is popular;
- it contains more rules;
- it agrees with another skill.

Demote or remove a candidate when it is redundant, repeatedly causes false positives, creates excessive context cost/churn, or loses to a simpler capability on comparable tasks.

A candidate may be excellent for one surface and inappropriate for another. Approval should preserve activation boundaries.

## Security gate

Before executable approval, apply the zero-trust skill supply-chain model from PR #17:

- immutable source capture;
- full dependency/instruction inspection;
- capability declaration;
- risk classification;
- sandbox/adversarial test;
- independent approval;
- narrow runtime activation;
- revocation path.

Benchmark usefulness cannot substitute for security admission.

## Current evaluation order

1. `interface-review` — first because it supplies a distinct change-review method rather than another aesthetic recipe.
2. `emil-design-eng` — evaluate on interaction/motion tasks where frequency and purpose matter.
3. `impeccable` — evaluate selectively as a possible replacement/consolidation source; do not install its CLI/hooks during initial comparison.

After these comparisons, decide what to promote, adapt into owned skills, keep as reference, demote, or reject before adding more design resources.
