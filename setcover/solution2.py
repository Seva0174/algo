"""Vérification des solutions.

Une solution est simplement une liste d'indices (0-based) de sous-ensembles.
``verify`` est indépendant de tous les algorithmes : c'est le juge commun
qui garantit que les résultats comparés sont valides.
"""


class Verification:
    def __init__(self, feasible, cost, uncovered, invalid, duplicates, redundant):
        self.feasible = feasible        # True si indices valides ET tout est couvert
        self.cost = cost                # nombre de sous-ensembles distincts choisis
        self.uncovered = uncovered      # éléments non couverts
        self.invalid = invalid          # indices hors de [0, m-1]
        self.duplicates = duplicates    # indices choisis plusieurs fois
        self.redundant = redundant      # sous-ensembles retirables sans perdre la couverture

    def __bool__(self):
        return self.feasible

    def message(self):
        if self.feasible:
            msg = f"OK : couverture valide de coût {self.cost}"
            if len(self.redundant) > 0:
                msg += f" ({len(self.redundant)} sous-ensemble(s) redondant(s))"
            return msg

        parts = []
        if len(self.invalid) > 0:
            parts.append(f"indices invalides {self.invalid[:10]}")
        if len(self.uncovered) > 0:
            parts.append(f"{len(self.uncovered)} élément(s) non couvert(s), ex. {self.uncovered[:10]}")
        return "INVALIDE : " + ", ".join(parts)


def verify(instance, selected):
    """Vérifie qu'une sélection couvre tout l'univers et calcule son coût."""
    seen = set()        # indices valides déjà rencontrés
    duplicates = []
    invalid = []
    for j in selected:
        if not isinstance(j, int) or j < 0 or j >= instance.m:
            invalid.append(j)
        elif j in seen:
            duplicates.append(j)
        else:
            seen.add(j)

    # count[e] = nombre de sous-ensembles choisis qui couvrent l'élément e
    count = [0] * instance.n
    for j in seen:
        for e in instance.subsets[j]:
            count[e] += 1

    uncovered = []
    for e in range(instance.n):
        if count[e] == 0:
            uncovered.append(e)

    # j est redondant si tous ses éléments sont couverts au moins 2 fois
    redundant = []
    for j in sorted(seen):
        tous_couverts_2_fois = True
        for e in instance.subsets[j]:
            if count[e] < 2:
                tous_couverts_2_fois = False
        if tous_couverts_2_fois:
            redundant.append(j)

    feasible = len(uncovered) == 0 and len(invalid) == 0
    return Verification(feasible, len(seen), uncovered, invalid, duplicates, redundant)


def is_cover(instance, selected):
    """Vrai si les sous-ensembles choisis couvrent tout l'univers."""
    covered = set()
    for j in selected:
        covered = covered | instance.subsets[j]
    return len(covered) == instance.n
