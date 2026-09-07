"""Agent OS work orders executed by Hermes's existing Kanban dispatcher.

Telegram is exposed through the human-first presentation adapter. The original
runtime remains the authority/state implementation underneath it.
"""
import sys as _sys

from . import telegram_human as telegram
from . import telegram_human_readonly as _telegram_human_readonly
from . import telegram_human_monitor as _telegram_human_monitor
from . import telegram_agent_directory as _telegram_agent_directory

# Explain is presentation only: install a renderer that performs reads without
# persisting routing proposals or changing any task/approval state.
_telegram_human_readonly.install(telegram)

# Monitor-channel fleet/contribution events use the same human-first contract.
# This changes presentation only; approval and execution semantics stay in the
# underlying Telegram runtime.
_telegram_human_monitor.install(telegram)

# Persistent Telegram shortcuts expose the agent directory and allow TK to
# deliberately choose a preferred owner for a real-time request. The chosen
# owner remains subject to normal routing validation, review, and permission
# boundaries; this is human direction, not authority widening.
_telegram_agent_directory.install(telegram)

# Any existing `from adapters.hermes.fleet import telegram` or
# `from adapters.hermes.fleet.telegram import ...` call now receives the
# presentation adapter without changing scheduler/service entrypoints.
_sys.modules[__name__ + ".telegram"] = telegram
