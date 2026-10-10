"""s_agent command line — multilingual (en/ar/fr/es), English default."""
from __future__ import annotations
import argparse, os, sys, getpass
from .config import load_config, save_config, PROVIDERS, cfg_path
from .agent import Agent
from .swarm import swarm_run
from . import tools, session
from .i18n import t, set_lang, LANGS

VERSION = "1.2.0"

LOGO = r"""
  ____     _____   ____ _____ _   _
 / ___|   |_   _| / ___| ____| \ | |_
 \___ \  _  | |  | |  _|  _| |  \| __|
  ___) || |_| |  | |_| | |___| |\  |_
 |____/  \__, |   \____|_____|_| \_(_)
         |___/
"""

def banner() -> str:
    return LOGO + " " + t("tagline", ver=VERSION)

YES = {"y", "yes", "نعم", "ن", "oui", "o", "sí", "si", "s"}

def _confirm(msg: str) -> bool:
    try:
        return input(msg).strip().lower() in YES
    except EOFError:
        return False

def cmd_doctor(_):
    import shutil
    print(t("doc_title"))
    print(t("doc_py", v=sys.version.split()[0], plat=os.name))
    print(t("doc_cfg", p=cfg_path()))
    c = load_config()
    print(t("doc_pm", p=c.provider, m=c.model, e=c.endpoint() or "(local)"))
    has_key = bool(c.api_key or os.environ.get((PROVIDERS.get(c.provider, {}).get("env", "") or "")))
    print(t("doc_key_yes") if has_key else t("doc_key_no"))
    for b in ("git", "python"):
        print(f"{b}: {'OK' if shutil.which(b) else 'MISSING'}")
    print(t("doc_tools", n=len(tools.REGISTRY), names=", ".join(tools.REGISTRY)))
    try:
        from .browser_pw import ensure as _be
        ok, msg = _be()
        print(t("doc_brow", s=t("st_ready", m=msg) if ok else t("st_missing", m=msg)))
    except Exception as e:
        print(t("doc_brow", s=t("st_error", e=e)))
    try:
        from .desktop import ensure as _de
        ok, msg = _de()
        print(t("doc_desk", s=t("st_ready", m=msg) if ok else t("st_missing", m=msg)))
    except Exception as e:
        print(t("doc_desk", s=t("st_error", e=e)))
    print(t("doc_ok"))

def cmd_run(a):
    cfg = load_config()
    set_lang(cfg.language)
    auto_yes = getattr(a, "yes", False)
    ag = Agent(cfg, cwd=getattr(a, "cwd", ".") or ".",
               confirm_fn=(lambda m: True) if auto_yes else _confirm)
    sid = session.new_id()
    r = ag.run(a.task)
    session.save_turn(sid, "user", a.task)
    session.save_turn(sid, "agent", r.text)
    print("\n" + r.text)
    print("\n" + t("run_report", sid=sid, n=r.steps))

def cmd_swarm(a):
    cfg = load_config()
    set_lang(cfg.language)
    out = swarm_run(a.goal, cfg, cwd=getattr(a, "cwd", ".") or ".",
                    workers=getattr(a, "workers", 4),
                    confirm_fn=(lambda m: True) if getattr(a, "yes", False) else _confirm)
    print(out)

def cmd_login(a):
    cfg = load_config()
    print(t("p_providers"), ", ".join(PROVIDERS))
    p = (getattr(a, "provider", "") or input(t("p_provider", cur=cfg.provider)).strip() or cfg.provider)
    if p not in PROVIDERS:
        print(t("p_unknown")); p = "local"
    info = PROVIDERS[p]
    key = ""
    if info.get("needs_key"):
        env = info.get("env", "")
        hint = t("p_key_hint", env=env) if env else ""
        key = getpass.getpass(t("p_key", p=p, hint=hint)).strip()
    base = input(t("p_base", cur=info.get("base_url", ""))).strip() or info.get("base_url", "")
    model = input(t("p_model", cur=info.get("model", ""))).strip() or info.get("model", "")
    cfg.provider, cfg.api_key, cfg.base_url, cfg.model = p, key, base, model
    print(t("p_saved"), save_config(cfg))

def cmd_lang(a):
    cfg = load_config()
    code = (getattr(a, "code", "") or "").lower()
    if not code:
        print(t("lang_cur", name=LANGS.get(cfg.language, cfg.language),
                langs=", ".join(f"{k} ({v})" for k, v in LANGS.items())))
        return
    if code not in LANGS:
        print(t("lang_unknown", x=code, langs=", ".join(LANGS)))
        return
    cfg.language = code
    save_config(cfg)
    set_lang(code)
    print(t("lang_set", name=LANGS[code]))

