"""Représentation d'une instance USCP (Unicost Set Cover Problem).

* l'univers est {0, ..., n-1}
* les sous-ensembles sont numérotés 0, ..., m-1
* tous les sous-ensembles coûtent 1
"""


class Instance:
    def __init__(self, n, subsets, name="unnamed"):
        self.n = n                                  # nombre d'éléments
        self.subsets = [set(s) for s in subsets]    # subsets[j] = éléments couverts par j
        self.m = len(self.subsets)                  # nombre de sous-ensembles
        self.name = name

        # vérification : chaque élément doit être entre 0 et n-1
        for j in range(self.m):
            for e in self.subsets[j]:
                if e < 0 or e >= n:
                    raise ValueError(f"sous-ensemble {j} : élément {e} hors de [0, {n - 1}]")

        # covering[e] = liste des sous-ensembles qui contiennent e
        self.covering = []
        for e in range(n):
            self.covering.append([])
        for j in range(self.m):
            for e in self.subsets[j]:
                self.covering[e].append(j)

    def uncoverable(self):
        """Éléments couverts par aucun sous-ensemble."""
        result = []
        for e in range(self.n):
            if len(self.covering[e]) == 0:
                result.append(e)
        return result

    def is_feasible(self):
        return len(self.uncoverable()) == 0

    def nnz(self):
        """Somme des tailles des sous-ensembles."""
        total = 0
        for s in self.subsets:
            total += len(s)
        return total

    def density(self):
        if self.n == 0 or self.m == 0:
            return 0.0
        return self.nnz() / (self.n * self.m)

    def stats(self):
        sizes = []
        for s in self.subsets:
            sizes.append(len(s))
        freq = []
        for c in self.covering:
            freq.append(len(c))

        resultat = {}
        resultat["name"] = self.name
        resultat["n"] = self.n
        resultat["m"] = self.m
        resultat["density"] = round(self.density(), 6)
        resultat["subset_size_min"] = min(sizes)
        resultat["subset_size_avg"] = round(sum(sizes) / len(sizes), 3)
        resultat["subset_size_max"] = max(sizes)
        resultat["elem_freq_min"] = min(freq)
        resultat["elem_freq_max"] = max(freq)
        resultat["feasible"] = self.is_feasible()
        return resultat

    def __repr__(self):
        return f"Instance(name={self.name!r}, n={self.n}, m={self.m})"
