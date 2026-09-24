#!/usr/bin/env python3
"""Controle de pre-vol d'un manuscrit avant soumission.

Repond a une seule question : ce projet est-il en etat d'etre soumis aujourd'hui ?
Ne corrige rien, ne soumet rien. Rend un verdict par point de controle, avec la
mesure qui le fonde, pour qu'aucun blocage ne soit decouvert au milieu d'un
formulaire de portail.

Points bloquants (l'auteur les a poses comme conditions) :
    - la porte 3bis est franchie : `verdict_diffusion.md` porte un verdict favorable
      au mode de diffusion vise (skill `verdict-diffusion`)
    - la vitrine est cadree pour LA revue visee : `cadrage_editorial.md` porte un
      verdict ALIGNE pour cette cle de revue (skill `cadrage-editorial`)
    - une version francaise `main_fr.tex` existe et n'est pas en retard sur l'anglais
    - le manuscrit compile et le PDF est plus recent que la source
    - la declaration d'assistance IA est presente
    - le mesocentre est remercie si, et seulement si, un calcul est passe par lui
    - TBannotator/tblearn est credite (Senelle et Lecarpentier) si, et seulement si,
      l'outil a servi
    - la signature scientifique est celle qu'impose l'universite

Usage : preflight.py [chemin_projet] [--journal CLE] [--target-words N]
"""

from __future__ import annotations

import argparse
import hashlib
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
    # Accents LaTeX a l'ancienne (\'e, \`a, \^o, \"i, \c{c}...) : la regle generale ci-dessous
    # ne les reconnait pas comme des commandes (l'accent n'est pas une lettre) et laisse le
    # backslash survivre jusqu'au nettoyage final, qui le remplace par une espace et coupe le mot
    # en deux ("prot\'eine" -> "prot" + "'eine", compte comme 2 mots au lieu de 1). Les reduire a
    # la lettre nue avant tout le reste evite ce faux comptage sur du francais en accents
    # classiques (cf. Rv0007 2026-09-01 : ratio fr/en gonfle a 1.38 au lieu de 1.12).
    body = re.sub(r"\\[`'^\"~=.]\{([a-zA-Z])\}", r"\1", body)
    body = re.sub(r"\\c\{([a-zA-Z])\}", r"\1", body)
    body = re.sub(r"\\[`'^\"~=.]([a-zA-Z])", r"\1", body)
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

VERDICTS = {"SOUMETTRE", "DIFFUSER-SANS-COMITE", "NE-PAS-DIFFUSER", "ROUVRIR"}
NIVEAUX = {"RUPTURE", "AVANCEE", "AVANCÉE", "SOLIDE", "MINEUR"}
VERDICT_PEREMPTION_JOURS = 90


def read_verdict(root: Path) -> tuple[str, datetime | None, str | None] | None:
    """Lit le verdict de diffusion courant, ou None si le registre n'existe pas.

    Les verdicts sont empiles du plus recent au plus ancien dans
    `verdict_diffusion.md` : la premiere occurrence de chaque cle est donc la
    courante. Format defini par le skill `verdict-diffusion`. `niveau` n'existe
    que sur un bloc SOUMETTRE ; None sinon, y compris quand le bloc courant est
    SOUMETTRE mais que la cle manque (verdict incomplet, signale par l'appelant).
    """
    f = root / "verdict_diffusion.md"
    if not f.exists():
        return None
    text = f.read_text(encoding="utf-8", errors="replace")
    mv = re.search(r"^\s*verdict\s*:\s*([A-Z-]+)\s*$", text, flags=re.M)
    if not mv:
        return ("(illisible)", None, None)
    md = re.search(r"^\s*rendu le\s*:\s*(\d{4}-\d{2}-\d{2})\s*$", text, flags=re.M)
    when = datetime.strptime(md.group(1), "%Y-%m-%d") if md else None
    # Le bloc courant est le texte entre le debut du fichier et le prochain titre
    # de verdict (les blocs sont empiles du plus recent au plus ancien) : chercher
    # 'niveau' seulement dans ce perimetre pour ne jamais lire celui d'un verdict
    # anterieur.
    bloc_fin = text.find("\n## ", mv.end())
    bloc = text[: bloc_fin if bloc_fin != -1 else None]
    mn = re.search(r"^\s*niveau\s*:\s*([A-ZÉ-]+)\s*$", bloc, flags=re.M)
    niveau = mn.group(1) if mn else None
    return (mv.group(1), when, niveau)


def resoumission(root: Path, journal: str | None) -> dict | None:
    """La revue visee a-t-elle DEJA evalue ce manuscrit et invite a resoumettre ?

    Une resoumission apres « revise and resubmit » n'est pas un premier depot, et
    deux portes du pre-vol y perdent leur objet : la 3bis (le resultat merite-t-il
    d'etre diffuse) et le cadrage editorial (la vitrine risque-t-elle un
    desk-reject de principe). Dans les deux cas l'exterieur a tranche, et son avis
    est strictement plus fort que celui d'une instance interne : le bureau a laisse
    passer le manuscrit, deux relecteurs l'ont lu, l'editeur demande une version
    revisee. Bloquer un renvoi la-dessus fait manquer une echeance pour un rituel.

    Constate le 2026-09-12 sur mtbc/clos_soumis/Rv2438A (MIMET-D-26-01013, revise and
    resubmit du 2026-08-31, echeance 2026-09-28) : le pre-vol exigeait un verdict
    de diffusion et un cadrage editorial pour un manuscrit deja en evaluation.

    `returned-to-draft` compte autant que `revision`, et le cas est meme plus net :
    le portail a deja accepte le depot et attribue un numero, et le bureau demande
    des corrections de forme. Choisir la revue n'est plus une question, elle est
    choisie. Constate le 2026-09-12 sur mtbc/clos_soumis/Rv1125 (9451231), ou le pre-vol
    exigeait un cadrage editorial et opposait la regle de variation a un dossier
    deja ouvert chez la revue.

    Rend la ligne du registre central, ou None. Les deux portes restent BLOQUANTES
    quand le registre ne porte, chez cette revue, ni revision ni renvoi en
    brouillon.
    """
    if not journal:
        return None
    reg = Path.home() / ".agents" / "knowledge" / "journals" / "submissions.tsv"
    if not reg.exists():
        return None
    try:
        lignes = reg.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None
    if not lignes:
        return None
    cols = lignes[0].split("\t")
    for ligne in lignes[1:]:
        vals = ligne.split("\t")
        if len(vals) != len(cols):
            continue
        row = dict(zip(cols, vals))
        if (row.get("project", "").lower() == root.name.lower()
                and row.get("journal_key") == journal
                and row.get("status") in ("revision", "returned-to-draft")):
            return row
    return None


