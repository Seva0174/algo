"""Test du chargement des instances de benchmark USCP (unicost).

Utilisation (depuis n'importe quel dossier) :

    python uscp/main.py                  # charge toutes les instances
    python uscp/main.py scpe1 data.27    # charge seulement celles qui contiennent ces noms
"""

from __future__ import annotations

import glob
import os
import sys
import time

from instance import load_any

# Dossier des instances, relatif à ce fichier : ALGO/USPC-instances
RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOSSIER = os.path.join(RACINE, "USPC-instances")


def lister_instances() -> list[str]:
    """Toutes les instances unicost gardées : OR-Library puis Steiner."""
    orlib = sorted(glob.glob(os.path.join(DOSSIER, "OR-Library", "scp*.txt")))
    steiner = sorted(
        glob.glob(os.path.join(DOSSIER, "steiner-triple-covering", "data.*")),
        key=lambda p: int(p.rsplit(".", 1)[1]),  # tri numérique : 9, 15, 27...
    )
    return orlib + steiner


def tester(path: str) -> bool:
    """Charge une instance et vérifie qu'elle est cohérente."""
    debut = time.perf_counter()
    inst = load_any(path)
    duree = time.perf_counter() - debut

    ok = (
        inst.is_coverable()                      # chaque élément est couvert
        and inst.is_cover(range(inst.m))         # prendre tout = une couverture
    )
    taille_moy = sum(len(s) for s in inst.subsets) / inst.m
    print(
        f"{os.path.basename(path):<14} n={inst.n:>7}  m={inst.m:>6}  "
        f"|S| moyen={taille_moy:6.1f}  chargé en {duree:5.2f}s  "
        f"{'OK' if ok else 'ERREUR'}"
    )
    return ok


def main() -> None:
    chemins = lister_instances()
    if len(sys.argv) > 1:  # filtre optionnel sur les noms
        chemins = [p for p in chemins if any(a in os.path.basename(p) for a in sys.argv[1:])]

    if not chemins:
        print(f"Aucune instance trouvée dans {DOSSIER}")
        return

    nb_ok = sum(tester(p) for p in chemins)
    print(f"\n{nb_ok}/{len(chemins)} instances chargées correctement")


if __name__ == "__main__":
    main()
