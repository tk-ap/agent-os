import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from runtime.product import ROUTING_FILE, _products, resolve_product


class ProductRoutingTests(unittest.TestCase):
    def test_ashwood_uses_canonical_repository_binding(self):
        products = _products(ROUTING_FILE.read_text())
        self.assertEqual(products["ashwood"]["repository"], "tk-ap/tk-ap.github.io")

    def test_unresolved_repository_is_not_guessed(self):
        routing = """products:
  agent-control:
    repository_status: unresolved
    plane: governance
    role: authorization intelligence
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "product-routing.yaml"
            path.write_text(routing)
            with patch("runtime.product.ROUTING_FILE", path):
                result = resolve_product("inspect agent control")

        self.assertEqual(result["status"], "UNRESOLVED")
        self.assertEqual(result["product_key"], "agent-control")
        self.assertIn("repository is unresolved", result["reason"])


if __name__ == "__main__":
    unittest.main()
