#!/usr/bin/env python3
"""
Objet     : bibliothèque interrogeable des arbres phylogénétiques d'un dépôt de
            recherche multi-projets. MOISSONNE les arbres déjà calculés au lieu
            d'exiger qu'on les enregistre, en extrait une fiche de métadonnées,
            et répond à « ai-je déjà un arbre qui ferait l'affaire ? » AVANT
            qu'un nouveau calcul ne soit lancé. Rend aussi des FORÊTS, pour les
            statistiques inter-arbres qu'un arbre isolé ne permet pas.
Entrées   : racine du dépôt (auto-détectée, ou --root) ; tout fichier Newick ou
            NEXUS sous <racine>/**, plus ses fichiers voisins (.log, .bestModel,
            .iqtree) d'où sont tirés outil, modèle, alignement et bootstrap.
            Table souche->clade lue dans <racine>/bdd/actuelle/.
Sorties   : .forest/ à la racine (index.jsonl, taxa.json, postings.json,
            notes.json) — index DÉRIVÉ, régénérable, hors suivi de version ;
            stdout compact pour les requêtes.
Réutilisable : oui — moissonnage et requêtes génériques ; seule la couche
            taxonomique (bdd/actuelle, taxonomy_crossmap.tsv) est spécifique
            MTBC et se dégrade proprement si absente.
Projet    : mtbc/ (outillage transverse) — canonique, exposé par `/phylo-forest`
Date      : 2026-08-27

Garde-fou : un arbre retrouvé n'est PAS un arbre validé. La fiche dit ce qu'il
CONTIENT, jamais s'il répond à la question posée. Le jeu de taxons, le modèle,
l'alignement et la DATE relative à la taxonomie doivent être lus avant réemploi :
un arbre peut être juste et néanmoins inexploitable pour l'argument voulu si la
taxonomie de référence a bougé depuis son calcul.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import statistics
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

INDEX_DIR = ".forest"
INDEX_FILE = "index.jsonl"
TAXA_FILE = "taxa.json"
POST_FILE = "postings.json"
NOTES_FILE = "notes.json"      # annotations humaines : JAMAIS écrasées par un harvest
META_FILE = "index.meta.json"
INDEX_VERSION = 1

# Extensions contenant réellement un ou plusieurs arbres. Les autres sorties des
# mêmes outils (.log, .rba, .ckp, .phy, .bestModel) sont lues comme SIDECARS,
# jamais indexées comme arbres.
TREE_EXT = {
    ".nwk", ".newick", ".tree", ".treefile", ".contree", ".nex", ".nexus",
    ".bestTree", ".support", ".bestTreeCollapsed", ".startTree", ".mlTrees",
    ".bootstraps", ".rootedTree", ".consensusTree", ".tre",
}
# RAxML 8 (`raxmlHPC`) ne met AUCUNE extension utile : il nomme ses sorties
# `RAxML_<role>.<nom_de_run>`, ou le nom de run est arbitraire (`.sortie1`, `.T3`...).
# Ces arbres etaient donc invisibles pour le moissonneur, qui ne filtre que sur
# l'extension (constate le 2026-09-04 sur un arbre de 1977 taxons rapatrie du cluster
# Lumiere, produit par RAxML 8.2.4). On les reconnait par leur PREFIXE. `RAxML_info` et
# `RAxML_log` sont volontairement absents : ce sont des journaux, pas des arbres.
RAXML8_PREFIXES = (
    "RAxML_result.", "RAxML_bestTree.", "RAxML_bipartitions.",
    "RAxML_bipartitionsBranchLabels.", "RAxML_rootedTree.",
    "RAxML_parsimonyTree.", "RAxML_randomTree.", "RAxML_bootstrap.",
    "RAxML_distances.",
)

SKIP_DIRS = {".git", INDEX_DIR, "__pycache__", "node_modules", ".venv", ".carrefour"}
MAX_BYTES = 64 * 1024 * 1024
MAX_TREES_PER_FILE = 8   # un fichier d'arbre au-delà est une anomalie, pas un arbre

# Accession SRA dans un label d'arbre. Le `\b` initial évident est un PIÈGE : les
# labels du dépôt s'écrivent le plus souvent `L4.4.2_SRR15315804`, or `_` est un
# caractère de mot, donc il n'y a aucune frontière entre `_` et `S` et `\bSRR`
# ne matche pas. Résultat mesuré avant correction : 268 tips sur 268 déclarés
# « inconnus » dans les arbres du projet L4.13, et donc AUCUNE composition
# taxonomique pour les arbres les plus pertinents. Même mode d'échec que le bug
# de `recadrage_signals.py` du 2026-08-26 : une frontière de mot supposée là où
# le vocabulaire réel n'en a pas.
ACC_RE = re.compile(r"(?<![A-Za-z0-9])([SED]RR\d{5,9})(?!\d)")


def sha(s: str, n: int = 12) -> str:
    return hashlib.sha256(s.encode("utf-8", "replace")).hexdigest()[:n]


# --- Parsing Newick, sans dépendance ---------------------------------------
# Parseur maison plutôt que Bio.Phylo/ete3, pour deux raisons mesurées.
# (1) Le moissonnage rencontre des fichiers tronqués, vides, à commentaires NHX
#     ou à labels non quotés : une exception sur l'un d'eux ne doit pas arrêter
#     la récolte, donc on tolère tout et on renseigne `parse_error`.
# (2) Il doit être ITÉRATIF. Les phylogénies MTBC sont fortement pectinées — des
#     lignées entières sont des peignes — et un parseur récursif y atteint une
#     profondeur de l'ordre du nombre de feuilles, donc RecursionError sur les
#     arbres les plus intéressants du dépôt. Aucune récursion ici, nulle part.

def strip_nexus(text: str) -> str:
    """Extrait les Newick d'un bloc NEXUS TREES, table `Translate` APPLIQUÉE.

    Le piège, mesuré : un NEXUS écrit par BEAST numérote ses feuilles (`1`, `2`,
    …) et donne la correspondance dans un bloc `Translate`. Sans l'appliquer, les
    feuilles s'appellent « 1 » à « 300 » dans TOUS les fichiers — deux
    sous-échantillons de souches entièrement différents reçoivent alors le même
    jeu de taxons, sont regroupés comme s'ils étaient comparables, et leur
    distance topologique compare des numéros qui ne désignent pas les mêmes
    souches. C'est ainsi qu'un lot d'arbres publiés (Loiseau 2020) est ressorti
    à une distance de Robinson-Foulds de 1,000, valeur assez extrême pour être
    invraisemblable et donc vérifiée : c'était l'artefact, pas un résultat.
    """
    if "#NEXUS" not in text[:400].upper():
        return text
    trans: dict[str, str] = {}
    mt = re.search(r"\bTranslate\b(.*?);", text, re.I | re.S)
    if mt:
        for line in mt.group(1).split(","):
            parts = line.strip().split(None, 1)
            if len(parts) == 2:
                trans[parts[0].strip()] = parts[1].strip().strip("'\"")
    out = []
    for m in re.finditer(r"^\s*(?:tree|utree)\s+[^=]*=\s*(?:\[[^\]]*\]\s*)?(\(.*?;)",
                         text, re.M | re.I | re.S):
        nwk = m.group(1)
        if trans:
            # Un label de feuille suit toujours `(` ou `,` et précède `:`, `[`,
            # `,` ou `)` : cibler cette position évite de renommer un support ou
            # une longueur de branche qui serait numériquement identique.
            nwk = re.sub(r"(?<=[(,])\s*(\w+)\s*(?=[:\[,)])",
                         lambda z: trans.get(z.group(1), z.group(1)), nwk)
        out.append(nwk)
    return "\n".join(out)


def split_trees(text: str) -> list[str]:
    """Un fichier peut porter N arbres (`.mlTrees`, `.bootstraps`, NEXUS)."""
    text = strip_nexus(text)
    text = re.sub(r"\[[^\]]*\]", "", text)          # commentaires NHX / NEXUS
    parts = [t.strip() for t in text.split(";")]
    return [t + ";" for t in parts if t.lstrip().startswith("(")]


def _read_token(s: str, i: int) -> tuple[str, float | None, int]:
    """Lit `label[:length]` à partir de i ; renvoie (label, length, i_suivant)."""
    n = len(s)
    if i < n and s[i] == "'":
        j = s.find("'", i + 1)
        label = s[i + 1:j if j > 0 else n]
        i = (j + 1) if j > 0 else n
    else:
        j = i
        while j < n and s[j] not in "(),:;":
            j += 1
        label = s[i:j].strip()
        i = j
    length = None
    if i < n and s[i] == ":":
        j = i + 1
        while j < n and s[j] not in "(),;":
            j += 1
        try:
            length = float(s[i + 1:j])
        except ValueError:
            length = None
        i = j
    return label, length, i


class Tree:
    __slots__ = ("parent", "label", "length", "tips", "n_nodes", "error")


def parse_newick(s: str) -> Tree:
    t = Tree()
    t.parent, t.label, t.length, t.tips, t.error = [], [], [], [], None
    stack: list[int] = []
    i, n = 0, len(s)

    def new_node(par: int) -> int:
        t.parent.append(par)
        t.label.append("")
        t.length.append(None)
        return len(t.parent) - 1

    try:
        while i < n:
            c = s[i]
            if c in " \t\r\n":
                i += 1
            elif c == "(":
                idx = new_node(stack[-1] if stack else -1)
                stack.append(idx)
                i += 1
            elif c == ",":
                i += 1
            elif c == ")":
                i += 1
                if not stack:
                    raise ValueError("parenthèse fermante orpheline")
                idx = stack.pop()
                lab, ln, i = _read_token(s, i)
                t.label[idx], t.length[idx] = lab, ln
            elif c == ";":
                break
            else:
                lab, ln, i = _read_token(s, i)
                idx = new_node(stack[-1] if stack else -1)
                t.label[idx], t.length[idx] = lab, ln
                t.tips.append(idx)
        if stack:
            raise ValueError("parenthèses non refermées")
    except Exception as exc:            # noqa: BLE001 — tolérance voulue
        t.error = str(exc)[:120]
    t.n_nodes = len(t.parent)
    return t


def tree_stats(t: Tree) -> dict:
    """Statistiques d'un arbre, toutes calculées sans récursion."""
    tips = t.tips
    labels = [t.label[i] for i in tips if t.label[i]]
    lens = [x for x in t.length if x is not None]
    # `set(tips)` UNE fois : le reconstruire dans la comprehension le rebâtit à
    # chaque nœud, ce qui est quadratique et fait passer un arbre de 8 500
    # feuilles de quelques secondes à plusieurs minutes — mesuré en bloquant un
    # moissonnage complet.
    tipset = set(tips)
    internal = [i for i in range(t.n_nodes) if i not in tipset]
    # supports : label numérique sur un nœud interne
    sup = []
    for i in range(t.n_nodes):
        if i in tipset or not t.label[i]:
            continue
        lab = t.label[i]
        try:
            sup.append(float(lab))
            continue
        except ValueError:
            pass
        # IQ-TREE écrit DEUX supports par nœud, `SH-aLRT/UFBoot` (ex. `81.5/100`),
        # qu'un simple float() rejette : mesuré, 18 arbres du dépôt étaient ainsi
        # déclarés sans support alors qu'ils en portaient deux. On retient l'UFBoot,
        # celui que les manuscrits rapportent.
        m2 = re.fullmatch(r"([\d.]+)/([\d.]+)", lab)
        if m2:
            try:
                sup.append(float(m2.group(2)))
            except ValueError:
                pass
    # Profondeur racine->feuille en UNE passe descendante. Invariant du parseur :
    # un noeud interne est cree quand on lit sa parenthese ouvrante, donc avant
    # tous ses descendants — l'ordre 0..n-1 est deja un ordre topologique.
    depth = [0.0] * t.n_nodes
    maxdepth = 0.0
    for i in range(t.n_nodes):
        p = t.parent[i]
        depth[i] = (depth[p] if p != -1 else 0.0) + (t.length[i] or 0.0)
    for leaf in tips:
        maxdepth = max(maxdepth, depth[leaf])
    # degré de la racine : 2 = enraciné, 3+ = non enraciné (convention Newick)
    roots = [i for i in range(t.n_nodes) if t.parent[i] == -1]
    root = roots[0] if roots else None
    root_deg = sum(1 for p in t.parent if p == root) if root is not None else 0
    npoly = 0
    kids = Counter(p for p in t.parent if p != -1)
    for node, k in kids.items():
        if k > 2 and node != root:
            npoly += 1
    return {
        "n_tips": len(labels),
        "n_internal": len(internal),
        "rooted": (root_deg == 2) if root_deg else None,
        "has_lengths": bool(lens),
        "has_support": bool(sup) and len(sup) >= 0.5 * max(1, len(internal) - 1),
        "total_length": round(sum(lens), 6) if lens else None,
        "max_root_to_tip": round(maxdepth, 6) if lens else None,
        "median_branch": round(statistics.median(lens), 8) if lens else None,
        "zero_branches": sum(1 for x in lens if x == 0.0),
        "polytomies": npoly,
        "support_median": round(statistics.median(sup), 2) if sup else None,
        "support_scale": (100 if sup and max(sup) > 1.5 else 1) if sup else None,
    }


