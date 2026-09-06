# Routine Cost Projections

Basis for the per-run and per-period caps in each routine contract. Prepared 2026-09-06.

**These are projections, not measurements.** They are derived from measured input sizes in this repository and published per-token prices. No routine has run yet. §5 defines how they get replaced with real numbers.

## 1. Price basis

Anthropic first-party API rates, per million tokens:

| Model | Input | Output |
|---|---|---|
| Claude Opus 5 | $5.00 | $25.00 |
| Claude Sonnet 5 | $2.00 | $10.00 |
| Claude Haiku 4.5 | $1.00 | $5.00 |

Prompt caching: cache reads ~0.1× base input; cache writes 1.25× (5-minute TTL) or 2× (1-hour TTL).

`registry/harnesses.yaml` registers both `claude-code` and `codex-cli`. **These projections assume a Claude harness.** A run executed through Codex prices differently and its caps must be derived separately — the harness is an execution choice, and per the registry it changes cost without changing authority.

## 2. Measured inputs

Actual sizes in this repository and the ASHWOOD site, at ~3.5 characters per token:

| Input | Bytes | ≈ Tokens |
|---|---|---|
| `agents/marlo/IDENTITY.md` | 15,483 | 4,400 |
| `agents/marlo/VOICE_PROFILE.md` | 12,059 | 3,400 |
| `skills/owned/recurring-work/SKILL.md` | 5,504 | 1,600 |
| `skills/owned/task-envelope/SKILL.md` | 3,034 | 900 |
| `skills/owned/authorization-policy/SKILL.md` | 1,571 | 450 |
| `skills/owned/audit-evidence-ledger/SKILL.md` | 1,458 | 400 |
| Routine contract (largest) | 11,848 | 3,400 |
| Existing field note, as structural template | 5,538 | 1,600 |
| Existing dispatch, as structural template | 16,328 | 4,700 |

**Stable per-run prefix: ~16K tokens of repository context, ~25K including harness system prompt and tool definitions.** This prefix is identical across runs, so it is the cacheable part.

Published output sizes, measured: a field note is ~5.5KB of HTML (~1,600 tokens); a dispatch is ~16KB (~4,700 tokens).

## 3. The cost driver is loop turns, not draft length

An agentic run re-sends its history every turn, so billed input is cumulative across turns, not the size of the source material. A 12-turn run against a 25K prefix bills roughly 300K input tokens uncached, or ~25K written once plus ~2.5K per subsequent turn when the prefix caches.

**Drafting is cheap; iterating is not.** The draft itself is 1.6K–4.7K output tokens against runs that generate 20K–30K output tokens total once thinking and tool-call arguments are counted.

## 4. Per-run projections (Claude Opus 5, caching enabled)

| Routine | Turns | Input (cum.) | Output | Projected cost |
|---|---|---|---|---|
| `ashwood-build-journal` — publishing run | 8–15 | ~180K | ~20K | **$1.50–2.00** |
| `ashwood-build-journal` — skip run | 2–3 | ~30K | ~2K | **$0.20–0.30** |
| `ashwood-dispatch` — publishing run | 15–20 | ~250K | ~30K | **$2.00–2.50** |
| `ashwood-dispatch` — skip run | 2–3 | ~30K | ~2K | **$0.20–0.30** |
| `discoverability-audit` — findings run, disciplined fetch | 12–18 | ~180K | ~12K | **$1.00–1.50** |
| `discoverability-audit` — findings run, naive fetch | 15–20 | ~700K–1M | ~12K | **$3.50–5.50** |
| `discoverability-audit` — clean run | 5–8 | ~80K | ~3K | **$0.35–0.45** |

On **Claude Sonnet 5** every figure is ~40% of the Opus 5 number. On **Haiku 4.5**, ~20%. Model choice is a routine-implementation decision and does not change any authority in these contracts.

### The audit routine's cost is an implementation choice

`discoverability-audit` fetches ~18 sitemap URLs plus discovered internal links. Feeding raw HTML into context at ~10KB per page puts 400KB — over 110K tokens — into a single run, and it compounds every turn. Extracting `<head>`, meta, canonical, and link elements **outside the model** and passing only those drops the same run to ~11K tokens of page data.

**The contract therefore requires pre-extraction** (`discoverability-audit.md` §6). The 3–4× spread in the table above is the cost of ignoring that requirement, not a modelling uncertainty.

## 5. Period projections

Assumptions, stated as assumptions: the journal publishes in ~40% of weeks; the audit finds something above threshold in ~30% of runs; dispatch fires ~12 times a year against its 26/year ceiling — extrapolated from one published dispatch to date, which is thin evidence.

| Routine | Cadence | Runs/yr | Projected/yr | Projected/mo |
|---|---|---|---|---|
| `ashwood-build-journal` | Weekly | 52 | ~$45 | ~$3.75 |
| `ashwood-dispatch` | Event-driven | ~12 | ~$27 | ~$2.25 |
| `discoverability-audit` | Weekly | 52 | ~$34 | ~$2.85 |
| **All three** | | ~116 | **~$106** | **~$9** |

**Cost is not the binding constraint on this system — blast radius is.** Nine dollars a month is not what should decide whether these routines run; the caps below exist to catch a malfunction, not to ration the work. Read them as circuit breakers, not budgets.

## 6. Recommended caps

Per-run caps sit at roughly 3× the projected publishing run, so ordinary variation does not trip them and a runaway loop does. Period caps sit at roughly 2.5× projected spend.

| Routine | Per-run cost | Per-run input | Per-run output | Wall clock | Per-month |
|---|---|---|---|---|---|
| `ashwood-build-journal` | $6.00 | 400K | 40K | 15 min | $25 |
| `ashwood-dispatch` | $8.00 | 600K | 60K | 20 min | $25 |
| `discoverability-audit` | $5.00 | 500K | 30K | 20 min | $30 |

**Portfolio breaker: $75/month across all routines suspends all three,** not only the routine that exceeded its own cap. A single routine can fail loudly within its own cap while the aggregate is what actually signals something is wrong.

Breaching a cap **suspends**; it never truncates a run mid-mutation. A run halted for cost between the page commit and the evidence record would leave exactly the inconsistent state the evidence rules exist to prevent, so the cost check runs at turn boundaries and before mutation, never during one.

## 7. Re-basing

These projections carry no measured runs behind them.

The first **three** runs of each routine record actual input, output, and cache token counts in their evidence records (`docs/evidence/routines/`). After the third, replace this document's projections with measured medians and re-derive the caps from those.

Until that happens, treat §4 as an order-of-magnitude estimate. It is precise about prices and measured file sizes, and genuinely uncertain about turn counts — which is the term that dominates the result.
