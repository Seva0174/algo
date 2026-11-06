"""Représentation d'une instance USCP (Unicost Set Covering Problem) + I/O.

Convention : l'univers est {0, ..., n-1} et les sous-ensembles sont numérotés
de 0 à m-1. Tous les sous-ensembles ont un coût de 1 (unicost), donc on
minimise simplement le nombre de sous-ensembles choisis.

Format de fichier (style OR-Library SCP, indices 1-based dans le fichier) :

    n m                      # nb d'éléments (lignes), nb de sous-ensembles (colonnes)
    1 1 ... 1                # m coûts (tous à 1)
    k  s_1 ... s_k           # pour chaque élément : nb de sous-ensembles qui le
                             # couvrent, puis leurs indices (1-based)
    ...                      # (n blocs)

Le parseur ne dépend que des tokens séparés par des espaces, les retours à la
ligne ne sont pas significatifs.
"""

from __future__ import annotations

from dataclasses import dataclass
"""
Exemple d'instance n = 6 (univers {0, 1, 2, 3, 4, 5}) et m = 4 sous-ensembles :

subsets = [
    {0, 1, 2},   # sous-ensemble 0 couvre les éléments 0, 1, 2
    {2, 3},      # sous-ensemble 1 couvre les éléments 2, 3
    {3, 4, 5},   # sous-ensemble 2 couvre les éléments 3, 4, 5
    {0, 5},      # sous-ensemble 3 couvre les éléments 0, 5
]
inst = Instance(n=6, m=4, subsets=subsets)

"""


@dataclass
class Instance:
    n: int                              # taille de l'univers
    m: int                              # nombre de sous-ensembles
    subsets: list[set[int]]             # subsets[j] = éléments couverts par j

    def __post_init__(self) -> None:
        if len(self.subsets) != self.m:
            raise ValueError("len(subsets) != m")
        for s in self.subsets:
            if s and not (0 <= min(s) and max(s) < self.n):
                raise ValueError("élément hors de l'univers")

    def is_coverable(self) -> bool:
        """True si chaque élément est dans au moins un sous-ensemble."""
        covered: set[int] = set()
        for s in self.subsets:
            covered |= s                # union en place : ajoute à `covered` les éléments de s                          
        return len(covered) == self.n   # si tous les n éléments (0..n-1) sont dans `covered`, l'instance est réalisable.

    def is_cover(self, chosen) -> bool:
        """True si les sous-ensembles `chosen` (indices) couvrent l'univers."""
        covered: set[int] = set()
        for j in chosen:
            covered |= self.subsets[j]
        return len(covered) == self.n


def save(instance: Instance, path: str) -> None:
    # Pour chaque élément, la liste des sous-ensembles qui le couvrent.
    covering: list[list[int]] = [[] for _ in range(instance.n)]
    for j, s in enumerate(instance.subsets):
        for e in s:
            covering[e].append(j)

    with open(path, "w") as f:
        f.write(f"{instance.n} {instance.m}\n")
        f.write(" ".join("1" for _ in range(instance.m)) + "\n")
        for sets in covering:
            f.write(f"{len(sets)} " + " ".join(str(j + 1) for j in sets) + "\n")


def load(path: str) -> Instance:
    with open(path) as f:
        tokens = f.read().split()
    pos = 0

    def nxt() -> int:
        nonlocal pos
        pos += 1
        return int(tokens[pos - 1])

    n, m = nxt(), nxt()
    for _ in range(m):  # coûts : on vérifie qu'ils valent tous 1 (unicost)
        if nxt() != 1:
            raise ValueError(f"{path} : instance pondérée (coût != 1), pas unicost")

    subsets: list[set[int]] = [set() for _ in range(m)]
    for e in range(n):
        for _ in range(nxt()):
            subsets[nxt() - 1].add(e)

    return Instance(n, m, subsets)


def load_steiner(path: str) -> Instance:
    """Charge une instance Steiner Triple Covering (fichiers data.*).

    Format du fichier (indices 1-based) :

        nb_variables nb_triplets     # attention : colonnes AVANT lignes
        a b c                        # un triplet par ligne = un élément à couvrir,
        ...                          # couvert par les sous-ensembles a, b et c

    Les triplets sont les éléments de l'univers, les variables sont les
    sous-ensembles. Pas de ligne de coûts : tout vaut 1.
    """
    with open(path) as f:
        tokens = [int(t) for t in f.read().split()]
    m, n = tokens[0], tokens[1]          # m sous-ensembles, n éléments
    if len(tokens) != 2 + 3 * n:
        raise ValueError(f"{path} : nombre de triplets incohérent")

    subsets: list[set[int]] = [set() for _ in range(m)]
    for e in range(n):
        for j in tokens[2 + 3 * e: 5 + 3 * e]:
            subsets[j - 1].add(e)

    return Instance(n, m, subsets)


def load_any(path: str) -> Instance:
    """Choisit le bon parseur selon le nom du fichier.

    - data.*  (dossier steiner-triple-covering) -> load_steiner
    - le reste (scp*.txt de l'OR-Library)       -> load
    """
    import os
    if os.path.basename(path).startswith("data."):
        return load_steiner(path)
    return load(path)
