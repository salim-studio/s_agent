"""OpenAI-compatible LLM client + local engine (works with no API key) — stdlib only."""
from __future__ import annotations
import json, urllib.request
from .config import SConfig
from .i18n import t, cur, LANGS

def system_prompt() -> str:
    lang_name = LANGS.get(cur(), "English")
    return t("sys", lang=lang_name)

SYSTEM = ""  # kept for backward-compat; use system_prompt() instead

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

# ---------- Local engine: instant planning with no network (multilingual EN/AR/FR/ES) ----------
import os, re
def local_plan(task: str, cwd: str) -> list:
    """Turn a task directly into tool steps (fast, no LLM). Accepts English and Arabic."""
    t = task.strip()
    steps = []
    # Real browser: open/browse/screenshot/fill forms (Playwright + Firefox)
    m_url = re.search(r"https?://[^\s\"'<>]+", t)
    if re.search(r"browser|firefox|playwright|open https?://|ouvrir https?://|abrir https?://|open (the |this )?(site|link|page|url)|screenshot.*(page|site|browser)|ouvrir|naviguer|navegador|abrir|متصفح|فايرفوكس|افتح (الموقع|الرابط|صفحة)|لقطة.*(متصفح|موقع|صفحة)", t, re.I):
        if m_url:
            u = m_url.group(0)
            steps.append({"tool": "browser", "args": {"action": "open", "url": u}})
            steps.append({"tool": "browser", "args": {"action": "text"}})
            if re.search(r"screenshot|capture|لقطة|صورة", t, re.I):
                steps.append({"tool": "browser", "args": {"action": "screenshot"}})
            return steps
        steps.append({"tool": "browser", "args": {"action": "status"}})
        return steps
    # Desktop: calculator/click/type/screen capture (PyAutoGUI)
    if re.search(r"desktop|screen|calculator|calculatrice|calculadora|pyautogui|click|cliquer|haz clic|move (the )?mouse|déplacer|capture|screen ?shot|bureau|écran|escritorio|pantalla|سطح المكتب|الشاشة|الحاسبة|انقر|حرّك الفأرة|لقطة شاشة", t, re.I):
        if re.search(r"shot|capture|لقطة", t, re.I):
            return [{"tool": "desktop", "args": {"action": "screenshot"}}]
        return [{"tool": "desktop", "args": {"action": "status"}}]
    if re.search(r"contents|folder|directory|show|list files|lister|contenu|dossier|afficher|listar|mostrar|contenido|carpeta|\bls\b|محتويات|مجلد|مجلّد|اعرض", t, re.I):
        return [{"tool": "ls", "args": {"path": cwd}}]
    m = re.search(r"(?:read|explain|show|open|lire|expliquer|afficher|ouvrir|leer|explicar|mostrar|abrir)\s*[ :]*([^\n]+)?", t, re.I)
    if re.search(r"explain|structure|entry|architect|expliquer|explicar|estructura|مكوّن|هيكل|اشرح", t, re.I):
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
    if re.search(r"\bsearch\b|grep|find|trace|locate|chercher|rechercher|buscar|rastrear|où|dónde|ابحث|أين", t, re.I):
        kw = re.sub(r"(search|grep|find|trace|locate|for|chercher|rechercher|buscar|rastrear|où|dónde|ابحث|عن|في)\s*", " ", t, flags=re.I).strip()[:60] or "TODO"
        return [{"tool": "grep", "args": {"pattern": kw, "path": cwd}}]
    if re.search(r"\btest\b|verify|check|run\b|tester|vérifier|exécuter|probar|verificar|ejecutar|اختبار|تحقق", t, re.I):
        return [
            {"tool": "ls", "args": {"path": cwd}},
            {"tool": "bash", "args": {"cmd": "python -m pytest -q 2>&1 | head -50" if os.path.exists(os.path.join(cwd,"tests")) else "python --version && dir" if os.name=="nt" else "python3 --version && ls"}},
        ]
    if re.search(r"create|write|new file|créer|écrire|fichier|crear|escribir|archivo|أنشئ|اكتب|ملف", t, re.I):
        steps.append({"tool": "ls", "args": {"path": cwd}})
        return steps
    # Default: quick exploration
    return [
        {"tool": "ls", "args": {"path": cwd}},
        {"tool": "bash", "args": {"cmd": "dir" if os.name == "nt" else "ls -la | head -40"}},
    ]

def local_summarize(task: str, observations: list) -> str:
    out = [t("r_understood") + "\n" + t("r_task", task=task), "\n" + t("r_done")]
    for o in observations[-8:]:
        out.append(f"- [{o.get('tool')}] {str(o.get('ok'))} — {str(o.get('summary',''))[:220]}")
    out += ["\n" + t("r_verified") + "\n" + t("r_verified1"),
            "\n" + t("r_remaining") + "\n" + t("r_remaining1")]
    return "\n".join(out)
