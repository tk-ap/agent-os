"""Milchik backlog: attention ranking and origin weighting."""
import unittest
import yaml

from runtime import backlog


def load():
    items = yaml.safe_load((__import__("pathlib").Path(__file__).resolve().parents[1] / "agents/milchik/backlog.yaml").read_text())
    return items


class ScoreTests(unittest.TestCase):
    def test_priority_dominates_origin(self):
        human_p1 = {"work_id": "h1", "source": "human", "priority": {"level": "p1"}}
        agent_p0 = {"work_id": "a0", "source": "agent", "priority": {"level": "p0"}}
        # p0 agent (60+15) ties p1 human (45+30) at default confidence, and
        # cleanly outranks p2 human. Priority never loses to origin.
        self.assertGreaterEqual(backlog.attention_score(agent_p0), backlog.attention_score(human_p1))
        human_p2 = {"work_id": "h2", "source": "human", "priority": {"level": "p2"}}
        self.assertGreater(backlog.attention_score(agent_p0), backlog.attention_score(human_p2))

    def test_human_default_confidence_outweighs_agent_default_at_same_priority(self):
        human = {"work_id": "h", "source": "human", "priority": {"level": "p2"}}
        agent = {"work_id": "a", "source": "agent", "priority": {"level": "p2"}}
        self.assertGreater(backlog.attention_score(human), backlog.attention_score(agent))

    def test_explicit_confidence_overrides_default(self):
        agent_confident = {"work_id": "a", "source": "agent", "priority": {"level": "p2", "confidence": 1.0}}
        human_uncertain = {"work_id": "h", "source": "human", "priority": {"level": "p2", "confidence": 0.1}}
        self.assertGreater(backlog.attention_score(agent_confident), backlog.attention_score(human_uncertain))

    def test_authority_present_only_for_human(self):
        self.assertTrue(backlog.authority_present({"source": "human"}))
        self.assertFalse(backlog.authority_present({"source": "agent"}))
        self.assertFalse(backlog.authority_present({"source": "routine"}))

    def test_rank_is_stable_and_descending(self):
        items = load()
        ranked = backlog.rank(items)
        scores = [backlog.attention_score(i) for i in ranked]
        self.assertEqual(scores, sorted(scores, reverse=True))
        # Human in-flight item is p0 and must surface first.
        self.assertEqual(ranked[0]["work_id"], "milchik-two-chat-runtime")

    def test_ecosystem_lane_gates_directives_softly(self):
        eco_p1 = {"work_id": "e", "source": "human", "priority": {"level": "p1"}, "lane": "ecosystem"}
        eco_p2 = {"work_id": "e2", "source": "agent", "priority": {"level": "p2"}, "lane": "ecosystem"}
        directive_p0 = {"work_id": "d", "source": "ailhat",
                        "priority": {"level": "p0", "confidence": 1.0}, "lane": "directive"}
        # Ecosystem work drains first...
        self.assertGreater(backlog.attention_score(eco_p1), backlog.attention_score(directive_p0))
        # ...but a p0 directive is not starved behind low-priority cleanup.
        self.assertGreater(backlog.attention_score(directive_p0), backlog.attention_score(eco_p2))

    def test_lane_defaults_to_ecosystem_and_rejects_unknown(self):
        self.assertEqual(backlog.lane({}), "ecosystem")
        self.assertEqual(backlog.lane({"lane": "nonsense"}), "ecosystem")

    def test_ailhat_is_intelligence_not_authority(self):
        self.assertFalse(backlog.authority_present({"source": "ailhat"}))

    def test_next_for_attention_respects_k(self):
        items = load()
        self.assertEqual(len(backlog.next_for_attention(items, k=2)), 2)


if __name__ == "__main__":
    unittest.main()
