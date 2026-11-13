"""Lecture / écriture des fichiers d'instances et de solutions.

Formats supportés
-----------------

1. **OR-Library SCP** (scpe*.txt, scpclr*.txt, scpcyc*.txt, et les fichiers
   générés par ``setcover.generator``) — indices 1-based ::

       n m                  # nb d'éléments (rows), nb de sous-ensembles (columns)
       c_1 ... c_m          # coût de chaque sous-ensemble (tous à 1 en unicost)
       k  j_1 ... j_k       # pour chaque élément : nb de sous-ensembles qui le
       ...                  # couvrent puis leurs indices (n blocs)

   Les retours à la ligne ne sont pas significatifs : on lit des jetons.

2. **Steiner Triple Covering** (data.9, data.15, ...) — indices 1-based ::

       nb_variables nb_triplets     # attention : sous-ensembles AVANT éléments
       a b c                        # un triplet par élément : il est couvert
       ...                          # par les sous-ensembles a, b et c

3. **Solution** (format maison, simple à relire à la main) ::

       # commentaires optionnels
       cost
       j_1 j_2 ... j_cost   # indices 1-based des sous-ensembles choisis
"""

from __future__ import annotations

import os
from typing import Iterable

from .instance import Instance


class UnicostError(ValueError):
    """Le fichier décrit une instance pondérée : hors sujet pour ce projet."""


# ---------------------------------------------------------------------- #
# Instances
# ---------------------------------------------------------------------- #
def _tokens(path: str) -> list[int]:
    with open(path) as f:
        return [int(t) for t in f.read().split()]


def read_orlib(path: str, require_unicost: bool = True, name: str | None = None) -> Instance:
    """Lit un fichier au format OR-Library SCP."""
    tok = _tokens(path)
    pos = 0
    n, m = tok[0], tok[1]
    pos = 2
    costs = tok[pos:pos + m]
    pos += m
    if require_unicost and any(c != 1 for c in costs):
        raise UnicostError(f"{path} : coûts != 1, instance pondérée (non unicost)")

    subsets: list[set[int]] = [set() for _ in range(m)]
    for e in range(n):
        k = tok[pos]
        pos += 1
        for j in tok[pos:pos + k]:
            subsets[j - 1].add(e)
        pos += k
    if pos != len(tok):
        raise ValueError(f"{path} : {len(tok) - pos} jetons en trop, fichier incohérent")
    return Instance(n=n, m=m, subsets=tuple(frozenset(s) for s in subsets),
                    name=name or _default_name(path))


def read_steiner(path: str, name: str | None = None) -> Instance:
    """Lit un fichier Steiner Triple Covering (data.*)."""
    tok = _tokens(path)
    m, n = tok[0], tok[1]               # m sous-ensembles (variables), n éléments (triplets)
    if len(tok) != 2 + 3 * n:
        raise ValueError(f"{path} : nombre de triplets incohérent")
    subsets: list[set[int]] = [set() for _ in range(m)]
    for e in range(n):
        for j in tok[2 + 3 * e: 5 + 3 * e]:
            subsets[j - 1].add(e)
    return Instance(n=n, m=m, subsets=tuple(frozenset(s) for s in subsets),
                    name=name or _default_name(path))


def read_instance(path: str, name: str | None = None) -> Instance:
    """Choisit le bon parseur d'après le nom du fichier (data.* -> Steiner)."""
    if os.path.basename(path).startswith("data."):
        return read_steiner(path, name=name)
    return read_orlib(path, name=name)


def write_orlib(instance: Instance, path: str) -> None:
    """Écrit une instance au format OR-Library (lisible par ``read_orlib``)."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w") as f:
        f.write(f"{instance.n} {instance.m}\n")
        f.write(" ".join("1" for _ in range(instance.m)) + "\n")
        for cov in instance.covering:
            f.write(f"{len(cov)} " + " ".join(str(j + 1) for j in cov) + "\n")


def _default_name(path: str) -> str:
    base = os.path.basename(path)
    return base[:-4] if base.endswith(".txt") else base


# ---------------------------------------------------------------------- #
# Solutions
# ---------------------------------------------------------------------- #
def write_solution(selected: Iterable[int], path: str, comment: str = "") -> None:
    sel = sorted(set(selected))
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w") as f:
        for line in comment.splitlines():
            f.write(f"# {line}\n")
        f.write(f"{len(sel)}\n")
        f.write(" ".join(str(j + 1) for j in sel) + "\n")


def read_solution(path: str) -> list[int]:
    """Renvoie les indices 0-based. Le coût annoncé est vérifié."""
    with open(path) as f:
        lines = [l for l in f if l.strip() and not l.lstrip().startswith("#")]
    tok = [int(t) for t in " ".join(lines).split()]
    if not tok:
        raise ValueError(f"{path} : fichier de solution vide")
    cost, idx = tok[0], tok[1:]
    if cost != len(idx):
        raise ValueError(f"{path} : coût annoncé {cost} mais {len(idx)} indices")
    return [j - 1 for j in idx]
