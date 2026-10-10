"""تحكم حقيقي بالمتصفح عبر Playwright — Firefox أولًا (مثل alphacode)، ثم Chromium.

تثبيت:
  pip install playwright
  python -m playwright install firefox   (أو chromium)
يعمل بدونه أيضًا: status يخبرك بما ينقصك.
"""
from __future__ import annotations
import os

_PW = None
_LAUNCH_ERR = ""
_BROWSER = None
_PAGE = None

def ensure():
    """(ok, msg) — فحص توفر playwright والمتصفح."""
    global _PW, _LAUNCH_ERR
    try:
        from playwright.sync_api import sync_playwright  # noqa
        _PW = sync_playwright
        return True, "playwright مثبت"
    except ImportError:
        return False, "playwright غير مثبت — نفّذ: pip install playwright && python -m playwright install firefox"

def _page(browser: str = "firefox", headless: bool = True, timeout: int = 30000):
    global _BROWSER, _PAGE, _PW, _LAUNCH_ERR
    ok, msg = ensure()
    if not ok:
        raise RuntimeError(msg)
    if _PAGE is not None:
        try:
            _ = _PAGE.url  # اختبار حيوية
            return _PAGE
        except Exception:
            _PAGE, _BROWSER = None, None
    pw = _PW().start()
    _PW_CTX = pw
    try:
        btype = getattr(pw, browser if browser in ("firefox", "chromium", "webkit") else "firefox")
        _BROWSER = btype.launch(headless=headless)
    except Exception as e:
        _LAUNCH_ERR = str(e)[:300]
        # محاولة أخيرة: chromium إن فشل firefox (غير مثبت)
        if browser != "chromium":
            try:
                _BROWSER = pw.chromium.launch(headless=headless)
            except Exception as e2:
                pw.stop()
                raise RuntimeError(f"تعذر إطلاق المتصفح: {e2}. نفّذ: python -m playwright install firefox")
        else:
            pw.stop()
            raise
    _PAGE = _BROWSER.new_page()
    _PAGE.set_default_timeout(timeout)
    _PAGE._pw_ctx = _PW_CTX
    return _PAGE

def t_browser(action: str = "status", url: str = "", selector: str = "",
              text: str = "", key: str = "", path: str = "",
              browser: str = "firefox", headless: bool = True,
              timeout: int = 30000) -> dict:
    """أداة المتصفح: status|open|text|click|fill|type|press|screenshot|close."""
    ok, msg = ensure()
    if action == "status":
        if not ok:
            return {"ok": False, "output": msg, "summary": "المتصفح غير جاهز"}
        # فحص وجود المتصفح فعليًا بمحاولة إطلاق سريعة headless
        try:
            pg = _page(browser=browser, headless=True, timeout=10000)
            u = pg.url or "about:blank"
            return {"ok": True, "output": f"جاهز ({browser}) — الصفحة: {u}", "summary": f"browser:{browser} جاهز"}
        except Exception as e:
            return {"ok": False, "output": str(e)[:400], "summary": "المتصفح ناقص"}
    try:
        pg = _page(browser=browser, headless=headless, timeout=timeout)
    except Exception as e:
        return {"ok": False, "error": str(e)[:400], "summary": "فشل الإطلاق"}
    try:
        if action in ("open", "goto"):
            pg.goto(url, wait_until="domcontentloaded")
            return {"ok": True, "output": f"فُتح {url} — العنوان: {pg.title()[:150]}",
                    "summary": f"open {url[:60]}"}
        if action in ("text", "snapshot"):
            try:
                body = pg.inner_text("body")[:6000]
            except Exception:
                body = pg.content()[:6000]
            return {"ok": True, "output": f"[{pg.url}]\n{body}", "summary": f"text {pg.url[:60]}"}
        if action == "click":
            pg.click(selector, timeout=timeout)
            return {"ok": True, "output": f"نُقر {selector}", "summary": f"click {selector[:60]}"}
        if action in ("fill", "type"):
            if action == "fill":
                pg.fill(selector, text, timeout=timeout)
            else:
                pg.click(selector, timeout=timeout)
                pg.keyboard.type(text)
            return {"ok": True, "output": f"أُدخل نص ({len(text)} حرفًا) في {selector}", "summary": f"{action} {selector[:50]}"}
        if action == "press":
            if selector:
                pg.press(selector, key or "Enter", timeout=timeout)
            else:
                pg.keyboard.press(key or "Enter")
            return {"ok": True, "output": f"ضُغط {key}", "summary": f"press {key}"}
        if action == "screenshot":
            out = path or os.path.join(os.path.expanduser("~"), "s_agent_shot.png")
            pg.screenshot(path=out, full_page=False)
            return {"ok": True, "output": f"حُفظت اللقطة: {out}", "summary": "screenshot"}
        if action == "close":
            close()
            return {"ok": True, "output": "أُغلق المتصفح", "summary": "close"}
        return {"ok": False, "error": f"إجراء غير معروف: {action} (status/open/text/click/fill/type/press/screenshot/close)",
                "summary": "إجراء خاطئ"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:400], "summary": f"browser:{action} فشل"}

def close():
    global _BROWSER, _PAGE
    try:
        if _PAGE is not None:
            ctx = getattr(_PAGE, "_pw_ctx", None)
            try: _PAGE.close()
            except Exception: pass
            _PAGE = None
            if ctx is not None:
                try: ctx.stop()
                except Exception: pass
        if _BROWSER is not None:
            try: _BROWSER.close()
            except Exception: pass
            _BROWSER = None
    except Exception:
        _BROWSER, _PAGE = None, None
