"""AlgoExemple: the smallest possible algorithm, to show how the base works.

It contains NO set cover logic: it simply selects every subset. This is
always a valid cover when the instance is feasible, but never a good one.
Copy this file to start a new algorithm (see DOCUMENTATION.md, section 5).

Run it:
    python -m setcover solve -a example E.1
"""

from __future__ import annotations

from ..instance import Instance
from .base import Algorithm, RunContext, register


@register                       # 1. register the class -> usable as "-a example"
class AlgoExemple(Algorithm):   # 2. inherit from Algorithm
    name = "example"            # 3. identifier used on the command line / in the CSV
    exact = False               # 4. True only if the algorithm guarantees the optimum

    def solve(self, instance: Instance, ctx: RunContext) -> list[int]:
        # 5. receive the instance (read-only) and the run context
        selected = []
        for j in range(instance.m):
            ctx.check_time()                 # stops cleanly if --time-limit is exceeded
            selected.append(j)
        ctx.stats["subsets_scanned"] = instance.m   # optional counters, saved in the CSV
        # 6. return the 0-based indices of the chosen subsets.
        #    No timing, no verification here: the runner does both.
        return selected
