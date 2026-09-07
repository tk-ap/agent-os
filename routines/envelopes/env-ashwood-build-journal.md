# Task Envelope — ASHWOOD Build Journal & Field Notes

**ID:** `env-ashwood-build-journal` · **Routine:** `routines/ashwood-build-journal.md` · **Created:** 2026-09-06

## Objective and expected outcome

Keep ASHWOOD's public build record current by converting verified, publication-cleared build evidence into journal and field-note entries on a continuing basis.

Business outcome: a public record that accumulates without competing for TK's attention, and that gives ALVIRA a credible referring surface. Traffic to ALVIRA is a downstream effect, not the objective — the objective is that the record exists and stays current.

## Originating signal and evidence

Not an external signal. This envelope originates from an internal capability decision: Growth / Marketing Engineering is a shared workforce capability (`README.md`), and `agents/marlo/IDENTITY.md` §09 already grants unattended publish authority over these two path families. The work is authorized and unperformed — that gap is the signal.

Evidence: one field note and a populated journal structure exist at `tk-ap/ashwood-info`; publishing cadence to date is manual.

## Owning product / shared capability

Shared workforce capability (Growth / Marketing Engineering), executing into the **ashwood** product (`registry/product-routing.yaml`: `repository: tk-ap/ashwood-info`).

ASHWOOD "selectively documents validated decisions and learning as public evidence" and is explicitly **not** a source of operational truth. This envelope inherits that constraint: it projects evidence outward, it never becomes the record.

## Accountable owner and executing agents

**Accountable:** TK. **Executing:** Marlo. **Verification:** W Dog. **Risk:** Rook. **Economics:** Ledger. **Sequencing:** Bill. **Coordination:** Router.

## Repositories, environments, exact targets

- **Repository:** `tk-ap/ashwood-info`
- **Targets:** `/journal/*`, `/journal/field-notes/*` — no other path
- **Environment:** production site, `ashwood-info.vercel.app`
- **Read-only sources:** `tk-ap/ALVIRA`, `tk-ap/ailhat`, `tk-ap/ledgato`, `tk-ap/ashwood-info` history

## Context and provenance

Supplied context: audit evidence events classified `public-candidate`, and commit/PR history of the repositories above.

Excluded: private analytics, customer data, credentials, and ALVIRA context beyond permitted use. No `context-envelope.schema.json` reference is required, because no ALVIRA-derived durable context is consumed. If that changes, this field changes with it.

Inferred context stays distinguishable from verified context in every entry; per `skills/owned/audit-evidence-ledger/SKILL.md`, intended, simulated, preview, deployed, and user-validated states are never collapsed.

## Constraints and protected regression boundaries

- Public-facing surface: a bad entry is visible before it is caught.
- Protected: everything outside `/journal` — site chrome, navigation, existing entries, `/dispatch`, and the site build.
- Existing entries are append-only from this envelope's perspective; corrections are new entries referencing the old, never rewrites.
- ASHWOOD's voice is a product asset. An entry that is accurate but off-voice is a defect.

## Permitted actions and required approvals

**Permitted without approval:** read the sources above; draft an entry; commit it to the two granted path families; record evidence.

**Requires approval:** any other path, any other repository, any Substack or social or email action, any change to site structure or navigation.

**Never permitted from this envelope:** sending to subscribers, contacting anyone, spending money, changing production configuration, or touching credentials.

Authorization state: **`allow`**, standing, scoped to the two path families, per `agents/marlo/IDENTITY.md` §09.

## Estimated cost and human oversight

~$1.50–2.00 per publishing run, ~$0.25 per skip, ~$3.75/month on Claude Opus 5 — `routines/COST_PROJECTIONS.md`, projected not measured. Caps: $6.00/run, $25/month.

Oversight: PR mode until TK promotes the routine to `ACTIVE`; unattended thereafter, with review restored automatically on any anomaly.

## Success criteria, verification, evidence destination

**Success:** the entry exists at its expected URL, returns 200, appears in `sitemap.xml`, renders, is in voice, and every factual claim traces to a recorded evidence event.

**Verification:** HTTP-level, performed independently of publication, owned by W Dog. No privileged browser capability required.

**Evidence:** `docs/evidence/routines/ashwood-build-journal/`.

## Stop conditions, rollback, handoff state

**Stop:** two consecutive failed runs; any attempted write outside the granted paths; revocation or material change of the §09 grant.

**Rollback:** `git revert` the entry commit, redeploy, record the reversal as an evidence event.

**Handoff state:** none open. Marlo executes end to end within this envelope; nothing is handed to another agent or product.

## Portable contracts

None required. No product ownership transfers, and the grant is standing rather than negotiated per run — `contracts/work-item.schema.json` would add ceremony without carrying anything across a boundary. `contracts/outcome-event.schema.json` becomes useful only if these runs start feeding a portfolio consumer such as ailhat; not today.

## Missing fields and assumptions

- **Assumption:** weekly cadence (confirmed by TK 2026-09-06).
- **Assumption:** ~40% of weeks will have publishable evidence. Unmeasured; drives the period cost projection only.
- **Open:** which harness executes (`claude-code` or `codex-cli`). Cost projections assume a Claude harness.

## Next permitted action

Bind the routine to a scheduler in the host adapter in PR mode, run three times, and re-base the cost caps from measured token counts.
