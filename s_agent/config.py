"""Settings and providers — fast and lightweight (JSON only)."""
from __future__ import annotations
import json, os
from dataclasses import dataclass, field, asdict

APP = "s_agent"

PROVIDERS = {
    "local":   {"base_url": "", "model": "local-heuristic", "needs_key": False,
                "note": "Works offline with no API key — fast local engine"},
    "openai":  {"base_url": "https://api.openai.com/v1", "model": "gpt-4o-mini", "needs_key": True, "env": "OPENAI_API_KEY"},
    "anthropic": {"base_url": "https://api.anthropic.com/v1", "model": "", "needs_key": True, "env": "ANTHROPIC_API_KEY", "note": "Requires an OpenAI-compatible gateway"},
    "gemini":  {"base_url": "https://generativelanguage.googleapis.com/v1beta/openai", "model": "gemini-2.0-flash", "needs_key": True, "env": "GEMINI_API_KEY"},
    "deepseek": {"base_url": "https://api.deepseek.com/v1", "model": "deepseek-chat", "needs_key": True, "env": "DEEPSEEK_API_KEY"},
    "openrouter": {"base_url": "https://openrouter.ai/api/v1", "model": "openrouter/auto", "needs_key": True, "env": "OPENROUTER_API_KEY"},
    "ollama":  {"base_url": "http://localhost:11434/v1", "model": "qwen2.5-coder:7b", "needs_key": False},
    "lmstudio": {"base_url": "http://localhost:1234/v1", "model": "local-model", "needs_key": False},
    "custom":  {"base_url": "", "model": "", "needs_key": True},
}

@dataclass
class SConfig:
    provider: str = "local"
    model: str = "local-heuristic"
    api_key: str = ""
    base_url: str = ""
    language: str = "en"
    safe_mode: bool = True
    max_steps: int = 12
    timeout: int = 60
    extra: dict = field(default_factory=dict)

    def endpoint(self) -> str:
        base = self.base_url or PROVIDERS.get(self.provider, {}).get("base_url", "")
        return (base.rstrip("/") + "/chat/completions") if base else ""

def _cfg_dir() -> str:
    if os.name == "nt":
        root = os.environ.get("APPDATA") or os.path.expanduser("~")
        return os.path.join(root, APP)
    return os.path.join(os.path.expanduser("~"), ".config", APP)

def _data_dir() -> str:
    if os.name == "nt":
        root = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        return os.path.join(root, APP)
    return os.path.join(os.path.expanduser("~"), ".local", "share", APP)

def cfg_path() -> str:
    return os.path.join(_cfg_dir(), "config.json")

def load_config() -> SConfig:
    p = cfg_path()
    c = SConfig()
    if os.path.exists(p):
        try:
            d = json.load(open(p, encoding="utf-8"))
            for k, v in d.items():
                if hasattr(c, k):
                    setattr(c, k, v)
        except Exception:
            pass
    # env keys auto-pickup
    prov = PROVIDERS.get(c.provider, {})
    env = prov.get("env", "")
    if not c.api_key and env and os.environ.get(env):
        c.api_key = os.environ[env]
    if not c.base_url:
        c.base_url = prov.get("base_url", "")
    if not c.model:
        c.model = prov.get("model", "")
    return c

def save_config(c: SConfig) -> str:
    p = cfg_path()
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(asdict(c), open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return p

def sessions_dir() -> str:
    d = os.path.join(_data_dir(), "sessions")
    os.makedirs(d, exist_ok=True)
    return d
