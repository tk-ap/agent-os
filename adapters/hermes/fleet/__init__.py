"""Agent OS work orders executed by Hermes's existing Kanban dispatcher.

Telegram is exposed through the human-first presentation adapter. The original
runtime remains the authority/state implementation underneath it.
"""
import sys as _sys

from . import telegram_human as telegram

# Any existing `from adapters.hermes.fleet import telegram` or
# `from adapters.hermes.fleet.telegram import ...` call now receives the
# presentation adapter without changing scheduler/service entrypoints.
_sys.modules[__name__ + ".telegram"] = telegram
