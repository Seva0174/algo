"""Meilleures solutions connues des benchmarks USCP et évaluation de la qualité.

BEST_KNOWN[nom_de_fichier] = (valeur, optimal_prouvé)

- optimal_prouvé = True  : la valeur est l'optimum (preuve dans la littérature).
- optimal_prouvé = False : meilleure solution connue (BKS), l'optimum peut être plus petit.

Sources :
- STS : USPC-instances/steiner-triple-covering/README (optimaux jusqu'à data.243).
  data.1215 et data.2187 : table de github.com/pinam45/USCP (sts.hpp), BKS.
- E, CLR, CYC : table de github.com/pinam45/USCP (orlibrary.hpp). Optimalité non
  vérifiée -> False (E est probablement optimal d'après Beasley 1987).
"""

from __future__ import annotations

import os

BEST_KNOWN: dict[str, tuple[int, bool]] = {
    # OR-Library, unicost
    "scpe1.txt": (5, False),
    "scpe2.txt": (5, False),
    "scpe3.txt": (5, False),
    "scpe4.txt": (5, False),
    "scpe5.txt": (5, False),
    "scpclr10.txt": (25, False),
    "scpclr11.txt": (23, False),
    "scpclr12.txt": (23, False),
    "scpclr13.txt": (23, False),
    "scpcyc06.txt": (60, False),
    "scpcyc07.txt": (144, False),
    "scpcyc08.txt": (342, False),
    "scpcyc09.txt": (772, False),
    "scpcyc10.txt": (1798, False),
    "scpcyc11.txt": (3968, False),
    # Steiner triple covering
    "data.9": (5, True),
    "data.15": (9, True),
    "data.27": (18, True),
    "data.45": (30, True),
    "data.81": (61, True),
    "data.135": (103, True),
    "data.243": (198, True),
    "data.405": (335, False),
    "data.729": (617, False),
    "data.1215": (1063, False),
    "data.2187": (1963, False),
}


def best_known(path: str) -> tuple[int, bool] | None:
    """(valeur, optimal_prouvé) pour ce fichier d'instance, ou None si inconnu."""
    return BEST_KNOWN.get(os.path.basename(path))


def evaluate(inst, chosen, path: str) -> dict:
    """Évalue une solution (liste d'indices de sous-ensembles) sur un benchmark.

    Retourne un dict :
      valid   : la solution couvre bien tout l'univers
      size    : nombre de sous-ensembles choisis
      best    : valeur de référence (None si instance inconnue)
      optimal : la référence est un optimum prouvé
      gap     : (size - best) / best, en % (None si pas de référence)
      status  : "INVALIDE", "SANS REF", "OK" ou "ALERTE" (voir ci-dessous)

    ALERTE = solution valide plus petite que la référence : soit une vraie
    amélioration d'un BKS, soit (si la référence est optimale) un bug.
    """
    chosen = list(chosen)
    valid = inst.is_cover(chosen)
    size = len(set(chosen))
    ref = best_known(path)

    res = {"valid": valid, "size": size, "best": None, "optimal": None,
           "gap": None, "status": "INVALIDE"}
    if not valid:
        return res
    if ref is None:
        res["status"] = "SANS REF"
        return res

    best, optimal = ref
    res.update(best=best, optimal=optimal, gap=100.0 * (size - best) / best)
    res["status"] = "ALERTE" if size < best else "OK"
    return res