def check_verdict(root: Path, art: Path, journal: str | None, rep: Report) -> None:
    """Porte 3bis : ce travail merite-t-il d'etre diffuse, et par quelle voie ?

    Le pipeline qualite prouve que le manuscrit est bien FAIT ; il ne dit rien de
    la valeur du RESULTAT. Sans ce controle, un manuscrit bien fabrique autour d'un
    resultat sans valeur arrive intact jusqu'au portail : c'est exactement ce qui
    s'est produit sur `Mycobacterium_sp_novel` (27 pages, 3 relectures internes,
    claim-check et bib-check verts, decouverte centrale artefactuelle).
    """
    found = read_verdict(root)
    registre = root / "verdict_diffusion.md"
    rev = resoumission(root, journal)
    if found is None and rev:
        rep.add(WARN, "Porte 3bis non franchie, mais resoumission en cours",
                f"{rev.get('journal_name')} ({rev.get('manuscript_id') or 'sans id'}) "
                "a demande une version revisee.\n"
                "La question « ce resultat merite-t-il d'etre diffuse » a recu une "
                "reponse externe :\nle manuscrit est passe en evaluation et "
                "l'editeur invite a resoumettre. Non bloquant ici,\nmais rendre le "
                "verdict reste utile a la trace du projet (/verdict-diffusion).")
        return
    if found is None:
        rep.add(FAIL, "Verdict de diffusion absent (porte 3bis non franchie)",
                f"attendu {registre}\n"
                "Le pipeline qualite dit que le manuscrit est bien fait, pas qu'il\n"
                "merite d'etre publie. Rendre le verdict avec /verdict-diffusion\n"
                "avant toute preparation de depot.")
        return
    verdict, when, niveau = found
    if verdict not in VERDICTS:
        rep.add(FAIL, "Verdict de diffusion illisible",
                f"{registre} ne porte pas de ligne 'verdict : <VALEUR>' exploitable.\n"
                f"Valeurs admises : {', '.join(sorted(VERDICTS))}.")
        return
    date_txt = f"{when:%Y-%m-%d}" if when else "date absente"
    detail = f"verdict : {verdict} (rendu le {date_txt})"

    if verdict == "SOUMETTRE":
        if niveau is None:
            rep.add(FAIL, "SOUMETTRE sans niveau de contribution",
                    detail + "\nUn verdict SOUMETTRE doit porter une ligne "
                    "'niveau : <VALEUR>' (RUPTURE, AVANCEE, SOLIDE ou MINEUR) "
                    "et son paragraphe de justification -- voir le skill "
                    "verdict-diffusion, section \"Niveau de contribution\". "
                    "Rejouer /verdict-diffusion pour le completer.")
            return
        if niveau not in NIVEAUX:
            rep.add(FAIL, "Niveau de contribution illisible",
                    detail + f"\nniveau : {niveau} n'est pas une valeur admise.\n"
                    "Valeurs admises : RUPTURE, AVANCEE, SOLIDE, MINEUR.")
            return
        detail += f" -- niveau : {niveau}"

    if verdict in ("NE-PAS-DIFFUSER", "ROUVRIR"):
        suite = ("archivage apres passe /recadrage" if verdict == "NE-PAS-DIFFUSER"
                 else "retour en phase 1, pistes rouvertes")
        rep.add(FAIL, "Le verdict du projet interdit ce depot",
                detail + f"\nSuite prevue par ce verdict : {suite}.\n"
                "Preparer une soumission contredirait la conclusion que le projet a\n"
                "lui-meme tiree. Rejouer /verdict-diffusion si un fait nouveau l'a\n"
                "renverse, plutot que de passer outre.")
        return
    if verdict == "DIFFUSER-SANS-COMITE" and journal:
        rep.add(FAIL, "Revue visee alors que le verdict exclut le comite de lecture",
                detail + f"\ncible passee : {journal}\n"
                "Ce verdict autorise le preprint ou le depot de code, pas la\n"
                "soumission a comite. Relancer sans --journal, ou rejouer le verdict.")
        return

    if when is None:
        rep.add(WARN, "Verdict de diffusion sans date", detail +
                "\nAjouter la ligne 'rendu le : AAAA-MM-JJ' : sans elle, ni la\n"
                "peremption ni le retard sur le manuscrit ne sont mesurables.")
        return
    age = (datetime.now() - when).days
    tex = art / "main.tex"
    if age > VERDICT_PEREMPTION_JOURS:
        rep.add(WARN, "Verdict de diffusion perime",
                detail + f"\nrendu il y a {age} jours (peremption a "
                f"{VERDICT_PEREMPTION_JOURS}). Le rejouer avant de deposer.")
    # Comparaison a la JOURNEE : l'en-tete ne porte qu'une date, donc `when` vaut
    # minuit. Comparer les instants ferait crier la reserve sur tout verdict rendu
    # le jour meme d'une retouche du manuscrit, c'est-a-dire sur le cas normal.
    elif tex.exists() and mtime(tex).date() > when.date():
        rep.add(WARN, "Manuscrit modifie apres le verdict",
                detail + f"\nmain.tex modifie le {mtime(tex):%Y-%m-%d %H:%M}, "
                f"verdict rendu le {date_txt}\n"
                "Verifier que la modification ne touche pas ce que le verdict a juge.")
    else:
        rep.add(OK, "Porte 3bis franchie", detail)


CADRAGES = {"ALIGNE", "ALIGNÉ", "RETOUCHER", "CHANGER-DE-CIBLE", "ROUVRIR"}
CADRAGE_PEREMPTION_JOURS = 90


def vitrine(art: Path, nom: str = "main.tex") -> tuple[str, str]:
    """Titre et resume tels que l'editeur les lira, nettoyes de leur LaTeX.

    C'est exactement le materiel sur lequel se joue le desk-reject, et donc le seul
    perimetre que le cadrage editorial engage.
    """
    tex = resolve_inputs(art / nom)
    mt = re.search(r"\\title\s*\{(.+?)\}\s*(?:\n|\\)", tex, flags=re.S)
    ma = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", tex, flags=re.S)
    if not ma:
        ma = re.search(r"\\abstract\s*\{(.*?)\n\s*\}\s*\n", tex, flags=re.S)

    def clean(s: str) -> str:
        s = re.sub(r"\\(cite|ref|label)\w*\s*(\[[^\]]*\])?\{[^}]*\}", " ", s)
        s = re.sub(r"\\(emph|textit|textbf|texttt|textsc)\s*\{([^{}]*)\}", r"\2", s)
        s = re.sub(r"\\[a-zA-Z@]+\*?", " ", s)
        s = re.sub(r"[{}$&~^_\\]", " ", s)
        return re.sub(r"\s+", " ", s).strip()

    return clean(mt.group(1) if mt else ""), clean(ma.group(1) if ma else "")


def vitrine_empreinte(art: Path, nom: str = "main.tex") -> str:
    """Somme de controle de la vitrine, pour detecter qu'elle a bouge apres le cadrage.

    Volontairement insensible a la casse et aux espaces : une recompilation ou une
    reindentation ne doit pas faire crier la reserve, une reecriture du titre si.
    """
    titre, resume = vitrine(art, nom)
    blob = re.sub(r"\s+", " ", f"{titre}|{resume}").strip().lower()
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()[:8]


def read_cadrage(root: Path) -> tuple[str, str | None, datetime | None, str | None] | None:
    """Lit le cadrage editorial courant : (verdict, revue, date, empreinte).

    Meme convention que `verdict_diffusion.md` : les entrees sont empilees de la plus
    recente a la plus ancienne, donc la premiere occurrence de chaque cle est la
    courante. Format defini par le skill `cadrage-editorial`.
    """
    f = root / "cadrage_editorial.md"
    if not f.exists():
        return None
    text = f.read_text(encoding="utf-8", errors="replace")
    mv = re.search(r"^\s*verdict\s*:\s*([A-ZÉ-]+)\s*$", text, flags=re.M)
    if not mv:
        return ("(illisible)", None, None, None)
    bloc_fin = text.find("\n## ", mv.end())
    bloc = text[: bloc_fin if bloc_fin != -1 else None]
    mr = re.search(r"^\s*revue\s*:\s*(\S+)\s*$", bloc, flags=re.M)
    md = re.search(r"^\s*rendu le\s*:\s*(\d{4}-\d{2}-\d{2})\s*$", bloc, flags=re.M)
    me = re.search(r"empreinte\s+([0-9a-f]{8})", bloc)
    when = datetime.strptime(md.group(1), "%Y-%m-%d") if md else None
    return (mv.group(1), mr.group(1) if mr else None, when, me.group(1) if me else None)


