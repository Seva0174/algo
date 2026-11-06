"""Générateur aléatoire d'instances USCP (modèle par densité)."""

from __future__ import annotations

import random

from instance import Instance


def generate(n: int, m: int, density: float, seed: int) -> Instance:
    """Génère une instance aléatoire réalisable.

    Chaque sous-ensemble contient chaque élément avec probabilité `density`.
    Les éléments restés non couverts sont ensuite affectés à un sous-ensemble
    tiré au hasard, ce qui garantit qu'une solution existe.
    Même (n, m, density, seed) => même instance.
    """
    if n <= 0 or m <= 0:
        raise ValueError("n et m doivent être > 0")
    if not 0.0 < density <= 1.0:
        raise ValueError("density doit être dans ]0, 1]")

    rng = random.Random(seed)  # RNG local : pas d'effet de bord sur random global
    subsets: list[set[int]] = [
        {e for e in range(n) if rng.random() < density} for _ in range(m)
    ]

    covered: set[int] = set().union(*subsets)
    for e in range(n):
        if e not in covered:
            subsets[rng.randrange(m)].add(e)

    return Instance(n, m, subsets)


instance = generate(10, 5, 0.5, 52)  # pour vérifier que le code est correct
print(instance)  # Affiche l'instance générée