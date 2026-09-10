"""CLI arguments and error classification. No shell interpolation or permission bypass."""
import json
import os
import re
import shutil


SUPPORTED = ("codex-cli", "claude-code", "gemini-cli", "codex-cli-network")


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
    if harness == "codex-cli-network":
        # Identical to codex-cli except that the workspace sandbox permits
        # network egress. It exists as its own registry entry, rather than as a
        # flag flipped on the ordinary harness when a grant arrives, so that
        # gaining network is a routing decision visible at enqueue time and
        # recorded in the evidence trail -- not a side effect of an approval.
        #
        # The trade this makes is real and worth stating: the sandbox grants
        # general egress, while the scoped grant that motivates it names
        # specific destinations. Restricting egress to those destinations is a
        # provider capability the sandbox does not offer, so the narrowing that
        # remains is that only work which declared the network capability is
        # ever routed here at all.
        return ["codex", "exec", "--json", "--sandbox", "workspace-write",
                "-c", 'approval_policy="never"',
                "-c", "sandbox_workspace_write.network_access=true",
                "-c", 'forced_login_method="chatgpt"',
                "-c", 'model_provider="openai"', "--cd", str(workspace), "-"]
    if harness == "gemini-cli":
        # approval_mode auto_edit auto-approves edit tools and nothing else, so
        # a shell call still needs a confirmation that headless mode cannot give.
        # That is the per-invocation capability boundary; the registry declares
        # gemini filesystem-only so routing never hands it git or shell work in
        # the first place. Two independent limits, matching the other harnesses.
        #
        # --sandbox is deliberately not passed. Docker is present, but running
        # the agent in a container changes how the workspace and the progress
        # checkpoint are mounted, and that could not be exercised end to end
        # here (no Gemini auth is configured). Revisit once a live run exists.
        #
        # The prompt arrives on stdin like the others; -p appends to stdin
        # input, so the flag carries only the instruction to read it.
        return ["gemini", "-p", "Follow the work order supplied on standard input.",
                "--approval-mode", "auto_edit", "-o", "stream-json"]
    raise ValueError(f"Unsupported harness: {harness}")


def environment():
    env = dict(os.environ)
    # Use existing subscription login; never silently fall through to API billing.
    for key in list(env):
        if key.startswith(("OPENAI_", "ANTHROPIC_", "CLAUDE_CODE_USE_", "HERMES_KANBAN_",
                           # Same rule for Gemini: the OAuth login is the
                           # subscription path, GEMINI_API_KEY/Vertex are metered.
                           "GEMINI_API_KEY", "GOOGLE_GENAI_", "GOOGLE_API_KEY")):
            env.pop(key)
    env.pop("CLAUDECODE", None)
    return env


def available(harness):
    return shutil.which(command(harness, ".")[0]) is not None


def classify(returncode, stdout, stderr):
    """Only provider error records/stderr can trigger rotation, never generated prose.

    A denied tool attempt inside an otherwise successful run is NOT a
    permission failure: under the scoped Bash allowlist a worker routinely
    attempts a non-git command, gets denied, and continues with allowed tools
    (the denial is recorded in permission_denials for the evidence trail).
    A completed run (is_error False, subtype success) classifies as executed
    even when it carries denied attempts; denied is fatal only when the run
    itself failed or errored.
    """
    errors = []
    denied_failed = False
    retry_after = None
    completed = False
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if not isinstance(event, dict):
            continue
        if event.get("permission_denials") and (
            event.get("is_error") or event.get("type") in {"error", "turn.failed"}
        ):
            denied_failed = True
        if event.get("type") == "result" and not event.get("is_error"):
            completed = True
        if event.get("type") in {"error", "turn.failed"} or event.get("is_error"):
            errors.append(json.dumps(event))
            delay = event.get("retry_after")
            if isinstance(delay, (int, float)) and not isinstance(delay, bool):
                retry_after = min(86400, max(60, delay))
    error = "\n".join(errors + ([stderr] if returncode else [])).lower()
    # Gemini refuses in prose and still exits 0, so its refusals appear in
    # neither the JSON error events nor the returncode-gated stderr above.
    # These two strings are specific enough to read from the raw streams.
    refusal = (stdout + "\n" + stderr).lower()
    if denied_failed or (not completed and re.search(
            r"permission.denied|approval.required|not authorized|sandbox.*denied", error)):
        return "permission", None
    # Gemini reports both of these on stdout/stderr and still exits 0, so
    # neither returncode nor the generic patterns below would catch them.
    if re.search(r"approval mode overridden.*not trusted", refusal):
        # The folder is untrusted, so auto_edit silently became "prompt for
        # approval" and a headless run can change nothing. Failing closed here
        # keeps a run that could not act from being recorded as clean work.
        return "permission", None
    if re.search(r"set an auth method", refusal) or re.search(
            r"authentication|unauthorized|invalid.api.key|login required|not logged in", error):
        return "authentication", None
    if re.search(r"rate_limit|rate limit|usage.limit|quota.exceeded|quota exhausted|too many requests|insufficient_quota", error):
        return "capacity", retry_after
    if returncode or errors:
        return "failed", None
    return "executed", None
