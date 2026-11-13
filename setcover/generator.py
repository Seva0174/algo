"""Générateur aléatoire d'instances USCP, paramétré comme demandé par le sujet.

Paramètres :
  * ``n``       : nombre d'éléments de l'univers ;
  * ``m``       : nombre de sous-ensembles candidats ;
  * ``density`` : probabilité qu'un élément appartienne à un sous-ensemble donné
    (chaque couple (élément, sous-ensemble) est tiré indépendamment) ;
  * ``seed``    : graine. Mêmes paramètres + même graine => même instance,
    ce qui rend toutes les expériences reproductibles.

Réparation (``repair=True``, par défaut) : après le tirage, chaque élément
couvert par aucun sous-ensemble est ajouté à un sous-ensemble tiré au hasard,
et chaque sous-ensemble vide reçoit un élément au hasard. L'instance est donc
toujours faisable. La densité réelle est légèrement supérieure à ``density``
quand celle-ci est très faible : utiliser ``instance.density`` pour la valeur
exacte dans les tableaux.
"""

from __future__ import annotations

import itertools
import os
import random
from typing import Iterable, Iterator

from .instance import Instance
from .io import write_orlib


def generate(n: int, m: int, density: float, seed: int = 0, repair: bool = True,
             name: str | None = None) -> Instance:
    if n <= 0 or m <= 0:
        raise ValueError("n et m doivent être > 0")
    if not 0.0 < density <= 1.0:
        raise ValueError("density doit être dans ]0, 1]")

    rng = random.Random(seed)  # générateur local : aucun effet sur random global
    subsets: list[set[int]] = [
        {e for e in range(n) if rng.random() < density} for _ in range(m)
    ]

    if repair:
        covered = set().union(*subsets)
        for e in range(n):
            if e not in covered:
                subsets[rng.randrange(m)].add(e)
        for s in subsets:
            if not s:
                s.add(rng.randrange(n))

    name = name or f"rand_n{n}_m{m}_p{density:g}_s{seed}"
    return Instance(n=n, m=m, subsets=tuple(frozenset(s) for s in subsets), name=name)


def grid(ns: Iterable[int], ms: Iterable[int], densities: Iterable[float],
         seeds: Iterable[int]) -> Iterator[Instance]:
    """Toutes les combinaisons de paramètres (plan d'expérience complet)."""
    for n, m, p, s in itertools.product(ns, ms, densities, seeds):
        yield generate(n, m, p, s)


def generate_to_dir(instances: Iterable[Instance], out_dir: str) -> list[str]:
    """Écrit les instances au format OR-Library dans ``out_dir``."""
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    for inst in instances:
        path = os.path.join(out_dir, f"{inst.name}.txt")
        write_orlib(inst, path)
        paths.append(path)
    return paths
