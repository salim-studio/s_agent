"""s_agent — a fast, hands-on coding agent for your terminal (stdlib core)."""
from .agent import Agent, AgentResult
from .config import load_config, SConfig

__version__ = "1.1.0"
__all__ = ["Agent", "AgentResult", "load_config", "SConfig"]
