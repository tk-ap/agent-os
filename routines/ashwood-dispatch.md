# Routine — ASHWOOD Dispatch Pages

**ID:** `ashwood-dispatch`
**Status:** `REVIEWED` — Reviewed by TK 2026-09-06. Blocked from `ACTIVE` by trigger source — see §3.
**Owner (design):** Bill · **Executing agent:** Marlo · **Verification:** W Dog · **Risk review:** Rook · **Economics:** Ledger · **Coordination:** Router

---

## 1. Purpose and expected outcome

Publish an ASHWOOD dispatch page when validated learning exists that is worth stating publicly, and hand TK the Substack cross-post as an explicit next action.

Expected outcome: dispatches continue to appear on their own evidentiary merit rather than stalling on TK's availability to run the publish step. Distribution to subscribers remains entirely TK's decision.

## 2. Originating objective / task-envelope reference

**Task envelope:** `routines/envelopes/env-ashwood-dispatch.md` (`env-ashwood-dispatch`).

Shared workforce Growth / Marketing Engineering capability (`README.md`), executing under the standing `scoped-publish` grant in `agents/marlo/IDENTITY.md` §09. The envelope defines what work is permitted; this contract defines only how it may repeat.

## 3. Trigger type and cadence

**Event-driven only. This routine has no calendar cadence, deliberately.**

Fire condition: a `LEARNING` record exists — from `skills/owned/market-truth-growth-intelligence/SKILL.md` or an equivalent validated-outcome source — that (a) changed a stated belief, (b) is not yet reflected in a published dispatch, and (c) is supported by evidence the routine can cite.

A scheduled dispatch cadence is rejected as a design: it converts an evidence-gated surface into a quota, which is precisely the failure mode §4 exists to prevent. One dispatch is currently published (`/dispatch/001-the-mind-is-the-moat`); there is no established rhythm to preserve and none should be invented.

## 4. Skip / no-op condition

No qualifying validated learning → no draft, no commit, no deploy, no handoff. Silence is the correct output and requires no explanation.

### Trigger source — blocking `ACTIVE`

**No `LEARNING` record store exists.** `skills/owned/market-truth-growth-intelligence/SKILL.md` defines the `LEARNING` output layer, but nothing persists one, and `runtime/evidence.py` has no `visibility` classification.

Unlike the journal routine, **there is no interim fallback here.** A `LEARNING` record is a judgment that a belief changed after an experiment; it is not derivable from commit history, and inferring one from repository activity would be exactly the fabrication §12 forbids.

This routine stays at `REVIEWED` until validated learning is recorded somewhere it can read. That is the correct outcome — an evidence-gated surface with no evidence source should not run.

## 5. Data sources and provenance expectations

Permitted inputs:
- validated `LEARNING` records and the experiments that produced them;
- audit evidence events classified `public-candidate`;
- already-published dispatches and journal entries, for de-duplication and continuity.

Excluded: private analytics, unverified market signal, customer or prospect data, competitor claims not independently sourced, and anything still at `SIGNAL` or `INTERPRETATION` stage. **An interpretation is not a learning.**

Provenance: recency must be stated; stale evidence must be labeled as such; counter-evidence that survived the experiment is stated rather than omitted.

## 6. Processing steps

1. Collect validated `LEARNING` records since the watermark.
2. Drop any already reflected in a published dispatch.
3. Drop any whose supporting evidence is not citable.
4. If nothing survives → skip (§4).
5. Select **one** — the routine never batches dispatches.
6. Marlo drafts the dispatch in voice, refusing unsupported claims outright.
7. Run output validation (§12).
8. Commit to `/dispatch/*`. In dry-run mode, open a PR instead.
9. **Record the Substack cross-post handoff** — an entry in `routines/BACKLOG.md` plus a `handoff` field in the run's evidence record, naming the dispatch and its URL. This is the explicit next action §09 requires Marlo to hand to TK.
10. Record an evidence event and advance the watermark.

## 7. Output destination and externally visible side effects

Destination: `tk-ap/ashwood-info` at `/dispatch/*`.

Externally visible side effects: a new public page and the resulting Vercel deploy. **No outbound notification.** Reversible by `git revert` plus redeploy.

**Not a side effect of this routine:** any send to `tkashwood.substack.com`. See §8.

## 8. Authority class and required approvals

**Authority class:** `scoped-publish`. **Decision: `allow`**, scoped exactly to `/dispatch/*` in `tk-ap/ashwood-info`, conditioned on a revertible site commit with no outbound notification.

**The Substack boundary is the sharp one and this routine encodes it as a hard stop.** Publishing the dispatch page is permitted. Sending it to subscribers is `deny` — not `approve-required` *for this routine*, which holds no capability to send and must never acquire one at runtime. The cross-post is handed to TK as work, and per §09 this never becomes permitted through repetition, successful prior runs, or an accumulated track record.

Every other surface — social, product landing pages, email, outreach, live positioning — is outside this grant and fails closed.

## 9. Concurrency and duplicate execution

Single-flight, repository-locked. Overlapping triggers are skipped rather than queued. At most one dispatch is in flight at any time.

## 10. Idempotency and reconciliation

A dispatch is content-addressed by the `LEARNING` record IDs it draws on; a learning already reflected in a published dispatch cannot produce a second one.

Dispatch numbering (`001-`, `002-`, …) is read from the live directory immediately before commit, never from cached state, so a partially completed prior run cannot cause a number collision or a silent overwrite. Remote HEAD is read before any push.

## 11. Dry-run / staging path

