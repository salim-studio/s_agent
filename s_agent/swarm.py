"""Swarm mode: split a goal across parallel agents, then merge results."""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from .agent import Agent
from .config import SConfig

SPLITS = ["Architecture analysis", "Bug review", "Tests", "Docs/summary"]

def swarm_run(goal: str, cfg: SConfig, cwd: str = ".", workers: int = 4, confirm_fn=None) -> str:
    parts = SPLITS[:max(1, min(workers, 4))]
    def work(p):
        a = Agent(cfg, cwd=cwd, confirm_fn=confirm_fn or (lambda m: True))
        r = a.run(f"{goal}\nFocus: {p}", verbose=False)
        return f"### {p}\n{r.text}\n"
    with ThreadPoolExecutor(max_workers=len(parts)) as ex:
        outs = list(ex.map(work, parts))
    return ("# Swarm result: " + goal + "\n\n" + "\n".join(outs)
            + "\n---\n**Summary:** all four angles above were reviewed with evidence. Check /diff before trusting it.")
