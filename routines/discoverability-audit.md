# Routine — Discoverability & Route Integrity Audit

**ID:** `discoverability-audit`
**Status:** `REVIEWED` — Reviewed by TK 2026-09-06. Trigger source available; ready for scheduler binding.
**Owner (design):** Bill · **Executing agent:** Eugene · **Verification:** W Dog · **Risk review:** Rook · **Economics:** Ledger · **Coordination:** Router

---

## 1. Purpose and expected outcome

Continuously audit the discoverability and route integrity of the two public surfaces — `ashwood-info.vercel.app` and `alviratech.vercel.app` — and open draft pull requests for the technical, non-copy defects it finds.

Expected outcome: sitemap coverage, canonical and metadata correctness, structured data, internal linking from ASHWOOD entries to the relevant ALVIRA pages, and broken-route detection stay maintained instead of decaying between manual passes. This is the only lane in the three that acts directly on ALVIRA's surface, and it does so without touching positioning.

**Baseline, corrected 2026-09-06:** ASHWOOD publishes 8 URLs in `sitemap.xml`; ALVIRA publishes 10 (`/`, `/pricing`, `/why-alvira`, `/interview`, `/meos`, `/data`, plus legal pages). Both allow all crawlers.

ALVIRA's live surface is **`alviratech.vercel.app`**. `alvira.ctonew.app` is the decommissioned cto.new domain and returns 503; it is not an audit target. Its state is watched by the monitor script only so that a change — coming back up, or starting to redirect — is noticed.

## 2. Originating objective / task-envelope reference

**Task envelope:** `routines/envelopes/env-discoverability-audit.md` (`env-discoverability-audit`).

Shared workforce Growth / Marketing Engineering capability (`README.md`). The envelope defines what work is permitted; this contract defines only how it may repeat.

## 3. Trigger type and cadence

**Scheduled scan.** Cadence: **weekly** — confirmed by TK, 2026-09-06.

Optional additional event trigger: a deploy to either surface. Deploy-triggered runs catch a regression when it lands rather than up to a week later, but they are the main driver of run volume. **Deferred until three weekly runs have produced measured per-run cost** (§16); the decision is an economic one and there is currently no measurement behind it.

## 4. Skip / no-op condition

No findings above the reporting threshold → no PR, no issue, no report. A clean audit produces a single evidence event recording that it ran and found nothing.

The routine must never open a PR to demonstrate activity, and must never lower its threshold because a run would otherwise be empty.

## 5. Data sources and provenance expectations

Permitted inputs:
- the two live public surfaces, fetched over HTTP as an ordinary anonymous visitor;
- `robots.txt` and `sitemap.xml` on each;
- the two repositories' route definitions and static output (`tk-ap/ashwood-info`, `tk-ap/ALVIRA`).

Excluded: authenticated pages, any account-gated ALVIRA surface, analytics platforms, search-console data, third-party rank or volume estimates, and any credentialed session. **The routine holds no credentials and authenticates to nothing.**

Provenance: findings cite the exact URL and HTTP response observed, with fetch timestamp. Estimated or inferred impact is labeled as such and never stated as measured traffic — per the market-truth evidence rules, search volume, traffic, mentions, and conversion are different signals and none may be presented as another.

## 6. Processing steps

1. Fetch `robots.txt` and `sitemap.xml` for both surfaces.
2. Enumerate routes actually present in each repository's build output.
3. Diff published sitemap entries against real routes — in both directions (missing entries, and entries pointing at routes that no longer exist).
4. Fetch every sitemap URL; record status codes and redirect chains.
5. Check per-page technical metadata: title, description, canonical, Open Graph, structured data validity.
6. Check internal links from ASHWOOD `/journal` and `/dispatch` entries, including links to ALVIRA, for resolution and correctness.
7. Rank findings by severity.
8. If nothing is above threshold → skip (§4).
9. Open **one** draft PR per surface containing only the mechanical fixes (§7 exclusions apply).
10. Record an evidence event.

