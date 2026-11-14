"""Base commune à tous les algorithmes.

Pour ajouter un algorithme :

1. créer un fichier dans ``setcover/algorithms/`` (ex. ``greedy.py``) ;
2. écrire une classe qui hérite de ``Algorithm`` et mettre ``@register`` au-dessus ;
3. l'importer dans ``setcover/algorithms/__init__.py``.

Exemple minimal ::

    @register
    class TakeAll(Algorithm):
        name = "take-all"

        def solve(self, instance, ctx):
            return list(range(instance.m))

Ce que reçoit ``solve`` :
  * ``instance`` : l'instance à résoudre (à ne pas modifier) ;
  * ``ctx`` : un ``RunContext`` qui contient
      - ``ctx.rng``          : générateur aléatoire (pour les algos aléatoires) ;
      - ``ctx.check_time()`` : à appeler dans les boucles longues ;
      - ``ctx.stats``        : dictionnaire pour vos compteurs (nœuds explorés...) ;
      - ``ctx.improve(sol)`` : pour signaler la meilleure solution trouvée.

Ce que renvoie ``solve`` : la liste des indices (0-based) des sous-ensembles
choisis. Le chronométrage et la vérification sont faits par le runner.
"""

import random
import time


class TimeLimitExceeded(Exception):
    """Levée par ``ctx.check_time()`` quand la limite de temps est dépassée."""


class RunContext:
    def __init__(self, time_limit=None, seed=0):
        self.time_limit = time_limit        # en secondes, None = pas de limite
        self.seed = seed
        self.rng = random.Random(seed)      # à utiliser pour tout tirage aléatoire
        self.stats = {}                     # compteurs libres
        self.best = None                    # meilleure solution signalée via improve()
        self.start = time.perf_counter()

    def elapsed(self):
        """Temps écoulé depuis le début, en secondes."""
        return time.perf_counter() - self.start

    def check_time(self):
        """À appeler dans les boucles : arrête l'algorithme si le temps est écoulé."""
        if self.time_limit is not None and self.elapsed() > self.time_limit:
            raise TimeLimitExceeded()

    def improve(self, selected):
        """Garde ``selected`` si elle est meilleure (plus petite) que la précédente.

        Si la limite de temps est atteinte, le runner renverra quand même
        cette meilleure solution.
        """
        selected = list(selected)
        if self.best is None or len(selected) < len(self.best):
            self.best = selected


class Algorithm:
    name = "abstract"       # identifiant utilisé en ligne de commande
    exact = False           # True si l'algorithme garantit l'optimum

    def solve(self, instance, ctx):
        """Renvoie les indices (0-based) des sous-ensembles choisis."""
        raise NotImplementedError("solve() doit être écrite dans la sous-classe")


# ---------------------------------------------------------------------- #
# Registre : dictionnaire  nom -> classe
# ---------------------------------------------------------------------- #
REGISTRY = {}


def register(cls):
    """Décorateur : ajoute la classe au registre sous son ``name``."""
    if cls.name in REGISTRY:
        raise ValueError(f"algorithme '{cls.name}' déjà enregistré")
    REGISTRY[cls.name] = cls
    return cls


def get_algorithm(name):
    """Crée un objet de l'algorithme enregistré sous ``name``."""
    if name not in REGISTRY:
        raise KeyError(f"algorithme inconnu '{name}', disponibles : {available()}")
    return REGISTRY[name]()


def available():
    """Liste triée des noms d'algorithmes disponibles."""
    return sorted(REGISTRY)
