#!/usr/bin/env python3
"""Recroisement mécanique des nombres d'un manuscrit LaTeX avec les données sources.

Pourquoi cet outil existe (Phase 1bis de /claim-check et de /manuscript-review).

La relecture humaine ne rattrape PAS un chiffre attribué au mauvais modèle, à la mauvaise
condition ou au mauvais échantillon : elle lit une phrase plausible et passe. Le mode
d'erreur le plus dangereux n'est pas le chiffre inventé (voyant), c'est le chiffre VRAI
rapporté sous la MAUVAISE condition — il existe dans les données, il survit au sens, et
seule une comparaison mécanique le débusque.

Cas fondateur (projet mabossDemo, 2026-07-11) : un manuscrit issu d'un framework
multi-variantes rapportait « 0,20 » comme valeur de contrôle. Le 0,20 existait bel et bien
dans les résultats... mais pour la variante `full_autocrine_hier`, alors que le contrôle
venait de `axl_slave` (0,341). Deux reviews humaines successives ne l'avaient pas vu.

Ce que fait le script :
  1. extrait tout nombre du .tex, avec sa phrase de contexte ;
  2. aplatit les fichiers de données (JSON/CSV) en (chemin, valeur) ;
  3. pour chaque nombre du manuscrit, cherche une valeur ÉGALE (à la tolérance d'arrondi)
     dans les données, et signale :
       - ABSENT   : aucune valeur correspondante -> chiffre non traçable, à justifier ;
       - PROCHE   : pas de correspondance exacte, mais une valeur voisine existe
                    (< `--near`) -> suspicion de mauvaise attribution ou d'arrondi faux ;
       - MULTIPLE : plusieurs chemins de données portent cette valeur -> l'attribution
                    n'est pas décidable par le seul chiffre ; vérifier À LA MAIN que la
                    phrase désigne bien le bon (c'est exactement le cas fondateur).

Le script NE conclut PAS : il RANGE les chiffres en « sûrs », « à vérifier », « suspects ».
La décision reste humaine, mais elle porte sur 5 chiffres au lieu de 300.

Usage :
    python3 numeric_crosscheck.py main.tex --data results/*.json --near 0.05
    python3 numeric_crosscheck.py main.tex --data r.json --json     # sortie machine
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

# Nombres à ignorer : ils ne viennent jamais des données (numérotation, dates, versions).
IGNORE_CONTEXT = re.compile(
    r"\\(cite|citep|citet|ref|cref|label|section|subsection|includegraphics|"
    r"documentclass|usepackage|newcommand|pageref|footnote)", re.I)
NUM = re.compile(r"(?<![\w.])(\d+(?:[.,]\d+)?)(?![\w])")


def flatten(obj, prefix=""):
    """Aplatit un JSON en (chemin, valeur numérique)."""
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            out += flatten(v, f"{prefix}.{k}" if prefix else str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out += flatten(v, f"{prefix}[{i}]")
    elif isinstance(obj, bool):
        pass
    elif isinstance(obj, (int, float)):
        out.append((prefix, float(obj)))
    return out


def load_data(paths: list[str]) -> list[tuple[str, float]]:
    vals: list[tuple[str, float]] = []
    for p in paths:
        path = Path(p)
        if not path.exists():
            print(f"  (donnees introuvables, ignore : {p})", file=sys.stderr)
            continue
        if path.suffix.lower() == ".json":
            vals += [(f"{path.name}:{k}", v)
                     for k, v in flatten(json.loads(path.read_text(encoding="utf-8")))]
        elif path.suffix.lower() in (".csv", ".tsv"):
            delim = "\t" if path.suffix.lower() == ".tsv" else ","
            with path.open(encoding="utf-8") as fh:
                for i, row in enumerate(csv.DictReader(fh, delimiter=delim)):
                    for k, v in row.items():
                        try:
                            vals.append((f"{path.name}:{k}[row{i}]", float(str(v).replace(",", "."))))
                        except (TypeError, ValueError):
                            pass
    return vals


def tex_numbers(tex: str) -> list[tuple[int, float, str]]:
    """(ligne, valeur, contexte) pour chaque nombre du CORPS, hors commandes techniques.

    Le preambule est exclu : \\DeclareUnicodeCharacter{0394}, les tailles de police et les
    numeros de version y produisent un bruit garanti et sans interet.
    """
    out = []
    start = tex.find("\\begin{document}")
    offset = tex[:start].count("\n") if start > 0 else 0
    body = tex[start:] if start > 0 else tex
    for lineno, line in enumerate(body.split("\n"), 1 + offset):
        if line.lstrip().startswith("%") or IGNORE_CONTEXT.search(line):
            continue
        for m in NUM.finditer(line):
            raw = m.group(1).replace(",", ".")
            try:
                val = float(raw)
            except ValueError:
                continue
            out.append((lineno, val, line.strip()[:100]))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("tex")
    ap.add_argument("--data", nargs="+", required=True, help="fichiers JSON/CSV de resultats")
    ap.add_argument("--tol", type=float, default=0.005, help="tolerance d'egalite (arrondi)")
    ap.add_argument("--near", type=float, default=0.05,
                    help="ecart en-deca duquel une valeur non egale est signalee PROCHE")
    ap.add_argument("--min", type=float, default=0.0,
                    help="ignorer les nombres < ce seuil (numerotation, petits entiers)")
    ap.add_argument("--show-multiple", action="store_true",
                    help="lister les valeurs presentes sous plusieurs conditions (bruyant)")
    ap.add_argument("--assert-file", metavar="JSON",
                    help="verification DECLARATIVE : {\"claims\": [{\"label\":..., \"tex\": 0.48, "
                         "\"path\": \"fichier.json:chemin.vers.valeur\"}]}. C'est le mode fiable.")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    data = load_data(a.data)

    if a.assert_file:
        # Mode declaratif : l'agent DECLARE quel chiffre vient de quel chemin, le script
        # verifie. Pas de devinette, pas de bruit -> c'est le mode a privilegier pour un
        # manuscrit issu d'un framework multi-variantes, ou le meme chiffre existe sous
        # plusieurs conditions et ou seule l'ATTRIBUTION est en jeu.
        lut = dict(data)
        claims = json.loads(Path(a.assert_file).read_text(encoding="utf-8"))["claims"]
        bad = 0
        for c in claims:
            src = lut.get(c["path"])
            if src is None:
                print(f"  INTROUVABLE {c['label']:<34} chemin absent : {c['path']}")
                bad += 1
                continue
            ok_ = abs(src - float(c["tex"])) <= a.tol
            bad += 0 if ok_ else 1
            print(f"  {'OK   ' if ok_ else 'ECART'} {c['label']:<34} "
                  f"source={src:<8} manuscrit={c['tex']}")
        print(f"\n{'TOUS LES CHIFFRES CONCORDENT' if not bad else f'{bad} ECART(S) A CORRIGER'}")
        return 0 if not bad else 1

    if not data:
        print("Aucune donnee chargee : rien a recroiser.", file=sys.stderr)
        return 2
    nums = [(l, v, c) for l, v, c in tex_numbers(Path(a.tex).read_text(encoding="utf-8"))
            if v >= a.min]

    absent, near, multiple, ok = [], [], [], []
    for lineno, val, ctx in nums:
        exact = [k for k, dv in data if abs(dv - val) <= a.tol]
        if exact:
            (multiple if len(set(exact)) > 1 else ok).append(
                {"line": lineno, "value": val, "context": ctx, "paths": sorted(set(exact))[:6]})
        else:
            # Un « PROCHE » n'a de sens que pour un nombre qui EST un resultat mesure :
            # au moins 2 decimales. Sinon on rapproche des nombres sans rapport semantique
            # (0.15 % d'une regle de trois et 0.163 d'une simulation), et l'outil crie a tort.
            decimals = len(f"{val}".split(".")[-1]) if "." in f"{val}" else 0
            is_measurement = decimals >= 2
            close = sorted(((abs(dv - val), k, dv) for k, dv in data
                            if abs(dv - val) <= a.near
                            and (val == 0 or abs(dv - val) / max(abs(val), 1e-9) <= 0.10)))
            if close and is_measurement:
                near.append({"line": lineno, "value": val, "context": ctx,
                             "closest": [{"path": k, "data_value": dv} for _, k, dv in close[:3]]})
            else:
                absent.append({"line": lineno, "value": val, "context": ctx})

    res = {"n_numbers": len(nums), "n_data_values": len(data),
           "ok": len(ok), "multiple": multiple, "near": near, "absent": absent}
    if a.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return 0

    print(f"Recroisement : {len(nums)} nombres du manuscrit vs {len(data)} valeurs de donnees\n")
    print(f"  trouves a l'identique      : {len(ok)}")
    print(f"  PROCHE   (mauvais chiffre ?): {len(near)}      <- le plus dangereux")
    print(f"  MULTIPLE (meme valeur, N conditions) : {len(multiple)}  (--show-multiple pour les lister)")
    print(f"  ABSENT   (non tracable)    : {len(absent)}\n")

    if near:
        print("PROCHE — une valeur voisine existe dans les donnees, mais pas celle-ci.")
        print("C'est la signature d'une mauvaise attribution ou d'un arrondi faux :")
        for h in near[:15]:
            c = h["closest"][0]
            print(f"  l.{h['line']:<5} {h['value']:<8} ~ {c['data_value']} ({c['path']})")
            print(f"          « {h['context']} »")
    if multiple and a.show_multiple:
        print("\nMULTIPLE — ce chiffre existe sous PLUSIEURS conditions. Le chiffre seul ne")
        print("dit pas laquelle la phrase designe : c'est le cas fondateur (0,20 du mauvais modele).")
        for h in multiple[:10]:
            print(f"  l.{h['line']:<5} {h['value']:<8} -> {', '.join(h['paths'][:3])}"
                  + (" ..." if len(h["paths"]) > 3 else ""))
    if absent:
        print("\nABSENT — aucun equivalent dans les donnees fournies (peut etre legitime :")
        print("valeur de la litterature, taille d'echantillon, chiffre derive) :")
        for h in absent[:15]:
            print(f"  l.{h['line']:<5} {h['value']}")
            print(f"          « {h['context']} »")
    return 0


if __name__ == "__main__":
    sys.exit(main())
