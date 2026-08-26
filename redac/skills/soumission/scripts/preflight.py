#!/usr/bin/env python3
"""Controle de pre-vol d'un manuscrit avant soumission.

Repond a une seule question : ce projet est-il en etat d'etre soumis aujourd'hui ?
Ne corrige rien, ne soumet rien. Rend un verdict par point de controle, avec la
mesure qui le fonde, pour qu'aucun blocage ne soit decouvert au milieu d'un
formulaire de portail.

Points bloquants (l'auteur les a poses comme conditions) :
    - une version francaise `main_fr.tex` existe et n'est pas en retard sur l'anglais
    - le manuscrit compile et le PDF est plus recent que la source
    - la declaration d'assistance IA est presente

Usage : preflight.py [chemin_projet] [--journal CLE] [--target-words N]
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

OK, WARN, FAIL = "OK  ", "TIEDE", "BLOC"


class Report:
    def __init__(self) -> None:
        self.lines: list[tuple[str, str, str]] = []

    def add(self, level: str, label: str, detail: str) -> None:
        self.lines.append((level, label, detail))

    def render(self) -> int:
        order = {FAIL: 0, WARN: 1, OK: 2}
        for level, label, detail in sorted(self.lines, key=lambda x: order[x[0]]):
            tag = {OK: "[ok]", WARN: "[!]", FAIL: "[BLOQUANT]"}[level]
            print(f"{tag:11s} {label}")
            for line in detail.splitlines():
                print(f"            {line}")
        n_fail = sum(1 for l, _, _ in self.lines if l == FAIL)
        n_warn = sum(1 for l, _, _ in self.lines if l == WARN)
        print()
        if n_fail:
            print(f"VERDICT : NON. {n_fail} point(s) bloquant(s), {n_warn} reserve(s).")
            return 1
        if n_warn:
            print(f"VERDICT : POSSIBLE avec {n_warn} reserve(s) a lever ou a assumer.")
            return 0
        print("VERDICT : OUI, le paquet est complet.")
        return 0


# --------------------------------------------------------------------------
# lecture LaTeX
# --------------------------------------------------------------------------

def strip_comments(text: str) -> str:
    """Retire les commentaires LaTeX sans casser les pourcentages echappes."""
    out = []
    for line in text.splitlines():
        cut, i = None, 0
        while i < len(line):
            if line[i] == "%" and (i == 0 or line[i - 1] != "\\"):
                cut = i
                break
            i += 1
        out.append(line if cut is None else line[:cut])
    return "\n".join(out)


def resolve_inputs(path: Path, seen: set[Path] | None = None, depth: int = 0) -> str:
    """Concatene un .tex et tout ce qu'il \\input / \\include, recursivement.

    Sans cette resolution, toute mesure de longueur ment : un main.tex de 180
    lignes peut porter un manuscrit de 2 000 lignes.
    """
    seen = seen if seen is not None else set()
    if depth > 8 or not path.exists() or path.resolve() in seen:
        return ""
    seen.add(path.resolve())
    text = strip_comments(path.read_text(encoding="utf-8", errors="replace"))

    def sub(m: re.Match) -> str:
        target = m.group(2).strip()
        cand = path.parent / target
        for p in (cand, cand.with_suffix(".tex"), Path(str(cand) + ".tex")):
            if p.exists():
                return "\n" + resolve_inputs(p, seen, depth + 1) + "\n"
        return ""

    return re.sub(r"\\(input|include)\s*\{([^}]+)\}", sub, text)


def count_words(tex: str) -> int:
    body = re.sub(r"\\begin\{(figure|table|equation|align|lstlisting|verbatim)\*?\}"
                  r".*?\\end\{\1\*?\}", " ", tex, flags=re.S)
    body = re.sub(r"\\(cite|ref|label|includegraphics)\w*\s*(\[[^\]]*\])?\{[^}]*\}", " ", body)
    body = re.sub(r"\\[a-zA-Z@]+\*?", " ", body)
    body = re.sub(r"[{}$&~^_\\]", " ", body)
    return len([w for w in re.split(r"\s+", body) if re.search(r"[A-Za-z]", w)])


def section_words(tex: str) -> list[tuple[str, int]]:
    parts = re.split(r"\\section\*?\{([^}]*)\}", tex)
    out = []
    if parts[0].strip():
        out.append(("(preambule et resume)", count_words(parts[0])))
    for i in range(1, len(parts) - 1, 2):
        out.append((parts[i], count_words(parts[i + 1])))
    return out


def abstract_words(tex: str) -> int | None:
    m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", tex, flags=re.S)
    if m:
        return count_words(m.group(1))
    m = re.search(r"\\abstract\s*\{(.*?)\n\s*\}\s*\n", tex, flags=re.S)
    return count_words(m.group(1)) if m else None


def mtime(p: Path) -> datetime:
    return datetime.fromtimestamp(p.stat().st_mtime)


# --------------------------------------------------------------------------
# controles
# --------------------------------------------------------------------------

def check_french(art: Path, rep: Report) -> None:
    en, fr = art / "main.tex", art / "main_fr.tex"
    if not fr.exists():
        rep.add(FAIL, "Version francaise absente",
                f"attendu {fr}\n"
                "Condition posee par l'auteur : toute soumission est accompagnee\n"
                "d'une traduction fidele. La produire avant d'aller plus loin.")
        return
    ten, tfr = resolve_inputs(en), resolve_inputs(fr)
    wen, wfr = count_words(ten), count_words(tfr)
    sen = [s for s, _ in section_words(ten)]
    sfr = [s for s, _ in section_words(tfr)]
    detail = (f"anglais {wen} mots / {len(sen)} sections\n"
              f"francais {wfr} mots / {len(sfr)} sections")
    late = mtime(en) > mtime(fr)
    if late:
        detail += (f"\nmain.tex modifie le {mtime(en):%Y-%m-%d %H:%M}, "
                   f"main_fr.tex le {mtime(fr):%Y-%m-%d %H:%M}")
    ratio = wfr / wen if wen else 0
    if len(sfr) != len(sen):
        rep.add(FAIL, "Version francaise desynchronisee",
                detail + "\nLe nombre de sections differe : la traduction n'est plus fidele.")
    elif ratio < 0.85 or ratio > 1.35:
        rep.add(WARN, "Version francaise de longueur suspecte",
                detail + f"\nratio fr/en = {ratio:.2f} (attendu 0.95 a 1.20 pour "
                "une traduction fidele du francais vers l'anglais)")
    elif late:
        rep.add(WARN, "Version francaise plus ancienne que l'anglaise",
                detail + "\nRepasser les modifications recentes de main.tex dans main_fr.tex.")
    else:
        rep.add(OK, "Version francaise presente et alignee", detail)


def check_preamble_parity(art: Path, rep: Report) -> None:
    """Compare le gabarit des deux versions, pas seulement leur texte.

    Une refonte de gabarit se repercute rarement en entier : le corps est traduit,
    mais le style de citation, les paquets et la nomenclature des rubriques restent
    ceux de l'ancienne cible. C'est invisible a la relecture du contenu, et c'est
    exactement ce que le portail verifie. Vecu sur Rv1025 : le francais est reste en
    citations numerotees huit jours apres le passage de l'anglais en auteur-annee.
    """
    en, fr = art / "main.tex", art / "main_fr.tex"
    if not (en.exists() and fr.exists()):
        return
    ten, tfr = strip_comments(en.read_text(encoding="utf-8", errors="replace")), \
        strip_comments(fr.read_text(encoding="utf-8", errors="replace"))

    def style(t: str) -> str:
        m = re.search(r"\\bibliographystyle\{([^}]*)\}", t)
        return m.group(1) if m else "(aucun)"

    def natbib(t: str) -> str:
        m = re.search(r"\\usepackage\[([^\]]*)\]\{natbib\}", t)
        return m.group(1) if m else "(sans option)"

    def packages(t: str) -> set[str]:
        return {p.strip() for m in re.findall(r"\\usepackage(?:\[[^\]]*\])?\{([^}]+)\}", t)
                for p in m.split(",")}

    ecarts = []
    if style(ten) != style(tfr):
        ecarts.append(f"bibliographystyle : {style(ten)} en anglais, "
                      f"{style(tfr)} en francais")
    if natbib(ten) != natbib(tfr):
        ecarts.append(f"options natbib : [{natbib(ten)}] en anglais, "
                      f"[{natbib(tfr)}] en francais")
    only_en, only_fr = packages(ten) - packages(tfr), packages(tfr) - packages(ten)
    ignorables = {"babel", "inputenc", "fontenc", "csquotes", "polyglossia"}
    only_en, only_fr = only_en - ignorables, only_fr - ignorables
    if only_en:
        ecarts.append(f"paquets presents seulement en anglais : {', '.join(sorted(only_en))}")
    if only_fr:
        ecarts.append(f"paquets presents seulement en francais : {', '.join(sorted(only_fr))}")

    if ecarts:
        rep.add(WARN, "Gabarits divergents entre les deux versions",
                "\n".join(ecarts) + "\nUne refonte de gabarit n'a ete repercutee que "
                "d'un cote.")
    else:
        rep.add(OK, "Gabarits identiques entre les deux versions",
                f"style {style(ten)}, natbib [{natbib(ten)}], memes paquets")


def check_build(art: Path, rep: Report) -> None:
    tex, pdf = art / "main.tex", art / "main.pdf"
    if not tex.exists():
        rep.add(FAIL, "Manuscrit introuvable", f"attendu {tex}")
        return
    if not pdf.exists():
        rep.add(FAIL, "PDF absent", f"attendu {pdf} — compiler avant de soumettre (make)")
        return
    if mtime(pdf) < mtime(tex):
        rep.add(FAIL, "PDF perime",
                f"main.pdf du {mtime(pdf):%Y-%m-%d %H:%M} anterieur a main.tex "
                f"du {mtime(tex):%Y-%m-%d %H:%M}\n"
                "Le fichier televerse ne serait pas la version relue. Recompiler.")
        return
    detail = f"main.pdf du {mtime(pdf):%Y-%m-%d %H:%M}"
    if shutil.which("pdfinfo"):
        try:
            info = subprocess.run(["pdfinfo", str(pdf)], capture_output=True,
                                  text=True, timeout=20).stdout
            pages = re.search(r"Pages:\s+(\d+)", info)
            if pages:
                detail += f", {pages.group(1)} pages"
        except (subprocess.SubprocessError, OSError):
            pass
    if shutil.which("pdftotext"):
        try:
            txt = subprocess.run(["pdftotext", str(pdf), "-"], capture_output=True,
                                 text=True, timeout=60).stdout
            n_undef = len(re.findall(r"\?\?", txt))
            if n_undef:
                rep.add(WARN, "References non resolues dans le PDF",
                        f"{n_undef} occurrences de '??' — relancer bibtex/biber et recompiler")
        except (subprocess.SubprocessError, OSError):
            pass
    rep.add(OK, "Manuscrit compile", detail)


def check_length(art: Path, rep: Report, target: int | None, abstract_max: int | None) -> None:
    tex = resolve_inputs(art / "main.tex")
    if not tex:
        return
    total = count_words(tex)
    secs = section_words(tex)
    detail = f"corps {total} mots\n" + "\n".join(
        f"  {name[:46]:46s} {n:5d}" for name, n in secs)
    aw = abstract_words(tex)
    if aw is not None:
        detail += f"\n  {'(resume)':46s} {aw:5d}"
    if target and total > target:
        rep.add(WARN, "Manuscrit plus long que la cible",
                detail + f"\ncible {target} mots, depassement de {total - target}. "
                "Basculer le materiel de moindre impact vers les supplementary.")
    elif target:
        rep.add(OK, "Longueur compatible avec la cible", detail + f"\ncible {target} mots")
    else:
        rep.add(OK, "Longueur mesuree", detail)
    if abstract_max and aw and aw > abstract_max:
        rep.add(FAIL, "Resume trop long",
                f"{aw} mots contre {abstract_max} autorises. "
                "Beaucoup de portails refusent le collage au-dela de la limite.")


def check_ai_declaration(art: Path, rep: Report) -> None:
    tex = resolve_inputs(art / "main.tex")
    low = tex.lower()
    has_decl = any(k in low for k in
                   ("generative ai", "ai-assisted", "artificial intelligence",
                    "claude code", "assistance d'outils d'intelligence"))
    if has_decl:
        model = re.search(r"claude\s+(sonnet|opus|fable|haiku)\s*[\d.]*", low)
        rep.add(OK, "Declaration d'assistance IA presente",
                f"modele nomme : {model.group(0) if model else 'non identifie dans le texte'}\n"
                "Verifier qu'il correspond au modele reellement employe.")
    else:
        rep.add(FAIL, "Declaration d'assistance IA absente",
                "Obligatoire pour tout manuscrit produit dans cet environnement.\n"
                "Texte canonique : references/soumission.md du skill cycle-projet.")


def check_figures(art: Path, rep: Report) -> None:
    tex = resolve_inputs(art / "main.tex")
    refs = re.findall(r"\\includegraphics\s*(?:\[[^\]]*\])?\s*\{([^}]+)\}", tex)
    if not refs:
        rep.add(WARN, "Aucune figure detectee", "manuscrit sans \\includegraphics")
        return
    missing = []
    for r in refs:
        base = art / r
        found = base.exists() or any(
            base.with_suffix(ext).exists() for ext in (".pdf", ".png", ".jpg", ".eps"))
        if not found:
            missing.append(r)
    if missing:
        rep.add(FAIL, "Figures introuvables",
                f"{len(missing)}/{len(refs)} : " + ", ".join(missing[:8]))
    else:
        rep.add(OK, "Figures presentes", f"{len(refs)} fichiers references, tous trouves")


def check_supplementary(art: Path, rep: Report) -> None:
    d = art / "supplementary_materials"
    tex = resolve_inputs(art / "main.tex")
    cited = set(re.findall(
        r"(?:Table|Tableau|Fig(?:ure)?\.?|Data|Dataset|File)\s*~?\s*S\s?(\d+)", tex))
    cited |= set(re.findall(r"\\ref\{(?:supp|sm|si|s)[:_-][^}]+\}", tex, flags=re.I))
    mentions = len(re.findall(r"[Ss]upplementar", tex))
    if not d.exists():
        if cited or mentions:
            rep.add(WARN, "Supplementary cites mais repertoire absent",
                    f"{len(cited)} elements numerotes et {mentions} mentions du mot, "
                    f"{d} introuvable")
        return
    files = [p for p in d.rglob("*") if p.is_file()]
    detail = (f"{len(files)} fichiers dans {d.name}\n"
              f"{len(cited)} elements numerotes cites, {mentions} mentions du mot "
              "'supplementary' dans le manuscrit")
    if files and not cited and not mentions:
        rep.add(FAIL, "Supplementary jamais cites dans le manuscrit",
                detail + "\nUn fichier supplementaire qu'aucune phrase n'appelle sera "
                "ignore par les relecteurs et parfois refuse par le portail.")
    elif files and not cited:
        rep.add(WARN, "Supplementary cites sans numerotation",
                detail + "\nVerifier que chaque fichier televerse a un appel identifiable "
                "(Table S1, Figure S2...) : c'est ce que le portail demande de nommer.")
    else:
        rep.add(OK, "Supplementary materials", detail)


def check_registry(project: str, journal: str | None, rep: Report) -> None:
    script = Path(__file__).with_name("submissions.py")
    try:
        out = subprocess.run([sys.executable, str(script), "list", "--project", project],
                             capture_output=True, text=True, timeout=30)
        listing = out.stdout.strip()
    except (subprocess.SubprocessError, OSError) as e:
        rep.add(WARN, "Registre illisible", str(e))
        return
    if "registre vide" in listing:
        rep.add(OK, "Aucune soumission anterieure pour ce projet", listing)
    else:
        rep.add(WARN, "Ce projet a deja un historique de soumission", listing)
    if journal:
        try:
            out = subprocess.run([sys.executable, str(script), "variety", journal],
                                 capture_output=True, text=True, timeout=30)
            level = FAIL if out.returncode == 2 else (
                WARN if "ALERTE" in out.stdout else OK)
            rep.add(level, f"Regle de variation pour {journal}", out.stdout.strip())
        except (subprocess.SubprocessError, OSError) as e:
            rep.add(WARN, "Regle de variation non evaluee", str(e))


def journal_limits(key: str) -> tuple[int | None, int | None, str]:
    """Lit les limites de la revue visee dans la base, pour ne pas les retaper."""
    sys.path.insert(0, str(Path(__file__).parent))
    try:
        import journals  # noqa: PLC0415
    except ImportError:
        return None, None, ""
    row = next((r for r in journals.load() if r.get("key") == key), None)
    if not row:
        return None, None, f"revue inconnue de la base : {key}"
    body = journals.parse_words(row.get("length_limit", ""))
    abstract = journals.parse_words(row.get("abstract_limit", ""))
    label = (f"{row.get('name')} : corps {row.get('length_limit')}, "
             f"resume {row.get('abstract_limit')}")
    return body, abstract, label


def check_git(art: Path, rep: Report) -> None:
    if not (art / ".git").exists():
        rep.add(WARN, "article/ n'est pas un depot Git", "aucun figement possible")
        return
    try:
        st = subprocess.run(["git", "-C", str(art), "status", "--porcelain"],
                            capture_output=True, text=True, timeout=30).stdout.strip()
    except (subprocess.SubprocessError, OSError) as e:
        rep.add(WARN, "Etat Git illisible", str(e))
        return
    if st:
        rep.add(WARN, "Modifications non commitees dans article/",
                f"{len(st.splitlines())} fichiers\n"
                "Committer avant de soumettre : la version deposee doit etre figee "
                "et retrouvable.")
    else:
        rep.add(OK, "article/ propre", "aucune modification non commitee")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("project_dir", nargs="?", default=".")
    p.add_argument("--journal", help="cle de la revue visee, pour la regle de variation")
    p.add_argument("--target-words", type=int, help="limite de la revue visee")
    p.add_argument("--abstract-max", type=int, help="limite de resume de la revue visee")
    p.add_argument("--subdir", default="article",
                   help="nom du sous-repertoire article a auditer, pour un projet "
                        "portant plusieurs manuscrits (ex. article2 pour un second papier)")
    args = p.parse_args()

    root = Path(args.project_dir).resolve()
    art = root / args.subdir
    if not art.exists():
        print(f"pas de repertoire {args.subdir}/ dans {root}", file=sys.stderr)
        return 1

    print(f"Pre-vol de soumission — {root.name}")
    print(f"{root}")
    target, abstract_max = args.target_words, args.abstract_max
    if args.journal:
        j_body, j_abs, label = journal_limits(args.journal)
        target = target if target is not None else j_body
        abstract_max = abstract_max if abstract_max is not None else j_abs
        print(f"Cible : {label or args.journal}")
    print()
    rep = Report()
    check_build(art, rep)
    check_french(art, rep)
    check_preamble_parity(art, rep)
    check_length(art, rep, target, abstract_max)
    check_ai_declaration(art, rep)
    check_figures(art, rep)
    check_supplementary(art, rep)
    check_git(art, rep)
    check_registry(root.name, args.journal, rep)
    if not args.journal:
        rep.add(WARN, "Aucune revue cible passee",
                "Sans --journal, ni les limites de longueur ni la regle de variation "
                "ne sont evaluees.\nRelancer avec --journal <cle> une fois la cible "
                "choisie (journals.py match pour la trouver).")
    return rep.render()


if __name__ == "__main__":
    sys.exit(main())
