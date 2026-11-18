# Randomized Greedy Algorithm for Set Cover

File: `setcover/algorithms/greedy_random.py` — run with
`python3 -m setcover solve -a greedy-random E.1 --seed 3 --show`.

This is the "randomized greedy search" listed in Section 2 of the project statement as an
additional heuristic. It is a variant of the classic greedy algorithm (see `doc/Greedy.md`).

## 1. The idea

The classic greedy always picks the subset with the largest gain, so it always returns the
**same** solution. If its first choices are locally best but globally bad (see Section 6 of
`Greedy.md`), nothing can fix it, and running it again changes nothing.

The randomized greedy keeps the same construction but adds randomness to the choice:

> At each round, build a short list of **good** candidates (gain close to the best one) and
> pick one of them **at random**.

Each run therefore builds a different cover. Running it several times and keeping the best
cover gives a chance to beat the classic greedy.

This is the construction phase of GRASP (*Greedy Randomized Adaptive Search Procedure*,
Feo & Resende), here **without** the local-search phase.

**Step by step.** The algorithm repeats the following round until every element is covered:

1. Find `gain_max`, the gain of the best subset (the one that covers the most uncovered
   elements).
2. Compute a threshold: `seuil = (1 − alpha) · gain_max`.
3. Keep every subset whose gain is at least `seuil` (and greater than 0): this is the
   **candidate list** (RCL). The best subset is always in it.
4. Pick **one** subset of the list at random and add it to the solution.
5. Update the gains as in the classic greedy: the newly covered elements are marked, and
   every subset containing them loses 1 gain per element.

Only steps 2 to 4 differ from the classic greedy, which would simply take the best subset at
step 2. The parameter `alpha` (detailed in Section 2) says how far below the best gain a
subset may be and still be a candidate.

## 2. The Restricted Candidate List (RCL)

With `gain_max` the best gain of the round and a parameter `alpha ∈ [0, 1]`:

```
RCL = { j : gain[j] > 0   and   gain[j] ≥ (1 − alpha) · gain_max }
```

| `alpha` | RCL | behaviour |
|---|---|---|
| 0 | only subsets with gain = `gain_max` | classic greedy, ties broken at random |
| small (0.1 – 0.3) | near-best subsets | mostly greedy, some diversity |
| 1 | every subset with gain > 0 | purely random choice |

`alpha` is the slider between **quality** (greedy) and **diversity** (random). The test
`gain[j] > 0` prevents choosing a subset that covers nothing new.

## 3. Pseudocode

```
best ← none
repeat nb_essais times:
    covered  ← ∅
    solution ← []
    while covered ≠ universe:
        gain_max ← max_j gain(S_j)
        if gain_max = 0: fail                         # infeasible instance
        RCL ← { j : gain(S_j) > 0 and gain(S_j) ≥ (1 − alpha) · gain_max }
        j* ← random element of RCL
        append j* to solution
        covered ← covered ∪ S_j*
    if |solution| < |best|: best ← solution
return best
```

## 4. Implementation

The construction reuses the structures of the classic greedy: `gain[j]`, `covered[e]`,
`nb_non_couverts`, and the incremental update through `instance.covering[e]` (each
element/subset pair is processed once). Only the choice step changes:

1. one scan of `gain` gives `gain_max`;
2. a second scan builds the list `candidats` (the RCL);
3. `ctx.rng.choice(candidats)` picks the subset.

| Parameter | Default | Role |
|---|---|---|
| `alpha` | 0.3 | RCL width (class attribute) |
| `nb_essais` | 1 | number of independent constructions; the best cover is kept |

`ctx.rng` is the random generator provided by the framework, seeded by `--seed`: **same seed
⇒ same result**. With `bench --repeats R`, the runs use seeds `seed, seed+1, …`, which gives
the spread (min / mean / standard deviation) needed for error bars.

## 5. Worked example

Same instance as Section 6 of `Greedy.md`, universe `{0..5}`:

```
S0 = {0,1,2,3}     S1 = {0,1,4}     S2 = {2,3,5}
```

Round 1: `gain = [4, 3, 3]`, `gain_max = 4`. With `alpha = 0.3` the threshold is
`0.7 × 4 = 2.8`, so **all three** subsets are candidates (each has probability 1/3).

- If `S0` is drawn: same as the classic greedy, cost **3**.
- If `S1` is drawn: `gain = [2, 0, 3]`, threshold `2.1`, RCL = `{S2}`; `S2` is taken. Cost
  **2** = optimum.
- If `S2` is drawn: symmetric, cost **2** = optimum.

So a single run finds the optimum with probability 2/3, whereas the classic greedy never
does. With `alpha = 0.2` the threshold is `3.2`, RCL = `{S0}` in round 1, and we get the
classic greedy back: `alpha` controls how much the algorithm is allowed to deviate.

