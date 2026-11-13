"""Exécution chronométrée + vérification, identique pour tous les algorithmes.

Mesure du temps :
  * ``time_s``  : temps réel (``time.perf_counter``) de l'appel à ``solve``
    uniquement — chargement de l'instance et vérification exclus ;
  * ``cpu_s``   : temps CPU du processus (``time.process_time``) sur le même
    intervalle, moins sensible à la charge de la machine.

La limite de temps est **coopérative** : l'algorithme doit appeler
``ctx.check_time()`` dans ses boucles. Si elle est dépassée, on renvoie la
meilleure solution signalée via ``ctx.improve`` (statut ``timeout``).

Chaque exécution produit un ``RunResult`` (une ligne de CSV).
"""

from __future__ import annotations

import csv
import gc
import os
import platform
import time
import traceback
from dataclasses import asdict, dataclass, field
from typing import Iterable

from .algorithms import Algorithm, RunContext, TimeLimitExceeded
from .instance import Instance
from .solution import verify


@dataclass
class RunResult:
    instance: str
    n: int
    m: int
    density: float
    algorithm: str
    params: str
    seed: int
    status: str                  # ok | timeout | infeasible | error
    cost: int | None             # coût vérifié (None si pas de solution)
    feasible: bool
    time_s: float
    cpu_s: float
    known: int | None = None     # valeur de référence (benchmarks)
    known_status: str | None = None   # optimal | bks | None
    gap_pct: float | None = None # 100 * (cost - known) / known
    exact: bool = False          # l'algorithme est-il exact ?
    stats: dict = field(default_factory=dict)
    selected: list[int] = field(default_factory=list, repr=False)
    error: str = ""

    def short(self) -> str:
        cost = "-" if self.cost is None else self.cost
        ref = ""
        if self.known is not None:
            ref = f"  réf={self.known} ({self.known_status})"
            if self.gap_pct is not None:
                ref += f"  écart={self.gap_pct:+.2f}%"
        return (f"{self.instance:<28} {self.params:<32} {self.status:<10} "
                f"coût={cost:<6} temps={self.time_s:9.4f}s{ref}")


def run(algorithm: Algorithm, instance: Instance, time_limit: float | None = None,
        seed: int = 0, known: int | None = None, known_status: str | None = None) -> RunResult:
    """Lance ``algorithm`` sur ``instance``, chronomètre et vérifie la solution."""
    ctx = RunContext(time_limit=time_limit, seed=seed)
    selected, status, error = None, "ok", ""

    gc.collect()                         # évite qu'un GC hérité fausse la mesure
    t0, c0 = time.perf_counter(), time.process_time()
    ctx._start = t0
    try:
        selected = list(algorithm.solve(instance, ctx))
    except TimeLimitExceeded:
        status, selected = "timeout", ctx.best
    except Exception as exc:              # on garde la trace dans le CSV
        status, error = "error", f"{type(exc).__name__}: {exc}"
        selected = ctx.best
        traceback.print_exc()
    t1, c1 = time.perf_counter(), time.process_time()

    cost, feasible = None, False
    if selected is not None:
        v = verify(instance, selected)
        feasible = v.feasible
        if feasible:
            cost = v.cost
        elif status == "ok":
            status, error = "infeasible", v.message()

    gap = None
    if cost is not None and known:
        gap = round(100.0 * (cost - known) / known, 4)
        if known_status == "optimal" and cost < known:
            error = (error + " " if error else "") + "ATTENTION: coût < optimum connu"

    return RunResult(
        instance=instance.name, n=instance.n, m=instance.m,
        density=round(instance.density, 6),
        algorithm=algorithm.name, params=algorithm.label, seed=seed,
        status=status, cost=cost, feasible=feasible,
        time_s=t1 - t0, cpu_s=c1 - c0,
        known=known, known_status=known_status, gap_pct=gap,
        exact=algorithm.exact, stats=dict(ctx.stats),
        selected=sorted(selected) if selected else [], error=error,
    )


def run_many(algorithms: Iterable[Algorithm], instances: Iterable[tuple[Instance, int | None, str | None]],
             repeats: int = 1, time_limit: float | None = None, base_seed: int = 0,
             csv_path: str | None = None, verbose: bool = True) -> list[RunResult]:
    """Produit cartésien algorithmes x instances x répétitions.

    ``instances`` : itérable de (instance, valeur connue, statut). Les
    résultats sont ajoutés au CSV au fur et à mesure (rien n'est perdu si on
    interrompt une longue campagne).
    """
    algorithms = list(algorithms)
    results = []
    for inst, known, kstatus in instances:
        for algo in algorithms:
            for r in range(repeats):
                res = run(algo, inst, time_limit=time_limit, seed=base_seed + r,
                          known=known, known_status=kstatus)
                results.append(res)
                if verbose:
                    print(res.short(), flush=True)
                if csv_path:
                    append_csv(res, csv_path)
    return results


CSV_FIELDS = ["instance", "n", "m", "density", "algorithm", "params", "seed", "status",
              "cost", "feasible", "time_s", "cpu_s", "known", "known_status", "gap_pct",
              "exact", "stats", "error", "machine"]


def append_csv(result: RunResult, path: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    new = not os.path.exists(path)
    row = asdict(result)
    row.pop("selected")
    row["stats"] = ";".join(f"{k}={v}" for k, v in row["stats"].items())
    row["machine"] = f"{platform.system()}-{platform.machine()}|py{platform.python_version()}"
    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if new:
            w.writeheader()
        w.writerow(row)
