"""واجهة الأوامر s_agent — عربية، سريعة، stdlib فقط."""
from __future__ import annotations
import argparse, os, sys, getpass
from .config import load_config, save_config, PROVIDERS, cfg_path
from .agent import Agent
from .swarm import swarm_run
from . import tools, session

VERSION = "1.0.0"

def _confirm(msg: str) -> bool:
    try:
        return input(msg).strip().lower() in ("y", "نعم", "yes", "ن")
    except EOFError:
        return False

def cmd_doctor(_):
    import shutil
    print("== فحص s_agent ==")
    print(f"Python: {sys.version.split()[0]}  | المنصة: {os.name}")
    print(f"الإعدادات: {cfg_path()}")
    c = load_config()
    print(f"المزوّد: {c.provider} | النموذج: {c.model} | endpoint: {c.endpoint() or '(محلي)'}")
    print(f"مفتاح API: {'موجود' if c.api_key or os.environ.get((PROVIDERS.get(c.provider,{}).get('env','') or '')) else 'غير مضبوط (سيعمل المحلي)'}" )
    for b in ("git", "python"):
        print(f"{b}: {'✓' if shutil.which(b) else '✗'}")
    print("الأدوات:", len(tools.REGISTRY), "أداة —", ", ".join(tools.REGISTRY))
    try:
        from .browser_pw import ensure as _be
        ok, msg = _be()
        print(f"المتصفح (playwright): {'✓ ' + msg if ok else '✗ ' + msg}")
    except Exception as e:
        print(f"المتصفح (playwright): ✗ {e}")
    try:
        from .desktop import ensure as _de
        ok, msg = _de()
        print(f"سطح المكتب (pyautogui): {'✓ ' + msg if ok else '✗ ' + msg}")
    except Exception as e:
        print(f"سطح المكتب (pyautogui): ✗ {e}")
    print("الحالة: سليم ✓")

def cmd_browser(a):
    kw = dict(action=getattr(a, "action", "status"), url=getattr(a, "url", "") or "",
              selector=getattr(a, "selector", "") or "", text=getattr(a, "text", "") or "",
              key=getattr(a, "key", "") or "", path=getattr(a, "path", "") or "",
              browser=getattr(a, "browser", "firefox") or "firefox")
    if getattr(a, "headed", False): kw["headless"] = False
    r = tools.run_tool("browser", kw)
    print(("✓ " if r.get("ok") else "✗ ") + str(r.get("output") or r.get("error"))[:2000])

def cmd_desktop(a):
    kw = dict(action=getattr(a, "action", "status"), text=getattr(a, "text", "") or "",
              key=getattr(a, "key", "") or "", path=getattr(a, "path", "") or "",
              button=getattr(a, "button", "left") or "left")
    for k in ("x", "y", "clicks", "amount"):
        v = getattr(a, k, None)
        if v is not None: kw[k] = v
    r = tools.run_tool("desktop", kw)
    print(("✓ " if r.get("ok") else "✗ ") + str(r.get("output") or r.get("error"))[:2000])

def cmd_run(a):
    cfg = load_config()
    auto_yes = getattr(a, "yes", False)
    ag = Agent(cfg, cwd=getattr(a, "cwd", ".") or ".",
               confirm_fn=(lambda m: True) if auto_yes else _confirm)
    sid = session.new_id()
    r = ag.run(a.task)
    session.save_turn(sid, "user", a.task)
    session.save_turn(sid, "agent", r.text)
    print("\n" + r.text)
    print(f"\n[الجلسة: {sid} | خطوات: {r.steps}]")

def cmd_swarm(a):
    cfg = load_config()
    out = swarm_run(a.goal, cfg, cwd=getattr(a, "cwd", ".") or ".",
                    workers=getattr(a, "workers", 4),
                    confirm_fn=(lambda m: True) if getattr(a, "yes", False) else _confirm)
    print(out)

def cmd_login(a):
    cfg = load_config()
    print("المزوّدون:", ", ".join(PROVIDERS))
    p = (getattr(a, "provider", "") or input(f"المزوّد [{cfg.provider}]: ").strip() or cfg.provider)
    if p not in PROVIDERS:
        print("مزود غير معروف، استُخدم local"); p = "local"
    info = PROVIDERS[p]
    key = ""
    if info.get("needs_key"):
        env = info.get("env", "")
        hint = f" (أو اضبط {env})" if env else ""
        key = getpass.getpass(f"مفتاح API لـ {p}{hint} (اتركه فارغًا للتخطي): ").strip()
    base = input(f"base_url [{info.get('base_url','')}]: ").strip() or info.get("base_url", "")
    model = input(f"النموذج [{info.get('model','')}]: ").strip() or info.get("model", "")
    cfg.provider, cfg.api_key, cfg.base_url, cfg.model = p, key, base, model
    print("حُفظ:", save_config(cfg))

