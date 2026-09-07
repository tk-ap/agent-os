import unittest

from adapters.hermes.fleet import auto_update


class AutoUpdateTests(unittest.TestCase):
    def test_runtime_change_detection(self):
        self.assertTrue(auto_update.affects_milchik(["adapters/hermes/fleet/telegram_agent_directory.py"]))
        self.assertTrue(auto_update.affects_milchik(["registry/agents.yaml"]))
        self.assertTrue(auto_update.affects_milchik(["adapters/hermes/fleet/__init__.py"]))
        self.assertFalse(auto_update.affects_milchik(["docs/AGENT_DIRECTORY.md"]))

    def test_runtime_prefixes_are_narrow(self):
        self.assertFalse(auto_update.affects_milchik(["adapters/hermes/WORKSPACE_CONTRACT.yaml"]))
        self.assertFalse(auto_update.affects_milchik(["README.md"]))


if __name__ == "__main__":
    unittest.main()
