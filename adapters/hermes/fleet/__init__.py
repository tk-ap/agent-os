"""Agent OS work orders executed by Hermes's existing Kanban dispatcher.

Telegram is exposed through the human-first presentation adapter. The original
runtime remains the authority/state implementation underneath it.
"""
import sys as _sys

from . import telegram_human
from . import telegram_human_readonly as _telegram_human_readonly
from . import telegram_human_monitor as _telegram_human_monitor
from . import telegram_agent_directory as _telegram_agent_directory
from . import telegram_agent_directory_hotfix as _telegram_agent_directory_hotfix
from . import telegram_runtime_recovery as _telegram_runtime_recovery
from . import telegram_blocker_briefs as _telegram_blocker_briefs
from . import telegram_blocker_brief_migration as _telegram_blocker_brief_migration
from . import telegram_digest as _telegram_digest
from . import telegram_operational_continuity as _telegram_operational_continuity

# Explain is presentation only: install a renderer that performs reads without
# persisting routing proposals or changing any task/approval state. The
# install writes into the wrapper module's own dict, which is exactly where
# the patched handle_update resolves `_technical_details` from.
_telegram_human_readonly.install(telegram_human)

# The human layer installs itself INTO the base runtime module in place
# (base.collect_reviews/deliver/decide/handle_update are the human-first
# versions after import). Expose that single module as `telegram`: every
# attribute read and write — including test isolation patches of ROOT/CONFIG —
# hits the one dict the runtime functions actually read, with no stale copies.
telegram = telegram_human.base

# Monitor-channel fleet/contribution events use the same human-first contract.
# This changes presentation only; approval and execution semantics stay in the
# underlying Telegram runtime.
_telegram_human_monitor.install(telegram)

# Persistent Telegram shortcuts expose the agent directory and allow TK to
# deliberately choose a preferred owner for a real-time request. The chosen
# owner remains subject to normal routing validation, review, and permission
# boundaries; this is human direction, not authority widening.
_telegram_agent_directory.install(telegram)

# The long-running listener dispatches through the underlying base Telegram
# module. Mirror the wrapped directory handler onto that real dispatch target so
# reply-keyboard text such as `Agent directory` and `Status` is intercepted
# before the legacy directive-only handler sees it.
_telegram_agent_directory_hotfix.install(telegram)

# Live-state recovery discovered by the first real autonomous ignition proof.
# Preserve historical done/error rows as evidence, but repair open backlog
# provenance that points at a done mirror and accept commit evidence from
# registered products (including Agent OS itself).
_telegram_runtime_recovery.install(telegram)

# Meaningful blockers are operator information, not something TK should infer
# from silence or raw lifecycle rows. Emit conversational private briefs that say
# what stopped, what happens next, safe alternatives, and exactly what TK needs
# to do (often: nothing).
_telegram_blocker_briefs.install(telegram)

# Existing blocker cards use idempotency keys from the older terse template.
# Emit one upgraded v2 card for currently active blockers so TK does not have to
# wait for another retry/state transition to receive the conversational version.
_telegram_blocker_brief_migration.install(telegram)

# Per-event cards answer "what must TK decide"; they cannot answer "how is the
# workforce doing". One private digest per period says what ran, what the fleet
# handled without TK, what stopped, and what genuinely needs him -- so reviewing
# the fleet is reading one message rather than reassembling a day of fragments.
_telegram_digest.install(telegram)

# Milchik + Polly operational continuity. The existing no-model fleet clock now
# has an ignition path: when the fleet is idle it may start at most one backlog
# item that is already human-origin or explicitly approved, using the exact same
# governed routing path as /next. Release-pending work is surfaced to Polly and
# remains open until scoped release authority + live verification exist.
_telegram_operational_continuity.install(telegram)

# Any existing `from adapters.hermes.fleet import telegram` or
# `from adapters.hermes.fleet.telegram import ...` call now receives the
# patched runtime without changing scheduler/service entrypoints.
_sys.modules[__name__ + ".telegram"] = telegram
