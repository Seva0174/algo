# Advanced Algorithms – Minimum Set Cover Problem

Master DSC/MLDM project, 2026–2027: algorithms for the **unicost Minimum Set Cover
Problem** and an experimental study of their running time and solution quality.

## Group

* Vsevolod Giovanni CINQUE
* Jughurta MEHENNI
* Mohamed-Amine BENKACEM
* Jayden TAN
* Yuhsaku NAKAI

## Language

Python 3.9 or newer, no external dependency. Every command is run from the repository
root with `python3`.

## Repository layout

```
setcover/            common framework (Python package) + algorithms
  algorithms/        one file per algorithm (example.py, bruteforce.py, ...)
tests/               unit tests
USPC-instances/      benchmark instances (OR-Library E/CLR/CYC, Steiner triple covering)
doc/                 project subject, group description, algorithm write-ups
results/             CSV files produced by experiments (git-ignored)
DOCUMENTATION.md     full documentation of the framework
```

## Quick start

```bash
python3 -m setcover list                              # algorithms and benchmarks available
python3 -m setcover info E CYC6                       # characteristics of instances
python3 -m setcover solve -a bruteforce STS9 --show   # solve, verify and time one instance
python3 -m setcover bench -a bruteforce STS9 STS15 --random 20 15 0.2 --count 5 -r 3 -t 60 \
        -o results/bruteforce.csv                     # experiment campaign -> CSV
python3 -m unittest discover -s tests                 # run the tests
```

To add an algorithm, copy `setcover/algorithms/example.py`, write its `solve` method and
import it in `setcover/algorithms/__init__.py`. See [DOCUMENTATION.md](DOCUMENTATION.md),
section 5.

## Progress

| Milestone | Status |
|---|---|
| 1. Common tools (instances, generator, benchmarks, verification, runner, CSV) | Done |
| 2. Brute force, greedy, dynamic programming, branch & bound | Brute force done, others to do |
| 3. Randomized greedy, local search, other methods | To do |
| 4–6. Experiments, report, defense | To do |
