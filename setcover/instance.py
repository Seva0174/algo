"""Représentation d'une instance USCP (Unicost Set Cover Problem).

Conventions utilisées partout dans le package :

* l'univers est {0, ..., n-1} (les "éléments", appelés "rows" dans l'OR-Library) ;
* les sous-ensembles sont numérotés 0, ..., m-1 (les "columns" de l'OR-Library) ;
* tous les sous-ensembles coûtent 1 : le coût d'une solution est son nombre
  de sous-ensembles distincts.

Les indices sont 0-based en mémoire. Les fichiers sur disque sont 1-based
(voir ``setcover.io``), la conversion se fait uniquement à la lecture/écriture.

Une instance est immuable : un algorithme ne peut pas la modifier par erreur,
ce qui garantit que toutes les méthodes travaillent sur exactement les mêmes
données. Plusieurs représentations dérivées sont calculées à la demande (et
mises en cache) pour que chaque algorithme utilise celle qui lui convient :

* ``subsets[j]``  : frozenset des éléments couverts par le sous-ensemble j ;
* ``covering[e]`` : tuple des sous-ensembles qui couvrent l'élément e ;
* ``masks[j]``    : entier (bitmask) dont le bit e vaut 1 si e ∈ subsets[j]
  (pratique pour la force brute, la programmation dynamique, le B&B).
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from typing import Iterable


@dataclass(frozen=True)
class Instance:
    n: int                                # taille de l'univers (nb d'éléments)
    m: int                                # nombre de sous-ensembles candidats
    subsets: tuple[frozenset[int], ...]   # subsets[j] = éléments couverts par j
    name: str = "unnamed"                 # nom lisible (fichier, paramètres...)

    # ------------------------------------------------------------------ #
    # Construction / validation
    # ------------------------------------------------------------------ #
    def __post_init__(self) -> None:
        # On accepte des listes de set/list en entrée et on normalise en
        # tuple de frozenset (dataclass gelée -> object.__setattr__).
        subsets = tuple(frozenset(s) for s in self.subsets)
        object.__setattr__(self, "subsets", subsets)

        if self.n < 0 or self.m < 0:
            raise ValueError("n et m doivent être positifs")
        if len(subsets) != self.m:
            raise ValueError(f"len(subsets)={len(subsets)} != m={self.m}")
        for j, s in enumerate(subsets):
            if s and (min(s) < 0 or max(s) >= self.n):
                raise ValueError(f"sous-ensemble {j} : élément hors de [0, {self.n - 1}]")

    @classmethod
    def from_subsets(cls, n: int, subsets: Iterable[Iterable[int]], name: str = "unnamed") -> "Instance":
        """Raccourci : ``Instance.from_subsets(6, [{0,1,2}, {2,3}, ...])``."""
        subsets = [frozenset(s) for s in subsets]
        return cls(n=n, m=len(subsets), subsets=tuple(subsets), name=name)

    # ------------------------------------------------------------------ #
    # Représentations dérivées (calculées une seule fois)
    # ------------------------------------------------------------------ #
    @cached_property
    def covering(self) -> tuple[tuple[int, ...], ...]:
        """covering[e] = sous-ensembles (triés) qui contiennent l'élément e."""
        cov: list[list[int]] = [[] for _ in range(self.n)]
        for j, s in enumerate(self.subsets):
            for e in s:
                cov[e].append(j)
        return tuple(tuple(sorted(c)) for c in cov)

    @cached_property
    def masks(self) -> tuple[int, ...]:
        """masks[j] = bitmask de subsets[j] (bit e à 1 si e est couvert)."""
        out = []
        for s in self.subsets:
            mask = 0
            for e in s:
                mask |= 1 << e
            out.append(mask)
        return tuple(out)

    @cached_property
    def full_mask(self) -> int:
        """Bitmask de l'univers complet : (1 << n) - 1."""
        return (1 << self.n) - 1

    # ------------------------------------------------------------------ #
    # Propriétés utiles
    # ------------------------------------------------------------------ #
    @cached_property
    def uncoverable(self) -> tuple[int, ...]:
        """Éléments couverts par aucun sous-ensemble (=> instance infaisable)."""
        return tuple(e for e in range(self.n) if not self.covering[e])

    @property
    def is_feasible(self) -> bool:
        """True s'il existe au moins une couverture (prendre tous les sous-ensembles)."""
        return not self.uncoverable

    @cached_property
    def nnz(self) -> int:
        """Nombre de couples (élément, sous-ensemble) : taille totale des sous-ensembles."""
        return sum(len(s) for s in self.subsets)

    @property
    def density(self) -> float:
        """Densité = nnz / (n * m), comme dans les tableaux du sujet."""
        return self.nnz / (self.n * self.m) if self.n and self.m else 0.0

    def stats(self) -> dict:
        """Caractéristiques de l'instance (pour les tableaux d'expériences)."""
        sizes = [len(s) for s in self.subsets] or [0]
        freq = [len(c) for c in self.covering] or [0]
        return {
            "name": self.name,
            "n": self.n,
            "m": self.m,
            "density": round(self.density, 6),
            "subset_size_min": min(sizes),
            "subset_size_avg": round(sum(sizes) / len(sizes), 3),
            "subset_size_max": max(sizes),
            "elem_freq_min": min(freq),       # nb min de sous-ensembles couvrant un élément
            "elem_freq_max": max(freq),
            "feasible": self.is_feasible,
        }

    def __repr__(self) -> str:  # pas de dump des sous-ensembles (trop gros)
        return f"Instance(name={self.name!r}, n={self.n}, m={self.m}, density={self.density:.4f})"