def splits_set(t: Tree):
    """Empreinte de topologie NON ENRACINÉE, par l'ensemble de ses splits.

    Chaque nœud interne définit une bipartition des feuilles. Deux choix rendent
    l'empreinte utile là où une simple somme de contrôle du fichier ne l'est pas.

    (1) NON ENRACINÉE : un split et son complément sont le même caractère, donc
    on garde un représentant canonique des deux côtés. Sans cela, deux
    reconstructions identiques réenracinées sur un outgroup différent
    passeraient pour deux arbres distincts — le cas fréquent, pas le cas rare.

    (2) COMMUTATIVE : le côté d'un split est identifié par le XOR des empreintes
    de ses feuilles, jamais par l'ensemble des noms. Accumuler des ensembles
    coûte O(n²) sur un arbre pectiné, et les phylogénies MTBC sont pectinées :
    mesuré à 3,3 s pour un seul peigne de 3 001 feuilles, soit des heures sur la
    forêt entière. Le XOR est associatif et commutatif, donc chaque union est en
    O(1) et la récolte complète tient en quelques minutes.
    """
    names = {i: t.label[i] for i in t.tips if t.label[i]}
    if len(names) < 4:
        return "", 0
    MASK = (1 << 64) - 1
    hsh = {i: int(hashlib.blake2b(nm.encode(), digest_size=8).hexdigest(), 16)
           for i, nm in names.items()}
    acc = [0] * t.n_nodes
    cnt = [0] * t.n_nodes
    for i, h in hsh.items():
        acc[i], cnt[i] = h, 1
    # Invariant du parseur pris à l'envers : parcourir n-1 -> 0 visite tout
    # enfant avant son parent, donc une seule passe suffit.
    for i in range(t.n_nodes - 1, -1, -1):
        p = t.parent[i]
        if p != -1:
            acc[p] ^= acc[i]
            cnt[p] += cnt[i]
    total = 0
    for h in hsh.values():
        total ^= h
    ntax = len(names)
    tipset = set(t.tips)
    parts = set()
    for i in range(t.n_nodes):
        if i in tipset or t.parent[i] == -1:
            continue
        k = cnt[i]
        if not 1 < k < ntax - 1:
            continue                       # split trivial : n'informe sur rien
        a = acc[i] & MASK
        b = (total ^ acc[i]) & MASK
        parts.add(min(a, b))               # représentant canonique des deux côtés
    return parts, total, set(names.values())


def splits_hash(t: Tree) -> tuple[str, int]:
    """Empreinte compacte de la topologie : hash de l'ensemble de ses splits."""
    parts, _, _ = splits_set(t)
    if not parts:
        return "", 0
    return sha("|".join(f"{x:016x}" for x in sorted(parts)), 16), len(parts)


def taxon_hash(name: str) -> int:
    return int(hashlib.blake2b(name.encode(), digest_size=8).hexdigest(), 16)


# --- Sidecars : ce que le fichier d'arbre ne dit pas ------------------------
# Un Newick ne contient ni le modèle, ni l'alignement, ni la commande, ni le
# nombre de réplicats — c'est-à-dire à peu près tout ce qui décide si un arbre
# est réemployable. Ces informations vivent dans les fichiers voisins que les
# outils écrivent à côté, et que personne ne relit jamais. Les récolter est le
# seul moyen d'avoir une fiche utile sans rien demander à l'utilisateur.

SIDECAR_PATTERNS = (".raxml.log", ".log", ".iqtree", ".raxml.bestModel", ".bestModel")


def _prefixes(path: Path) -> list[Path]:
    """Préfixes plausibles : `x.raxml.bestTree` -> `x.raxml`, `x`."""
    out, p = [], path
    for _ in range(3):
        p = p.with_suffix("")
        out.append(p)
        if not p.suffix:
            break
    return out


_SIDECAR_CACHE: dict[str, dict] = {}


def read_sidecars(path: Path) -> dict:
    # Un run RAxML produit bestTree, startTree, mlTrees, support et bootstraps :
    # cinq fichiers d'arbres pour UN log. Sans ce cache, le log est relu cinq fois.
    ck = str(_prefixes(path)[-1])
    if ck in _SIDECAR_CACHE:
        return _SIDECAR_CACHE[ck]
    info: dict = {}
    seen: set[Path] = set()
    # RAxML 8 ne suit pas le schema prefixe+suffixe : pour `RAxML_result.sortie1`,
    # les metadonnees (version, commande, modele, patterns) sont dans
    # `RAxML_info.sortie1`, meme repertoire et meme nom de run, autre prefixe.
    name = path.name
    if name.startswith("RAxML_") and "." in name:
        run = name.split(".", 1)[1]
        for kin in ("RAxML_info.", "RAxML_log."):
            cand = path.with_name(kin + run)
            if cand.exists() and cand.stat().st_size <= 4_000_000:
                seen.add(cand)
                try:
                    _scan_log(cand.read_text(errors="replace")[:60_000], info)
                except OSError:
                    pass
    for pref in _prefixes(path):
        for suf in SIDECAR_PATTERNS:
            cand = Path(str(pref) + suf)
            if cand in seen or not cand.exists() or cand.stat().st_size > 4_000_000:
                continue
            seen.add(cand)
            try:
                txt = cand.read_text(errors="replace")[:60_000]
            except OSError:
                continue
            _scan_log(txt, info)
    _SIDECAR_CACHE[ck] = info
    return info


def _scan_log(txt: str, info: dict) -> None:
    pats = {
        "command": [r"(?:RAxML-NG was called as follows|RAxML was called as follows|Command):\s*\n?\s*(.+)",
                    r"^\s*(raxml-ng[^\n]{10,400})$", r"^\s*(iqtree2?[^\n]{10,400})$"],
        "model": [r"Model of substitution:\s*(\S+)", r"^\s*Model:\s*(\S+)",
                  r"--model\s+(\S+)", r"^([A-Z]{2,10}\+?[A-Z0-9+{}.,]*)\{",
                  r"Substitution model:\s*(\S+)", r"\s-m\s+([A-Z][A-Z0-9]{2,20})"],
        "alignment": [r"Input file name:\s*(\S+)", r"Alignment file:\s*(\S+)",
                      r"--msa\s+(\S+)", r"-s\s+(\S+\.(?:fasta|fa|phy|aln|nex))"],
        "n_taxa_log": [r"Loaded alignment with (\d+) taxa",
                       r"Alignment has (\d+) sequences"],
        "n_sites": [r"with \d+ taxa and (\d+) sites",
                    r"Alignment has (\d+) distinct alignment patterns",
                    r"Alignment has \d+ sequences with (\d+) columns"],
        "bootstrap": [r"--bs-trees\s+(\d+)", r"-B\s+(\d+)", r"-b\s+(\d+)",
                      r"Number of bootstrap replicates:\s*(\d+)"],
        "tool_version": [r"(RAxML-NG v\.?\s*[\d.]+)", r"(IQ-TREE (?:multicore )?version [\d.]+)",
                         r"(FastTree(?: version)? [\d.]+)", r"This is (RAxML version [\d.]+)"],
        "seed": [r"random seed[^\d]{0,10}(\d+)"],
    }
    for key, regs in pats.items():
        if info.get(key):
            continue
        for r in regs:
            m = re.search(r, txt, re.M)
            if m:
                info[key] = m.group(1).strip()[:300]
                break


def guess_tool(path: Path, info: dict) -> str:
    name = path.name
    v = (info.get("tool_version") or "") + " " + (info.get("command") or "")
    # RAxML 8 (`raxmlHPC`) et RAxML-NG sont deux logiciels distincts, aux modeles et
    # aux performances differentes : les confondre trompe quiconque filtre par outil
    # pour retrouver « ses arbres RAxML-NG ». RAxML 8 se reconnait a son nom de
    # fichier `RAxML_<role>.<run>` ou a sa banniere « This is RAxML version 8.x ».
    if name.startswith("RAxML_") or re.search(r"raxml version [78]", v.lower()) \
            or "raxmlhpc" in v.lower():
        return "raxml8"
    if ".raxml." in name or "raxml" in v.lower():
        return "raxml-ng"
    if name.endswith((".treefile", ".contree")) or "iq-tree" in v.lower() or "iqtree" in v.lower():
        return "iqtree"
    if "fasttree" in v.lower():
        return "fasttree"
    if "beast" in v.lower() or name.endswith((".trees", ".mcc")):
        return "beast"
    if "nj" in name.lower():
        return "nj"
    return "inconnu"


# Un run produit un arbre de RÉSULTAT et une nuée d'arbres INTERMÉDIAIRES : arbre
# de départ, réplicats ML, réplicats bootstrap. Les confondre fausserait tout ce
# que la bibliothèque sert à mesurer — cent réplicats bootstrap d'un même run ne
# sont pas cent reconstructions indépendantes, et compter la fréquence d'un clade
# à travers eux revient à recompter le bootstrap de ce run en le déguisant en
# consensus inter-études. Ils restent indexés (on veut pouvoir les retrouver),
# mais ils sont écartés par défaut des recherches et des statistiques.
INDEPENDENT_ROLES = {"ML best", "consensus", "ML + supports", "enraciné",
                     "ML collapsé", "arbre"}

