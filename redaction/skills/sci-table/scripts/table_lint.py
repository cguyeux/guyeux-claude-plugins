#!/usr/bin/env python3
"""table_lint.py — audit mecanique des tableaux d'un manuscrit LaTeX.

Ne remplace pas le jugement : il mesure ce qu'une relecture lineaire ne voit pas
(precision heterogene d'une colonne, colonne constante, largeur reelle, rustines
de reduction, tableau non cite) et rend un rapport groupe par tableau.

Usage
    python3 table_lint.py main.tex [supplementary.tex ...] [--json] [--width 75]
    python3 table_lint.py --corpus ~/docs/codes/mtbc          # audit de plusieurs projets

Severites
    FOND   le tableau ne devrait pas etre ce qu'il est (mauvais vehicule, colonne inutile)
    FORME  le tableau est le bon objet mais mal mis en forme
    INFO   signal a verifier a l'oeil, pas necessairement un defaut

Sans dependance externe.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from collections import Counter

# --- largeurs cibles, en caracteres a 10 pt -----------------------------------
# Mesure de reference : une ligne de texte a 10 pt sur \textwidth d'un article
# une colonne (~ 160 mm) porte environ 90 caracteres ; une colonne d'un article
# deux colonnes (~ 85 mm) en porte environ 48. Ces bornes servent d'alarme, pas
# de preuve : seul le PDF compile tranche (voir la regle T2).
WIDTH_ONECOL = 90
WIDTH_TWOCOL = 48

FLOAT_ENVS = r"table\*?|longtable\*?|sidewaystable\*?|table\*"
INNER_ENVS = r"tabular\*?|tabularx|tblr|longtable|NiceTabular|array"

RULE_RE = re.compile(
    r"\\(?:toprule|midrule|bottomrule|hline|cmidrule\s*(?:\([^)]*\))?\s*\{[^}]*\}"
    r"|cmidrule|addlinespace(?:\[[^\]]*\])?|specialrule\{[^}]*\}\{[^}]*\}\{[^}]*\})"
)
MACRO_RE = re.compile(r"\\[a-zA-Z@]+\*?(?:\[[^\]]*\])?")
NUM_RE = re.compile(r"^[-+(]?\s*\d[\d\s\u00a0,.']*\d*\s*\)?$")


def strip_comments(src: str) -> str:
    return re.sub(r"(?<!\\)%.*", "", src)


def clean_cell(cell: str) -> str:
    """Texte visible approche d'une cellule.

    Les macros de mise en forme sont depliees ; toute autre macro (un symbole
    mathematique, par exemple) compte pour un caractere, de sorte que la largeur
    estimee reste juste et que l'en-tete reste identifiable dans le rapport.
    """
    c = cell
    c = re.sub(r"\\multicolumn\{\d+\}\{[^}]*\}\{(.*)\}", r"\1", c, flags=re.S)
    c = re.sub(r"\\multirow\{[^}]*\}\{[^}]*\}\{(.*)\}", r"\1", c, flags=re.S)
    for _ in range(3):
        c = re.sub(r"\\(?:textbf|textit|texttt|emph|mathrm|mathit|text|num|si|bfseries|itshape)\s*\{([^{}]*)\}",
                   r"\1", c)
    c = c.replace("$", "")
    c = MACRO_RE.sub("*", c)
    c = c.replace("{", "").replace("}", "").replace("~", " ").replace("\\", "")
    return re.sub(r"\s+", " ", c).strip()


def short(txt: str, n: int = 22) -> str:
    txt = txt or ""
    return txt if len(txt) <= n else txt[: n - 1] + "\u2026"


def as_number(cell: str):
    """Rend (valeur, nb_decimales) si la cellule est un nombre nu, sinon None."""
    c = clean_cell(cell)
    c = c.replace("\u00a0", "").replace(" ", "").replace("'", "")
    if not c or not NUM_RE.match(c):
        return None
    neg = c.startswith("-") or c.startswith("(")
    c = c.strip("()+-")
    # separateur de milliers : 12,345 ou 12.345 selon la locale, ambigu -> on
    # ne compte les decimales que si le dernier groupe n'a pas exactement 3 chiffres
    if "," in c and "." in c:
        c = c.replace(",", "")
    parts = re.split(r"[.,]", c)
    if len(parts) == 1:
        dec = 0
    else:
        last = parts[-1]
        dec = 0 if (len(last) == 3 and len(parts[0]) <= 3 and len(parts) > 1 and len(c.split(parts[-1])[0]) <= 4 and "." not in c[:-4]) else len(last)
    try:
        val = float(re.sub(r"[,](?=\d{3}\b)", "", c).replace(",", "."))
    except ValueError:
        return None
    return (-val if neg else val, dec)


class Table:
    def __init__(self, path, env, body, start_line):
        self.path = path
        self.env = env
        self.body = body
        self.line = start_line
        self.findings = []
        self.colspec = ""
        self.grid = []
        self.header = []
        self.slides = False
        self.parse()

    # -- extraction ------------------------------------------------------------
    def parse(self):
        m = re.search(
            r"\\begin\{(" + INNER_ENVS + r")\}\s*(\[[^\]]*\])?\s*(\{[^{}]*\})?\s*"
            r"(\{(?:[^{}]|\{[^{}]*\})*\})",
            self.body,
            re.S,
        )
        if not m:
            self.inner = None
            return
        self.inner = m.group(1)
        self.colspec = (m.group(4) or "")[1:-1]
        content = self.body[m.end():]
        content = re.split(r"\\end\{" + re.escape(self.inner) + r"\}", content)[0]
        self.content = content
        content = RULE_RE.sub(" ", content)
        rows = [r for r in re.split(r"\\\\(?:\s*\[[^\]]*\])?", content) if r.strip()]
        grid = []
        for r in rows:
            cells = re.split(r"(?<!\\)&", r)
            if any(c.strip() for c in cells):
                grid.append([c.strip() for c in cells])
        self.grid = grid
        self.header = grid[0] if grid else []

    @property
    def ncol(self):
        if self.grid:
            return max(len(r) for r in self.grid)
        return 0

    @property
    def nrow(self):
        return max(0, len(self.grid) - 1)

    def column(self, i):
        return [r[i] for r in self.grid[1:] if len(r) > i]

    def add(self, sev, rule, msg, fix=None):
        self.findings.append(dict(sev=sev, rule=rule, msg=msg, fix=fix))

    # -- identite --------------------------------------------------------------
    @property
    def label(self):
        m = re.search(r"\\label\{([^}]*)\}", self.body)
        return m.group(1) if m else None

    @property
    def caption(self):
        m = re.search(r"\\caption\s*(\[[^\]]*\])?\s*\{", self.body)
        if not m:
            return None
        i = self.body.index("{", m.end() - 1)
        depth, j = 0, i
        while j < len(self.body):
            if self.body[j] == "{":
                depth += 1
            elif self.body[j] == "}":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        return self.body[i + 1:j]

    def est_width(self):
        """Largeur estimee en caracteres : somme des maxima par colonne + gouttieres."""
        w = 0
        for i in range(self.ncol):
            col = [clean_cell(r[i]) for r in self.grid if len(r) > i]
            w += max((len(c) for c in col), default=0)
        return w + 2 * max(0, self.ncol - 1)


# --- regles -------------------------------------------------------------------

def lint_table(t: Table, src: str, target_width: int, in_supp: bool):
    if t.inner is None:
        t.add("INFO", "T0", "environnement flottant sans tabular reconnu : audit impossible")
        return

    # T1 vehicule
    if t.nrow <= 2 and t.ncol <= 3:
        t.add("FOND", "T1", f"{t.nrow} ligne(s) x {t.ncol} colonne(s) : trop peu pour un flottant",
              "porter ces valeurs dans une phrase du corps, un tableau ne se justifie qu'a partir de trois lignes comparees")
    if t.nrow > 25 and not in_supp:
        t.add("FOND", "T1", f"{t.nrow} lignes dans le corps",
              "au-dela d'une vingtaine de lignes le lecteur ne compare plus, il consulte : verser en supplementaire, ou resumer par la statistique qui porte l'argument")
    if t.ncol == 2 and t.nrow <= 12:
        pairs = [clean_cell(r[1]) for r in t.grid[1:] if len(r) > 1]
        if pairs and sum(len(p.split()) > 4 for p in pairs) >= max(2, len(pairs) // 2):
            t.add("FOND", "T16", "deux colonnes dont la seconde est du texte long : liste deguisee en tableau",
                  "un environnement description, ou de la prose ; un tableau sert a comparer des valeurs, pas a etiqueter des definitions")

    # T2 largeur
    w = t.est_width()
    if w > target_width:
        t.add("FORME", "T2", f"largeur estimee ~{w} caracteres pour une cible de {target_width}",
              "reduire le NOMBRE de colonnes (fusionner n et %, sortir une colonne constante, transposer), avant d'envisager une police plus petite")

    # T3 rustines
    shrink = [c for c in ("\\tiny", "\\scriptsize", "\\footnotesize", "\\small") if c in t.body]
    boxes = [c for c in ("resizebox", "scalebox", "adjustbox") if c in t.body]
    if boxes:
        t.add("FOND" if w > target_width else "FORME", "T3",
              f"tableau mis a l'echelle par {', '.join(boxes)}",
              "une mise a l'echelle casse la taille de police du journal et rend le tableau incoherent avec le texte ; repenser le contenu ou passer en pleine page / rotation")
    elif shrink and w > target_width * 0.9:
        t.add("FORME", "T3", f"police reduite ({shrink[0]}) sur un tableau deja large",
              "la reduction est une rustine : verifier d'abord qu'aucune colonne n'est superflue")

    # T4 filets
    if "|" in t.colspec:
        t.add("FORME", "T4", "filets verticaux dans le colspec",
              "supprimer les | : la typographie scientifique separe les colonnes par l'espace (booktabs), jamais par un trait")
    nh = len(re.findall(r"\\hline", t.content))
    if nh >= 2:
        t.add("FORME", "T4", f"{nh} \\hline",
              "remplacer par \\toprule / \\midrule / \\bottomrule (booktabs) : un filet par frontiere logique, pas un par ligne")
    if "\\hline\\hline" in t.content.replace(" ", ""):
        t.add("FORME", "T4", "double filet", "un seul \\toprule")

    # colonnes : precision, unites, constantes, alignement
    numeric_cols, unaligned = [], []
    for i in range(t.ncol):
        raw = t.column(i)
        vals = [as_number(c) for c in raw]
        nums = [v for v in vals if v is not None]
        cleaned = [clean_cell(c) for c in raw]
        head = short(clean_cell(t.header[i])) if len(t.header) > i else f"col{i+1}"

        # T8 colonne constante
        nonempty = [c for c in cleaned if c and c not in ("-", "--", "---", "n/a", "NA")]
        if len(nonempty) >= 3 and len(set(nonempty)) == 1:
            t.add("FOND", "T8", f"colonne {i+1} ({head!r}) constante a {nonempty[0]!r}",
                  "une colonne qui ne discrimine rien n'informe pas : la supprimer et l'enoncer une fois en note ou dans la legende")

        if len(nums) >= 3 and len(nums) >= 0.6 * len(cleaned):
            numeric_cols.append(i)
            decs = {d for _, d in nums}
            if len(decs) > 1:
                t.add("FORME", "T5", f"colonne {i+1} ({head!r}) : precisions melangees {sorted(decs)}",
                      "une colonne se lit verticalement : meme nombre de decimales partout, fixe par la precision REELLE de la mesure la moins precise")
            if max(decs) >= 4 and max(abs(v) for v, _ in nums) < 1000:
                t.add("FORME", "T19", f"colonne {i+1} ({head!r}) : jusqu'a {max(decs)} decimales",
                      "arrondir : une precision affichee superieure a la precision de la mesure est une fausse promesse")
            big = [v for v, _ in nums if abs(v) >= 10000]
            # une colonne S groupe les milliers d'elle-meme (group-minimum-digits) :
            # n'alerter que sur les colonnes ordinaires
            if big and "S" not in t.colspec \
                    and not any(sep in "".join(raw) for sep in (",", "\\,", "\u00a0", "\\num")):
                t.add("FORME", "T12", f"colonne {i+1} ({head!r}) : nombres >= 10000 sans separateur de milliers",
                      "\\num{12345} (siunitx) rend 12 345 et aligne")
            if max(decs) > 0 and "S" not in t.colspec:
                unaligned.append(i + 1)

        # T7 unites dans les cellules
        unit_cells = [c for c in cleaned if re.search(r"\d\s*(%|bp|kb|Mb|nt|aa|SNPs?|years?|ans|Gb|min|h|x)\b", c)]
        if len(unit_cells) >= 3 and not re.search(r"\(|%|\[", head):
            t.add("FORME", "T7", f"colonne {i+1} ({head!r}) : unite repetee dans {len(unit_cells)} cellules",
                  "sortir l'unite dans l'en-tete, entre parentheses : la colonne ne porte plus que des nombres, donc comparables")

        # T9 p-values
        if re.search(r"\b[pq]\b|value|valeur", head, re.I):
            zeros = [c for c in cleaned if re.fullmatch(r"0(?:[.,]0+)?", c)]
            if zeros:
                t.add("FORME", "T9", f"colonne {i+1} ({head!r}) : {len(zeros)} valeur(s) affichee(s) a zero",
                      "une p-value n'est jamais nulle : ecrire < 10^{-3} (ou la borne reellement atteignable compte tenu du nombre de permutations)")

        # T20 marqueur de manquant incoherent
        missing = {c for c in cleaned if c in ("-", "--", "---", "NA", "n/a", "N/A", "ND", "")}
        if len(missing) > 1:
            t.add("FORME", "T20", f"colonne {i+1} ({head!r}) : marqueurs de donnee absente melanges {sorted(missing)!r}",
                  "un seul marqueur dans tout le tableau, explique en note ; distinguer 'non mesure' de 'mesure nulle'")

    if unaligned:
        t.add("FORME", "T6",
              f"colonne(s) {', '.join(map(str, unaligned))} a decimales sans colonne S de siunitx",
              "S[table-format=2.1] aligne sur la virgule decimale : sans lui les ordres de grandeur "
              "d'une meme colonne ne se comparent plus a l'oeil")

    # T15 couple n / %
    heads = [clean_cell(h).lower() for h in t.header]
    if any(h.strip() in ("n", "count", "effectif") for h in heads) and any("%" in h for h in heads):
        t.add("INFO", "T15", "colonnes n et % cote a cote",
              "legitime si le denominateur varie d'une ligne a l'autre ; redondant s'il est constant, auquel cas le donner une fois dans la legende")

    # T10 caption
    cap = t.caption
    if t.slides:
        return
    if cap is None:
        t.add("FORME", "T10", "pas de \\caption")
    else:
        capline = t.body.index("\\caption")
        tabline = t.body.index("\\begin{" + t.inner + "}")
        if capline > tabline and t.env.startswith("table"):
            t.add("FORME", "T10", "legende placee SOUS le tableau",
                  "une legende de tableau se lit avant lui (au-dessus), a l'inverse d'une figure : le lecteur a besoin de la cle avant les chiffres")
        capw = len(re.sub(r"\\[a-zA-Z]+", " ", cap).split())
        if capw < 8:
            t.add("FORME", "T10", f"legende de {capw} mots",
                  "une legende de tableau doit rendre le tableau autonome : ce qui est compte, sur quel echantillon (n), dans quelle unite, quel test")
        autonome = re.search(r"\bn\s*=|\bN\s*=|%|\bper\b|\bunit|\bp\s*[<=]|test\b", cap, re.I)
        if not autonome and capw < 25 and t.nrow >= 3:
            t.add("INFO", "T10", "legende ni effectif, ni unite, ni test",
                  "une legende de tableau doit se lire sans le corps : sur quoi porte le comptage, "
                  "dans quelle unite, quel test ; les abreviations de colonnes s'y developpent")

    # T11 citation dans le texte
    if not t.label:
        t.add("FORME", "T11", "pas de \\label : le tableau ne peut pas etre appele",
              "\\label{tab:...} puis \\cref{tab:...}")
    else:
        key = re.escape(t.label)
        cited = re.findall(r"\\(?:auto|c|C)?ref\*?\{[^}]*" + key, src)
        if not cited:
            t.add("FOND", "T11", f"tableau {t.label!r} jamais cite dans le corps",
                  "un tableau que le texte n'appelle jamais ne sert a rien : le citer a l'endroit de l'argument qu'il porte, ou le supprimer")

    # T13 notes bricolees
    if re.search(r"\\multicolumn\{\d+\}\{[^}]*\}\{\s*\\?(?:footnotesize|small|textit|emph)?\s*\{?\s*(?:Note|Abbrev|\*)", t.body, re.I) \
            and "threeparttable" not in t.body:
        t.add("FORME", "T13", "note de tableau bricolee en \\multicolumn",
              "threeparttable : les notes s'alignent sur la largeur du tableau et les appels sont numerotes")

    # T14 en-tete a deux niveaux
    if re.search(r"\\multicolumn\{[2-9]\}", t.body) and "cmidrule" not in t.body:
        t.add("FORME", "T14", "en-tete groupe par \\multicolumn sans \\cmidrule",
              "\\cmidrule(lr){2-3} sous chaque groupe : sans lui le lecteur ne sait pas ou s'arrete le groupe")

    # T17 longtable dans le corps
    if t.inner == "longtable" and not in_supp and t.nrow < 30:
        t.add("FORME", "T17", "longtable pour un tableau qui tient sur une page",
              "un simple table/tabular ; longtable interdit le placement flottant sans rien apporter ici")


def redundancy_with_text(t: Table, src: str):
    """Part des nombres du tableau qui sont aussi ecrits dans le corps du texte."""
    body_text = re.sub(r"\\begin\{(?:" + FLOAT_ENVS + r")\}.*?\\end\{(?:" + FLOAT_ENVS + r")\}", " ", src, flags=re.S)
    nums = set()
    for row in t.grid[1:]:
        for c in row:
            v = as_number(c)
            if v is not None and (v[1] > 0 or abs(v[0]) > 10):
                nums.add(clean_cell(c))
    if len(nums) < 8:
        return None
    hit = sum(1 for n in nums if re.search(r"(?<![\d.])" + re.escape(n) + r"(?![\d])", body_text))
    return hit / len(nums)


MARK = "\\SCITABLEFILE"


def read_tex(path, depth=0, seen=None):
    """Lit un .tex en depliant ses \\input / \\include.

    Un manuscrit modulaire place ses tableaux dans des fichiers separes ; sans
    depliage, la regle T11 (tableau jamais cite) se declenche a tort sur chacun,
    puisque la citation est dans le fichier maitre.
    """
    seen = seen if seen is not None else set()
    real = os.path.abspath(path)
    if real in seen or depth > 4:
        return ""
    seen.add(real)
    src = strip_comments(open(path, encoding="utf-8", errors="replace").read())
    base = os.path.dirname(real)

    def repl(m):
        name = m.group(2).strip()
        cand = name if name.endswith(".tex") else name + ".tex"
        full = cand if os.path.isabs(cand) else os.path.join(base, cand)
        if not os.path.exists(full):
            return m.group(0)
        inner = read_tex(full, depth + 1, seen)
        return f"{MARK}{{{full}}}\n{inner}\n{MARK}{{{real}}}\n"

    return re.sub(r"\\(input|include)\s*\{([^}]*)\}", repl, src)


def extract_tables(path):
    src = read_tex(path)
    is_slides = bool(re.search(r"\\documentclass(\[[^\]]*\])?\{beamer\}|\\begin\{frame\}", src))
    out = []
    def origin(pos):
        marks = list(re.finditer(re.escape(MARK) + r"\{([^}]*)\}", src[:pos]))
        return marks[-1].group(1) if marks else path

    for m in re.finditer(r"\\begin\{(" + FLOAT_ENVS + r")\}(.*?)\\end\{\1\}", src, re.S):
        line = src[:m.start()].count("\n") + 1
        out.append(Table(origin(m.start()), m.group(1), m.group(2), line))
    if is_slides:
        # une slide n'a ni legende ni numerotation : les regles de flottant ne
        # s'y appliquent pas, seules les regles de contenu et de forme valent
        for t in out:
            t.slides = True
        return src, out

    # tabular hors flottant
    consumed = " ".join(t.body for t in out)
    for m in re.finditer(r"\\begin\{(tabular\*?|tabularx|tblr)\}(.*?)\\end\{\1\}", src, re.S):
        if m.group(0)[:60] in consumed:
            continue
        line = src[:m.start()].count("\n") + 1
        t = Table(path, "inline", m.group(0), line)
        t.add("INFO", "T0", "tabular hors environnement table : ni legende, ni label, ni numerotation")
        out.append(t)
    return src, out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*", help="fichiers .tex")
    ap.add_argument("--corpus", help="repertoire a balayer (*/article/*.tex)")
    ap.add_argument("--width", type=int, default=WIDTH_ONECOL,
                    help=f"largeur cible en caracteres ({WIDTH_ONECOL} une colonne, {WIDTH_TWOCOL} deux colonnes)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    files = list(args.files)
    if args.corpus:
        files += sorted(glob.glob(os.path.join(os.path.expanduser(args.corpus), "*", "article", "*.tex")))
        files = [f for f in files if not os.path.basename(f).startswith("main_fr")]
    if not files:
        ap.error("aucun fichier : donner un .tex ou --corpus")

    report, counts = [], Counter()
    for path in files:
        if not os.path.exists(path):
            print(f"!! introuvable : {path}", file=sys.stderr)
            continue
        in_supp = "supp" in os.path.basename(path).lower()
        src, tables = extract_tables(path)
        for t in tables:
            lint_table(t, src, args.width, in_supp)
            red = redundancy_with_text(t, src)
            if red is not None and red > 0.7:
                t.add("FOND", "T18", f"{red:.0%} des valeurs du tableau sont aussi ecrites dans le texte",
                      "le texte doit dire ce que le tableau montre, pas le relire : garder le chiffre qui porte l'argument, renvoyer au tableau pour le reste")
            for f in t.findings:
                counts[f["rule"]] += 1
                counts[f["sev"]] += 1
            same = os.path.abspath(t.path) == os.path.abspath(path)
            report.append(dict(file=t.path, line=t.line if same else None, env=t.env, label=t.label,
                               ncol=t.ncol, nrow=t.nrow, width=t.est_width() if t.inner else None,
                               findings=t.findings))

    if args.json:
        print(json.dumps(dict(tables=report, counts=counts), indent=1, ensure_ascii=False))
        return

    for r in report:
        loc = f"{os.path.relpath(r['file'])}" + (f":{r['line']}" if r["line"] else " (inclus)")
        head = f"{loc}  [{r['env']}] {r['label'] or '(sans label)'}"
        print("\n" + head)
        print("  " + "-" * (len(head) - 2))
        print(f"  {r['nrow']} lignes x {r['ncol']} colonnes, largeur estimee ~{r['width']} car.")
        if not r["findings"]:
            print("  rien a signaler")
        for f in r["findings"]:
            print(f"  [{f['sev']:<5}] {f['rule']}  {f['msg']}")
            if f.get("fix"):
                print(f"          -> {f['fix']}")
    print("\n" + "=" * 72)
    print(f"{len(report)} tableau(x) ; "
          f"FOND {counts['FOND']}, FORME {counts['FORME']}, INFO {counts['INFO']}")
    top = [f"{k}:{v}" for k, v in counts.most_common() if k.startswith("T")]
    if top:
        print("regles declenchees : " + ", ".join(top))


if __name__ == "__main__":
    main()
