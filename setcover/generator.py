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
quand celle-ci est très faible : utiliser ``instance.density()`` pour la valeur
exacte dans les tableaux.
"""

import os
import random

from .instance import Instance
from .io import write_orlib


def generate(n, m, density, seed=0, repair=True, name=None):
    if n <= 0 or m <= 0:
        raise ValueError("n et m doivent être > 0")
    if density <= 0.0 or density > 1.0:
        raise ValueError("density doit être dans ]0, 1]")

    # Générateur aléatoire propre à cette fonction : il n'affecte pas
    # le module random global. Même graine => mêmes tirages.
    rng = random.Random(seed)

    # Pour chaque sous-ensemble, chaque élément est choisi avec
    # une probabilité égale à density.
    subsets = []
    for j in range(m):
        sous_ensemble = set()
        for e in range(n):
            if rng.random() < density:
                sous_ensemble.add(e)
        subsets.append(sous_ensemble)

    if repair:
        # 1. Les éléments couverts par aucun sous-ensemble
        #    sont ajoutés à un sous-ensemble choisi au hasard.
        covered = set()
        for s in subsets:
            covered = covered | s
        for e in range(n):
            if e not in covered:
                j = rng.randrange(m)
                subsets[j].add(e)

        # 2. Les sous-ensembles vides reçoivent un élément au hasard.
        for s in subsets:
            if len(s) == 0:
                s.add(rng.randrange(n))

    if name is None:
        name = f"rand_n{n}_m{m}_p{density:g}_s{seed}"
    return Instance(n, subsets, name)


def grid(ns, ms, densities, seeds):
    """Toutes les combinaisons de paramètres (plan d'expérience complet).

    Renvoie la liste des instances générées.
    """
    instances = []
    for n in ns:
        for m in ms:
            for density in densities:
                for seed in seeds:
                    instances.append(generate(n, m, density, seed))
    return instances


def generate_to_dir(instances, out_dir):
    """Écrit les instances au format OR-Library dans ``out_dir``.

    Renvoie la liste des chemins des fichiers créés.
    """
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    for inst in instances:
        path = os.path.join(out_dir, f"{inst.name}.txt")
        write_orlib(inst, path)
        paths.append(path)
    return paths