ROLE_BY_EXT = {
    ".bestTree": "ML best", ".support": "ML + supports", ".contree": "consensus",
    ".treefile": "ML best", ".startTree": "arbre de départ", ".mlTrees": "réplicats ML",
    ".bootstraps": "réplicats bootstrap", ".bestTreeCollapsed": "ML collapsé",
    ".consensusTree": "consensus", ".rootedTree": "enraciné",
}


# --- Couche taxonomique -----------------------------------------------------
# CG l'a demandé explicitement, et c'est le point qui rend une fiche citable
# plutôt qu'indicative : dire « cet arbre contient 40 L4.13 » n'a aucun sens sans
# dire SELON QUEL SYSTÈME. Le dépôt en connaît dix-huit (Coll, Napier, Freschi,
# Shitikov, Lipworth, Zwyer…), et ils ne découpent pas le même arbre de la même
# façon. La référence locale est `bdd/actuelle/` — système « guyeux » — dont
# l'état est lui-même daté, puisqu'il bouge de semaine en semaine.

def load_taxonomy(root: Path) -> dict:
    base = root / "bdd" / "actuelle"
    tax = {"system": "guyeux/bdd-actuelle", "snapshot": None, "n_clades": 0,
           "strain2clade": {}}
    if not base.is_dir():
        return tax
    s2c: dict[str, str] = {}
    n = 0
    for clade in os.scandir(base):
        if not clade.is_dir() or clade.name.startswith("."):
            continue
        n += 1
        try:
            for st in os.scandir(clade.path):
                if st.is_dir() and ACC_RE.fullmatch(st.name):
                    s2c[st.name] = clade.name
        except OSError:
            continue
    tax["strain2clade"] = s2c
    tax["n_clades"] = n
    bc = root / "global_supplementary" / "barcoding_v2" / "barcode_complete.tsv"
    if bc.exists():
        tax["snapshot"] = time.strftime("%Y-%m-%d", time.localtime(bc.stat().st_mtime))
    return tax


def load_crossmap(root: Path) -> dict:
    """`taxonomy_crossmap.tsv` : traduire un clade local vers les autres systèmes."""
    f = root / "global_supplementary" / "barcoding_v2" / "taxonomy_crossmap.tsv"
    out: dict[str, dict[str, str]] = {}
    if not f.exists():
        return out
    with f.open(encoding="utf-8", errors="replace") as fh:
        head = fh.readline().rstrip("\n").split("\t")
        try:
            i_moi, i_sys, i_code = (head.index("moi_lineage"), head.index("system"),
                                    head.index("best_match_code"))
            i_jac = head.index("jaccard_pct")
        except ValueError:
            return out
        for line in fh:
            p = line.rstrip("\n").split("\t")
            if len(p) <= max(i_moi, i_sys, i_code, i_jac):
                continue
            try:
                if float(p[i_jac] or 0) < 50:
                    continue          # correspondance trop faible pour être citée
            except ValueError:
                continue
            out.setdefault(p[i_moi], {})[p[i_sys]] = p[i_code]
    return out


def composition(tips: list[str], tax: dict) -> dict:
    s2c = tax["strain2clade"]
    clades = Counter()
    known = 0
    for t in tips:
        m = ACC_RE.search(t)
        acc = m.group(1) if m else None
        c = s2c.get(acc) if acc else None
        if c:
            clades[c] += 1
            known += 1
    return {
        "n_known": known,
        "n_unknown": len(tips) - known,
        "clades": dict(clades.most_common()),
        "n_clades": len(clades),
    }


# --- Moissonnage ------------------------------------------------------------
# Choix de conception central : on RÉCOLTE, on ne demande pas d'enregistrer.
# Le dépôt disposait déjà d'un mécanisme d'archivage sur déclaration explicite
# (`investigate_phylo/history/`, alimenté par `get_phylo.py`) : il contenait
# 3 arbres après trois mois et demi, pour environ 1 800 fichiers d'arbres
# réellement produits. Un archivage qui coûte un geste n'est pas fait. Celui-ci
# ne coûte rien : il lit ce qui est déjà sur le disque.

def find_root(start: Path, min_projects: int = 5) -> Path:
    cur = start.resolve()
    for _ in range(6):
        try:
            n = sum(1 for _ in cur.glob("*/cahier_de_labo.md"))
        except OSError:
            n = 0
        if n >= min_projects:
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    return start.resolve()


def iter_tree_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".git")]
        for fn in filenames:
            p = Path(dirpath) / fn
            sufs = p.suffixes
            if fn.startswith(RAXML8_PREFIXES):
                try:
                    if p.stat().st_size < MAX_BYTES:
                        yield p
                except OSError:
                    pass
                continue
            if not sufs:
                continue
            if sufs[-1] in TREE_EXT:
                try:
                    if p.stat().st_size < MAX_BYTES:
                        yield p
                except OSError:
                    continue


def context_of(root: Path, path: Path) -> str:
    """Indice de la question d'origine, tiré de ce qui est déjà écrit.

    Aucune heuristique ne devinera la question à laquelle un arbre répondait ;
    en revanche le chemin la porte souvent presque en clair
    (`analyse_clade_caprae_results/`, `Phylogenies/L1_focused/`), et un README
    voisin la porte parfois vraiment. On assemble donc un indice, présenté comme
    tel, et le champ `question` reste vide jusqu'à ce qu'un humain ou un agent
    l'écrive avec `annotate`.
    """
    rel = path.relative_to(root)
    bits = [b for b in rel.parts[:-1] if b not in ("résultats", "resultats", "analyses",
                                                   "data", "experiments", "output")]
    ctx = " / ".join(bits[-3:])
    for cand in (path.parent / "README.md", path.parent / "readme.md"):
        if cand.exists() and cand.stat().st_size < 200_000:
            try:
                for line in cand.read_text(errors="replace").splitlines():
                    if line.strip().startswith("#"):
                        ctx += " | " + line.strip("# ").strip()[:140]
                        break
            except OSError:
                pass
            break
    return ctx[:300]


# Un pipeline qui journalise sa cible rend la question RÉCOLTABLE. C'est
# l'exception à « la question n'est pas devinable » : `analyse_lignee.py` écrit
# « Analyse de la cible : L6* » dans un resume.txt voisin, et cette ligne est la
# question, écrite par celui qui a lancé le calcul. Elle reste distincte du champ
# `question` de notes.json, qui porte l'intention humaine et n'est pas dérivable.
TARGET_RE = re.compile(r"^Analyse de la (?:cible|lign[ée]e)\s*:\s*(.+)$", re.M)
OUTG_RE = re.compile(r"^Outgroup\s*:\s*(.+)$", re.M)
KEPT_RE = re.compile(r"^Souches (?:de la cible|de \S+) retenues\s*:\s*(\S+)", re.M)
OTHER_RE = re.compile(r"^Souches des autres lign[ée]es\s*:\s*(\d+)", re.M)


def read_target(path: Path) -> str | None:
    """Cible journalisée par le pipeline dans un resume.txt voisin, si elle existe."""
    for d in (path.parent, path.parent.parent):
        f = d / "resume.txt"
        if not f.is_file():
            continue
        try:
            txt = f.read_text(errors="replace")[:4000]
        except OSError:
            continue
        m = TARGET_RE.search(txt)
        if not m:
            continue
        bits = [f"cible {m.group(1).strip()}"]
        k = KEPT_RE.search(txt)
        o = OTHER_RE.search(txt)
        if k:
            bits.append(f"{k.group(1)} souches de la cible")
        if o:
            bits.append(f"{o.group(1)} des autres lignées")
        g = OUTG_RE.search(txt)
        if g:
            bits.append(f"outgroup {g.group(1).strip()}")
        return ", ".join(bits)
    return None


def harvest(root: Path, verbose: bool = True) -> None:
    tax = load_taxonomy(root)
    by_content: dict[str, dict] = {}
    taxa: dict[str, list[str]] = {}
    n_files = n_trees = n_err = 0
    t0 = time.time()
    for path in iter_tree_files(root):
        n_files += 1
        try:
            raw = path.read_text(errors="replace")
        except OSError:
            continue
        trees = split_trees(raw)
        if not trees:
            continue
        sc = read_sidecars(path)
        tool = guess_tool(path, sc)
        role = ROLE_BY_EXT.get(path.suffixes[-1], "arbre")
        rel = str(path.relative_to(root))
        st = path.stat()
        # Un fichier de replicats (.mlTrees, .bootstraps) peut porter des centaines
        # d'arbres quasi identiques. En indexer un echantillon suffit a savoir que
        # la forêt existe et ou la trouver ; les indexer tous coûte des heures pour
        # une information qu'aucune requête ne pose.
        n_in_file = len(trees)
        if n_in_file > MAX_TREES_PER_FILE:
            trees = trees[:MAX_TREES_PER_FILE]
        for k, txt in enumerate(trees):
            n_trees += 1
            csha = sha(re.sub(r"\s+", "", txt), 16)
            loc = f"{rel}#{k}" if len(trees) > 1 else rel
            if csha in by_content:
                by_content[csha]["paths"].append(loc)
                continue
            tr = parse_newick(txt)
            if tr.error or len(tr.tips) < 3:
                n_err += 1
                if len(tr.tips) < 3:
                    continue
            tips = [tr.label[i] for i in tr.tips if tr.label[i]]
            stats = tree_stats(tr)
            tsha, nsp = splits_hash(tr)
            rec = {
                "tree_id": csha,
                "paths": [loc],
                "project": Path(rel).parts[0],
                "mtime": time.strftime("%Y-%m-%d", time.localtime(st.st_mtime)),
                "size": st.st_size,
                "role": role if n_in_file == 1 else f"{role} [{k + 1}/{n_in_file}]",
                "independent": role in INDEPENDENT_ROLES and n_in_file == 1,
                "tool": tool,
                "topo_sha": tsha,
                "n_splits": nsp,
                "taxa_sha": sha("|".join(sorted(tips)), 16),
                "parse_error": tr.error,
                "context": context_of(root, path),
                "target": read_target(path),
                "composition": composition(tips, tax),
            }
            rec.update(stats)
            for key in ("model", "alignment", "bootstrap", "n_sites", "tool_version",
                        "command", "seed"):
                if sc.get(key):
                    rec[key] = sc[key]
            by_content[csha] = rec
            taxa[csha] = tips
        if verbose and n_files % 200 == 0:
            print(f"  … {n_files} fichiers, {len(by_content)} arbres uniques, "
                  f"{time.time() - t0:.0f}s", file=sys.stderr, flush=True)

    postings: dict[str, list[str]] = defaultdict(list)
    for tid, tips in taxa.items():
        for tp in tips:
            m = ACC_RE.search(tp)
            postings[m.group(1) if m else tp].append(tid)

    d = root / INDEX_DIR
    d.mkdir(exist_ok=True)
    with (d / INDEX_FILE).open("w", encoding="utf-8") as fh:
        for rec in by_content.values():
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    (d / TAXA_FILE).write_text(json.dumps(taxa), encoding="utf-8")
    (d / POST_FILE).write_text(json.dumps(postings), encoding="utf-8")
    (d / META_FILE).write_text(json.dumps({
        "version": INDEX_VERSION, "harvested": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "n_files": n_files, "n_trees_seen": n_trees, "n_unique": len(by_content),
        "taxonomy": {k: v for k, v in tax.items() if k != "strain2clade"},
        "seconds": round(time.time() - t0, 1),
    }, ensure_ascii=False), encoding="utf-8")
    print(f"{len(by_content)} arbres uniques ({n_trees} occurrences dans {n_files} "
          f"fichiers, {n_err} illisibles) en {time.time() - t0:.1f}s")


