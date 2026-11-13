"""Tous les algorithmes disponibles.

Chaque nouveau module d'algorithme doit être importé ici pour que son
``@register`` soit exécuté.
"""

from .base import (REGISTRY, Algorithm, RunContext, TimeLimitExceeded,
                   available, get_algorithm, register)
from . import example  # noqa: F401  (registers "example")
# from . import greedy
# from . import bruteforce
# from . import branch_and_bound
# from . import dynamic_programming

__all__ = ["Algorithm", "RunContext", "TimeLimitExceeded", "register",
           "get_algorithm", "available", "REGISTRY"]
