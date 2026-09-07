import json
import socket
import ssl
from pathlib import Path
import subprocess
import tempfile
import time
import unittest
from unittest.mock import Mock, patch
import urllib.error

from adapters.hermes.fleet import bridge, telegram
from tests import test_hermes_fleet as fleet_tests

kb = fleet_tests.kb


class TelegramTransportTests(unittest.TestCase):
    def test_invalid_token_reports_401_without_token_or_url(self):
        token = "123:secret_fixture_value"
        error = urllib.error.HTTPError(f"https://api.telegram.org/bot{token}/getMe",401,"Unauthorized",{},None)
        with patch("urllib.request.urlopen",side_effect=error):
            with self.assertRaises(telegram.TelegramError) as caught:
                telegram.API(token).call("getMe")
        self.assertIn("rejected the bot token",str(caught.exception))
        self.assertNotIn(token,str(caught.exception))

    def test_dns_failure_is_distinct_from_invalid_token(self):
        with patch("urllib.request.urlopen",side_effect=urllib.error.URLError(socket.gaierror(-3,"lookup"))):
            with self.assertRaisesRegex(telegram.TelegramError,"DNS lookup failed"):
                telegram.API("123:fixture").call("getMe")

    def test_certificate_failure_does_not_disable_verification(self):
        error = urllib.error.URLError(ssl.SSLCertVerificationError(1,"certificate"))
        with patch("urllib.request.urlopen",side_effect=error):
            with self.assertRaisesRegex(telegram.TelegramError,"verification remains enabled"):
                telegram.API("123:fixture").call("getMe")


