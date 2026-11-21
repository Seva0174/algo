"""Recuit simulé pour le problème de couverture d'ensemble unicost."""

from .base import Algorithm, register


@register
class SimulatedAnnealing(Algorithm):
    name = "sa"
    exact = False

    def solve(self, instance, ctx):
        if not instance.is_feasible():
            raise ValueError("instance infaisable : éléments impossibles à couvrir")

        # Solution initiale : couverture gloutonne, puis suppression des
        # sous-ensembles devenus redondants.
        gains = [len(s) for s in instance.subsets]
        covered = [False] * instance.n
        uncovered = instance.n
        selected = set()

        while uncovered:
            ctx.check_time()
            best = max(range(instance.m), key=lambda j: (gains[j], -j))
            if gains[best] <= 0:
                break
            selected.add(best)
            for e in instance.subsets[best]:
                if not covered[e]:
                    covered[e] = True
                    uncovered -= 1
                    for j in instance.covering[e]:
                        gains[j] -= 1

        selected = self._remove_redundant(instance, selected)
        self._record_if_feasible(instance, selected, ctx)

        if len(selected) == 1:
            ctx.stats.update({"iterations": 0, "accepted": 0, "initial_cost": 1,
                              "final_cost": 1})
            return sorted(selected)

        temperature = max(1.0, len(selected) * 0.5)
        final_temperature = 0.05
        cooling = 0.995
        iterations = 0
        accepted = 0
        current = set(selected)
        current_cost = len(current)

        while temperature > final_temperature:
            ctx.check_time()
            iterations += 1

            candidate = set(current)
            move = ctx.rng.random()

            if move < 0.55:
                # Retirer puis réparer si nécessaire.
                removable = list(candidate)
                if not removable:
                    continue
                candidate.remove(ctx.rng.choice(removable))
            elif move < 0.85:
                # Ajouter un sous-ensemble absent.
                absent = [j for j in range(instance.m) if j not in candidate]
                if absent:
                    candidate.add(ctx.rng.choice(absent))
            else:
                # Échange : retirer un sous-ensemble puis en ajouter un autre.
                if candidate:
                    candidate.remove(ctx.rng.choice(list(candidate)))
                absent = [j for j in range(instance.m) if j not in candidate]
                if absent:
                    candidate.add(ctx.rng.choice(absent))

            candidate = self._repair(instance, candidate, ctx)
            candidate = self._remove_redundant(instance, candidate)

            candidate_cost = len(candidate)
            delta = candidate_cost - current_cost
            if delta <= 0 or ctx.rng.random() < self._acceptance(delta, temperature):
                current = candidate
                current_cost = candidate_cost
                accepted += 1

            if current_cost < len(ctx.best) if ctx.best is not None else True:
                self._record_if_feasible(instance, current, ctx)

            temperature *= cooling

        ctx.stats.update({"iterations": iterations, "accepted": accepted,
                          "initial_cost": len(selected), "final_cost": len(current)})
        return sorted(current)

    @staticmethod
    def _repair(instance, selected, ctx):
        count = [0] * instance.n
        for j in selected:
            for e in instance.subsets[j]:
                count[e] += 1

        missing = [e for e in range(instance.n) if count[e] == 0]
        for e in missing:
            ctx.check_time()
            choices = instance.covering[e]
            if not choices:
                raise ValueError("instance infaisable : élément impossible à couvrir")
            j = max(choices, key=lambda k: sum(1 for x in instance.subsets[k] if count[x] == 0))
            if j not in selected:
                selected.add(j)
                for x in instance.subsets[j]:
                    count[x] += 1
        return selected

    @staticmethod
    def _remove_redundant(instance, selected):
        result = set(selected)
        while True:
            count = [0] * instance.n
            for j in result:
                for e in instance.subsets[j]:
                    count[e] += 1

            redundant = None
            for j in sorted(result):
                if all(count[e] >= 2 for e in instance.subsets[j]):
                    redundant = j
                    break
            if redundant is None:
                return result
            result.remove(redundant)

    @staticmethod
    def _acceptance(delta, temperature):
        if delta <= 0:
            return 1.0
        if temperature <= 0:
            return 0.0
        # Maximize : energy is cost, so higher cost is less likely.
        try:
            import math
            return math.exp(-delta / temperature)
        except OverflowError:
            return 0.0

    @staticmethod
    def _record_if_feasible(instance, selected, ctx):
        count = [0] * instance.n
        for j in selected:
            for e in instance.subsets[j]:
                count[e] += 1
        if all(v > 0 for v in count):
            ctx.improve(sorted(selected))
