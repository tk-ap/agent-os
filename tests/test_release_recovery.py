import tempfile
import unittest

from runtime import release_recovery as recovery


def sample(now=1_800_000_000):
    return {
        "recovery_id": "release-1",
        "work_id": "work-1",
        "product": "alvira-meos",
        "repository": "tk-ap/ALVIRA",
        "target_environment": "production",
        "action": {"kind": "deploy", "target": "production", "scope": "deploy commit abc"},
        "authority": {"reference": "grant-1", "status": "valid", "expires_at": recovery.iso(now + 3600)},
        "state": "ready",
        "retry_policy": {"max_mutation_attempts": 3, "max_elapsed_seconds": 86400},
        "availability_checks": 0,
        "mutation_attempts": 0,
        "created_at": recovery.iso(now - 60),
        "updated_at": recovery.iso(now - 60),
    }


class ReleaseRecoveryTests(unittest.TestCase):
    def test_wait_is_durable_and_due_later(self):
        now = 1_800_000_000
        record = recovery.wait_for_availability(sample(now), blocker_class="rate_limit",
                                                reason="provider cooldown", now=now,
                                                provider_retry_at=now + 600)
        self.assertEqual(record["state"], "waiting_availability")
        self.assertFalse(recovery.due(record, now + 599))
        self.assertTrue(recovery.due(record, now + 600))

    def test_expired_authority_never_resumes(self):
        now = 1_800_000_000
        record = sample(now)
        record["authority"]["expires_at"] = recovery.iso(now - 1)
        self.assertEqual(recovery.resume_eligibility(record, now=now),
                         (False, "authority:expired"))

    def test_ambiguous_result_requires_reconciliation(self):
        now = 1_800_000_000
        record = recovery.mark_reconciling(sample(now), {"provider_request": "dep-123"}, now=now)
        self.assertEqual(recovery.resume_eligibility(record, now=now),
                         (False, "reconciliation-required"))

    def test_retry_budget_is_mutation_budget(self):
        now = 1_800_000_000
        record = sample(now)
        record["mutation_attempts"] = 3
        self.assertEqual(recovery.resume_eligibility(record, now=now),
                         (False, "retry-budget-exhausted"))

    def test_live_verified_requires_evidence(self):
        with self.assertRaises(ValueError):
            recovery.mark_live_verified(sample(), [])
        done = recovery.mark_live_verified(sample(), [{"url": "https://example.com", "status": 200}])
        self.assertEqual(done["state"], "live_verified")
        self.assertTrue(recovery.is_terminal(done))

    def test_store_survives_process_boundary(self):
        with tempfile.TemporaryDirectory() as directory:
            store = recovery.RecoveryStore(directory)
            path = store.save(sample())
            self.assertTrue(path.exists())
            loaded = recovery.RecoveryStore(directory).load("release-1")
            self.assertEqual(loaded["work_id"], "work-1")


if __name__ == "__main__":
    unittest.main()
