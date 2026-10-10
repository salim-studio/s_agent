"""Lightweight, fast tests for s_agent."""
import os, tempfile
from s_agent import tools
from s_agent.agent import parse_tool_calls
from s_agent.providers import local_plan, local_summarize
from s_agent.i18n import t, set_lang, LANGS

def test_tools_roundtrip():
    d = tempfile.mkdtemp()
    p = os.path.join(d, "a.txt")
    assert tools.t_write(p, "hello")["ok"]
    assert "hello" in tools.t_read(p)["output"]
    assert tools.t_edit(p, "hello", "hi")["ok"]
    assert tools.t_grep("hi", d)["ok"]
    assert tools.t_ls(d)["ok"]
    r = tools.t_bash("echo ok", cwd=d)
    assert r["ok"] and "ok" in r["output"]

def test_parse_and_plan():
    calls = parse_tool_calls('```tool:\n{"tool":"ls","args":{"path":"."}}\n```')
    assert calls and calls[0]["tool"] == "ls"
    assert isinstance(local_plan("explain this project", "."), list)

def test_browser_desktop_registered_and_safe():
    assert "browser" in tools.REGISTRY and "desktop" in tools.REGISTRY
    # Local routing: browser/desktop tasks -> the right tool (no real execution)
    b = local_plan("open https://example.com in the browser and summarize it", ".")
    assert b and b[0]["tool"] == "browser" and b[0]["args"].get("url") == "https://example.com"
    d = local_plan("take a desktop screenshot", ".")
    assert d and d[0]["tool"] == "desktop"
    # Bilingual: Arabic tasks still route correctly
    assert local_plan("افتح المتصفح https://example.com ولخصه", ".")[0]["tool"] == "browser"
    # status always works (ready or install hint — never crashes)
    rb = tools.run_tool("browser", {"action": "status"})
    assert set(("ok", "summary")) <= set(rb)
    rd = tools.run_tool("desktop", {"action": "status"})
    assert set(("ok", "summary")) <= set(rd)
    # desktop refuses clicks without coordinates (safety) — installed or not
    rc = tools.run_tool("desktop", {"action": "click"})
    assert rc["ok"] is False

def test_i18n_covers_all_languages():
    assert set(LANGS) == {"en", "ar", "fr", "es"}
    try:
        set_lang("fr")
        assert "élément" in tools.t_ls(".")["summary"]
        assert "Compris" in local_summarize("x", [])
        set_lang("ar")
        assert "عنصر" in tools.t_ls(".")["summary"] or "عنصرًا" in tools.t_ls(".")["summary"]
        assert "ما تم فهمه" in local_summarize("x", [])
        set_lang("es")
        assert "elemento" in tools.t_ls(".")["summary"]
        set_lang("xx")  # unknown -> English fallback
        assert "items in" in tools.t_ls(".")["summary"]
        assert t("no_such_key") == "no_such_key"
    finally:
        set_lang("en")
