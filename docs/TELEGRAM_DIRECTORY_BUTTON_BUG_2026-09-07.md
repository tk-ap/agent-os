# Telegram Agent Directory shortcut bug — 2026-09-07

## Observed live behavior

The persistent reply keyboard renders correctly with `Agent directory` and `Status`, but pressing either button sends plain text into the older directive handler, which replies:

> Not recorded. Prefix a directive with > or /do — plain messages here are not instructions.

## Root cause

`telegram_agent_directory.install()` wraps `telegram.handle_update`, but the long-running listener path is still dispatching through the underlying base Telegram module's `handle_update` reference. The shortcut UI is therefore installed, but the button-text interception is not on the actual live listener dispatch path.

## Required fix

Install the directory wrapper on the real dispatch target as well as the public adapter surface. In practice, when the human presentation adapter exposes an underlying `base` module, set that module's `handle_update` to the wrapped handler too. Preserve all existing authorization checks and callback behavior.

Acceptance:
- tapping `Agent directory` opens the agent directory immediately;
- tapping `Status` returns the status view immediately;
- `/agents` opens the directory;
- ordinary plain text still remains non-directive unless TK is in a pending `Direct a request to <Agent>` flow;
- selecting an agent and sending the next plain-language message records that directed request;
- no permission, review, publish, or deployment authority changes.
