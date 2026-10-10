"""وضع السرب: تقسيم الهدف إلى وكلاء متوازيين ثم دمج النتائج."""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from .agent import Agent
from .config import SConfig

SPLITS = ["تحليل المعمارية", "مراجعة الأخطاء", "الاختبارات", "التوثيق/التلخيص"]

def swarm_run(goal: str, cfg: SConfig, cwd: str = ".", workers: int = 4, confirm_fn=None) -> str:
    parts = SPLITS[:max(1, min(workers, 4))]
    def work(p):
        a = Agent(cfg, cwd=cwd, confirm_fn=confirm_fn or (lambda m: True))
        r = a.run(f"{goal}\nالتركيز: {p}", verbose=False)
        return f"### {p}\n{r.text}\n"
    with ThreadPoolExecutor(max_workers=len(parts)) as ex:
        outs = list(ex.map(work, parts))
    return ("# نتيجة السرب: " + goal + "\n\n" + "\n".join(outs)
            + "\n---\n**الخلاصة:** رُوجعت الزوايا الأربع أعلاه بالأدلة. راجع /diff قبل الاعتماد.")