def check_cadrage(root: Path, art: Path, journal: str | None, rep: Report) -> None:
    """Le titre et le resume ont-ils ete cadres pour LA revue visee ?

    Un manuscrit excellent se fait renvoyer par un editeur qui, en trois minutes de
    lecture du titre et du resume, ne voit pas ce que ce travail fait dans sa revue.
    Le pipeline qualite ne mesure pas cela, le choix de revue non plus : il ecarte
    les cibles impossibles sans jamais regarder ce que le manuscrit met en avant.
    Un cadrage rendu pour une autre revue ne vaut rien pour celle-ci.
    """
    if not journal:
        return
    found = read_cadrage(root)
    registre = root / "cadrage_editorial.md"
    rev = resoumission(root, journal)
    if found is None and rev:
        rep.add(OK, "Cadrage editorial sans objet (resoumission)",
                f"{rev.get('journal_name')} a deja fait passer ce manuscrit le bureau "
                "editorial\net l'evaluation externe : il n'y a plus de desk-reject de "
                "cadrage a eviter.")
        return
    if found is None:
        rep.add(FAIL, "Cadrage editorial absent",
                f"attendu {registre}, cible {journal}\n"
                "Le titre et le resume n'ont pas ete relus contre ce que cette revue\n"
                "publie reellement. Lancer /cadrage-editorial avant de deposer : un\n"
                "desk-reject de cadrage brule la revue pour douze mois et n'apprend rien.")
        return
    verdict, revue, when, empreinte = found
    if verdict not in CADRAGES:
        rep.add(FAIL, "Cadrage editorial illisible",
                f"{registre} ne porte pas de ligne 'verdict : <VALEUR>' exploitable.\n"
                f"Valeurs admises : {', '.join(sorted(CADRAGES))}.")
        return
    date_txt = f"{when:%Y-%m-%d}" if when else "date absente"
    detail = f"verdict : {verdict} pour {revue or '(revue non declaree)'} ({date_txt})"

    if revue and revue != journal:
        rep.add(FAIL, "Cadrage rendu pour une autre revue",
                detail + f"\ncible passee : {journal}\n"
                "Un cadrage ne se transpose pas d'une revue a l'autre : les clauses,\n"
                "la forme des titres et le vocabulaire different. Rejouer\n"
                f"/cadrage-editorial {journal} apres avoir relu l'entree {revue}.")
        return
    if revue is None:
        rep.add(FAIL, "Cadrage sans revue declaree",
                detail + "\nAjouter la ligne 'revue : <cle>' : sans elle, rien ne dit "
                "pour quelle cible ce cadrage a ete rendu.")
        return
    if verdict == "RETOUCHER":
        rep.add(FAIL, "Retouches de cadrage identifiees mais non integrees",
                detail + "\nRETOUCHER n'est pas un etat stable : appliquer les retouches,\n"
                "rejouer la simulation, puis empiler une entree ALIGNE. Sinon, trancher\n"
                "CHANGER-DE-CIBLE.")
        return
    if verdict in ("CHANGER-DE-CIBLE", "ROUVRIR"):
        suite = ("retour au choix de revue (/soumission phase 2)"
                 if verdict == "CHANGER-DE-CIBLE"
                 else "retour porte 3bis (/verdict-diffusion)")
        rep.add(FAIL, "Le cadrage editorial interdit ce depot",
                detail + f"\nSuite prevue par ce verdict : {suite}.\n"
                "Deposer contredirait la conclusion que la passe de cadrage a tiree.")
        return

    if when is None:
        rep.add(WARN, "Cadrage editorial sans date", detail +
                "\nAjouter la ligne 'rendu le : AAAA-MM-JJ'.")
        return
    actuelle = vitrine_empreinte(art)
    age = (datetime.now() - when).days
    if empreinte and empreinte != actuelle:
        rep.add(WARN, "Vitrine modifiee depuis le cadrage",
                detail + f"\nempreinte au cadrage {empreinte}, vitrine actuelle {actuelle}\n"
                "Le titre ou le resume ont change apres la passe : verifier que la\n"
                "modification ne defait pas ce que le cadrage avait aligne.")
    elif age > CADRAGE_PEREMPTION_JOURS:
        rep.add(WARN, "Cadrage editorial perime",
                detail + f"\nrendu il y a {age} jours (peremption a "
                f"{CADRAGE_PEREMPTION_JOURS}). Le corpus de la revue a vieilli.")
    else:
        rep.add(OK, "Vitrine cadree pour la revue visee",
                detail + (f"\nempreinte {actuelle}, inchangee depuis le cadrage"
                          if empreinte else ""))


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
                rep.add(FAIL, "References non resolues dans le PDF livre",
                        f"{n_undef} occurrences de '??' dans {pdf.name} — c'est ce que "
                        "verrait le relecteur. Relancer bibtex/biber et recompiler.")
        except (subprocess.SubprocessError, OSError):
            pass
    rep.add(OK, "Manuscrit compile", detail)


