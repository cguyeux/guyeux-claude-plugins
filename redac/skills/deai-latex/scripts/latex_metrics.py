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

Quatre verifications structurelles supplementaires (R1, R2, R8, R9), ajoutees le
2026-08-01 apres avoir constate qu'une passe /deai-latex complete improvisait un
grep ad hoc pour ces quatre points a CHAQUE invocation, alors qu'elles sont de
simples comptages regex sans piege de fond (contrairement a R13.1/R12 ci-dessus,
qui exigent un traitement dedie). Ce sont des SIGNAUX a relire, pas des verdicts :
un \\textbf en legende ou en en-tete de tableau est legitime (cf. SKILL.md R1), le
compteur le remonte quand meme pour que l'humain/l'agent tranche avec le contexte
sous les yeux, plutot que de re-ecrire la regex a la main a chaque manuscrit.

  R7     Longueur de paragraphe.
         Piege VECU (Rv3222c, 2026-08-12) : R7 disait "> 20 lignes : envisager de
         scinder", mais un paragraphe de 759 mots (compte APRES coupure) a
         travers la relecture manuelle, parce que "20 lignes" se lit sur le
         SOURCE .tex, dont le retour a la ligne est arbitraire (~100 caracteres),
         sans rapport fiable avec l'occupation reelle dans un PDF a deux colonnes.
         Ce paragraphe occupait dans les faits PRESQUE DEUX COLONNES PLEINES.
         Le compte de MOTS APRES RENDU (meme fonction que R13.1) est un proxy
         bien plus robuste que les lignes source. Calibrage sur cet incident :
         un decoupage en 5 paragraphes de 140-215 mots chacun occupe 1/3 a 1/2
         colonne chacun dans ce meme document (elsarticle 5p, deux colonnes) --
         d'ou les seuils ci-dessous, deliberement plus stricts en mise en page
         a deux colonnes qu'a une colonne.

Usage :
    python3 latex_metrics.py main.tex                 # abstract + R1/R2/R7/R8/R9
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
    # Au moins un segment de 4 caracteres ou plus. Sans cette exigence, la regle
    # ramasse les enumerations d'identifiants courts separes par des slashes, qui
    # sont du CONTENU : `cp1/cp3/cp6` (noms de copies d'un element mobile, vu sur
    # Rv3222c 2026-08-12), `A/B/C`, `wt/ko/rescue`. Un vrai chemin porte presque
    # toujours un segment lexical (`data`, `results`, `figures`, `phase3`).
    (r"\b(?=[a-z0-9_./-]*[a-z0-9_-]{4})[a-z0-9_-]+/[a-z0-9_-]+/[a-z0-9_./-]+",
     "chemin multi-segments"),
    (r"\b(?:in-house|home-made|our own script|fallback to the local)\b", "auto-reference opaque"),
    (r"\bAJAX\b|\bAPI endpoint\b", "detail d'implementation"),
]
# Faux positifs legitimes dans un PDF scientifique : URL, DOI, depots publics.
LOCAL_ALLOW = re.compile(
    r"https?://|doi\.org|10\.\d{4}/|arxiv|github\.com|gitlab|zenodo|figshare|"
    r"bioconductor|/dev/null",
    re.IGNORECASE,
)


def resolve_inputs(path: Path, seen: set[Path] | None = None, depth: int = 0) -> str:
    """Concatene le .tex et ses \\input/\\include -- sans ca, un manuscrit decoupe
    en squelette + sections (SKILL.md dit deja de le faire a la lecture, mais ce
    script lisait le fichier seul : toute metrique tombait silencieusement sur le
    seul squelette, cf. piege R12/R13.1 documente en tete de fichier)."""
    seen = seen if seen is not None else set()
    path = path.resolve()
    if path in seen or depth > 6 or not path.exists():
        return ""
    seen.add(path)
    text = path.read_text(encoding="utf-8", errors="replace")

    def sub(m: re.Match) -> str:
        target = m.group(2).strip()
        cand = (path.parent / target)
        for c in (cand, cand.with_suffix(".tex"), Path(str(cand) + ".tex")):
            if c.exists() and c.is_file():
                return "\n" + resolve_inputs(c, seen, depth + 1) + "\n"
        return ""  # fichier absent : ne pas inventer de contenu

    return re.sub(r"\\(input|include)\{([^}]*)\}", sub, text)


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


