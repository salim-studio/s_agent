"""اختبارات خفيفة وسريعة لـ s_agent."""
import os, tempfile
from s_agent import tools
from s_agent.agent import parse_tool_calls
from s_agent.providers import local_plan

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
    assert isinstance(local_plan("اشرح المشروع", "."), list)

def test_browser_desktop_registered_and_safe():
    assert "browser" in tools.REGISTRY and "desktop" in tools.REGISTRY
    # التوجيه المحلي: مهمة متصفح/سطح مكتب → الأداة الصحيحة (بدون تنفيذ فعلي)
    b = local_plan("افتح المتصفح https://example.com ولخصه", ".")
    assert b and b[0]["tool"] == "browser" and b[0]["args"].get("url") == "https://example.com"
    d = local_plan("خذ لقطة شاشة لسطح المكتب", ".")
    assert d and d[0]["tool"] == "desktop"
    # status يعمل دائمًا (يُرجع جاهزًا أو تعليمات التثبيت — لا يكسر أبدًا)
    rb = tools.run_tool("browser", {"action": "status"})
    assert set(("ok", "summary")) <= set(rb)
    rd = tools.run_tool("desktop", {"action": "status"})
    assert set(("ok", "summary")) <= set(rd)
    # desktop يرفض النقر بلا إحداثيات (أمان) — سواء مثبت أم لا
    rc = tools.run_tool("desktop", {"action": "click"})
    assert rc["ok"] is False