## 7. Output destination and externally visible side effects

Destination: a **draft pull request** against `tk-ap/ashwood-info` and/or `tk-ap/ALVIRA`.

**The routine never merges and never deploys.** Nothing it does is visible to a site visitor until TK merges.

**Strictly in scope** — mechanical, non-editorial changes: sitemap entries, `lastmod` values, canonical tags, `robots.txt` correctness, structured-data syntax, alt text on existing images, broken or malformed internal links, redirect-chain cleanup.

**Strictly out of scope** — anything that changes what the site *says*: page copy, headlines, titles and meta descriptions that carry positioning language, pricing statements, new pages, navigation structure, or claims of any kind. Per `agents/marlo/IDENTITY.md` §09, product landing pages and live positioning are draft-only and `approve-required`; this routine does not hold and does not request that authority. A finding in this class is **reported in the PR description as a recommendation for TK, never implemented.**

## 8. Authority class and required approvals

**Authority class:** `AUTONOMOUS + AUDIT` under `policies/AUTONOMY_POLICY.md` — the action is within role, reversible, credential-free, and produces no externally visible change on its own.

**Decision: `allow`** for read-only fetching of public pages and for opening draft PRs. **`deny`** for merging, deploying, editing copy, and any authenticated access. Merge is `approve-required` and belongs to TK.

## 9. Concurrency and duplicate execution

Single-flight per surface. A tick that fires while a run is in progress is skipped, not queued.

At most **one open audit PR per surface** at any time. If the previous PR is still unmerged, the next run updates that branch rather than opening a second — an accumulating stack of stale audit PRs is itself a failure mode.

## 10. Idempotency and reconciliation

Findings are keyed by `(surface, URL, finding type)`. A finding already present in the open PR is not duplicated. A finding TK previously closed without merging is recorded as **declined** and suppressed until the underlying page changes — the routine does not re-litigate a human decision on a weekly cycle.

## 11. Dry-run / staging path

The routine's normal mode *is* its dry-run: a draft PR is not a mutation. For the first three runs it opens the PR with findings only and no code changes, so the finding quality can be judged before any diff is reviewed.

## 12. Validation rules for generated output

A PR fails validation if it:
- modifies any file outside the mechanical scope in §7;
- alters rendered user-visible copy;
- changes routing, redirects, or `robots.txt` in a way that could de-index a live page;
- adds a sitemap entry for a route that does not return 200;
- contains a traffic, ranking, or volume claim presented as measured;
- fails the target repository's build or existing checks.

De-indexing risk is treated as the highest-severity validation class: a change that could remove a live page from search is escalated to TK even when technically correct.

## 13. Retry policy and ceiling

Maximum **2** retries per fetch, for transient network failure only. A URL failing after retries is recorded as a finding, not as a routine error — an unreachable page is exactly what this routine exists to notice.

No retry on PR creation after an ambiguous timeout; reconcile against the open-PR list first (§9).

## 14. Circuit breakers

- Maximum **1** PR per surface per run.
- Halt if findings exceed **25** on a surface in one run — that volume implies a structural change or a broken build, which is a human diagnosis, not a batch of mechanical fixes.
- Halt if more than **20%** of fetched URLs return non-200 — likely an outage or a deploy in flight; auditing during one produces false findings.
- Hard ceiling of **60 URL fetches per run** — roughly 3× the 18 URLs currently published across both sitemaps, leaving room for discovered internal links without permitting an unbounded crawl.
- Per-run ceilings: **500K input tokens, 30K output tokens, 20 minutes wall clock, $5.00.**

## 15. Anomaly conditions — pause and escalate

Suspend and escalate when:
- either surface is wholly unreachable;
- `robots.txt` has changed unexpectedly since the last run, in either direction;
- sitemap URL count changes by more than half between runs;
- a page returns a status suggesting an access-control change rather than a routing bug;
- the diff would touch a file outside the mechanical scope;
- the same finding recurs after having been merged as fixed — that indicates a build process overwriting the fix, which no further PR will solve.

