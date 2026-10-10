"""Swarm mode: split a goal across parallel agents, then merge results."""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from .agent import Agent
from .config import SConfig
from .i18n import t

def swarm_run(goal: str, cfg: SConfig, cwd: str = ".", workers: int = 4, confirm_fn=None) -> str:
    parts = [t("sw_s1"), t("sw_s2"), t("sw_s3"), t("sw_s4")][:max(1, min(workers, 4))]
    def work(p):
        a = Agent(cfg, cwd=cwd, confirm_fn=confirm_fn or (lambda m: True))
        r = a.run(f"{goal}\n{t('sw_focus', p=p)}", verbose=False)
        return f"### {p}\n{r.text}\n"
    with ThreadPoolExecutor(max_workers=len(parts)) as ex:
        outs = list(ex.map(work, parts))
    return (t("sw_title", goal=goal) + "\n\n" + "\n".join(outs)
            + "\n---\n" + t("sw_tail"))
