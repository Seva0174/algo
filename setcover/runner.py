"""Exécution chronométrée + vérification, identique pour tous les algorithmes.

Pour chaque exécution :
  1. on lance l'algorithme en mesurant le temps ;
  2. on vérifie que la solution couvre bien tout l'univers ;
  3. on affiche le résultat.

La limite de temps est "coopérative" : l'algorithme doit appeler
``ctx.check_time()`` dans ses boucles. Si le temps est dépassé, on garde
la meilleure solution trouvée jusque-là (``ctx.best``).
"""

import csv
import os
import time

from .algorithms import RunContext, TimeLimitExceeded
from .solution import verify


def run(algorithm, instance, time_limit=None, seed=0, known=None, known_status=None):
    """Lance ``algorithm`` sur ``instance`` et renvoie un dictionnaire de résultats.

    * time_limit : limite en secondes (None = pas de limite)
    * seed       : graine pour les algorithmes aléatoires
    * known      : meilleure valeur connue pour cette instance (facultatif)
    * known_status : "optimal" ou "bks" (facultatif, juste pour l'affichage)
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
        "n": instance.n,                # nombre d'éléments
        "m": instance.m,                # nombre de sous-ensembles
        "density": round(instance.density(), 6),
        "algorithm": algorithm.name,
        "exact": algorithm.exact,       # True si l'algorithme garantit l'optimum
        "status": status,
        "cost": cost,
        "feasible": feasible,
        "time_s": fin - debut,
        "known": known,
        "known_status": known_status,
        "gap_pct": ecart,
        "error": error,
        "selected": selected,           # indices 0-based (None si aucune solution)
        "stats": ctx.stats,             # compteurs de l'algorithme
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
        if resultat["known_status"] is not None:
            ligne += f" ({resultat['known_status']})"
        if resultat["gap_pct"] is not None:
            ligne += f"  écart={resultat['gap_pct']:+.2f}%"
    if resultat["error"] != "":
        ligne += f"  ({resultat['error']})"
    print(ligne)


def run_many(algorithms, instances, time_limit=None):
    """Lance chaque algorithme sur chaque instance et affiche les résultats.

    ``instances`` est une liste de triplets (instance, valeur connue, statut)
    (valeur connue et statut peuvent être None).
    Renvoie la liste de tous les résultats.
    """
    resultats = []
    for instance, known, status in instances:
        for algorithm in algorithms:
            resultat = run(algorithm, instance, time_limit=time_limit,
                           known=known, known_status=status)
            afficher(resultat)
            resultats.append(resultat)
    return resultats


CSV_COLONNES = ["instance", "n", "m", "density", "algorithm", "exact", "seed",
                "status", "cost", "feasible", "time_s",
                "known", "known_status", "gap_pct", "stats", "error"]


def append_csv(resultat, path, seed=0):
    """Ajoute une ligne au fichier CSV (l'en-tête est écrit si le fichier est nouveau)."""
    dossier = os.path.dirname(os.path.abspath(path))
    os.makedirs(dossier, exist_ok=True)
    nouveau = not os.path.exists(path)

    ligne = {}
    for colonne in CSV_COLONNES:
        if colonne == "seed":
            ligne[colonne] = seed
        elif colonne == "stats":
            # dictionnaire de compteurs -> texte "cle=valeur;cle=valeur"
            morceaux = []
            for cle in sorted(resultat["stats"]):
                morceaux.append(f"{cle}={resultat['stats'][cle]}")
            ligne[colonne] = ";".join(morceaux)
        else:
            ligne[colonne] = resultat[colonne]

    with open(path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLONNES)
        if nouveau:
            writer.writeheader()
        writer.writerow(ligne)
