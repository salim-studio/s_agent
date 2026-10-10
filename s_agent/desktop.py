"""Desktop control via PyAutoGUI.

Install:
  pip install pyautogui pillow
Safety: FAILSAFE is on — move the mouse to the top-left corner for an instant stop.
Clicks need explicit coordinates or an image. No blind guessing.
"""
from __future__ import annotations
import os, time

def ensure():
    try:
        import pyautogui  # noqa
        return True, "pyautogui installed"
    except ImportError:
        return False, "pyautogui not installed — run: pip install pyautogui pillow"

def t_desktop(action: str = "status", x: int = None, y: int = None,
              text: str = "", key: str = "", path: str = "",
              button: str = "left", clicks: int = 1, amount: int = 200,
              confidence: float = 0.85) -> dict:
    """Desktop tool: status|size|screenshot|move|click|type|press|hotkey|scroll|locate|windows."""
    ok, msg = ensure()
    if action == "status":
        if not ok:
            return {"ok": False, "output": msg, "summary": "Desktop not ready"}
        import pyautogui
        w, h = pyautogui.size()
        px, py = pyautogui.position()
        return {"ok": True, "output": f"Ready — screen {w}x{h} — mouse ({px},{py}) — FAILSAFE on",
                "summary": f"desktop {w}x{h}"}
    if not ok:
        return {"ok": False, "error": msg, "summary": "pyautogui missing"}
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
            return {"ok": True, "output": f"Saved: {out} ({dt:.1f}s)", "summary": "desktop screenshot"}
        if action == "move":
            if x is None or y is None:
                return {"ok": False, "error": "move needs x and y", "summary": "Missing coordinates"}
            pyautogui.moveTo(int(x), int(y), duration=0.25)
            return {"ok": True, "output": f"Mouse -> ({x},{y})", "summary": f"move {x},{y}"}
        if action == "click":
            if x is None or y is None:
                return {"ok": False, "error": "click needs x and y (or use locate with an image first)", "summary": "Missing coordinates"}
            pyautogui.click(int(x), int(y), clicks=int(clicks or 1), button=button or "left")
            return {"ok": True, "output": f"Clicked ({x},{y}) button {button}x{clicks}", "summary": f"click {x},{y}"}
        if action == "type":
            pyautogui.write(text or "", interval=0.02)
            return {"ok": True, "output": f"Typed {len(text or '')} char(s)", "summary": "desktop type"}
        if action == "press":
            pyautogui.press(key or "enter")
            return {"ok": True, "output": f"Pressed {key}", "summary": f"press {key}"}
        if action == "hotkey":
            keys = [k.strip() for k in (key or "").split("+") if k.strip()]
            if not keys:
                return {"ok": False, "error": "hotkey needs key, e.g. ctrl+s", "summary": "Missing key"}
            pyautogui.hotkey(*keys)
            return {"ok": True, "output": f"Pressed {'+'.join(keys)}", "summary": f"hotkey {key}"}
        if action == "scroll":
            pyautogui.scroll(int(amount))
            return {"ok": True, "output": f"Scrolled {amount}", "summary": "scroll"}
        if action == "locate":
            if not path or not os.path.exists(path):
                return {"ok": False, "error": "locate needs path to an existing image", "summary": "Missing image"}
            box = pyautogui.locateOnScreen(path, confidence=float(confidence or 0.85))
            if not box:
                return {"ok": False, "error": "Image not visible on screen", "summary": "locate: no match"}
            cx, cy = pyautogui.center(box)
            return {"ok": True, "output": f"Found at ({cx},{cy}) — run click with them to confirm",
                    "summary": f"locate {cx},{cy}"}
        if action == "windows":
            try:
                titles = pyautogui.getAllTitles() if hasattr(pyautogui, "getAllTitles") else []
                titles = [t for t in titles if t][:30]
                return {"ok": True, "output": "\n".join(titles) or "No visible windows", "summary": f"{len(titles)} window(s)"}
            except Exception as e:
                return {"ok": False, "error": str(e)[:200], "summary": "windows failed"}
        return {"ok": False, "error": f"Unknown action: {action} (status/size/screenshot/move/click/type/press/hotkey/scroll/locate/windows)",
                "summary": "Bad action"}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {str(e)[:300]} (emergency: move mouse to top-left corner)",
                "summary": f"desktop:{action} failed"}
