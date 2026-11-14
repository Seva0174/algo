# Greedy Algorithm for Set Cover

File: `setcover/algorithms/greedy.py` — run with
`python3 -m setcover solve -a greedy E.1 --show`.

## 1. The problem

We are given a universe `{0, …, n-1}` and `m` subsets `S_0, …, S_{m-1}`. The goal is to find
the **smallest number of subsets whose union is the whole universe** (every subset costs 1).
The problem is NP-hard: no fast algorithm is known that always finds the optimum.

## 2. The idea

Instead of trying everything (brute force), the solution is built step by step. At each step
we make the choice that looks best **at that moment**, and we never go back:

> While some elements are still uncovered, pick the subset that covers
> **the largest number of still-uncovered elements**.

An important point: we do **not** pick "the largest subset". A subset of 100 elements that
are all already covered brings nothing, while a small subset of 3 brand-new elements is more
useful. So we compare **gains**, not sizes:

```
gain(S_j) = |S_j \ (already covered elements)|
```

## 3. Pseudocode

```
covered  ← ∅
solution ← []
while covered ≠ universe:
    j* ← argmax_j gain(S_j)          # ties: smallest index
    if gain(S_j*) = 0: fail           # infeasible instance
    append j* to solution
    covered ← covered ∪ S_j*
return solution
```

## 4. Efficient implementation

Recomputing `|S_j \ covered|` for every `j` at every round would be expensive. Instead, three
structures are maintained:

| Variable | Role |
|---|---|
| `gain[j]` | number of uncovered elements of subset `j` (initially `|S_j|`) |
| `covered[e]` | `True` if element `e` is already covered |
| `nb_non_couverts` | counter that stops the loop when it reaches 0 |

At each round:

1. **Choice**: scan `gain` to find the index of the maximum gain.
2. **Update**: for every element `e` of the chosen subset that was not yet covered, set
   `covered[e] = True`, decrement `nb_non_couverts`, then subtract 1 from the `gain` of
   **every** subset containing `e` (precomputed list `instance.covering[e]`).

No set intersection is ever computed: each (element, subset) pair is processed **exactly
once** over the whole run, at the moment the element becomes covered.

## 5. Worked example

Universe `{0..7}`, three subsets:

```
S0 = {0,1,2,3,4,5}     S1 = {0,1,2,3,6}     S2 = {6,7}
```

| Round | `gain` `[S0, S1, S2]` | choice | newly covered |
|---|---|---|---|
| start | `[6, 5, 2]` | | |
| 1 | `[6, 5, 2]` | `S0` (gain 6) | 0,1,2,3,4,5 |
| 2 | `[0, 1, 2]` | `S2` (gain 2) | 6,7 |

Result: `[S0, S2]`, cost 2. In round 2, `S1` (size 5) is much larger than `S2` (size 2), but it
only brings one new element (6) versus 2 for `S2`. Choosing "the largest subset" would have
been wrong, which is why we follow the gains. This case is tested in `tests/test_base.py`
(`test_uses_uncovered_gain_not_raw_size`).

## 6. Greedy is not optimal

Universe `{0..5}`:

```
S0 = {0,1,2,3}     S1 = {0,1,4}     S2 = {2,3,5}
```

- Greedy: `S0` (gain 4); `{4,5}` remains; `S1` and `S2` both have gain 1, so `S1` is taken
  (smallest index), then `S2` for element 5. Cost **3**.
- Optimum: `S1 + S2` already cover everything. Cost **2**.

The first choice, `S0`, was the best locally but bad globally. Since greedy never backtracks,
the mistake stays.

## 7. Complexity and guarantee

**Time: O(nnz + k·m)**, where `nnz` is the sum of the subset sizes and `k` the number of
chosen subsets (`k ≤ min(n, m)`).

- initialising `gain`: O(m);
- gain updates: O(nnz) in total (each element/subset pair once);
- maximum search: O(m) per round, so O(k·m) overall.

The maximum search dominates when `m` is large. A priority queue with lazy updates would
bring this part down to about O(nnz · log m), at the cost of code that is harder to explain.

**Memory: O(nnz + n + m)** (the `covering`, `gain` and `covered` lists).

**Approximation guarantee** (Johnson, 1974; Chvátal, 1979):

```
cost(greedy) ≤ H(d) × optimum,      H(d) = 1 + 1/2 + … + 1/d ≤ ln(d) + 1
```

where `d` is the size of the largest subset. Greedy can therefore never be arbitrarily far
from the optimum, and this ratio is essentially the best a polynomial-time algorithm can
achieve unless P = NP (Dinur & Steurer, 2014; see the Wikipedia page below). The algorithm is
still **not exact**: `exact = False` in the code.

## 8. Implementation details

- **Ties**: the comparison is strict (`gain[j] > gain[best]`), so on equal gain the smallest
  index is kept. The result is **deterministic** and reproducible (no seed needed).
- **Infeasible instance**: if the maximum gain is 0 while elements remain, no subset can
  cover them; a `ValueError` is raised (the runner reports `status=error`).
- **Time limit**: `ctx.check_time()` is called at every round.
- **Statistic**: `ctx.stats["iterations"]` = number of chosen subsets.
- **Redundancy**: a greedy cover may contain a subset that became useless (all its elements
  are covered by later choices). `verify` reports them in `redundant`. Removing them is a
  possible improvement (a greedy variant).

## 9. Observed results

Gap with respect to the optimum ("optimal") or the best known solution ("bks").

| Instance | Greedy cost | Reference | Gap | Time |
|---|---|---|---|---|
| E.1 – E.3, E.5 | 5 | 5 (optimal) | 0 % | < 1 ms |
| E.4 | 6 | 5 (optimal) | +20 % | < 1 ms |
| CLR10 | 33 | 25 (bks) | +32 % | ~1 ms |
| CLR13 | 32 | 23 (bks) | +39 % | ~25 ms |
| CYC6 | 60 | 60 (bks) | 0 % | < 1 ms |
| CYC11 | 4304 | 3968 (bks) | +8.5 % | ~2 s |
| STS27 | 19 | 18 (optimal) | +5.6 % | < 1 ms |
| STS243 | 211 | 198 (optimal) | +6.6 % | ~4 ms |
| STS2187 | 2059 | 1963 (bks) | +4.9 % | ~0.4 s |

**Reading**: greedy is very fast and often close to the optimum (0 to 10 % on E, CYC and
STS), but it is clearly worse on the **CLR** family (30 to 39 %). These instances are known
to be hard for heuristics; the reason remains to be checked in the experimental study (for
example by looking at the distribution of gains). Timings are measured in Python and are only
indicative.

## 10. References

- Wikipedia, *Set cover problem* — problem definition, greedy algorithm section and
  inapproximability results: <https://en.wikipedia.org/wiki/Set_cover_problem>
- The Modern SDE, *Set Cover Problem: Greedy Approximation Algorithm and the ln n Proof*
  (DSA Course L195), YouTube video: <https://www.youtube.com/watch?v=MoHb5RCKJbU>
- D. S. Johnson, *Approximation algorithms for combinatorial problems*, Journal of Computer
  and System Sciences, 9(3), 1974.
- V. Chvátal, *A Greedy Heuristic for the Set-Covering Problem*, Mathematics of Operations
  Research, 4(3), 1979.
- I. Dinur and D. Steurer, *Analytical approach to parallel repetition*, STOC 2014
  (inapproximability of Set Cover within (1 − o(1)) ln n).
