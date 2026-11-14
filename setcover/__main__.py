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
"""

import argparse
import os
import sys
import time

from . import benchmarks
from .algorithms import available, get_algorithm
from .generator import generate, generate_to_dir, grid
from .io import read_instance, read_solution, write_solution
from .runner import run, afficher, append_csv
from .solution import verify


# ---------------------------------------------------------------------- #
def resolve(specs):
    """Renvoie la liste des triplets (instance, valeur connue, statut), un par instance trouvée."""
    resultat = []
    for spec in specs:
        if os.path.isdir(spec):
            # dossier : toutes les instances qu'il contient
            for nom in sorted(os.listdir(spec)):
                chemin = os.path.join(spec, nom)
                if os.path.isfile(chemin):
                    resultat.append((read_instance(chemin), None, None))

        elif os.path.isfile(spec):
            # fichier : on regarde si c'est un benchmark connu
            info = benchmarks.short_name(spec)
            name = None
            known, status = None, None
            if info is not None:
                name = info[0]
                known, status = benchmarks.known_value(name)
            resultat.append((read_instance(spec, name=name), known, status))

        elif spec.upper() in benchmarks.FAMILY_ORDER:
            # famille entière (E, CLR, CYC, STS)
            for b in benchmarks.list_benchmarks([spec.upper()]):
                resultat.append((b.load(), b.known, b.status))

        else:
            # nom court de benchmark (E.1, CYC6...)
            b = benchmarks.find(spec)
            resultat.append((b.load(), b.known, b.status))
    return resultat


# ---------------------------------------------------------------------- #
def cmd_list(args):
    print("Algorithmes :", ", ".join(available()))
    print(f"\nBenchmarks ({benchmarks.DEFAULT_DIR}) :")
    for b in benchmarks.list_benchmarks():
        if b.known is not None:
            ref = f"{b.known} ({b.status})"
        else:
            ref = "inconnue"
        print(f"  {b.family:<4} {b.name:<8} réf={ref:<16} {os.path.relpath(b.path)}")


def cmd_info(args):
    for inst, known, status in resolve(args.instances):
        s = inst.stats()
        ref = ""
        if known is not None:
            ref = f"  réf={known} ({status})"
        print(f"{s['name']:<28} n={s['n']:>7} m={s['m']:>7} densité={s['density']:.4f} "
              f"|S| moy={s['subset_size_avg']:>8} freq élt=[{s['elem_freq_min']},{s['elem_freq_max']}] "
              f"faisable={s['feasible']}{ref}")


def cmd_solve(args):
    algo = get_algorithm(args.algorithm)
    instances = resolve(args.instances)
    for inst, known, status in instances:
        res = run(algo, inst, time_limit=args.time_limit, seed=args.seed,
                  known=known, known_status=status)
        afficher(res)

        selected = res["selected"]
        if args.show and selected:
            print("    sous-ensembles (1-based) :", [j + 1 for j in selected])

        if args.output and selected:
            if len(instances) == 1:
                path = args.output
            else:
                path = os.path.join(args.output, f"{inst.name}.sol")
            write_solution(selected, path,
                           comment=f"{inst.name} {algo.name} {res['time_s']:.6f}s")
            print("    solution écrite dans", path)


def cmd_verify(args):
    inst = resolve([args.instance])[0][0]
    v = verify(inst, read_solution(args.solution))
    print(v.message())
    if v.feasible:
        sys.exit(0)
    sys.exit(1)


def cmd_generate(args):
    seeds = range(args.seed, args.seed + args.count)
    paths = generate_to_dir(grid(args.n, args.m, args.p, seeds), args.out)
    print(f"{len(paths)} instance(s) écrite(s) dans {args.out}")


def cmd_bench(args):
    algos = []
    for spec in args.algorithm:
        algos.append(get_algorithm(spec))

    instances = resolve(args.instances)
    if args.random:
        n, m, p = args.random
        for seed in range(args.seed, args.seed + args.count):
            instances.append((generate(int(n), int(m), float(p), seed), None, None))

    if args.output:
        out = args.output
    else:
        out = os.path.join("results", time.strftime("bench_%Y%m%d_%H%M%S.csv"))

    for inst, known, status in instances:
        for algo in algos:
            for r in range(args.repeats):
                seed = args.seed + r        # une graine différente par répétition
                res = run(algo, inst, time_limit=args.time_limit, seed=seed,
                          known=known, known_status=status)
                afficher(res)
                append_csv(res, out, seed=seed)
    print(f"\nRésultats ajoutés à {out}")


# ---------------------------------------------------------------------- #
def main(argv=None):
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
