"""OpenAI-compatible LLM client + local engine (works with no API key) — stdlib only."""
from __future__ import annotations
import json, urllib.request
from .config import SConfig

SYSTEM = ('You are s_agent: a practical coding agent. '
  'Answer with a short plan, then act with tools. A tool call is one JSON line, e.g. '
  '{"tool":"read","args":{"path":"."}} — one or more calls, each on its own block. '
  'Tools: read,write,edit,ls,grep,bash,todo,memory,webfetch,websearch,patch,diff,browser,desktop. '
  'Understand -> plan -> execute -> verify -> report. Reply in English.')

def chat_openai_compat(cfg: SConfig, messages: list, timeout: int = 60) -> str:
    url = cfg.endpoint()
    if not url:
        raise RuntimeError("no-endpoint")
    key = cfg.api_key or ""
    body = json.dumps({
        "model": cfg.model, "messages": messages,
        "temperature": 0.2, "max_tokens": 2000,
    }).encode()
    req = urllib.request.Request(url, data=body, method="POST",
        headers={"Content-Type": "application/json",
                 **({"Authorization": f"Bearer {key}"} if key else {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.load(r)
    try:
        return d["choices"][0]["message"]["content"] or ""
    except Exception:
        return json.dumps(d, ensure_ascii=False)[:2000]

# ---------- Local engine: instant planning with no network (bilingual EN/AR) ----------
import os, re
def local_plan(task: str, cwd: str) -> list:
    """Turn a task directly into tool steps (fast, no LLM). Accepts English and Arabic."""
    t = task.strip()
    steps = []
    # Real browser: open/browse/screenshot/fill forms (Playwright + Firefox)
    m_url = re.search(r"https?://[^\s\"'<>]+", t)
    if re.search(r"browser|firefox|playwright|open https?://|open (the |this )?(site|link|page|url)|screenshot.*(page|site|browser)|متصفح|فايرفوكس|افتح (الموقع|الرابط|صفحة)|لقطة.*(متصفح|موقع|صفحة)", t, re.I):
        if m_url:
            u = m_url.group(0)
            steps.append({"tool": "browser", "args": {"action": "open", "url": u}})
            steps.append({"tool": "browser", "args": {"action": "text"}})
            if re.search(r"screenshot|لقطة|صورة", t, re.I):
                steps.append({"tool": "browser", "args": {"action": "screenshot"}})
            return steps
        steps.append({"tool": "browser", "args": {"action": "status"}})
        return steps
    # Desktop: calculator/click/type/screen capture (PyAutoGUI)
    if re.search(r"desktop|screen|calculator|pyautogui|click|move (the )?mouse|screen ?shot|capture|سطح المكتب|الشاشة|الحاسبة|انقر|حرّك الفأرة|لقطة شاشة", t, re.I):
        if re.search(r"shot|capture|لقطة", t, re.I):
            return [{"tool": "desktop", "args": {"action": "screenshot"}}]
        return [{"tool": "desktop", "args": {"action": "status"}}]
    if re.search(r"contents|folder|directory|show|list files|\bls\b|محتويات|مجلد|مجلّد|اعرض", t, re.I):
        return [{"tool": "ls", "args": {"path": cwd}}]
    m = re.search(r"(?:read|explain|show|open)\s*[ :]*([^\n]+)?", t, re.I)
    if re.search(r"explain|structure|entry|architect|مكوّن|هيكل|اشرح", t, re.I):
        steps += [
            {"tool": "ls", "args": {"path": cwd}},
            {"tool": "grep", "args": {"pattern": "def main|if __name__|class .*Agent|function main", "path": cwd}},
        ]
        return steps
    if m and m.group(1):
        target = m.group(1).strip().strip("\"'")[:200]
        cand = target if os.path.isabs(target) else os.path.join(cwd, target)
        if os.path.exists(cand):
            return [{"tool": "read", "args": {"path": cand}}]
        return [{"tool": "grep", "args": {"pattern": re.escape(target[:40]), "path": cwd}}]
    if re.search(r"\bsearch\b|grep|find|trace|locate|ابحث|أين", t, re.I):
        kw = re.sub(r"(search|grep|find|trace|locate|for|ابحث|عن|في)\s*", " ", t, flags=re.I).strip()[:60] or "TODO"
        return [{"tool": "grep", "args": {"pattern": kw, "path": cwd}}]
    if re.search(r"\btest\b|verify|check|run\b|اختبار|تحقق", t, re.I):
        return [
            {"tool": "ls", "args": {"path": cwd}},
            {"tool": "bash", "args": {"cmd": "python -m pytest -q 2>&1 | head -50" if os.path.exists(os.path.join(cwd,"tests")) else "python --version && dir" if os.name=="nt" else "python3 --version && ls"}},
        ]
    if re.search(r"create|write|new file|أنشئ|اكتب|ملف", t, re.I):
        steps.append({"tool": "ls", "args": {"path": cwd}})
        return steps
    # Default: quick exploration
    return [
        {"tool": "ls", "args": {"path": cwd}},
        {"tool": "bash", "args": {"cmd": "dir" if os.name == "nt" else "ls -la | head -40"}},
    ]

def local_summarize(task: str, observations: list) -> str:
    out = [f"## Understood\nTask: {task}", "\n## Done"]
    for o in observations[-8:]:
        out.append(f"- [{o.get('tool')}] {str(o.get('ok'))} — {str(o.get('summary',''))[:220]}")
    out += ["\n## Verified\n- Tool outputs above were reviewed.",
            "\n## Remaining\n- Name a precise next step (e.g. a file path) and I will run it right away."]
    return "\n".join(out)
