from runtime.task import Task

TERMINAL_VERIFICATION_STATES = {"VERIFIED", "NOT VERIFIED", "BLOCKED"}


def _ineligible_identities(task: Task) -> set[str]:
    ctx = task.verification_context or {}
    return set(ctx.get("authors", [])) | set(ctx.get("remediators", [])) | set(ctx.get("material_participants", []))


def verify_independently(task: Task, verifier_identity: str | None = None):
    """Apply the Independent Verifier contract to provider-backed evidence.

    This function does not run the provider test itself. It evaluates evidence
    supplied by the verification runner and fails closed when the required live
    rerun has not happened. A verification workflow must never turn BLOCKED into
    VERIFIED by inference.
    """
    verifier_identity = verifier_identity or task.agent
    ctx = task.verification_context or {}

    if not verifier_identity:
        result = {"status": "BLOCKED", "reason": "No verifier identity was assigned."}
    elif verifier_identity in _ineligible_identities(task):
        result = {"status": "BLOCKED", "reason": "Assigned verifier is not independent of authorship/remediation.", "verifier": verifier_identity}
    elif ctx.get("live_required") and not ctx.get("fresh_live_rerun"):
        result = {"status": "BLOCKED", "reason": "Fresh live/provider-backed rerun is required but has not completed.", "verifier": verifier_identity}
    elif ctx.get("credential_required") and not ctx.get("fresh_credential_used"):
        result = {"status": "BLOCKED", "reason": "Fresh verification credential is required but unavailable or not used.", "verifier": verifier_identity}
    elif ctx.get("blocking_failure") or int(ctx.get("unauthorized_successes", 0)) > 0 or int(ctx.get("unresolved_bypasses", 0)) > 0:
        result = {
            "status": "NOT VERIFIED",
            "reason": "Verification found a blocking failure or unresolved bypass.",
            "verifier": verifier_identity,
            "unauthorized_successes": int(ctx.get("unauthorized_successes", 0)),
            "unresolved_bypasses": int(ctx.get("unresolved_bypasses", 0)),
        }
    elif not ctx.get("provider_readback"):
        result = {"status": "BLOCKED", "reason": "Independent provider readback is required.", "verifier": verifier_identity}
    elif not ctx.get("all_required_families_passed"):
        result = {"status": "BLOCKED", "reason": "The complete required verification suite has not passed.", "verifier": verifier_identity}
    else:
        result = {
            "status": "VERIFIED",
            "verifier": verifier_identity,
            "scope": ctx.get("scope"),
            "checks": ctx.get("checks", []),
            "limitations": ctx.get("limitations", []),
        }

    if result["status"] not in TERMINAL_VERIFICATION_STATES:
        raise RuntimeError("Independent Verifier returned an invalid terminal state")
    task.verification = result
    return result


def verify(task: Task):
    if task.task_class == "verification":
        return verify_independently(task)

    execution = task.execution
    if execution.get("status") != "EXECUTED":
        result = {"status": "FAILED", "reason": "Execution did not complete successfully.", "execution_status": execution.get("status")}
    elif execution.get("repository") and execution.get("entries") is not None:
        result = {"status": "VERIFIED", "checks": ["GitHub adapter executed", "repository identified", "repository evidence present"], "limitations": ["repository evidence does not prove deployment, runtime health, or resolution"]}
    else:
        result = {"status": "FAILED", "reason": "Execution produced insufficient evidence."}
    task.verification = result
    return result
