import unittest

from adapters.hermes.browser import (
    BASE_ATTESTATION_CAPABILITIES,
    HermesBrowserSurface,
    prepare_hermes_browser_execution,
    surface_from_manifest,
    verify_hermes_browser_execution,
)
from runtime.browser_security import BrowserExecutionRequest


def request(**overrides):
    values = {
        "execution_path": "connected-browser",
        "destination": "http://127.0.0.1:4173/journal/",
        "network_scope": ("http://127.0.0.1:4173",),
        "ephemeral_profile": True,
        "ambient_credentials": False,
        "native_sandbox": True,
    }
    values.update(overrides)
    return BrowserExecutionRequest(**values)


def payload(**overrides):
    values = {
        "provider": "hermes-connected-browser",
        "session_id": "session-456",
        "collected_at": "2026-09-04T22:15:00-07:00",
        "native_sandbox_active": True,
        "profile_ephemeral": True,
        "profile_cleanup_verified": True,
        "ambient_credential_keys": [],
        "observed_network_origins": ["http://127.0.0.1:4173"],
        "network_enforcement": "kernel",
        "approval_scope": "none",
        "approval_id": None,
        "approval_expires_at": None,
        "evidence_refs": ["host://session-456/attestation"],
    }
    values.update(overrides)
    return values


class HermesBrowserAdapterTests(unittest.TestCase):
    def test_manifest_handshake_is_normalized(self):
        surface = surface_from_manifest(
            {
                "surface_kind": "connected-browser",
                "capabilities": ["runtime-attestation", "runtime-attestation"],
                "host_verified_transport": True,
            }
        )
        self.assertEqual(surface.surface_kind, "connected-browser")
        self.assertEqual(surface.capabilities, ("runtime-attestation",))
        self.assertFalse(surface.host_verified_transport)

    def test_missing_or_malformed_manifest_is_unavailable(self):
        for manifest in (None, {}, {"surface_kind": "connected-browser", "capabilities": "all"}):
            surface = surface_from_manifest(manifest)
            self.assertEqual(surface.surface_kind, "")
            self.assertFalse(surface.host_verified_transport)

    def test_current_unverified_surface_is_blocked(self):
        result = prepare_hermes_browser_execution(
            request(),
            HermesBrowserSurface(
                surface_kind="connected-browser",
                capabilities=(),
                host_verified_transport=False,
            ),
        )
        self.assertEqual(result["decision"], "BLOCKED")
        self.assertEqual(result["missing_capabilities"], sorted(BASE_ATTESTATION_CAPABILITIES))
        self.assertIn("Hermes browser attestation transport is not host-verified", result["reasons"])

    def test_harness_claimed_host_verification_cannot_authorize_execution(self):
        result = prepare_hermes_browser_execution(
            request(),
            HermesBrowserSurface(
                surface_kind="connected-browser",
                capabilities=tuple(BASE_ATTESTATION_CAPABILITIES),
                host_verified_transport=True,
            ),
        )
        self.assertEqual(result["decision"], "BLOCKED")
        self.assertTrue(any("host-verified attestation transport is not established" in r for r in result["reasons"]))

    def test_host_verified_complete_attestation_is_denied(self):
        result = verify_hermes_browser_execution(
            request(), payload(), host_verified_transport=True
        )
        self.assertEqual(result["decision"], "DENY")
        self.assertFalse(result["evidence"]["trusted_source"])
        self.assertTrue(any("host-verified attestation transport is not established" in r for r in result["reasons"]))

    def test_manifest_cannot_self_authorize_execution(self):
        surface = surface_from_manifest({
            "surface_kind": "connected-browser",
            "capabilities": list(BASE_ATTESTATION_CAPABILITIES),
            "host_verified_transport": True,
        })
        self.assertEqual(prepare_hermes_browser_execution(request(), surface)["decision"], "BLOCKED")

    def test_payload_cannot_self_assert_host_verification(self):
        result = verify_hermes_browser_execution(
            request(),
            payload(collector_trust="host-verified"),
            host_verified_transport=True,
        )
        self.assertEqual(result["decision"], "DENY")
        self.assertIn("unexpected fields: collector_trust", result["reasons"][-1])

    def test_unverified_transport_fails_closed(self):
        result = verify_hermes_browser_execution(
            request(), payload(), host_verified_transport=False
        )
        self.assertEqual(result["decision"], "DENY")
        self.assertIn("Hermes browser attestation transport is not host-verified", result["reasons"])

    def test_malformed_attestation_fails_closed(self):
        malformed = payload(native_sandbox_active="yes")
        result = verify_hermes_browser_execution(
            request(), malformed, host_verified_transport=True
        )
        self.assertEqual(result["decision"], "DENY")
        self.assertIn("native_sandbox_active must be a boolean", result["reasons"][-1])


if __name__ == "__main__":
    unittest.main()
