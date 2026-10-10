"""تحكم سطح المكتب عبر PyAutoGUI (+ fallback وندوز) — مثل alphacode لكن أخف.

تثبيت:
  pip install pyautogui pillow
ملاحظة أمان: FAILSAFE مفعّل — حرّك الفأرة للزاوية العلوية اليسرى للإيقاف الفوري.
النقر يتطلب إحداثيات صريحة أو صورة. لا ينقر عشوائيًا.
"""
from __future__ import annotations
import os, time

def ensure():
    try:
        import pyautogui  # noqa
        return True, "pyautogui مثبت"
    except ImportError:
        return False, "pyautogui غير مثبت — نفّذ: pip install pyautogui pillow"

def t_desktop(action: str = "status", x: int = None, y: int = None,
              text: str = "", key: str = "", path: str = "",
              button: str = "left", clicks: int = 1, amount: int = 200,
              confidence: float = 0.85) -> dict:
    """أداة سطح المكتب: status|size|screenshot|move|click|type|press|hotkey|scroll|locate|windows."""
    ok, msg = ensure()
    if action == "status":
        if not ok:
            # fallback: وندوز على الأقل للقطات عبر PowerShell؟ نكتفي بالتقرير
            return {"ok": False, "output": msg, "summary": "سطح المكتب غير جاهز"}
        import pyautogui
        w, h = pyautogui.size()
        px, py = pyautogui.position()
        return {"ok": True, "output": f"جاهز — الشاشة {w}x{h} — الفأرة ({px},{py}) — FAILSAFE مفعّل",
                "summary": f"desktop {w}x{h}"}
    if not ok:
        return {"ok": False, "error": msg, "summary": "pyautogui ناقص"}
    import pyautogui
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.15
    try:
        if action == "size":
            w, h = pyautogui.size()
            return {"ok": True, "output": f"{w}x{h}", "summary": f"size {w}x{h}"}
        if action == "screenshot":
            out = path or os.path.join(os.path.expanduser("~"), "s_agent_desktop.png")
            t0 = time.time()
            pyautogui.screenshot(out)
            dt = time.time() - t0
            return {"ok": True, "output": f"حُفظت: {out} ({dt:.1f}s)", "summary": "desktop screenshot"}
        if action == "move":
            if x is None or y is None:
                return {"ok": False, "error": "move يتطلب x و y", "summary": "إحداثيات ناقصة"}
            pyautogui.moveTo(int(x), int(y), duration=0.25)
            return {"ok": True, "output": f"الفأرة → ({x},{y})", "summary": f"move {x},{y}"}
        if action == "click":
            if x is None or y is None:
                return {"ok": False, "error": "click يتطلب x و y (أو استخدم locate بصورة أولًا)", "summary": "إحداثيات ناقصة"}
            pyautogui.click(int(x), int(y), clicks=int(clicks or 1), button=button or "left")
            return {"ok": True, "output": f"نُقر ({x},{y}) زر {button}x{clicks}", "summary": f"click {x},{y}"}
        if action == "type":
            pyautogui.write(text or "", interval=0.02)
            return {"ok": True, "output": f"كُتب {len(text or '')} حرفًا", "summary": "desktop type"}
        if action == "press":
            pyautogui.press(key or "enter")
            return {"ok": True, "output": f"ضُغط {key}", "summary": f"press {key}"}
        if action == "hotkey":
            keys = [k.strip() for k in (key or "").split("+") if k.strip()]
            if not keys:
                return {"ok": False, "error": "hotkey يتطلب key مثل: ctrl+s", "summary": "مفتاح ناقص"}
            pyautogui.hotkey(*keys)
            return {"ok": True, "output": f"ضُغط {'+'.join(keys)}", "summary": f"hotkey {key}"}
        if action == "scroll":
            pyautogui.scroll(int(amount))
            return {"ok": True, "output": f"تمرير {amount}", "summary": "scroll"}
        if action == "locate":
            if not path or not os.path.exists(path):
                return {"ok": False, "error": "locate يتطلب path لصورة موجودة", "summary": "صورة ناقصة"}
            box = pyautogui.locateOnScreen(path, confidence=float(confidence or 0.85))
            if not box:
                return {"ok": False, "error": "الصورة غير ظاهرة على الشاشة", "summary": "locate: لا تطابق"}
            cx, cy = pyautogui.center(box)
            return {"ok": True, "output": f"وُجدت في ({cx},{cy}) — نفّذ click بهما للتأكيد",
                    "summary": f"locate {cx},{cy}"}
        if action == "windows":
            try:
                titles = pyautogui.getAllTitles() if hasattr(pyautogui, "getAllTitles") else []
                titles = [t for t in titles if t][:30]
                return {"ok": True, "output": "\n".join(titles) or "لا نوافذ مرئية", "summary": f"{len(titles)} نافذة"}
            except Exception as e:
                return {"ok": False, "error": str(e)[:200], "summary": "windows فشل"}
        return {"ok": False, "error": f"إجراء غير معروف: {action} (status/size/screenshot/move/click/type/press/hotkey/scroll/locate/windows)",
                "summary": "إجراء خاطئ"}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {str(e)[:300]} (للطوارئ: الفأرة للزاوية العلوية)",
                "summary": f"desktop:{action} فشل"}