def cmd_browser(a):
    kw = dict(action=getattr(a, "action", "status"), url=getattr(a, "url", "") or "",
              selector=getattr(a, "selector", "") or "", text=getattr(a, "text", "") or "",
              key=getattr(a, "key", "") or "", path=getattr(a, "path", "") or "",
              browser=getattr(a, "browser", "firefox") or "firefox")
    if getattr(a, "headed", False): kw["headless"] = False
    r = tools.run_tool("browser", kw)
    print(("OK " if r.get("ok") else "FAIL ") + str(r.get("output") or r.get("error"))[:2000])

def cmd_desktop(a):
    kw = dict(action=getattr(a, "action", "status"), text=getattr(a, "text", "") or "",
              key=getattr(a, "key", "") or "", path=getattr(a, "path", "") or "",
              button=getattr(a, "button", "left") or "left")
    for k in ("x", "y", "clicks", "amount"):
        v = getattr(a, k, None)
        if v is not None: kw[k] = v
    r = tools.run_tool("desktop", kw)
    print(("OK " if r.get("ok") else "FAIL ") + str(r.get("output") or r.get("error"))[:2000])

def repl():
    cfg = load_config()
    set_lang(cfg.language)
    print(banner())
    print(t("prov_line", p=cfg.provider, m=cfg.model,
            s=t("on") if cfg.safe_mode else t("off")))
    print(t("hint"))
    sid = session.new_id()
    ag = Agent(cfg, cwd=".", confirm_fn=_confirm)
    while True:
        try: line = input("\ns_agent> ").strip()
        except (EOFError, KeyboardInterrupt): print("\n" + t("sess_saved", sid=sid)); break
        if not line: continue
        if line in ("/exit", "exit", "quit"): print(t("sess_saved", sid=sid)); break
        if line in ("help", "/help"):
            print(t("help1"))
            print(t("help2"))
            continue
        if line.startswith("/swarm "):
            print(swarm_run(line[7:], load_config(), confirm_fn=_confirm)); continue
        if line == "/lang" or line.startswith("/lang "):
            code = line[5:].strip()
            cmd_lang(argparse.Namespace(code=code))
            ag.cfg = load_config()
            continue
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
        ag.cfg = load_config()  # pick up any config change
        set_lang(ag.cfg.language)
        r = ag.run(line)
        session.save_turn(sid, "agent", r.text)
        print("\n" + r.text)

def main(argv=None):
    cfg = load_config()
    set_lang(cfg.language)
    ap = argparse.ArgumentParser(prog="s_agent", description="s_agent — fast coding agent for your terminal")
    ap.add_argument("--version", action="store_true")
    ap.add_argument("--lang", default="", help="UI language: en, ar, fr, es")
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("run", help="Run a single task"); p.add_argument("task"); p.add_argument("--cwd", default="."); p.add_argument("--yes", action="store_true"); p.set_defaults(fn=cmd_run)
    p = sub.add_parser("swarm", help="Swarm mode"); p.add_argument("goal"); p.add_argument("--cwd", default="."); p.add_argument("--workers", type=int, default=4); p.add_argument("--yes", action="store_true"); p.set_defaults(fn=cmd_swarm)
    p = sub.add_parser("doctor", help="Health check"); p.set_defaults(fn=cmd_doctor)
    p = sub.add_parser("login", help="Connect a provider"); p.add_argument("--provider", default=""); p.set_defaults(fn=cmd_login)
    p = sub.add_parser("lang", help="Show or set UI language (en, ar, fr, es)"); p.add_argument("code", nargs="?", default=""); p.set_defaults(fn=cmd_lang)
    p = sub.add_parser("sessions", help="List sessions"); p.set_defaults(fn=lambda a: [print("-", s["id"]) for s in session.list_sessions()] or print(t("no_sessions")))
    b = sub.add_parser("browser", help="Real browser (playwright)")
    b.add_argument("action", default="status", nargs="?", help="status|open|text|click|fill|type|press|screenshot|close");
    b.add_argument("--url", default=""); b.add_argument("--selector", default=""); b.add_argument("--text", default="")
    b.add_argument("--key", default=""); b.add_argument("--path", default=""); b.add_argument("--browser", default="firefox")
    b.add_argument("--headed", action="store_true", help="Visible window instead of headless"); b.set_defaults(fn=cmd_browser)
    d = sub.add_parser("desktop", help="Desktop control (pyautogui)")
    d.add_argument("action", default="status", nargs="?", help="status|size|screenshot|move|click|type|press|hotkey|scroll|locate|windows")
    d.add_argument("--x", type=int, default=None); d.add_argument("--y", type=int, default=None)
    d.add_argument("--text", default=""); d.add_argument("--key", default=""); d.add_argument("--path", default="")
    d.add_argument("--button", default="left"); d.add_argument("--clicks", type=int, default=None); d.add_argument("--amount", type=int, default=None)
    d.set_defaults(fn=cmd_desktop)
    a = ap.parse_args(argv)
    if a.lang:
        cmd_lang(argparse.Namespace(code=a.lang))
        return
    if a.version: print(VERSION); return
    if not getattr(a, "cmd", None): repl(); return
    a.fn(a)

if __name__ == "__main__":
    main()