def compile_in_copy(art: Path, base: str, timeout: int = 600) -> dict:
    """Compile REELLEMENT `base` dans une copie, et rend ce que verrait le lecteur.

    Protocole eprouve le 2026-09-08 sur les 187 manuscrits du depot mtbc (piste
    P41.14.2). Trois pieges y ont ete mesures, et ce sont eux qui dictent la forme :

    1. Ne jamais compter les renvois non resolus sur la sortie CUMULEE de latexmk :
       la premiere passe precede la construction du .bbl, ses "Citation undefined"
       restent dans le flux meme quand le document final est propre. Un manuscrit
       parfaitement sain ressortait ainsi a 90 citations manquantes. On lit donc le
       .log de la DERNIERE passe.
    2. Compiler avec -outdir casse les bibliographies a chemin relatif
       (\bibliography{../litterature_review/references}), motif frequent : bibtex
       s'execute dans le repertoire de sortie et ne trouve plus la base.
    3. Meme avec BIBINPUTS etendu, -outdir produit encore des echecs fantomes quand
       le projet embarque un .bbl pre-construit plus riche que son .bib.

    D'ou la copie : `article/` et son voisin `litterature_review/` sont recopies dans
    un temporaire, les fichiers derives purges, et la compilation se fait EN PLACE,
    exactement comme la ferait l'auteur. Le depot n'est jamais touche.
    """
    import tempfile
    src = art / base
    if not src.exists():
        return {"absent": True}
    tmp = Path(tempfile.mkdtemp(prefix="preflight_"))
    try:
        shutil.copytree(art, tmp / "article")
        lr = art.parent / "litterature_review"
        if lr.is_dir():
            shutil.copytree(lr, tmp / "litterature_review")
        work = tmp / "article"
        for f in work.iterdir():
            if f.suffix.lstrip(".") in ("aux", "bbl", "blg", "out", "log", "fls",
                                        "fdb_latexmk", "toc", "lof", "lot"):
                f.unlink()
        try:
            proc = subprocess.run(["latexmk", "-pdf", "-interaction=nonstopmode", base],
                                  cwd=work, capture_output=True, text=True,
                                  encoding="utf-8", errors="replace", timeout=timeout)
            code = proc.returncode
        except subprocess.TimeoutExpired:
            return {"timeout": True}
        except (OSError, subprocess.SubprocessError) as exc:
            return {"erreur": str(exc)[:200]}
        stem = base[:-4]
        logf, blgf = work / f"{stem}.log", work / f"{stem}.blg"
        log = logf.read_text(encoding="utf-8", errors="replace") if logf.exists() else ""
        blg = blgf.read_text(encoding="utf-8", errors="replace") if blgf.exists() else ""
        return {
            "code": code,
            "pdf": (work / f"{stem}.pdf").exists(),
            "erreurs": re.findall(r"^! .*", log, re.M)[:3],
            "n_erreurs": len(re.findall(r"^! ", log, re.M)),
            "citations": len(re.findall(r"Citation `[^']+' on page \d+ undefined", log)),
            "refs": len(re.findall(r"Reference `[^']+' on page \d+ undefined", log)),
            "bibtex": [l for l in blg.splitlines()
                       if l.startswith(("I was expecting", "I couldn't"))][:2],
        }
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def check_compilation(art: Path, rep: Report) -> None:
    """Compile les DEUX versions et bloque sur tout renvoi non resolu.

    Le controle historique (`check_build`) verifiait qu'un PDF existait et qu'il
    etait posterieur au .tex : un manuscrit pouvait donc etre declare pret et se
    reveler bloque au depot. Cas vecu : `animal_vs_human` avait un PDF a jour, mais
    32 entrees de son .bib sans virgule avant le champ `verified` faisaient refuser
    la base ENTIERE par bibtex, et le PDF portait 79 citations et 68 renvois non
    resolus, soit des ?? partout sur une trentaine de pages.
    """
    if not shutil.which("latexmk"):
        rep.add(WARN, "latexmk absent",
                "compilation reelle non verifiee — installer latexmk")
        return
    for base, quoi in (("main.tex", "anglaise"), ("main_fr.tex", "francaise")):
        r = compile_in_copy(art, base)
        if r.get("absent"):
            continue                      # check_french traite deja l'absence du fr
        if r.get("timeout"):
            rep.add(FAIL, f"Compilation {quoi} en delai depasse",
                    f"{base} n'a pas fini de compiler en 10 min")
            continue
        if r.get("erreur"):
            rep.add(WARN, f"Compilation {quoi} non evaluee", r["erreur"])
            continue
        if not r["pdf"]:
            det = "\n".join(r["erreurs"]) or "aucune erreur nommee dans le log"
            rep.add(FAIL, f"Version {quoi} NE COMPILE PAS", f"{base}\n{det}")
            continue
        pb = []
        if r["n_erreurs"]:
            pb.append(f"{r['n_erreurs']} erreur(s) LaTeX")
        if r["citations"]:
            pb.append(f"{r['citations']} citation(s) non resolue(s)")
        if r["refs"]:
            pb.append(f"{r['refs']} renvoi(s) non resolu(s)")
        if pb:
            det = f"{base} : " + ", ".join(pb)
            if r["bibtex"]:
                det += "\nbibtex : " + " | ".join(x[:110] for x in r["bibtex"])
            det += ("\nCe sont les ?? que verrait le lecteur du PDF televerse. "
                    "Corriger avant de soumettre.")
            rep.add(FAIL, f"Version {quoi} compile mais porte des renvois non resolus", det)
        else:
            rep.add(OK, f"Version {quoi} compile proprement",
                    f"{base} : 0 erreur, 0 renvoi non resolu")


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


# ---------------------------------------------------------------------------
# Remerciements et affiliation. Deux formules imposees de l'exterieur, qu'aucune
# relecture de fond ne rattrape parce qu'elles ne sont pas du fond : le mesocentre
# demande a etre cite par tout article dont un calcul est passe chez lui, et
# l'universite impose la forme exacte de la signature scientifique.
# Texte destine a etre recopie tel quel dans le manuscrit : accents compris.
MESO_PHRASE = ("Computations have been performed on the supercomputer facilities "
               "of the Mésocentre de calcul de Franche-Comté.")
MESO_MARQUEURS_TEX = ("mesocentre de calcul de franche-comte", "supercomputer facilities",
                      "mesocentre de calcul")
# Traces d'un calcul distant dans la memoire du projet. Volontairement etroites :
# un faux positif ferait reclamer un remerciement pour un calcul qui n'a pas eu lieu.
MESO_TRACES = ("mesohelios", "mesologin", "mesocentre", "sbatch", "squeue", "slurm",
               "sur mh", "mh:/", "--gres=gpu", "scontrol")
MESO_FICHIERS = ("cahier_de_labo.md", "etat_des_decouvertes.md", "JOURNAL.md")

# Une ligne qui PARLE du garde-fou n'est pas la trace d'un calcul. Sans ce filtre,
# le controle se declenche sur sa propre documentation : constate sur mtbc/Rv2438A
# le 2026-09-12, ou le seul mot « mesocentre » des 5 000 lignes du cahier etait la
# phrase qui decrit cette regle, et le pre-vol bloquait un manuscrit dont aucun
# calcul n'etait jamais parti sur mp ni mh.
#
# La liste de mots-cles seule ne suffit pas, et l'echec est instructif : l'entree
# de cahier qui RENDAIT COMPTE de ce correctif a reintroduit le faux positif le
# jour meme, parce qu'elle citait le libelle de l'alerte sans employer aucun des
# mots de la liste. Un cahier de laboratoire parle de ses propres outils : c'est
# sa fonction. D'ou le second filtre, sur la FORME de l'occurrence -- un marqueur
# cite entre guillemets ou en emphase est une mention, pas une trace.
MESO_META = ("preflight", "garde-fou", "garde fou", "pre-vol", "prevol",
             "remerciement du mesocentre manquant", "skill soumission",
             "signature-et-remerciements", "verdict_diffusion", "cette regle",
             "faux positif", "non remercie", "le detecteur", "ce controle",
             "bloquant")


def _est_cite(ligne: str, marqueur: str, profondeur: int = 0) -> bool:
    """Le marqueur est-il entre guillemets ou en emphase, donc MENTIONNE ?

    « Mesocentre utilise mais non remercie » entre guillemets francais, "..." ou
    *...* designe le libelle d'une alerte, jamais un calcul qui a tourne.

    `profondeur` est le nombre de guillemets francais ouverts AVANT cette ligne.
    Il est indispensable et son absence a laisse passer le faux positif une
    TROISIEME fois le 2026-09-12 : une citation de deux lignes ne montre, sur la
    ligne du marqueur, que son guillemet fermant, et un test ligne par ligne
    conclut alors a une trace. Un cahier de laboratoire justifie a 100 colonnes,
    donc ses citations enjambent les retours a la ligne : c'est le cas normal, pas
    le cas limite.
    """
    i = ligne.find(marqueur)
    if i < 0:
        return False
    if profondeur > 0:
        return True  # citation francaise ouverte sur une ligne precedente
    # Citation ouverte plus haut et fermee ici : un « \u00bb » sans « \u00ab » avant lui.
    ferme_orphelin = ligne.find("\u00bb", i + len(marqueur))
    if ferme_orphelin >= 0 and ligne.rfind("\u00ab", 0, i) < 0:
        return True
    for ouvre, ferme in (("\u00ab", "\u00bb"), ('"', '"'), ("*", "*"),
                         ("`", "`"), ("\u201c", "\u201d")):
        avant = ligne.rfind(ouvre, 0, i)
        if avant < 0:
            continue
        apres = ligne.find(ferme, i + len(marqueur))
        if apres >= 0:
            return True
    return False

AFFIL_PROSCRITES = {
    "universite de franche-comte": "« Université de Franche-Comté » : nom d'avant 2025",
    "university of franche-comte": "« University of Franche-Comte » : nom d'avant 2025",
    "bourgogne-franche-comte": "« Bourgogne-Franche-Comté » : COMUE dissoute",
    "bourgogne franche-comte": "« Bourgogne Franche-Comté » : COMUE dissoute",
}
AFFIL_GENERATEUR = ("https://scienceouverte.umlp.fr/accueil/publications/"
                    "signature-scientifique/")
