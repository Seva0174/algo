"""Interface commune à tous les algorithmes.

Pour ajouter un algorithme :

1. créer un fichier dans ``setcover/algorithms/`` (ex. ``bruteforce.py``) ;
2. écrire une classe qui hérite de ``Algorithm`` et la décorer avec ``@register`` ;
3. l'importer dans ``setcover/algorithms/__init__.py``.

Exemple minimal ::

    @register
    class TakeAll(Algorithm):
        name = "take-all"
        exact = False

        def solve(self, instance, ctx):
            return list(range(instance.m))

Elle est alors utilisable partout : ``python -m setcover solve -a take-all E.1``.

Ce que reçoit ``solve`` :
  * ``instance`` : l'``Instance`` (immuable) ;
  * ``ctx`` : un ``RunContext`` qui donne la graine / le générateur aléatoire,
    la limite de temps (``ctx.check_time()`` à appeler régulièrement dans les
    boucles longues), un dictionnaire ``ctx.stats`` pour les compteurs
    (nœuds explorés, itérations...) et ``ctx.improve(sol)`` pour signaler la
    meilleure solution trouvée jusqu'ici.

Ce que renvoie ``solve`` : les indices (0-based) des sous-ensembles choisis.
Le chronométrage et la vérification sont faits à l'extérieur (``runner``),
de la même façon pour tous les algorithmes.

Paramètres : ``get_algorithm("grasp", alpha=0.3)`` appelle ``__init__`` avec
``alpha=0.3`` ; on les retrouve dans ``self.params`` et dans les CSV.
"""

from __future__ import annotations

import random
import time
from abc import ABC, abstractmethod
from typing import ClassVar, Iterable

from ..instance import Instance


class TimeLimitExceeded(Exception):
    """Levée par ``ctx.check_time()`` quand la limite de temps est dépassée."""


class RunContext:
    def __init__(self, time_limit: float | None = None, seed: int = 0):
        self.time_limit = time_limit            # secondes, None = pas de limite
        self.seed = seed
        self.rng = random.Random(seed)          # à utiliser pour tout tirage aléatoire
        self.stats: dict = {}                   # compteurs libres, recopiés dans les résultats
        self.best: list[int] | None = None      # meilleure solution signalée via improve()
        self.trace: list[tuple[float, int]] = []  # (temps, coût) à chaque amélioration
        self._start = time.perf_counter()

    def elapsed(self) -> float:
        return time.perf_counter() - self._start

    def time_left(self) -> float:
        if self.time_limit is None:
            return float("inf")
        return self.time_limit - self.elapsed()

    def check_time(self) -> None:
        """À appeler dans les boucles : interrompt l'algorithme si le temps est écoulé."""
        if self.time_limit is not None and self.elapsed() > self.time_limit:
            raise TimeLimitExceeded()

    def improve(self, selected: Iterable[int]) -> bool:
        """Enregistre ``selected`` si elle est meilleure que la précédente.

        Utile pour les méthodes exactes ou les métaheuristiques : si la limite
        de temps est atteinte, le runner renvoie quand même cette solution.
        L'appelant doit s'assurer que ``selected`` est une couverture valide
        (elle sera de toute façon revérifiée par le runner).
        """
        sel = list(selected)
        if self.best is None or len(sel) < len(self.best):
            self.best = sel
            self.trace.append((self.elapsed(), len(sel)))
            return True
        return False


class Algorithm(ABC):
    name: ClassVar[str] = "abstract"   # identifiant utilisé en ligne de commande
    exact: ClassVar[bool] = False      # True si l'algorithme garantit l'optimum

    def __init__(self, **params):
        self.params = params

    @abstractmethod
    def solve(self, instance: Instance, ctx: RunContext) -> Iterable[int]:
        """Renvoie les indices (0-based) des sous-ensembles choisis."""

    @property
    def label(self) -> str:
        """Nom + paramètres, ex. ``grasp(alpha=0.3)``."""
        if not self.params:
            return self.name
        args = ",".join(f"{k}={v}" for k, v in sorted(self.params.items()))
        return f"{self.name}({args})"


# ---------------------------------------------------------------------- #
# Registre des algorithmes
# ---------------------------------------------------------------------- #
REGISTRY: dict[str, type[Algorithm]] = {}


def register(cls: type[Algorithm]) -> type[Algorithm]:
    if cls.name in REGISTRY:
        raise ValueError(f"algorithme '{cls.name}' déjà enregistré")
    REGISTRY[cls.name] = cls
    return cls


def get_algorithm(name: str, **params) -> Algorithm:
    try:
        return REGISTRY[name](**params)
    except KeyError:
        raise KeyError(f"algorithme inconnu '{name}', disponibles : {sorted(REGISTRY)}") from None


def available() -> list[str]:
    return sorted(REGISTRY)