## 16. Cost assumptions and caps

Projected: **~$1.00–1.50** per findings run, **~$0.40** per clean run, **~$2.85/month** on Claude Opus 5. Basis and method: `routines/COST_PROJECTIONS.md`.

Caps: **$5.00 per run**, **$30 per month**, plus the 60-fetch ceiling in §14.

**Pre-extraction is why this routine is affordable.** Feeding raw page HTML into context costs 3–4× more per run — roughly $3.50–5.50 against $1.00–1.50 — because ~40 pages at ~10KB each put over 110K tokens into a run and compound on every turn. That is why §6 extracts `<head>`, meta, canonical, and link elements outside the model and passes only those. It is a contract requirement, not an optimization, and a run that skips it will trip the per-run cap rather than quietly costing more.

The deploy-trigger decision in §3 waits on three measured weekly runs.

**Projections, not measurements.** Re-base from the first three runs.

## 17. Human review requirements

Human review is **structural and permanent** here: every change this routine proposes reaches the public surface only through a TK merge. There is no review-reduction path, because the routine has no unattended side effect to reduce review over.

Status still drops to `SUSPENDED` on any anomaly (§15) or stop condition (§20).

## 18. Success criteria and verification

A run succeeds when: both surfaces were fetched, the sitemap/route diff completed in both directions, findings were ranked and deduplicated against prior decisions, and either a PR was opened/updated or the run correctly skipped.

Verification, owned by W Dog, is independent of the audit and confirms that merged fixes actually took effect on the live surface — a sitemap entry is verified by fetching the URL it claims, not by reading the file.

**Capability limit, stated deliberately:** verification here is HTTP-level and requires no privileged browser. Browser-based interaction checks are **not** part of this routine. Per `docs/security/BROWSER_EXECUTION_ACCEPTANCE.md`, browser execution remains behind an unresolved runtime-attestation gate where `READY` means only that a request is admissible; a run reaches `VERIFIED` only with trusted runtime attestation. `runtime/browser_evidence.py` normalizes such evidence when a check has been run — it does not itself authorize one. Interaction-level verification stays a separately gated, human-initiated activity until that gate is closed.

## 19. Evidence destination and audit trail

Each run records: run ID, timestamp, surfaces audited, URLs fetched with status codes, findings by severity, findings suppressed as previously declined, PR opened or updated, skip decision, verification result, and cost when known.

Destination: `docs/evidence/routines/discoverability-audit/<YYYY-MM-DD>-<run-id>.json`. Record shape and rules: `docs/evidence/routines/README.md`.

Kept separate from `docs/security/evidence/`, which is security acceptance and attestation evidence; mixing operational run history into it would dilute both.

## 20. Stop conditions, suspension, rollback

**Stop:** two consecutive failed runs; any attempted change outside the mechanical scope; any attempt to merge, deploy, or authenticate; three or more unmerged audit PRs accumulating across surfaces, which indicates the routine is producing findings TK does not want.

**Suspension:** set status `SUSPENDED` and unbind the scheduler in the host adapter.

**Rollback:** close the draft PR. Nothing reached production, so no site-level rollback exists. For a merged PR later found harmful, `git revert` plus redeploy, with the reversal recorded as an evidence event.

## 21. Loop termination and escalation

No producer/inspector loop. A finding rejected twice by TK is marked permanently declined and never re-raised for the same page state.

Escalation owner: **TK.** Router coordinates. Rook reviews any anomaly involving `robots.txt`, access control, or de-indexing risk.

---

## Authority state

`allow` for anonymous read of public pages and for draft PR creation. `deny` for merge, deploy, copy changes, and authenticated access. No credentials are held or required.

## Next permitted action

All prerequisites are resolved. Bind the routine to a weekly scheduler in the host adapter, with the **first three runs reporting findings only and no diff** (§11), so finding quality can be judged before any patch is reviewed.

Then re-base §16 from measured cost and settle the deploy-trigger question.