AFFIL_FORME = (
    "Forme imposee depuis janvier 2025 :\n"
    "  Université Marie et Louis Pasteur, (établissements-composantes employeurs "
    "ou hébergeurs des auteurs, dans leur ordre d'apparition), CNRS, institut "
    "FEMTO-ST, F-code postal Ville, France\n"
    "  anglais : Université Marie et Louis Pasteur, (...), CNRS, FEMTO-ST "
    "institute, F-code postal Ville, France")


def _sans_accents(t: str) -> str:
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", t)
                   if unicodedata.category(c) != "Mn")


def _delatex_accents(t: str) -> str:
    """Reduit les accents LaTeX a l'ancienne a la lettre nue.

    Meme piege que dans count_words : `Universit\\'e Marie et Louis Pasteur` ne
    contient pas la chaine « universite » tant que `\\'e` n'a pas ete reduit, et
    un controle d'affiliation naif declare alors non conforme un manuscrit qui
    l'est (constate sur mtbc/Rv3604c).
    """
    t = re.sub(r"\\[`'^\"~=.]\{([a-zA-Z])\}", r"\1", t)
    t = re.sub(r"\\c\{([a-zA-Z])\}", r"\1", t)
    t = re.sub(r"\\[`'^\"~=.]([a-zA-Z])", r"\1", t)
    return t


def _norm(t: str) -> str:
    return re.sub(r"[{}~]", "", _sans_accents(_delatex_accents(t))).lower()


# Indices qu'une ligne rapporte un calcul EXECUTE, et pas seulement le sujet
# « calcul distant » : un identifiant de job, un chemin sur la machine distante,
# une option de soumission. C'est le quatrieme etage de ce controle, et le dernier,
# parce que les trois premiers etaient des heuristiques de FORME (liste de mots,
# mots meta, guillemets) et qu'aucune ne peut distinguer un cahier qui PARLE de
# calcul distant d'un cahier qui en RAPPORTE un : toute phrase meta finit par
# ressembler a une trace. Celui-ci demande autre chose -- que la trace soit
# ACTIONNABLE. Un compte rendu de calcul porte presque toujours un numero de job
# ou un chemin ; une phrase sur l'outillage n'en porte pas.
MESO_PREUVES = (
    re.compile(r"\b(?:job|jobid|slurm)\s*:?\s*#?\s*\d{4,9}\b"),
    re.compile(r"\b\d{4,9}\b.{0,40}\b(?:slurm|sbatch|squeue|mesocentre|mesohelios)\b"),
    re.compile(r"\b(?:slurm|sbatch|squeue|mesocentre|mesohelios)\b.{0,40}\b\d{4,9}\b"),
    re.compile(r"m[hp]:/\S+"),
    re.compile(r"--gres=gpu|--partition|scontrol|squeue\s+-"),
    re.compile(r"\b(?:mesohelios|mesologin)\b"),
)


def _hors_citation(ligne: str) -> str:
    """La ligne privee de ses fragments cites, ou une preuve ne compte pas.

    Une phrase qui DECRIT une trace la cite souvent telle quelle, et un exemple
    syntaxiquement valide est indistinguable d'une trace : « un chemin de staging
    `mh:/Work` » porte litteralement un chemin distant sans qu'aucun calcul n'ait
    tourne. Chercher les preuves hors des backticks et des guillemets ferme ce
    dernier trou, quatrieme et derniere incarnation du faux positif du 2026-09-12.
    """
    for motif in (r"`[^`]*`", r"\u00ab[^\u00bb]*\u00bb", r'"[^"]*"',
                  r"\u201c[^\u201d]*\u201d"):
        ligne = re.sub(motif, " ", ligne)
    return ligne


def _traces_dans_memoire(root: Path, marqueurs: tuple[str, ...],
                          preuves: tuple[re.Pattern, ...],
                          meta: tuple[str, ...]) -> list[tuple[str, bool]]:
    """Ou la memoire du projet dit qu'une ressource externe a servi.

    Generalise sur `marqueurs` (vocabulaire qui trahit un usage) ce qui etait
    ecrit uniquement pour le mesocentre : la meme logique s'applique telle
    quelle au credit du a TBannotator/tblearn (Senelle et Lecarpentier), et
    factoriser evite qu'un correctif de forme (guillemets, meta-mentions) ne
    soit porte que par l'un des deux controles.

    Rend des couples (ou, preuve_forte). `preuve_forte` distingue une trace
    ACTIONNABLE -- numero de job, chemin distant, option de soumission -- d'une
    simple occurrence du vocabulaire. L'appelant bloque sur la premiere et se
    contente d'avertir sur la seconde : un mot ne vaut pas un fait, et un
    garde-fou qui bloque sur un mot finit par bloquer sur sa propre documentation,
    ce qui est arrive quatre fois le 2026-09-12.
    """
    vues: list[tuple[str, bool]] = []
    for nom in MESO_FICHIERS:
        p = root / nom
        if not p.exists():
            continue
        try:
            brut = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        profondeur = 0  # guillemets francais ouverts, suivis d'une ligne a l'autre
        for num, ligne in enumerate(brut.splitlines(), start=1):
            texte = _norm(ligne)
            if not ligne.strip():
                # Une citation n'enjambe pas un paragraphe. Sans cette remise a
                # zero, un guillemet ouvert et jamais ferme -- prose bancale,
                # copier-coller tronque -- masque TOUT le reste du fichier : un
                # faux negatif, donc un garde-fou muet sur un calcul reel, ce qui
                # est plus grave que le faux positif qu'on corrige ici.
                profondeur = 0
                continue
            ouverte = profondeur
            profondeur = max(0, profondeur + ligne.count("\u00ab") - ligne.count("\u00bb"))
            if any(m in texte for m in meta):
                continue  # la ligne documente le controle, elle ne trace aucun usage
            for m in marqueurs:
                if m in texte and not _est_cite(texte, m, ouverte):
                    nu = _hors_citation(texte)
                    forte = any(rx.search(nu) for rx in preuves)
                    vues.append((f"{nom}:{num} : « {m} »", forte))
                    break
            # Une preuve forte tranche ; sinon continuer, une ligne plus bas peut
            # en porter une.
            if vues and vues[-1][1]:
                break
    return vues


def meso_traces(root: Path) -> list[tuple[str, bool]]:
    """Ou la memoire du projet dit qu'un calcul est parti sur mp, mh ou Lumiere."""
    return _traces_dans_memoire(root, MESO_TRACES, MESO_PREUVES, MESO_META)


# ---------------------------------------------------------------------------
# Credit du a TBannotator/tblearn. Meme logique que le mesocentre, meme raison
# d'etre : ni prose ni memoire ne rattrapent un remerciement du a des personnes
# precises si rien ne le controle mecaniquement. Regle posee par CG le
# 2026-09-23 : Gaetan Senelle (auteur d'origine du pipeline TBannotator) ET
# Clement Lecarpentier (developpement et maintenance actuels, sujet de these)
# sont tous deux a remercier des que l'outil a servi -- l'un sans l'autre est
# incomplet. Voir ~/.agents/knowledge/signature-et-remerciements.md et la
# fiche de chacun dans collaborators.md.
TBANNO_PHRASE = ("We thank Gaëtan Senelle (original author) and Clément Lecarpentier "
                  "(current development) for TB-Annotator, used in this study for "
                  "[usage : requete de metadonnees / classification en lignee / ...].")