## 6. Complexity and guarantee

**Time per construction: O(nnz + k·m)**, the same order as the classic greedy: a round costs
two scans of O(m) (maximum, then RCL) and O(1) for the draw; gain updates are O(nnz) in
total. Best case `k = 1`, worst case `k = n`, as for the classic greedy. In practice `k` is
larger (the choices are less greedy), so one run is slightly slower, especially for a large
`alpha`.

**Total time: `nb_essais × O(nnz + k·m)`.** This repetition is the real cost of the method.

**Memory:** O(nnz + n + m), the same as the classic greedy.

**Guarantee.** There is no useful guarantee on one run for large `alpha` (for `alpha = 1`
the choice is random). For `alpha < 1`, a simple argument gives a weaker bound than the
classic greedy: a chosen subset has gain at least `(1 − alpha) · gain_max`, and `gain_max`
is at least `r / OPT` when `r` elements remain uncovered. So `r` shrinks by a factor at least
`(1 − (1 − alpha)/OPT)` per round, which leads to

```
k ≤ OPT · (1 + ln(n / OPT) / (1 − alpha))
```

This is our own derivation (not taken from a reference): it shows the cost cannot be
arbitrarily bad for `alpha < 1`, but it degrades as `alpha → 1`. For `alpha = 0` the usual
guarantee `H(d) × OPT` still holds, since any tie-breaking is allowed. The algorithm is
**not exact** (`exact = False`).

## 7. Implementation details

- **Ties at `alpha = 0`**: broken at random, unlike the classic greedy (smallest index).
- **Infeasible instance**: if `gain_max = 0` while elements remain, a `ValueError` is raised.
- **Time limit**: `ctx.check_time()` at every round, and `ctx.improve()` after each finished
  construction, so the best cover found so far is returned if the limit is reached.
- **Statistics**: `ctx.stats["alpha"]` and `ctx.stats["essais"]`.
- **Validation**: `alpha` outside `[0, 1]` raises a `ValueError`.
- **No local search**: a possible improvement is to remove redundant subsets from each
  cover (see `Greedy.md`, Section 8) before comparing covers.

## 8. Observed results

Gap with respect to the optimum ("optimal") or the best known solution ("bks"). Each cell
shows `min / mean / max` of the cost over **30 runs** (one construction per run, seeds
0 – 29). Timings are per run, measured in Python, and only indicative.

| Instance | Ref | Greedy | `alpha` = 0.1 | `alpha` = 0.3 | `alpha` = 0.6 | Time / run |
|---|---|---|---|---|---|---|
| E.4 | 5 (optimal) | 6 | 5 / 5.8 / 6 | 6 / 6.7 / 8 | 9 / 10.0 / 11 | ~1 ms |
| CLR10 | 25 (bks) | 33 | 31 / 31.9 / 33 | 31 / 33.3 / 36 | 36 / 40.2 / 44 | ~2 ms |
| CLR13 | 23 (bks) | 32 | 31 / 32.2 / 34 | 34 / 35.2 / 37 | 41 / 45.3 / 48 | ~27 ms |
| CYC6 | 60 (bks) | 60 | 64 / 67.4 / 71 | 68 / 70.9 / 74 | 78 / 83.6 / 89 | ~2 ms |
| STS27 | 18 (optimal) | 19 | 19 / 19.0 / 19 | 18 / 18.9 / 19 | 19 / 19.9 / 21 | < 1 ms |
| STS243 | 198 (optimal) | 211 | 209 / 210.9 / 211 | 206 / 209.3 / 211 | 214 / 217.2 / 221 | ~11 ms |

Best cover over **30 constructions** in one run (`nb_essais = 30`, seed 0), compared with the
classic greedy:

| Instance | Greedy | `alpha` = 0.1 | `alpha` = 0.3 |
|---|---|---|---|
| E.4 | 6 | **5** (optimal) | 6 |
| CLR10 | 33 (+32 %) | **30** (+20 %) | 31 (+24 %) |
| CLR13 | 32 (+39 %) | **30** (+30 %) | 33 (+43 %) |
| CYC6 | **60** (0 %) | 65 (+8.3 %) | 66 (+10 %) |
| STS27 | 19 (+5.6 %) | 19 (+5.6 %) | **18** (optimal) |
| STS243 | 211 (+6.6 %) | 209 (+5.6 %) | **207** (+4.5 %) |

**Reading**:

- A **single run** is almost never better than the classic greedy, and its **mean gets worse
  as `alpha` grows**: with `alpha = 0.6` the cost is 20 – 40 % above the greedy on most
  instances. Large `alpha` is a bad choice.
- **Repeating** the construction helps: with `alpha = 0.1` or `0.3`, the best of 30 beats
  the greedy on E.4, CLR10, CLR13, STS27 and STS243. The gain is modest (1 – 3 units), and
  the optimum is reached only on the easiest instances (E.4, STS27).
