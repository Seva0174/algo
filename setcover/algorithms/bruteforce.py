"""Force brute : essaie toutes les combinaisons de sous-ensembles.

Adapté de la première version écrite par Jayden (hors du package) pour la base commune.

Principe : on essaie d'abord toutes les combinaisons de 1 sous-ensemble,
puis de 2, puis de 3, etc. La première combinaison qui couvre tout l'univers
est donc forcément une solution optimale (la plus petite possible).

Complexité : jusqu'à 2^m combinaisons -> utilisable seulement sur de très
petites instances (STS9, STS15, instances aléatoires avec m ≈ 20).

Lancer :
    python -m setcover solve -a bruteforce STS9 --show
"""

from itertools import combinations

from .base import Algorithm, register


@register
class BruteForce(Algorithm):
    name = "bruteforce"
    exact = True                # garantit l'optimum

    def solve(self, instance, ctx):
        m = instance.m
        n = instance.n
        nb_combinaisons = 0

        # k = nombre de sous-ensembles choisis, du plus petit au plus grand
        for k in range(m + 1):
            for indices in combinations(range(m), k):
                ctx.check_time()        # s'arrête proprement si le temps est dépassé
                nb_combinaisons += 1

                # union des sous-ensembles choisis
                covered = set()
                for j in indices:
                    covered.update(instance.subsets[j])

                # l'univers est {0, ..., n-1} : il est couvert si on a n éléments
                if len(covered) == n:
                    ctx.stats["combinaisons_testees"] = nb_combinaisons
                    ctx.stats["k_optimal"] = k
                    return list(indices)

            # on garde le compteur à jour pour le CSV même en cas de timeout
            ctx.stats["combinaisons_testees"] = nb_combinaisons
            ctx.stats["k_atteint"] = k

        raise ValueError("instance infaisable : aucune combinaison ne couvre l'univers")
