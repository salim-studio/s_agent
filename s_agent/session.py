"""الجلسات المستمرة — JSONL خفيف وسريع."""
from __future__ import annotations
import json, os, time, uuid
from .config import sessions_dir

def new_id() -> str:
    return time.strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]

def save_turn(sid: str, role: str, text: str):
    d = sessions_dir()
    p = os.path.join(d, f"{sid}.jsonl")
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps({"t": time.time(), "role": role, "text": text[:8000]}, ensure_ascii=False) + "\n")
    return p

def list_sessions() -> list:
    d = sessions_dir()
    out = []
    for fn in sorted(os.listdir(d), reverse=True):
        if fn.endswith(".jsonl"):
            fp = os.path.join(d, fn)
            out.append({"id": fn[:-6], "size": os.path.getsize(fp)})
    return out[:30]

def load_session(sid: str) -> list:
    p = os.path.join(sessions_dir(), f"{sid}.jsonl")
    if not os.path.exists(p): return []
    rows = []
    for ln in open(p, encoding="utf-8"):
        try: rows.append(json.loads(ln))
        except Exception: pass
    return rows