TBANNO_MARQUEURS_NOMS = ("senelle", "lecarpentier")
# Vocabulaire qui trahit un usage de l'outil, pas seulement sa mention en passant.
# Volontairement etroit sur le meme principe que MESO_TRACES : chaque variante de
# nom de skill (fetch-tbannotator, tbannotator-mcp, tbannotator-es, tbannotator-
# upstream) contient deja la sous-chaine "tbannotator".
TBANNO_TRACES = ("tbannotator", "tblearn", "tb-annotator", "tb annotator")
TBANNO_PREUVES = (
    re.compile(r"mcp__tbannotator__\w+"),
    re.compile(r"\btool_(?:query_postgres|get_schema|submit_accession"
               r"|submission_state|make_a_request|read_requests)\b"),
    re.compile(r"\btblearn[.\s]tbannotator\b"),
    re.compile(r"\b(?:requete|requête|query)\b.{0,40}\b(?:tbannotator|tblearn)\b"),
    re.compile(r"\b(?:tbannotator|tblearn)\b.{0,40}\b(?:requete|requête|query)\b"),
)


def tbanno_traces(root: Path) -> list[tuple[str, bool]]:
    """Ou la memoire du projet dit que TBannotator/tblearn a ete interroge."""
    return _traces_dans_memoire(root, TBANNO_TRACES, TBANNO_PREUVES, MESO_META)


def check_acknowledgements(root: Path, art: Path, rep: Report) -> None:
    """Le mesocentre est-il remercie quand il a servi, et seulement alors ?"""
    tex = _norm(resolve_inputs(art / "main.tex"))
    cite = any(m in tex for m in MESO_MARQUEURS_TEX)
    traces = meso_traces(root)

    fortes = [ou for ou, forte in traces if forte]
    faibles = [ou for ou, forte in traces if not forte]
    traces_txt = [ou for ou, _ in traces]

    if traces and cite:
        rep.add(OK, "Mesocentre cite dans les remerciements",
                "calcul distant trace dans " + ", ".join(traces_txt[:3]))
    elif faibles and not fortes and not cite:
        rep.add(WARN, "Vocabulaire de calcul distant, sans trace d'execution",
                "Mentionne sans numero de job, chemin distant ni option de "
                "soumission : " + " ; ".join(faibles[:3]) + "\n"
                "Probablement une phrase QUI PARLE de calcul distant plutot qu'un "
                "calcul qui a tourne\n(un cahier de laboratoire parle de ses "
                "outils). Verifier la ligne : si un calcul a bien eu lieu pour ce "
                "manuscrit, remercier le mesocentre.")
    elif fortes and not cite:
        rep.add(FAIL, "Mesocentre utilise mais non remercie",
                "Trace d'un calcul distant : " + " ; ".join(fortes[:3]) + "\n"
                "Ajouter aux remerciements, en anglais et dans la version francaise :\n"
                f"  {MESO_PHRASE}\n"
                "Si le calcul cite n'a rien a voir avec ce manuscrit, ignorer ce point "
                "et le dire dans le cahier plutot que de le laisser revenir a chaque "
                "pre-vol.")
    elif cite and not traces:
        rep.add(WARN, "Mesocentre remercie sans trace de calcul distant",
                "Le manuscrit remercie le mesocentre, mais ni le cahier ni l'etat "
                "n'en gardent trace. Verifier que le calcul a bien eu lieu pour CE "
                "manuscrit : un remerciement recopie d'un article precedent est une "
                "affirmation fausse comme une autre.")
    else:
        rep.add(OK, "Pas de remerciement mesocentre attendu",
                "aucun calcul distant trace dans la memoire du projet")


def check_tbannotator_credit(root: Path, art: Path, rep: Report) -> None:
    """Senelle ET Lecarpentier sont-ils credites quand TBannotator/tblearn a servi ?

    Symetrique de check_acknowledgements, avec une nuance : le credit est du a
    DEUX personnes (Gaetan Senelle, auteur d'origine ; Clement Lecarpentier,
    developpement et maintenance actuels), et l'une sans l'autre reste
    incomplet -- pas de citation partielle qui vaille.
    """
    tex = _norm(resolve_inputs(art / "main.tex"))
    presents = [nom for nom in TBANNO_MARQUEURS_NOMS if nom in tex]
    cite = len(presents) == len(TBANNO_MARQUEURS_NOMS)
    manquants = [nom for nom in TBANNO_MARQUEURS_NOMS if nom not in presents]
    traces = tbanno_traces(root)

    fortes = [ou for ou, forte in traces if forte]
    faibles = [ou for ou, forte in traces if not forte]
    traces_txt = [ou for ou, _ in traces]

    if traces and cite:
        rep.add(OK, "Senelle et Lecarpentier credites pour TBannotator/tblearn",
                "usage trace dans " + ", ".join(traces_txt[:3]))
    elif faibles and not fortes and not cite:
        rep.add(WARN, "Vocabulaire TBannotator/tblearn, sans trace d'usage reel",
                "Mentionne sans requete ni appel d'outil identifiable : "
                + " ; ".join(faibles[:3]) + "\n"
                "Probablement une phrase QUI PARLE de l'outil plutot qu'un usage "
                "reel. Verifier la ligne : si l'outil a bien servi pour ce "
                "manuscrit, crediter Senelle et Lecarpentier.")
    elif fortes and not cite:
        qui = " et ".join(m.capitalize() for m in manquants)
        rep.add(FAIL, "TBannotator/tblearn utilise mais credit incomplet ou absent",
                "Trace d'un usage reel : " + " ; ".join(fortes[:3]) + "\n"
                f"Manque : {qui}. Les deux sont dus, l'un sans l'autre ne suffit pas "
                "(auteur d'origine du pipeline, puis developpement et maintenance "
                "actuels).\n"
                "Ajouter aux remerciements :\n"
                f"  {TBANNO_PHRASE}\n"
                "Si l'usage cite n'a rien a voir avec ce manuscrit, ignorer ce point "
                "et le dire dans le cahier plutot que de le laisser revenir a chaque "
                "pre-vol.")
    elif cite and not traces:
        rep.add(WARN, "Senelle/Lecarpentier credites sans trace d'usage TBannotator",
                "Le manuscrit les remercie, mais ni le cahier ni l'etat n'en gardent "
                "trace d'un usage de TBannotator/tblearn. Verifier que l'outil a bien "
                "servi pour CE manuscrit : un remerciement recopie d'un article "
                "precedent est une affirmation fausse comme une autre.")
    else:
        rep.add(OK, "Pas de credit TBannotator/tblearn attendu",
                "aucun usage trace dans la memoire du projet")


