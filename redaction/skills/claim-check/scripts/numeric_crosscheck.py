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

Claims de COMPTAGE (« 5 témoins », « n=9 génomes ») : chaque fichier CSV/TSV/JSON(liste)
expose aussi une entrée synthétique `<fichier>:__n_rows__` portant son nombre de lignes/
enregistrements, à déclarer comme n'importe quel autre chemin en mode `--assert-file`. Sans
elle, un chiffre qui compte des ENTRÉES plutôt qu'il ne cite une CELLULE ne peut jamais être
recroisé : c'est le défaut vécu porte 3bis `lineage_subdivision_methods` (2026-09-19), table
de témoins citée à 5 entrées alors que le `.tsv` régénéré en portait 9 — chaque cellule était
juste, seul le COMPTE avait dérivé.

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
# Un nombre, avec son signe optionnel et ses eventuels separateurs de milliers.
# Les separateurs admis sont ceux qu'on rencontre reellement dans un .tex : la virgule
# anglaise (2,618), l'espace fine LaTeX (2\,618) et l'insecable (2~618) -- ces trois
# conventions sont celles que la doc du skill demande d'auditer, il faut donc les LIRE.
NUM = re.compile(r"(?<![\w.])(-|−)?(\d{1,3}(?:(?:,|\\,|~)\d{3})+|\d+)([.,]\d+)?(?![\w])")


def _parse_number(sign: str | None, integer: str, frac: str | None, decimal_comma: bool):
    """Reconstruit la valeur d'un nombre ecrit en LaTeX. Renvoie None si non interpretable.

    Le piege corrige ici (vecu le 2026-08-03, tissue_tropism_mtbc) : l'ancienne version
    faisait `raw.replace(",", ".")`, si bien qu'un « 2,618 » anglais devenait 2.618. Ce
    n'est pas qu'un faux positif de couverture : c'est une VALEUR FAUSSE, donc un ecart
    reel pouvait etre manque ou invente. Une virgule suivie d'exactement trois chiffres
    (repetable) est un separateur de milliers ; suivie d'un autre compte, elle est
    decimale. En francais (`\\usepackage[french]`), la convention decimale `0{,}89` prime,
    d'ou le drapeau `decimal_comma`.
    """
    whole = re.sub(r"(,|\\,|~)", "", integer)
    if frac:
        # `frac` commence par . ou , : en anglais une virgule ici reste decimale
        # (cas « 0,89 » d'un document francophone mal converti), on l'accepte.
        whole += "." + frac[1:]
    elif decimal_comma and re.fullmatch(r"\d{1,3},\d{3}", integer):
        # Document francais : « 1,234 » se lit 1.234, pas 1234.
        whole = integer.replace(",", ".")
    try:
        v = float(whole)
    except ValueError:
        return None
    return -v if sign else v


