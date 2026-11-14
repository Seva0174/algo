"""Glouton classique pour le Set Cover.

Principe : tant qu'il reste des éléments non couverts, on choisit le
sous-ensemble qui couvre le PLUS d'éléments ENCORE NON COUVERTS
(et pas simplement le plus grand sous-ensemble : un grand sous-ensemble
dont tous les éléments sont déjà couverts n'apporte rien).

Mise en œuvre :
  * gain[j] = nombre d'éléments non couverts contenus dans le sous-ensemble j ;
  * au départ gain[j] = |S_j| ;
  * quand un élément e devient couvert, chaque sous-ensemble qui contient e
    (liste ``instance.covering[e]``) perd 1 de gain.
  Ainsi on ne recalcule jamais d'intersection : chaque couple (élément,
  sous-ensemble) n'est décrémenté qu'une seule fois.

Complexité : O(nnz + k * m), où nnz = somme des tailles des sous-ensembles
et k = nombre de sous-ensembles choisis (une recherche du max en O(m) par tour).

Garantie : coût <= H(d) * optimum, avec d = taille du plus grand sous-ensemble
et H(d) = 1 + 1/2 + ... + 1/d <= ln(d) + 1. Ce n'est PAS un algorithme exact.

Égalités : à gain égal, on prend le sous-ensemble d'indice le plus petit
(résultat déterministe, reproductible).

Lancer :
    python -m setcover solve -a greedy E.1 --show
"""

from .base import Algorithm, register


@register
class Greedy(Algorithm):
    name = "greedy"
    exact = False

    def solve(self, instance, ctx):
        # gain[j] = nombre d'éléments non couverts dans le sous-ensemble j
        #   au départ rien n'est couvert, donc gain[j] = taille du sous-ensemble j
        gain = []
        for j in range(instance.m):
            gain.append(len(instance.subsets[j]))

        # covered[e] = True si l'élément e est déjà couvert (au départ : aucun)
        covered = []
        for e in range(instance.n):
            covered.append(False)
        nb_non_couverts = instance.n
        selected = []

        while nb_non_couverts > 0:
            ctx.check_time()

            # 1. sous-ensemble de gain maximal
            #    (comparaison stricte ">" : en cas d'égalité on garde le premier,
            #     donc l'indice le plus petit)
            best = 0
            for j in range(1, instance.m):
                if gain[j] > gain[best]:
                    best = j
            if gain[best] == 0:
                # il reste des éléments, mais aucun sous-ensemble ne les contient
                raise ValueError("instance infaisable : éléments impossibles à couvrir")

            # 2. on le choisit et on marque ses nouveaux éléments comme couverts
            selected.append(best)
            for e in instance.subsets[best]:
                if not covered[e]:
                    covered[e] = True
                    nb_non_couverts -= 1
                    # 3. tous les sous-ensembles contenant e perdent 1 de gain
                    for j in instance.covering[e]:
                        gain[j] -= 1

        ctx.stats["iterations"] = len(selected)
        return selected
