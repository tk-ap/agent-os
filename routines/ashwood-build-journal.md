# Routine — ASHWOOD Build Journal & Field Notes

**ID:** `ashwood-build-journal`
**Status:** `REVIEWED` — Reviewed by TK 2026-09-06. Blocked from `ACTIVE` by trigger source — see §3.
**Owner (design):** Bill · **Executing agent:** Marlo · **Verification:** W Dog · **Risk review:** Rook · **Economics:** Ledger · **Coordination:** Router

---

## 1. Purpose and expected outcome

Convert accumulated verified build evidence into curated public journal and field-note entries on ASHWOOD, so the public build record stays current without a human in the loop.

Expected outcome: ASHWOOD carries a continuously current, evidence-backed record of what was actually built and decided. Indirect traffic to ALVIRA is a downstream effect of that record existing, not a target the routine optimizes.

## 2. Originating objective / task-envelope reference

**Task envelope:** `routines/envelopes/env-ashwood-build-journal.md` (`env-ashwood-build-journal`).

Shared workforce Growth / Marketing Engineering capability (`README.md`), executing under the standing `scoped-publish` grant in `agents/marlo/IDENTITY.md` §09. The envelope defines what work is permitted; this contract defines only how it may repeat.

## 3. Trigger type and cadence

**Event-conditioned scan on a scheduled tick.**

- Tick cadence: **weekly** — confirmed by TK, 2026-09-06.
- Fire condition: at least one evidence event with `visibility: public-candidate` recorded since the last successful run's watermark.

The tick only *checks*. The evidence condition decides whether anything is produced.

### Trigger source — blocking `ACTIVE`

**The evidence store this condition queries does not exist.** `runtime/evidence.py` builds an in-memory evidence dict per task run and returns it; it does not persist a queryable ledger, and it carries no `visibility` field, so nothing is classified `public-candidate` anywhere today.

Two ways forward, TK's choice:

1. **Build the ledger** — persist evidence events with the `visibility` classification `skills/owned/audit-evidence-ledger/SKILL.md` already defines. Correct, and larger than this routine.
2. **Commit-derived candidates as an interim trigger** — §5 already permits commit and PR history as an input, and the Hermes change-digest path already baselines ASHWOOD and ALVIRA on commits (`adapters/hermes/fleet/TELEGRAM.md`). The routine would derive candidates from commits and Marlo would classify publication-suitability per candidate rather than reading a stored classification.

Option 2 is bindable now and weaker: classification becomes a per-run judgment instead of a recorded decision, so provenance is thinner. It should be marked as interim in every evidence record it produces.

## 4. Skip / no-op condition

No new `public-candidate` evidence since the watermark → the run ends with no draft, no commit, no deploy, and no evidence event other than a no-op record.

This routine must never manufacture an entry to fill a scheduled slot. A quiet week is a correct outcome.

## 5. Data sources and provenance expectations

Permitted inputs:
- audit evidence events (`skills/owned/audit-evidence-ledger/SKILL.md`);
- commit and PR history of participating product repositories (`tk-ap/ALVIRA`, `tk-ap/ashwood-info`, `tk-ap/ailhat`, `tk-ap/ledgato`);
- already-published ASHWOOD content, for continuity and de-duplication.

Excluded inputs: private analytics, customer or prospect data, credentials, ALVIRA context beyond permitted use, and any private operational data not classified `public-candidate`.

Provenance: every factual claim in an entry must trace to a specific evidence event. Intended, simulated, preview, deployed, and user-validated states remain distinct in the copy and are never collapsed into "shipped."

## 6. Processing steps

1. Read watermark from the last successful run.
2. Collect evidence events since the watermark.
3. Filter to `visibility: public-candidate`.
4. Discard any candidate whose claims are not traceable to a recorded evidence event.
5. If nothing survives → skip (§4).
6. Marlo drafts one entry in voice (`agents/marlo/VOICE_PROFILE.md`), refusing any claim the evidence does not support rather than softening it.
7. Run output validation (§12).
8. Commit to the granted path. In dry-run mode, open a PR instead.
9. Record an evidence event for the run.
10. Advance the watermark only after a successful commit.

## 7. Output destination and externally visible side effects

Destination: `tk-ap/ashwood-info` at `/journal/*` and `/journal/field-notes/*`.

Externally visible side effects: a new public page and the resulting Vercel deploy at `ashwood-info.vercel.app`. **No outbound notification to any person.** Fully reversible by `git revert` plus redeploy.

## 8. Authority class and required approvals

**Authority class:** `scoped-publish`. **Decision: `allow`**, scoped exactly to `/journal/*` and `/journal/field-notes/*` in `tk-ap/ashwood-info`, conditioned on the action being a revertible site commit with no outbound notification.

Any write outside those paths is **out of scope and fails closed** — the routine halts rather than requesting scope at runtime. The grant confers nothing on Substack, social, product landing pages, email, or live positioning; per `skills/owned/authorization-policy/SKILL.md`, publish authority is never inferred from read access and never accrues through repetition.

## 9. Concurrency and duplicate execution

Single-flight. One run at a time, guarded by a lock on the target repository. A tick that fires while a run is in progress is **skipped, not queued** — queuing would let two runs draft from the same watermark.

