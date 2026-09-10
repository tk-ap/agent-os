# Routine — ASHWOOD Workspace Workstream Projection

**ID:** `ashwood-workspace-workstreams`
**Status:** `REVIEWED-PENDING` — implements agent-os issue #54; not `ACTIVE` until the sync token is confirmed (see §4).
**Owner (design):** Router · **Executing agent:** Eugene · **Source-of-truth review:** W Dog · **Auth / data-minimization review:** Rook · **Human liaison:** Milchik

---

## 1. Purpose

Publish a human-facing projection of AgentOS-owned workstreams into ASHWOOD
`/workspace` for cross-life/company/creative synthesis, without moving execution
truth out of AgentOS. AgentOS stays canonical for execution state, ownership,
review lifecycle, approvals, and issue/work-order state.

Not a second task system. No duplicate execution database in ASHWOOD.

## 2. Executable

`python -m runtime.workspace_workstreams` (add `--dry-run` to build and print the
snapshot without sending). Source manifest: `registry/workspace-workstreams.json`.

## 3. Sync behavior

- Derives each projection from **current AgentOS state**: the live GitHub issue
  (title, canonical URL) plus registry-resolved owner and product. The manifest
  holds only stable descriptors (summary, stage, next gate, goal ids, and an
  optional `work_id` link), never execution progress.
- **Status comes from AgentOS execution state when there is any.** A source may
  carry an optional `work_id`; when it names a live fleet order, that order's
  phase decides the status and the issue's open/closed lifecycle is only the
  fallback. Deriving status from GitHub alone contradicted this routine's own
  premise that AgentOS is canonical for execution state, and collapsed
  `waiting_approval`, `blocked` and `review` into a single indistinguishable
  `ACTIVE`.
- Status values use the vocabulary ASHWOOD already renders: `workspace/
  workstreams.mjs` colours `blocked`/`failed` as risk and `waiting_approval`/
  `review` as a decision, and `workspace/priorities.mjs` surfaces
  "AgentOS · needs you" for that second group. Emitting only `ACTIVE` and `DONE`
  meant that path could never fire. `waiting_capacity` maps to `in_progress`
  rather than a decision: work parked on an exhausted provider resumes on its
  own and needs nobody.
- Sends `source_id, source_system, canonical_url, title, summary, product,
  owner, status, stage, next_gate, goal_ids, confidence, metadata, observed_at`.
- Authenticates with the existing `WORKSPACE_BOARD_SYNC_TOKEN` contract (Bearer).
- Publishes with `replace: true` scoped to `source_system=agent-os`, so ASHWOOD
  clears stale agent-os rows but never deletes other source systems' projections.
- **Fails visibly, never blocks AgentOS execution:** a missing token or an
  ASHWOOD outage returns `ok:false` with a reason and a non-zero exit; it does
  not raise into any caller. A projection/derivation error fails before anything
  is sent.
- Never sends secrets, private task payloads, raw prompts, or credentials — a
  secret-pattern backstop refuses to publish a row that matches one.

## 4. Trigger source — blocking `ACTIVE`

The publisher is runnable now, but going `ACTIVE` on a scheduled tick requires
`WORKSPACE_BOARD_SYNC_TOKEN` to be present in the AgentOS runtime environment.
Per the issue lifecycle, Milchik surfaces that credential/configuration decision
to TK; nothing else in this routine needs a human.

## 5. First workstreams

`tk-ap/agent-os#51` (Ledgato external-user readiness / technical proof) and
`tk-ap/agent-os#53` (Scout-owned Ledgato design-partner outreach). Both project
to product `ledgato` with a canonical link back to the AgentOS issue.

## 6. Acceptance (issue #54)

Owner/status/next-gate update when AgentOS state changes (owner and status are
derived, not copied); projection links to canonical source; no duplicate
execution DB; ASHWOOD outage does not interrupt AgentOS work; stale/failed sync
is detectable (`ok:false` + exit code); no sensitive context crosses the
boundary.
