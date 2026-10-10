"""Agent loop: understand -> plan -> execute (parallel) -> verify -> report."""
from __future__ import annotations
import json, re, os
from dataclasses import dataclass
from .config import SConfig
from . import tools
from .providers import SYSTEM, chat_openai_compat, local_plan, local_summarize

TOOL_RE = re.compile(r"```tool:\s*(\{.*?\})\s*```", re.S)

def parse_tool_calls(text: str) -> list:
    calls = []
    for m in TOOL_RE.finditer(text or ""):
        try:
            d = json.loads(m.group(1))
            if "tool" in d: calls.append(d)
        except Exception: pass
    # Fallback: single JSON lines
    for ln in (text or "").splitlines():
        ln = ln.strip()
        if ln.startswith('{"tool"'):
            try:
                d = json.loads(ln); calls.append(d)
            except Exception: pass
    # Deduplicate
    seen, uniq = set(), []
    for c in calls:
        k = json.dumps(c, sort_keys=True, ensure_ascii=False)
        if k not in seen: seen.add(k); uniq.append(c)
    return uniq[:8]

@dataclass
class AgentResult:
    text: str
    observations: list
    steps: int

class Agent:
    def __init__(self, cfg: SConfig, cwd: str = ".", confirm_fn=None):
        self.cfg = cfg
        self.cwd = cwd or "."
        self.confirm_fn = confirm_fn or (lambda msg: True)
        self.history = []

    def _llm(self, task: str, obs_text: str) -> str:
        msgs = [{"role": "system", "content": SYSTEM + "\nTools:\n" + tools.describe_tools()},
                {"role": "user", "content": f"Task: {task}\nObservations so far:\n{obs_text[-3000:]}\nExecute the next step with tools."}]
        try:
            if self.cfg.provider == "local" or not self.cfg.endpoint():
                raise RuntimeError("local")
            return chat_openai_compat(self.cfg, msgs, timeout=self.cfg.timeout)
        except Exception:
            return ""  # falls back to the local planner

    def run(self, task: str, verbose: bool = True) -> AgentResult:
        obs, steps = [], 0
        plan = local_plan(task, self.cwd)
        # Merge LLM output when available, otherwise rely on local (faster, offline)
        llm_text = self._llm(task, "")
        llm_calls = parse_tool_calls(llm_text)
        queue = (llm_calls or []) + plan
        if verbose and llm_text:
            print(llm_text[:1500])

        for _ in range(self.cfg.max_steps):
            if not queue: break
            batch, queue = queue[:4], queue[4:]  # parallel batches = speed
            # Safe-mode confirmation for writing/executing
            allowed = []
            for c in batch:
                t, a = c.get("tool",""), c.get("args",{})
                if t in ("write", "edit", "patch", "bash", "browser", "desktop") and self.cfg.safe_mode:
                    if not self.confirm_fn(f"Run {t} {str(a)[:100]}? [y/N] "):
                        obs.append({"tool": t, "ok": False, "summary": "Rejected by user"})
                        continue
                allowed.append(c)
            if not allowed: continue
            results = tools.run_batch(allowed, cwd=self.cwd, parallel=True)
            obs.extend(results); steps += 1
            if verbose:
                for r in results:
                    mark = "✓" if r.get("ok") else "✗"
                    print(f"  {mark} {r.get('tool')}: {r.get('summary','')} {str(r.get('error',''))[:120]}")
            # Follow-up: ask the LLM for the next step when available
            if self.cfg.provider != "local" and self.cfg.endpoint():
                txt = "\n".join(f"[{r.get('tool')}] ok={r.get('ok')} {str(r.get('summary',r.get('error','')))[:300]}" for r in results)
                nxt = self._llm(task, "\n".join(o.get("tool","")+str(o.get("summary","")) for o in obs))
                nc = parse_tool_calls(nxt)
                if nc: queue += nc
                if verbose and nxt: print(nxt[:800])
                if not nc and not queue: break
            else:
                # Local: summarize right after the first exploration (2 steps max for speed)
                if steps >= 2: break
        summary = local_summarize(task, obs)
        if self.cfg.provider != "local" and self.cfg.endpoint() and llm_text:
            summary = summary  # keep the unified structured report
        return AgentResult(text=summary, observations=obs, steps=steps)
