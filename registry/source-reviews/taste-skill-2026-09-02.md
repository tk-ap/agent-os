# Source review: Taste Skill

Date: 2026-09-02
Source: `Leonxlnx/taste-skill`
Website reviewed: `https://www.tasteskill.dev/`
Pinned commit: `ccbc15639c97057cbfcf32ecebc38ef716e4bb37`
License: MIT
User-supplied install reference: `npx skills add Leonxlnx/taste-skill`

## Review purpose

Determine which Taste Skill capabilities materially improve the current Agent OS workforce and product environments without allowing an external design framework to become a cross-product aesthetic authority.

Taste Skill is capability supply. Agent OS remains the source of truth for ownership, skill selection, authorization, verification, product boundaries, and activation.

## Catalog observed

The public Taste Skill catalog currently exposes 13 skills:

1. `taste-skill` / install name `design-taste-frontend` — v2 experimental default.
2. `taste-skill-v1` — legacy fallback.
3. `gpt-tasteskill` / `gpt-taste` — GPT/Codex-oriented high-variance motion-heavy frontend rules.
4. `image-to-code-skill` / `image-to-code` — image-first visual reference then implementation.
5. `redesign-skill` / `redesign-existing-projects` — audit-first improvement of existing projects.
6. `soft-skill` / `high-end-visual-design` — soft, premium, motion-rich style protocol.
7. `output-skill` / `full-output-enforcement` — completion and placeholder-avoidance rules.
8. `minimalist-skill` / `minimalist-ui` — editorial/utilitarian minimalist style protocol.
9. `brutalist-skill` / `industrial-brutalist-ui` — Swiss/industrial/tactical style protocol.
10. `stitch-skill` / `stitch-design-taste` — Google Stitch DESIGN.md generation.
11. `imagegen-frontend-web` — image-only website section art direction.
12. `imagegen-frontend-mobile` — image-only mobile app screen/flow art direction.
13. `brandkit` — image-only brand identity board generation.

## Source-level strengths

Useful recurring principles:

- read the brief and existing product direction before generating;
- reject generic AI-default composition rather than merely decorating it;
- audit existing products before redesigning them;
- preserve current stack and functionality during redesign;
- verify dependencies instead of hallucinating imports;
- treat mobile as a real layout/flow state;
- require functional interactions, readable hierarchy, focus/error/empty states, and truthful evidence;
- use image references when visual fidelity materially improves implementation;
- finish requested deliverables rather than substituting placeholders or skipped sections;
- make visual-system choices specific to audience, product, and brand rather than one universal look.

These align with the owned `quality-railguards` direction and can strengthen it without importing Taste Skill as policy.

## Important source-level risks

The collection contains substantial hard-coded aesthetic and stack preferences. Examples include mandatory/default Tailwind or React assumptions, named font preferences/bans, GSAP or Motion preferences, required giant spacing, bento/layout prescriptions, mandatory imagery, specific icon-family bans, and style-specific palette rules.

These rules are useful only when they fit the product brief. They must never override:

- repository-local brand/type/interaction direction;
- existing framework and dependencies;
- protected regression boundaries;
- accessibility, security, or performance evidence;
- user-requested visual language;
- Agent OS minimum-sufficient skill selection.

No Taste Skill tool declaration or install command grants execution authority.

## Skill dispositions

### 1. `taste-skill` / `design-taste-frontend`

Disposition: **candidate — high relevance, selective adaptation required**
Priority: P0/P1
Proposed agents: Designer, Eugene, W Dog

Best scope:
- ASHWOOD public/editorial/portfolio surfaces;
- ALVIRA, ailhat, and other product public shells/landing pages;
- portfolio, editorial, marketing, and redesign work.

Do not route automatically to:
- dashboards;
- data tables;
- multi-step product UI;
- dense operational application surfaces.

Strengths:
- brief inference;
- design-system selection based on actual audience/context;
- audit-first redesign protocol;
- dependency verification;
- hard pre-flight quality gate;
- strong anti-default discipline.

Adaptation required:
- remove universal Tailwind/React/font/icon preferences;
- do not make dual-mode/dark-mode, GSAP, or specific design systems mandatory;
- preserve product-local typography and existing CSS architecture;
- do not apply Taste Skill's stylistic bans as cross-product rules.

### 2. `redesign-skill` / `redesign-existing-projects`

Disposition: **candidate — high relevance**
Priority: P0
Proposed agents: Designer, Eugene, W Dog

Best scope:
- existing-site audit and targeted redesign;
- preserving live functionality while improving composition, states, responsiveness, metadata, and implementation quality.

Strong fit with existing ASHWOOD/ALVIRA working pattern: audit first, preserve stack, make focused changes, test after changes.

Adaptation required:
- do not automatically replace existing fonts;
- never fabricate realistic-looking names, dates, metrics, avatars, or placeholder imagery to make a page look finished;
- real assets and source-grounded content outrank Picsum or invented content;
- subjective visual upgrade rules remain subordinate to product direction.

### 3. `output-skill` / `full-output-enforcement`

Disposition: **candidate/reference — concepts adapted into owned quality railguards now**
Priority: P0
Proposed agents: all producers; especially Eugene, Bill, Designer, W Dog

Useful concepts:
- count requested deliverables;
- no placeholder code or omitted middle sections when full output was promised;
- compare output against original request before calling complete;
- if a host/output limit prevents completion, report exact partial state instead of pretending the work is complete.

Do not import literally:
- platform-specific continuation syntax;
- instructions that conflict with host response limits or higher-level communication policy.

### 4. `image-to-code-skill` / `image-to-code`

