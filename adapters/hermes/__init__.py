"""Hermes harness adapter package.

Browser execution support is optional until the browser-security workstream lands.
Core fleet, routine, and updater modules must remain importable without it.
"""

__all__: list[str] = []

try:
    from adapters.hermes.browser import (
        BASE_ATTESTATION_CAPABILITIES,
        HermesBrowserSurface,
        prepare_hermes_browser_execution,
        surface_from_manifest,
        verify_hermes_browser_execution,
    )
except ModuleNotFoundError as exc:
    # Only tolerate the intentionally optional adapter itself being absent.
    # Missing dependencies *inside* browser.py must still fail closed.
    if exc.name != "adapters.hermes.browser":
        raise
else:
    __all__ = [
        "BASE_ATTESTATION_CAPABILITIES",
        "HermesBrowserSurface",
        "prepare_hermes_browser_execution",
        "surface_from_manifest",
        "verify_hermes_browser_execution",
    ]
