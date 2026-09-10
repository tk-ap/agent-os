import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

from runtime import workspace_workstreams as w


def fake_issue(repo, number):
    return {
        "number": number,
        "title": f"Live title for {repo}#{number}",
        "state": "OPEN",
        "url": f"https://github.com/{repo}/issues/{number}",
    }


def closed_issue(repo, number):
    d = fake_issue(repo, number)
    d["state"] = "CLOSED"
    return d


NOW = "2026-09-08T00:00:00+00:00"


class ManifestTests(unittest.TestCase):
    def test_ships_the_two_first_workstreams(self):
        m = w.load_manifest()
        issues = {s["issue"] for s in m["sources"]}
        self.assertIn(51, issues)
        self.assertIn(53, issues)
        self.assertEqual(m["source_system"], "agent-os")

    def test_manifest_holds_no_execution_progress_fields(self):
        # Guard against the manifest drifting into a duplicate task DB.
        m = w.load_manifest()
        forbidden = {"status", "assignee", "progress", "state", "completed", "review"}
        for s in m["sources"]:
            self.assertFalse(forbidden & set(s.keys()),
                             f"manifest source {s['issue']} carries execution state")


class SnapshotTests(unittest.TestCase):
    def build(self, fetcher=fake_issue):
        return w.build_snapshot(issue_fetcher=fetcher, now=NOW)

    def test_snapshot_is_agent_os_scoped_replace(self):
        snap = self.build()
        self.assertEqual(snap["source_system"], "agent-os")
        self.assertTrue(snap["replace"])  # replace only agent-os rows, keep others

    def test_feed_contains_both_sources(self):
        ids = {r["source_id"] for r in self.build()["rows"]}
        self.assertEqual(ids, {"agent-os#51", "agent-os#53"})

    def test_title_and_url_are_derived_live_not_from_manifest(self):
        row = next(r for r in self.build()["rows"] if r["source_id"] == "agent-os#51")
        self.assertEqual(row["title"], "Live title for tk-ap/agent-os#51")
        self.assertEqual(row["canonical_url"], "https://github.com/tk-ap/agent-os/issues/51")

    def test_status_derives_from_live_issue_lifecycle(self):
        self.assertEqual(self.build(fake_issue)["rows"][0]["status"], "active")
        self.assertEqual(self.build(closed_issue)["rows"][0]["status"], "done")

    def test_owner_51_is_router_derived(self):
        row = next(r for r in self.build()["rows"] if r["source_id"] == "agent-os#51")
        # verification class routes to an independent verifier, not a literal name in the manifest
        self.assertIn(row["owner"], {"w-dog", "rook"})
        self.assertEqual(row["metadata"]["owner_spec"], "@router:verification")

    def test_owner_53_is_scout(self):
        row = next(r for r in self.build()["rows"] if r["source_id"] == "agent-os#53")
        self.assertEqual(row["owner"], "scout")

    def test_both_carry_ownership_goal(self):
        for r in self.build()["rows"]:
            self.assertIn("ownership", r["goal_ids"])

    def test_product_is_ledgato_for_both(self):
        for r in self.build()["rows"]:
            self.assertEqual(r["product"], "ledgato")

    def test_rows_conform_to_schema_shape(self):
        required = {"source_id", "source_system", "title", "status"}
        allowed = required | {"canonical_url", "summary", "product", "owner", "stage",
                              "next_gate", "goal_ids", "confidence", "metadata", "observed_at"}
        for r in self.build()["rows"]:
            self.assertTrue(required <= set(r), f"missing required field in {r['source_id']}")
            self.assertTrue(set(r) <= allowed, f"unexpected field in {r['source_id']}")
            self.assertIsInstance(r["goal_ids"], list)
            self.assertLessEqual(len(r["goal_ids"]), 12)
            self.assertGreaterEqual(r["confidence"], 0)
            self.assertLessEqual(r["confidence"], 1)
            self.assertLessEqual(len(r["title"]), 500)
            self.assertLessEqual(len(r["status"]), 40)


