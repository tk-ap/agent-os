# Hermes activation note — Telegram Agent Directory and humanized monitor

Execute this now on the AgentOS workstation.

## Goal

Activate and verify the newly merged Telegram operator updates from PR #39.

## Required steps

1. Pull the latest `main` for `tk-ap/agent-os`.
2. Confirm the merge containing the humanized monitor, permission-state handling, `docs/AGENT_DIRECTORY.md`, and Telegram Agent Directory/direct-request flow is present.
3. Restart the Milchik Telegram listener/service so the new runtime is loaded.
4. Refresh the bot command/menu state if Telegram does not surface the new controls automatically.
5. Verify in Telegram, on-device, all of the following:
   - `/agents` opens the Agent Directory.
   - The persistent `Agent directory` shortcut is visible.
   - Selecting an agent shows role, specialties, and typical contribution in plain language.
   - `Direct a request to <Agent>` makes the next plain-language message a human-selected-owner directive.
   - Router preserves the selected owner unless there is a real incompatibility or safety reason; any override must be explained to TK.
   - Monitor handoffs are human-readable rather than raw `directive-*` / queue terminology.
   - `permission` / `waiting_approval` is shown as `Decision required — <Agent> needs permission to continue`, not `Finished: permission` / `Stuck`.
   - A protected action creates the corresponding private approval path and no permission boundary is crossed without approval.
6. Run the existing Telegram E2E tests and any relevant review/monitor tests.
7. Send TK a concise result report with:
   - **Live and verified**
   - **Live but not verified**
   - **Blocked / needs TK**
   - **Failed**

Do not report complete merely because the code was pulled or the service restarted. Completion requires an actual Telegram test of the directory, direct-to-agent request routing, handoff messaging, and permission/approval path.
