# Task Envelope — ASHWOOD Dispatch Pages

**ID:** `env-ashwood-dispatch` · **Routine:** `routines/ashwood-dispatch.md` · **Created:** 2026-09-06

## Objective and expected outcome

Publish an ASHWOOD dispatch page when validated learning exists that is worth stating publicly, so dispatches appear on their evidentiary merit rather than stalling on TK's availability to run the publish step.

Outcome: the dispatch series continues at whatever rate the evidence actually supports. Subscriber distribution stays entirely TK's decision and is outside this envelope.

## Originating signal and evidence

Internal capability decision, same basis as `env-ashwood-build-journal`: §09 already grants unattended publish over `/dispatch/*`, and the authority is unused.

Evidence: one dispatch published (`/dispatch/001-the-mind-is-the-moat`). One data point establishes that the surface works; it establishes nothing about cadence, and this envelope does not pretend otherwise.

## Owning product / shared capability

Shared workforce capability (Growth / Marketing Engineering), executing into the **ashwood** product (`tk-ap/ashwood-info`).

A dispatch is a positioning artifact, which makes it a heavier object than a journal entry despite sharing a repository and an authority class. This envelope is deliberately more restrictive than the journal envelope in what it will publish.

## Accountable owner and executing agents

**Accountable:** TK. **Executing:** Marlo. **Verification:** W Dog. **Risk:** Rook. **Economics:** Ledger. **Sequencing:** Bill. **Coordination:** Router.

## Repositories, environments, exact targets

- **Repository:** `tk-ap/ashwood-info`
- **Target:** `/dispatch/*` — no other path
- **Environment:** production site, `ashwood-info.vercel.app`
- **Explicitly not a target:** `tkashwood.substack.com`, and every social, email, and outreach surface

## Context and provenance

Supplied context: validated `LEARNING` records from `skills/owned/market-truth-growth-intelligence/SKILL.md` or an equivalent validated-outcome source, plus the evidence events behind them.

Excluded: signals still at `SIGNAL` or `INTERPRETATION` stage, unverified market claims, private analytics, customer data. **An interpretation is not a learning**, and this envelope does not permit publishing one as if it were.

Recency is stated; stale evidence is labeled; surviving counter-evidence is stated rather than omitted.

## Constraints and protected regression boundaries

- Positioning surface: a dispatch says what the company believes, so an unsupported claim here costs more than an unsupported claim in a build note.
- Protected: `/journal`, site chrome, navigation, existing dispatches, the dispatch index, and dispatch numbering.
- No forward-looking commitments, roadmap promises, pricing statements, or legal representations — all exceed delegated authority under `policies/AUTONOMY_POLICY.md`.

## Permitted actions and required approvals

**Permitted without approval:** read the sources above; draft one dispatch; commit it to `/dispatch/*`; record evidence; record the Substack cross-post as a handoff item for TK.

**Requires approval:** any other path or repository; any change to an existing dispatch.

**Structurally excluded, not merely unapproved:** sending to Substack subscribers. The routine holds no capability to send and must not acquire one at runtime. Per §09 this never becomes permitted through repetition or an accumulated track record.

Authorization state: **`allow`** for the page commit, scoped to `/dispatch/*`. **`deny`** for subscriber distribution.

## Estimated cost and human oversight

~$2.00–2.50 per publishing run, ~$0.25 per skip, ~$2.25/month at ~12 dispatches a year — `routines/COST_PROJECTIONS.md`, projected not measured. Caps: $8.00/run, $25/month.

Oversight: PR mode is the **recommended steady state** here, not merely the starting state, until at least three dispatches have been produced and reviewed under this envelope. A positioning artifact earns unattended publication by demonstrated track record, not by inheriting the journal's.

## Success criteria, verification, evidence destination

**Success:** the dispatch exists at its expected URL, returns 200, appears in `sitemap.xml`, renders, every claim traces to cited evidence, **and the cross-post handoff is recorded for TK.**

A published page with no recorded handoff is a failed run.

**Verification:** HTTP-level, independent of publication, owned by W Dog.

**Evidence:** `docs/evidence/routines/ashwood-dispatch/`.

## Stop conditions, rollback, handoff state

**Stop:** two consecutive failed runs; any attempted write outside `/dispatch/*`; any attempt to reach Substack, social, or email; revocation or material change of the §09 grant.

**Rollback:** `git revert`, redeploy, record the reversal. Note the asymmetry: if TK has already cross-posted, reverting the page does not reverse the send. The evidence record states that rather than implying full reversibility.

**Handoff state — open by design.** Every published dispatch leaves one item owned by TK: the Substack cross-post. This envelope is not complete on publication; it is complete when the handoff is recorded and TK holds it.

## Portable contracts

None required for the page commit. The Substack cross-post is a handoff to a human, not a cross-product work item, and does not need `contracts/work-item.schema.json` to be legible.

## Missing fields and assumptions

- **Confirmed:** event-driven trigger, no calendar cadence, 14-day minimum spacing (TK, 2026-09-06).
- **Assumption:** ~12 dispatches a year, extrapolated from one published dispatch. Weak evidence; affects the cost projection and nothing else.
- **Resolved 2026-09-06:** the handoff is satisfied by a recorded evidence entry plus a backlog item, not by an automated delivery channel. Automated delivery with confirmation is deferred to `routines/BACKLOG.md`.
- **Open:** which harness executes.

## Next permitted action

Bind the routine to an event trigger in the host adapter in PR mode. Do not promote to `ACTIVE` before three reviewed dispatches.
