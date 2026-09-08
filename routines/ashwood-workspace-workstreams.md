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
  (title, canonical URL, open/closed → status) plus registry-resolved owner and
  product. The manifest holds only stable descriptors (summary, stage, next
  gate, goal ids), never execution progress.
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
