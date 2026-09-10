import json
import unittest
from pathlib import Path

from runtime.browser_security import (
    BrowserExecutionRequest,
    BrowserRuntimeAttestation,
    evaluate_browser_execution,
    verify_browser_execution,
)


def request(**overrides):
    values = {
        "execution_path": "connected-browser",
        "destination": "http://127.0.0.1:4173/journal/#latest",
        "network_scope": ("http://127.0.0.1:4173",),
        "ephemeral_profile": True,
        "ambient_credentials": False,
        "native_sandbox": True,
        "outside_default_sandbox": False,
        "approval_scope": "none",
        "arguments": ("--headless",),
    }
    values.update(overrides)
    return BrowserExecutionRequest(**values)


def attestation(**overrides):
    values = {
        "provider": "codex-connected-browser",
        "session_id": "browser-session-123",
        "collected_at": "2026-09-04T22:15:00-07:00",
        "collector_trust": "provider-attested",
        "native_sandbox_active": True,
        "profile_ephemeral": True,
        "profile_cleanup_verified": True,
        "ambient_credential_keys": (),
        "observed_network_origins": ("http://127.0.0.1:4173",),
        "network_enforcement": "kernel",
        "approval_scope": "none",
        "approval_id": None,
        "approval_expires_at": None,
        "evidence_refs": ("provider://browser-session-123/runtime-attestation",),
    }
    values.update(overrides)
    return BrowserRuntimeAttestation(**values)