class DerivationGuardTests(unittest.TestCase):
    AGENTS = {"scout": {}, "w-dog": {}, "rook": {}}
    ROUTING = "products:\n  ledgato:\n    repository: tk-ap/ledgato\n"

    def row(self, source, fetcher=fake_issue):
        return w.build_row(source, agents=self.AGENTS, routing_text=self.ROUTING,
                           issue_fetcher=fetcher, now=NOW)

    def base(self, **kw):
        s = {"issue": 51, "repo": "tk-ap/agent-os", "product": "ledgato",
             "owner": "scout", "goal_ids": ["ownership"]}
        s.update(kw)
        return s

    def test_unknown_owner_is_rejected(self):
        with self.assertRaises(w.ProjectionError):
            self.row(self.base(owner="ghost"))

    def test_missing_ownership_goal_is_rejected(self):
        with self.assertRaises(w.ProjectionError):
            self.row(self.base(goal_ids=["leadership"]))

    def test_unknown_product_is_rejected(self):
        with self.assertRaises(w.ProjectionError):
            self.row(self.base(product="not-a-product"))

    def test_secret_in_projection_is_refused(self):
        leak = "ghp_" + "A" * 36
        with self.assertRaises(w.ProjectionError):
            self.row(self.base(summary=f"token {leak}"))

    def test_long_fields_are_capped(self):
        row = self.row(self.base(next_gate="x" * 5000))
        self.assertEqual(len(row["next_gate"]), 1000)


class PublishTests(unittest.TestCase):
    SNAP = {"source_system": "agent-os", "replace": True,
            "rows": [{"source_id": "agent-os#51", "title": "t", "status": "ACTIVE",
                      "source_system": "agent-os", "goal_ids": []}]}

    def test_missing_token_fails_visibly_without_raising(self):
        with patch.dict("os.environ", {}, clear=True):
            res = w.publish(self.SNAP, endpoint="https://x/y", token=None)
        self.assertFalse(res["ok"])
        self.assertIn("not configured", res["reason"])

    def test_ashwood_outage_does_not_raise(self):
        def broken_opener(req, timeout=10):
            raise urllib.error.URLError("connection refused")
        res = w.publish(self.SNAP, endpoint="https://x/y", token="t", opener=broken_opener)
        self.assertFalse(res["ok"])
        self.assertIn("unreachable", res["reason"])

    def test_http_error_is_captured_not_raised(self):
        import io
        def erroring_opener(req, timeout=10):
            raise urllib.error.HTTPError("https://x/y", 403, "Forbidden", {},
                                         io.BytesIO(b'{"error":"Invalid sync token"}'))
        res = w.publish(self.SNAP, endpoint="https://x/y", token="t", opener=erroring_opener)
        self.assertFalse(res["ok"])
        self.assertEqual(res["reason"], "HTTP 403")

    def test_success_sends_bearer_token_and_reports_count(self):
        captured = {}
        class Resp:
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def read(self): return b'{"ok":true,"upserted":1}'
        def opener(req, timeout=10):
            captured["auth"] = req.headers.get("Authorization")
            captured["url"] = req.full_url
            captured["method"] = req.get_method()
            captured["body"] = json.loads(req.data)
            return Resp()
        res = w.publish(self.SNAP, endpoint="https://ashwood/api", token="s3cret", opener=opener)
        self.assertTrue(res["ok"])
        self.assertEqual(res["sent"], 1)
        self.assertEqual(captured["auth"], "Bearer s3cret")
        self.assertEqual(captured["method"], "POST")
        # replace scoping travels in the body so ASHWOOD keeps other systems' rows
        self.assertEqual(captured["body"]["source_system"], "agent-os")
        self.assertTrue(captured["body"]["replace"])

    def test_token_is_never_in_the_payload_body(self):
        captured = {}
        class Resp:
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def read(self): return b'{}'
        def opener(req, timeout=10):
            captured["body"] = req.data.decode()
            return Resp()
        w.publish(self.SNAP, endpoint="https://ashwood/api", token="s3cret-token", opener=opener)
        self.assertNotIn("s3cret-token", captured["body"])


