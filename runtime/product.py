from pathlib import Path
import re
import subprocess
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ROUTING_FILE = ROOT / "registry" / "product-routing.yaml"


def _section(text: str, heading: str) -> str:
    m = re.search(rf"^\s*{re.escape(heading)}:\s*$", text, re.M)
    if not m:
        return ""
    rest = text[m.end():]
    nxt = re.search(r"^\S.*:\s*$", rest, re.M)
    return rest[:nxt.start()] if nxt else rest


def _products(text: str) -> dict[str, dict[str, Any]]:
    section = _section(text, "products")
    result: dict[str, dict[str, Any]] = {}
    current = None
    for line in section.splitlines():
        m = re.match(r"^  ([a-z0-9][a-z0-9-]*):\s*$", line)
        if m:
            current = m.group(1)
            result[current] = {}
            continue
        if current:
            m = re.match(r"^    repository:\s*(.+)$", line)
            if m:
                result[current]["repository"] = m.group(1).strip().strip("'\"")
            m = re.match(r"^    role:\s*(.+)$", line)
            if m:
                result[current]["role"] = m.group(1).strip()
            m = re.match(r"^    plane:\s*(.+)$", line)
            if m:
                result[current]["plane"] = m.group(1).strip()
    return result


def _environments(text: str) -> dict[str, dict[str, str]]:
    section = _section(text, "environments")
    result = {}
    for line in section.splitlines():
        m = re.match(r"^  ([a-z0-9][a-z0-9-]*):\s*(.*)$", line)
        if m:
            name, value = m.groups()
            result[name] = {"config": value}
    return result


def _repo_exists(repo: str) -> bool:
    p = subprocess.run(["gh", "api", f"repos/{repo}"], capture_output=True, text=True)
    return p.returncode == 0


def resolve_product(request: str, explicit: str | None = None) -> dict[str, Any]:
    text = ROUTING_FILE.read_text()
    products = _products(text)
    lowered = request.lower()
    key = explicit
    if not key:
        matches = sorted(products, key=len, reverse=True)
        for candidate in matches:
            if re.search(rf"(?<![a-z0-9]){re.escape(candidate)}(?![a-z0-9])", lowered):
                key = candidate
                break
    if not key:
        aliases = {"ashwood-web": "ashwood", "alvira": "alvira-meos", "agent control": "agent-control"}
        for alias, candidate in aliases.items():
            if alias in lowered and candidate in products:
                key = candidate
                break
    if not key:
        return {"status": "UNRESOLVED", "reason": "No product matched the request."}
    if key not in products:
        return {"status": "UNRESOLVED", "reason": f"Product '{key}' is not in registry/product-routing.yaml."}

    info = products[key]
    repo = info.get("repository")
    if not repo:
        repo = {"ashwood": "tk-ap/ashwood-web", "alvira-meos": "tk-ap/ALVIRA", "ailhat": "tk-ap/ailhat"}.get(key, f"tk-ap/{key}")
    integrated = False
    if _repo_exists(repo):
        p = subprocess.run(["gh", "api", f"repos/{repo}/contents/.agent-os/product.yaml"], capture_output=True, text=True)
        integrated = p.returncode == 0

    return {
        "status": "RESOLVED",
        "product_key": key,
        "repository": repo,
        "plane": info.get("plane"),
        "role": info.get("role"),
        "integration_level": "NATIVE" if integrated else "DISCOVERABLE",
        "source": "registry/product-routing.yaml",
    }
