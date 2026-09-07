"""Agent OS work orders executed by Hermes's existing Kanban dispatcher.

Telegram is exposed through the human-first presentation adapter. The original
runtime remains the authority/state implementation underneath it.
"""
import sys as _sys

from . import telegram_human as telegram
from . import telegram_human_readonly as _telegram_human_readonly

# Explain is presentation only: install a renderer that performs reads without
# persisting routing proposals or changing any task/approval state.
_telegram_human_readonly.install(telegram)

# Any existing `from adapters.hermes.fleet import telegram` or
# `from adapters.hermes.fleet.telegram import ...` call now receives the
# presentation adapter without changing scheduler/service entrypoints.
_sys.modules[__name__ + ".telegram"] = telegram