# Environnements dont le \textbf est une convention legitime (SKILL.md R1) :
# titres de section, labels de description, captions, en-tetes de tableau.
# On ne les EXCLUT pas du comptage (trop de faux negatifs possibles selon la
# classe du document) : on se contente de signaler le corps du document APRES
# \begin{document}, ce qui exclut deja le preambule (macros \newcommand, souvent
# porteuses d'un \textbf litteral dans leur propre definition, ex. \rev{}{}).
def body_text(tex: str) -> str:
    m = re.search(r"\\begin\{document\}(.*)\\end\{document\}", tex, re.S)
    return m.group(1) if m else tex


def body_start_line(tex: str) -> int:
    """Numero de ligne (0-based) ou commence body_text(tex) dans le fichier ENTIER.

    Necessaire pour que toute position calculee sur `body` (ex. R7 ci-dessous)
    reste juste une fois reportee a l'utilisateur : `body` exclut le preambule,
    donc une ligne comptee dans `body` seul est systematiquement en avance sur
    la vraie ligne du fichier (defaut vecu : R7 rapportait "ligne 140" pour un
    paragraphe reellement a la ligne 186, ecart exactement egal aux 46 lignes
    de preambule avant \\begin{document}).
    """
    m = re.search(r"\\begin\{document\}", tex)
    return tex.count("\n", 0, m.end()) if m else 0


def count_command(body: str, cmd: str) -> int:
    return len(re.findall(rf"\\{cmd}\*?\{{", body))


def count_env(body: str, env: str) -> int:
    return len(re.findall(rf"\\begin\{{{env}\}}", body))


def count_em_dashes(body: str) -> int:
    """R8 : tiret cadratin litteral (---), caractere unicode em-dash, ou \\textemdash."""
    t = re.sub(r"(?<!\\)%.*", "", body)  # commentaires
    return len(re.findall(r"---|\u2014|\\textemdash\b", t))


def find_orphan_labels(body: str) -> list[str]:
    """R9 : \\label{} sans aucun \\ref/\\cref/\\Cref/\\autoref/\\eqref correspondant."""
    labels = re.findall(r"\\label\{([^}]*)\}", body)
    refs = set(re.findall(r"\\(?:ref|cref|Cref|autoref|eqref|pageref)\{([^}]*)\}", body))
    return [l for l in labels if l not in refs]



# Blocs a ne JAMAIS compter comme un paragraphe de prose : un \begin{...} n'importe
# ou dans le bloc signale un flottant (figure/table/equation), une liste, ou
# l'abstract lui-meme -- leur "compte de mots" ne dit rien de l'occupation d'un
# paragraphe de texte courant, et un gros tableau y ressemblerait a tort.
_PARA_SKIP_ENV = re.compile(r"\\begin\{")
_PARA_SKIP_START = re.compile(
    r"^\\(section|subsection|subsubsection|paragraph|title|author|affiliation"
    r"|maketitle|address|corref|fntext|received|makeatletter|makeatother)\b"
)

# Seuils de mots RENDUS par paragraphe (calibres sur l'incident Rv3222c ci-dessus).
# Deux colonnes = format le plus punitif (une colonne etroite remplit vite) ; une
# colonne pleine largeur tolere environ le double avant de devenir aussi genant.
PARA_BANDS_TWOCOL = {"warn": 300, "flag": 450}
PARA_BANDS_ONECOL = {"warn": 500, "flag": 750}


def detect_two_column(tex: str) -> tuple[bool, str]:
    """Heuristique sur \\documentclass : renvoie (est_deux_colonnes, comment_su)."""
    m = re.search(r"\\documentclass(\[([^\]]*)\])?\{([^}]*)\}", tex)
    if not m:
        return True, "documentclass introuvable, hypothese prudente (deux colonnes)"
    opts = (m.group(2) or "").lower()
    cls = m.group(3).lower()
    opt_list = [o.strip() for o in opts.split(",")]
    if "onecolumn" in opt_list or "1p" in opt_list:
        return False, f"option '{'1p' if '1p' in opt_list else 'onecolumn'}' de {cls}"
    if "twocolumn" in opt_list or "3p" in opt_list or "5p" in opt_list:
        tok = next(o for o in ("twocolumn", "3p", "5p") if o in opt_list)
        return True, f"option '{tok}' de {cls}"
    if cls in ("ieeetran",):
        return True, f"classe {cls} (deux colonnes par defaut)"
    return True, f"classe {cls} sans option de colonnes reconnue, hypothese prudente (deux colonnes)"


