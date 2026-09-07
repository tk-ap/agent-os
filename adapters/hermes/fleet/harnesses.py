"""CLI arguments and error classification. No shell interpolation or permission bypass."""
import json
import os
import re
import shutil


SUPPORTED = ("codex-cli", "claude-code")


def command(harness, workspace):
    if harness == "codex-cli":
        return ["codex", "exec", "--json", "--sandbox", "workspace-write",
                "-c", 'approval_policy="never"',
                "-c", 'forced_login_method="chatgpt"',
                "-c", 'model_provider="openai"', "--cd", str(workspace), "-"]
    if harness == "claude-code":
        # File tools plus Bash, scoped to git/gh via --allowedTools. Anything
        # not allowlisted is auto-denied in --print + dontAsk mode (verified
        # live: git runs; arbitrary bash is recorded as a permission denial).
        # WebFetch/WebSearch are absent from --tools entirely.
        return ["claude", "--print", "--output-format", "json",
                "--permission-mode", "dontAsk", "--strict-mcp-config",
                "--mcp-config", '{"mcpServers":{}}',
                "--tools", "Read,Write,Edit,Glob,Grep,Bash",
                "--allowedTools", "Read,Write,Edit,Glob,Grep,Bash(git:*),Bash(gh:*)"]
    raise ValueError(f"Unsupported harness: {harness}")


def environment():
    env = dict(os.environ)
    # Use existing subscription login; never silently fall through to API billing.
    for key in list(env):
        if key.startswith(("OPENAI_", "ANTHROPIC_", "CLAUDE_CODE_USE_", "HERMES_KANBAN_")):
            env.pop(key)
    env.pop("CLAUDECODE", None)
    return env


def available(harness):
    return shutil.which(command(harness, ".")[0]) is not None


def classify(returncode, stdout, stderr):
    """Only provider error records/stderr can trigger rotation, never generated prose."""
    errors = []
    denied = False
    retry_after = None
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if not isinstance(event, dict):
            continue
        denied |= bool(event.get("permission_denials"))
        if event.get("type") in {"error", "turn.failed"} or event.get("is_error"):
            errors.append(json.dumps(event))
            delay = event.get("retry_after")
            if isinstance(delay, (int, float)) and not isinstance(delay, bool):
                retry_after = min(86400, max(60, delay))
    error = "\n".join(errors + ([stderr] if returncode else [])).lower()
    if denied or re.search(r"permission.denied|approval.required|not authorized|sandbox.*denied", error):
        return "permission", None
    if re.search(r"authentication|unauthorized|invalid.api.key|login required|not logged in", error):
        return "authentication", None
    if re.search(r"rate_limit|rate limit|usage.limit|quota.exceeded|quota exhausted|too many requests|insufficient_quota", error):
        return "capacity", retry_after
    if returncode or errors:
        return "failed", None
    return "executed", None