- On **CYC6** the classic greedy is already at the best known value, and randomization only
  makes it worse: the method does not always help.
- The best `alpha` depends on the instance (0.1 on E.4, CLR, 0.3 on STS), so it should be
  tuned in the experimental study.
- The cost is `nb_essais` times the greedy time: the gain has to be weighed against it.

The experiments above are a first sample (a single series of seeds, no confidence interval).
The final study should use more instances, more seeds and error bars.

## 9. Comparison with the classic greedy

### 9.1 Two levels in the code

| Level | Code | Role |
|---|---|---|
| **One construction** | `construire` | the randomized greedy itself: threshold, RCL, random draw |
| **Repetition** | the loop in `solve` | `nb_essais` constructions, the best cover is kept |

The repetition is part of the method (GRASP builds several solutions and keeps the best),
but it is only an outer loop: it calls `construire` several times and compares the sizes.
It is also what makes the randomness useful, because a single randomized construction is
usually worse than the classic greedy (Section 8).

### 9.2 Two ways to use it

| Mode | Setting | Question it answers |
|---|---|---|
| **Single construction** | `nb_essais = 1` (default), repeated by `bench --repeats R` with seeds `seed … seed+R−1` | how are the results distributed (min, mean, standard deviation)? |
| **Best of N** | `nb_essais = N` | can we beat the classic greedy by spending more time? |

`nb_essais = 1` is the default on purpose: each run of the benchmark is then one
construction, which gives the spread and the error bars asked by the checklist (question 6).
The "best of N" mode is the one to compare with the classic greedy on quality.

### 9.3 Classic greedy vs randomized greedy

| | Classic greedy | Randomized greedy |
|---|---|---|
| Choice at each round | best gain (smallest index on ties) | random among the RCL |
| Result | always the same | depends on the seed |
| Variance over runs | none | grows with `alpha` |
| Parameters | none | `alpha`, `nb_essais`, seed |
| Time complexity (one run) | O(nnz + k·m) | O(nnz + k·m) |
| Total time | O(nnz + k·m) | `nb_essais` × O(nnz + k·m) |
| Guarantee | `H(d) × OPT` | `H(d) × OPT` at `alpha = 0`, weaker bound for `alpha < 1`, none at `alpha = 1` |
| Quality of one run | good | usually worse; worse as `alpha` grows |
| Quality of the best of N | cannot improve | can be better, not guaranteed (CYC6) |
| Extra time is useful | no | yes |

Here `n` is the number of elements, `m` the number of subsets, `nnz` the sum of the subset
sizes and `k` the number of chosen subsets (`1 ≤ k ≤ min(n, m)`, so the worst case is
O(nnz + n·m)). The two methods have the **same complexity**: only `k` changes in practice
(the randomized greedy usually needs more rounds), and the randomized version is multiplied
by `nb_essais` when it repeats the construction.

In short: the classic greedy is cheap, predictable and a good default; the randomized greedy
trades **extra computing time** for a chance of a better cover.

### 9.4 How to compare them fairly

The two methods do not use the same amount of time, so comparing a single greedy run with the
best of N constructions on quality alone would favour the randomized version. A fair
protocol (checklist, question 10):

1. run the classic greedy once and record its cost and time `t_g`;
2. run the randomized greedy as a **single construction** with `R` seeds, and report min,
   mean and standard deviation of the cost (this measures the variability);
3. run the **best of N** and report the cost **together with its total time** (about
   `N × t_r`, with `t_r` the time of one construction), or choose `N` so that the total time
   matches a stated budget;
4. use the same instances, the same machine and the same time limit for every method, and
   compare the gaps to the optimum or to the best known solution.

The framework allows an equal-budget comparison: `ctx.improve()` is called after each finished
construction, so if the time limit (`-t`) is reached, the runner returns the best cover found
so far. This usage has not been tested yet.

## 10. References

- Wikipedia, *Set cover problem*: <https://en.wikipedia.org/wiki/Set_cover_problem>. It
  describes the greedy algorithm and, for the weighted case, other randomized methods
  (randomized rounding of the LP relaxation). **Randomized rounding is a different
  technique, not implemented here.**
- T. A. Feo and M. G. C. Resende, *A probabilistic heuristic for a computationally difficult
  set covering problem*, Operations Research Letters, 8(2), 67–71, 1989. First use of a
  randomized greedy construction for set covering.
- T. A. Feo and M. G. C. Resende, *Greedy Randomized Adaptive Search Procedures*, Journal of
  Global Optimization, 6, 109–133, 1995. The RCL scheme with parameter `alpha`.
- D. S. Johnson, *Approximation algorithms for combinatorial problems*, Journal of Computer
  and System Sciences, 9(3), 1974 (guarantee of the classic greedy, used at `alpha = 0`).