class DryRunTests(unittest.TestCase):
    def test_dry_run_builds_but_does_not_publish(self):
        with patch.object(w, "_gh_issue_state", fake_issue):
            res = w.run(dry_run=True)
        self.assertTrue(res["dry_run"])
        self.assertEqual(len(res["snapshot"]["rows"]), 2)

    def test_building_a_snapshot_makes_no_network_call(self):
        """The patch above only works because the fetcher is resolved on call.
        While it was a default argument the mock never applied, so this suite
        was reaching the live GitHub API and passed only where gh was logged
        in. Fail loudly rather than quietly go to the network."""
        def forbidden(*args, **kwargs):
            raise AssertionError("build_snapshot reached the live GitHub API")
        with patch.object(w, "_gh_issue_state", forbidden):
            with self.assertRaises(AssertionError):
                w.build_snapshot()
        with patch.object(w, "_gh_issue_state", fake_issue):
            snapshot = w.build_snapshot()
        self.assertEqual(len(snapshot["rows"]), 2)


if __name__ == "__main__":
    unittest.main()


class ExecutionStatusTests(unittest.TestCase):
    """AgentOS is canonical for execution state, so a linked fleet order decides
    the status. Deriving it from the GitHub issue alone collapsed every live
    phase into ACTIVE, so a workstream waiting on TK looked identical to one
    running fine -- and ASHWOOD, which already renders "AgentOS · needs you" for
    waiting_approval/review/blocked, could never show it."""

    SOURCE = {"issue": 51, "repo": "tk-ap/agent-os", "product": "ledgato",
              "owner": "scout", "goal_ids": ["ownership"], "stage": "s",
              "summary": "x", "next_gate": "g", "confidence": 0.5,
              "work_id": "some-fleet-work"}

    AGENTS = {"scout": {}, "w-dog": {}, "rook": {}}
    ROUTING = "products:\n  ledgato:\n    repository: tk-ap/ledgato\n"

    def _row(self, phase, source=None, issue_state="OPEN"):
        return w.build_row(
            dict(source or self.SOURCE),
            agents=self.AGENTS, routing_text=self.ROUTING,
            issue_fetcher=lambda repo, number: {
                "title": "t", "url": "https://example.invalid", "state": issue_state},
            execution_fetcher=lambda work_id: phase)

    def test_a_linked_order_decides_the_status(self):
        self.assertEqual(self._row("running")["status"], "in_progress")
        self.assertEqual(self._row("blocked")["status"], "blocked")
        self.assertEqual(self._row("done")["status"], "done")

    def test_work_waiting_on_tk_reads_as_needing_him(self):
        """ASHWOOD's priorities.mjs treats these as NEEDS_OWNER and labels the
        row "AgentOS · needs you"."""
        needs_owner = {"waiting_approval", "decision_required", "review",
                       "blocked", "needs_attention"}
        self.assertIn(self._row("waiting_approval")["status"], needs_owner)
        self.assertIn(self._row("review")["status"], needs_owner)

    def test_waiting_on_a_provider_does_not_read_as_needing_him(self):
        """Capacity-parked work resumes on its own. Showing it as a decision is
        the same false alarm the operator cards were fixed for."""
        needs_owner = {"waiting_approval", "decision_required", "review",
                       "blocked", "needs_attention"}
        self.assertNotIn(self._row("waiting_capacity")["status"], needs_owner)

    def test_an_unmapped_phase_falls_back_to_the_issue(self):
        """superseded has no honest ASHWOOD equivalent; forcing it into one
        would misreport it."""
        self.assertEqual(self._row("superseded")["status"], "active")
        self.assertEqual(self._row("superseded", issue_state="CLOSED")["status"], "done")

    def test_a_source_with_no_link_uses_the_issue(self):
        unlinked = dict(self.SOURCE)
        unlinked.pop("work_id")
        self.assertEqual(self._row(None, source=unlinked)["status"], "active")

    def test_the_row_records_which_basis_it_used(self):
        self.assertEqual(self._row("running")["metadata"]["status_basis"],
                         "agent-os execution phase")
        self.assertEqual(self._row(None)["metadata"]["status_basis"],
                         "github issue lifecycle")
        self.assertEqual(self._row("running")["metadata"]["execution_phase"], "running")

    def test_a_missing_fleet_database_is_not_an_error(self):
        """The projection must never be the reason the fleet database is opened
        for writing, and its absence just means no execution state to project."""
        self.assertIsNone(w._fleet_phase("anything"))
        self.assertIsNone(w._fleet_phase(""))
