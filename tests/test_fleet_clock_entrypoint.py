import tempfile
import unittest
from pathlib import Path

from adapters.hermes.fleet import install as fleet_install


class FleetClockEntrypointTests(unittest.TestCase):
    def test_generated_fleet_clock_enters_continuity_tick(self):
        source = fleet_install._fleet_script_source()
        self.assertIn('"continuity-tick"', source)
        self.assertNotIn('"tick"])', source)

    def test_agent_os_managed_script_can_upgrade(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "clock.py"
            path.write_text("# Installed by Agent OS; old contract\n")
            replacement = "# Installed by Agent OS; new contract\n"
            fleet_install._install_script(path, replacement)
            self.assertEqual(path.read_text(), replacement)

    def test_unmanaged_existing_script_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "clock.py"
            path.write_text("print('operator owned')\n")
            with self.assertRaises(RuntimeError):
                fleet_install._install_script(
                    path, "# Installed by Agent OS; replacement\n"
                )
            self.assertEqual(path.read_text(), "print('operator owned')\n")


if __name__ == "__main__":
    unittest.main()