def load(root: Path) -> tuple[list[dict], dict, dict, dict]:
    d = root / INDEX_DIR
    if not (d / INDEX_FILE).exists():
        print("index absent — lancer `forest.py harvest` d'abord", file=sys.stderr)
        sys.exit(2)
    recs = [json.loads(l) for l in (d / INDEX_FILE).read_text(encoding="utf-8").splitlines()]
    taxa = json.loads((d / TAXA_FILE).read_text(encoding="utf-8"))
    post = json.loads((d / POST_FILE).read_text(encoding="utf-8"))
    notes = {}
    if (d / NOTES_FILE).exists():
        notes = json.loads((d / NOTES_FILE).read_text(encoding="utf-8"))
    for r in recs:
        if r["tree_id"] in notes:
            r["note"] = notes[r["tree_id"]]
    return recs, taxa, post, notes


# --- Requêtes ---------------------------------------------------------------

def _filters(recs: list[dict], a) -> list[dict]:
    out = recs
    if a.min_tips:
        out = [r for r in out if r.get("n_tips", 0) >= a.min_tips]
    if a.max_tips:
        out = [r for r in out if r.get("n_tips", 0) <= a.max_tips]
    if a.tool:
        out = [r for r in out if r.get("tool") == a.tool]
    if a.project:
        out = [r for r in out if a.project.lower() in r.get("project", "").lower()]
    if a.since:
        out = [r for r in out if r.get("mtime", "") >= a.since]
    if a.support:
        out = [r for r in out if r.get("has_support")]
    if a.rooted:
        out = [r for r in out if r.get("rooted")]
    if not getattr(a, "all", False):
        # Par défaut on ne montre que les arbres de RÉSULTAT (cf. INDEPENDENT_ROLES).
        out = [r for r in out if r.get("independent")]
    return out


def read_taxa_arg(val: str) -> list[str]:
    """Accepte une liste inline, un fichier de noms, ou un FASTA."""
    p = Path(val)
    if p.exists():
        txt = p.read_text(errors="replace")
        if txt.lstrip().startswith(">"):
            return [l[1:].split()[0] for l in txt.splitlines() if l.startswith(">")]
        return [l.strip() for l in txt.splitlines() if l.strip()]
    return [x.strip() for x in re.split(r"[,\s]+", val) if x.strip()]


def cmd_find(root: Path, a) -> None:
    recs, taxa, post, _ = load(root)
    cand = _filters(recs, a)
    want: list[str] = []
    scored: list[tuple] = []

    if a.taxa:
        want = read_taxa_arg(a.taxa)
        wset = set(want)
        for r in cand:
            tips = set(taxa.get(r["tree_id"], []))
            accs = {ACC_RE.search(t).group(1) for t in tips if ACC_RE.search(t)}
            hit = len(wset & (tips | accs))
            if hit:
                cov = hit / max(1, len(wset))
                spec = hit / max(1, r.get("n_tips", 1))
                scored.append((cov, spec, hit, r))
        scored.sort(key=lambda x: (-x[0], -x[1], -x[3].get("n_tips", 0)))
    elif a.clade:
        for r in cand:
            cl = r.get("composition", {}).get("clades", {})
            hit = sum(n for c, n in cl.items()
                      if c == a.clade or c.startswith(a.clade + "."))
            if hit >= (a.min or 1):
                spec = hit / max(1, r.get("n_tips", 1))
                scored.append((hit / max(1, a.min or 1), spec, hit, r))
        scored.sort(key=lambda x: (-x[2], -x[1]))
    else:
        for r in cand:
            scored.append((0, 0, 0, r))
        scored.sort(key=lambda x: -x[3].get("n_tips", 0))

    if not scored:
        print("aucun arbre ne correspond — il faut en calculer un "
              "(penser à `harvest` après coup pour qu'il serve la prochaine fois)")
        return
    print(f"{'couv':>5} {'spéc':>5} {'n':>5} {'tips':>6} {'projet':22s} {'outil':9s} "
          f"{'date':10s} {'id':16s} contexte")
    for cov, spec, hit, r in scored[:a.k]:
        sup = "S" if r.get("has_support") else " "
        rt = "R" if r.get("rooted") else " "
        print(f"{cov:5.2f} {spec:5.2f} {hit:5d} {r.get('n_tips', 0):6d} "
              f"{r.get('project', '')[:22]:22s} {r.get('tool', '')[:9]:9s} "
              f"{r.get('mtime', ''):10s} {r['tree_id']:16s} {sup}{rt} "
              f"{(r.get('note') or r.get('context', ''))[:60]}")
    print(f"\n{len(scored)} arbres candidats · un arbre retrouvé n'est pas un arbre "
          f"VALIDÉ : lire `show <id>` (modèle, alignement, date vs taxonomie) avant réemploi.")


def cmd_show(root: Path, tid: str) -> None:
    recs, taxa, _, _ = load(root)
    hit = [r for r in recs if r["tree_id"].startswith(tid)]
    if not hit:
        print("aucun arbre avec cet identifiant")
        return
    r = hit[0]
    tips = taxa.get(r["tree_id"], [])
    cm = load_crossmap(root)
    meta = json.loads((root / INDEX_DIR / META_FILE).read_text())
    print(f"# arbre {r['tree_id']}")
    for k in ("project", "role", "tool", "tool_version", "model", "alignment",
              "n_sites", "bootstrap", "seed", "mtime", "n_tips", "rooted",
              "has_lengths", "has_support", "support_median", "total_length",
              "max_root_to_tip", "median_branch", "zero_branches", "polytomies",
              "n_splits", "topo_sha", "taxa_sha", "parse_error"):
        if r.get(k) not in (None, "", False) or k in ("rooted", "has_support"):
            print(f"  {k:16s} {r.get(k)}")
    if r.get("note"):
        print(f"  {'question':16s} {r['note']}")
    else:
        print(f"  {'question':16s} (non renseignée — `annotate {r['tree_id']} \"…\"`)")
    if r.get("target"):
        print(f"  {'cible (récoltée)':16s} {r['target']}")
    print(f"  {'contexte':16s} {r.get('context', '')}")
    print(f"  {'fichiers':16s} {len(r['paths'])}")
    for p in r["paths"][:6]:
        print(f"    {p}")
    if len(r["paths"]) > 6:
        print(f"    … {len(r['paths']) - 6} autres")
    comp = r.get("composition", {})
    tx = meta.get("taxonomy", {})
    print(f"\n  composition selon {tx.get('system')} (snapshot {tx.get('snapshot')}) — "
          f"{comp.get('n_known')} tips reconnus, {comp.get('n_unknown')} inconnus")
    for c, n in list(comp.get("clades", {}).items())[:14]:
        alt = cm.get(c, {})
        tr = ("  ≈ " + ", ".join(f"{s}:{v}" for s, v in list(alt.items())[:3])) if alt else ""
        print(f"    {c:28s} {n:5d}{tr}")
    if comp.get("n_clades", 0) > 14:
        print(f"    … {comp['n_clades'] - 14} autres clades")
    if tips[:3]:
        print(f"\n  premiers taxons : {', '.join(tips[:6])}")


def cmd_stats(root: Path) -> None:
    recs, taxa, post, _ = load(root)
    meta = json.loads((root / INDEX_DIR / META_FILE).read_text())
    n_files = sum(len(r["paths"]) for r in recs)
    topo = Counter(r.get("topo_sha") for r in recs if r.get("topo_sha"))
    tset = Counter(r.get("taxa_sha") for r in recs)
    annot = sum(1 for r in recs if r.get("note"))
    print(f"{len(recs)} arbres uniques · {n_files} occurrences sur disque · "
          f"{len(post)} taxons distincts")
    print(f"topologies distinctes : {len(topo)} · jeux de taxons distincts : {len(tset)}")
    # Rapporter les questions au TOTAL des arbres diviserait le taux par trois : un
    # arbre de départ ou un réplicat n'a pas de question propre. Même piège que le
    # taux de support, rectifié en P52.6 — la population de référence est celle des
    # arbres de résultat.
    res = [r for r in recs if r.get("independent")]
    qa = sum(1 for r in res if r.get("note"))
    tg = sum(1 for r in res if r.get("target"))
    doc = sum(1 for r in res if r.get("note") or r.get("target"))
    print(f"question renseignée   : {qa}/{len(res)} arbres de résultat "
          f"(+ {tg} cibles récoltées d'un pipeline, {doc} documentés au total, "
          f"{100 * doc / len(res):.1f} %)")
    print("outils   :", ", ".join(f"{k}={v}" for k, v in
                                  Counter(r.get("tool") for r in recs).most_common()))
    print("projets  :", ", ".join(f"{k}={v}" for k, v in
                                  Counter(r.get("project") for r in recs).most_common(8)))
    szs = sorted(r.get("n_tips", 0) for r in recs)
    if szs:
        print(f"taille   : min={szs[0]} médiane={szs[len(szs) // 2]} max={szs[-1]}")
    print(f"avec supports : {sum(1 for r in recs if r.get('has_support'))} · "
          f"enracinés : {sum(1 for r in recs if r.get('rooted'))} · "
          f"modèle connu : {sum(1 for r in recs if r.get('model'))}")
    print(f"taxonomie : {meta.get('taxonomy', {}).get('system')} "
          f"(snapshot {meta.get('taxonomy', {}).get('snapshot')})")
    dup = [r for r in recs if len(r["paths"]) > 1]
    if dup:
        print(f"redondance : {len(dup)} arbres présents en plusieurs exemplaires "
              f"({sum(len(r['paths']) for r in dup)} fichiers)")


