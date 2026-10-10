"""Built-in tools — parallel execution. Core is stdlib; browser/desktop are optional."""
from __future__ import annotations
import os, re, json, difflib, subprocess, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor
from .safety import is_path_blocked, is_cmd_risky

MEMO = {}

def t_read(path: str, offset: int = 1, limit: int = 200) -> dict:
    if is_path_blocked(path): return {"ok": False, "error": "Blocked path"}
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        sel = lines[offset-1:offset-1+limit]
        return {"ok": True, "output": "".join(sel)[:20000],
                "summary": f"{path} ({len(lines)} lines, showing {len(sel)})"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:300]}

def t_write(path: str, content: str) -> dict:
    if is_path_blocked(path): return {"ok": False, "error": "Blocked path"}
    try:
        os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
        open(path, "w", encoding="utf-8").write(content)
        return {"ok": True, "output": f"Wrote {len(content)} chars", "summary": f"Created/wrote {path}"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:300]}

def t_edit(path: str, old: str, new: str) -> dict:
    if is_path_blocked(path): return {"ok": False, "error": "Blocked path"}
    try:
        s = open(path, encoding="utf-8", errors="replace").read()
        if old not in s: return {"ok": False, "error": "Old text not found"}
        open(path, "w", encoding="utf-8").write(s.replace(old, new, 1))
        return {"ok": True, "output": "Edited", "summary": f"Edited {path}"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:300]}

def t_ls(path: str = ".") -> dict:
    try:
        items = sorted(os.listdir(path or "."))
        return {"ok": True, "output": "\n".join(items[:200]), "summary": f"{len(items)} items in {path}"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:300]}

def t_grep(pattern: str, path: str = ".", include: str = "") -> dict:
    outs, n = [], 0
    exts = [e.strip() for e in include.split(",") if e.strip()] or None
    try:
        rx = re.compile(pattern)
    except Exception:
        rx = re.compile(re.escape(pattern))
    for root, _, files in os.walk(path or "."):
        if any(x in root for x in (".git", "__pycache__", "node_modules", ".venv")): continue
        for fn in files:
            if exts and not any(fn.endswith(e) for e in exts): continue
            fp = os.path.join(root, fn)
            try:
                if os.path.getsize(fp) > 500_000: continue
                txt = open(fp, encoding="utf-8", errors="ignore").read()
                for i, ln in enumerate(txt.splitlines(), 1):
                    if rx.search(ln):
                        outs.append(f"{fp}:{i}: {ln[:200]}")
                        n += 1
                        if n >= 60: break
            except Exception:
                pass
            if n >= 60: break
        if n >= 60: break
    return {"ok": True, "output": "\n".join(outs) or "No matches", "summary": f"{n} match(es) for /{pattern}/"}

def t_bash(cmd: str, timeout: int = 60, cwd: str = ".") -> dict:
    if is_cmd_risky(cmd): return {"ok": False, "error": "Blocked (destructive) command — refused"}
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout, cwd=cwd or ".")
        out = (p.stdout or "") + (("\n[stderr]\n" + p.stderr) if p.stderr else "")
        return {"ok": p.returncode == 0, "output": out[-8000:] or f"(exit {p.returncode})",
                "summary": f"exit={p.returncode} `{cmd[:80]}`"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"Timed out ({timeout}s)"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:300]}

def t_todo(action: str = "list", item: str = "") -> dict:
    lst = MEMO.setdefault("todos", [])
    if action == "add" and item: lst.append({"t": item, "done": False})
    elif action == "done" and item:
        for x in lst:
            if item in x["t"]: x["done"] = True
    elif action == "clear": lst.clear()
    txt = "\n".join(f"[{'x' if x['done'] else ' '}] {x['t']}" for x in lst) or "(empty)"
    return {"ok": True, "output": txt, "summary": f"{len(lst)} task(s)"}

def t_memory(action: str = "list", key: str = "", value: str = "") -> dict:
    m = MEMO.setdefault("mem", {})
    if action == "set" and key: m[key] = value
    elif action == "get" and key: return {"ok": True, "output": str(m.get(key, "")), "summary": key}
    return {"ok": True, "output": json.dumps(m, ensure_ascii=False)[:4000], "summary": f"{len(m)} memor(ies)"}

def t_webfetch(url: str) -> dict:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "s_agent/1.1"})
        txt = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "ignore")
        txt = re.sub(r"<script.*?</script>|<style.*?</style>|<[^>]+>", " ", txt, flags=re.S)
        txt = re.sub(r"\s+", " ", txt)
        return {"ok": True, "output": txt[:6000], "summary": f"Fetched {url[:70]}"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:300]}

