"""Base commune du projet Minimum (Unicost) Set Cover.

Modules :
  instance    – classe ``Instance`` (univers, sous-ensembles, bitmasks...)
  io          – lecture/écriture OR-Library, Steiner, solutions
  generator   – générateur aléatoire (n, m, densité, graine)
  solution    – ``verify`` : vérification indépendante des solutions
  benchmarks  – catalogue E / CLR / CYC / STS + valeurs optimales / BKS
  algorithms  – interface ``Algorithm`` + registre + algorithmes
  runner      – exécution chronométrée, vérifiée, export CSV

Usage rapide en Python ::

    from setcover import generate, get_algorithm, run
    inst = generate(n=30, m=20, density=0.2, seed=1)
    print(run(get_algorithm("example"), inst).short())
"""

from .instance import Instance
from .io import read_instance, write_orlib, read_solution, write_solution
from .generator import generate
from .solution import verify, is_cover
from .algorithms import Algorithm, RunContext, register, get_algorithm, available
from .runner import run, run_many, RunResult
from . import benchmarks

__all__ = ["Instance", "read_instance", "write_orlib", "read_solution", "write_solution",
           "generate", "verify", "is_cover", "Algorithm", "RunContext", "register",
           "get_algorithm", "available", "run", "run_many", "RunResult", "benchmarks"]