def resolve_inputs(path: Path, seen: set[Path] | None = None, depth: int = 0) -> str:
    """Concatene le .tex et ses \\input/\\include -- sans ca, un manuscrit decoupe
    en squelette + sections fait manquer tout nombre cite hors du squelette."""
    seen = seen if seen is not None else set()
    path = path.resolve()
    if path in seen or depth > 6 or not path.exists():
        return ""
    seen.add(path)
    text = path.read_text(encoding="utf-8", errors="replace")

    def sub(m: re.Match) -> str:
        target = m.group(2).strip()
        cand = path.parent / target
        for c in (cand, cand.with_suffix(".tex"), Path(str(cand) + ".tex")):
            if c.exists() and c.is_file():
                return "\n" + resolve_inputs(c, seen, depth + 1) + "\n"
        return ""

    return re.sub(r"\\(input|include)\{([^}]*)\}", sub, text)


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
    """Aplatit chaque fichier en (chemin, valeur), plus une entree synthetique
    `<fichier>:__n_rows__` portant le NOMBRE de lignes/enregistrements.

    Sans elle, un claim de comptage (« 5 temoins », « n=9 genomes ») ne peut se
    verifier que contre une CELLULE du tableau, jamais contre sa TAILLE -- or
    c'est precisement le defaut vecu (porte 3bis `lineage_subdivision_methods`,
    2026-09-19) : une table de temoins citee a 5 entrees dans le manuscrit alors
    que le `.tsv` regenere en portait 9. Aucune cellule n'etait fausse, c'etait
    le COMPTE qui avait derive -- la comparaison cellule-a-cellule ne le voit pas.
    """
    vals: list[tuple[str, float]] = []
    for p in paths:
        path = Path(p)
        if not path.exists():
            print(f"  (donnees introuvables, ignore : {p})", file=sys.stderr)
            continue
        if path.suffix.lower() == ".json":
            obj = json.loads(path.read_text(encoding="utf-8"))
            vals += [(f"{path.name}:{k}", v) for k, v in flatten(obj)]
            if isinstance(obj, list):
                vals.append((f"{path.name}:__n_rows__", float(len(obj))))
        elif path.suffix.lower() in (".csv", ".tsv"):
            delim = "\t" if path.suffix.lower() == ".tsv" else ","
            with path.open(encoding="utf-8") as fh:
                n_rows = 0
                for i, row in enumerate(csv.DictReader(fh, delimiter=delim)):
                    n_rows = i + 1
                    for k, v in row.items():
                        try:
                            vals.append((f"{path.name}:{k}[row{i}]", float(str(v).replace(",", "."))))
                        except (TypeError, ValueError):
                            pass
                vals.append((f"{path.name}:__n_rows__", float(n_rows)))
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
    # La convention decimale depend de la langue du document : c'est le preambule qui la
    # donne, donc on le lit meme si on ne compte pas ses nombres.
    decimal_comma = bool(re.search(r"\\usepackage\[[^]]*\b(french|francais)\b", tex, re.I))
    for lineno, line in enumerate(body.split("\n"), 1 + offset):
        if line.lstrip().startswith("%") or IGNORE_CONTEXT.search(line):
            continue
        for m in NUM.finditer(line):
            val = _parse_number(m.group(1), m.group(2), m.group(3), decimal_comma)
            if val is None:
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
    ap.add_argument("--lines", metavar="A-B",
                    help="restreindre la COUVERTURE a cette plage de lignes du .tex (une section)")
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
        # Le fichier de claims dit « le manuscrit affirme X, qui vient de la source Y ».
        # Il faut donc verifier LES DEUX cotes. Ne verifier que X contre Y laisse le fichier
        # DERIVER du .tex : on corrige un chiffre dans le manuscrit, on oublie la declaration,
        # et l'outil reste au vert en comparant une valeur que le manuscrit ne contient plus.
        # Vecu le 2026-07-11 : une fourchette changee dans le .tex, « tous concordent » quand meme.
        tex_raw = resolve_inputs(Path(a.tex))
        tex_vals = {round(v, 4) for _, v, _ in tex_numbers(tex_raw)}
        bad = 0
        for c in claims:
            src = lut.get(c["path"])
            if src is None:
                print(f"  INTROUVABLE {c['label']:<34} chemin absent : {c['path']}")
                bad += 1
                continue
            ok_src = abs(src - float(c["tex"])) <= a.tol
            in_tex = round(float(c["tex"]), 4) in tex_vals
            bad += 0 if (ok_src and in_tex) else 1
            if not in_tex:
                flag = "ORPHELIN"   # la declaration ne correspond a AUCUN nombre du manuscrit
            elif not ok_src:
                flag = "ECART"
            else:
                flag = "OK   "
            hint = ""
            if not in_tex:
                # Un ORPHELIN a deux causes tres differentes : la declaration est perimee
                # (defaut REEL), ou le nombre est bien la mais le tokenizer ne l'isole pas
                # -- typiquement colle a un prefixe (PC9, L4, Rv0667). Ne pas distinguer les
                # deux oblige a inspecter chaque cas a la main, ce qui est exactement le
                # travail que cet outil doit eviter (vecu le 2026-08-03).
                glued = re.search(rf"[A-Za-z]{re.escape(str(c['tex']))}(?![\w.])", tex_raw)
                hint = ("  <- present mais COLLE a un prefixe (" + glued.group(0)
                        + ") : le tokenizer ne l'isole pas, ce n'est PAS un ecart"
                        if glued else
                        "  <- ABSENT du manuscrit : declaration perimee ?")
                if glued:
                    bad -= 1          # faux positif identifie : ne pas le compter en ecart
            print(f"  {flag} {c['label']:<34} source={src:<8} declare={c['tex']}{hint}")
        print(f"\n{'TOUS LES CHIFFRES CONCORDENT' if not bad else f'{bad} ECART(S) A CORRIGER'}")

        # --- COUVERTURE : le piege du mode declaratif ---------------------------------
        # Un fichier de claims ne verifie QUE ce qu'on lui declare. Un chiffre OUBLIE dans
        # les declarations passe donc au vert sans avoir ete verifie — et c'est exactement
        # la ou se cachent les defauts (vecu 2026-07-11 : l'outil rendait « 23/23 OK »
        # alors qu'une plage 0,47-0,58 du manuscrit, non declaree, melangeait des
        # conditions). « Tout vert » ne vaut RIEN sans la couverture.
        declared = {round(float(c["tex"]), 4) for c in claims}
        lo, hi = (0, 10**9)
        if a.lines:
            lo, hi = (int(x) for x in a.lines.split("-"))
        body = [(l, v, c) for l, v, c in tex_numbers(resolve_inputs(Path(a.tex)))
                if lo <= l <= hi and v >= a.min]
        uncovered = [(l, v, c) for l, v, c in body if round(v, 4) not in declared]
        scope = f"lignes {lo}-{hi}" if a.lines else "tout le corps"
        print(f"\nCOUVERTURE ({scope}) : {len(body) - len(uncovered)}/{len(body)} nombres declares")
        if uncovered:
            print(f"  {len(uncovered)} nombre(s) NON declare(s) — donc NON verifies. C'est la que")
            print("  se cachent les defauts. Declarer, ou justifier (litterature, n, chiffre rond) :")
            seen = set()
            for l, v, c in uncovered:
                if v in seen:
                    continue
                seen.add(v)
                print(f"    l.{l:<5} {v:<8} « {c[:72]} »")
        return 0 if not bad and not uncovered else 1

    if not data:
        print("Aucune donnee chargee : rien a recroiser.", file=sys.stderr)
        return 2
    nums = [(l, v, c) for l, v, c in tex_numbers(resolve_inputs(Path(a.tex)))
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
