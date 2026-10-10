"""s_agent — وكيل برمجة طرفي سريع، عملي، متكامل (stdlib فقط)."""
from .agent import Agent, AgentResult
from .config import load_config, SConfig

__version__ = "1.0.0"
__all__ = ["Agent", "AgentResult", "load_config", "SConfig"]
