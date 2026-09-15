#!/usr/bin/env python3
"""Detecteur mecanique de figures manquantes, orphelines et desequilibrees.

Ce que la lecture lineaire d'un manuscrit ne voit pas, et que ce script mesure :

1. FIGURES PENDANTES   : un \\ref{fig:x} sans \\label{fig:x} correspondant.
2. FIGURES ORPHELINES  : un fichier image produit, jamais inclus dans le manuscrit.
3. FIGURES MUETTES     : une figure incluse, jamais citee dans le corps du texte.
4. REGISTRE VISUEL     : la repartition des figures par famille, et le deficit
                         conceptuel (schema + pipeline + frise) face au corpus.
5. PROSE SANS FIGURE   : les sections longues dont la prose porte des marqueurs
                         de mecanisme, de chronologie, de geographie, de flux ou
                         de comparaison, sans aucun appel de figure. Chaque famille
                         de marqueurs designe l'archetype candidat.
6. PRODUCTION          : dpi, formats et palettes des scripts de figures.

Usage :
    python3 fig_gap_scan.py <main.tex> [--json out.json] [--min-words 250] [--quiet]
    python3 fig_gap_scan.py <projet/>  [--json out.json]

Le script ne modifie rien et ne juge rien : il rend une LISTE DE CANDIDATS a
inspecter. Un score eleve n'est pas la preuve qu'une figure manque, c'est
l'endroit ou aller regarder.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

# --------------------------------------------------------------------------
# Familles de marqueurs. Chaque famille pointe vers un archetype du bestiaire.
# Bilingue : les manuscrits sont en anglais, les notes de travail en francais.
# --------------------------------------------------------------------------
MARKER_FAMILIES: dict[str, dict[str, object]] = {
    "mecanisme": {
        "archetype": "M1 schema de mecanisme",
        "patterns": [
            r"\bmechanis(?:m|ms|tic)\b", r"\bmecanisme?s?\b",
            r"\brecombinat\w+", r"\btranspos\w+", r"\bexcis\w+", r"\binsertion sites?\b",
            r"\bleads? to\b", r"\bresults? in\b", r"\bgives? rise to\b", r"\bcauses?\b",
            r"\bconduit a\b", r"\bentraine\b", r"\baboutit a\b",
            r"\bupstream of\b", r"\bdownstream of\b", r"\bpromoter\b", r"\boperon\b",
            r"\bloss[- ]of[- ]function\b", r"\bpseudogen\w+", r"\bframeshift\b",
            r"\bhorizontal\w* transfer\b", r"\bscenario\b", r"\bsketch\b",
        ],
    },
    "chronologie": {
        "archetype": "T1 frise a double registre",
        "patterns": [
            r"\b\d{3,4}\s?(?:BCE|CE|BP|AD|BC)\b", r"\bkya\b", r"\bMya\b",
            r"\bdivergence times?\b", r"\btMRCA\b", r"\bMRCA\b",
            r"\bNeolithi\w+", r"\bBronze Age\b", r"\bcolonial\b", r"\bpre-Columbian\b",
            r"\bcentur(?:y|ies)\b", r"\bsiecles?\b", r"\bmillenni\w+",
            r"\bdated? to\b", r"\bemerged? (?:around|circa|in)\b", r"\bHPD\b",
            r"\bcalibrat\w+", r"\bmolecular clock\b", r"\bhorloge moleculaire\b",
        ],
    },
    "geographie": {
        "archetype": "G1 carte, G2 carte + arbre couples",
        "patterns": [
            r"\bcountr(?:y|ies)\b", r"\bregions?\b", r"\bcontinents?\b",
            r"\bmigrat\w+", r"\bdispersal\b", r"\bspread\b", r"\bintroduc\w+ (?:into|to)\b",
            r"\bphylogeograph\w+", r"\bendemic\b", r"\bimported?\b",
            r"\btrade routes?\b", r"\bslave trade\b", r"\bsampling sites?\b",
            r"\bAfrica\b", r"\bAsia\b", r"\bEurope\b", r"\bAmericas?\b", r"\bOceania\b",
            r"\bgeographic\w*\b", r"\bgeographique\w*\b",
        ],
    },
    "flux": {
        "archetype": "P1 diagramme de flux des donnees (CONSORT genomique)",
        "patterns": [
            r"\bpipelines?\b", r"\bworkflows?\b", r"\bwe (?:then|next|subsequently)\b",
            r"\bfirst,\b", r"\bsecond,\b", r"\bthird,\b", r"\bfinally,\b",
            r"\bstep [1-9]\b", r"\betapes?\b", r"\bfilter(?:ed|ing)\b", r"\bexclud(?:ed|ing)\b",
            r"\bretained\b", r"\bdiscarded\b", r"\bthreshold\w*\b", r"\bcut-?off\b",
            r"\bquality controls?\b", r"\bQC\b", r"\bwere removed\b", r"\bremaining\b",
            r"\bgates?\b", r"\btriage\b", r"\bcriteri(?:a|on)\b",
        ],
    },
    "comparaison": {
        "archetype": "C1 avant/apres (etat de l'art contre contribution)",
        "patterns": [
            r"\bin contrast\b", r"\bwhereas\b", r"\bhowever\b", r"\bunlike\b",
            r"\bpreviously (?:reported|described|thought|placed)\b",
            r"\bearlier (?:studies|work|analyses)\b", r"\bhas been (?:assumed|considered)\b",
            r"\bwe (?:instead|rather) (?:find|show|place|propose)\b",
            r"\brevis\w+", r"\breassign\w+", r"\breclassif\w+", r"\bcontrary to\b",
            r"\bau contraire\b", r"\bcontrairement a\b", r"\balors que\b",
            r"\bchallenges? the\b", r"\bdiffers? from\b",
        ],
    },
    "structure": {
        "archetype": "S1 anatomie de locus, S2 dossier structural d'un gene",
        "patterns": [
            r"\bcodons? \d+\b", r"\bresidues? \d+\b", r"\bamino acid\b",
            r"\bstrand\b", r"\boverlaps?\b", r"\bnucleotides?\b",
            r"\b\d{4,7}\s?(?:--|-|to)\s?\d{4,7}\b", r"\bbinding site\b",
            # « fold » seul capte les « 3-fold enrichment » : exiger le contexte proteique.
            r"\bactive site\b", r"\bcatalytic\b",
            r"\b(?:protein|structural|tertiary|same|conserved|Rossmann|TIM[- ]barrel)\s+fold\b",
            r"\bdomains?\b",
            r"\bN-terminal\b", r"\bC-terminal\b", r"\bTSS\b", r"\btranscription start\b",
        ],
    },
    "denombrement": {
        "archetype": "D1 matrice triee par l'arbre, D2 alluvial de nomenclatures",
        "patterns": [
            r"\bn\s?=\s?\d", r"\b\d+\s?(?:strains?|genomes?|isolates?|souches?)\b",
            r"\bproportions?\b", r"\bfrequenc(?:y|ies)\b", r"\bpercentage\b",
            r"\bshared by\b", r"\bexclusive to\b", r"\bpresent in\b", r"\babsent from\b",
            r"\bsynapomorph\w+", r"\bmarkers?\b", r"\bbarcode\b",
            r"\bnomenclatur\w+", r"\bscheme\b", r"\bcross-?map\w*\b",
        ],
    },
}

# Signaux FORTS, testes avant les indices faibles et dans cet ordre.
# Lecon du banc d'essai `animal_vs_human` (2026-08-24) : des indices comme « clade »,
# « lineage » ou « map » apparaissent dans la legende de figures qui ne sont ni des
# arbres ni des cartes, et classaient 17 figures sur 21 en « arbre » la ou le manuscrit
# n'en portait que deux. Le TYPE DE TRACE nomme dans la legende prime sur le sujet.
STRONG_SIGNALS: list[tuple[str, str]] = [
    ("frise", r"\btime\s?line\b|\bfrise\b|\bthrough time\b|\bchronolog\w+|\bskyline\b|"
              r"\bdated (?:tree|phylogeny)\b|\bcalendar\b"),
    ("pipeline", r"\bflow\s?chart\b|\bworkflow\b|\bpipeline\b|\bdecision tree\b|"
                 r"\bCONSORT\b|\btriage\b|\blogigram\w*"),
    # « phylogenetic » est un ADJECTIF qui qualifie aussi l'axe d'un diagramme en
    # barres (« at each phylogenetic node ») : exiger un NOM d'arbre.
    ("arbre", r"\btrees?\b|\bcladogram\b|\bdendrogram\b|\bphylogen(?:y|ies)\b|"
              r"\btopolog(?:y|ies)\b|\bnewick\b|\bRAxML\b|\bIQ-?TREE\b|\biTOL\b|"
              r"\bbranch lengths?\b|\btip labels?\b"),
    ("carte", r"\bworld map\b|\bchoropleth\b|\bgeographic\w*\b|\bcountr(?:y|ies)\b|"
              r"\bsampling sites?\b|\bspatial distribution\b|\bmigration (?:routes?|arcs?)\b|"
              r"\blatitude\b|\bcarte\b"),
    ("schema", r"\bschematic\b|\bdiagram\b|\bpathway\b|\bmechanis\w+|\bgraphical abstract\b|"
               r"\boverview of\b|\banatomy\b|\blocus (?:map|architecture)\b|\boperon structure\b"),
    # Le type de trace, teste APRES les schemas : « pathway overview ... bar plots »
    # est un schema de voie, pas un graphique.
    ("statistique", r"\bbar\s?(?:chart|plot)s?\b|\bstacked bar\b|\bheat\s?map\b|"
                    r"\bscatter\b|\bbox\s?plot\b|\bviolin\b|\bhistogram\b|\bdensity plot\b|"
                    r"\brarefaction\b|\bregression\b|\bROC\b|\bPCA\b|\bt-?SNE\b|"
                    r"\bpermutation test\b|\bdistribution of\b|\bcorrelation\b"),
]

FIGURE_TYPE_HINTS: dict[str, list[str]] = {
    "arbre": ["tree", "arbre", "phylo", "raxml", "iqtree", "itol", "newick",
              "dendro", "topolog", "bootstrap"],
    "carte": ["carte", "choropleth", "country", "world", "atlas",
              "geographic", "migration"],
    "structure": ["struct", "pymol", "alphafold", "esmfold", "boltz", "pocket",
                  "active_site", "fold", "pdb", "disorder"],
    "schema": ["schema", "scheme", "diagram", "mechanism", "mecanisme", "concept",
               "model", "overview", "graphical_abstract", "abstract", "sketch",
               "architecture", "locus", "operon", "anatomy"],
    "pipeline": ["pipeline", "workflow", "flow", "flux", "consort", "triage",
                 "decision", "logigram", "qc_"],
    "frise": ["timeline", "frise", "chrono", "dated", "dating", "skyline", "temporal",
              "history"],
    "alignement": ["align", "msa", "synteny", "syntenie", "circos", "genome_map"],
}

# Un titre de section qui annonce un dessin. Signal le plus precis du corpus.
TITLE_SIGNAL = re.compile(
    r"\b(?:sketch|overview|schema|scheme|model|architecture|scenario|framework|"
    r"workflow|pipeline|timeline|chronolog\w*|anatomy|landscape|roadmap|"
    r"vue d'ensemble|apercu|panorama|deroul\w*)\b", re.I)

# Sections non argumentatives : elles portent des marqueurs sans jamais appeler
# de figure. Les laisser remonter ferait du bruit a chaque passage.
BOILERPLATE = re.compile(
    r"\b(?:availability|acknowledg\w*|funding|competing|conflicts? of interest|"
    r"ethic\w*|consent|references|bibliograph\w*|author contributions?|"
    r"abbreviations?|supplementary (?:materials?|information)|declarations?|"
    r"remerciements?|financement|disponibilit\w*)\b", re.I)

STAT_FALLBACK = "statistique"

CONCEPTUAL_FAMILIES = {"schema", "pipeline", "frise"}

# Reference de corpus, mesuree sur 113 figures de 17 manuscrits MTBC (2026-08).
CORPUS_REFERENCE = {
    "statistique": 0.504, "arbre": 0.133, "carte": 0.115, "structure": 0.071,
    "schema": 0.062, "pipeline": 0.053, "frise": 0.044, "alignement": 0.009,
}
CORPUS_CONCEPTUAL_SHARE = 0.159


# --------------------------------------------------------------------------
# Lecture du manuscrit, includes resolus
# --------------------------------------------------------------------------
def strip_comments(text: str) -> str:
    """Retirer les commentaires LaTeX sans casser les \\% echappes."""
    return re.sub(r"(?<!\\)%.*", "", text)


def load_manuscript(main_tex: Path) -> tuple[str, list[Path], str]:
    """Concatener main.tex et ses \\input/\\include resolus. Rend (texte_sans_commentaires,
    fichiers_lus, texte_brut_avec_commentaires)."""
    seen: list[Path] = []
    raw_parts: list[str] = []

    def absorb(path: Path, depth: int = 0) -> None:
        if depth > 6 or path in seen or not path.is_file():
            return
        seen.append(path)
        raw = path.read_text(encoding="utf-8", errors="replace")
        raw_parts.append(raw)
        body = strip_comments(raw)
        for inc in re.findall(r"\\(?:input|include|subfile)\s*\{([^}]+)\}", body):
            cand = (path.parent / inc).with_suffix(".tex")
            if not cand.is_file():
                cand = path.parent / inc
            absorb(cand, depth + 1)

    absorb(main_tex)
    raw_text = "\n".join(raw_parts)
    return strip_comments(raw_text), seen, raw_text


def find_main_tex(target: Path) -> Path | None:
    if target.is_file() and target.suffix == ".tex":
        return target
    for cand in (target / "article" / "main.tex", target / "main.tex"):
        if cand.is_file():
            return cand
    hits = sorted(target.glob("*/main.tex")) + sorted(target.glob("*/*/main.tex"))
    return hits[0] if hits else None


# --------------------------------------------------------------------------
# Analyses
# --------------------------------------------------------------------------
def classify_figure(name: str, caption: str) -> str:
    """Le TYPE DE TRACE nomme dans la legende prime sur le sujet de la figure.

    Les signaux forts sont testes dans l'ordre de STRONG_SIGNALS ; les indices
    faibles ne servent qu'en dernier recours. Sans cette precedence, un mot de
    sujet (« clade », « lineage », « map ») classe une serie de barres en arbre
    ou une voie metabolique en carte.
    """
    blob = f"{name} {caption}"
    # Le signal nomme LE PLUS TOT dans la legende gagne : une legende commence par
    # decrire ce que la figure EST (« Clustered heatmap... », « Schematic cladogram... »)
    # avant de dire de quoi elle parle.
    hits = []
    for rank, (fam, pattern) in enumerate(STRONG_SIGNALS):
        m = re.search(pattern, blob, re.I)
        if m:
            hits.append((m.start(), rank, fam))
    if hits:
        return min(hits)[2]
    low = blob.lower()
    scores = {fam: sum(low.count(h) for h in hints)
              for fam, hints in FIGURE_TYPE_HINTS.items()}
    best = max(scores, key=lambda k: scores[k])
    return best if scores[best] > 0 else STAT_FALLBACK


def extract_figures(text: str) -> list[dict]:
    """Un enregistrement par environnement figure, plus les includegraphics isoles."""
    figures: list[dict] = []
    for env in re.finditer(
        r"\\begin\{(figure\*?|sidewaysfigure)\}(.*?)\\end\{\1\}", text, re.S
    ):
        body = env.group(2)
        graphics = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\s*\{([^}]+)\}", body)
        cap = re.search(r"\\caption\s*\{", body)
        caption = _balanced(body, cap.end() - 1) if cap else ""
        label = re.search(r"\\label\s*\{([^}]+)\}", body)
        figures.append({
            "graphics": graphics,
            "caption": caption.strip(),
            "caption_words": len(caption.split()),
            "label": label.group(1) if label else None,
            "has_todo": bool(re.search(r"\\todo\s*\{", body)),
            "type": classify_figure(" ".join(graphics), caption),
        })
    known = {g for f in figures for g in f["graphics"]}
    for g in re.findall(r"\\includegraphics(?:\[[^\]]*\])?\s*\{([^}]+)\}", text):
        if g not in known:
            figures.append({"graphics": [g], "caption": "", "caption_words": 0,
                            "label": None, "has_todo": False, "orphan_env": True,
                            "type": classify_figure(g, "")})
            known.add(g)
    return figures


def _balanced(text: str, open_idx: int) -> str:
    """Extraire le contenu d'un groupe {...} en respectant l'imbrication."""
    depth, out = 0, []
    for ch in text[open_idx:]:
        if ch == "{":
            depth += 1
            if depth == 1:
                continue
        elif ch == "}":
            depth -= 1
            if depth == 0:
                break
        if depth >= 1:
            out.append(ch)
    return "".join(out)


def split_sections(text: str) -> list[dict]:
    pat = re.compile(r"\\(section|subsection|subsubsection)\*?\s*\{")
    marks = []
    for m in pat.finditer(text):
        title = _balanced(text, m.end() - 1)
        marks.append((m.start(), m.group(1), title))
    sections = []
    for i, (pos, level, title) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(text)
        body = text[pos:end]
        prose = re.sub(r"\\begin\{(figure\*?|table\*?|tabular|equation\*?|align\*?)\}.*?"
                       r"\\end\{\1\}", " ", body, flags=re.S)
        prose = re.sub(r"\\[a-zA-Z@]+\*?(?:\[[^\]]*\])?(?:\{[^{}]*\})?", " ", prose)
        sections.append({
            "level": level, "title": title.strip(),
            "words": len(prose.split()),
            "fig_refs": re.findall(r"\\(?:auto|c|C)?ref\s*\{(fig:[^}]+)\}", body),
            "has_figure_env": bool(re.search(r"\\begin\{figure", body)),
            "prose": prose,
        })
    return sections


def score_markers(prose: str) -> dict[str, int]:
    low = prose.lower()
    out = {}
    for fam, spec in MARKER_FAMILIES.items():
        n = 0
        for pat in spec["patterns"]:  # type: ignore[index]
            n += len(re.findall(pat, low, flags=re.I))
        out[fam] = n
    return out


def scan_orphan_files(project_root: Path, used: set[str]) -> list[str]:
    """Images produites sur disque et jamais incluses dans le manuscrit.

    Une image incluse par la SOURCE d'une figure (un `.tex` standalone qui compose
    la figure) n'est pas orpheline : c'est un intrant. Le premier jet ne lisait que
    le manuscrit et signalait donc comme orphelines les icones d'une figure qu'il
    venait lui-meme de faire integrer.
    """
    used_stems = set()
    for u in used:
        used_stems.add(Path(u).stem)
        used_stems.add(Path(u).name)
    # Graphiques references depuis n'importe quel .tex du projet (sources de figures
    # standalone comprises), pas seulement depuis la chaine du manuscrit.
    for tex in project_root.rglob("*.tex"):
        if any(p in {".git", ".venv", "_build", "node_modules"} for p in tex.parts):
            continue
        try:
            body = strip_comments(tex.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
        for g in re.findall(r"\\includegraphics(?:\[[^\]]*\])?\s*\{([^}]+)\}", body):
            used_stems.add(Path(g).stem)
            used_stems.add(Path(g).name)

    exts = {".pdf", ".png", ".svg", ".tiff", ".tif", ".jpg", ".eps"}
    # `_build` est le repertoire de compilation de tikz_build.py : ses sorties sont
    # des intermediaires. `icons`/`assets` sont des MAGASINS D'ASSETS : leur contenu
    # est inclus par la source d'une figure, souvent A TRAVERS UNE MACRO que la regex
    # ci-dessus ne peut pas resoudre. D'ou la convention : ranger les assets d'une
    # figure dans un sous-repertoire nomme, jamais a plat a cote des figures.
    skip = {".git", ".venv", "node_modules", "__pycache__", "site-packages",
            "archives", "archive", ".claude", "worktrees", "_build",
            "icons", "assets", "logos"}
    orphans = []
    for d in ("article/figures", "figures", "résultats", "resultats",
              "results", "article/fig", "supplementary"):
        base = project_root / d
        if not base.is_dir():
            continue
        for f in base.rglob("*"):
            if f.suffix.lower() not in exts or not f.is_file():
                continue
            if any(p in skip for p in f.parts):
                continue
            if f.stem in used_stems or f.name in used_stems:
                continue
            orphans.append(str(f.relative_to(project_root)))
    return sorted(orphans)


def audit_production(project_root: Path) -> dict:
    """dpi, formats et palettes des scripts de figures."""
    dpis: Counter = Counter()
    fmts: Counter = Counter()
    colors: Counter = Counter()
    styles = 0
    nscripts = 0
    skip = {".git", ".venv", "node_modules", "__pycache__", "site-packages"}
    for py in project_root.rglob("*.py"):
        if any(p in skip for p in py.parts):
            continue
        try:
            src = py.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "savefig" not in src and "matplotlib" not in src:
            continue
        nscripts += 1
        dpis.update(re.findall(r"dpi\s*=\s*(\d+)", src))
        fmts.update(m.lower() for m in re.findall(r"savefig\([^)]*\.(\w{3,4})", src))
        colors.update(c.upper() for c in re.findall(r"#[0-9A-Fa-f]{6}", src))
        styles += len(re.findall(r"plt\.style\.use|mplstyle", src))
    return {
        "scripts": nscripts,
        "dpi": dict(dpis.most_common(8)),
        "formats": dict(fmts.most_common(6)),
        "top_colors": dict(colors.most_common(8)),
        "style_sheet_uses": styles,
    }


# --------------------------------------------------------------------------
# Rapport
# --------------------------------------------------------------------------
def build_report(main_tex: Path, min_words: int) -> dict:
    text, files, raw = load_manuscript(main_tex)
    project_root = main_tex.parent.parent if main_tex.parent.name == "article" \
        else main_tex.parent

    figures = extract_figures(text)
    labels = {f["label"] for f in figures if f["label"]}
    refs = set(re.findall(r"\\(?:auto|c|C)?ref\s*\{(fig:[^}]+)\}", text))
    used_graphics = {g for f in figures for g in f["graphics"]}

    types = Counter(f["type"] for f in figures)
    total = sum(types.values())
    conceptual = sum(types[t] for t in CONCEPTUAL_FAMILIES)

    sections = split_sections(text)
    candidates = []
    for s in sections:
        if s["fig_refs"] or BOILERPLATE.search(s["title"]):
            continue
        marks = score_markers(s["prose"])
        dominant = max(marks, key=lambda k: marks[k])
        density = round(1000 * sum(marks.values()) / max(s["words"], 1), 1)
        if marks[dominant] == 0:
            continue
        # Un titre de section qui annonce deja un dessin est le signal le plus sur
        # du corpus : « An evolutionary sketch », « Overview of the pipeline »...
        title_flag = bool(TITLE_SIGNAL.search(s["title"]))
        # Une section courte mais dense vaut une section longue et diluee : le seuil
        # de longueur seul aurait manque « An evolutionary sketch » a UN mot pres.
        long_enough = s["words"] >= min_words
        short_but_dense = s["words"] >= 120 and density >= 15.0
        if not (long_enough or short_but_dense or (title_flag and s["words"] >= 60)):
            continue
        candidates.append({
            "section": s["title"], "level": s["level"], "words": s["words"],
            "markers": {k: v for k, v in marks.items() if v},
            "dominant": dominant,
            "archetype": MARKER_FAMILIES[dominant]["archetype"],
            "density_per_1000w": density,
            "title_announces_a_figure": title_flag,
        })
    candidates.sort(key=lambda c: (not c["title_announces_a_figure"],
                                   -c["density_per_1000w"], -c["words"]))

    todo_captions = re.findall(r"\\todo\s*\{([^}]{0,120})", raw)

    return {
        "main_tex": str(main_tex),
        "files_read": [str(f) for f in files],
        "word_count": len(re.sub(r"\\[a-zA-Z@]+\*?(?:\[[^\]]*\])?(?:\{[^{}]*\})?", " ",
                                 text).split()),
        "figures": {
            "count": total,
            "by_type": dict(types.most_common()),
            "conceptual_share": round(conceptual / total, 3) if total else 0.0,
            "corpus_conceptual_share": CORPUS_CONCEPTUAL_SHARE,
            "captions_under_25_words": [f["label"] or f["graphics"][:1]
                                        for f in figures if f["caption_words"] < 25],
        },
        "pending_refs": sorted(refs - labels),
        "mute_figures": sorted(lb for lb in labels if lb not in refs),
        "todo_markers": todo_captions,
        "orphan_files": scan_orphan_files(project_root, used_graphics),
        "prose_without_figure": candidates,
        "production": audit_production(project_root),
    }


def render(rep: dict) -> str:
    L: list[str] = []
    add = L.append
    add(f"MANUSCRIT   {rep['main_tex']}")
    add(f"            {rep['word_count']} mots, {len(rep['files_read'])} fichier(s) .tex")
    fg = rep["figures"]
    add("")
    add(f"FIGURES     {fg['count']} incluse(s)")
    if fg["count"]:
        add("            " + ", ".join(f"{k} {v}" for k, v in fg["by_type"].items()))
        add(f"            part conceptuelle (schema+pipeline+frise) : "
            f"{100*fg['conceptual_share']:.0f}% "
            f"(corpus MTBC : {100*fg['corpus_conceptual_share']:.0f}%)")
    if fg["captions_under_25_words"]:
        add(f"            legendes trop courtes pour etre autonomes : "
            f"{len(fg['captions_under_25_words'])}")

    if rep["pending_refs"]:
        add("")
        add("BLOQUANT    reference(s) de figure sans figure : "
            + ", ".join(rep["pending_refs"]))
    if rep["mute_figures"]:
        add("")
        add("MUETTE      figure(s) jamais citee(s) dans le texte : "
            + ", ".join(rep["mute_figures"]))
    if rep["todo_markers"]:
        add("")
        add(f"TODO        {len(rep['todo_markers'])} marqueur(s) de figure a produire")
        for t in rep["todo_markers"][:5]:
            add(f"            - {t.strip()[:100]}")

    orph = rep["orphan_files"]
    if orph:
        add("")
        add(f"ORPHELINES  {len(orph)} image(s) produite(s) et jamais incluse(s)")
        for o in orph[:12]:
            add(f"            - {o}")
        if len(orph) > 12:
            add(f"            ... et {len(orph)-12} autres")

    cand = rep["prose_without_figure"]
    add("")
    add(f"PROSE SANS FIGURE   {len(cand)} section(s) longue(s) sans appel de figure")
    for c in cand[:10]:
        marks = " ".join(f"{k}:{v}" for k, v in sorted(
            c["markers"].items(), key=lambda kv: -kv[1])[:3])
        flag = " (le titre annonce deja un dessin)" if c.get(
            "title_announces_a_figure") else ""
        add(f"  [{c['density_per_1000w']:>5}/1000 mots] {c['words']:>5} mots  "
            f"{c['section'][:58]}{flag}")
        add(f"       marqueurs {marks}")
        add(f"       archetype candidat : {c['archetype']}")

    prod = rep["production"]
    add("")
    add(f"PRODUCTION  {prod['scripts']} script(s) de figure")
    if prod["dpi"]:
        add("            dpi : " + ", ".join(f"{k} ({v}x)" for k, v in prod["dpi"].items()))
    if prod["formats"]:
        add("            formats : " + ", ".join(f"{k} ({v}x)"
                                                 for k, v in prod["formats"].items()))
    if prod["style_sheet_uses"] == 0 and prod["scripts"] > 2:
        add("            aucune feuille de style partagee (plt.style.use / .mplstyle)")
    add("")
    add("Ces chiffres sont des CANDIDATS a inspecter, pas un verdict.")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", type=Path, help="main.tex ou repertoire de projet")
    ap.add_argument("--json", type=Path, default=None, help="ecrire le rapport JSON")
    ap.add_argument("--min-words", type=int, default=250,
                    help="seuil de longueur d'une section candidate (defaut 250)")
    ap.add_argument("--quiet", action="store_true", help="ne rien afficher")
    args = ap.parse_args()

    main_tex = find_main_tex(args.target)
    if main_tex is None:
        print(f"erreur : aucun main.tex trouve depuis {args.target}", file=sys.stderr)
        return 2

    rep = build_report(main_tex, args.min_words)
    if args.json:
        args.json.write_text(json.dumps(rep, indent=2, ensure_ascii=False),
                             encoding="utf-8")
    if not args.quiet:
        print(render(rep))
    return 1 if (rep["pending_refs"] or rep["todo_markers"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
