"""Lecture / écriture des fichiers d'instances et de solutions.

Formats supportés
-----------------

1. OR-Library SCP (scpe*.txt, scpclr*.txt, scpcyc*.txt, et les fichiers
   générés par ``setcover.generator``) - indices 1-based ::

       n m                  # nb d'éléments (rows), nb de sous-ensembles (columns)
       c_1 ... c_m          # coût de chaque sous-ensemble (tous à 1 en unicost)
       k  j_1 ... j_k       # pour chaque élément : nb de sous-ensembles qui le
       ...                  # couvrent puis leurs indices (n blocs)

   Les retours à la ligne ne sont pas significatifs : on lit des nombres
   les uns après les autres.

2. Steiner Triple Covering (data.9, data.15, ...) - indices 1-based ::

       nb_variables nb_triplets     # attention : sous-ensembles AVANT éléments
       a b c                        # un triplet par élément : il est couvert
       ...                          # par les sous-ensembles a, b et c

3. Solution (format maison, simple à relire à la main) ::

       # commentaires optionnels
       cost
       j_1 j_2 ... j_cost   # indices 1-based des sous-ensembles choisis
"""

import os

from .instance import Instance


class UnicostError(ValueError):
    """Le fichier décrit une instance pondérée : hors sujet pour ce projet."""


# ---------------------------------------------------------------------- #
# Instances
# ---------------------------------------------------------------------- #
def _lire_nombres(path):
    """Lit un fichier et renvoie tous les nombres qu'il contient, dans une liste."""
    nombres = []
    with open(path) as f:
        for mot in f.read().split():
            nombres.append(int(mot))
    return nombres


def _nom_par_defaut(path):
    """Nom du fichier sans le dossier et sans l'extension .txt."""
    base = os.path.basename(path)
    if base.endswith(".txt"):
        return base[:-4]
    return base


def read_orlib(path, require_unicost=True, name=None):
    """Lit un fichier au format OR-Library SCP."""
    nombres = _lire_nombres(path)

    # Les deux premiers nombres : n (éléments) et m (sous-ensembles)
    n = nombres[0]
    m = nombres[1]
    position = 2

    # Les m nombres suivants : le coût de chaque sous-ensemble
    couts = nombres[position:position + m]
    position += m
    if require_unicost:
        for c in couts:
            if c != 1:
                raise UnicostError(f"{path} : coûts != 1, instance pondérée (non unicost)")

    # subsets[j] = éléments couverts par le sous-ensemble j
    subsets = []
    for j in range(m):
        subsets.append(set())

    # Pour chaque élément : k, puis les k sous-ensembles qui le couvrent
    for e in range(n):
        k = nombres[position]
        position += 1
        for j in nombres[position:position + k]:
            subsets[j - 1].add(e)       # -1 car le fichier est 1-based
        position += k

    if position != len(nombres):
        raise ValueError(f"{path} : {len(nombres) - position} nombres en trop, fichier incohérent")

    if name is None:
        name = _nom_par_defaut(path)
    return Instance(n, subsets, name)


def read_steiner(path, name=None):
    """Lit un fichier Steiner Triple Covering (data.*)."""
    nombres = _lire_nombres(path)

    # Attention : ici m (sous-ensembles) est écrit AVANT n (éléments)
    m = nombres[0]
    n = nombres[1]
    if len(nombres) != 2 + 3 * n:
        raise ValueError(f"{path} : nombre de triplets incohérent")

    subsets = []
    for j in range(m):
        subsets.append(set())

    # Chaque élément (triplet) est couvert par 3 sous-ensembles
    for e in range(n):
        debut = 2 + 3 * e
        for j in nombres[debut:debut + 3]:
            subsets[j - 1].add(e)       # -1 car le fichier est 1-based

    if name is None:
        name = _nom_par_defaut(path)
    return Instance(n, subsets, name)


def read_instance(path, name=None):
    """Choisit le bon lecteur d'après le nom du fichier (data.* -> Steiner)."""
    if os.path.basename(path).startswith("data."):
        return read_steiner(path, name)
    return read_orlib(path, name=name)


def write_orlib(instance, path):
    """Écrit une instance au format OR-Library (lisible par ``read_orlib``)."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w") as f:
        # Ligne 1 : n et m
        f.write(f"{instance.n} {instance.m}\n")

        # Ligne 2 : les coûts, tous égaux à 1
        couts = []
        for j in range(instance.m):
            couts.append("1")
        f.write(" ".join(couts) + "\n")

        # Une ligne par élément : k puis les sous-ensembles qui le couvrent
        for cov in instance.covering:
            indices = []
            for j in cov:
                indices.append(str(j + 1))      # +1 car le fichier est 1-based
            f.write(f"{len(cov)} " + " ".join(indices) + "\n")


# ---------------------------------------------------------------------- #
# Solutions
# ---------------------------------------------------------------------- #
def write_solution(selected, path, comment=""):
    # sans doublons, dans l'ordre croissant
    sel = sorted(set(selected))
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w") as f:
        # Les commentaires commencent par #
        for ligne in comment.splitlines():
            f.write(f"# {ligne}\n")

        # Le coût, puis les indices (1-based)
        f.write(f"{len(sel)}\n")
        indices = []
        for j in sel:
            indices.append(str(j + 1))
        f.write(" ".join(indices) + "\n")


def read_solution(path):
    """Renvoie les indices 0-based. Le coût annoncé est vérifié."""
    # On garde seulement les lignes non vides qui ne sont pas des commentaires
    lignes = []
    with open(path) as f:
        for ligne in f:
            if ligne.strip() != "" and not ligne.lstrip().startswith("#"):
                lignes.append(ligne)

    nombres = []
    for mot in " ".join(lignes).split():
        nombres.append(int(mot))

    if len(nombres) == 0:
        raise ValueError(f"{path} : fichier de solution vide")

    cout = nombres[0]
    indices = nombres[1:]
    if cout != len(indices):
        raise ValueError(f"{path} : coût annoncé {cout} mais {len(indices)} indices")

    # On repasse en 0-based
    resultat = []
    for j in indices:
        resultat.append(j - 1)
    return resultat
