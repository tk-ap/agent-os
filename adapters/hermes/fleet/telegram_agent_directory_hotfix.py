"""Hotfix installer for Telegram Agent Directory live listener dispatch.

The directory module wraps the public adapter's handle_update. The long-running
listener ultimately dispatches through the underlying base Telegram module, so
this installer mirrors the wrapped handler onto that real dispatch target.
"""


def install(telegram):
    base = getattr(telegram, "base", None)
    if base is not None:
        base.handle_update = telegram.handle_update