def check_affiliation(art: Path, rep: Report) -> None:
    """La signature scientifique est-elle celle qu'impose l'universite ?

    Forme imposee depuis janvier 2025, rappelee cinq fois par la direction de
    l'institut : l'universite en toutes lettres d'abord, les etablissements-
    composantes dans l'ordre d'apparition des auteurs, puis CNRS, puis l'institut,
    puis `F-code postal Ville, France`. Le sigle UMLP y est proscrit, et les noms
    d'avant 2025 (Universite de Franche-Comte, Bourgogne-Franche-Comte) font
    perdre les publications dans les bases bibliometriques.
    """
    brut = resolve_inputs(art / "main.tex")
    tex = _norm(brut)
    if "femto" not in tex and "marie et louis pasteur" not in tex:
        rep.add(WARN, "Affiliation non reconnue",
                "Ni FEMTO-ST ni l'universite ne sont nommes : manuscrit ou l'auteur "
                "signe ailleurs, ou affiliation a verifier a la main.")
        return

    fautes = [msg for motif, msg in AFFIL_PROSCRITES.items() if motif in tex]
    if re.search(r"\bUMLP\b", brut):
        fautes.append("sigle « UMLP » : proscrit dans une signature de publication, "
                      "le nom se donne en toutes lettres")

    manquants = []
    if "marie et louis pasteur" not in tex:
        manquants.append("« Université Marie et Louis Pasteur » en toutes lettres")
    if "cnrs" not in tex:
        manquants.append("CNRS")
    if "femto" not in tex:
        manquants.append("l'institut FEMTO-ST")
    if not re.search(r"\bf-?\s?\d{5}\b", tex):
        manquants.append("le « F-code postal Ville » (ex. F-25000 Besançon, "
                         "F-90000 Belfort)")

    if fautes:
        rep.add(FAIL, "Signature scientifique polluee par une forme proscrite",
                "\n".join("  - " + f for f in fautes) + "\n"
                f"Generateur officiel : {AFFIL_GENERATEUR}")
    elif "marie et louis pasteur" not in tex:
        rep.add(FAIL, "Signature scientifique non conforme",
                "Il manque : " + " ; ".join(manquants) + "\n" + AFFIL_FORME + "\n"
                f"Generateur officiel : {AFFIL_GENERATEUR}")
    elif manquants:
        rep.add(WARN, "Signature scientifique incomplete",
                "Il manque : " + " ; ".join(manquants) + "\n" + AFFIL_FORME + "\n"
                f"Generateur officiel : {AFFIL_GENERATEUR}")
    else:
        rep.add(OK, "Signature scientifique conforme",
                "universite en toutes lettres, CNRS, institut et code postal "
                "presents, aucune forme proscrite. Le generateur tranche les cas "
                "a plusieurs etablissements-composantes.")


