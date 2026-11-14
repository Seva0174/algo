# `setcover` — Documentation

A small, dependency-free Python framework for the **Unicost Set Cover Problem
(USCP)**, built for the *Advanced Algorithms* project (Master DSC/MLDM, 2026–2027).
It does everything that is **common to all algorithms** so that each group member
only has to write the `solve` method of their own algorithm:

- load the benchmark instances (OR-Library E / CLR / CYC, Steiner triple covering STS);
- generate random instances (universe size, number of subsets, density, seed);
- run an algorithm with a **timer and an optional time limit**;
- **verify** every solution independently of the algorithm that produced it;
- compare the result with the known optimum / best known solution;
- write one CSV line per run, ready for plots and tables in the report.

The code is deliberately written in simple Python (plain classes, explicit loops,
no type annotations) so that every group member can read and explain it.

Contents

1. [Quick start](#1-quick-start)
2. [The problem and the conventions](#2-the-problem-and-the-conventions)
3. [Project layout and data flow](#3-project-layout-and-data-flow)
4. [Module reference](#4-module-reference)
5. [Writing a new algorithm](#5-writing-a-new-algorithm)
6. [Running experiments](#6-running-experiments)
7. [File formats](#7-file-formats)
8. [Benchmark instances and reference values](#8-benchmark-instances-and-reference-values)
9. [Tests](#9-tests)
10. [FAQ / troubleshooting](#10-faq--troubleshooting)

---

## 1. Quick start

**Requirements:** Python ≥ 3.9. No external package. Every command is run from
the **repository root** (the folder that contains `setcover/` and `USPC-instances/`).

```bash
python3 -m setcover list                          # available algorithms and benchmark instances
python3 -m setcover info E CYC6                   # characteristics of instances
python3 -m setcover solve -a bruteforce STS9      # run the brute force on STS9
python3 -m setcover bench -a example E CLR -t 60  # experiment campaign -> results/*.csv
python3 -m unittest discover -s tests             # run the tests
```

Output of `solve`:

```
STS9      bruteforce      ok      coût=5      temps=0.0002s  réf=5 (optimal)  écart=+0.00%
```

(Console messages are in French: `coût` = cost, `temps` = time, `réf` = reference value,
`écart` = gap.)

---

## 2. The problem and the conventions

**Set Cover.** Given a universe `U = {0, …, n-1}` and a family of `m` subsets
`S_0, …, S_{m-1}` of `U`, choose the smallest number of subsets whose union is `U`.
In the *unicost* version every subset costs 1, so **the cost of a solution is the
number of distinct subsets it contains**.

Vocabulary used everywhere in the code:

| Term | Meaning | OR-Library name |
|---|---|---|
| `n` | number of **elements** (size of the universe) | rows |
| `m` | number of **subsets** (candidate sets) | columns |
| `e` | an element, `0 ≤ e < n` | row |
| `j` | a subset index, `0 ≤ j < m` | column |
| solution / `selected` | list of subset indices `j` | — |
| density | `(Σ_j |S_j|) / (n·m)`, the share of 1s in the incidence matrix | density |

**Indices are 0-based in memory and 1-based in files.** The conversion is done only
in `setcover/io.py`; algorithms never see 1-based indices.

Small example used in the tests:

```python
from setcover import Instance
inst = Instance(6, [{0, 1, 2}, {2, 3}, {3, 4, 5}, {0, 5}], name="small")
# n = 6, m = 4, optimal solution = [0, 2] (cost 2)
```

---

## 3. Project layout and data flow

```
ALGO/
├── README.md                 short presentation of the project
├── DOCUMENTATION.md          ← this file
├── USPC-instances/           benchmark files (OR-Library + Steiner)
├── setcover/                 the framework (Python package)
│   ├── __init__.py           public API (what you import)
│   ├── __main__.py           command line: python3 -m setcover ...
│   ├── instance.py           Instance class
│   ├── io.py                 read/write instance and solution files
│   ├── generator.py          random instance generator
│   ├── solution.py           verify(): independent solution checker
│   ├── benchmarks.py         benchmark catalogue + optimal / best known values
│   ├── runner.py             timed + verified execution, CSV export
│   └── algorithms/
│       ├── __init__.py       imports every algorithm module (registration)
│       ├── base.py           Algorithm class, RunContext, registry
│       ├── example.py        AlgoExemple: minimal template, no logic
│       └── bruteforce.py     exhaustive search
├── tests/test_base.py        unit tests
├── doc/                      subject, group description, algorithm write-ups
└── results/                  CSV files written by `bench` (git-ignored)
```

How one run flows through the modules:

```
 file / benchmark name ──io.read_instance──► Instance ──────────────┐
 (n, m, density, seed) ──generator.generate─►                        │
                                                                    ▼
             runner.run(algorithm, instance, time_limit, seed, known)
               1. start timer
               2. selected = algorithm.solve(instance, ctx)   ◄── your code
               3. stop timer
               4. solution.verify(instance, selected)
               5. gap with the reference value (benchmarks.KNOWN)
                                                                    │
                                                                    ▼
                result (dict) ──► console line (runner.afficher)
                              └─► CSV line     (runner.append_csv)
```

The key design rule: **an algorithm only computes a list of subsets.** Timing,
verification, reference values and CSV output are done by the same code for every
algorithm, so results are comparable (checklist items 9 and 10 of the subject).

---

## 4. Module reference

Everything below can be imported directly from the package:

```python
from setcover import (Instance, read_instance, write_orlib, read_solution, write_solution,
                      generate, verify, is_cover, Algorithm, RunContext, register,
                      get_algorithm, available, run, run_many, afficher, append_csv,
                      benchmarks)
```

### 4.1 `instance.py` — `Instance`

```python
Instance(n, subsets, name="unnamed")
```

| Attribute / method | Type | Description |
|---|---|---|
| `n`, `m` | `int` | number of elements, number of subsets (`m = len(subsets)`) |
| `name` | `str` | display name (file name, benchmark name or generator parameters) |
| `subsets[j]` | `set` | elements covered by subset `j` |
| `covering[e]` | `list` | subsets that contain element `e` (increasing order) |
| `uncoverable()` | `list` | elements covered by no subset |
| `is_feasible()` | `bool` | `True` if a cover exists (no uncoverable element) |
| `nnz()` | `int` | `Σ_j |S_j|` |
| `density()` | `float` | `nnz / (n·m)` |
| `stats()` | `dict` | n, m, density, min/avg/max subset size, min/max element frequency, feasibility |

`subsets` and `covering` are computed once in the constructor. Choose the
representation that suits your algorithm:

- `subsets` — natural for greedy-like methods (`len(S & uncovered)`);
- `covering` — "which subsets can cover this element?" (branching in B&B, repair in
  local search).

The constructor checks that every element is in `[0, n-1]`, otherwise `ValueError`.

**The instance must not be modified by an algorithm** (for example
`instance.subsets[j].remove(e)`): it is shared by all runs, and `covering` would no
longer match `subsets`. Work on copies (`set(instance.subsets[j])`) when needed.

### 4.2 `io.py` — files

| Function | Description |
|---|---|
| `read_instance(path, name=None)` | picks the right parser: files named `data.*` → Steiner, otherwise OR-Library |
| `read_orlib(path, require_unicost=True, name=None)` | OR-Library format; raises `UnicostError` if a cost is not 1 |
| `read_steiner(path, name=None)` | Steiner triple covering format |
| `write_orlib(instance, path)` | writes the OR-Library format (used for generated instances) |
| `write_solution(selected, path, comment="")` | writes a solution file (1-based, sorted, without duplicates) |
| `read_solution(path)` | reads a solution file, returns 0-based indices, checks the announced cost |

Formats are described in [section 7](#7-file-formats).

### 4.3 `generator.py` — random instances

```python
generate(n, m, density, seed=0, repair=True, name=None) -> Instance
```

- each pair (element, subset) is included independently with probability `density`
  (this is the generator required by the subject);
- uses its own `random.Random(seed)`: **same parameters + same seed ⇒ same instance**;
- `repair=True` (default) guarantees feasibility: every uncovered element is added to a
  random subset, and every empty subset receives one random element. For very small
  densities the real density is therefore a bit higher than `density`; report
  `instance.density()` (also in the CSV) rather than the parameter;
- default name: `rand_n{n}_m{m}_p{density}_s{seed}`.

Helpers:

```python
grid(ns, ms, densities, seeds)         # list of instances for every combination (full factorial design)
generate_to_dir(instances, out_dir)    # writes them as OR-Library files, returns the paths
```

### 4.4 `solution.py` — verification

```python
verify(instance, selected) -> Verification
```

The single, algorithm-independent judge. It returns a `Verification` with:

| Field | Meaning |
|---|---|
| `feasible` | `True` iff all indices are valid **and** every element is covered |
| `cost` | number of **distinct** valid subsets (duplicates are not counted twice) |
| `uncovered` | elements not covered |
| `invalid` | indices outside `[0, m-1]` (or not integers) |
| `duplicates` | indices that appear more than once |
| `redundant` | chosen subsets that could each be removed **alone** without losing feasibility |

`bool(v)` is `v.feasible`; `v.message()` gives a readable summary.

Note on `redundant`: each subset is tested on its own. Removing one redundant subset
may make another one necessary, so the list is not "all the subsets you can remove
at the same time".

```python
is_cover(instance, selected) -> bool
```

A quick check (no details) that can be called inside algorithms. It assumes that all
indices are valid.

### 4.5 `benchmarks.py` — benchmark catalogue

| Name | Description |
|---|---|
| `DEFAULT_DIR` | `<repo>/USPC-instances`, or the `USCP_INSTANCES` environment variable |
| `KNOWN` | `dict` short name → `(value, status)` with status `"optimal"` or `"bks"` |
| `list_benchmarks(families=None)` | list of `Benchmark` found on disk, sorted by family then size |
| `find(name)` | one benchmark by short name, case-insensitive (`"cyc6"`, `"E.1"`) |
| `known_value(name)` | `(value, status)` or `(None, None)` |
| `short_name(path)` | file path → `(short name, family)`, e.g. `scpcyc06.txt` → `("CYC6", "CYC")`, or `None` |

A `Benchmark` has `name`, `family`, `path`, `known`, `status` and a `load()` method.
Families: `E`, `CLR`, `CYC`, `STS`. See [section 8](#8-benchmark-instances-and-reference-values).

### 4.6 `algorithms/base.py` — the algorithm interface

```python
class Algorithm:
    name = "abstract"            # command-line identifier, e.g. "bruteforce"
    exact = False                # True if the method guarantees optimality
    def solve(self, instance, ctx)   # your code: returns a list of subset indices
```

Algorithms have no parameters: one class = one method. A variant (for example another
greedy rule) is written as another class with its own `name`.

`solve` raises `NotImplementedError` if a subclass forgets to define it.

Registry:

| Function | Description |
|---|---|
| `@register` | class decorator, adds the class to `REGISTRY` under its `name` (error if the name is taken) |
| `get_algorithm(name)` | creates an object of a registered algorithm; `KeyError` if the name is unknown |
| `available()` | sorted list of registered names |

`RunContext` — the second argument of `solve`:

| Member | Description |
|---|---|
| `ctx.rng` | `random.Random(seed)`: use it for **all** randomness (reproducible with `--seed`) |
| `ctx.seed` | the seed itself |
| `ctx.time_limit` | seconds, or `None` |
| `ctx.check_time()` | raises `TimeLimitExceeded` if the limit is exceeded; call it in long loops |
| `ctx.elapsed()` | seconds since the start of the run |
| `ctx.improve(selected)` | records `selected` if it is smaller than the previous best |
| `ctx.best` | best solution recorded by `improve` (or `None`) |
| `ctx.stats` | free `dict` of counters (nodes, iterations…), written in the CSV |

### 4.7 `runner.py` — timed and verified execution

```python
run(algorithm, instance, time_limit=None, seed=0, known=None, known_status=None) -> dict
```

Steps: create the `RunContext` → start the clock → `algorithm.solve(instance, ctx)` →
stop the clock → `verify` → gap with the reference value.

The time is measured on the `solve` call only (loading and verification excluded),
with `time.perf_counter()` (wall-clock time).

Final status:

| Status | When | Returned solution |
|---|---|---|
| `ok` | `solve` returned a valid cover | the returned one |
| `timeout` | `ctx.check_time()` raised | `ctx.best` (may be `None` → `cost` empty) |
| `infeasible` | `solve` returned something that is not a cover | none (`cost` empty), reason in `error` |
| `error` | `solve` raised another exception | `ctx.best`, message in `error` |

The result is a dictionary with the keys:

| Key | Meaning |
|---|---|
| `instance`, `n`, `m`, `density` | instance name and characteristics |
| `algorithm`, `exact` | algorithm name and whether it is exact |
| `status`, `error` | see the table above |
| `cost`, `feasible` | cost of the verified solution (`None` if no valid solution) |
| `time_s` | running time of `solve`, in seconds |
| `known`, `known_status`, `gap_pct` | reference value, `"optimal"`/`"bks"`, `100·(cost − known)/known` |
| `selected` | chosen subset indices (0-based), not written in the CSV |
| `stats` | the `ctx.stats` counters |

Other functions:

```python
afficher(result)                       # prints one readable line
append_csv(result, path, seed=0)       # appends one line to a CSV file (header if new file)
run_many(algorithms, instances, time_limit=None) -> list
```

`run_many` runs every algorithm on every `(instance, known, status)` triple and prints
each result. CSV columns, in order:

```
instance, n, m, density, algorithm, exact, seed, status, cost, feasible, time_s,
known, known_status, gap_pct, stats, error
```

`stats` is written as `key=value;key=value`.

### 4.8 `__main__.py` — command line

```
python3 -m setcover <command> [options]
```

| Command | Options | Description |
|---|---|---|
| `list` | — | registered algorithms, benchmarks found and their reference values |
| `info INST...` | — | characteristics of instances |
| `solve -a ALGO INST...` | `-t SEC`, `--seed S`, `--show`, `-o PATH` | solve, verify, time; `--show` prints the chosen subsets; `-o` writes the solution (a folder if several instances) |
| `verify INST SOLUTION` | — | checks a solution file; exit code 0 if valid, 1 otherwise |
| `generate -n N.. -m M.. -p P..` | `--seed S`, `--count K`, `-o DIR` | writes every combination of n × m × p, K seeds each (default folder `generated/`) |
| `bench -a ALGO [-a ALGO...] [INST...]` | `--random N M P`, `--count K`, `-r R`, `-t SEC`, `--seed S`, `-o CSV` | experiment campaign, CSV in `results/bench_<date>_<time>.csv` by default |

`INST` can be:

- a file path (`USPC-instances/OR-Library/scpe1.txt`) — reference values are found
  automatically if it is a known benchmark file;
- a short benchmark name (`E.1`, `CLR10`, `CYC6`, `STS27`);
- a whole family (`E`, `CLR`, `CYC`, `STS`);
- a folder (every file inside, e.g. a folder created by `generate`).

In `bench`, each algorithm is run `-r R` times on each instance with seeds
`--seed`, `--seed + 1`, …, and every run is **appended to the CSV immediately**, so an
interrupted campaign loses nothing.

---

## 5. Writing a new algorithm

### 5.1 The template: `AlgoExemple`

`setcover/algorithms/example.py` contains **no set cover logic**. It returns every
subset (always a valid cover, never a good one) and shows what every algorithm needs:

```python
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
```

### 5.2 Step by step

1. Copy `setcover/algorithms/example.py` to a new file, e.g. `greedy.py`
   (no dash in the name, otherwise Python cannot import it).
2. Rename the class and change `name` (must be unique) and `exact`.
3. Write `solve`. It must **return a list of 0-based subset indices**.
4. Add one line in `setcover/algorithms/__init__.py`:
   ```python
   from . import greedy  # enregistre "greedy"
   ```
5. Check: `python3 -m setcover list` shows it; `python3 -m setcover solve -a greedy STS9`.

### 5.3 Rules for fair and reproducible comparisons

- **Do not time or verify inside `solve`**: the runner does it the same way for everyone.
- **Do not modify the instance** and do not read files in `solve`: loading is not part
  of the measured time.
- **Randomness only through `ctx.rng`** (never the global `random` module), so that
  `--seed` reproduces a run exactly and `-r 10` gives 10 different runs (seeds 0–9),
  needed for error bars (checklist item 6).
- **Call `ctx.check_time()` in every long loop** (each node of a search tree, each
  iteration of a metaheuristic). The limit is *cooperative*: Python cannot safely stop
  a function from outside, so an algorithm that never calls it is never interrupted.
- **Exact and anytime methods: call `ctx.improve(solution)` each time a better cover
  is found.** On timeout the runner returns that solution with status `timeout`, so
  the report can show the best cost reached within the limit.
- **Put counters in `ctx.stats`** (`nodes`, `pruned`, `iterations`, `memo_size`…):
  they explain the running times in the report.
- For an infeasible instance, raise `ValueError` (status `error`); the generator and
  all benchmarks are feasible, so this should not happen in practice.

### 5.4 Example of a real method: brute force

`setcover/algorithms/bruteforce.py` enumerates subsets by increasing size, so the
first cover found is optimal (detailed explanation in `doc/BF-Defence2_v2.0.md`):

```python
from itertools import combinations

from .base import Algorithm, register


@register
class BruteForce(Algorithm):
    name = "bruteforce"
    exact = True

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

It solves STS9 and STS15 in less than 0.1 s, and hits any reasonable time limit on
STS27 or E.1 (about 2.6·10^11 combinations for E.1).

### 5.5 Using it from Python (notebooks, plots)

```python
from setcover import generate, get_algorithm, run, afficher, benchmarks

algo = get_algorithm("bruteforce")

inst = generate(n=20, m=15, density=0.2, seed=3)
res = run(algo, inst, time_limit=10)
print(res["status"], res["cost"], res["time_s"], res["stats"])

b = benchmarks.find("STS15")
res = run(algo, b.load(), known=b.known, known_status=b.status)
afficher(res)
```

---

## 6. Running experiments

### 6.1 Benchmarks

```bash
# every algorithm on every family, 60 s per run
python3 -m setcover bench -a bruteforce -a greedy E CLR CYC STS -t 60 -o results/benchmarks.csv

# stochastic methods: 10 repetitions (seeds 0..9) for mean / std / error bars
python3 -m setcover bench -a rgreedy E CLR CYC STS -r 10 -t 60 -o results/stochastic.csv
```

### 6.2 Random instances

Either generate files first (they can be reused and shipped with the report):

```bash
python3 -m setcover generate -n 10 15 20 25 30 -m 20 -p 0.1 0.2 0.3 --count 5 -o generated/small
python3 -m setcover bench -a bruteforce -a example generated/small -t 30 -o results/small.csv
```

or generate on the fly (`--random N M P`, `--count` instances, seeds starting at `--seed`):

```bash
python3 -m setcover bench -a example --random 100 80 0.1 --count 10
```

Suggested axes, as listed in the subject: `n` (universe size), `m` (number of subsets),
density `p` (and so subset sizes). Vary one at a time with the others fixed, and use
several seeds per point.

### 6.3 Analysing the CSV

The CSV files are written in `results/` (git-ignored). Copy the ones used in the report
to a tracked folder so that the results can be reproduced (checklist item 8).

```python
import pandas as pd
df = pd.read_csv("results/benchmarks.csv")
ok = df[df.status == "ok"]
print(ok.groupby(["instance", "algorithm"])[["cost", "time_s", "gap_pct"]].agg(["mean", "std"]))
print(ok.groupby(["n", "algorithm"])["time_s"].mean())     # time as a function of n
```

Distinguish `known_status == "optimal"` (gap to the optimum) from `"bks"` (gap to the best
known solution only), as the subject requires. Runs with `status == "timeout"` should be
reported separately (their cost is only the best found within the limit).

---

## 7. File formats

### 7.1 OR-Library SCP (`scp*.txt`, generated instances)

Whitespace-separated integers (line breaks do not matter), 1-based indices:

```
n m                 number of elements (rows), number of subsets (columns)
c_1 ... c_m         cost of each subset (all 1 for unicost)
k_1 j j ... j       for element 1: number of subsets covering it, then their indices
...
k_n j j ... j       for element n
```

Example (the 6-element instance of section 2):

```
6 4
1 1 1 1
2 1 4
1 1
2 1 2
2 2 3
1 3
2 3 4
```

### 7.2 Steiner triple covering (`data.*`)

```
m n                 number of subsets (variables) FIRST, then number of elements (triples)
a b c               one line per element: it is covered by subsets a, b and c (1-based)
...
```

### 7.3 Solution file (`.sol`)

```
# optional comment lines
cost
j_1 j_2 ... j_cost  1-based indices of the chosen subsets
```

`read_solution` refuses a file whose announced cost differs from the number of indices.

---

## 8. Benchmark instances and reference values

Unicost instances present in `USPC-instances/` (from github.com/pinam45/USCP_instances):

| Family | Instances | Elements (n) | Subsets (m) | Density | Files |
|---|---|---|---|---|---|
| E | E.1–E.5 | 50 | 500 | 20 % | `OR-Library/scpe*.txt` |
| CLR | CLR10–CLR13 | 511–4 095 | 210–715 | 12 % | `OR-Library/scpclr*.txt` |
| CYC | CYC6–CYC11 | 240–28 160 | 192–11 264 | 0.04–2.1 % | `OR-Library/scpcyc*.txt` |
| STS | STS9–STS2187 | 12–796 797 | 9–2 187 | 0.1–33 % | `steiner-triple-covering/data.*` |

Reference values stored in `benchmarks.KNOWN`:

| Instance | Value | Status |
|---|---|---|
| E.1 – E.5 | 5 | optimal |
| CLR10 / CLR11 / CLR12 / CLR13 | 25 / 23 / 23 / 23 | bks |
| CYC6 / CYC7 / CYC8 / CYC9 / CYC10 / CYC11 | 60 / 144 / 342 / 772 / 1798 / 3968 | bks |
| STS9 / 15 / 27 / 45 / 81 / 135 / 243 | 5 / 9 / 18 / 30 / 61 / 103 / 198 | optimal |
| STS405 / STS729 / STS1215 / STS2187 | 335 / 617 / 1063 / 1963 | bks |

Sources:

- **values**: tables of the solver github.com/pinam45/USCP, the solver that goes with the
  instance repository (`code/common/include/common/data/instances/orlibrary/orlibrary.hpp`
  and `.../instances/sts.hpp`, field `BKS`);
- **"optimal" for STS9 to STS243, "bks" for STS405 and STS729**:
  `USPC-instances/steiner-triple-covering/README` (Fulkerson et al. 1974, Ratliff 1979,
  Mannino & Sassano 1995, Ostrowski et al. 2009–2010, Resende & Toso 2010);
- **"optimal" for E.1 to E.5**: `USPC-instances/OR-Library/README`, which states that the
  optimal value of each Beasley (1987) file is given in the paper;
- **CLR and CYC**: no source marks them as optimal, so they are all `bks`.

The instance repository points to Kritter et al. 2019 (*On the optimal placement of
cameras for surveillance and the underlying set cover problem*, Applied Soft Computing
74, DOI 10.1016/j.asoc.2018.10.025) for the state of the art; cite it in the report.
To fix or add a value, edit the `KNOWN` dictionary in `setcover/benchmarks.py`.

Only unicost instances are used, as the subject requires: `read_orlib` raises
`UnicostError` on a weighted file.

---

## 9. Tests

```bash
python3 -m unittest discover -s tests -v
```

`tests/test_base.py` checks: `Instance` (covering, density, input validation, uncoverable
elements), `verify` (valid, uncovered, invalid, duplicate, redundant subsets), file
round-trip, generator reproducibility / feasibility / density, `AlgoExemple`, the runner
(timeout returns the best solution recorded, invalid outputs and exceptions are detected)
and loading every benchmark file under 2 MB. It contains a tiny brute-force oracle
(`brute_force_optimum`) that you can reuse to test an exact method on small random
instances:

```python
for seed in range(20):
    inst = generate(12, 10, 0.25, seed=seed)
    assert run(get_algorithm("dp"), inst)["cost"] == brute_force_optimum(inst)
```

Add a test file per algorithm in `tests/` (`test_<name>.py`); `discover` finds it.

---

## 10. FAQ / troubleshooting

**`ModuleNotFoundError: No module named 'setcover'`** — run the command from the repository
root, not from inside `setcover/`.

**`KeyError: algorithme inconnu 'xxx'`** — the module is not imported in
`setcover/algorithms/__init__.py`, or `name` is different from what you typed.

**`ValueError: algorithme 'xxx' déjà enregistré`** — two classes use the same `name`.

**My algorithm ignores `-t`** — it never calls `ctx.check_time()`.

**Status `infeasible`** — `solve` returned a list that does not cover everything; the
`error` column lists some uncovered elements. Use `verify(instance, selected).message()`
while debugging.

**A cost below a proven optimum** — there is a bug in the algorithm, or the reference
value in `KNOWN` is wrong. Check the `gap_pct` column: it must never be negative when
`known_status` is `optimal`.

**Benchmarks not found** — the folder must be `<repo>/USPC-instances`, or set
`export USCP_INSTANCES=/path/to/instances`.

**Messages are in French** — console messages and code comments are in French; the
behaviour is the one documented here.
