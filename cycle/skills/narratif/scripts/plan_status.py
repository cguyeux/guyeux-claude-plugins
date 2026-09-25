#!/usr/bin/env python3
"""Contrôles numériques d'un `plan_narratif.md`, pour le skill /narratif.

Ce script NE TRANCHE RIEN. Il mesure ce qu'une relecture linéaire ne sait pas
vérifier, parce que chaque contrôle exige de croiser deux fichiers ou deux
tableaux distants :

  1. ACQUIS SANS RANG — un acquis de `etat_des_decouvertes.md` §2 destiné à ce
     manuscrit (`destination : A`) mais absent du tri du plan. C'est la condition
     de la porte 2 : aucun acquis ne part à la rédaction sans que sa place ait
     été décidée.

  2. BASCULE SANS FIGURE — un point de bascule qui n'a pas de figure ou de table
     en regard. Le lecteur bascule là ; le lui montrer n'est pas optionnel.

  3. DÉPENDANCE INVERSÉE — un maillon qui dépend d'un maillon énoncé APRÈS lui.
     Le plan est un graphe orienté ; un cycle ou une inversion dit que l'ordre
     est faux, pas que la science l'est.

  4. FIGURES DU CORPS — leur nombre contre le nombre de bascules, et la présence
     d'une justification écrite pour chaque figure en excès.

  5. TAILLE PROJETÉE, puis les revues compatibles. Cette dernière sortie est une
     INFORMATION POUR LA PHASE 4, jamais une contrainte : la revue n'arbitre ni
     l'article, ni le message, ni la longueur (règle CG 2026-09-09). Si aucune
     revue ne convient, le préprint est une réponse, l'amputation n'en est pas une.

Usage :
    python3 plan_status.py [projet]
    python3 plan_status.py [projet] --json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

JOURNALS = Path.home() / ".agents" / "knowledge" / "journals" / "journals.tsv"

RANGS = {"PORTEUR", "BASCULE", "MENTION", "SUPPLEMENTAIRE", "SERENDIPITE"}

# Format réel du parc : `**Destination : A**` en gras et en fin de phrase, pas une
# ligne à part ; les valeurs vont de A à E, avec C1/C2 pour les essaimages. Même
# motif que RE_DEST de cycle_status.py, volontairement.
RE_DEST = re.compile(r"destination\s*:\s*\**(C[12]|[ABCDE])(?![\w])", re.IGNORECASE)


def _defold(s: str) -> str:
    """Majuscules sans accent, pour comparer un rang écrit SUPPLÉMENTAIRE ou non."""
    tbl = str.maketrans("ÀÂÄÉÈÊËÎÏÔÖÙÛÜÇàâäéèêëîïôöùûüç",
                        "AAAEEEEIIOOUUUCaaaeeeeiioouuuc")
    return s.translate(tbl).upper().strip()


def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def trouver_racine(depart: Path) -> Path | None:
    p = depart.resolve()
    for cand in [p, *p.parents]:
        if (cand / "cahier_de_labo.md").exists():
            return cand
    return None


def resoudre(arg: str | None) -> Path | None:
    if arg:
        p = Path(arg).expanduser()
        if not p.is_absolute():
            # Racines de repli pour un nom de projet relatif nu : défaut =
            # l'environnement pour lequel ce skill a été conçu (le plugin
            # `cycle` est domain-agnostic, ce raccourci ne l'est pas) ;
            # surchargeable par les mêmes variables que
            # `cycle-projet/cycle_status.py` et `recadrage/recadrage_signals.py`
            # (CYCLE_PROJECT_SHORTCUT_ROOT) et `init-project/init_project.py`
            # (INIT_PROJECT_CODES_ROOT).
            racine_mtbc = Path(os.environ.get(
                "CYCLE_PROJECT_SHORTCUT_ROOT",
                str(Path.home() / "docs" / "codes" / "mtbc"))).expanduser()
            racine_codes = Path(os.environ.get(
                "INIT_PROJECT_CODES_ROOT",
                str(Path.home() / "docs" / "codes"))).expanduser()
            for base in (Path.cwd(), racine_mtbc, racine_codes):
                if (base / p).exists():
                    p = base / p
                    break
        return trouver_racine(p) if p.exists() else None
    return trouver_racine(Path.cwd())


# --------------------------------- parsing -------------------------------------

def rows(txt: str, prefixe: str) -> list[list[str]]:
    """Lignes de tableau markdown dont la 1re cellule vaut <prefixe><chiffres>."""
    out = []
    pat = re.compile(r"^\s*\|\s*" + prefixe + r"\s*(\d+)\s*\|(.*)$", re.M)
    for m in pat.finditer(txt):
        cells = [c.strip() for c in m.group(2).split("|")]
        if cells and cells[-1] == "":
            cells.pop()
        out.append([prefixe + m.group(1), *cells])
    return out


def entete(txt: str) -> dict:
    """Clés `nom : valeur` avant la première section `##`."""
    head = txt.split("\n## ", 1)[0]
    d = {}
    for m in re.finditer(r"^([a-zà-ÿ][a-zà-ÿ' \-]{2,40})\s*:\s*(.+)$", head, re.M | re.I):
        d[m.group(1).strip().lower()] = m.group(2).strip()
    return d


def tri_du_plan(txt: str) -> list[dict]:
    """Tableau de la section `## 4` : acquis, rang, lieu, taille."""
    m = re.search(r"^##\s*4\.[^\n]*\n(.*?)(?=^##\s|\Z)", txt, re.M | re.S)
    if not m:
        return []
    out = []
    for line in m.group(1).splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2:
            continue
        rang = _defold(cells[1])
        if rang not in RANGS:
            continue                              # en-tête, séparateur, ligne libre
        taille = cells[3] if len(cells) > 3 else ""
        n = re.search(r"(\d{2,5})\s*mots", taille)
        out.append({"acquis": cells[0], "rang": rang,
                    "lieu": cells[2] if len(cells) > 2 else "",
                    "taille": taille,
                    "mots": int(n.group(1)) if n else (25 if rang == "MENTION" else 0)})
    return out


def acquis_de_letat(txt: str) -> list[dict]:
    """Items de `## 2.` portant une ligne `destination :`."""
    m = re.search(r"^##\s*2\.[^\n]*\n(.*?)(?=^##\s|\Z)", txt, re.M | re.S)
    if not m:
        return []
    bloc = m.group(1)
    # un item = un tiret de premier niveau ouvrant sur un titre en gras
    parts = re.split(r"^-\s+(?=\*\*)", bloc, flags=re.M)
    out = []
    for part in parts[1:]:
        t = re.match(r"\*\*(.+?)\*\*", part, re.S)
        titre = re.sub(r"\s+", " ", t.group(1)).strip() if t else "(sans titre)"
        # Format réel du parc : `**Destination : A**` en gras, en fin de phrase,
        # pas une ligne à part. Accepter les deux, et la minuscule.
        d = RE_DEST.search(part)
        out.append({"titre": titre, "destination": d.group(1) if d else None})
    return out


def mots_cle(s: str) -> set[str]:
    return {w for w in re.findall(r"[a-zà-ÿ0-9]{4,}", s.lower())}


def apparie(titre: str, candidats: list[str]) -> str | None:
    """Apparie un acquis de l'état à sa ligne du tri, par INCLUSION des mots-clés.

    La mesure n'est pas la similarité mais le recouvrement du plus court par le plus
    long : au tri, un acquis est désigné par un intitulé ABRÉGÉ (« Variant du hit
    GWAS = allèle ancestral »), alors que l'état porte la phrase entière. Une
    similarité de Jaccard punit mécaniquement cet écart de longueur et rate tous les
    appariements — mesuré sur `Rv2566`, 21 faux « sans rang » sur 25. L'inclusion
    demande seulement que le vocabulaire de l'abrégé se retrouve dans le titre long.
    """
    a = mots_cle(titre)
    if not a:
        return None
    best, score = None, 0.0
    for c in candidats:
        b = mots_cle(c)
        if not b:
            continue
        inter = len(a & b)
        s = inter / min(len(a), len(b))
        if s > score:
            best, score = c, s
    return best if score >= 0.6 else None


# --------------------------------- contrôles ------------------------------------

def compatibles(taille: int) -> list[tuple[str, str]]:
    """Revues dont la limite annoncée admet cette taille. INDICATIF : la limite est
    du texte libre et son périmètre (résumé inclus ou non) varie d'une revue à
    l'autre. Toujours relire le guide auteurs avant de s'y fier."""
    if not JOURNALS.exists() or taille <= 0:
        return []
    out = []
    for i, line in enumerate(_read(JOURNALS).splitlines()):
        if i == 0:
            continue
        c = line.split("\t")
        if len(c) < 8:
            continue
        nom, lim = c[1], c[7]
        if not lim or lim == "unknown":
            continue
        nums = [int(n) for n in re.findall(r"(\d{3,5})\s*(?:words|mots)", lim)]
        if any(n >= taille for n in nums) or "unlimited" in lim.lower() \
           or "sans limite" in lim.lower():
            out.append((nom, lim[:110]))
    return out


def collecte(root: Path) -> dict:
    plan_p = root / "plan_narratif.md"
    etat_p = root / "etat_des_decouvertes.md"
    d: dict = {"racine": str(root), "plan": plan_p.exists(),
               "etat": etat_p.exists(), "alertes": [], "info": []}

    etat_txt = _read(etat_p)
    d["acquis_etat"] = acquis_de_letat(etat_txt)
    d["acquis_article"] = [a for a in d["acquis_etat"] if a["destination"] == "A"]

    if not plan_p.exists():
        d["alertes"].append(
            "aucun `plan_narratif.md` : la porte 2 n'est pas franchie. "
            "Lancer `/narratif`.")
        return d

    txt = _read(plan_p)
    d["entete"] = entete(txt)
    d["maillons"] = rows(txt, "M")
    d["bascules"] = rows(txt, "B")
    d["supp"] = rows(txt, "S")
    d["tri"] = tri_du_plan(txt)

    # 1. acquis destinés à l'article, absents du tri
    tries = [t["acquis"] for t in d["tri"]]
    sans_rang = [a["titre"] for a in d["acquis_article"]
                 if not apparie(a["titre"], tries)]
    d["sans_rang"] = sans_rang
    if sans_rang:
        d["alertes"].append(
            f"{len(sans_rang)} acquis destinés à l'article n'ont pas de rang au plan")

    # 2. bascule sans figure
    muettes = [b[0] for b in d["bascules"]
               if len(b) < 4 or not re.search(r"fig|table|tabl", b[3], re.I)]
    d["bascules_sans_figure"] = muettes
    if muettes:
        d["alertes"].append(
            f"bascule(s) sans figure ni table : {', '.join(muettes)}")

    # 3. dépendances inversées
    rang_m = {m[0]: i for i, m in enumerate(d["maillons"])}
    inversions = []
    for m in d["maillons"]:
        deps = re.findall(r"\bM(\d+)\b", m[-1]) if len(m) > 1 else []
        for dep in deps:
            k = "M" + dep
            if k == m[0]:
                continue
            if k in rang_m and rang_m[k] >= rang_m[m[0]]:
                inversions.append(f"{m[0]} dépend de {k}, énoncé après lui")
    d["inversions"] = inversions
    if inversions:
        d["alertes"].extend(inversions)

    # 4. figures du corps contre bascules
    n_b = len(d["bascules"])
    justifiees = len(re.findall(r"^\s*[-*]\s*figure\s+\d+\s*—", txt, re.M | re.I))
    d["figures_corps"] = n_b + justifiees
    d["info"].append(
        f"{n_b} bascule(s), {justifiees} figure(s) hors bascule justifiée(s) "
        f"au registre, soit {d['figures_corps']} figure(s) au corps")

    # 5. taille projetée
    t = d["entete"].get("taille visée du corps", "") or d["entete"].get("taille visee du corps", "")
    n = re.search(r"(\d{3,6})", t.replace(" ", ""))
    d["taille"] = int(n.group(1)) if n else 0
    somme = sum(x.get("mots", 0) for x in d["tri"])
    d["somme_tri"] = somme
    if d["taille"] and somme:
        # Le total annonce doit couvrir la somme des items PLUS les sections que le
        # tri ne porte pas (introduction, methodes, discussion, conclusion). Un total
        # INFERIEUR a la seule somme des items est une incoherence interne : le plan
        # promet une taille que son propre tri dement. Vu a la premiere application
        # reelle (Rv2566), ou 15 items totalisaient 5000 mots sous un total de 4600.
        d["info"].append(f"somme des items du tri : {somme} mots")
        if somme >= d["taille"]:
            d["alertes"].append(
                f"incohérence interne : les items du tri totalisent {somme} mots, "
                f"soit autant ou plus que la taille visée du corps ({d['taille']}), "
                "qui doit aussi loger introduction, méthodes, discussion et conclusion")
    if d["taille"]:
        rev = compatibles(d["taille"])
        d["revues"] = rev
        d["info"].append(
            f"taille visée {d['taille']} mots — {len(rev)} revue(s) de journals.tsv "
            f"l'admettent (indicatif, phase 4 ; sinon préprint)")
    return d


def rendre(d: dict) -> str:
    L = [f"Plan narratif — {d['racine']}"]
    if not d["etat"]:
        L.append("  etat_des_decouvertes.md ABSENT : rien à croiser.")
    if not d["plan"]:
        L.append("  plan_narratif.md ABSENT.")
    else:
        e = d.get("entete", {})
        L.append(f"  message      : {e.get('message', '(non renseigné)')[:100]}")
        L.append(f"  contre-msg   : {e.get('contre-message', '(non renseigné)')[:100]}")
        L.append(f"  archétype    : {e.get('archetype', '(non renseigné)')}")
        L.append(f"  maillons {len(d['maillons'])}  bascules {len(d['bascules'])}  "
                 f"supplémentaire {len(d['supp'])} item(s)  tri {len(d['tri'])} acquis")
        rangs: dict[str, int] = {}
        for t in d["tri"]:
            rangs[t["rang"]] = rangs.get(t["rang"], 0) + 1
        if rangs:
            L.append("  rangs        : " +
                     "  ".join(f"{k} {v}" for k, v in sorted(rangs.items())))
    for i in d.get("info", []):
        L.append(f"  · {i}")
    if d["alertes"]:
        L.append("  ALERTES")
        for a in d["alertes"]:
            L.append(f"    - {a}")
        for t in d.get("sans_rang", [])[:15]:
            L.append(f"      sans rang : {t[:88]}")
    else:
        L.append("  aucune alerte.")
    L.append("  (ce script mesure, il ne tranche pas ; la revue n'arbitre pas la longueur)")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("projet", nargs="?")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    root = resoudre(a.projet)
    if root is None:
        print("Aucune racine de projet trouvée (pas de cahier_de_labo.md).",
              file=sys.stderr)
        return 2
    d = collecte(root)
    print(json.dumps(d, ensure_ascii=False, indent=2) if a.json else rendre(d))
    return 1 if d["alertes"] else 0


if __name__ == "__main__":
    sys.exit(main())