class BrowserSecurityAcceptanceTests(unittest.TestCase):
    def assert_denied(self, expected_reason, **overrides):
        result = evaluate_browser_execution(request(**overrides))
        self.assertEqual(result["decision"], "DENY")
        self.assertIn(expected_reason, result["reasons"])
        return result

    def test_declared_controlled_secretless_destination_scoped_browser_is_ready(self):
        result = evaluate_browser_execution(request())
        self.assertEqual(result["decision"], "READY")
        self.assertEqual(result["evidence"]["destination_origin"], "http://127.0.0.1:4173")
        self.assertTrue(result["evidence"]["native_sandbox"])

    def test_no_sandbox_is_always_denied(self):
        self.assert_denied(
            "Chromium native sandbox must remain enabled",
            native_sandbox=False,
            arguments=("--headless", "--no-sandbox"),
        )

    def test_sandbox_weakening_argument_variant_is_denied(self):
        result = self.assert_denied(
            "Chromium native sandbox must remain enabled",
            arguments=("--headless", "--disable-seccomp-filter-sandbox=true"),
        )
        self.assertEqual(
            result["evidence"]["sandbox_weakening_arguments"],
            ["--disable-seccomp-filter-sandbox=true"],
        )

    def test_direct_restricted_shell_execution_fails_closed(self):
        self.assert_denied(
            "direct shell browser execution is incompatible with the restricted sandbox",
            execution_path="shell",
        )

    def test_outside_execution_requires_one_time_approval(self):
        self.assert_denied(
            "execution outside the default sandbox requires one-time approval",
            execution_path="shell",
            outside_default_sandbox=True,
        )

    def test_persistent_approval_is_denied(self):
        self.assert_denied(
            "persistent browser execution approvals are prohibited",
            execution_path="shell",
            outside_default_sandbox=True,
            approval_scope="persistent",
        )

    def test_destination_outside_network_scope_is_denied(self):
        self.assert_denied(
            "destination origin is outside the declared network scope",
            destination="https://example.com/",
        )

    def test_destination_with_embedded_credentials_is_denied(self):
        self.assert_denied(
            "destination must be an explicit HTTP(S) URL",
            destination="http://token@127.0.0.1:4173/journal/",
        )

    def test_malformed_network_scope_is_denied(self):
        self.assert_denied(
            "network scope contains an invalid origin",
            network_scope=("http://127.0.0.1:4173", "not-an-origin"),
        )

    def test_ambient_credentials_are_denied(self):
        self.assert_denied(
            "ambient credentials would be exposed to the browser",
            ambient_credentials=True,
        )

    def test_persistent_profile_is_denied(self):
        self.assert_denied(
            "browser profile is not ephemeral",
            ephemeral_profile=False,
        )

    def test_decision_contains_non_secret_audit_evidence(self):
        result = evaluate_browser_execution(request())
        self.assertEqual(result["policy_version"], "browser-execution/v2")
        self.assertEqual(result["evidence"]["allowed_origins"], ["http://127.0.0.1:4173"])
        self.assertEqual(result["evidence"]["approval_scope"], "none")

    def test_trusted_complete_runtime_attestation_is_verified(self):
        result = verify_browser_execution(request(), attestation())
        self.assertEqual(result["decision"], "VERIFIED")
        self.assertEqual(result["reasons"], [])

    def test_missing_runtime_attestation_fails_closed(self):
        result = verify_browser_execution(request(), None)
        self.assertEqual(result["decision"], "DENY")
        self.assertIn("trusted runtime attestation is required", result["reasons"])

    def test_self_reported_runtime_attestation_is_denied(self):
        result = verify_browser_execution(
            request(), attestation(collector_trust="self-reported")
        )
        self.assertEqual(result["decision"], "DENY")
        self.assertIn(
            "runtime evidence is not from a trusted attestation source", result["reasons"]
        )

    def test_provider_policy_alone_is_not_accepted_as_egress_enforcement(self):
        result = verify_browser_execution(
            request(), attestation(network_enforcement="provider-policy")
        )
        self.assertEqual(result["decision"], "DENY")
        self.assertIn(
            "network scope lacks kernel or destination-locked proxy enforcement",
            result["reasons"],
        )

    def test_observed_origin_outside_scope_is_denied(self):
        result = verify_browser_execution(
            request(),
            attestation(observed_network_origins=("https://example.com",)),
        )
        self.assertEqual(result["decision"], "DENY")
        self.assertIn(
            "observed network origin is outside the declared network scope",
            result["reasons"],
        )

    def test_incomplete_runtime_controls_are_denied(self):
        result = verify_browser_execution(
            request(),
            attestation(
                native_sandbox_active=False,
                profile_cleanup_verified=False,
                ambient_credential_keys=("GITHUB_TOKEN",),
                evidence_refs=(),
            ),
        )
        self.assertEqual(result["decision"], "DENY")
        self.assertIn(
            "runtime did not attest an active Chromium native sandbox", result["reasons"]
        )
        self.assertIn("runtime profile cleanup was not verified", result["reasons"])
        self.assertIn("runtime exposed ambient credential keys", result["reasons"])
        self.assertIn("runtime attestation has no evidence references", result["reasons"])

    def test_one_time_execution_requires_attested_approval_identity_and_expiration(self):
        outside_request = request(
            execution_path="shell",
            outside_default_sandbox=True,
            approval_scope="one-time",
        )
        result = verify_browser_execution(
            outside_request, attestation(approval_scope="one-time")
        )
        self.assertEqual(result["decision"], "DENY")
        self.assertIn(
            "one-time approval identity or expiration is missing", result["reasons"]
        )

    def test_expired_one_time_approval_is_denied(self):
        outside_request = request(
            execution_path="shell",
            outside_default_sandbox=True,
            approval_scope="one-time",
        )
        result = verify_browser_execution(
            outside_request,
            attestation(
                approval_scope="one-time",
                approval_id="approval-123",
                approval_expires_at="2026-09-04T22:14:59-07:00",
            ),
        )
        self.assertEqual(result["decision"], "DENY")
        self.assertIn(
            "one-time approval expiration is invalid or expired", result["reasons"]
        )

    def test_unapproved_request_rejects_approval_metadata(self):
        result = verify_browser_execution(
            request(),
            attestation(
                approval_id="unexpected",
                approval_expires_at="2026-09-04T23:00:00-07:00",
            ),
        )
        self.assertEqual(result["decision"], "DENY")
        self.assertIn(
            "runtime supplied approval metadata for an unapproved request",
            result["reasons"],
        )

    def test_evidence_fixture_keeps_production_enforcement_denied(self):
        evidence_path = (
            Path(__file__).resolve().parents[1]
            / "docs"
            / "security"
            / "evidence"
            / "browser-execution-2026-09-04.json"
        )
        evidence = json.loads(evidence_path.read_text())
        gates = {item["gate"]: item["state"] for item in evidence["spec"]["gates"]}
        self.assertEqual(evidence["spec"]["state"], "implemented")
        self.assertEqual(gates["Production enforcement claim"], "denied")


if __name__ == "__main__":
    unittest.main()
