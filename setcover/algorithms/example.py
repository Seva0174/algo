"""Exemple : le plus petit algorithme possible.

Il ne contient aucune logique de set cover : il choisit tous les sous-ensembles.
C'est toujours une couverture valide (si l'instance est faisable), mais jamais
une bonne. Copiez ce fichier pour démarrer un nouvel algorithme.

Lancer :
    python -m setcover solve -a example E.1
"""

from .base import Algorithm, register


@register                       # 1. enregistre la classe -> utilisable avec "-a example"
class AlgoExemple(Algorithm):   # 2. on hérite de Algorithm
    name = "example"            # 3. identifiant en ligne de commande
    exact = False               # 4. True seulement si l'optimum est garanti

    def solve(self, instance, ctx):
        selected = []
        for j in range(instance.m):
            ctx.check_time()            # s'arrête proprement si le temps est dépassé
            selected.append(j)
        ctx.stats["subsets_scanned"] = instance.m   # compteur facultatif
        # 5. on renvoie les indices (0-based) des sous-ensembles choisis.
        #    Ni chronométrage ni vérification ici : le runner s'en occupe.
        return selected