def t_websearch(query: str) -> dict:
    try:
        q = urllib.parse.quote(query)
        req = urllib.request.Request(f"https://html.duckduckgo.com/html/?q={q}",
            headers={"User-Agent": "Mozilla/5.0"})
        html = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "ignore")
        links = re.findall(r'result__a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html)[:10]
        out = "\n".join(f"- {re.sub('<[^>]+>','',t)[:120]} — {u[:120]}" for u, t in links) or "No results"
        return {"ok": True, "output": out, "summary": f"Search: {query[:50]}"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:300]}

def t_diff(path: str = "") -> dict:
    try:
        if path and os.path.isfile(path):
            return {"ok": True, "output": "(see git diff for details)", "summary": path}
        p = subprocess.run("git diff --stat 2>&1 | head -30", shell=True, capture_output=True, text=True, timeout=15)
        return {"ok": True, "output": (p.stdout or "No git or no changes")[:4000], "summary": "diff --stat"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}

def t_patch(path: str, unified: str) -> dict:
    """Apply edits in a simple format: lines starting with - are removed, + are added."""
    if is_path_blocked(path): return {"ok": False, "error": "Blocked path"}
    try:
        cur = open(path, encoding="utf-8", errors="replace").read().splitlines() if os.path.exists(path) else []
        for ln in unified.splitlines():
            if ln.startswith("-"):
                t = ln[1:]
                if t in cur: cur.remove(t)
            elif ln.startswith("+"):
                cur.append(ln[1:])
        open(path, "w", encoding="utf-8").write("\n".join(cur))
        return {"ok": True, "output": "Simple patch applied", "summary": f"patch {path}"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:300]}

def _t_browser(action: str = "status", **kw) -> dict:
    """Lazy wrapper: imports browser_pw only when called (core stays stdlib)."""
    try:
        from .browser_pw import t_browser as _b
        return _b(action=action, **kw)
    except Exception as e:
        return {"ok": False, "error": str(e)[:300], "summary": "browser unavailable"}

def _t_desktop(action: str = "status", **kw) -> dict:
    try:
        from .desktop import t_desktop as _d
        for k in ("x", "y", "clicks", "amount"):
            if k in kw and isinstance(kw[k], str) and kw[k].lstrip("-").isdigit():
                kw[k] = int(kw[k])
        return _d(action=action, **kw)
    except Exception as e:
        return {"ok": False, "error": str(e)[:300], "summary": "desktop unavailable"}

REGISTRY = {
    "read":   (t_read, "Read a file"),
    "write":  (t_write, "Write a file"),
    "edit":   (t_edit, "Targeted edit"),
    "ls":     (t_ls, "List a directory"),
    "grep":   (t_grep, "Search code"),
    "bash":   (t_bash, "Run a shell command"),
    "todo":   (t_todo, "Task list"),
    "memory": (t_memory, "Persistent memory"),
    "webfetch": (t_webfetch, "Fetch a page"),
    "websearch": (t_websearch, "Web search"),
    "diff":   (t_diff, "Show changes"),
    "patch":  (t_patch, "Patch a file"),
    "browser": (_t_browser, "Real browser via Playwright"),
    "desktop": (_t_desktop, "Desktop control via PyAutoGUI"),
}

def describe_tools() -> str:
    return "\n".join(f"- {k}: {v[1]}" for k, v in REGISTRY.items())

def run_tool(name: str, args: dict, cwd: str = ".") -> dict:
    fn = REGISTRY.get(name, (None, ""))[0]
    if not fn:
        return {"ok": False, "tool": name, "error": f"Unknown tool: {name}", "summary": "Rejected"}
    try:
        if name == "bash" and "cwd" not in args:
            args = {**args, "cwd": cwd}
        r = fn(**{k: v for k, v in (args or {}).items()})
        r["tool"] = name
        r.setdefault("summary", name)
        return r
    except TypeError as e:
        return {"ok": False, "tool": name, "error": f"Bad arguments: {e}", "summary": "Argument error"}

def run_batch(calls: list, cwd: str = ".", parallel: bool = True) -> list:
    """Run independent batches in parallel for higher speed."""
    if not parallel or len(calls) < 2:
        return [run_tool(c.get("tool",""), c.get("args",{}), cwd) for c in calls]
    with ThreadPoolExecutor(max_workers=min(8, len(calls))) as ex:
        futs = [ex.submit(run_tool, c.get("tool",""), c.get("args",{}), cwd) for c in calls]
        return [f.result() for f in futs]
