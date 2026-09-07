# Task Envelope — Discoverability & Route Integrity Audit

**ID:** `env-discoverability-audit` · **Routine:** `routines/discoverability-audit.md` · **Created:** 2026-09-06

## Objective and expected outcome

Keep the technical discoverability and route integrity of `ashwood-info.vercel.app` and `alviratech.vercel.app` from decaying between manual passes, by auditing both continuously and proposing mechanical fixes as draft pull requests.

Outcome: sitemap coverage, canonical and metadata correctness, structured data, and internal linking from ASHWOOD entries into ALVIRA stay maintained. This is the only envelope of the three that acts on ALVIRA's surface, and it does so without touching what the site says.

## Originating signal and evidence

Observed state, corrected 2026-09-06: ALVIRA's live surface is `alviratech.vercel.app`; the cto.new domain `alvira.ctonew.app` is decommissioned and returns 503, and is not an audit target. ASHWOOD publishes 8 URLs in `sitemap.xml`; ALVIRA publishes 10 (`/`, `/pricing`, `/why-alvira`, `/interview`, `/meos`, `/data`, plus legal). Both allow all crawlers. No routine currently checks either against actual routes, in either direction.

This is a measured baseline, not a claim about traffic. Nothing here asserts that these counts are wrong — only that nothing verifies them.

## Owning product / shared capability

Shared workforce capability (Growth / Marketing Engineering), acting on the **ashwood** and **alvira-meos** products (`registry/product-routing.yaml`: `tk-ap/ashwood-info`, `tk-ap/ALVIRA`).

Neither product's ownership transfers. This envelope produces proposals; each product's owner disposes of them.

## Accountable owner and executing agents

**Accountable:** TK. **Executing:** Eugene. **Verification:** W Dog. **Risk:** Rook — specifically for de-indexing and access-control risk. **Economics:** Ledger. **Sequencing:** Bill. **Coordination:** Router.

## Repositories, environments, exact targets

- **Repositories:** `tk-ap/ashwood-info`, `tk-ap/ALVIRA`
- **Target:** draft pull requests only — no branch merge, no deploy
- **Environments read:** the two live production sites, fetched anonymously over HTTP
- **Not targets:** authenticated pages, any account-gated ALVIRA surface, analytics platforms, search consoles

## Context and provenance

Supplied context: the two public surfaces as an anonymous visitor sees them, their `robots.txt` and `sitemap.xml`, and the two repositories' route definitions and build output.

**The routine holds no credentials and authenticates to nothing.** Findings cite the exact URL and HTTP response observed, with fetch timestamp.

Estimated impact is labeled as estimated. Search volume, traffic, mentions, and conversion are different signals and none is presented as another — no traffic claim is made from a discoverability finding.

## Constraints and protected regression boundaries

- **Protected above all: index status.** A change that could remove a live page from search is the highest-severity class here and escalates to TK even when technically correct.
- Protected: rendered user-visible copy, positioning language, pricing statements, navigation structure, page inventory, routing and redirect behavior, and the repositories' existing checks.
- ALVIRA is a revenue surface. This envelope may correct how it is described to machines; it may not change how it speaks to people.

## Permitted actions and required approvals

**Permitted without approval:** anonymous HTTP fetches of public pages; reading both repositories; opening or updating one draft PR per surface; recording evidence.

**In scope for a PR diff** — mechanical, non-editorial: sitemap entries and `lastmod` values, canonical tags, `robots.txt` correctness, structured-data syntax, alt text on existing images, broken or malformed internal links, redirect-chain cleanup.

**Out of scope, reported as a recommendation and never implemented:** page copy, headlines, titles and meta descriptions carrying positioning language, pricing, new pages, navigation. Per `agents/marlo/IDENTITY.md` §09 these are `approve-required`; this envelope neither holds nor requests that authority.

**Requires approval:** merging any PR. **Never permitted:** deploying, authenticating, or acquiring credentials.

Authorization state: **`allow`** for anonymous read and draft PR creation, class `AUTONOMOUS + AUDIT` per `policies/AUTONOMY_POLICY.md` — within role, reversible, credential-free, no externally visible change. **`deny`** for merge, deploy, copy change, and authenticated access.

## Estimated cost and human oversight

~$1.00–1.50 per findings run with pre-extracted page metadata, ~$0.40 clean, ~$2.85/month — `routines/COST_PROJECTIONS.md`. Caps: $5.00/run, $30/month, 60 URL fetches/run.

The naive implementation — full page HTML into context — costs 3–4× more per run. Pre-extraction is a contract requirement, not an optimization.

Oversight is **structural and permanent**: every proposed change reaches a public surface only through a TK merge. There is no review-reduction path, because there is no unattended side effect to reduce review over.

## Success criteria, verification, evidence destination

**Success:** both surfaces fetched; the sitemap/route diff completed in both directions; findings ranked and deduplicated against prior TK decisions; a PR opened or updated, or the run correctly skipped.

**Verification:** owned by W Dog and independent of the audit — a merged fix is verified by fetching the live URL it claims, never by re-reading the file that claims it.

**Capability limit:** verification here is HTTP-level. Browser-based interaction checks are out of scope, because browser execution remains behind an unresolved runtime-attestation gate (`docs/security/BROWSER_EXECUTION_ACCEPTANCE.md`) where `READY` means only that a request is admissible. `runtime/browser_evidence.py` normalizes such evidence; it does not authorize collecting it.

**Evidence:** `docs/evidence/routines/discoverability-audit/`.

## Stop conditions, rollback, handoff state

**Stop:** two consecutive failed runs; any attempted change outside the mechanical scope; any attempt to merge, deploy, or authenticate; three or more unmerged audit PRs accumulating, which indicates the routine is producing findings TK does not want.

**Rollback:** close the draft PR. Nothing reached production, so there is no site-level rollback. For a merged PR later found harmful: `git revert`, redeploy, record the reversal.

**Handoff state — open by design.** Every findings run leaves a PR owned by TK. The envelope completes at PR creation, not at merge.

## Portable contracts

The draft PR functions as the proposal artifact across the product boundary. `contracts/work-item.schema.json` would formalize the same handoff and is worth adopting only if ALVIRA's ownership later wants audit findings routed as tracked work items rather than PRs. Not required today.

## Missing fields and assumptions

- **Confirmed:** weekly cadence (TK, 2026-09-06).
- **Open:** whether to add a deploy-triggered run. Deferred pending measured run cost — it is the main driver of run volume.
- **Assumption:** ~30% of runs produce findings above threshold. Unmeasured; affects the period cost projection only.
- **Open:** which harness executes.

## Next permitted action

Bind the routine to a weekly scheduler in the host adapter, with the first three runs reporting findings only and no diff, so finding quality can be judged before any patch is reviewed.
