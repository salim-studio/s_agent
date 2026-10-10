"""عميل LLM متوافق مع OpenAI + محرك محلي (يعمل بدون مفتاح) — stdlib فقط."""
from __future__ import annotations
import json, urllib.request
from .config import SConfig

SYSTEM = ('أنت s_agent: وكيل برمجة عملي يتكلم العربية. '
  'أجب بخطة قصيرة ثم نفذ بالأدوات. صيغة استدعاء الأداة سطر JSON داخل كتلة tool، مثال: '
  '{"tool":"read","args":{"path":"."}} — أداة واحدة أو أكثر، كل واحدة في كتلة مستقلة. '
  'الأدوات: read,write,edit,ls,grep,bash,todo,memory,webfetch,websearch,patch,diff.')

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

# ---------- المحرك المحلي: تخطيط سريع بدون شبكة ----------
import os, re
def local_plan(task: str, cwd: str) -> list:
    """يحوّل المهمة إلى خطوات أدوات مباشرة (سريع، بلا LLM)."""
    t = task.strip()
    steps = []
    # متصفح حقيقي: افتح/تصفح/لقطة/املأ نموذج (Playwright + Firefox)
    m_url = re.search(r"https?://[^\s\"'<>]+", t)
    if re.search(r"متصفح|فايرفوكس|browser|playwright|افتح (الموقع|الرابط|صفحة)|لقطة.*(متصفح|موقع|صفحة)|screenshot.*(page|site|browser)", t, re.I):
        if m_url:
            u = m_url.group(0)
            steps.append({"tool": "browser", "args": {"action": "open", "url": u}})
            steps.append({"tool": "browser", "args": {"action": "text"}})
            if re.search(r"لقطة|screenshot|صورة", t, re.I):
                steps.append({"tool": "browser", "args": {"action": "screenshot"}})
            return steps
        steps.append({"tool": "browser", "args": {"action": "status"}})
        return steps
    # سطح المكتب: حاسبة/انقر/اكتب/لقطة شاشة (PyAutoGUI)
    if re.search(r"سطح المكتب|الشاشة|الحاسبة|calculator|desktop|pyautogui|انقر|حرّك الفأرة|لقطة شاشة", t, re.I):
        if re.search(r"لقطة|screenshot", t, re.I):
            return [{"tool": "desktop", "args": {"action": "screenshot"}}]
        return [{"tool": "desktop", "args": {"action": "status"}}]
    # أمثلة أنماط شائعة بالعربية/الإنجليزية
    if re.search(r"محتويات|مجلد|مجلّد|اعرض|contents|folder|list files|\bls\b", t, re.I):
        return [{"tool": "ls", "args": {"path": cwd}}]
    m = re.search(r"(?:اقرأ|اعرض|اشرح|read|explain)\s*[ :]*([^\n]+)?", t, re.I)
    if re.search(r"اشرح|مكوّن|هيكل|entry|explain|struct|list", t, re.I):
        steps += [
            {"tool": "ls", "args": {"path": cwd}},
            {"tool": "grep", "args": {"pattern": "def main|if __name__|class .*Agent|function main", "path": cwd}},
        ]
        return steps
    if m and m.group(1):
        target = m.group(1).strip().strip("\"'")[:200]
        # إن كان مسارًا موجودًا اقرأه، وإلا ابحث عنه
        cand = target if os.path.isabs(target) else os.path.join(cwd, target)
        if os.path.exists(cand):
            return [{"tool": "read", "args": {"path": cand}}]
        return [{"tool": "grep", "args": {"pattern": re.escape(target[:40]), "path": cwd}}]
    if re.search(r"ابحث|search|grep|أين|trace", t, re.I):
        kw = re.sub(r"(ابحث|عن|في|search|grep|find|for)\s*", " ", t, flags=re.I).strip()[:60] or "TODO"
        return [{"tool": "grep", "args": {"pattern": kw, "path": cwd}}]
    if re.search(r"اختبار|test|تحقق|verify|run", t, re.I):
        return [
            {"tool": "ls", "args": {"path": cwd}},
            {"tool": "bash", "args": {"cmd": "python -m pytest -q 2>&1 | head -50" if os.path.exists(os.path.join(cwd,"tests")) else "python --version && dir" if os.name=="nt" else "python3 --version && ls"}},
        ]
    if re.search(r"أنشئ|اكتب|ملف|create|write|new file", t, re.I):
        steps.append({"tool": "ls", "args": {"path": cwd}})
        return steps
    # افتراضي: استكشاف سريع
    return [
        {"tool": "ls", "args": {"path": cwd}},
        {"tool": "bash", "args": {"cmd": "dir" if os.name == "nt" else "ls -la | head -40"}},
    ]

def local_summarize(task: str, observations: list) -> str:
    out = [f"## ما تم فهمه\nالمهمة: {task}", "\n## ما تم فعله"]
    for o in observations[-8:]:
        out.append(f"- [{o.get('tool')}] {str(o.get('ok'))} — {str(o.get('summary',''))[:220]}")
    out += ["\n## ما تم التحقق منه\n- رُوجعت مخرجات الأدوات أعلاه.",
            "\n## المتبقي\n- حدّد خطوة تالية بدقة (مثال: اذكر اسم ملف) وسأنفذها فورًا."]
    return "\n".join(out)
