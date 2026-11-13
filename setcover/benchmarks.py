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

from __future__ import annotations

import glob
import os
import re
from dataclasses import dataclass

from .instance import Instance
from .io import read_instance

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DIR = os.environ.get("USCP_INSTANCES", os.path.join(ROOT, "USPC-instances"))

# nom court -> (valeur de référence, statut)
KNOWN: dict[str, tuple[int, str]] = {
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


@dataclass
class Benchmark:
    name: str            # nom court, ex. "CYC6"
    family: str          # E, CLR, CYC, STS
    path: str
    known: int | None    # valeur de référence
    status: str | None   # "optimal", "bks" ou None

    def load(self) -> Instance:
        return read_instance(self.path, name=self.name)


def short_name(path: str) -> tuple[str, str] | None:
    """Fichier -> (nom court, famille). None si fichier non reconnu."""
    base = os.path.basename(path)
    if m := re.fullmatch(r"scpe(\d+)\.txt", base):
        return f"E.{m[1]}", "E"
    if m := re.fullmatch(r"scpclr(\d+)\.txt", base):
        return f"CLR{int(m[1])}", "CLR"
    if m := re.fullmatch(r"scpcyc(\d+)\.txt", base):
        return f"CYC{int(m[1])}", "CYC"
    if m := re.fullmatch(r"data\.(\d+)", base):
        return f"STS{m[1]}", "STS"
    return None


FAMILY_ORDER = ["E", "CLR", "CYC", "STS"]


def list_benchmarks(families: list[str] | None = None, directory: str = DEFAULT_DIR) -> list[Benchmark]:
    """Toutes les instances trouvées, triées par famille puis par taille."""
    paths = glob.glob(os.path.join(directory, "**", "*"), recursive=True)
    out = []
    for p in paths:
        info = short_name(p)
        if info is None:
            continue
        name, fam = info
        if families and fam not in families:
            continue
        known, status = KNOWN.get(name, (None, None))
        out.append(Benchmark(name, fam, p, known, status))

    def key(b: Benchmark):
        num = int(re.sub(r"\D", "", b.name) or 0)
        return (FAMILY_ORDER.index(b.family), num)
    return sorted(out, key=key)


def find(name: str, directory: str = DEFAULT_DIR) -> Benchmark:
    """Cherche une instance par nom court, insensible à la casse (ex. "cyc6", "E.1")."""
    for b in list_benchmarks(directory=directory):
        if b.name.lower() == name.lower():
            return b
    raise KeyError(f"benchmark '{name}' introuvable dans {directory}")


def known_value(name: str) -> tuple[int | None, str | None]:
    return KNOWN.get(name, (None, None))
