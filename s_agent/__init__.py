"""s_agent — a fast, hands-on coding agent for your terminal (stdlib core)."""
from .agent import Agent, AgentResult
from .config import load_config, SConfig
from .i18n import t, set_lang, LANGS

__version__ = "1.2.0"
__all__ = ["Agent", "AgentResult", "load_config", "SConfig", "t", "set_lang", "LANGS"]
