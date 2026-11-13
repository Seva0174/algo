"""Exécution chronométrée + vérification, identique pour tous les algorithmes.

Pour chaque exécution :
  1. on lance l'algorithme en mesurant le temps ;
  2. on vérifie que la solution couvre bien tout l'univers ;
  3. on affiche le résultat.

La limite de temps est "coopérative" : l'algorithme doit appeler
``ctx.check_time()`` dans ses boucles. Si le temps est dépassé, on garde
la meilleure solution trouvée jusque-là (``ctx.best``).
"""

import time

from .algorithms import RunContext, TimeLimitExceeded
from .solution2 import verify


def run(algorithm, instance, time_limit=None, seed=0, known=None):
    """Lance ``algorithm`` sur ``instance`` et renvoie un dictionnaire de résultats.

    * time_limit : limite en secondes (None = pas de limite)
    * seed       : graine pour les algorithmes aléatoires
    * known      : meilleure valeur connue pour cette instance (facultatif)
    """
    ctx = RunContext(time_limit=time_limit, seed=seed)
    status = "ok"
    error = ""

    # 1. Lancer l'algorithme en mesurant le temps
    debut = time.perf_counter()
    try:
        selected = list(algorithm.solve(instance, ctx))
    except TimeLimitExceeded:
        status = "timeout"
        selected = ctx.best             # meilleure solution trouvée avant la fin
    except Exception as exc:
        status = "error"
        error = f"{type(exc).__name__}: {exc}"
        selected = ctx.best
    fin = time.perf_counter()

    # 2. Vérifier la solution (s'il y en a une)
    cost = None
    feasible = False
    if selected is not None:
        verification = verify(instance, selected)
        feasible = verification.feasible
        if feasible:
            cost = verification.cost
        elif status == "ok":
            status = "infeasible"
            error = verification.message()

    # 3. Écart avec la meilleure valeur connue, en pourcentage
    ecart = None
    if cost is not None and known is not None:
        ecart = 100.0 * (cost - known) / known

    return {
        "instance": instance.name,
        "algorithm": algorithm.label,
        "status": status,
        "cost": cost,
        "feasible": feasible,
        "time_s": fin - debut,
        "known": known,
        "gap_pct": ecart,
        "error": error,
    }


def afficher(resultat):
    """Affiche une ligne lisible pour un résultat renvoyé par ``run``."""
    cout = resultat["cost"]
    if cout is None:
        cout = "-"
    ligne = (f"{resultat['instance']:<28} {resultat['algorithm']:<24} "
             f"{resultat['status']:<10} coût={cout:<6} temps={resultat['time_s']:.4f}s")
    if resultat["known"] is not None:
        ligne += f"  réf={resultat['known']}"
        if resultat["gap_pct"] is not None:
            ligne += f"  écart={resultat['gap_pct']:+.2f}%"
    if resultat["error"] != "":
        ligne += f"  ({resultat['error']})"
    print(ligne)


def run_many(algorithms, instances, time_limit=None):
    """Lance chaque algorithme sur chaque instance et affiche les résultats.

    ``instances`` est une liste de couples (instance, valeur connue ou None).
    Renvoie la liste de tous les résultats.
    """
    resultats = []
    for instance, known in instances:
        for algorithm in algorithms:
            resultat = run(algorithm, instance, time_limit=time_limit, known=known)
            afficher(resultat)
            resultats.append(resultat)
    return resultats