def repl():
    cfg = load_config()
    print(f"s_agent v{VERSION} — اكتب مهمتك بالعربية (help/ للمساعدة، /exit للخروج)")
    print(f"المزوّد: {cfg.provider} | النموذج: {cfg.model} | الوضع الآمن: {'ON' if cfg.safe_mode else 'OFF'}")
    sid = session.new_id()
    ag = Agent(cfg, cwd=".", confirm_fn=_confirm)
    while True:
        try: line = input("\ns_agent> ").strip()
        except (EOFError, KeyboardInterrupt): print("\nحُفظت الجلسة:", sid); break
        if not line: continue
        if line in ("/exit", "exit", "خروج"): print("حُفظت الجلسة:", sid); break
        if line in ("help", "/help", "مساعدة"):
            print("/swarm <هدف> | /sessions | /diff | /doctor | /model")
            print("/browser open <url> | /browser shot | /desktop shot — تحكم حقيقي")
            continue
        if line.startswith("/swarm "):
            print(swarm_run(line[7:], load_config(), confirm_fn=_confirm)); continue
        if line.startswith("/browser"):
            rest = line[len("/browser"):].strip()
            if rest.startswith("open "):
                cmd_browser(argparse.Namespace(action="open", url=rest[5:].strip(), selector="", text="", key="", path="", browser="firefox", headed=False)); continue
            if rest in ("shot", "screenshot"):
                cmd_browser(argparse.Namespace(action="screenshot", url="", selector="", text="", key="", path="", browser="firefox", headed=False)); continue
            cmd_browser(argparse.Namespace(action="status", url="", selector="", text="", key="", path="", browser="firefox", headed=False)); continue
        if line.startswith("/desktop"):
            rest = line[len("/desktop"):].strip()
            if rest in ("shot", "screenshot"):
                cmd_desktop(argparse.Namespace(action="screenshot", text="", key="", path="", button="left", x=None, y=None, clicks=None, amount=None)); continue
            cmd_desktop(argparse.Namespace(action="status", text="", key="", path="", button="left", x=None, y=None, clicks=None, amount=None)); continue
        if line == "/sessions":
            for s in session.list_sessions(): print("-", s["id"], s["size"], "bytes")
            continue
        if line == "/diff": print(tools.t_diff()["output"]); continue
        if line == "/doctor": cmd_doctor(None); continue
        if line.startswith("/login") or line.startswith("/model"):
            cmd_login(argparse.Namespace(provider="")); continue
        session.save_turn(sid, "user", line)
        ag.cfg = load_config()  # التقط أي تغيير إعدادات
        r = ag.run(line)
        session.save_turn(sid, "agent", r.text)
        print("\n" + r.text)

def main(argv=None):
    ap = argparse.ArgumentParser(prog="s_agent", description="s_agent — وكيل برمجة عربي سريع")
    ap.add_argument("--version", action="store_true")
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("run", help="تنفيذ مهمة واحدة"); p.add_argument("task"); p.add_argument("--cwd", default="."); p.add_argument("--yes", action="store_true"); p.set_defaults(fn=cmd_run)
    p = sub.add_parser("swarm", help="وضع السرب"); p.add_argument("goal"); p.add_argument("--cwd", default="."); p.add_argument("--workers", type=int, default=4); p.add_argument("--yes", action="store_true"); p.set_defaults(fn=cmd_swarm)
    p = sub.add_parser("doctor", help="فحص"); p.set_defaults(fn=cmd_doctor)
    p = sub.add_parser("login", help="تسجيل مزود"); p.add_argument("--provider", default=""); p.set_defaults(fn=cmd_login)
    p = sub.add_parser("sessions", help="الجلسات"); p.set_defaults(fn=lambda a: [print("-", s["id"]) for s in session.list_sessions()] or print("لا جلسات"))
    b = sub.add_parser("browser", help="متصفح حقيقي (playwright)")
    b.add_argument("action", default="status", nargs="?", help="status|open|text|click|fill|type|press|screenshot|close");
    b.add_argument("--url", default=""); b.add_argument("--selector", default=""); b.add_argument("--text", default="")
    b.add_argument("--key", default=""); b.add_argument("--path", default=""); b.add_argument("--browser", default="firefox")
    b.add_argument("--headed", action="store_true", help="نافذة مرئية بدل headless"); b.set_defaults(fn=cmd_browser)
    d = sub.add_parser("desktop", help="سطح المكتب (pyautogui)")
    d.add_argument("action", default="status", nargs="?", help="status|size|screenshot|move|click|type|press|hotkey|scroll|locate|windows")
    d.add_argument("--x", type=int, default=None); d.add_argument("--y", type=int, default=None)
    d.add_argument("--text", default=""); d.add_argument("--key", default=""); d.add_argument("--path", default="")
    d.add_argument("--button", default="left"); d.add_argument("--clicks", type=int, default=None); d.add_argument("--amount", type=int, default=None)
    d.set_defaults(fn=cmd_desktop)
    a = ap.parse_args(argv)
    if a.version: print(VERSION); return
    if not getattr(a, "cmd", None): repl(); return
    a.fn(a)

if __name__ == "__main__":
    main()
