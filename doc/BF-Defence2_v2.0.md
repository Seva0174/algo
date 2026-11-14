# Brute Force Algorithm for Set Cover

## Problem Setup

This brute force algorithm covers the set cover problem. It is written as a class of the
common `setcover` package, so it receives an already loaded `Instance` instead of reading
the file itself. The main variables in the program are:

- `instance.n` is the number of elements in the universe. The universe is `{0, 1, …, n-1}`
  (0-based in memory, files on disk are 1-based).
- `instance.subsets` is the list of the `m` available subsets. Each subset is a Python `set`
  containing some of the elements of the universe.
- `instance.m` is the number of subsets.

The main goal is to select the fewest subsets whose union equals the universe. The brute
force algorithm (exhaustive search) tries every possible selection of subsets, first starting
with the smallest selection.

## Brute Force Algorithm

File: `setcover/algorithms/bruteforce.py`

```python
from itertools import combinations

from .base import Algorithm, register


@register
class BruteForce(Algorithm):
    name = "bruteforce"
    exact = True                # guarantees the optimum

    def solve(self, instance, ctx):
        m = instance.m
        n = instance.n
        nb_combinaisons = 0

        for k in range(m + 1):
            for indices in combinations(range(m), k):
                ctx.check_time()
                nb_combinaisons += 1

                covered = set()
                for j in indices:
                    covered.update(instance.subsets[j])

                if len(covered) == n:
                    ctx.stats["combinaisons_testees"] = nb_combinaisons
                    ctx.stats["k_optimal"] = k
                    return list(indices)

            ctx.stats["combinaisons_testees"] = nb_combinaisons
            ctx.stats["k_atteint"] = k

        raise ValueError("instance infaisable : aucune combinaison ne couvre l'univers")
```

### Integration with the common package

- `@register` adds the class to the list of algorithms, so it can be used from the command
  line with `-a bruteforce`.
- `name = "bruteforce"` is the identifier used on the command line and in the CSV files.
- `exact = True` indicates that the algorithm always returns an optimal solution.
- `solve(self, instance, ctx)` receives the instance and a run context `ctx`, and returns the
  list of the chosen subset indices. The cover size is simply the length of this list.

## The Loops

The outer loop checks each solution in increasing order of size:

- `k = 0` – select no subsets.
- `k = 1` – select one subset.
- `k = 2` – select two subsets.
- Continue until `k = m`.

The inner loop uses `combinations(range(m), k)` to generate every combination that contains
exactly `k` subsets.

`ctx.check_time()` is called for each combination. If a time limit was given (option `-t`)
and it is exceeded, the search stops cleanly and the result is reported as `timeout`.

## Building the Union

`covered` becomes an empty set for every new combination. The loop over `indices` then adds
the elements of each selected subset with `covered.update(instance.subsets[j])`, so that
`covered` becomes the union of all the selected subsets.

## Valid Cover

Since the universe is exactly `{0, 1, …, n-1}` and `covered` only contains elements of the
universe, `len(covered) == n` means that the selected subsets contain every element. In turn,
the combination is a valid cover. The method then returns the list of chosen subset indices;
its length is the cover size `k`.

If no combination covers the universe (some element belongs to no subset), the method raises
an error and the run is reported with the status `error`.

## Optimal Solution

The outer loop tests sizes in increasing order of `k`. When the algorithm reaches size `k`,
it has already tested every combination with fewer than `k` subsets and none of them covered
the universe. Therefore, the first valid cover found must use the minimum possible number of
subsets.

## Counters

The algorithm records counters in `ctx.stats`, which are written in the `stats` column of the
CSV files:

- `combinaisons_testees` – number of combinations tested.
- `k_optimal` – size of the optimal cover found.
- `k_atteint` – last size `k` that was fully tested (useful when the run hits the time limit).

## Running the Program

Timing, loading of the file and verification of the solution are no longer written in the
algorithm. They are done by the common runner (`setcover/runner.py`) in the same way for
every algorithm, which makes the comparisons fair:

```
python3 -m setcover solve -a bruteforce STS9 --show
```

The runner calls `time.perf_counter()` just before and just after `solve`. This is so that
the execution time only covers the search and not the loading of the file. Then the solution
is checked by `verify`, which is independent of the algorithm, and compared to the known
optimal value of the benchmark. With `--show`, subsets are printed 1-based (S1, S2, …) to
match the numbering in the data file.

To run several instances and save the results in a CSV file:

```
python3 -m setcover bench -a bruteforce STS9 STS15 --random 20 15 0.2 --count 3 -t 60 -o results/bruteforce.csv
```

## Results

Running the program on the STS9 benchmark gives the following:

```
STS9    bruteforce    ok    coût=5    temps=0.0003s  réf=5 (optimal)  écart=+0.00%
    sous-ensembles (1-based) : [1, 2, 3, 4, 5]
```

The chosen subsets contain the following elements (1-based, as in the data file):

```
S1: [2, 3, 7, 10]
S2: [1, 3, 8, 11]
S3: [1, 2, 9, 12]
S4: [1, 5, 6, 10]
S5: [2, 4, 6, 11]
```

The union of these subsets is `{1, 2, …, 12}`, so every element of the universe is covered.
Because the algorithm tests all the smaller selections first, no cover with 4 or fewer subsets
exists. This is confirmed by the counters: `combinaisons_testees = 257`, that is
1 + 9 + 36 + 84 + 126 = 256 combinations of size 0 to 4, plus the first combination of size 5.
The cost is equal to the known optimum (`écart = +0.00%`). The execution time depends on the
machine and can vary between runs.

Other results:

| Instance | n | m | Optimum | Found | Time |
|---|---|---|---|---|---|
| STS9 | 12 | 9 | 5 | 5 | 0.0003 s |
| STS15 | 35 | 15 | 9 | 9 | 0.04 s |
| STS27 | 117 | 27 | 18 | – | timeout (3 s) |
| E.1 | 50 | 500 | 5 | – | timeout (3 s) |

## Complexity

In the worst case, the algorithm examines all 2^m combinations of subsets, and building the
union for each one takes time depending on the size of the chosen subsets. This can lead to
running time growing exponentially with `m`. If the optimum is `k*`, the algorithm tests
C(m,0) + C(m,1) + … + C(m,k*) combinations: for E.1 (m = 500, k* = 5) this is about
2.6 · 10^11 combinations, which is far too many. Therefore, brute force is only practical for
small instances such as STS9 and STS15, or random instances with about 20 subsets.
