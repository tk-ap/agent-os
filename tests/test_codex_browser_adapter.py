import unittest

from adapters.codex.browser import (
    BASE_ATTESTATION_CAPABILITIES,
    CodexBrowserSurface,
    prepare_codex_browser_execution,
    surface_from_manifest,
    verify_codex_browser_execution,
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
        "provider": "codex-connected-browser",
        "session_id": "session-123",
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
        "evidence_refs": ["provider://session-123/attestation"],
    }
    values.update(overrides)
    return values


class CodexBrowserAdapterTests(unittest.TestCase):
    def test_manifest_handshake_is_normalized(self):
        surface = surface_from_manifest(
            {
                "provider_id": "codex-cua",
                "capabilities": ["runtime-attestation", "runtime-attestation"],
                "authenticated_attestation_transport": True,
            }
        )
        self.assertEqual(surface.provider_id, "codex-cua")
        self.assertEqual(surface.capabilities, ("runtime-attestation",))
        self.assertFalse(surface.authenticated_attestation_transport)

    def test_missing_or_malformed_manifest_is_unavailable(self):
        for manifest in (None, {}, {"provider_id": "codex-cua", "capabilities": "all"}):
            surface = surface_from_manifest(manifest)
            self.assertEqual(surface.provider_id, "")
            self.assertFalse(surface.authenticated_attestation_transport)

    def test_current_unattested_surface_is_blocked(self):
        result = prepare_codex_browser_execution(
            request(),
            CodexBrowserSurface(
                provider_id="codex-cua",
                capabilities=(),
                authenticated_attestation_transport=False,
            ),
        )
        self.assertEqual(result["decision"], "BLOCKED")
        self.assertEqual(result["missing_capabilities"], sorted(BASE_ATTESTATION_CAPABILITIES))
        self.assertIn("Codex browser attestation transport is not authenticated", result["reasons"])

    def test_caller_authenticated_surface_cannot_authorize_execution(self):
        result = prepare_codex_browser_execution(
            request(),
            CodexBrowserSurface(
                provider_id="codex-cua",
                capabilities=tuple(BASE_ATTESTATION_CAPABILITIES),
                authenticated_attestation_transport=True,
            ),
        )
        self.assertEqual(result["decision"], "BLOCKED")
        self.assertTrue(any("authentication is not implemented" in reason for reason in result["reasons"]))

    def test_caller_authenticated_complete_attestation_is_denied(self):
        result = verify_codex_browser_execution(
            request(), payload(), authenticated_transport=True
        )
        self.assertEqual(result["decision"], "DENY")
        self.assertFalse(result["evidence"]["trusted_source"])
        self.assertTrue(any("authentication is not implemented" in reason for reason in result["reasons"]))

    def test_manifest_cannot_self_authorize_execution(self):
        surface = surface_from_manifest({
            "provider_id": "codex-cua",
            "capabilities": list(BASE_ATTESTATION_CAPABILITIES),
            "authenticated_attestation_transport": True,
        })
        self.assertEqual(prepare_codex_browser_execution(request(), surface)["decision"], "BLOCKED")

    def test_payload_cannot_self_assert_transport_trust(self):
        result = verify_codex_browser_execution(
            request(),
            payload(collector_trust="provider-attested"),
            authenticated_transport=True,
        )
        self.assertEqual(result["decision"], "DENY")
        self.assertIn("unexpected fields: collector_trust", result["reasons"][-1])

    def test_unauthenticated_transport_fails_closed(self):
        result = verify_codex_browser_execution(
            request(), payload(), authenticated_transport=False
        )
        self.assertEqual(result["decision"], "DENY")
        self.assertIn("Codex browser attestation transport is not authenticated", result["reasons"])

    def test_malformed_attestation_fails_closed(self):
        malformed = payload(native_sandbox_active="yes")
        result = verify_codex_browser_execution(
            request(), malformed, authenticated_transport=True
        )
        self.assertEqual(result["decision"], "DENY")
        self.assertIn("native_sandbox_active must be a boolean", result["reasons"][-1])


if __name__ == "__main__":
    unittest.main()
