# Advance Algo - Minimum Set Cover Problem

## Groupe
* Vsevolod Giovanni CINQUE
* Jughurta MEHENNI
* Mohamed-Amine BENKACEM
* Jayden TAN
* Yuhsaku NAKAI

## Langage : Python 3

Aucune dépendance externe. Les scripts se lancent avec `python3`.

## Organisation du dépôt

```
uscp/
  instance.py     # classe Instance + lecture/écriture des fichiers
  generator.py    # générateur aléatoire d'instances
  best_known.py   # meilleures solutions connues des benchmarks + evaluate()
  main.py         # vérifie le chargement de toutes les instances de benchmark
USPC-instances/
  OR-Library/               # scpe*, scpclr*, scpcyc* (unicost)
  steiner-triple-covering/  # data.9 ... data.2187
doc/              # sujet et planning du groupe
```

## Représentation d'une instance

`Instance(n, m, subsets)` dans `uscp/instance.py` :
- l'univers est `{0, ..., n-1}` ;
- `subsets[j]` est l'ensemble des éléments couverts par le sous-ensemble `j` (`0 <= j < m`) ;
- tous les coûts valent 1 (unicost) : on minimise le **nombre** de sous-ensembles choisis.

Une **solution** est une liste d'indices de sous-ensembles, par exemple `[0, 3, 7]`.

Méthodes utiles :
- `inst.is_cover(chosen)` : vrai si `chosen` couvre tout l'univers ;
- `inst.is_coverable()` : vrai si l'instance admet une solution.

## Format des fichiers d'instance

**OR-Library** (`scp*.txt`, indices 1-based) :

```
n m                 # nb d'éléments, nb de sous-ensembles
1 1 ... 1           # m coûts (tous à 1)
k  s_1 ... s_k      # pour chaque élément : nb de sous-ensembles qui le couvrent, puis leurs indices
...                 # (n blocs)
```

C'est aussi le format produit par `instance.save()` pour nos instances générées.

**Steiner** (`data.*`, indices 1-based) :

```
m n                 # attention : nb de sous-ensembles AVANT nb d'éléments
a b c               # un triplet par élément : les 3 sous-ensembles qui le couvrent
...
```

`load_any(path)` choisit le bon parseur selon le nom du fichier.

## Charger les instances

```python
from instance import load_any
inst = load_any("../USPC-instances/steiner-triple-covering/data.27")
```

```python
from generator import generate
inst = generate(n=50, m=30, density=0.1, seed=42)   # même paramètres => même instance
```

Vérifier que tous les benchmarks se chargent :

```bash
python3 uscp/main.py                  # toutes les instances
python3 uscp/main.py scpe1 data.27    # seulement celles dont le nom contient ces filtres
```

Chaque ligne affiche `n`, `m`, la taille moyenne des sous-ensembles, le temps de chargement et la référence `ref=` (voir ci-dessous).

## Meilleures solutions connues

`uscp/best_known.py` contient `BEST_KNOWN[nom_de_fichier] = (valeur, optimal_prouvé)` : la taille de la meilleure couverture connue pour chaque benchmark.

- `optimal_prouvé = True` (affiché `ref=5*`) : c'est l'optimum, on ne peut pas faire mieux. C'est le cas de `data.9` à `data.243`.
- `optimal_prouvé = False` (affiché `ref=335`) : meilleure solution connue (BKS), sans preuve d'optimalité.

Sources : le README de `USPC-instances/steiner-triple-covering/` pour les STS jusqu'à `data.729`, et la table du solveur [pinam45/USCP](https://github.com/pinam45/USCP) pour `data.1215`, `data.2187`, E, CLR et CYC. L'optimalité de E, CLR et CYC n'a pas été vérifiée : elles sont marquées `False`.

## Tester un algorithme

Un algorithme prend une `Instance` et renvoie une liste d'indices de sous-ensembles. On le contrôle avec `evaluate(inst, chosen, path)` :

```bash
cd uscp
python3 -c "
from instance import load_any
from best_known import evaluate

p = '../USPC-instances/steiner-triple-covering/data.27'
inst = load_any(p)
chosen = mon_algo(inst)            # à remplacer par votre algorithme
print(evaluate(inst, chosen, p))
"
```

Résultat, par exemple :

```
{'valid': True, 'size': 20, 'best': 18, 'optimal': True, 'gap': 11.1, 'status': 'OK'}
```

| Champ | Sens |
|---|---|
| `valid` | la solution couvre tout l'univers |
| `size` | nombre de sous-ensembles choisis |
| `best`, `optimal` | référence et indicateur d'optimum prouvé |
| `gap` | écart à la référence en % : `(size - best) / best * 100` |
| `status` | verdict, voir ci-dessous |

| `status` | Interprétation |
|---|---|
| `INVALIDE` | la solution ne couvre pas tout : **bug** |
| `SANS REF` | solution valide, mais pas de référence pour ce fichier (ex. instance générée) |
| `OK` | solution valide, taille ≥ référence : lire `gap` |
| `ALERTE` | solution valide **plus petite** que la référence : bug si `optimal` est vrai, sinon amélioration du BKS à vérifier |

**Interpréter le résultat selon le type d'algorithme :**
- **algorithmes exacts** (brute force, branch & bound, programmation dynamique) : `gap` doit valoir 0 sur les optimums prouvés. Seuls les petits benchmarks (`data.9`, `data.15`) sont à leur portée ; on les compare entre eux sur des instances générées ;
- **heuristiques** (glouton, glouton randomisé, recherche locale, recuit simulé) : `gap` mesure la qualité de la solution ; plus il est petit, mieux c'est.

## Avancement

| Milestone | État |
|---|---|
| 1. Outils communs | Langage, générateur, parseur des benchmarks et meilleures solutions connues faits. Interface commune (format de sortie, chronométrage) à faire. |
| 2. Brute force, glouton, DP, branch & bound | À faire |
| 3. Glouton randomisé, recherche locale, recuit simulé | À faire |
| 4–6. Expériences, rapport, soutenance | À faire |
