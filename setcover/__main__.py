"""Interface en ligne de commande : ``python -m setcover <commande> ...``

Commandes :
  list                          algorithmes et benchmarks disponibles
  info     INST...              caractéristiques d'instances
  solve    -a ALGO INST...      résout, vérifie, chronomètre (option -o solution)
  verify   INST SOLUTION        vérifie un fichier solution
  generate -n N -m M -p P ...   génère des instances aléatoires (format OR-Library)
  bench    -a ALGO [...]        campagne d'expériences -> CSV

INST peut être un chemin de fichier, un nom de benchmark (E.1, CLR10, CYC6,
STS27...) ou une famille entière (E, CLR, CYC, STS).

Paramètres d'algorithme : ``-a nom:param1=valeur,param2=valeur``.
"""

from __future__ import annotations

import argparse
import ast
import os
import sys
import time

from . import benchmarks
from .algorithms import available, get_algorithm
from .generator import generate, generate_to_dir, grid
from .io import read_instance, read_solution, write_solution
from .runner import run, run_many
from .solution import verify


# ---------------------------------------------------------------------- #
def parse_algo(spec: str):
    """'nom:k1=v1,k2=v2' -> Algorithm."""
    name, _, args = spec.partition(":")
    params = {}
    for kv in filter(None, args.split(",")):
        k, _, v = kv.partition("=")
        try:
            params[k] = ast.literal_eval(v)
        except (ValueError, SyntaxError):
            params[k] = v
    return get_algorithm(name, **params)


def resolve(specs: list[str]):
    """Itère sur (instance, valeur connue, statut) pour chaque argument INST."""
    for spec in specs:
        if os.path.isdir(spec):
            for f in sorted(os.listdir(spec)):
                p = os.path.join(spec, f)
                if os.path.isfile(p):
                    yield read_instance(p), None, None
        elif os.path.isfile(spec):
            info = benchmarks.short_name(spec)   # fichier de benchmark reconnu ?
            name = info[0] if info else None
            known, status = benchmarks.known_value(name) if name else (None, None)
            yield read_instance(spec, name=name), known, status
        elif spec.upper() in benchmarks.FAMILY_ORDER:
            for b in benchmarks.list_benchmarks([spec.upper()]):
                yield b.load(), b.known, b.status
        else:
            b = benchmarks.find(spec)
            yield b.load(), b.known, b.status


# ---------------------------------------------------------------------- #
def cmd_list(args) -> None:
    print("Algorithmes :", ", ".join(available()))
    print(f"\nBenchmarks ({benchmarks.DEFAULT_DIR}) :")
    for b in benchmarks.list_benchmarks():
        ref = f"{b.known} ({b.status})" if b.known else "inconnue"
        print(f"  {b.family:<4} {b.name:<8} réf={ref:<16} {os.path.relpath(b.path)}")


def cmd_info(args) -> None:
    for inst, known, status in resolve(args.instances):
        s = inst.stats()
        ref = f"  réf={known} ({status})" if known else ""
        print(f"{s['name']:<28} n={s['n']:>7} m={s['m']:>7} densité={s['density']:.4f} "
              f"|S| moy={s['subset_size_avg']:>8} freq élt=[{s['elem_freq_min']},{s['elem_freq_max']}] "
              f"faisable={s['feasible']}{ref}")


def cmd_solve(args) -> None:
    algo = parse_algo(args.algorithm)
    for inst, known, status in resolve(args.instances):
        res = run(algo, inst, time_limit=args.time_limit, seed=args.seed,
                  known=known, known_status=status)
        print(res.short())
        if res.error:
            print("   ", res.error)
        if args.show:
            print("    sous-ensembles (1-based) :", [j + 1 for j in res.selected])
        if args.output and res.selected:
            path = args.output if len(args.instances) == 1 else os.path.join(args.output, f"{inst.name}.sol")
            write_solution(res.selected, path, comment=f"{inst.name} {algo.label} {res.time_s:.6f}s")
            print("    solution écrite dans", path)


def cmd_verify(args) -> None:
    inst, _, _ = next(resolve([args.instance]))
    v = verify(inst, read_solution(args.solution))
    print(v.message())
    sys.exit(0 if v.feasible else 1)


def cmd_generate(args) -> None:
    seeds = range(args.seed, args.seed + args.count)
    paths = generate_to_dir(grid(args.n, args.m, args.p, seeds), args.out)
    print(f"{len(paths)} instance(s) écrite(s) dans {args.out}")


def cmd_bench(args) -> None:
    algos = [parse_algo(a) for a in args.algorithm]
    instances = list(resolve(args.instances))
    if args.random:
        n, m, p = args.random
        seeds = range(args.seed, args.seed + args.count)
        instances += [(generate(int(n), int(m), float(p), s), None, None) for s in seeds]
    out = args.output or os.path.join("results", time.strftime("bench_%Y%m%d_%H%M%S.csv"))
    run_many(algos, instances, repeats=args.repeats, time_limit=args.time_limit,
             base_seed=args.seed, csv_path=out)
    print(f"\nRésultats ajoutés à {out}")


# ---------------------------------------------------------------------- #
def main(argv=None) -> None:
    p = argparse.ArgumentParser(prog="python -m setcover", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list").set_defaults(func=cmd_list)

    q = sub.add_parser("info")
    q.add_argument("instances", nargs="+")
    q.set_defaults(func=cmd_info)

    q = sub.add_parser("solve")
    q.add_argument("-a", "--algorithm", required=True)
    q.add_argument("instances", nargs="+")
    q.add_argument("-t", "--time-limit", type=float, default=None)
    q.add_argument("--seed", type=int, default=0)
    q.add_argument("--show", action="store_true", help="affiche les sous-ensembles choisis")
    q.add_argument("-o", "--output", help="fichier (ou dossier si plusieurs instances) de solution")
    q.set_defaults(func=cmd_solve)

    q = sub.add_parser("verify")
    q.add_argument("instance")
    q.add_argument("solution")
    q.set_defaults(func=cmd_verify)

    q = sub.add_parser("generate")
    q.add_argument("-n", type=int, nargs="+", required=True, help="taille(s) de l'univers")
    q.add_argument("-m", type=int, nargs="+", required=True, help="nombre(s) de sous-ensembles")
    q.add_argument("-p", type=float, nargs="+", required=True, help="densité(s)")
    q.add_argument("--seed", type=int, default=0)
    q.add_argument("--count", type=int, default=1, help="instances par combinaison (graines successives)")
    q.add_argument("-o", "--out", default="generated")
    q.set_defaults(func=cmd_generate)

    q = sub.add_parser("bench")
    q.add_argument("-a", "--algorithm", action="append", required=True)
    q.add_argument("instances", nargs="*", default=[])
    q.add_argument("--random", nargs=3, metavar=("N", "M", "P"),
                   help="ajoute des instances aléatoires générées à la volée")
    q.add_argument("--count", type=int, default=5, help="nb d'instances aléatoires")
    q.add_argument("-r", "--repeats", type=int, default=1)
    q.add_argument("-t", "--time-limit", type=float, default=None)
    q.add_argument("--seed", type=int, default=0)
    q.add_argument("-o", "--output", help="CSV de sortie (défaut : results/bench_<date>.csv)")
    q.set_defaults(func=cmd_bench)

    args = p.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
