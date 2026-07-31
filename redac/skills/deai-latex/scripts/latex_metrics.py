#!/usr/bin/env python3
"""Metriques de conformite d'un manuscrit LaTeX, pour le skill /deai-latex.

Deux mesures qu'il ne faut JAMAIS refaire a la main, parce qu'elles ont chacune
un piege qui produit un chiffre faux mais credible :

  R13.1  Longueur de l'abstract.
         Piege : "ignorer les commandes LaTeX" se traduit naivement par une regex
         qui supprime la commande AVEC son argument. Or \\emph{X}, \\textit{X},
         \\node{X}, \\ce{X}... RENDENT leur argument : le supprimer SOUS-ESTIME
         la longueur. A l'inverse, compter sur le PDF via pdftotext SUR-ESTIME
         quand le manuscrit charge `lineno` (les numeros de ligne deviennent des
         mots). Vecu : 315 mots (sous-estime) puis 354 (sur-estime) pour un
         abstract qui en faisait 324. Deux mesures fausses en sens opposes, la
         bonne valeur au milieu, et un abstract declare conforme a tort.
         Regle : garder l'argument des commandes de MISE EN FORME, supprimer les
         commandes structurelles avec leur argument, compter une formule math
         pour un mot.

  R12    Cuisine locale (chemins/scripts/repertoires internes).
         Piege : grep sur le source .tex rate ce qui s'est incruste dans une
         legende de figure/tableau ou dans un \\input{}. Le seul test qui fait foi
         est le grep sur le PDF *rendu*. Distinction critique : un
         \\includegraphics{supplementary_materials/f.pdf} DOIT rester dans le
         source (directive de compilation) et n'apparait PAS dans le PDF : c'est
         precisement pourquoi on teste le rendu et non la source.

Usage :
    python3 latex_metrics.py main.tex                 # abstract seul
    python3 latex_metrics.py main.tex --pdf main.pdf  # + scan R12 sur le rendu
    python3 latex_metrics.py main.tex --json
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# Commandes dont l'argument est RENDU dans le PDF : on garde le contenu.
INLINE_CMDS = (
    "emph|textit|textbf|texttt|textsc|textrm|textsf|underline|uline|"
    "mbox|text|mathrm|node|gene|ce|chem|si|SI|num|enquote|dquote|"
    "citeauthor|citeyear|nameref|acs|acl|ac|glsentryshort|glsentrylong"
)
# Commandes dont l'argument n'est PAS du texte courant : on supprime tout.
DROP_CMDS = (
    "label|ref|cref|Cref|autoref|eqref|pageref|cite|citep|citet|parencite|"
    "textcite|autocite|footnote|todo|color|textcolor|hspace|vspace|"
    "includegraphics|input|include|caption|index|marginpar"
)

# Motifs de cuisine locale (R12), cherches dans le TEXTE RENDU du PDF.
#
# Le piege ici est la SUR-DETECTION. Une regex "un slash quelque part" ramasse
# GAS6/AXL, epithelial/mesenchymal, E/M, 0.5/0.5, miR-205/ZEB1, 6/8/10/1 (partition
# de phenotypes), un DOI... Un test qui hurle a tort est un test qu'on apprend a
# ignorer : il est PIRE qu'absent. Deux lignes de defense : les INDICES FORTS de
# chemin ci-dessous, et le rejet de tout match SANS lettre (voir scan_pdf_for_local_paths).
# On exige donc un INDICE FORT de chemin de fichier, pas un simple slash :
#   - un segment snake_case suivi d'un slash        (met_rtk_split/, data_raw/)
#   - une extension de fichier locale connue        (phase3.py, report.json)
#   - au moins deux slashes entre segments minuscules (a/b/c)
#   - un chemin absolu ou relatif explicite         (/home/..., ./x, ../x)
LOCAL_PATTERNS = [
    (r"\b[a-z0-9]+(?:_[a-z0-9]+)+/[A-Za-z0-9_./-]*", "repertoire snake_case"),
    (r"\b[A-Za-z0-9_-]+\.(?:py|sh|pkl|h5|nwk|json|csv|tsv|yaml|yml|log|sql|bnd|cfg|ipynb)\b",
     "nom de fichier local"),
    (r"(?:^|\s)(?:\.{1,2}/|/(?:home|Users|tmp|mnt|opt|var)/)[A-Za-z0-9_./-]+", "chemin systeme"),
    (r"\b[a-z0-9_-]+/[a-z0-9_-]+/[a-z0-9_./-]+", "chemin multi-segments"),
    (r"\b(?:in-house|home-made|our own script|fallback to the local)\b", "auto-reference opaque"),
    (r"\bAJAX\b|\bAPI endpoint\b", "detail d'implementation"),
]
# Faux positifs legitimes dans un PDF scientifique : URL, DOI, depots publics.
LOCAL_ALLOW = re.compile(
    r"https?://|doi\.org|10\.\d{4}/|arxiv|github\.com|gitlab|zenodo|figshare|"
    r"bioconductor|/dev/null",
    re.IGNORECASE,
)


def extract_abstract(tex: str) -> str | None:
    for pat in (
        r"\\begin\{abstract\}(.*?)\\end\{abstract\}",
        r"\\begin\{abstract\*\}(.*?)\\end\{abstract\*\}",
        r"\\abstract\{(.*?)\n\}",
    ):
        m = re.search(pat, tex, re.S)
        if m:
            return m.group(1)
    return None


def count_rendered_words(chunk: str) -> int:
    """Compte les mots effectivement RENDUS. Voir le piege en tete de fichier."""
    t = re.sub(r"(?<!\\)%.*", "", chunk)                      # commentaires
    t = re.sub(rf"\\({DROP_CMDS})\*?(\[[^\]]*\])?\{{[^{{}}]*\}}", " ", t)
    for _ in range(3):                                        # commandes imbriquees
        t = re.sub(rf"\\({INLINE_CMDS})\*?\{{([^{{}}]*)\}}", r"\2", t)
    # Une formule = un mot, MAIS sans injecter d'espace : le math inline colle
    # souvent au mot qui l'entoure ($\Delta$Np63$\alpha$ rend "DNp63a", UN mot).
    # Injecter " X " le couperait en trois et sur-estimerait la longueur.
    t = re.sub(r"\$\$?[^$]*\$\$?", "X", t)
    t = re.sub(r"\\begin\{[^}]*\}|\\end\{[^}]*\}", " ", t)
    t = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?", " ", t)        # commandes restantes
    t = re.sub(r"[{}\\~^_&]", " ", t)
    return len([w for w in t.split() if any(c.isalnum() for c in w)])


# Bornes INCLUSIVES a droite : 300 mots pile est la limite admise par PLOS ONE et
# Scientific Reports, pas un depassement. Une borne exclusive ferait crier l'outil
# sur un abstract exactement conforme -- encore un faux positif.
LENGTH_BANDS = [
    (0, 99, "trop court", "manque probablement le contexte ou la conclusion"),
    (100, 149, "court", "tolerable (Nature Brief Comm., PNAS) ; verifier la cible"),
    (150, 250, "standard", "OK pour la majorite des revues"),
    (251, 300, "acceptable", "a la limite de PLOS ONE / Sci. Rep. (300) : conforme, sans marge"),
    (301, 350, "long", "beaucoup de revues coupent a 300 : raccourcir"),
    (351, 10**6, "trop long", "sera tronque par l'editeur : raccourcir imperativement"),
]


def band(n: int) -> tuple[str, str]:
    for lo, hi, name, advice in LENGTH_BANDS:
        if lo <= n <= hi:
            return name, advice
    return "inconnu", ""


def scan_pdf_for_local_paths(pdf: Path) -> list[dict] | None:
    """R12 : le seul test qui fait foi. None si pdftotext indisponible."""
    try:
        out = subprocess.run(
            ["pdftotext", str(pdf), "-"], capture_output=True, text=True, timeout=60
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if out.returncode != 0:
        return None
    hits: list[dict] = []
    for lineno, line in enumerate(out.stdout.splitlines(), 1):
        for pat, kind in LOCAL_PATTERNS:
            for m in re.finditer(pat, line):
                tok = m.group(0)
                # Un chemin / script / repertoire interne contient TOUJOURS au moins
                # une lettre. Une sequence purement numerique separee par des slashes
                # (6/8/10/1 = partition de phenotypes E/M/pEM/Naive, 0.5/0.5, 2020/21)
                # est un ratio, une date ou un decompte, jamais un chemin. Sans ce
                # garde-fou, "chemin multi-segments" ramasse ces nombres -- exactement
                # le faux positif que R12 existe pour eviter (vecu mabossDemo 2026-07-21).
                if not re.search(r"[A-Za-z]", tok):
                    continue
                # Tester l'allow-list sur le VOISINAGE, pas sur le token seul :
                # pdftotext casse les DOI en fin de ligne ("doi: 10." puis
                # "1093/bioinformatics/btad374"), et le fragment orphelin ressemble
                # alors a un chemin. Le "10." qui le precede est l'indice qui sauve.
                around = line[max(0, m.start() - 12): m.end() + 4]
                if LOCAL_ALLOW.search(tok) or LOCAL_ALLOW.search(around):
                    continue
                hits.append({"page_line": lineno, "match": tok, "kind": kind,
                             "context": line.strip()[:90]})
    return hits


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("tex")
    ap.add_argument("--pdf", help="PDF compile, pour le test R12 sur le rendu")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    tex = Path(a.tex).read_text(encoding="utf-8")
    res: dict = {}

    abstract = extract_abstract(tex)
    if abstract is None:
        res["abstract"] = {"found": False}
    else:
        n = count_rendered_words(abstract)
        name, advice = band(n)
        res["abstract"] = {"found": True, "words": n, "band": name, "advice": advice}

    if a.pdf:
        hits = scan_pdf_for_local_paths(Path(a.pdf))
        res["r12"] = (
            {"available": False, "reason": "pdftotext indisponible ou echec"}
            if hits is None
            else {"available": True, "hits": hits, "clean": not hits}
        )

    if a.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return 0

    ab = res["abstract"]
    if not ab["found"]:
        print("Abstract : introuvable (verifier la classe du document)")
    else:
        print(f"Abstract : {ab['words']} mots -- {ab['band']}")
        if ab["advice"]:
            print(f"           {ab['advice']}")
    if "r12" in res:
        r = res["r12"]
        if not r["available"]:
            print(f"R12 (PDF) : {r['reason']}")
        elif r["clean"]:
            print("R12 (PDF rendu) : aucune cuisine locale visible")
        else:
            print(f"R12 (PDF rendu) : {len(r['hits'])} occurrence(s) A TRAITER")
            for h in r["hits"][:15]:
                print(f"  [{h['kind']}] {h['match']}  <<  {h['context']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
