import unittest

from runtime.authorization import authorize
from runtime.router import route_task
from runtime.server import _prepare, _status
from runtime.task import Task, normalize
from runtime.verifier import verify_independently


class IndependentVerifierTests(unittest.TestCase):
    def test_normalize_detects_independent_verification(self):
        task = normalize("Run an independent verification live rerun for LEDGATo")
        self.assertEqual(task.task_class, "verification")

    def test_router_excludes_authors_and_remediators(self):
        task = Task(
            request="independent verify",
            task_class="verification",
            verification_context={
                "authors": ["w-dog"],
                "remediators": [],
                "candidate_verifiers": ["w-dog", "rook"],
            },
        )
        routed = route_task(task)
        self.assertEqual(routed["agent"], "rook")
        self.assertEqual(routed["role"], "Independent Verifier")
        self.assertEqual(routed["mode"], "INDEPENDENT VERIFICATION")

    def test_verifier_cannot_self_attest(self):
        task = Task(
            request="independent verify",
            task_class="verification",
            agent="rook",
            verification_context={"authors": ["rook"]},
        )
        result = verify_independently(task)
        self.assertEqual(result["status"], "BLOCKED")

    def test_missing_fresh_live_rerun_is_blocked(self):
        task = Task(
            request="independent verify",
            task_class="verification",
            agent="w-dog",
            verification_context={
                "live_required": True,
                "fresh_live_rerun": False,
                "credential_required": True,
                "fresh_credential_used": False,
            },
        )
        result = verify_independently(task)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("live", result["reason"].lower())

    def test_unresolved_bypass_is_not_verified(self):
        task = Task(
            request="independent verify",
            task_class="verification",
            agent="w-dog",
            verification_context={
                "fresh_live_rerun": True,
                "fresh_credential_used": True,
                "unresolved_bypasses": 1,
                "provider_readback": True,
                "all_required_families_passed": True,
            },
        )
        result = verify_independently(task)
        self.assertEqual(result["status"], "NOT VERIFIED")

    def test_complete_live_evidence_can_verify(self):
        task = Task(
            request="independent verify",
            task_class="verification",
            agent="w-dog",
            verification_context={
                "live_required": True,
                "fresh_live_rerun": True,
                "credential_required": True,
                "fresh_credential_used": True,
                "unauthorized_successes": 0,
                "unresolved_bypasses": 0,
                "provider_readback": True,
                "all_required_families_passed": True,
                "scope": "github_lab_merge",
            },
        )
        result = verify_independently(task)
        self.assertEqual(result["status"], "VERIFIED")
        self.assertEqual(result["scope"], "github_lab_merge")

    def test_verification_authorization_is_audited_not_release_authority(self):
        task = Task(request="attest the live result", task_class="verification")
        result = authorize(task)
        self.assertEqual(result["status"], "AUTHORIZED")
        self.assertEqual(result["decision_class"], "AUTONOMOUS_AUDIT")

    def test_task_api_records_ledgato_as_blocked_without_fresh_credential(self):
        payload = _prepare(
            "independent verification live rerun for LEDGATo github_lab_merge",
            product="ledgato",
            verification_context={
                "authors": ["claude"],
                "remediators": ["claude"],
                "candidate_verifiers": ["w-dog", "rook"],
                "live_required": True,
                "fresh_live_rerun": False,
                "credential_required": True,
                "fresh_credential_used": False,
                "scope": "github_lab_merge",
            },
        )
        self.assertEqual(payload["routing"]["role"], "Independent Verifier")
        self.assertEqual(payload["verification"]["status"], "BLOCKED")
        self.assertEqual(_status(payload), "BLOCKED")


if __name__ == "__main__":
    unittest.main()
