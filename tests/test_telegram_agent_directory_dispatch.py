"""Regression tests for Telegram reply-keyboard directory/status dispatch."""


def test_hotfix_installs_wrapped_handler_on_base_module():
    from adapters.hermes.fleet import telegram
    base = getattr(telegram, "base", None)
    assert base is not None
    assert base.handle_update is telegram.handle_update
