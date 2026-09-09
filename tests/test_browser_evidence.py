import unittest

from runtime.browser_evidence import (
    BrowserRouteCheck,
    BrowserVerificationRecord,
    attach_browser_evidence,
)
from runtime.task import Task
from runtime.verifier import verify


def record(**overrides):
    values = {
        "provider": "codex-connected-browser",
        "base_url": "https://ashwood-info.vercel.app/",
        "routes": (
            BrowserRouteCheck(
                route="/",
                url="https://ashwood-info.vercel.app/",
                title="ASHWOOD — TK Ashwood",
                body_length=2497,
            ),
        ),
        "interactions": ("home reveal interaction",),
        "security_state": "transport-verified",
        "evidence_ref": "docs/security/evidence/ashwood-route-smoke-2026-09-05.json",
    }
    values.update(overrides)
    return BrowserVerificationRecord(**values)


class BrowserEvidenceTests(unittest.TestCase):
    def test_transport_verified_browser_result_is_first_class_task_evidence(self):
        task = Task("verify ASHWOOD")
        verification = attach_browser_evidence(task, record())
        self.assertEqual(task.execution["adapter"], "codex-browser")
        self.assertEqual(verification["status"], "PREVIEWED")
        self.assertEqual(task.execution["browser_verification"]["provider"], "codex-connected-browser")
        self.assertTrue(verification["limitations"])

    def test_caller_runtime_label_cannot_promote_browser_result(self):
        task = Task("verify ASHWOOD")
        verification = attach_browser_evidence(task, record(security_state="runtime-verified"))
        self.assertEqual(verification["status"], "PREVIEWED")
        self.assertTrue(verification["limitations"])
        self.assertEqual(verify(task)["status"], "PREVIEWED")

    def test_generic_verifier_preserves_previewed_browser_state(self):
        task = Task("verify ASHWOOD")
        attach_browser_evidence(task, record())
        result = verify(task)
        self.assertEqual(result["status"], "PREVIEWED")

    def test_blank_route_is_rejected(self):
        task = Task("verify ASHWOOD")
        bad = record(routes=(BrowserRouteCheck("/", "https://ashwood-info.vercel.app/", "", 0),))
        with self.assertRaisesRegex(ValueError, "blank"):
            attach_browser_evidence(task, bad)

    def test_cross_origin_route_is_rejected(self):
        task = Task("verify ASHWOOD")
        bad = record(routes=(BrowserRouteCheck("/offsite", "https://example.com/", "Example", 20),))
        with self.assertRaisesRegex(ValueError, "escaped"):
            attach_browser_evidence(task, bad)


if __name__ == "__main__":
    unittest.main()
