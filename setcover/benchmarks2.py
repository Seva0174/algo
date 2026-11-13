"""Catalogue des instances de benchmark unicost et de leurs valeurs connues.

Les fichiers sont cherchés dans ``<racine du dépôt>/USPC-instances`` (ou dans
le dossier donné par la variable d'environnement ``USCP_INSTANCES``).

Chaque instance a un nom court (celui du tableau du sujet / du dépôt
pinam45/USCP_instances : E.1, CLR10, CYC6, STS27...) et une valeur de
référence avec son statut :

* ``optimal`` : optimum prouvé -> on peut parler d'écart à l'optimum ;
* ``bks``     : meilleure solution connue seulement (best known solution) ;
* ``None``    : valeur inconnue / non renseignée.

Le sujet demande de distinguer clairement ces cas dans l'évaluation.

Sources : README du dossier steiner-triple-covering pour STS ; Grossman & Wool
(1997) et Kritter et al. (2019, Applied Soft Computing 74) pour E, CLR, CYC.
**À revérifier dans [Kritter2019] avant de les citer dans le rapport.**
"""

import glob
import os

from .io2 import read_instance

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DIR = os.environ.get("USCP_INSTANCES", os.path.join(ROOT, "USPC-instances"))

# nom court -> (valeur de référence, statut)
KNOWN = {
    # OR-Library E (Beasley 1987), unicost, 50 éléments x 500 sous-ensembles
    "E.1": (5, "optimal"), "E.2": (5, "optimal"), "E.3": (5, "optimal"),
    "E.4": (5, "optimal"), "E.5": (5, "optimal"),
    # CLR (Grossman & Wool 1997)
    "CLR10": (25, "optimal"), "CLR11": (23, "bks"),
    "CLR12": (23, "bks"), "CLR13": (23, "bks"),
    # CYC (Grossman & Wool 1997)
    "CYC6": (60, "optimal"), "CYC7": (144, "optimal"), "CYC8": (342, "bks"),
    "CYC9": (772, "bks"), "CYC10": (1798, "bks"), "CYC11": (4076, "bks"),
    # Steiner Triple Covering (README du dossier steiner-triple-covering)
    "STS9": (5, "optimal"), "STS15": (9, "optimal"), "STS27": (18, "optimal"),
    "STS45": (30, "optimal"), "STS81": (61, "optimal"), "STS135": (103, "optimal"),
    "STS243": (198, "optimal"), "STS405": (335, "bks"), "STS729": (617, "bks"),
}

# Ordre d'affichage des familles
FAMILY_ORDER = ["E", "CLR", "CYC", "STS"]


class Benchmark:
    def __init__(self, name, family, path, known, status):
        self.name = name        # nom court, ex. "CYC6"
        self.family = family    # E, CLR, CYC ou STS
        self.path = path        # chemin du fichier
        self.known = known      # valeur de référence (ou None)
        self.status = status    # "optimal", "bks" ou None

    def load(self):
        """Lit le fichier et renvoie l'Instance correspondante."""
        return read_instance(self.path, self.name)


def short_name(path):
    """Fichier -> (nom court, famille). Renvoie None si le fichier n'est pas reconnu.

    Exemples : scpe1.txt -> ("E.1", "E")     scpclr10.txt -> ("CLR10", "CLR")
               scpcyc6.txt -> ("CYC6", "CYC")   data.27 -> ("STS27", "STS")
    """
    base = os.path.basename(path)

    # scpe<numéro>.txt
    if base.startswith("scpe") and base.endswith(".txt"):
        numero = base[len("scpe"):-len(".txt")]
        if numero.isdigit():
            return "E." + numero, "E"

    # scpclr<numéro>.txt
    if base.startswith("scpclr") and base.endswith(".txt"):
        numero = base[len("scpclr"):-len(".txt")]
        if numero.isdigit():
            return "CLR" + str(int(numero)), "CLR"

    # scpcyc<numéro>.txt
    if base.startswith("scpcyc") and base.endswith(".txt"):
        numero = base[len("scpcyc"):-len(".txt")]
        if numero.isdigit():
            return "CYC" + str(int(numero)), "CYC"

    # data.<numéro>
    if base.startswith("data."):
        numero = base[len("data."):]
        if numero.isdigit():
            return "STS" + numero, "STS"

    return None


def _cle_de_tri(benchmark):
    """Pour trier : d'abord par famille, puis par numéro (E.2 avant E.10)."""
    chiffres = ""
    for caractere in benchmark.name:
        if caractere.isdigit():
            chiffres += caractere
    if chiffres == "":
        numero = 0
    else:
        numero = int(chiffres)
    return (FAMILY_ORDER.index(benchmark.family), numero)


def list_benchmarks(families=None, directory=DEFAULT_DIR):
    """Toutes les instances trouvées, triées par famille puis par taille.

    ``families`` : liste de familles à garder, par exemple ["E", "CLR"].
    None = toutes les familles.
    """
    chemins = glob.glob(os.path.join(directory, "**", "*"), recursive=True)

    trouves = []
    for chemin in chemins:
        info = short_name(chemin)
        if info is None:
            continue            # fichier non reconnu : on l'ignore
        name = info[0]
        family = info[1]

        if families is not None and family not in families:
            continue            # famille non demandée

        if name in KNOWN:
            known, status = KNOWN[name]
        else:
            known, status = None, None
        trouves.append(Benchmark(name, family, chemin, known, status))

    return sorted(trouves, key=_cle_de_tri)


def find(name, directory=DEFAULT_DIR):
    """Cherche une instance par nom court, sans tenir compte des majuscules (ex. "cyc6", "E.1")."""
    for b in list_benchmarks(directory=directory):
        if b.name.lower() == name.lower():
            return b
    raise KeyError(f"benchmark '{name}' introuvable dans {directory}")


def known_value(name):
    """Renvoie (valeur de référence, statut), ou (None, None) si inconnue."""
    if name in KNOWN:
        return KNOWN[name]
    return None, None