@unittest.skipIf(kb is None, "Requires installed Hermes environment")
class TelegramReviewTests(unittest.TestCase):
    setUp = fleet_tests.FleetTests.setUp
    tearDown = fleet_tests.FleetTests.tearDown
    enqueue = fleet_tests.FleetTests.enqueue
    claimed = fleet_tests.FleetTests.claimed

    def card(self):
        subprocess.run(["git","init","-q",str(self.workspace)],check=True)
        (self.workspace/"base.txt").write_text("original")
        subprocess.run(["git","-C",str(self.workspace),"add","base.txt"],check=True)
        subprocess.run(["git","-C",str(self.workspace),"-c","user.name=Fixture",
                        "-c","user.email=fixture@example.invalid","commit","-qm","baseline"],check=True)
        task = self.claimed()
        (self.workspace/"result.txt").write_text("reviewed result")
        conn = bridge.connect(self.state)
        conn.execute("UPDATE agent_os_orders SET phase='review',attempts=1 WHERE task_id=?",(task.id,))
        kb.request_review(conn,task.id,summary="Fixture ready",reviewer="agent-os-review",expected_run_id=task.current_run_id)
        telegram.schema(conn)
        # A card only reaches TK after an independent check. These tests exercise
        # the acceptance mechanics, so the check is seeded as already passed;
        # test_no_card_without_an_independent_check covers the gate itself.
        conn.execute("""INSERT OR REPLACE INTO agent_os_inspections
            (task_id,inspector_task_id,verdict,failed,cycles) VALUES (?,?,?,?,1)""",
            (task.id,"t_inspector_fixture","pass","Fixture inspection passed"))
        telegram.collect_reviews(conn,self.state)
        card = conn.execute("SELECT * FROM telegram_cards").fetchone()
        conn.execute("UPDATE telegram_cards SET delivery='sent',message_id=7 WHERE id=?",(card["id"],))
        config = {"user_id":123,"chat_id":123}
        query = {"id":"query-1","from":{"id":123},"message":{"chat":{"id":123},"message_id":7},
                 "data":f"aos:{card['id']}:accept"}
        return conn,task,config,query

    def test_acceptance_closes_exact_local_task_and_prevents_replay(self):
        conn,task,config,query = self.card()
        try:
            self.assertIn("accepted",telegram.decide(conn,config,query).lower())
            self.assertEqual(kb.get_task(conn,task.id).status,"done")
            self.assertIn("already handled",telegram.decide(conn,config,query))
            self.assertEqual(bridge.order_row(conn,task.id)["phase"],"accepted")
        finally:
            conn.close()

    def test_wrong_actor_and_chat_cannot_approve(self):
        conn,task,config,query = self.card()
        try:
            query["from"]["id"] = 999
            self.assertEqual(telegram.decide(conn,config,query),"Not authorized")
            query["from"]["id"] = 123
            query["message"]["chat"]["id"] = 999
            self.assertEqual(telegram.decide(conn,config,query),"Not authorized")
            self.assertEqual(kb.get_task(conn,task.id).status,"review")
        finally:
            conn.close()

    def test_changed_files_reject_stale_card(self):
        conn,task,config,query = self.card()
        try:
            (self.workspace/"result.txt").write_text("different result")
            self.assertIn("Files changed",telegram.decide(conn,config,query))
            self.assertEqual(kb.get_task(conn,task.id).status,"review")
        finally:
            conn.close()

    def test_expired_revoked_and_wrong_message_denied(self):
        conn,task,config,query = self.card()
        try:
            query["message"]["message_id"] = 9
            self.assertIn("unavailable",telegram.decide(conn,config,query))
            query["message"]["message_id"] = 7
            conn.execute("UPDATE telegram_cards SET expires=0")
            self.assertIn("expired",telegram.decide(conn,config,query))
            conn.execute("UPDATE telegram_cards SET expires=?",(time.time()+60,))
            conn.execute("UPDATE agent_os_orders SET revoked=1")
            self.assertIn("revoked",telegram.decide(conn,config,query))
            self.assertEqual(kb.get_task(conn,task.id).status,"review")
        finally:
            conn.close()

    def test_feedback_pauses_and_records_distinct_reason(self):
        conn,task,config,query = self.card()
        try:
            query["data"] = query["data"].replace(":accept",":redo")
            result = telegram.decide(conn,config,query)
            self.assertIn("Rethink the approach",result)
            self.assertEqual(bridge.order_row(conn,task.id)["revoked"],1)
            self.assertEqual(bridge.order_row(conn,task.id)["phase"],"redo")
            self.assertNotEqual(kb.get_task(conn,task.id).status,"running")
            card = conn.execute("SELECT feedback FROM telegram_cards").fetchone()
            self.assertIn("Rethink",card["feedback"])
        finally:
            conn.close()

    def test_no_card_without_an_independent_check(self):
        """Work must not reach TK having been seen only by the agent that did it."""
        task = self.claimed()
        conn = bridge.connect(self.state)
        try:
            conn.execute("UPDATE agent_os_orders SET phase='review',attempts=1 WHERE task_id=?",(task.id,))
            kb.request_review(conn,task.id,summary="Fixture ready",reviewer="agent-os-review",
                              expected_run_id=task.current_run_id)
            telegram.schema(conn)
            telegram.collect_reviews(conn,self.state)
            self.assertIsNone(conn.execute("SELECT 1 FROM telegram_cards WHERE channel='private'").fetchone())
            conn.execute("""INSERT INTO agent_os_inspections
                (task_id,inspector_task_id,verdict,failed,cycles) VALUES (?,?,?,?,1)""",
                (task.id,"t_inspector","pass","checked"))
            telegram.collect_reviews(conn,self.state)
            self.assertIsNotNone(conn.execute("SELECT 1 FROM telegram_cards WHERE channel='private'").fetchone())
        finally:
            conn.close()

    def test_inspection_is_not_itself_inspected(self):
        """An inspection reaching review must not spawn another inspection."""
        task = self.claimed()
        conn = bridge.connect(self.state)
        try:
            telegram.schema(conn)
            conn.execute("UPDATE agent_os_orders SET phase='review',work_id=? WHERE task_id=?",
                         ("something" + telegram.INSPECTION_SUFFIX, task.id))
            telegram.request_inspection(conn,self.state)
            self.assertIsNone(conn.execute("SELECT 1 FROM agent_os_inspections").fetchone())
        finally:
            conn.close()

    def test_verdict_does_not_carry_to_changed_files(self):
        """A pass is about the files inspected, not the ones TK ends up seeing."""
        conn,task,config,query = self.card()
        try:
            conn.execute("UPDATE agent_os_inspections SET snapshot='inspected-something-else' WHERE task_id=?",
                         (task.id,))
            conn.execute("DELETE FROM telegram_cards")
            telegram.collect_reviews(conn,self.state)
            card = conn.execute("SELECT message FROM telegram_cards WHERE channel='private'").fetchone()
            self.assertIn("NO LONGER APPLIES", card["message"])
            self.assertNotIn("found no problems", card["message"])
        finally:
            conn.close()

    def test_tick_yields_polling_to_a_live_listener(self):
        """Two pollers would steal each other's updates; only one may hold getUpdates."""
        conn = bridge.connect(self.state)
        try:
            telegram.schema(conn)
            self.assertFalse(telegram.listener_is_live(conn))
            conn.execute("INSERT OR REPLACE INTO telegram_meta VALUES ('listener_heartbeat',?)",
                         (str(time.time()),))
            self.assertTrue(telegram.listener_is_live(conn))
            # A listener that stopped checking in must hand polling back.
            conn.execute("INSERT OR REPLACE INTO telegram_meta VALUES ('listener_heartbeat',?)",
                         (str(time.time() - telegram.LISTENER_STALE_AFTER - 1),))
            self.assertFalse(telegram.listener_is_live(conn))
            conn.execute("INSERT OR REPLACE INTO telegram_meta VALUES ('listener_heartbeat','nonsense')")
            self.assertFalse(telegram.listener_is_live(conn))
        finally:
            conn.close()

    def test_publishing_is_a_separate_press_from_saving(self):
        """A card that can publish still offers the smaller choice, and honours it."""
        deploy = {"workspace": "/tmp", "work_id": "w",
                  "publish_action": {"kind": "deploy", "paths": ["a"], "branch": "main",
                                     "deploys_to": "https://example.invalid"}}
        names = [n for n, _label, _d in telegram.publish_choices(deploy)]
        self.assertEqual(names, ["commit", "deploy"])
        # Pressing save on a deploy-capable card must not publish.
        self.assertIsNone(telegram.perform_publish({"publish_action": {"kind": "deploy"}},
                                                   None, chosen="accept"))
        commit_only = {"workspace": "/tmp", "work_id": "w",
                       "publish_action": {"kind": "commit", "paths": ["a"]}}
        self.assertEqual([n for n, _l, _d in telegram.publish_choices(commit_only)], ["commit"])
        self.assertEqual([n for n, _l, _d in telegram.publish_choices({"workspace": "/tmp"})], ["accept"])

    def test_feedback_choices_are_distinct_and_structured(self):
        """Feedback is a set of distinct selectable buttons, not one vague rejection."""
        names = [n for n, _label, _reason in telegram.FEEDBACK_CHOICES]
        self.assertEqual(len(names), len(set(names)))  # distinct actions
        self.assertIn("offvoice", names)
        self.assertIn("wrongclaim", names)
        self.assertEqual(telegram.feedback_action("redo"),
                         "Rethink the approach. The current one does not answer what was asked.")
        self.assertIsNone(telegram.feedback_action("pause"))

    def test_feedback_never_routes_to_publish(self):
        """A feedback press must not be mistaken for an approval."""
        self.assertIsNone(telegram.feedback_action("accept"))
        self.assertIsNone(telegram.feedback_action("commit"))
        self.assertIsNone(telegram.feedback_action("deploy"))

    def test_batch_publish_refuses_if_the_branch_moved(self):
        """The branch shown on the card must be the branch that gets pushed."""
        entry = {"label": "X", "path": str(self.workspace), "branch": "a-branch-that-is-not-checked-out",
                 "commits": 3}
        subprocess.run(["git", "init", "-q", str(self.workspace)], check=True)
        with self.assertRaises(ValueError) as caught:
            telegram.publish_branch(entry)
        self.assertIn("branch changed", str(caught.exception))
        self.assertIn("nothing published", str(caught.exception))

    def test_review_deduplication(self):
        conn,task,config,query = self.card()
        try:
            telegram.collect_reviews(conn,self.state)
            self.assertEqual(conn.execute("SELECT count(*) FROM telegram_cards").fetchone()[0],1)
        finally:
            conn.close()

    def test_ambiguous_delivery_is_not_retried(self):
        conn,task,config,query = self.card()
        try:
            conn.execute("UPDATE telegram_cards SET delivery='pending',message_id=NULL")
            api = Mock()
            api.call.side_effect = telegram.TelegramError("uncertain")
            with self.assertRaises(telegram.TelegramError):
                telegram.deliver(conn,config,api)
            telegram.deliver(conn,config,api)
            self.assertEqual(api.call.call_count,1)
            self.assertEqual(conn.execute("SELECT delivery FROM telegram_cards").fetchone()[0],"uncertain")
        finally:
            conn.close()

    def test_batch_threshold_per_product_and_no_commit_deployment_conflation(self):
        conn = bridge.connect(self.state)
        telegram.schema(conn)
        try:
            for n in range(5):
                telegram.record_change(conn,"ashwood","commit",str(n),"local commit")
            telegram.record_change(conn,"alvira-meos","deployment","one","producer receipt")
            telegram.collect_batches(conn,5,"deployment")
            self.assertEqual(conn.execute("SELECT count(*) FROM telegram_cards").fetchone()[0],0)
            telegram.collect_batches(conn,5,"commit")
            self.assertEqual(conn.execute("SELECT count(*) FROM telegram_cards").fetchone()[0],1)
            telegram.collect_batches(conn,5,"commit")
            self.assertEqual(conn.execute("SELECT count(*) FROM telegram_cards").fetchone()[0],1)
        finally:
            conn.close()

    def test_no_config_means_no_network(self):
        api = Mock()
        result = telegram.tick(self.state,self.root/"missing.json",api)
        self.assertEqual(result["status"],"not_configured")
        api.call.assert_not_called()


if __name__ == "__main__":
    unittest.main()
