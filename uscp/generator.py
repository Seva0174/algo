"""Générateur aléatoire d'instances USCP (modèle par densité)."""

from __future__ import annotations

import random

from .instance import Instance


def generate(n: int, m: int, density: float, seed: int) -> Instance:
    """Génère une instance aléatoire réalisable.

    Chaque sous-ensemble contient chaque élément avec probabilité `density`.
    Les éléments restés non couverts sont ensuite affectés à un sous-ensemble
    tiré au hasard, ce qui garantit qu'une solution existe.
    Même (n, m, density, seed) => même instance.
    """
    # Test des donnée d'entrée
    if n <= 0 or m <= 0:
        raise ValueError("n et m doivent être > 0")
    if not 0.0 < density <= 1.0:
        raise ValueError("density doit être dans ]0, 1]")
    
    # Initialisation  de la lst des sous-ensembles
    rng = random.Random(seed)  # RNG local : pas d'effet de bord sur random global
    subsets: list[set[int]] = []
    for _ in range(m):  # un sous-ensemble par itération
        subset: set[int] = set()
        for e in range(n):  # on teste chaque élément de l'univers
            if rng.random() < density:  # tirage dans [0, 1[ : vrai avec probabilité `density`
                subset.add(e)
        subsets.append(subset)
    
    # Garantir la faisabilité : tout élément couvert par aucun sous-ensemble
    # est ajouté à un sous-ensemble tiré au hasard.
    covered: set[int] = set().union(*subsets)
    for e in range(n):
        if e not in covered:
            subsets[rng.randrange(m)].add(e)

    # Renvoie la une instance
    return Instance(n, m, subsets)