Disposition: **candidate — high relevance for visually important work**
Priority: P1
Proposed agents: Designer, Eugene
Dependencies: image-generation capability plus repository/file implementation capability

Best scope:
- ASHWOOD visual reconstruction and editorial art direction;
- high-fidelity landing/public pages;
- screenshot/reference-led redesigns.

Adaptation required:
- image-first is optional and evidence-driven, not mandatory for every frontend task;
- user-provided photography/design references outrank generated references;
- generated images are design evidence, not permission to change product requirements;
- avoid wasteful one-image-per-section generation when fewer references are sufficient.

### 5. `imagegen-frontend-web`

Disposition: **candidate — relevant visual-direction tool**
Priority: P1
Proposed agents: Designer
Dependencies: image-generation capability

Best scope:
- premium section-level website concepts before implementation;
- testing distinct visual directions without changing production code.

Adaptation required:
- no mandatory one-image-per-section rule;
- no fixed section count;
- product content and available assets determine image count and composition;
- generated text in images is not product copy evidence.

### 6. `imagegen-frontend-mobile`

Disposition: **candidate — relevant visual-direction tool**
Priority: P1
Proposed agents: Designer
Dependencies: image-generation capability

Best scope:
- native/mobile product concept flows;
- mobile rethinking where a visual reference would reduce implementation ambiguity.

Adaptation required:
- distinguish native app concepts from mobile web/responsive-site review;
- device mockup framing is optional;
- rendered responsive testing remains required for web products.

### 7. `brandkit`

Disposition: **candidate — relevant brand-system exploration**
Priority: P1
Proposed agents: Designer, Steward
Dependencies: image-generation capability

Best scope:
- ALVIRA / ailhat / ASHWOOD / future product identity exploration;
- logo and visual-world concept boards;
- brand-system comparison before implementation.

Adaptation required:
- generated logos are concepts, not trademark-clearance evidence;
- never invent brand strategy when repository/user direction already exists;
- user-approved brand assets remain authoritative.

### 8. `soft-skill` / `high-end-visual-design`

Disposition: **candidate style reference only**
Priority: P2
Proposed agents: Designer

Use only when the user/product brief explicitly calls for a soft, premium, atmospheric language.

Do not treat its font bans, double-bezel requirement, floating-pill nav, giant spacing, or motion prescriptions as generic quality rules. It directly conflicts with some current product typography and restrained editorial directions.

### 9. `minimalist-skill` / `minimalist-ui`

Disposition: **candidate style reference only**
Priority: P2
Proposed agents: Designer

Useful when a product explicitly calls for restrained editorial/utilitarian minimalism.

Do not automatically adopt its palette, bento grids, serif pairings, animations, Picsum imagery, or named-font bans. This is an aesthetic recipe, not a quality authority.

### 10. `brutalist-skill` / `industrial-brutalist-ui`

Disposition: **candidate style reference only**
Priority: P2
Proposed agents: Designer

Useful only when the brief explicitly calls for Swiss industrial, mechanical, terminal, tactical, or raw brutalist language.

Never route automatically based on product being "technical" or agent-related. The style can overwhelm clarity and brand continuity if inferred too broadly.

## Explicitly not onboarded as executable candidates

### `gpt-tasteskill` / `gpt-taste`

Disposition: **blocked from runtime; reference-only if manually inspected**

Reasons:
- requires simulated Python/random-choice output rather than grounded design selection;
- mandates AIDA structure for every page;
- says static interfaces are forbidden;
- mandates GSAP patterns and multiple motion paradigms;
- imposes giant spacing and gapless bento behavior;
- suggests generic external placeholder imagery;
- model-specific aggression would compete with product direction and Agent OS verification/quality policy.

Selected ideas such as avoiding six-line hero wraps or checking button contrast are already better represented by owned quality railguards and other candidates.

### `taste-skill-v1`

Disposition: **excluded**
Reason: legacy fallback preserved upstream only for exact-behavior compatibility. Current catalog recommends v2 unless v2 breaks a specific project.

### `stitch-skill` / `stitch-design-taste`

Disposition: **deferred / not currently relevant**
Reason: requires a Google Stitch workflow or Stitch MCP integration. No current Agent OS product/environment binding needs Stitch. Re-evaluate only if Stitch enters the build harness.

## Onboarding model

Do not run `npx skills add Leonxlnx/taste-skill` inside Agent OS as a blanket install.

Instead:

1. pin this reviewed source commit;
2. register the relevant skill candidates in `registry/vendor-acquisition.yaml`;
3. keep style recipes non-executable until a matching product brief exists;
4. forward-test P0/P1 candidates on real work;
5. adapt/remove conflicting instructions;
6. vendor or stable-reference only the candidates that materially improve outcomes;
7. record usefulness and demote redundant skills.

## Suggested forward tests

1. **ASHWOOD redesign/public surface:** compare owned quality railguards alone vs. + `taste-skill` v2 / `redesign-skill` concepts on one bounded section; preserve ASHWOOD typography, photography, route structure, and regression boundaries.
2. **ASHWOOD visual-reference task:** test `image-to-code` or `imagegen-frontend-web` on a single section where generated art direction is genuinely useful; measure fidelity and implementation churn.
3. **ALVIRA public shell:** use `taste-skill` only on the marketing/public route, explicitly excluding `/app`, interviews, Context creation, Reflect, uploads, auth, data models, and backend behavior.
4. **Mobile concept:** test `imagegen-frontend-mobile` only when the task is a native/app-style visual concept; use rendered browser verification for responsive web instead.
5. **Brand exploration:** test `brandkit` on a non-production identity concept and require human selection before implementation.
6. **Output completeness:** compare quality/rework when producer runs the owned completeness gate derived from `output-skill` before inspector handoff.