def find_long_paragraphs(tex: str, two_col: bool) -> list[dict]:
    """R7 : paragraphes de prose dont le compte de mots RENDUS depasse les seuils."""
    body = body_text(tex)
    base_line = body_start_line(tex)
    bands = PARA_BANDS_TWOCOL if two_col else PARA_BANDS_ONECOL
    hits: list[dict] = []
    pos = 0
    for block in re.split(r"\n[ \t]*\n", body):
        start_line = base_line + body.count("\n", 0, pos) + 1
        pos += len(block) + 2
        stripped = block.strip()
        if not stripped or stripped.startswith("%"):
            continue
        if _PARA_SKIP_ENV.search(stripped) or _PARA_SKIP_START.match(stripped):
            continue
        n = count_rendered_words(stripped)
        if n >= bands["warn"]:
            severity = "FLAG" if n >= bands["flag"] else "WARN"
            hits.append({
                "line": start_line, "words": n, "severity": severity,
                "excerpt": re.sub(r"\s+", " ", stripped)[:70],
            })
    return sorted(hits, key=lambda h: -h["words"])


def structural_checks(tex: str) -> dict:
    """R1/R2/R7/R8/R9 : comptages structurels, signaux a relire (pas des verdicts)."""
    body = body_text(tex)
    two_col, layout_source = detect_two_column(tex)
    return {
        "r1_textbf_body": count_command(body, "textbf"),
        "r2_itemize": count_env(body, "itemize"),
        "r2_enumerate": count_env(body, "enumerate"),
        "r7_layout": {"two_column": two_col, "source": layout_source},
        "r7_long_paragraphs": find_long_paragraphs(tex, two_col),
        "r8_em_dash": count_em_dashes(body),
        "r9_orphan_labels": find_orphan_labels(body),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("tex")
    ap.add_argument("--pdf", help="PDF compile, pour le test R12 sur le rendu")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    tex = resolve_inputs(Path(a.tex))
    res: dict = {}

    abstract = extract_abstract(tex)
    if abstract is None:
        res["abstract"] = {"found": False}
    else:
        n = count_rendered_words(abstract)
        name, advice = band(n)
        res["abstract"] = {"found": True, "words": n, "band": name, "advice": advice}

    res["structural"] = structural_checks(tex)

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

    s = res["structural"]
    print(f"R1  \\textbf dans le corps : {s['r1_textbf_body']} "
          f"(revoir : titres/captions/en-tetes de tableau legitimes, le reste non)")
    print(f"R2  itemize : {s['r2_itemize']}  enumerate : {s['r2_enumerate']} "
          f"(cible : rare, protocoles/criteres formels seulement)")
    lay = s["r7_layout"]
    bands = PARA_BANDS_TWOCOL if lay["two_column"] else PARA_BANDS_ONECOL
    print(f"R7  mise en page : {'deux colonnes' if lay['two_column'] else 'une colonne'} "
          f"({lay['source']}) -- seuils WARN {bands['warn']} / FLAG {bands['flag']} mots")
    if s["r7_long_paragraphs"]:
        print(f"R7  paragraphes longs : {len(s['r7_long_paragraphs'])} a scinder")
        for p in s["r7_long_paragraphs"][:15]:
            print(f"    [{p['severity']}] {p['words']} mots, ligne {p['line']} : {p['excerpt']}...")
    else:
        print("R7  paragraphes longs : aucun")
    print(f"R8  tirets cadratins (---/—) : {s['r8_em_dash']}")
    if s["r9_orphan_labels"]:
        print(f"R9  labels orphelins (jamais references) : {len(s['r9_orphan_labels'])}")
        for lbl in s["r9_orphan_labels"][:15]:
            print(f"    {lbl}")
    else:
        print("R9  labels orphelins : aucun")

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
