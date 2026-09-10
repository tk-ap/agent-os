# Routines — Backlog & Radar

Deferred work and pending handoffs for the routines in this directory. Not a task queue with authority; items here are proposals and reminders until they enter a task envelope.

## Open handoffs to TK

Items a routine produced and handed over. Marlo appends here on publish; TK clears them.

| Date | Routine | Item | Status |
|---|---|---|---|
| — | — | *(none yet — no routine has run)* | — |

**Dispatch cross-posts land in this table.** Per `agents/marlo/IDENTITY.md` §09, publishing a dispatch page to the site is permitted and sending it to `tkashwood.substack.com` subscribers is not. Every published dispatch appends a row here naming the dispatch and its URL, and the same handoff is recorded in the run's evidence record. Clearing the row is TK's action, and the send itself never becomes a routine's to make.

## Deferred — Substack

**Automated cross-post delivery with read-confirmation.** *Deferred 2026-09-06 at TK's direction; keep on radar.*

The dispatch routine currently satisfies its §09 handoff obligation by recording it (backlog row + evidence field) rather than delivering it through a channel. That is sufficient for governance and verification, and it removed the blocker that would otherwise have kept `ashwood-dispatch` in `DRAFT`.

What is deferred is only ergonomics: a delivery channel that actively notifies TK a cross-post is waiting, and a confirmation signal that closes the loop when it has been sent.

**Scope boundary if this is ever picked up:** it covers *notifying TK that a cross-post is pending*. It does not cover sending to subscribers. An automated notification is not a step toward automated distribution, and building one grants no authority over the Substack surface — §09's boundary holds regardless of how convenient the handoff becomes.

## Radar — ALVIRA as an on-ramp to a customer's own Agent OS

*Parked 2026-09-08 at TK's direction: "we should make that a separate think tank of a project."*

The question is whether ALVIRA should be positioned as the path by which a customer stands up
their own agent control plane, rather than only producing context that some other runtime
consumes.

The pieces already exist and interlock. Build Brief turns maintained context into a portable
specification for whichever AI builder or agentic environment the user prefers, which is
already the "be the format, not the platform" answer. ailhat already emits Drift as one of
its four intelligence outputs. `contracts/context-envelope.schema.json` already pins
`context_origin` to `alvira-context`.

The argument against making it the entry point: it is the largest category a customer could
be asked to learn, and it directly opposes the near-term direction ratified the same day —
failure-triggered Context correction wins precisely because the user has to adopt nothing.
Both stories on one homepage produces the abstract positioning the Littlebird memo warns
about in 8.1. There is also a resourcing reality: provisioning customer agent infrastructure
is a support burden, not a feature.

Working shape if picked up: front door is "your AI keeps getting you wrong"; hallway is
Build Brief; Agent OS is a door at the end that people already running agents *discover*,
offered as a reference implementation rather than a provisioned service.

**Not started.** Scope boundary: this is a positioning and sequencing question, not
authorization to build agent-provisioning features. The ailhat-culls-Agent-OS-members-per-project
idea is explicitly out of scope until a user reports the problem it solves.

## Radar — Telegram / Mr. Milchik connection to Agent OS

*Raised 2026-09-06. Parked, not started.*

`adapters/hermes/fleet/` already contains a working Telegram review inbox — "Mr. Milchik" — with review cards, Accept / Needs changes / Pause buttons, acceptance bound to card ID, paired user and chat, message ID, task status, work-order digest and git fingerprint, and 24-hour expiry. It is the obvious channel for everything these routines currently have nowhere to send: escalations, suspensions, PR-mode approvals, cap breaches, and the dispatch cross-post handoff.

**Connected 2026-09-06.** The bot is configured and paired (`~/.hermes/agent-os-telegram.json`, mode 0600), and `hermes-gateway.service` is running, so the tick that drives delivery is live.

What it carries today is fleet review cards. Routine escalations, approvals, cap breaches, and the dispatch handoff are **not** wired to it.

