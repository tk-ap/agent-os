"""Normalize connected-browser checks into first-class task execution evidence."""

from dataclasses import asdict, dataclass, field
from urllib.parse import urlsplit

from runtime.task import Task


@dataclass(frozen=True)
class BrowserRouteCheck:
    route: str
    url: str
    title: str
    body_length: int
    console_errors: tuple[str, ...] = field(default_factory=tuple)
    error_overlay: bool = False


@dataclass(frozen=True)
class BrowserVerificationRecord:
    provider: str
    base_url: str
    routes: tuple[BrowserRouteCheck, ...]
    interactions: tuple[str, ...] = field(default_factory=tuple)
    security_state: str = "transport-verified"
    evidence_ref: str | None = None


def attach_browser_evidence(task: Task, record: BrowserVerificationRecord) -> dict:
    """Attach non-secret browser evidence and derive a truthful task state."""

    allowed_origin = _origin(record.base_url)
    if not record.provider or not allowed_origin or not record.routes:
        raise ValueError("browser evidence requires provider, base URL, and route checks")
    for route in record.routes:
        if _origin(route.url) != allowed_origin:
            raise ValueError("browser route escaped the declared base origin")
        if route.body_length < 1:
            raise ValueError(f"browser route is blank: {route.route}")

    task.execution = {
        "status": "EXECUTED",
        "adapter": "codex-browser",
        "provider": record.provider,
        "browser_verification": asdict(record),
        "evidence_scope": "read-only browser route and interaction checks",
    }
    # No authenticated receipt verifier is wired here yet. Caller labels cannot
    # establish runtime security, even when they say "runtime-verified".
    verified = False
    task.verification = {
        "status": "VERIFIED" if verified else "PREVIEWED",
        "checks": [
            f"{len(record.routes)} browser routes rendered",
            f"{len(record.interactions)} read-only interactions checked",
            "no console errors or framework overlays" if all(
                not route.console_errors and not route.error_overlay for route in record.routes
            ) else "console or overlay issues present",
        ],
        "limitations": [] if verified else [
            "provider runtime attestation is unavailable; this is transport-verified evidence only"
        ],
    }
    return task.verification


def _origin(value: str) -> str | None:
    try:
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            return None
        port = parsed.port
    except ValueError:
        return None
    default_port = 80 if parsed.scheme == "http" else 443
    authority = parsed.hostname if port in {None, default_port} else f"{parsed.hostname}:{port}"
    return f"{parsed.scheme}://{authority}"
