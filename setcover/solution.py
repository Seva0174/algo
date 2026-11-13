"""Vérification des solutions.

Une solution est simplement une collection d'indices (0-based) de
sous-ensembles. ``verify`` est **indépendant de tous les algorithmes** : c'est
le juge commun qui garantit que les résultats comparés sont valides.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .instance import Instance


@dataclass
class Verification:
    feasible: bool                  # True ssi indices valides ET tout est couvert
    cost: int                       # nb de sous-ensembles distincts choisis
    uncovered: list[int] = field(default_factory=list)   # éléments non couverts
    invalid: list[int] = field(default_factory=list)     # indices hors [0, m-1]
    duplicates: list[int] = field(default_factory=list)  # indices choisis 2 fois
    redundant: list[int] = field(default_factory=list)   # retirables sans perdre la couverture

    def __bool__(self) -> bool:
        return self.feasible

    def message(self) -> str:
        if self.feasible:
            msg = f"OK : couverture valide de coût {self.cost}"
            if self.redundant:
                msg += f" ({len(self.redundant)} sous-ensemble(s) redondant(s))"
            return msg
        parts = []
        if self.invalid:
            parts.append(f"indices invalides {self.invalid[:10]}")
        if self.uncovered:
            parts.append(f"{len(self.uncovered)} élément(s) non couvert(s), ex. {self.uncovered[:10]}")
        return "INVALIDE : " + ", ".join(parts)


def verify(instance: Instance, selected: Iterable[int]) -> Verification:
    """Vérifie qu'une sélection couvre tout l'univers et calcule son coût."""
    selected = list(selected)
    seen: set[int] = set()
    duplicates, invalid = [], []
    for j in selected:
        if not (isinstance(j, int) and 0 <= j < instance.m):
            invalid.append(j)
        elif j in seen:
            duplicates.append(j)
        else:
            seen.add(j)

    # Combien de fois chaque élément est couvert (sert aussi à la redondance).
    count = [0] * instance.n
    for j in seen:
        for e in instance.subsets[j]:
            count[e] += 1
    uncovered = [e for e in range(instance.n) if count[e] == 0]

    # j est redondant si tous ses éléments sont couverts au moins 2 fois.
    redundant = [j for j in sorted(seen) if all(count[e] >= 2 for e in instance.subsets[j])]

    return Verification(
        feasible=not uncovered and not invalid,
        cost=len(seen),
        uncovered=uncovered,
        invalid=invalid,
        duplicates=duplicates,
        redundant=redundant,
    )


def is_cover(instance: Instance, selected: Iterable[int]) -> bool:
    """Version rapide (bitmask) pour les algorithmes qui testent beaucoup de solutions."""
    mask = 0
    masks = instance.masks
    for j in selected:
        mask |= masks[j]
    return mask == instance.full_mask