**Known Hermes behaviour, worth watching.** On 2026-09-06 the Hermes desktop app was observed calling `xdg-open` on the Milchik pairing deep link *after pairing had already completed*, spawning a browser each time because no `tg://` handler was registered. The handler is fixed — `telegram-desktop` is installed and owns `x-scheme-handler/tg` — so the symptom is gone. The underlying behaviour, reopening a stale one-time pairing link, was not addressed and is a Hermes-side issue rather than an Agent OS one. If it recurs it now opens Telegram rather than a browser, which is harmless but still wrong.

Two things to settle before binding routines to it, both governance rather than plumbing:

1. `fleet/TELEGRAM.md` states the current bot handles fleet result acceptance only, and that HUMAN_GATE and deployment approval "require separate action-specific bindings." Routine approvals are a new binding, not a reuse.
2. Notification and approval must stay separate. A card that tells TK a routine suspended is not the same object as a card that lets TK resume it, and the Substack boundary in `agents/marlo/IDENTITY.md` §09 means no button may ever send a dispatch to subscribers.

## Open — ALVIRA discoverability, live defect

*Found 2026-09-06 by `adapters/hermes/routines/monitors/discoverability-fingerprint.sh`.*

`alviratech.vercel.app` is the live ALVIRA surface. Its `sitemap.xml` still lists all 10 canonical URLs on `alvira.ctonew.app`, the decommissioned cto.new domain that returns 503, and its `robots.txt` points crawlers at a sitemap on that dead host.

De-indexing risk — the highest-severity class in `discoverability-audit.md` §12. Fix is in `tk-ap/ALVIRA`: `public/sitemap.xml`, `public/robots.txt`. Three further legacy references in `ALVIRA_LOGO_FIDELITY_FIX_BRIEF.md`, `docs/VERCEL_RUNTIME_MIGRATION.md`, `codex/launch-readiness-report`.

Not fixed by Agent OS — cross-product writes default to `propose-handoff`, and the audit routine is read-and-propose only. Worth clearing before the routine is scheduled, so its first real run is not dominated by one known defect.

## Deferred — routine mechanics

| Item | Blocked on | Notes |
|---|---|---|
| Deploy-triggered runs for `discoverability-audit` | Three measured weekly runs | Main driver of run volume; the decision is economic, and there is no measurement behind it yet (`discoverability-audit.md` §3, §16). |
| Re-base all cost caps from measurement | First three runs of each routine | `COST_PROJECTIONS.md` §7. Turn count dominates the estimate and is the least certain term in it. |
| Evidence ledger with `visibility` classification | Decision | Blocks both ASHWOOD publishing routines. `runtime/evidence.py` returns an in-memory dict per task run and persists nothing queryable. Journal has an interim commit-derived option; dispatch has none. |
| Cap enforcement | Implementation | Caps are contract terms today, checked by reading evidence records. Nothing measures spend at a turn boundary or trips the $75 portfolio breaker. |
| Machine-readable `routine` contract in `contracts/v0/` | Decision | `contracts/v0/` defines `task`, `workflow`, `harness`, `host`, `evidence` — no `routine`. These contracts are prose until that is settled. |
| Harness selection per routine | Decision | `registry/harnesses.yaml` registers `claude-code` and `codex-cli`. Cost projections assume a Claude harness; a Codex run prices differently and needs its own caps. |

## Not in scope for any routine

Recorded so the boundary stays visible rather than being rediscovered each time:

- Sending to Substack subscribers.
- Social posting, outreach, and email of any kind — including through the AgentMail skills in `registry/skills.yaml`.
- Product landing page copy, positioning, and pricing changes on ALVIRA or ASHWOOD.
- Browser-based interaction verification, which remains behind the unresolved runtime-attestation gate in `docs/security/BROWSER_EXECUTION_ACCEPTANCE.md`.

All are `approve-required` or gated. None becomes permitted through a routine's track record.