def cmd_annotate(root: Path, tid: str, question: str) -> None:
    d = root / INDEX_DIR
    f = d / NOTES_FILE
    notes = json.loads(f.read_text()) if f.exists() else {}
    recs, _, _, _ = load(root)
    hit = [r for r in recs if r["tree_id"].startswith(tid)]
    if not hit:
        print("aucun arbre avec cet identifiant")
        return
    notes[hit[0]["tree_id"]] = question
    f.write_text(json.dumps(notes, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{hit[0]['tree_id']} : question enregistrée ({len(notes)} au total)")


def _load_tree_text(root: Path, rec: dict) -> str | None:
    loc = rec["paths"][0]
    idx = 0
    if "#" in loc:
        loc, k = loc.rsplit("#", 1)
        idx = int(k)
    p = root / loc
    if not p.exists():
        return None
    try:
        trees = split_trees(p.read_text(errors="replace"))
    except OSError:
        return None
    return trees[idx] if idx < len(trees) else None


def cmd_support(root: Path, a) -> None:
    """Fréquence à laquelle un groupe forme un clade À TRAVERS la forêt.

    C'est la statistique que la bibliothèque rend possible et qu'aucun arbre
    isolé ne donne. Un bootstrap mesure la robustesse d'un clade au rééchan-
    tillonnage des SITES, dans un seul arbre, sous un seul modèle, sur un seul
    jeu de taxons. Ici on mesure sa robustesse au changement d'échantillonnage
    des TAXONS, de modèle, d'outil et d'analyste — un clade qui survit à
    quarante reconstructions indépendantes est appuyé autrement qu'un clade à
    100 de bootstrap dans l'unique arbre où il a jamais été testé.

    Réserves à porter avec le chiffre : les arbres ne sont pas indépendants (ils
    partagent des alignements, une référence H37Rv, un pipeline et des biais),
    et un groupe absent d'un arbre n'y est pas réfuté, il n'y est pas testé.
    """
    recs, taxa, _, _ = load(root)
    want = set(read_taxa_arg(a.taxa))
    recs = _filters(recs, a)
    tested = mono = 0
    rows = []
    for r in recs:
        tips = taxa.get(r["tree_id"], [])
        acc = {}
        for t in tips:
            m = ACC_RE.search(t)
            acc[m.group(1) if m else t] = t
        inter = want & set(acc)
        if len(inter) < max(3, a.min or 3):
            continue
        txt = _load_tree_text(root, r)
        if not txt:
            continue
        tr = parse_newick(txt)
        if tr.error:
            continue
        parts, total, names = splits_set(tr)
        if not parts:
            continue
        x = 0
        for k in inter:
            x ^= taxon_hash(acc[k])
        ok = min(x & ((1 << 64) - 1), (total ^ x) & ((1 << 64) - 1)) in parts
        tested += 1
        mono += ok
        rows.append((ok, len(inter), r))
    if not tested:
        print("aucun arbre ne contient assez de ces taxons pour trancher")
        return
    rows.sort(key=lambda z: (-z[0], -z[1]))
    for ok, k, r in rows[:a.k]:
        print(f"  {'clade   ' if ok else 'éclaté  '} {k:4d}/{len(want):<4d} taxons  "
              f"{r.get('n_tips', 0):6d} tips  {r.get('project', '')[:20]:20s} "
              f"{r.get('tool', '')[:8]:8s} {r.get('mtime', ''):10s} {r['tree_id']}")
    print(f"\nmonophylétique dans {mono}/{tested} arbres ({100 * mono / tested:.0f} %) "
          f"— arbres NON indépendants (mêmes alignements, même référence, même "
          f"pipeline) : un taux n'est pas une probabilité postérieure.")


def cmd_forest(root: Path, a) -> None:
    """Sortie machine : la liste des chemins d'une forêt, pour un autre outil."""
    recs, taxa, _, _ = load(root)
    recs = _filters(recs, a)
    if a.clade:
        recs = [r for r in recs
                if sum(n for c, n in r.get("composition", {}).get("clades", {}).items()
                       if c == a.clade or c.startswith(a.clade + ".")) >= (a.min or 1)]
    if a.taxa:
        want = set(read_taxa_arg(a.taxa))
        recs = [r for r in recs if want & set(taxa.get(r["tree_id"], []))]
    for r in recs[:a.k]:
        print(f"{r['tree_id']}\t{r.get('n_tips', 0)}\t{r.get('tool', '')}\t"
              f"{r.get('mtime', '')}\t{r['paths'][0]}")



# --- Ce que les manuscrits citent -------------------------------------------

FIG_ENV = re.compile(r"\\begin\{(figure\*?|sidewaysfigure)\}(.*?)\\end\{\1\}", re.S)
INCLUDE = re.compile(r"\\includegraphics\s*(?:\[[^\]]*\])?\s*\{([^}]+)\}")
CAPTION = re.compile(r"\\caption\s*\{")
# Un arbre REPRÉSENTÉ : l'objet de la figure est l'arbre lui-même.
SHOWS_TREE = re.compile(
    r"\b(phylogenetic tree|phylogeny|phylogenies|cladogram|dendrogram|"
    r"(?:ML|maximum[- ]likelihood|neighbour[- ]joining|neighbor[- ]joining|NJ|"
    r"time[- ]?scaled|dated|consensus|constraint)\s+tree|tree\s+(?:of|inferred|showing|"
    r"with|for)|topology|topologies|arbre phylog|monophyl|paraphyl)", re.I)
# Un DÉRIVÉ : la figure se calcule sur un arbre sans le montrer.
DERIVED = re.compile(
    r"\b(root[- ]to[- ]tip|lineage[- ]through[- ]time|\bLTT\b|skyline|skygrid|"
    r"tMRCA|time to the most recent common ancestor|ancestral state|ancestral "
    r"reconstruction|\bASR\b|Robinson[- ]Foulds|patristic|THD|haplotypic density|"
    r"branch length|divergence time)", re.I)
# Ce qui, dans une légende, désigne une figure qui n'est PAS un arbre.
NOT_TREE = re.compile(
    r"\b(heatmap|bar chart|barplot|bar plot|boxplot|box plot|scatter|histogram|"
    r"world map|geographic distribution|pie chart|venn|flowchart|sequence diagram|"
    r"pipeline|violin|rarefaction|regression of|schematic overview|"
    # « topology » désigne aussi le repliement d'une protéine : sans ce garde-fou,
    # toute figure de structure entre dans le décompte des figures d'arbre.
    r"pLDDT|ESMFold|AlphaFold|catalytic|active[- ]site|residues?\b|\bfold\b)", re.I)

TREE_LITERAL = re.compile(
    r"[\"']([^\"'\n]*(?:bestTree|bestTreeCollapsed|\.nwk|\.newick|\.treefile|"
    r"\.contree|\.support|\.tree|\.nex|\.nexus)[^\"'\n]*)[\"']")
# « 181~taxa », « 91-taxon dataset », « 151 representative MTBC genomes » : le
# compte et son unité sont séparés tantôt par un tilde LaTeX, tantôt par un
# trait d'union, tantôt par deux mots d'adjectifs.
CAP_COUNT = re.compile(
    r"(\d[\d,~\s\\]{0,9})[-~ ]?(?:[A-Za-z.]+[ ]){0,2}"
    r"(?:taxa|taxon|tips?|strains?|genomes?|isolates?)\b", re.I)


def _brace_body(s: str, open_idx: int) -> str:
    """Contenu d'une accolade LaTeX correctement appariée."""
    depth = 0
    for i in range(open_idx, len(s)):
        if s[i] == "{":
            depth += 1
        elif s[i] == "}":
            depth -= 1
            if depth == 0:
                return s[open_idx + 1:i]
    return s[open_idx + 1:]


def _detex(x: str) -> str:
    x = re.sub(r"\\[a-zA-Z]+\*?\s*", " ", x)
    return re.sub(r"\s+", " ", x.replace("{", " ").replace("}", " ")).strip()


def _fig_kind(caption: str, figname: str) -> str | None:
    """`arbre`, `dérivé`, ou None. Le nom du fichier ne tranche jamais seul."""
    namehint = re.search(r"tree|phylo|arbre|cladogram|topolog|dendro|itol", figname, re.I)
    if SHOWS_TREE.search(caption) and not NOT_TREE.search(caption):
        return "arbre"
    if namehint and not NOT_TREE.search(caption):
        return "arbre"
    if DERIVED.search(caption):
        return "dérivé"
    return None


def _manuscript_figures(root: Path) -> list[dict]:
    """Figures des manuscrits du dépôt qui montrent un arbre ou en dérivent."""
    out = []
    for tex in sorted(root.rglob("main.tex")):
        if ".git" in tex.parts or tex.parts[len(root.parts)].startswith("."):
            continue
        try:
            s = tex.read_text(errors="replace")
        except OSError:
            continue
        for m in FIG_ENV.finditer(s):
            body = m.group(2)
            figs = INCLUDE.findall(body)
            if not figs:
                continue
            cm = CAPTION.search(body)
            cap = _detex(_brace_body(body, cm.end() - 1)) if cm else ""
            kind = _fig_kind(cap, " ".join(figs))
            if kind:
                out.append({"tex": str(tex.relative_to(root)),
                            "project": tex.relative_to(root).parts[0],
                            "figs": figs, "caption": cap, "kind": kind})
    return out


def _tree_paths_in_scripts(root: Path, project: str, stem: str) -> list[str]:
    """Chemins d'arbres littéraux des scripts du projet qui nomment cette figure."""
    hits = []
    base = root / project
    if not base.is_dir():
        return hits
    for pat in ("*.py", "*.sh", "*.R", "*.ipynb"):
        for sc in base.rglob(pat):
            if ".git" in sc.parts:
                continue
            try:
                txt = sc.read_text(errors="replace")
            except OSError:
                continue
            if stem in txt:
                hits.extend(TREE_LITERAL.findall(txt))
    return hits


def _norm_literal(c: str) -> str | None:
    """Suffixe de chemin exploitable, ou None.

    Deux pièges payés : une f-string `{ROOT}/a/T3.raxml.bestTree` doit rendre sa
    part littérale, et un fragment d'extension `.treefile` (issu de
    f"{p}.treefile") ressemble à un nom de fichier sans en être un.
    """
    if "*" in c or " " in c:
        return None
    if "}" in c:
        c = c[c.rindex("}") + 1:]
    if "{" in c:
        return None
    c = c.lstrip("./").lstrip("/")
    b = os.path.basename(c)
    if not b or b.startswith(".") or not re.fullmatch(r"[A-Za-z0-9_.\-]+", b):
        return None
    return c


def cmd_cite(root: Path, a) -> None:
    """Quels arbres de la forêt un manuscrit du dépôt montre-t-il ?

    Un manuscrit ne cite jamais un `tree_id` : il inclut une figure. Le lien
    figure → arbre se reconstruit par le script qui a produit la figure, et à
    défaut par le nombre de feuilles que la légende annonce elle-même.
    """
    recs, _, _, notes = load(root)
    byname: dict[str, list[dict]] = {}
    bypath: dict[str, dict] = {}
    for r in recs:
        for p in r["paths"]:
            pp = p.split("#")[0]
            byname.setdefault(os.path.basename(pp), []).append(r)
            bypath[pp] = r
    ambiguous = {n for n, v in byname.items() if len({x["tree_id"] for x in v}) > 3}
    byproject: dict[str, list[dict]] = {}
    for r in recs:
        byproject.setdefault(r["project"], []).append(r)

    figures = _manuscript_figures(root)
    if a.project:
        figures = [f for f in figures if f["project"] == a.project]
    rows, cited = [], {}
    for f in figures:
        tids, how, dead = set(), set(), set()
        for fig in f["figs"]:
            stem = os.path.splitext(os.path.basename(fig))[0]
            for lit in _tree_paths_in_scripts(root, f["project"], stem):
                c = _norm_literal(lit)
                if not c:
                    continue
                b = os.path.basename(c)
                if "/" in c:
                    hit = [r for p, r in bypath.items() if p.endswith(c)]
                    if hit:
                        tids.update(r["tree_id"] for r in hit)
                        how.add("chemin")
                        continue
                # Le projet du manuscrit prime toujours : `timetree.nwk` existe
                # dans plusieurs projets, et celui du manuscrit est le bon.
                same = [r for r in byname.get(b, []) if r["project"] == f["project"]]
                if same:
                    tids.update(r["tree_id"] for r in same)
                    how.add("nom+projet")
                    continue
                if b in byname and b not in ambiguous:
                    tids.update(r["tree_id"] for r in byname[b])
                    how.add("nom")
                    continue
                dead.add(c)
        if not tids:                      # repli : le compte annoncé par la légende
            want = set()
            for m in CAP_COUNT.finditer(f["caption"]):
                n = re.sub(r"[^0-9]", "", m.group(1))
                if n and 3 <= int(n) <= 60000:
                    want.add(int(n))
            hit = [r for r in byproject.get(f["project"], [])
                   if r.get("n_tips") in want and r["independent"]]
            if hit:
                tids.update(r["tree_id"] for r in hit)
                how.add("n_tips")
        for t in tids:
            cited.setdefault(t, []).append((f["project"], f["figs"][0]))
        rows.append({**f, "tids": sorted(tids), "how": sorted(how), "dead": sorted(dead)})

    shown = [r for r in rows if r["kind"] == "arbre"]
    unres = [r for r in shown if not r["tids"]]
    todo = [t for t in cited if t not in notes]
    print(f"manuscrits parcourus : {len({r['tex'] for r in rows})} | figures d'arbre : "
          f"{len(shown)} | figures dérivées : {len(rows) - len(shown)}")
    print(f"arbres cités et résolus : {len(cited)} | déjà annotés : "
          f"{len(cited) - len(todo)} | SANS QUESTION : {len(todo)}")
    print(f"figures d'arbre non résolues : {len(unres)}\n")
    if a.arg != "todo":
        for r in sorted(rows, key=lambda x: (x["project"], x["figs"][0])):
            if a.arg == "unresolved" and r["tids"]:
                continue
            mark = "·" if r["kind"] == "arbre" else "~"
            print(f"{mark} {r['project']:26s} {os.path.basename(r['figs'][0])[:34]:34s} "
                  f"{'/'.join(r['how']) or '—':12s} {len(r['tids'])} arbre(s)"
                  + (f"  MORT: {r['dead']}" if r["dead"] else ""))
    else:
        for t in sorted(todo, key=lambda x: cited[x][0]):
            r = next(x for x in recs if x["tree_id"] == t)
            src = ", ".join(f"{p}::{os.path.basename(g)}" for p, g in cited[t][:2])
            print(f"{t}  n_tips={r.get('n_tips', 0):5d}  {r['role']:14s} "
                  f"{str(r.get('tool')):9s} {r['mtime']}  {src}")
            print(f"        {r['paths'][0]}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("Garde-fou")[0])
    ap.add_argument("cmd", choices=["harvest", "find", "show", "stats", "annotate",
                                    "support", "forest", "diverge", "clades", "unstable",
                                    "cite"])
    ap.add_argument("arg", nargs="?", default="")
    ap.add_argument("arg2", nargs="?", default="")
    ap.add_argument("--root", default=None)
    ap.add_argument("--taxa", help="liste inline, fichier de noms, ou FASTA")
    ap.add_argument("--clade", help="clade de la taxonomie locale (guyeux/bdd-actuelle)")
    ap.add_argument("--min", type=int, help="nombre minimal de taxons du clade")
    ap.add_argument("--min-tips", type=int)
    ap.add_argument("--max-tips", type=int)
    ap.add_argument("--tool")
    ap.add_argument("--project")
    ap.add_argument("--since", help="AAAA-MM-JJ")
    ap.add_argument("--support", action="store_true", help="seulement avec supports")
    ap.add_argument("--rooted", action="store_true", help="seulement enracinés")
    ap.add_argument("--all", action="store_true",
                    help="inclut les arbres intermédiaires (départ, réplicats ML et "
                         "bootstrap), écartés par défaut car non indépendants")
    ap.add_argument("-k", type=int, default=12)
    ap.add_argument("--scope", choices=["global", "focalise", "tous"], default="tous",
                    help="`clades` : restreindre aux arbres GLOBAUX ou aux arbres FOCALISÉS "
                         "sur un clade. Ces deux populations ne se comparent pas (P62) : un "
                         "arbre focalisé ne peut confirmer que les sous-clades de son focus.")
    a = ap.parse_args()
    root = Path(a.root).resolve() if a.root else find_root(Path.cwd())

    if a.cmd == "harvest":
        harvest(root)
    elif a.cmd == "find":
        cmd_find(root, a)
    elif a.cmd == "forest":
        cmd_forest(root, a)
    elif a.cmd == "cite":
        cmd_cite(root, a)
    elif a.cmd == "unstable":
        cmd_unstable(root, a)
    elif a.cmd == "clades":
        cmd_clades(root, a)
    elif a.cmd == "diverge":
        cmd_diverge(root, a)
    elif a.cmd == "support":
        if not a.taxa:
            print("usage : forest.py support --taxa A,B,C", file=sys.stderr)
            return 2
        cmd_support(root, a)
    elif a.cmd == "show":
        cmd_show(root, a.arg)
    elif a.cmd == "annotate":
        if not a.arg or not a.arg2:
            print('usage : forest.py annotate <tree_id> "<question d\'origine>"',
                  file=sys.stderr)
            return 2
        cmd_annotate(root, a.arg, a.arg2)
    else:
        cmd_stats(root)
    return 0



# --- Divergence topologique -------------------------------------------------

def rf_distance(pa: set, pb: set, ntax: int) -> tuple[int, float]:
    """Robinson-Foulds sur les splits canoniques, et sa version normalisée.

    Le maximum théorique pour deux arbres binaires non enracinés à n feuilles est
    2(n-3) ; on normalise par le nombre de splits réellement présents des deux
    côtés, ce qui reste borné à 1 et ne pénalise pas un arbre partiellement
    résolu (polytomies) comme s'il était en désaccord.
    """
    d = len(pa ^ pb)
    denom = len(pa) + len(pb)
    return d, (d / denom if denom else 0.0)


def cmd_diverge(root: Path, a) -> None:
    """Jeux de taxons IDENTIQUES reconstruits en topologies DIFFÉRENTES.

    Question mesurable derrière ce mode : quand le dépôt refait le même arbre,
    obtient-il le même arbre ? Et si non, l'écart tient-il à la stochastique de
    l'inférence, aux données, ou à l'outil ?

    La réponse ne se lit pas dans un chiffre global : elle exige de stratifier
    par CAUSE POSSIBLE, sinon on additionne des divergences de natures
    différentes. Trois strates ici, de la plus bénigne à la plus lourde de
    conséquences — même outil ET même alignement (l'optimisation ML n'a pas
    convergé au même optimum), même outil et alignements différents (les données
    d'entrée ne sont pas les mêmes), outils différents (l'inférence elle-même).
    """
    recs, taxa, _, _ = load(root)
    recs = [r for r in recs if r.get("independent")] if not getattr(a, "all", False) else recs
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in recs:
        if r.get("taxa_sha") and r.get("topo_sha") and r.get("n_tips", 0) >= 4:
            groups[r["taxa_sha"]].append(r)
    rows = []
    for tsha, g in groups.items():
        if len({r["topo_sha"] for r in g}) < 2:
            continue
        # une topologie par empreinte : comparer deux fichiers identiques n'apprend rien
        uniq: dict[str, dict] = {}
        for r in g:
            uniq.setdefault(r["topo_sha"], r)
        parts: dict[str, set] = {}
        for th, r in uniq.items():
            txt = _load_tree_text(root, r)
            if not txt:
                continue
            tr = parse_newick(txt)
            if tr.error:
                continue
            p, _tot, _nm = splits_set(tr)
            # Un arbre de CONTRAINTE (topologie partiellement spécifiée pour
            # forcer un clade pendant l'inférence) ou un squelette ne porte que
            # quelques splits. Le comparer à une reconstruction complète donne
            # mécaniquement une distance maximale — mesuré : `contrainte_218.nwk`
            # et son unique split ressortaient à RF 1,000 contre un arbre à 286
            # splits, ce qui ne dit rien d'autre que « ces deux fichiers ne sont
            # pas de même nature ». On exige donc une résolution minimale.
            if p and len(p) >= 0.25 * max(1, r.get("n_tips", 0) - 3):
                parts[th] = p
        if len(parts) < 2:
            continue
        ks = list(parts)
        ds = []
        for i in range(len(ks)):
            for j in range(i + 1, len(ks)):
                _d, nd = rf_distance(parts[ks[i]], parts[ks[j]], g[0].get("n_tips", 0))
                ds.append(nd)
        tools = {r.get("tool") for r in uniq.values()}
        # Le chemin d'alignement est normalisé avant comparaison : un même fichier
        # est écrit tantôt en absolu tantôt en relatif selon le répertoire d'où
        # l'outil a été lancé, et le compter deux fois fait basculer un groupe de
        # la strate « optimisation » vers « alignements », c'est-à-dire attribue à
        # des données différentes ce qui n'est qu'une différence de notation.
        aligns = {os.path.basename(str(r.get("alignment")))
                  for r in uniq.values() if r.get("alignment")}
        models = {r.get("model") for r in uniq.values() if r.get("model")}
        projs = {r.get("project") for r in uniq.values()}
        if len(tools) > 1:
            strate = "outils"
        elif len(aligns) > 1:
            strate = "alignements"
        elif len(aligns) == 1:
            strate = "optimisation"
        else:
            strate = "indéterminé"
        rows.append({
            "taxa_sha": tsha, "n_tips": g[0].get("n_tips", 0), "n_arbres": len(g),
            "n_topo": len(parts), "rf_med": statistics.median(ds), "rf_max": max(ds),
            "strate": strate, "tools": sorted(tools), "projets": sorted(projs),
            "n_align": len(aligns), "models": sorted(m for m in models if m),
        })
    if not rows:
        print("aucun jeu de taxons reconstruit en plusieurs topologies")
        return
    rows.sort(key=lambda r: -r["rf_max"])
    print(f"{'tips':>6} {'arb':>4} {'top':>4} {'RFméd':>6} {'RFmax':>6} {'strate':13s} "
          f"{'outils':18s} projets")
    for r in rows[:a.k]:
        print(f"{r['n_tips']:6d} {r['n_arbres']:4d} {r['n_topo']:4d} {r['rf_med']:6.3f} "
              f"{r['rf_max']:6.3f} {r['strate']:13s} {','.join(r['tools'])[:18]:18s} "
              f"{','.join(r['projets'])[:40]}")
    print()
    by = Counter(r["strate"] for r in rows)
    print(f"{len(rows)} jeux de taxons à topologies multiples · par strate : "
          + ", ".join(f"{k}={v}" for k, v in by.most_common()))
    for st in ("optimisation", "alignements", "outils"):
        sel = [r["rf_med"] for r in rows if r["strate"] == st]
        if sel:
            print(f"  {st:13s} n={len(sel):3d}  RF normalisée médiane {statistics.median(sel):.3f} "
                  f"(min {min(sel):.3f}, max {max(sel):.3f})")
    print("\nUne RF non nulle n'est pas en soi une anomalie : deux optima ML voisins "
          "diffèrent sur les branches courtes. Ce qui compte est la strate et l'ampleur.")


# --- Épreuve des clades sur la forêt ---------------------------------------

def tree_scope(present: set, s2c: dict, frac: float = 0.95) -> tuple[str, str]:
    """Un arbre est-il GLOBAL ou FOCALISÉ sur un clade ? (piste P62)

    Un arbre focalisé sur `L4.1` ne peut pas mettre `L4.1` à l'épreuve, ni aucun
    de ses ancêtres : ses feuilles y appartiennent toutes. Agréger son taux de
    monophylie avec celui d'un arbre global fabrique donc une progression qui
    mesure l'essor des arbres focalisés, pas un gain de qualité taxonomique — le
    dépôt en donnait un exemple net, 14,8 % en 2021 contre 91,5 % en août 2026,
    l'essentiel de l'écart venant des 4 277 arbres focalisés de
    `lineage_navigator` sur 7 122.

    La portée se lit en descendant la hiérarchie des étiquettes tant qu'une même
    composante rassemble au moins `frac` des feuilles ÉTIQUETÉES. Le dénominateur
    reste le nombre total d'étiquetées à chaque profondeur, de sorte que le focus
    rendu couvre bien 95 % de l'arbre et pas 95 % d'un sous-ensemble déjà réduit.
    Rend `("global", "")`, `("focalise", "L4.1")`, ou `("indetermine", "")` quand
    trop peu de feuilles sont rattachées à la taxonomie pour trancher.
    """
    labs = [s2c[x].split(".") for x in present if x in s2c]
    n = len(labs)
    if n < 8 or n < 0.5 * len(present):
        return ("indetermine", "")
    dom: list[str] = []
    cur = labs
    for depth in range(12):
        c = Counter(p[depth] for p in cur if len(p) > depth)
        if not c:
            break
        top, k = c.most_common(1)[0]
        if k < frac * n:
            break
        dom.append(top)
        cur = [p for p in cur if len(p) > depth and p[depth] == top]
    return ("focalise", ".".join(dom)) if dom else ("global", "")


def cmd_clades(root: Path, a) -> None:
    """Chaque clade de la taxonomie ressort-il monophylétique dans la forêt ?

    L'ordre du parcours n'est pas indifférent : on itère sur les ARBRES et non
    sur les clades. Un arbre coûte un parsing et un calcul de splits ; les 739
    clades s'y testent ensuite par un XOR chacun. L'ordre inverse relirait chaque
    arbre autant de fois qu'il contient de clades.

    **Ce que la mesure ne peut pas établir, et qu'il faut dire avant de la lire.**
    Les arbres du dépôt partagent alignements, référence H37Rv et pipeline ; pire,
    les clades sont DÉFINIS par des marqueurs qui servent aussi à bâtir les
    alignements. La circularité est donc structurelle et un taux de confirmation
    élevé ne prouve rien. Deux sorties y échappent, et ce sont les seules à lire :
    les clades testés dans UN SEUL arbre — jamais mis à l'épreuve — et ceux qui
    ÉCHOUENT malgré la circularité, c'est-à-dire qu'un groupe que tout conspire à
    confirmer s'éclate quand même.
    """
    import random
    recs, taxa, post, _ = load(root)
    res = [r for r in recs if r.get("independent")]
    if getattr(a, "since", None):
        # Restreindre aux arbres POSTÉRIEURS à une date est la seule façon
        # d'interroger un clade plutôt que l'âge des arbres : avant sa définition,
        # un clade n'a aucune raison d'y être monophylétique.
        res = [r for r in res if r.get("mtime", "") >= a.since]
    # P62.1 : `--min-tips`/`--max-tips` existaient dans l'analyseur d'arguments mais
    # n'étaient appliqués que par `find`. Sans eux, `clades` mélange un arbre de
    # 20 feuilles et un arbre de 30 000, dont la difficulté n'a rien de commun :
    # les câbler ici est la condition d'une comparaison à périmètre égal.
    if getattr(a, "min_tips", None):
        res = [r for r in res if r.get("n_tips", 0) >= a.min_tips]
    if getattr(a, "max_tips", None):
        res = [r for r in res if r.get("n_tips", 0) <= a.max_tips]
    tax = load_taxonomy(root)
    # Convention dir-mixte du dépôt (décision CG 2026-07-04) : les souches basales
    # ou non encore classées vivent dans le conteneur NU du clade, et ses
    # sous-clades ont leurs propres répertoires. Le contenu d'un conteneur nu est
    # donc un GRADE, jamais un clade — le tester tel quel demande à un paraphylum
    # d'être monophylétique, ce qu'il n'est pas par construction. Mesuré avant
    # correction : `L4.1` (8 389 souches, 7 sous-clades) ressortait « éclaté »,
    # ce qui était le résultat attendu et non une anomalie. Un nœud interne est
    # donc testé avec TOUTE sa descendance ; seules les feuilles se testent seules.
    direct: dict[str, set[str]] = defaultdict(set)
    for st, cl in tax["strain2clade"].items():
        direct[cl].add(st)
    children = {c: [d for d in direct if d.startswith(c + ".")] for c in direct}
    clade2strains: dict[str, set[str]] = {}
    for c, own in direct.items():
        u = set(own)
        for d in children[c]:
            u |= direct[d]
        clade2strains[c] = u
    internal = {c for c, kids in children.items() if kids}
    # La détection de descendance procède par PRÉFIXE, ce qui rate un renommage :
    # `bdd/actuelle/L1` est un pool de 21 163 souches sans aucun `L1.*`, sa
    # subdivision vivant sous `L_1.*`. `L1` passe donc pour une feuille géante et
    # ses « échecs » sont en réalité l'artefact du conteneur nu, sous un autre nom.
    # On ne devine pas le renommage ; on signale la forme suspecte.
    suspects = {c for c in direct
                if c not in internal and len(direct[c]) >= 500}
    MASK = (1 << 64) - 1
    tested = Counter()
    mono = Counter()
    seen_trees: dict[str, set[str]] = defaultdict(set)
    rng = random.Random(20260830)
    null_tested = null_mono = 0
    # P62.2 : plus JAMAIS une seule série par mois. Les arbres globaux et les
    # arbres focalisés ne mesurent pas la même chose, et les additionner produit
    # une courbe qui ne dit rien. On tient donc deux séries distinctes, et le
    # recensement des portées qui permet de les lire.
    by_age: dict[str, dict[str, list]] = {
        "global": defaultdict(lambda: [0, 0]), "focalise": defaultdict(lambda: [0, 0])}
    scope_n = Counter()
    focus_n = Counter()
    tested_g = Counter()
    mono_g = Counter()

    for r in res:
        tips = taxa.get(r["tree_id"], [])
        if len(tips) < 8:
            continue
        acc: dict[str, str] = {}
        for t in tips:
            m = ACC_RE.search(t)
            if m:
                acc[m.group(1)] = t
        if len(acc) < 8:
            continue
        txt = _load_tree_text(root, r)
        if not txt:
            continue
        tr = parse_newick(txt)
        if tr.error:
            continue
        parts, total, names = splits_set(tr)
        if not parts:
            continue
        present = set(acc)
        kind, focus = tree_scope(present, tax["strain2clade"])
        scope_n[kind] += 1
        if kind == "focalise":
            focus_n[focus] += 1
        want = getattr(a, "scope", "tous")
        if want != "tous" and kind != want:
            continue
        hashes = {k: taxon_hash(acc[k]) for k in present}
        sizes = []
        for cl, strains in clade2strains.items():
            inter = present & strains
            k = len(inter)
            if k < 3 or k > len(present) - 2:
                continue          # trivial d'un côté ou de l'autre
            x = 0
            for s in inter:
                x ^= hashes[s]
            ok = min(x & MASK, (total ^ x) & MASK) in parts
            tested[cl] += 1
            mono[cl] += ok
            if kind == "global":
                tested_g[cl] += 1
                mono_g[cl] += ok
            seen_trees[cl].add(r["tree_id"])
            sizes.append(k)
            # Stratifier par ANCIENNETÉ de l'arbre est indispensable, et ce n'est
            # pas un raffinement. Un arbre porte les étiquettes de la taxonomie du
            # jour où il a été construit ; un clade redéfini depuis rassemble des
            # souches qui y étaient dispersées, et son « échec » ne dit rien de sa
            # validité — il mesure la distance entre la taxonomie d'aujourd'hui et
            # un arbre d'hier. Seul un désaccord avec un arbre RÉCENT interroge le
            # clade lui-même.
            if kind in by_age:
                by_age[kind][r.get("mtime", "")[:7]][0] += 1
                by_age[kind][r.get("mtime", "")[:7]][1] += ok
        # Modèle nul : mêmes tailles, mêmes arbres, membres tirés au hasard.
        # Sans lui, un taux de monophylie élevé pourrait n'être qu'un artefact de
        # la structure des arbres, et la mesure ne mesurerait rien.
        pool = sorted(present)
        for k in sizes[:a.k if a.k else 12]:
            grp = rng.sample(pool, k)
            x = 0
            for s in grp:
                x ^= hashes[s]
            null_tested += 1
            null_mono += min(x & MASK, (total ^ x) & MASK) in parts

    if not tested:
        print("aucun clade testable dans la forêt")
        return
    rows = []
    for cl, n in tested.items():
        rows.append((cl, len(clade2strains[cl]), n, mono[cl], mono[cl] / n))
    jamais = [x for x in rows if x[2] == 1]
    echecs = [x for x in rows if x[2] >= 3 and x[4] < 0.5]
    echecs.sort(key=lambda x: (x[4], -x[2]))
    untested = [c for c in clade2strains if c not in tested and len(clade2strains[c]) >= 3]

    if suspects:
        print(f"[garde] {len(suspects)} clades sans descendance déclarée dépassent 500 souches "
              f"({', '.join(sorted(suspects)[:5])}…) : vérifier qu'une subdivision n'existe pas "
              f"sous un AUTRE nom, auquel cas ce sont des conteneurs nus et leur échec est attendu.")
    tot_scope = sum(scope_n.values())
    if tot_scope:
        top_focus = ", ".join(f"{c}×{n}" for c, n in focus_n.most_common(4))
        print(f"[portée] {scope_n['global']} arbres GLOBAUX, {scope_n['focalise']} FOCALISÉS "
              f"sur un clade, {scope_n['indetermine']} indéterminés (taxonomie trop incomplète)"
              + (f" · focus dominants : {top_focus}" if top_focus else ""))
        if getattr(a, "scope", "tous") != "tous":
            print(f"[portée] mesure restreinte aux arbres « {a.scope} » (--scope)")
    print(f"{len(rows)} clades testés au moins une fois sur {len(clade2strains)} de la taxonomie "
          f"· {len(untested)} jamais testables (absents de la forêt ou trop peu représentés)")
    print(f"clades testés dans UN SEUL arbre : {len(jamais)}")
    print(f"clades échouant dans plus de la moitié des arbres (≥3 tests) : {len(echecs)}\n")
    if jamais:
        # La sortie la moins contestable du mode : un clade vu dans un seul arbre
        # n'a jamais été mis à l'épreuve, indépendamment de toute question de
        # circularité ou d'obsolescence.
        print("clades vus dans UN SEUL arbre (jamais mis à l'épreuve) :")
        for cl, ns, n, m, t in sorted(jamais, key=lambda x: -x[1])[:20]:
            kind = "nœud" if cl in internal else "feuille"
            print(f"  {cl[:34]:34s} {ns:6d} souches {kind:8s} "
                  f"{'monophylétique' if m else 'ÉCLATÉ'}")
        print()
    # Les deux dernières colonnes restreignent la mesure aux arbres GLOBAUX : c'est
    # la seule où un échec interroge vraiment le clade, un arbre focalisé ne pouvant
    # ni confirmer ni infirmer son propre focus. Un clade qui échoue partout sauf
    # dans les arbres globaux (`n_glob` à 0) n'a en réalité jamais été testé.
    print(f"{'clade':34s} {'souches':>8} {'testé':>6} {'mono':>5} {'taux':>6}  "
          f"{'n_glob':>6} {'taux_g':>6}")
    for cl, ns, n, m, t in echecs[:a.k or 15]:
        kind = "nœud" if cl in internal else "feuille"
        ng, mg = tested_g[cl], mono_g[cl]
        tg = f"{mg / ng:6.2f}" if ng else "     —"
        print(f"{cl[:34]:34s} {ns:8d} {n:6d} {m:5d} {t:6.2f}  {ng:6d} {tg}  {kind}")
    # P62.2 : deux séries séparées, jamais une seule. La série agrégée qui existait
    # ici montait de 14,8 % (2021) à 91,5 % (août 2026) et se lisait comme un gain
    # de qualité taxonomique ; elle mesurait en fait le remplacement progressif des
    # arbres globaux par des arbres focalisés. Les juxtaposer rend l'artefact visible
    # au lieu de le dissimuler dans une moyenne.
    for kind, titre in (("global", "arbres GLOBAUX"), ("focalise", "arbres FOCALISÉS")):
        series = by_age[kind]
        if not any(n >= 50 for n, _ in series.values()):
            continue
        print(f"\ntaux de monophylie par MOIS — {titre} :")
        for mois in sorted(series):
            n, m = series[mois]
            if n >= 50:
                print(f"  {mois}  {m:6d}/{n:<6d}  {100 * m / n:5.1f} %")
    if by_age["global"] and by_age["focalise"]:
        print("  (ne pas comparer les deux séries entre elles : un arbre focalisé sur un clade "
              "ne peut pas mettre ce clade ni ses ancêtres à l'épreuve.)")
    if null_tested:
        print(f"\n[modèle nul] groupes ALÉATOIRES de mêmes tailles dans les mêmes arbres : "
              f"{null_mono}/{null_tested} monophylétiques ({100 * null_mono / null_tested:.2f} %) "
              f"contre {100 * sum(mono.values()) / sum(tested.values()):.1f} % pour les clades réels.")
    print("\nUn taux élevé ne prouve rien : les clades sont définis par des marqueurs qui servent "
          "aussi à bâtir les alignements. Lire les ÉCHECS et les clades testés une seule fois.")


# --- Stabilité du placement d'une souche -----------------------------------

def sister_sets(t: Tree, max_size: int = 20) -> dict[str, frozenset]:
    """Pour chaque feuille, l'ensemble des feuilles du plus petit clade la contenant.

    Le « voisinage » d'une souche est pris topologiquement et non par distance
    patristique : c'est plus robuste (indépendant des longueurs de branches et de
    l'enracinement), c'est directement interprétable — avec qui cette souche
    est-elle groupée ? — et c'est calculable en une passe pour toutes les feuilles
    à la fois, là où des k plus proches voisins demanderaient un parcours par
    souche. Les voisinages de plus de `max_size` feuilles sont écartés : une
    souche placée dans une grande polytomie n'a pas de voisin au sens utile.
    """
    tipset = set(t.tips)
    names = {i: t.label[i] for i in t.tips if t.label[i]}
    kids: dict[int, list[int]] = defaultdict(list)
    for i in range(t.n_nodes):
        if t.parent[i] != -1:
            kids[t.parent[i]].append(i)
    leaves: list[set[str]] = [set() for _ in range(t.n_nodes)]
    for i, nm in names.items():
        leaves[i] = {nm}
    for i in range(t.n_nodes - 1, -1, -1):
        p = t.parent[i]
        if p != -1:
            leaves[p] |= leaves[i]
    out: dict[str, frozenset] = {}
    for i, nm in names.items():
        p = t.parent[i]
        if p == -1:
            continue
        sis = leaves[p] - {nm}
        if 0 < len(sis) <= max_size:
            out[nm] = frozenset(sis)
    return out


def _major_clade(neigh: frozenset, s2c: dict) -> str | None:
    """Clade dominant d'un voisinage — la souche se rattache-t-elle au même groupe ?"""
    c = Counter(s2c[x] for x in neigh if x in s2c)
    if not c:
        return None
    top, n = c.most_common(1)[0]
    return top if n >= max(1, len(neigh) // 2) else None


def cmd_unstable(root: Path, a) -> None:
    """Souches dont le voisinage change d'un arbre à l'autre.

    **Le contrôle est ce qui fait la mesure.** Une souche change de voisins pour
    deux raisons très différentes : parce qu'elle est mal placée, ou simplement
    parce que ses voisins ne sont pas dans l'autre arbre. Seul le premier cas
    intéresse. On n'oppose donc deux arbres que si les voisins constatés dans le
    premier sont PRÉSENTS dans le second : s'ils y sont et qu'aucun n'est plus
    voisin, le désaccord porte sur la souche ; sinon le cas n'est pas testable et
    n'est pas compté — ni comme stable, ni comme instable.
    """
    recs, taxa, _, _ = load(root)
    res = [r for r in recs if r.get("independent")]
    if getattr(a, "since", None):
        res = [r for r in res if r.get("mtime", "") >= a.since]
    else:
        print("[garde] sans --since, on mesure surtout l'obsolescence de la taxonomie "
              "et des arbres, pas l'instabilité d'une souche.", file=sys.stderr)
    per_tree: dict[str, dict[str, frozenset]] = {}
    tree_taxa: dict[str, set[str]] = {}
    for r in res:
        tips = taxa.get(r["tree_id"], [])
        if len(tips) < 10:
            continue
        txt = _load_tree_text(root, r)
        if not txt:
            continue
        tr = parse_newick(txt)
        if tr.error:
            continue
        ss = sister_sets(tr)
        if not ss:
            continue
        acc = {}
        for lab in ss:
            m = ACC_RE.search(lab)
            if m:
                acc[m.group(1)] = frozenset(
                    ACC_RE.search(x).group(1) for x in ss[lab] if ACC_RE.search(x))
        if acc:
            per_tree[r["tree_id"]] = acc
            tree_taxa[r["tree_id"]] = set(acc)

    where: dict[str, list[str]] = defaultdict(list)
    for tid, acc in per_tree.items():
        for s in acc:
            where[s].append(tid)

    s2c = load_taxonomy(root)["strain2clade"]
    rows = []
    for s, tids in where.items():
        if len(tids) < 2:
            continue
        testable = disagree = 0
        for i in range(len(tids)):
            for j in range(i + 1, len(tids)):
                A, B = tids[i], tids[j]
                na, nb = per_tree[A].get(s), per_tree[B].get(s)
                if not na or not nb:
                    continue
                # Les voisins vus dans A sont-ils seulement présents dans B ?
                shared = na & tree_taxa[B]
                if not shared:
                    continue                     # non testable, et non compté
                testable += 1
                # Un désaccord de VOISIN immédiat n'est pas un désaccord de
                # placement. Dans un clade clonal dense — et le MTBC ne fait que
                # cela — deux souches à zéro ou un SNP permutent d'un arbre à
                # l'autre sans que rien ne bouge biologiquement : mesuré, 17 % des
                # souches ressortaient ainsi « instables », chiffre inexploitable.
                # Ce qui compte est le CLADE auquel la souche se rattache. On
                # compare donc le clade majoritaire de son voisinage de part et
                # d'autre, et on ne retient le désaccord que s'il change.
                ca = _major_clade(na, s2c)
                cb = _major_clade(nb, s2c)
                if ca and cb and ca != cb:
                    disagree += 1
        if testable >= (a.min or 3):
            rows.append((s, len(tids), testable, disagree, disagree / testable))
    if not rows:
        print("aucune souche testable : pas assez d'arbres comparables")
        return
    rows.sort(key=lambda x: (-x[4], -x[2]))
    tax = {"strain2clade": s2c}
    print(f"{len(rows)} souches testées sur {len(where)} présentes dans la fenêtre · "
          f"{len(per_tree)} arbres retenus")
    print(f"\n{'souche':14s} {'arbres':>6} {'paires':>7} {'désacc':>7} {'taux':>6}  clade actuel")
    for s, nt, te, di, ta in rows[:a.k or 20]:
        if ta < 0.5:
            break
        print(f"{s:14s} {nt:6d} {te:7d} {di:7d} {ta:6.2f}  {tax['strain2clade'].get(s, '?')}")
    # Sortie complète sur disque : le terminal ne montre qu'une tête de liste, or
    # la population entière est ce qui permet de mesurer un enrichissement par
    # clade, et donc de distinguer un signal d'un biais d'échantillonnage.
    out = root / INDEX_DIR / "unstable.tsv"
    with out.open("w", encoding="utf-8") as fh:
        fh.write("souche\tarbres\tpaires\tdesaccords\ttaux\tclade\n")
        for s_, nt, te, di, ta in rows:
            fh.write(f"{s_}\t{nt}\t{te}\t{di}\t{ta:.3f}\t{tax['strain2clade'].get(s_, '?')}\n")
    print(f"\nliste complète : {out}")
    n_bad = sum(1 for x in rows if x[4] >= 0.5)
    print(f"\n{n_bad} souches en désaccord dans au moins la moitié des paires TESTABLES "
          f"(voisins présents et pourtant non voisins).")
    print("Un désaccord n'est pas une erreur de la souche : il peut venir de l'arbre. "
          "Ces souches sont des CANDIDATES à vérifier (`/strain-qc`, `/species-id`), pas un verdict.")

if __name__ == "__main__":
    sys.exit(main())