PR mode until TK promotes to `ACTIVE`. Given that a dispatch is a positioning artifact rather than a build record, **PR mode is the recommended steady state** until at least three dispatches have been produced and reviewed under this contract.

## 12. Validation rules for generated output

A dispatch fails validation if it:
- states a metric, quote, traffic figure, conversion result, or citation not traceable to cited evidence;
- presents an interpretation, hypothesis, or intended state as a validated outcome;
- makes a forward-looking commitment, roadmap promise, pricing statement, or legal/contractual representation — all of which exceed delegated authority under `policies/AUTONOMY_POLICY.md`;
- names a customer, prospect, or third party without clearance;
- writes outside `/dispatch/*`, or the diff touches files elsewhere;
- omits counter-evidence that materially qualifies the claim;
- fails the site build or contains an unresolved internal link.

## 13. Retry policy and ceiling

Maximum **2** retries on transient infrastructure failure. No retry after an ambiguous push timeout until remote HEAD reconciliation confirms the page did not land (§10).

The Substack handoff is emitted **at most once per dispatch** and is never retried automatically — a duplicated handoff risks a duplicated send by a human acting on it.

## 14. Circuit breakers

- Maximum **1** dispatch per run, and at most **1** unmerged dispatch PR open at a time.
- Maximum **1** dispatch per rolling 14 days — confirmed by TK, 2026-09-06. If the evidence genuinely supports more, that is an escalation to TK, not an automatic allowance.
- Per-run ceilings: **600K input tokens, 60K output tokens, 20 minutes wall clock, $8.00.**
- Any validation failure halts the run.

## 15. Anomaly conditions — pause and escalate

Suspend and escalate when:
- more than one qualifying learning appears in a single window (suggests the evidence bar has drifted down);
- a draft contains a forward-looking or contractual statement;
- a write outside `/dispatch/*` is attempted;
- the dispatch index or an existing dispatch would be modified rather than added to;
- the handoff cannot be recorded — **the page must not publish without a recorded handoff**;
- the §09 grant text has changed since the last run.

## 16. Cost assumptions and caps

Projected: **~$2.00–2.50** per publishing run, **~$0.25** per skip, **~$2.25/month** at roughly 12 dispatches a year on Claude Opus 5. Basis and method: `routines/COST_PROJECTIONS.md`.

Caps: **$8.00 per run**, **$25 per month**. A breach suspends; it never truncates a run mid-mutation.

The annual figure extrapolates from one published dispatch, which is thin evidence. It affects the projection only — the per-run cap does not depend on it.

**Projections, not measurements.** Re-base from the first three runs.

## 17. Human review requirements

Mandatory in `DRAFT` and `REVIEWED` (PR mode). Recommended to remain mandatory beyond that (§11).

If promoted to `ACTIVE`, per-run review is not required for the page commit. Review is restored automatically, and status drops to `SUSPENDED`, on any anomaly (§15) or stop condition (§20), or on any material change to target, audience, or reversibility.

The Substack step is never covered by any review reduction — it is not this routine's to perform at any status.

## 18. Success criteria and verification

A run succeeds when: the dispatch exists at its expected URL, returns HTTP 200, appears in `sitemap.xml`, renders, every claim traces to cited evidence, **and the cross-post handoff is recorded.**

A published page with no recorded handoff is a **failed run**, not a partial success.

**Resolved 2026-09-06.** The handoff is satisfied by a durable record Marlo can write and W Dog can verify — a `routines/BACKLOG.md` entry plus the evidence record's `handoff` field — not by delivery to a notification channel. This keeps §09's "explicit next action" obligation intact while removing the dependency on a channel that does not exist. Automated delivery with read-confirmation is deferred to the backlog; it is an ergonomics improvement, not a governance requirement.

Verification is independent of publication and owned by W Dog. HTTP-level checks suffice; no privileged browser capability is required.

## 19. Evidence destination and audit trail

Each run records: run ID, timestamp, learning record IDs consumed, skip/publish decision, dispatch number and URL, validation result, verification result, handoff delivery confirmation, reversal path, and cost when known.

Destination: `docs/evidence/routines/ashwood-dispatch/<YYYY-MM-DD>-<run-id>.json`. Record shape and rules: `docs/evidence/routines/README.md`.

The `handoff` field is mandatory on any run that published (§18).

## 20. Stop conditions, suspension, rollback

**Stop:** two consecutive failed runs; any attempted write outside `/dispatch/*`; any attempt to reach Substack, social, or email from within the routine; revocation or material change of the §09 grant; a dispatch published without a recorded handoff.

**Suspension:** set status `SUSPENDED` and unbind the scheduler in the host adapter.

**Rollback:** `git revert` and redeploy. If the cross-post has already been sent by TK, the page revert does not reverse the send — record that asymmetry in the evidence event rather than implying full reversibility.

## 21. Loop termination and escalation

No producer/inspector loop. A draft that fails validation twice is abandoned and handed to TK with the failure reason.

Escalation owner: **TK.** Router coordinates. Rook reviews any anomaly involving the Substack boundary or an out-of-scope write — that class of anomaly is treated as a permission incident, not a bug.

---

## Authority state

`allow`, scoped and standing, for `/dispatch/*` page commits only. Subscriber distribution is `deny` and is structurally absent from this routine's capabilities.

## Next permitted action

All prerequisites are resolved. Bind the routine to an event trigger in the host adapter **in PR mode** (§11).

Do not promote to `ACTIVE` before three dispatches have been produced and reviewed under this contract — a positioning surface earns unattended publication by track record, not by inheriting the journal routine's.
