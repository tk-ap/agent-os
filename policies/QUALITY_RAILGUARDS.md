# Agent OS Quality Railguards

## Principle

Quality railguards prevent agent-generated work from becoming generic, inflated, fabricated, incomplete, overbuilt, or superficially verified. They are a quality control layer, not an aesthetic authority and not a substitute for product direction.

A railguard may reject unsupported or low-quality work. It must not erase deliberate product identity merely because a technique is common.

## Scope

Apply these railguards when an agent creates or materially changes:

- product UI or interaction;
- public or product copy;
- application code, scripts, infrastructure, or configuration;
- tests and verification artifacts;
- architecture or implementation documentation intended to guide execution;
- a requested full artifact where omission or placeholder substitution would make delivery materially incomplete.

Use the minimum relevant checks. Do not load every specialist quality skill for every task.

## Two-Phase Quality Model

Quality control has two distinct phases.

### Phase 1 — production guardrails

While producing the work, apply only the hard preventative constraints needed to avoid known invalid states: do not fabricate, do not create knowingly dead shippable interactions, do not silently violate authorization/security boundaries, do not substitute placeholders for explicitly required complete deliverables, and do not knowingly overwrite protected product direction.

Do not make the producer carry every taste heuristic, optional style recipe, or post-hoc cleanup rule while solving the primary task. Excessive concurrent review context can degrade implementation quality and encourage rule-following over product judgment.

### Phase 2 — bounded post-production inspection

After the producer has completed the bounded implementation and run the relevant functional/mechanical checks, run the full quality-railguard inspection against the changed scope.

The inspection exists to find slop that survived production. It is not permission to reopen product strategy, redesign unrelated surfaces, or expand the task.

Default sequence:

`task → produce → functional/mechanical check → anti-slop inspection → minimal correction → diff review → end-to-end verification when applicable → human/owner acceptance`

## Preserve Contract

Before a post-production anti-slop inspection can modify work, define what must be preserved.

Unless the task explicitly authorizes otherwise, preserve:

- intended behavior and accepted product outcome;
- repository-local product direction and visual/interaction language;
- facts, examples, source-grounded claims, and evidence;
- accepted architecture and ownership boundaries;
- public voice and intentionally chosen terminology;
- protected regression boundaries, routes, assets, data contracts, and integrations;
- security, authorization, validation, observability, and failure-handling boundaries.

The inspection may change only what falls inside the authorized changed scope and is justified by a concrete quality finding, such as unnecessary abstraction, generic wording, redundant structure, comment noise, unsupported fallback expansion, duplicate generated patterns, incomplete requested output, or unmotivated UI treatment.

If a proposed cleanup would alter preserved behavior or direction, classify it as a separate product/technical decision rather than an anti-slop fix.

## Hard Gates

Work is not ready for delivery when any applicable gate fails:

1. **Evidence over invention** — do not fabricate APIs, schema behavior, statistics, testimonials, security claims, deployment state, test results, or product capabilities.
2. **Working over decorative** — interactive controls in shippable UI must work or be removed/clearly marked. Placeholder behavior must not masquerade as completion.
3. **Specific over generic** — sections, components, copy, abstractions, names, and workflows must exist because the product needs them, not because they are common AI-generated defaults.
4. **Necessary over overbuilt** — prefer the smallest implementation that satisfies the acceptance criteria. Do not add wrappers, fallback layers, dependencies, agents, files, or configuration without a concrete need.
5. **Behavior over test theater** — tests and checks must exercise meaningful behavior or contracts. A green check that merely mirrors implementation is not evidence of correctness.
6. **Reality over status labels** — `READY`, HTTP 200, lint success, CI success, or a generated report do not by themselves prove a user-visible or runtime outcome.
7. **Direction over anti-slop monoculture** — product-local art direction, voice, interaction language, and repository conventions outrank generic anti-slop or Taste Skill preferences unless they conflict with safety, truth, accessibility, or explicit acceptance criteria.
8. **Resilience over happy-path polish** — when relevant, verify mobile/responsive behavior, empty/loading/error states, keyboard/focus behavior, failure paths, and protected regression boundaries.
9. **Security is not slop** — do not remove validation, authorization, observability, or defensive controls merely to make code shorter or visually cleaner. Rook/Eugene own the relevant technical judgment.
10. **No false completion** — do not claim a rendered visual pass, production verification, cross-device success, or human acceptance when that evidence was not actually obtained.
11. **Complete over placeholder** — if the user asked for a full file, full component set, complete page/section set, or other bounded deliverable, do not substitute `TODO`, `...`, omitted middle sections, placeholder comments, or prose descriptions and still call the artifact complete. If a host/output boundary prevents completion, report the exact partial state and remaining deliverables.

## Quality Dimensions

### Interface and visual work

Before applying any style framework or recipe, infer the design read from the actual product, audience, current brand/assets, user references, and repository-local direction. Do not choose a design language merely because a skill labels it premium.

Ask:

- Does the composition reflect the product's actual content and identity?
- Can every visual technique be tied to hierarchy, comprehension, identity, feedback, or another concrete purpose?
- Does the interface remain usable rather than merely distinctive?
- Has responsive/mobile behavior been treated as a first-class layout state rather than a compressed desktop afterthought?
- Are accessibility, focus, states, and interaction completion accounted for?
- Did the implementation preserve existing routes, assets, typography, stack, and protected behavior unless the task explicitly authorized changing them?

A familiar technique is not automatically slop. Unmotivated technique stacking is.

Image-first or generated-reference workflows are optional. Use them when they materially improve art direction or implementation fidelity. User-supplied photography, screenshots, references, and existing product assets outrank generated references.

### Copy and prose

Reject:

- claims without evidence;
- vague prestige language that does not name the mechanism or benefit;
- repetitive AI cadence that substitutes emphasis for meaning;
- product copy that describes categories before the reader understands the problem;
- fake specificity, fake urgency, or invented customer proof.

Preserve intentional voice. Do not flatten every product into one house style.

### Code and implementation

Inspect the changed code first. Search adjacent same-role code only when needed to determine whether a new helper, type, abstraction, dependency, or implementation duplicates something that already exists.

Inspect for:

- hallucinated or stale APIs/configuration;
- a new abstraction with one caller or one concrete implementation that adds no meaningful boundary;
- generic naming that hides domain meaning;
- duplicated near-twin logic created by context-free generation;
- defensive fallback layers that conceal uncertainty instead of failing clearly at the right boundary;
- noisy comments that narrate obvious code;
- dependencies, platform support, files, configuration, or fallback behavior added without being requested or materially required;
- tests that only ratify the implementation rather than challenge behavior;
- incomplete requested implementation hidden behind placeholders or omitted sections.

Correct framework conventions and justified defensive boundaries are not slop.

## Delivery Gate

Before a meaningful artifact is called done:

1. Read the repository/product direction and acceptance criteria.
2. For visual work, record the product-specific design read before choosing any style recipe or specialist design skill.
3. Count bounded requested deliverables when completeness is material.
4. Produce the bounded implementation while applying only applicable hard preventative gates.
5. Run available functional/mechanical checks that already belong to the repository.
6. Freeze the preserve contract and changed scope for inspection.
7. Apply `skills/owned/quality-railguards/SKILL.md` as a post-production inspection of the changed scope.
8. Load only an approved specialist anti-slop/taste skill when it adds material value beyond the owned railguard.
9. Fix blockers and clearly justified quality failures; do not churn subjective preferences or redesign unrelated work.
10. Review the resulting diff to confirm the correction did not violate the preserve contract or expand scope.
11. Compose with `skills/owned/end-to-end-verification/SKILL.md` when the promise crosses runtime, deployment, UI, data, authorization, or integration boundaries.
12. Capture evidence and classify the result as `pass`, `partial`, `failed`, or `blocked`.
13. When aesthetic or experiential acceptance is materially subjective, preserve a human acceptance gate. Automated anti-slop/taste review cannot certify taste.

## Producer / Inspector Rule

The producer is responsible for hard preventative gates during implementation and a basic self-check for obvious defects. The full anti-slop inspection is a distinct post-production pass after the bounded implementation exists.

The inspector receives the preserve contract, changed scope/diff, acceptance criteria, and relevant product direction. The inspector does not receive blanket authority to redesign the feature or clean the repository.

An independent inspector is warranted only when it materially reduces risk or supplies missing evidence. Inspectors report violated acceptance criteria, concrete evidence, and the smallest actionable correction. They must not turn anti-slop into an unbounded preference loop.

## Quality Learning Loop

Quality review should become more specific to the workforce over time without allowing the system to rewrite its own rules autonomously.

For meaningful anti-slop inspections, record when useful:

- `useful-catch` — the railguard found a real defect that was accepted and corrected;
- `false-positive` — a finding was intentionally rejected because the pattern served the product or was otherwise justified;
- `missed-issue` — a later human/reviewer finding should reasonably have been caught by the railguard;
- `reverted-correction` — an anti-slop correction was later undone because it degraded behavior, clarity, voice, design, or maintainability.

Use repeated evidence, not one-off taste disagreements, to evolve the owned quality model. Repeated useful catches may justify strengthening or adding an owned rule. Repeated false positives or reverted corrections may justify narrowing or removing one.

Rule changes require normal Agent OS review/version control. A quality skill must never self-modify, silently promote a vendor heuristic into policy, or infer a universal preference from a single acceptance/rejection event.

## External Skill Boundary

External anti-slop, Taste Skill, or other design-quality skills are capability supply, not Agent OS policy. They remain subordinate to:

1. user instruction;
2. repository-local product direction and regression boundaries;
3. Agent OS autonomy, authorization, handoff, evidence, and quality policies;
4. the minimum-sufficient skill rule.

Never allow an upstream install wizard, `load always` instruction, tool declaration, default framework/font/icon stack, mandatory aesthetic recipe, or mutable latest version to bypass Agent OS skill review and pinning.
