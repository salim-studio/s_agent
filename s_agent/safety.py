"""Safety guardrails: block destructive paths/commands + interactive confirmation."""
from __future__ import annotations
import os, re

BLOCKED_PATHS = [
    "C:\\Windows\\System32", "C:\\Windows", "/etc", "/sys", "/proc",
    os.path.join(os.path.expanduser("~"), ".ssh"),
]
BLOCKED_NAMES = {"id_rsa", "id_ed25519", ".env"}

RISKY_CMD = re.compile(
    r"(rm\s+-rf\s+/( |$)|mkfs|dd\s+of=/dev|:?\(\)\s*\{\s*:\|:\s*&\s*\}|shutdown|format\s+[a-z]:|rd\s+/s\s+/q\s+c:\\)",
    re.I)

def is_path_blocked(path: str) -> bool:
    ap = os.path.abspath(path)
    for b in BLOCKED_PATHS:
        try:
            if ap.lower() == b.lower() or ap.lower().startswith(b.lower().rstrip("\\/") + os.sep.lower().replace("/", "\\") if os.name=="nt" else b.lower() + "/"):
                return True
        except Exception:
            pass
    if os.path.basename(ap) in BLOCKED_NAMES:
        return True
    return False

def is_cmd_risky(cmd: str) -> bool:
    return bool(RISKY_CMD.search(cmd or ""))

def need_confirm(tool: str, args: dict, safe_mode: bool) -> str:
    """Return the reason confirmation is required, or ''."""
    if not safe_mode:
        return ""
    if tool in ("write", "edit", "multiedit", "patch", "bash"):
        return "Writing/executing requires confirmation (safe mode)"
    return ""