## 10. Idempotency and reconciliation

An entry is content-addressed by the set of evidence-event IDs it draws on. If every source ID in a candidate already appears in a published entry, the candidate is dropped.

Before any push, the routine reads remote HEAD to detect an entry a prior ambiguous run may already have landed. The watermark advances only on confirmed commit, so a failed run re-reads the same window rather than skipping it.

## 11. Dry-run / staging path

Until TK promotes the routine to `ACTIVE`, and again after any material change to paths, sources, or validation rules, the routine opens a **pull request** instead of committing. The PR is the deliverable; merge is a human action.

## 12. Validation rules for generated output

An entry fails validation if any of the following is true:
- it contains a metric, quote, traffic figure, adoption number, or citation not traceable to an evidence event;
- it presents a preview, simulated, or intended state as deployed or user-validated;
- it includes secrets, credentials, personal data, or customer names not cleared for publication;
- it writes outside the granted paths, or the diff touches files outside `/journal`;
- an internal link does not resolve, or the site build fails.

Any failure blocks publication. Validation failures are never resolved by weakening the rule.

## 13. Retry policy and ceiling

Maximum **2** retries, transient failures only (network, build runner, rate limit).

**No retry after an ambiguous push timeout.** The routine reconciles against remote HEAD first (§10) and only then decides whether to retry, because a blind retry can duplicate an externally visible page.

## 14. Circuit breakers

- Maximum **1** entry published per run.
- Maximum **2** entries published per rolling 7 days.
- Per-run ceilings: **400K input tokens, 40K output tokens, 15 minutes wall clock, $6.00.**
- Any validation failure (§12) halts the run immediately; the breaker is failure count > 0, not a threshold.

## 15. Anomaly conditions — pause and escalate

The routine suspends itself and escalates rather than continuing when:
- candidate evidence volume departs materially from its normal envelope in either direction;
- a draft carries a claim with no traceable source;
- a write is attempted outside the granted paths;
- the diff touches files outside `/journal`;
- entry length falls outside its expected envelope;
- the deploy fails or the published URL does not resolve after publication;
- the Marlo §09 grant text has changed since the last run.

## 16. Cost assumptions and caps

Projected: **~$1.50–2.00** per publishing run, **~$0.25** per skip, **~$3.75/month** on Claude Opus 5. Basis and method: `routines/COST_PROJECTIONS.md`.

Caps: **$6.00 per run**, **$25 per month**. A breach suspends the routine; it never truncates a run between the page commit and the evidence record, so the cost check runs at turn boundaries and before mutation.

The portfolio breaker in `COST_PROJECTIONS.md` §6 — $75/month across all routines — suspends this routine even when it is inside its own cap.

**These are projections, not measurements.** The first three runs record actual token counts (§19); the caps are re-derived from those.

## 17. Human review requirements

Review is **mandatory** in `DRAFT` and `REVIEWED` status (PR mode, §11).

In `ACTIVE` status, review is not required per run — that is the point of the standing grant.

Review is **restored automatically** and status drops to `SUSPENDED` when any anomaly (§15) or stop condition (§20) fires, or when the target paths, source set, audience, or reversibility of the action materially change.

## 18. Success criteria and verification

A run succeeds when: the entry exists at its expected URL, returns HTTP 200, appears in `sitemap.xml`, renders, and every claim traces to a recorded evidence event.

Verification is performed independently of the publishing step and owned by W Dog. HTTP-level checks are sufficient here and require no privileged browser capability.

## 19. Evidence destination and audit trail

Each run records an evidence event carrying: run ID, timestamp, trigger, evidence-event IDs consumed, skip/publish decision, published URL, validation result, verification result, reversal path, and cost when known.

Destination: `docs/evidence/routines/ashwood-build-journal/<YYYY-MM-DD>-<run-id>.json`. Record shape and rules: `docs/evidence/routines/README.md`.

A run that publishes without writing a record is a failed run, even when the page is correct. The first three runs additionally record input, output, and cache token counts, so §16 can be re-based on measurement.

## 20. Stop conditions, suspension, rollback

**Stop:** two consecutive failed runs; any attempted write outside the granted paths; revocation or material change of the §09 grant; unresolved validation failure on the same candidate twice.

**Suspension:** set status to `SUSPENDED` and unbind the scheduler in the host adapter. No change to this contract is required to stop the routine.

**Rollback:** `git revert` the entry commit and redeploy. Record the reversal as an evidence event — reversals are part of the product record and are not deleted from it.

## 21. Loop termination and escalation

This routine runs no producer/inspector loop. A candidate that fails validation twice is abandoned and handed to TK with the failure reason; it is not redrafted a third time.

Escalation owner: **TK.** Router coordinates. Rook is pulled in when the trigger is a permission or unauthorized-path anomaly.

---

## Authority state

`allow`, scoped and standing, for the two granted path families. Everything else in this routine's blast radius is `deny` by fail-closed default.

## Next permitted action

All prerequisites are resolved. Bind the routine to a weekly scheduler in the host adapter **in PR mode** (§11), run three times, then re-base the caps in §16 from the measured token counts.

Promotion past `REVIEWED` remains TK's decision.