def check_links(art: Path, rep: Report, timeout: float = 8.0) -> None:
    r"""Les URL et les routes que le manuscrit promet repondent-elles encore ?

    Un manuscrit est fige, la ressource qu'il annonce continue de bouger. Un
    relecteur qui suit un lien mort en tire une conclusion sur le soin apporte au
    travail, et il a raison. Ce controle existe parce que le cas s'est produit :
    le 2026-09-12, `annotation_mtbc` etait pret a etre re-depose chez Molecular
    Microbiology en promettant un « companion JSON endpoint (/api/genes) », qui
    rendait 404 en production.

    Le mecanisme merite d'etre lu, car c'est le pire de sa famille et il explique
    la forme de ce controle. La route n'avait PAS ete renommee : elle est toujours
    declaree dans le code (`site/backend/app.py`), et elle rend 200 en local. Ce
    qui l'a tuee est la bascule du conteneur FastAPI vers un site statique, le
    2026-09-06, dont le generateur ne gelait que l'API versionnee `/api/v1`. Une
    URL exacte a la redaction, servie par un code inchange, publiee morte, en
    silence, pendant six jours. Aucun controle du depot ne la regardait : le
    temoin de publication du projet verifie le CONTENU servi, jamais la survie des
    adresses citees ailleurs -- manuscrit, skills partages, README. D'ou la regle :
    un lien ne se verifie qu'en le demandant a la production, jamais en le
    relisant, et jamais depuis la machine qui heberge le code.

    Deux familles sont testees. Les URL absolues de \url{} et \href{}, et --
    c'est la seule facon d'attraper le cas ci-dessus -- les ROUTES relatives
    citees en \texttt{/...}, resolues contre chaque domaine racine que le
    manuscrit cite par ailleurs. Une route citee sans domaine n'est verifiable
    que comme cela, et c'est precisement la forme qu'un article donne a l'API
    qu'il publie.
    """
    import urllib.error  # noqa: PLC0415
    import urllib.request  # noqa: PLC0415

    tex = resolve_inputs(art / "main.tex")
    absolues = set(re.findall(r"\\(?:url|href)\s*\{\s*(https?://[^}\s]+?)\s*\}", tex))
    absolues |= set(re.findall(r"\\texttt\s*\{\s*(https?://[^}\s]+?)\s*\}", tex))
    absolues = {u.rstrip(".,;") for u in absolues}

    # Racines citees : seulement les domaines que le manuscrit cite NUS (chemin
    # vide ou « / »), c'est-a-dire le domaine de la ressource elle-meme. Croiser
    # les routes avec tous les domaines cites fabrique du bruit qui noie le vrai
    # signal : doi.org/api/genes et w3id.org/genes rendent 404 sans rien dire du
    # manuscrit. Un resolveur d'identifiants n'est jamais cite nu, il porte
    # toujours un chemin, donc cette regle suffit et la liste ci-dessous n'est
    # qu'une ceinture de securite.
    RESOLVEURS = ("doi.org", "w3id.org", "handle.net", "orcid.org", "purl.org",
                  "n2t.net", "identifiers.org", "arxiv.org", "biorxiv.org")
    racines = {m.group(1) for u in absolues
               if (m := re.fullmatch(r"(https?://[^/]+)/?", u))
               and not any(h in m.group(1) for h in RESOLVEURS)}
    routes = {r.rstrip(".,;") for r in
              re.findall(r"\\texttt\s*\{\s*(/[A-Za-z0-9_./<>-]{2,})\s*\}", tex)}
    # Une route a placeholder (/gene/<Rv>) n'est pas testable telle quelle.
    routes = {r for r in routes if "<" not in r and ">" not in r}

    cibles = sorted(absolues) + sorted(
        f"{racine}{route}" for racine in sorted(racines) for route in sorted(routes))
    if not cibles:
        rep.add(OK, "Aucun lien a verifier", "le manuscrit ne cite aucune URL")
        return

    morts, injoignables, vivants = [], [], 0
    for url in cibles[:40]:
        req = urllib.request.Request(url, method="HEAD",
                                     headers={"User-Agent": "preflight/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                code = r.status
        except urllib.error.HTTPError as e:
            code = e.code
        except Exception as e:  # reseau coupe, DNS, TLS, timeout  # noqa: BLE001
            injoignables.append(f"{url} ({type(e).__name__})")
            continue
        if code >= 400:
            morts.append(f"{url} -> HTTP {code}")
        else:
            vivants += 1

    # Un DOI reserve mais non publie rend 404, et c'est une pratique DELIBEREE
    # (reserver a la soumission, publier au camera-ready). Le distinguer d'un lien
    # casse, sans quoi ce controle crie au loup sur tout manuscrit qui suit cette
    # pratique : constate sur mtbc/clos_soumis/Rv1125 le 2026-09-12, dont le cahier dit
    # explicitement « publication du depot Zenodo a l'acceptation ».
    reserves = [m for m in morts if "doi.org/" in m]
    morts = [m for m in morts if m not in reserves]
    if reserves:
        rep.add(WARN, "DOI non resolu, probablement reserve et non publie",
                "\n".join(reserves[:6]) + "\n"
                "Un DOI reserve rend 404 jusqu'a la publication du depot : c'est la "
                "pratique normale\n(reserver a la soumission, publier au "
                "camera-ready), et le cahier du projet doit le dire.\n"
                "Mais le relecteur, lui, suit le lien et voit un 404. Deux issues "
                "tenables : publier le\ndepot maintenant, ou ecrire dans le "
                "manuscrit que le DOI sera actif a la publication.\n"
                "Verifier aussi qu'il ne s'agit pas d'un DOI simplement faux.")
    if morts:
        rep.add(FAIL, "Lien(s) mort(s) dans le manuscrit",
                "\n".join(morts[:10]) + "\n"
                "Un relecteur suivra ces liens.\n"
                "Avant de corriger le MANUSCRIT, verifier ce qui est publie : une "
                "route peut etre\nintacte dans le code et morte en production "
                "(alias non gele par un build statique,\nregle de reecriture "
                "perdue, redirection oubliee). Reparer la PUBLICATION vaut alors "
                "mieux\nque retoucher un manuscrit deja soumis. Les routes "
                "relatives sont testees contre les\ndomaines que le manuscrit "
                "cite nus.")
    elif injoignables and not vivants:
        rep.add(WARN, "Liens non verifies (reseau)",
                f"{len(injoignables)} cible(s) injoignable(s), aucune atteinte : "
                "probablement pas de reseau ici.\n" + "\n".join(injoignables[:4]))
    elif vivants:
        detail = f"{vivants}/{len(cibles[:40])} cible(s) repondent"
        if reserves:
            detail += f", {len(reserves)} DOI non resolu(s), signale(s) a part"
        if injoignables:
            detail += f", {len(injoignables)} injoignable(s) : " + \
                      "; ".join(injoignables[:3])
        rep.add(OK, "Liens du manuscrit vivants", detail)


def check_figures(art: Path, rep: Report) -> None:
    tex = resolve_inputs(art / "main.tex")
    refs = re.findall(r"\\includegraphics\s*(?:\[[^\]]*\])?\s*\{([^}]+)\}", tex)
    if not refs:
        # Une figure dessinee en TikZ n'a pas de fichier a inclure, et un controle
        # qui ne cherche que \includegraphics declare alors sans figure un
        # manuscrit qui en porte deux (constate sur mtbc/clos_soumis/Rv2438A le
        # 2026-09-12, ou la figure reclamee par les deux relecteurs etait en
        # TikZ natif). Compter les environnements avant de conclure.
        env = re.findall(r"\\begin\{figure\*?\}", tex)
        tikz = re.findall(r"\\begin\{tikzpicture\}", tex)
        if env:
            rep.add(OK, "Figures presentes, dessinees dans le source",
                    f"{len(env)} environnement(s) figure, {len(tikz)} tikzpicture, "
                    "aucun fichier externe a televerser separement.\n"
                    "Verifier que le portail accepte des figures integrees au PDF, "
                    "ou exporter chaque figure a part si des fichiers sont exiges.")
            return
        rep.add(WARN, "Aucune figure detectee",
                "ni \\includegraphics ni environnement figure")
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
    # Ne compter que ce qu'on televerse : un .tex compile laisse .aux, .log, .out,
    # .bbl, .blg a cote de son .pdf, et un decompte naif annonce quatorze
    # supplementary pour un seul document (constate sur mtbc/clos_soumis/Rv2438A).
    d = art / "supplementary_materials"
    tex = resolve_inputs(art / "main.tex")
    cited = set(re.findall(
        r"(?:Table|Tableau|Fig(?:ure)?\.?|Data|Dataset|File|Text|Texte|Note|"
        r"Method(?:s)?|Method(?:e|es)?|Material(?:s)?|Appendix|Annexe)"
        r"\s*~?\s*S\s?(\d+)", tex))
    cited |= set(re.findall(r"\\ref\{(?:supp|sm|si|s)[:_-][^}]+\}", tex, flags=re.I))
    mentions = len(re.findall(r"[Ss]upplementar", tex))
    if not d.exists():
        if cited or mentions:
            rep.add(WARN, "Supplementary cites mais repertoire absent",
                    f"{len(cited)} elements numerotes et {mentions} mentions du mot, "
                    f"{d} introuvable")
        return
    JETABLES = {".aux", ".log", ".out", ".bbl", ".blg", ".toc", ".synctex",
                ".fls", ".fdb_latexmk", ".nav", ".snm", ".lof", ".lot"}
    files = [p for p in d.rglob("*")
             if p.is_file() and p.suffix.lower() not in JETABLES]
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


def check_registry(project: str, journal: str | None, rep: Report,
                   root: Path | None = None) -> None:
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
        # La regle de variation sert a CHOISIR une revue. Sur une resoumission elle
        # n'a rien a arbitrer : le dossier est deja ouvert chez cette revue, et son
        # verdict y devient trompeur -- il opposait un REFUS a Rv1125 le 2026-09-12
        # au motif qu'un autre manuscrit etait en evaluation chez Molecular
        # Microbiology, alors que Rv1125 y etait deja soumis et renvoye en brouillon.
        rev = resoumission(root, journal) if root is not None else None
        try:
            out = subprocess.run([sys.executable, str(script), "variety", journal],
                                 capture_output=True, text=True, timeout=30)
            if rev:
                rep.add(OK, f"Regle de variation sans objet ({journal})",
                        "resoumission chez une revue qui detient deja ce dossier "
                        f"({rev.get('manuscript_id') or 'sans id'}) : il n'y a pas "
                        "de cible a choisir.\nVerdict informatif, non bloquant :\n"
                        + out.stdout.strip())
            else:
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
    p.add_argument("--no-compile", action="store_true", dest="no_compile",
                   help="ne pas recompiler les deux versions (iteration rapide) ; "
                        "le pre-vol perd alors sa garantie principale")
    p.add_argument("--vitrine-empreinte", metavar="MAIN_TEX", dest="empreinte_de",
                   help="afficher la somme de controle du titre et du resume d'un "
                        "main.tex, a recopier dans cadrage_editorial.md, puis sortir")
    p.add_argument("--no-net", action="store_true", dest="no_net",
                   help="ne pas tester les liens cites par le manuscrit "
                        "(hors ligne, ou iteration rapide)")
    p.add_argument("--subdir", default="article",
                   help="nom du sous-repertoire article a auditer, pour un projet "
                        "portant plusieurs manuscrits (ex. article2 pour un second papier)")
    args = p.parse_args()

    if args.empreinte_de:
        tex = Path(args.empreinte_de).resolve()
        if not tex.exists():
            print(f"introuvable : {tex}", file=sys.stderr)
            return 1
        titre, resume = vitrine(tex.parent, tex.name)
        print(f"empreinte {vitrine_empreinte(tex.parent, tex.name)}")
        print(f"titre  ({len(titre.split())} mots) : {titre}")
        print(f"resume ({len(resume.split())} mots) : {resume[:120]}...")
        return 0

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
    check_verdict(root, art, args.journal, rep)
    check_cadrage(root, art, args.journal, rep)
    check_build(art, rep)
    if args.no_compile:
        rep.add(WARN, "Compilation reelle non verifiee",
                "--no-compile : ni main.tex ni main_fr.tex n'ont ete recompiles. "
                "Ne pas soumettre sur cette base.")
    else:
        check_compilation(art, rep)
    check_french(art, rep)
    check_preamble_parity(art, rep)
    check_length(art, rep, target, abstract_max)
    check_ai_declaration(art, rep)
    check_acknowledgements(root, art, rep)
    check_tbannotator_credit(root, art, rep)
    check_affiliation(art, rep)
    check_figures(art, rep)
    if not args.no_net:
        check_links(art, rep)
    check_supplementary(art, rep)
    check_git(art, rep)
    check_registry(root.name, args.journal, rep, root)
    if not args.journal:
        rep.add(WARN, "Aucune revue cible passee",
                "Sans --journal, ni les limites de longueur ni la regle de variation "
                "ne sont evaluees.\nRelancer avec --journal <cle> une fois la cible "
                "choisie (journals.py match pour la trouver).")
    return rep.render()


if __name__ == "__main__":
    sys.exit(main())
