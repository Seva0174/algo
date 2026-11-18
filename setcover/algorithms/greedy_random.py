"""Glouton aléatoire (type GRASP) pour le Set Cover.

Même principe que le glouton classique (voir greedy.py), mais au lieu de
prendre TOUJOURS le sous-ensemble de gain maximal, on en tire un au hasard
dans une liste restreinte de candidats (RCL) :

    RCL = { j : gain[j] >= (1 - alpha) * gain_max   et   gain[j] > 0 }

  * alpha = 0 : seuls les sous-ensembles de gain maximal sont candidats
                (comme le glouton classique, mais les égalités sont
                départagées au hasard au lieu de prendre le plus petit indice) ;
  * alpha = 1 : tous les sous-ensembles utiles (gain > 0) sont candidats
                (choix purement aléatoire).

Les gains sont maintenus de la même façon que dans le glouton classique
(décrémentation via ``instance.covering[e]``), donc le coût d'un tour reste
O(m) : un parcours pour gain_max, un parcours pour construire la RCL.

Comme le résultat change d'une exécution à l'autre, on peut refaire
``nb_essais`` constructions et garder la meilleure.

Complexité : nb_essais * O(nnz + k * m). Pas d'algorithme exact, et pas de
garantie d'approximation sur une exécution isolée.

Lancer :
    python -m setcover solve -a greedy-random E.1 --seed 3 --show
"""

from .base import Algorithm, register


@register
class GreedyRandom(Algorithm):
    name = "greedy-random"
    exact = False

    alpha = 0.3         # 0 = glouton pur, 1 = choix totalement aléatoire
    nb_essais = 1       # nombre de constructions ; on garde la meilleure

    def solve(self, instance, ctx):
        if not 0 <= self.alpha <= 1:
            raise ValueError("alpha doit être entre 0 et 1")

        meilleure = None
        for essai in range(self.nb_essais):
            selected = self.construire(instance, ctx)
            ctx.improve(selected)       # garde la meilleure si le temps est dépassé
            if meilleure is None or len(selected) < len(meilleure):
                meilleure = selected

        ctx.stats["alpha"] = self.alpha
        ctx.stats["essais"] = self.nb_essais
        return meilleure

    def construire(self, instance, ctx):
        """Une construction gloutonne aléatoire : renvoie la liste des indices choisis."""
        # gain[j] = nombre d'éléments non couverts dans le sous-ensemble j
        gain = []
        for j in range(instance.m):
            gain.append(len(instance.subsets[j]))

        covered = []
        for e in range(instance.n):
            covered.append(False)
        nb_non_couverts = instance.n
        selected = []

        while nb_non_couverts > 0:
            ctx.check_time()

            # 1. gain maximal du tour
            gain_max = 0
            for j in range(instance.m):
                if gain[j] > gain_max:
                    gain_max = gain[j]
            if gain_max == 0:
                raise ValueError("instance infaisable : éléments impossibles à couvrir")

            # 2. liste restreinte de candidats (RCL) : gain proche du maximum
            seuil = (1 - self.alpha) * gain_max
            candidats = []
            for j in range(instance.m):
                if gain[j] > 0 and gain[j] >= seuil:
                    candidats.append(j)

            # 3. tirage au hasard parmi les candidats (ctx.rng => reproductible avec --seed)
            choisi = ctx.rng.choice(candidats)

            # 4. mise à jour : identique au glouton classique
            selected.append(choisi)
            for e in instance.subsets[choisi]:
                if not covered[e]:
                    covered[e] = True
                    nb_non_couverts -= 1
                    for j in instance.covering[e]:
                        gain[j] -= 1

        return selected
