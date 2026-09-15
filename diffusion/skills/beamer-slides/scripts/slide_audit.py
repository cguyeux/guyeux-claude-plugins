#!/usr/bin/env python3
"""Audit mecanique d'un deck Beamer.

Ne juge pas le fond : il mesure ce qu'une relecture lineaire ne voit pas.
Six controles, chacun calibre sur des defauts REELS mesures dans les decks
du parc (voir --pourquoi).

    python3 slide_audit.py deck.tex [--duree 20] [--json] [--pourquoi]

Sortie : rapport texte, ou JSON avec --json. Code de sortie 1 s'il reste un
FAIL, 0 sinon (utilisable en garde-fou).

Aucune dependance obligatoire. Pillow, s'il est present, active le controle
d'encre dans les marges (--pixels).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import unicodedata
from dataclasses import dataclass, field, asdict

# ---------------------------------------------------------------- seuils
# Tires du diagnostic du 2026-09-09 sur neuf decks du parc. Les changer
# demande une mesure, pas une intuition.
MOTS_WARN = 40           # au-dela, la slide se lit au lieu de s'ecouter
MOTS_FAIL = 60
KB_MOTS_MAX = 25         # au-dela, un take-away est un paragraphe
SANS_VISUEL_MAX = 0.30   # part maximale de slides sans objet visuel
MONOTONIE_MAX = 0.60     # part maximale de slides de meme signature
SUITE_MEME_TYPE_MAX = 3  # slides consecutives de meme type
TIKZ_MOTS_NOEUD = 6     # au-dela : c'est une phrase, pas un label

POURQUOI = """\
Calibration des seuils (mesures du 2026-09-09, parc de neuf decks) :

  reduction de police  431 occurrences / 75 frames  (audition PR)
                       311 / 96                     (seminaire Musee de l'Homme)
                        95 / 22                     (candidature PR)
      -> On retrecit la police pour faire tenir, au lieu de couper. Tout
         \\footnotesize, \\scriptsize ou \\tiny dans un corps de frame est
         donc un FAIL, sauf dans une source, une note ou un pied de tableau.

  graphiques de donnees  0 sur huit decks sur neuf
      -> Des arguments quantitatifs, jamais montres comme donnees. D'ou le
         seuil sur la part de slides sans objet visuel.

  Overfull \\vbox       17, 5 et 3 dans les logs, jamais relus
      -> Le debordement est SILENCIEUX : du contenu absorbe sous le bas de
         frame ressemble a une slide simplement courte. Controle mecanique
         obligatoire, jamais visuel seul.

  TikZ decoratif       « La cle : deux echelles emboitees » (L5L6) : deux
                       rectangles arrondis contenant des phrases, sur la
                       moitie de la slide, pour zero information de plus
                       qu'une puce.
      -> Une figure TikZ sans axe, sans echelle et sans donnee, dont les
         noeuds portent des phrases, est une puce deguisee en schema.
"""

# ------------------------------------------------- normalisation (fig-check 4.2)
def normalize(s: str) -> str:
    """Normalise source LaTeX et texte rendu de la MEME facon.

    Reprise verbatim de fig-check phase 4.2, avec les pieges deja payes :
    apostrophes typographiques substituees a la compilation, commandes qui
    RENDENT un caractere (\\S -> §) au lieu de disparaitre, et commandes
    d'un seul caractere non alphabetique (\\_ dans un \\texttt) que la regex
    generale ne matche pas.
    """
    # Accents LaTeX : \'e, \`a, \^i, \"u, \~n, \c{c}... Ce sont des commandes
    # d'UN caractere NON alphabetique, donc la regex generale \\[a-zA-Z]+ ne
    # les voit pas : cote source il reste « 'e », cote PDF il y a « e », et
    # toute phrase accentuee remonte a tort comme TRONQUEE (mesure : 2 des 3
    # sondes de la demo, 2026-09-09). On efface la commande d'accent en
    # gardant la lettre, puis on compare sans diacritiques des deux cotes.
    s = re.sub(r"\\([`'^\"~=.])\{?([a-zA-Z])\}?", r'\2', s)
    s = re.sub(r'\\([cuvHkrbd])\{([a-zA-Z])\}', r'\2', s)
    # Commandes NON TEXTUELLES a effacer AVEC leur argument : sinon la regex
    # generale mange la commande et laisse l'argument, et « \vspace{6pt} »
    # depose « 6pt » au milieu de la phrase (mesure sur L5L6, 2026-09-09).
    s = re.sub(r'\\(?:vspace|hspace|vskip|hskip|kern|label|ref|cref|input|'
               r'includegraphics|definecolor|setlength|addtolength|color|begin|end|'
               r'colorbox|graphicspath|hfill|vfill|centering|par|noindent)'
               r'\*?(\[[^\]]*\])?(\{[^{}]*\})?(\{[^{}]*\})?', ' ', s)
    s = re.sub(r'\\([_%&#$])', r'\1', s)
    s = re.sub(r'\\[a-zA-Z]+\*?\s*(\[[^\]]*\])?\{?', ' ', s)
    s = s.replace('{', '').replace('}', '')
    s = s.replace('~', ' ').replace('\\', ' ').replace('$', ' ')
    s = s.replace('\u2019', "'").replace('\u2018', "'")
    s = s.replace('\u00a0', ' ').replace('\u202f', ' ')
    for ch in '§¶£†‡©°':
        s = s.replace(ch, ' ')
    # Comparaison insensible aux diacritiques : le PDF porte « é », la source
    # normalisee porte « e ». Sans cela la sonde ne se retrouve jamais.
    s = ''.join(c for c in unicodedata.normalize('NFKD', s)
                if not unicodedata.combining(c))
    s = re.sub(r'\s+', ' ', s).strip()
    # Dimensions isolees laissees par une commande de mise en page mal fermee
    s = re.sub(r'\b\d+(?:\.\d+)?(?:pt|mm|cm|em|ex|in|sp|bp|dd)\b', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def compact(s: str) -> str:
    """Forme insensible aux espaces, tirets et ponctuation.

    Seconde chance pour la sonde de troncature : le PDF CESURE (babel french
    coupe les mots en fin de ligne) et `pdftotext -layout` insere des espaces
    de colonne. Une sonde qui echoue sur la forme normale mais reussit ici
    n'est pas une troncature, c'est une coupure de ligne.
    """
    return re.sub(r'[^a-z0-9]', '', s.lower())


def strip_comments(tex: str) -> str:
    return re.sub(r'(?<!\\)%.*', '', tex)


# ---------------------------------------------------------------- modele
@dataclass
class Issue:
    niveau: str          # FAIL | WARN | INFO
    code: str
    message: str


@dataclass
class Slide:
    num: int
    titre: str
    corps: str
    ligne: int
    issues: list = field(default_factory=list)
    mots: int = 0
    signature: str = ""
    visuel: str = "aucun"
    nature: str = "corps"
    source: str = ""

    def add(self, niveau, code, message):
        self.issues.append(Issue(niveau, code, message))


# ------------------------------------------------------------- fragments
# Un expose se decline : version courte et version longue, francais et anglais.
# Deux repertoires copies divergent des la premiere correction de chiffre, donc
# les variantes partagent leurs fragments par \input. Sans les suivre, l'audit
# ne voit AUCUNE frame dans le maitre et rend un feu vert entierement faux :
# mesure le 2026-09-10, << 0 FAIL, 0 WARN >> sur un deck de 7 pages.
_INPUT = re.compile(r'\\(?:input|include)(?![a-zA-Z])\s*(?:\{\s*([^}]*?)\s*\}|([^\s%{}\\,]+))')


def _resoud(nom: str, base_dir: str):
    for cand in (nom, nom + '.tex'):
        chemin = os.path.join(base_dir, cand)
        if os.path.isfile(chemin):
            return os.path.abspath(chemin)
    return None


def aplatis(tex_path: str, base_dir: str = None, _pile=None):
    """Rend (texte, origines, manquants) pour un deck eventuellement fragmente.

    origines[i] = (fichier, ligne) pour la ligne i (0-based) du texte aplati :
    c'est ce qui permet de rendre un << corps.tex:37 >> actionnable plutot
    qu'un numero de ligne du texte reconstitue, qui ne designe rien.
    """
    tex_path = os.path.abspath(tex_path)
    base_dir = base_dir or os.path.dirname(tex_path)
    _pile = list(_pile or [])
    if tex_path in _pile:                      # \input circulaire
        return "", [], []
    _pile.append(tex_path)
    brut = open(tex_path, encoding='utf-8', errors='replace').read()
    lignes = strip_comments(brut).split('\n')
    out, origines, manquants = [], [], []
    for n, ligne in enumerate(lignes, 1):
        m = _INPUT.search(ligne)
        nom = ((m.group(1) or m.group(2)) or '').strip() if m else ''
        cible = _resoud(nom, base_dir) if nom else None
        if cible:
            avant = ligne[:m.start()].strip()
            if avant:
                out.append(avant)
                origines.append((tex_path, n))
            sous_t, sous_o, sous_m = aplatis(cible, base_dir, _pile)
            if sous_t:
                out += sous_t.split('\n')
                origines += sous_o
            manquants += sous_m
            apres = ligne[m.end():].strip()
            if apres:
                out.append(apres)
                origines.append((tex_path, n))
        else:
            if nom and not nom.lower().endswith(('.sty', '.cfg', '.cls', '.def')) \
                    and not nom.startswith(('/', '\\')):
                manquants.append((os.path.basename(tex_path), n, nom))
            out.append(ligne)
            origines.append((tex_path, n))
    return '\n'.join(out), origines, manquants


def _fichier_du_log(log: str, pos: int, fragments, maitre: str) -> str:
    """Dernier fragment CONNU ouvert dans le log avant pos.

    TeX rapporte << detected at line N >> en lignes du fichier qu'il lit, donc
    du fragment, pas du maitre : mesure le 2026-09-10. On ne cherche que les
    noms de nos propres fragments, ce qui evite le parseur de parentheses de
    log, notoirement fragile des qu'un message contient une parenthese.
    """
    best, bestpos, amont = maitre, -1, log[:pos]
    for f in fragments:
        for m in re.finditer(r'\(\.?[/\\]?' + re.escape(os.path.basename(f)), amont):
            if m.start() > bestpos:
                bestpos, best = m.start(), f
    return best


# ---------------------------------------------------------------- parsing
# sliderupture (theme guyeux) enveloppe une frame : sans cela le deck compte
# une slide de moins et les ratios sont faux.
FRAME_OPEN = re.compile(r'\\begin\{(?:frame|sliderupture)\}')
FRAME_CLOSE = re.compile(r'\\end\{(?:frame|sliderupture)\}')


def decoupe_frames(tex: str):
    """Rend (titre, corps, ligne) pour chaque frame, y compris imbriquees
    dans un environnement maison (sliderupture)."""
    out = []
    pos = 0
    while True:
        m = FRAME_OPEN.search(tex, pos)
        if not m:
            break
        depth, i = 1, m.end()
        while depth and i < len(tex):
            o = FRAME_OPEN.search(tex, i)
            c = FRAME_CLOSE.search(tex, i)
            if not c:
                break
            if o and o.start() < c.start():
                depth += 1
                i = o.end()
            else:
                depth -= 1
                i = c.end()
        fin_tag = re.search(r'\\end\{(frame|sliderupture)\}\s*$', tex[m.end():i])
        bloc = tex[m.end():i - (len(fin_tag.group(0)) if fin_tag else 11)]
        ligne = tex[:m.start()].count('\n') + 1
        # titre : \begin{frame}[opts]{titre} ou \frametitle{titre}
        titre = ""
        reste = bloc
        mo = re.match(r'\s*(\[[^\]]*\])?\s*\{', bloc)
        if mo:
            depth2, j = 1, mo.end()
            while depth2 and j < len(bloc):
                if bloc[j] == '{':
                    depth2 += 1
                elif bloc[j] == '}':
                    depth2 -= 1
                j += 1
            titre = bloc[mo.end():j - 1]
            reste = bloc[j:]
        else:
            mt = re.search(r'\\frametitle\{', bloc)
            if mt:
                depth2, j = 1, mt.end()
                while depth2 and j < len(bloc):
                    if bloc[j] == '{':
                        depth2 += 1
                    elif bloc[j] == '}':
                        depth2 -= 1
                    j += 1
                titre = bloc[mt.end():j - 1]
        ligne_fin = tex[:i].count('\n') + 1
        out.append((m.group(0)[7:-1], titre, reste, ligne, m.start(), ligne_fin))
        pos = i
    return out


def arg_brace(txt: str, start: int):
    """Contenu de l'accolade ouvrante en position start."""
    depth, i = 1, start + 1
    while depth and i < len(txt):
        if txt[i] == '{' and txt[i - 1] != '\\':
            depth += 1
        elif txt[i] == '}' and txt[i - 1] != '\\':
            depth -= 1
        i += 1
    return txt[start + 1:i - 1], i


def noeuds_tikz(t: str):
    """Textes des noeuds d'un tikzpicture, accolades imbriquees comprises.

    `[^{}]*` echoue des qu'un noeud contient \\textbf{...}, ce qui est le cas
    general : sans appariement reel, la detection ne voit aucun noeud.
    """
    out = []
    for m in re.finditer(r'\\node\b', t):
        i = t.find('{', m.end())
        fin_instr = t.find(';', m.end())
        if i < 0 or (fin_instr >= 0 and i > fin_instr):
            continue
        txt, _ = arg_brace(t, i)
        out.append(txt)
    return out


def blocs_de_texte(corps: str):
    """Fragments de texte assez longs pour porter une sonde de troncature."""
    frags = []
    for m in re.finditer(r'\\item\b', corps):
        seg = corps[m.end():]
        fin = re.search(r'\\item\b|\\end\{', seg)
        frags.append(seg[:fin.start()] if fin else seg)
    for cmd in (r'\\kb', r'\\cle', r'\\lecture'):
        for m in re.finditer(cmd + r'(\[[^\]]*\])?\{', corps):
            frags.append(arg_brace(corps, corps.index('{', m.end() - 1))[0])
    sans_env = re.sub(r'\\begin\{(tikzpicture|tabular\*?|axis|columns)\}.*?\\end\{\1\}',
                      ' ', corps, flags=re.S)
    for para in re.split(r'\n\s*\n', sans_env):
        if len(normalize(para)) >= 60:
            frags.append(para)
    return [f for f in frags if len(normalize(f)) >= 45]


# ---------------------------------------------------------------- controles
SHRINK = re.compile(r'\\(footnotesize|scriptsize|tiny)\b')
# Tolerances : une source, une note, un pied de tableau, et surtout la taille
# d'une ETIQUETTE de schema (`font=\scriptsize` dans des options TikZ), qui
# n'est pas un retrecissement pour faire tenir mais une hierarchie voulue.
SHRINK_TOLERE = re.compile(r'\\(src|footnote|caption|thanks)\b|%\s*shrink-ok')
SHRINK_ETIQUETTE = re.compile(r'font\s*=\s*\\(footnotesize|scriptsize|tiny)\b')


def audit(tex_path: str, duree: float | None, faire_pixels: bool):
    tex_path = os.path.abspath(tex_path)
    base = os.path.splitext(tex_path)[0]
    src, origines, frag_manquants = aplatis(tex_path)
    fragments = sorted({f for f, _ in origines})

    def situe(lg: int):
        """(fichier, ligne) d'origine d'une ligne du texte aplati."""
        if not origines:
            return tex_path, lg
        return origines[max(0, min(len(origines) - 1, lg - 1))]

    rapport = {"deck": tex_path, "slides": [], "global": [], "compilation": {}}

    # -- 0. compilation ----------------------------------------------------
    log_path = base + '.log'
    pdf_path = base + '.pdf'
    if not os.path.exists(pdf_path) or os.path.getmtime(pdf_path) < os.path.getmtime(tex_path):
        subprocess.run(['pdflatex', '-interaction=nonstopmode', os.path.basename(tex_path)],
                       cwd=os.path.dirname(tex_path), capture_output=True)
        subprocess.run(['pdflatex', '-interaction=nonstopmode', os.path.basename(tex_path)],
                       cwd=os.path.dirname(tex_path), capture_output=True)
    log = open(log_path, encoding='utf-8', errors='replace').read() if os.path.exists(log_path) else ""
    erreurs = len(re.findall(r'^!', log, re.M))
    overfull = re.findall(r'Overfull \\vbox \(([\d.]+)pt too high\) detected at line (\d+)', log)
    rapport["compilation"] = {"erreurs": erreurs, "overfull": len(overfull),
                              "pdf": os.path.exists(pdf_path)}
    if erreurs:
        rapport["global"].append(asdict(Issue("FAIL", "C1", f"{erreurs} erreur(s) de compilation")))
    hbox = re.findall(r'Overfull \\hbox \(([\d.]+)pt too wide\) in paragraph at lines (\d+)', log)
    for pts, ligne in hbox:
        if float(pts) > 5:
            rapport["global"].append(asdict(Issue(
                "WARN", "C3",
                f"Overfull \\hbox de {pts} pt ligne {ligne} : du texte sort de la marge "
                f"droite, typiquement un identifiant ou un chemin insecable")))
    # Les Overfull sont rattaches a LEUR slide plus bas : un numero de ligne
    # de log n'est pas actionnable, un numero de slide l'est.
    overfull_restants = list(overfull)
    # En deck fragmente, la ligne du log est celle du FRAGMENT : sans cette
    # carte, tous les Overfull tomberaient << hors de toute frame >>.
    fichier_overfull = {}
    if len(fragments) > 1:
        for m in re.finditer(r'Overfull \\vbox \(([\d.]+)pt too high\) detected at line (\d+)', log):
            fichier_overfull[(m.group(1), m.group(2))] = _fichier_du_log(
                log, m.start(), fragments, tex_path)

    # -- texte rendu -------------------------------------------------------
    pages = []
    n_pdf = 0
    if os.path.exists(pdf_path):
        for mode in ('-layout', '-raw'):
            out = subprocess.run(['pdftotext', mode, pdf_path, '-'],
                                 capture_output=True, text=True).stdout
            parts = out.split('\x0c')
            if mode == '-layout':
                n_pdf = len([x for x in parts if x.strip()])
            pages += [normalize(p) for p in parts]

    # -- par slide ---------------------------------------------------------
    frames = decoupe_frames(src)
    # Tout ce qui suit \appendix est du back-pocket : compte dans les
    # controles de debordement, jamais dans les ratios du corps.
    pos_appendix = src.find('\\appendix')
    sans_visuel = 0
    signatures = []
    corps_util = 0
    for n, (env, titre, corps, ligne, offset, ligne_fin) in enumerate(frames, 1):
        s = Slide(num=n, titre=normalize(titre), corps=corps, ligne=ligne)
        f_src, l_src = situe(ligne)
        _, l_src_fin = situe(ligne_fin)
        s.source = (f"{os.path.basename(f_src)}:{l_src}" if len(fragments) > 1
                    else f"ligne {l_src}")
        for pts, lg in list(overfull_restants):
            if (fichier_overfull.get((pts, lg), f_src) == f_src
                    and l_src <= int(lg) <= l_src_fin):
                s.add("FAIL", "C2",
                      f"Overfull \\vbox de {pts} pt (ligne {lg}) : du contenu deborde du "
                      f"cadre. Invisible a l'oeil : ce qui passe sous le bord ressemble a "
                      f"une slide simplement courte")
                overfull_restants.remove((pts, lg))
        # Nature de la slide : une page de titre, une rupture ou une annexe
        # n'a pas a porter un objet visuel ni a peser dans la monotonie.
        est_annexe = pos_appendix >= 0 and offset > pos_appendix
        if re.search(r'\\titlepage', corps):
            s.nature = "titre"
        elif est_annexe:
            s.nature = "annexe"
        elif env == 'sliderupture' or re.search(r'\[standout\]', corps[:40]):
            s.nature = "rupture"
        elif re.search(r'\\sectionpage|\\tableofcontents', corps):
            s.nature = "section"
        else:
            s.nature = "corps"

        # 1. troncature (fig-check 4.2)
        pages_compactes = [compact(p) for p in pages]
        for frag in blocs_de_texte(corps):
            norm = normalize(frag)
            queue = norm[-45:]
            trouve = any(queue in p for p in pages)
            if not trouve:
                qc = compact(norm)[-35:]
                trouve = any(qc in p for p in pages_compactes)
            if pages and not trouve:
                s.add("FAIL", "T1",
                      f"Texte absent du PDF rendu, donc tronque ou pousse hors cadre : "
                      f"...{queue[-40:]!r}")

        # 2. reduction de police
        corps_sans_tolere = SHRINK_ETIQUETTE.sub(' ', SHRINK_TOLERE.sub(' ', corps))
        nb_shrink = len(SHRINK.findall(corps_sans_tolere))
        if nb_shrink:
            s.add("FAIL", "D1",
                  f"{nb_shrink} reduction(s) de police dans le corps : on retrecit pour "
                  f"faire tenir au lieu de couper")

        # 3. densite
        txt = normalize(re.sub(r'\\begin\{(tikzpicture|axis)\}.*?\\end\{\1\}', ' ',
                               corps, flags=re.S))
        s.mots = len(txt.split())
        if s.mots > MOTS_FAIL:
            s.add("FAIL", "D2", f"{s.mots} mots portes par la slide (seuil {MOTS_FAIL})")
        elif s.mots > MOTS_WARN:
            s.add("WARN", "D2", f"{s.mots} mots portes par la slide (seuil {MOTS_WARN})")

        # 4. take-away trop long
        for m in re.finditer(r'\\kb(\[[^\]]*\])?\{', corps):
            contenu = arg_brace(corps, corps.index('{', m.end() - 1))[0]
            nm = len(normalize(contenu).split())
            if nm > KB_MOTS_MAX:
                s.add("WARN", "D3",
                      f"Take-away de {nm} mots : au-dela de {KB_MOTS_MAX} ce n'est plus "
                      f"une phrase a retenir, c'est un paragraphe")

        # 5. objet visuel / TikZ decoratif
        a_image = bool(re.search(r'\\includegraphics|\\slidefigure', corps))
        a_plot = bool(re.search(r'\\begin\{axis\}|addplot|\\begin\{tabular', corps))
        tikz = re.findall(r'\\begin\{tikzpicture\}(.*?)\\end\{tikzpicture\}', corps, re.S)
        a_tikz_utile = False
        for t in tikz:
            noeuds = noeuds_tikz(t)
            # Un noeud qui porte une PHRASE (plus de 6 mots) ou qui declare une
            # largeur de texte n'est pas un label : c'est un paragraphe dans un
            # rectangle. Calibre sur L5L6 slide 7, ou trois noeuds de 7 a 11
            # mots dessinent deux rectangles arrondis et rien d'autre.
            prose = [x for x in noeuds if len(normalize(x).split()) > TIKZ_MOTS_NOEUD]
            largeur = len(re.findall(r'text width\s*=', t))
            porte_donnee = bool(re.search(
                r'\\begin\{axis\}|addplot|datavisualization|pgfplots|'
                r'coordinate\s*\(|--\s*\(|\\pgfplotstable', t))
            if (len(prose) >= 2 or (prose and largeur)) and not porte_donnee:
                s.add("FAIL", "V1",
                      f"TikZ decoratif : {max(len(prose), largeur)} noeud(s) portant une "
                      f"phrase, sans axe ni echelle ni donnee. C'est une puce deguisee en "
                      f"schema, qui coute la place d'une figure pour l'information d'une ligne")
            else:
                a_tikz_utile = True
        if s.nature != "corps":
            s.visuel = s.nature
        elif a_image:
            s.visuel = "figure"
        elif a_plot:
            s.visuel = "donnees"
        elif tikz and a_tikz_utile:
            s.visuel = "schema"
        elif re.search(r'\\bigchiffre', corps) or \
                re.search(r'\\fontsize\{\s*([3-9]\d|2[4-9])', corps):
            s.visuel = "chiffre"
        else:
            s.visuel = "aucun"

        # 6. signature structurelle (monotonie)
        sig = []
        if re.search(r'\\begin\{itemize\}', corps):
            sig.append("liste")
        if a_image:
            sig.append("figure")
        if re.search(r'\\begin\{columns\}|\\slidecompare', corps):
            sig.append("colonnes")
        if re.search(r'\\kb\b', corps):
            sig.append("kb")
        if tikz:
            sig.append("tikz")
        s.signature = "+".join(sig) if sig else "texte"
        if s.nature == "corps":
            corps_util += 1
            if s.visuel == "aucun":
                sans_visuel += 1
            signatures.append(s.signature)
        rapport["slides"].append({k: v for k, v in asdict(s).items() if k != "corps"})

    # -- global ------------------------------------------------------------
    n = corps_util
    if n:
        part = sans_visuel / n
        if part > SANS_VISUEL_MAX:
            rapport["global"].append(asdict(Issue(
                "FAIL", "V2",
                f"{sans_visuel}/{n} slides de corps ({part:.0%}) sans aucun objet visuel "
                f"(seuil {SANS_VISUEL_MAX:.0%})")))
        from collections import Counter
        commune, freq = Counter(signatures).most_common(1)[0]
        if freq / n > MONOTONIE_MAX:
            rapport["global"].append(asdict(Issue(
                "WARN", "M1",
                f"{freq}/{n} slides ({freq/n:.0%}) partagent la signature « {commune} » : "
                f"le deck se repete, l'oeil decroche")))
        suite, courant, debut = 1, signatures[0], 1
        for i, sg in enumerate(signatures[1:], 2):
            if sg == courant:
                suite += 1
            else:
                if suite > SUITE_MEME_TYPE_MAX:
                    rapport["global"].append(asdict(Issue(
                        "WARN", "M2",
                        f"{suite} slides consecutives de type « {courant} » "
                        f"(slides {debut} a {i-1})")))
                suite, courant, debut = 1, sg, i
        if suite > SUITE_MEME_TYPE_MAX:
            rapport["global"].append(asdict(Issue(
                "WARN", "M2", f"{suite} slides consecutives de type « {courant} » "
                              f"(slides {debut} a {n})")))
        if duree:
            par_slide = duree / n
            if par_slide < 0.5:
                rapport["global"].append(asdict(Issue(
                    "FAIL", "R1",
                    f"{n} slides pour {duree:g} min, soit {par_slide*60:.0f} s par slide : "
                    f"le deck ne peut pas etre presente dans le temps imparti")))
            elif par_slide < 0.8:
                rapport["global"].append(asdict(Issue(
                    "WARN", "R1",
                    f"{n} slides pour {duree:g} min, soit {par_slide*60:.0f} s par slide")))

    # -- controle d'encre dans les marges (optionnel) -----------------------
    if faire_pixels and os.path.exists(pdf_path):
        try:
            rapport["global"] += controle_pixels(pdf_path)
        except Exception as e:              # Pillow absent, ou pdftoppm muet
            rapport["global"].append(asdict(Issue("INFO", "P0", f"controle pixels ignore : {e}")))

    for pts, lg in overfull_restants:
        rapport["global"].append(asdict(Issue(
            "FAIL", "C2", f"Overfull \\vbox de {pts} pt ligne {lg}, hors de toute frame "
                          f"(preambule, page de section ou annexe)")))
    # Garde-fou : un rapport vide sur un PDF plein est un feu vert faux, et
    # c'est le pire mode d'echec possible pour un outil de controle.
    if n_pdf and not frames:
        rapport["global"].append(asdict(Issue(
            "FAIL", "S0",
            f"aucune frame trouvee dans le source alors que le PDF en compte {n_pdf} : "
            f"fragments \\input non resolus, ou syntaxe de frame inattendue. Rien de ce "
            f"qui suit n'a de valeur tant que ce point n'est pas regle")))
    for fich, lg, nom in frag_manquants:
        rapport["global"].append(asdict(Issue(
            "WARN", "S1",
            f"{fich}:{lg} : fragment \\input{{{nom}}} introuvable, son contenu n'est pas "
            f"audite (le PDF, lui, peut tres bien le contenir)")))
    if len(fragments) > 1:
        noms = ", ".join(os.path.basename(f) for f in fragments)
        rapport["global"].append(asdict(Issue(
            "INFO", "S2", f"deck fragmente, {len(fragments)} fichiers audites : {noms}")))
    rapport["resume"] = {"slides": len(frames), "corps": corps_util,
                         "sans_visuel": sans_visuel, "fragments": len(fragments),
                         "pages_pdf": n_pdf}
    return rapport


def controle_pixels(pdf_path: str):
    """Encre dans la bande basse hors zone sure.

    Complement du controle de troncature : attrape ce qui deborde sans que
    LaTeX le signale (une image trop haute, un tikz qui sort du cadre).
    Le pied de page occupe legitimement cette bande : on calibre sur la
    MEDIANE des pages et on ne signale que les pages nettement au-dessus.
    """
    from PIL import Image
    import glob
    import tempfile
    issues = []
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(['pdftoppm', '-r', '80', '-png', pdf_path, os.path.join(td, 'p')],
                       capture_output=True)
        mesures = []
        for f in sorted(glob.glob(os.path.join(td, 'p-*.png'))):
            im = Image.open(f).convert('L')
            w, h = im.size
            # Une slide de rupture ou une page de titre en intensite affirmee est
            # un aplat : sa bande basse est encree par construction, et la
            # comparer aux slides sur fond clair la signale toujours a tort
            # (mesure : 4536 pixels contre 0 en mediane, demo du theme).
            total = im.getdata()
            sombres = sum(1 for px in total if px < 200)
            if sombres > 0.40 * w * h:
                continue
            bande = im.crop((0, int(h * 0.965), w, h))
            encre = sum(1 for px in bande.getdata() if px < 200)
            mesures.append((os.path.basename(f), encre))
        if not mesures:
            return issues
        vals = sorted(m[1] for m in mesures)
        mediane = vals[len(vals) // 2]
        seuil = max(mediane * 3, mediane + 400)
        for nom, encre in mesures:
            if encre > seuil:
                page = int(re.search(r'p-0*(\d+)', nom).group(1))
                issues.append(asdict(Issue(
                    "WARN", "P1",
                    f"page {page} : {encre} pixels d'encre dans la bande basse contre "
                    f"{mediane} en mediane, contenu probablement pousse sous le cadre")))
    return issues


def imprime(rapport):
    print(f"Deck : {rapport['deck']}")
    c = rapport["compilation"]
    print(f"Compilation : {c['erreurs']} erreur(s), {c['overfull']} Overfull, "
          f"PDF {'present' if c['pdf'] else 'ABSENT'}")
    print(f"Slides : {len(rapport['slides'])}\n")
    nf = nw = 0
    for s in rapport["slides"]:
        if not s["issues"]:
            continue
        situation = s.get('source') or f"ligne {s['ligne']}"
        print(f"  Slide {s['num']:>2} ({situation}) — {s['titre'][:64] or '(sans titre)'}")
        for i in s["issues"]:
            print(f"      [{i['niveau']}] {i['code']}  {i['message']}")
            nf += i["niveau"] == "FAIL"
            nw += i["niveau"] == "WARN"
        print()
    if rapport["global"]:
        print("  Deck entier")
        for i in rapport["global"]:
            print(f"      [{i['niveau']}] {i['code']}  {i['message']}")
            nf += i["niveau"] == "FAIL"
            nw += i["niveau"] == "WARN"
        print()
    r = rapport.get("resume", {})
    sansv, ncorps = r.get("sans_visuel", 0), r.get("corps", 0)
    print(f"Bilan : {nf} FAIL, {nw} WARN — {sansv}/{ncorps} slides de corps sans objet visuel")
    return nf


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("deck", nargs="?", help="fichier .tex du deck")
    ap.add_argument("--duree", type=float, help="duree de l'expose en minutes")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--pixels", action="store_true",
                    help="controle d'encre dans les marges (necessite Pillow)")
    ap.add_argument("--pourquoi", action="store_true",
                    help="d'ou viennent les seuils")
    a = ap.parse_args()
    if a.pourquoi:
        print(POURQUOI)
        return 0
    if not a.deck:
        ap.error("indiquer un deck .tex")
    r = audit(a.deck, a.duree, a.pixels)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 1 if any(i["niveau"] == "FAIL" for i in r["global"]) or \
                    any(i["niveau"] == "FAIL" for s in r["slides"] for i in s["issues"]) else 0
    return 1 if imprime(r) else 0


if __name__ == "__main__":
    sys.exit(main())
