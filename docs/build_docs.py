#!/usr/bin/env python3
"""Génère la documentation des skills (docs/) à partir du frontmatter des SKILL.md.

La documentation est cadrée sous l'angle de la recherche M. tuberculosis (MTBC) :
un pipeline de recherche organise l'ensemble, et chaque page de plugin ouvre sur
son rôle dans un projet M. tuberculosis. Les entrées par skill (raison d'être,
compétences) sont extraites fidèlement du frontmatter des SKILL.md.

Le plugin `maboss` relève d'un AUTRE projet (modélisation booléenne de la
signalisation, mabossDemo) : il est documenté sur une page à part, hors pipeline.

Régénérable : relancer `python3 docs/build_docs.py` depuis la racine du dépôt
après tout ajout/modification de skill. Chaque skill canonique (SKILL.md réel)
est documenté une fois, sur la page de son plugin d'origine ; les skills partagés
par symlink sont listés avec un lien croisé vers leur page d'origine.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"

# Plugins de la collection M. tuberculosis (ordre d'affichage).
PLUGINS = [
    "bio_pathogens",
    "bio_population_genetics",
    "bio_redac",
    "redac",
    "ia",
    "multimedia",
    "ops",
    "web",
]

# Plugins d'un AUTRE projet, documentés à part (hors angle M. tuberculosis).
SEPARATE = ["maboss"]
ALL_PLUGINS = PLUGINS + SEPARATE

# Rôle de chaque plugin DANS UN PROJET M. tuberculosis (cadrage éditorial).
MTB_ANGLE = {
    "bio_pathogens": (
        "Cœur du dispositif. Rassemble les skills qui touchent directement le "
        "complexe Mycobacterium tuberculosis (MTBC) et les pathogènes apparentés : "
        "accès aux génomes de référence et aux isolats de recherche publiés, "
        "fréquences alléliques de résistance aux antituberculeux telles que "
        "rapportées dans la littérature évaluée par des pairs, assignation de "
        "lignées, bases de données génomiques spécialisées. C'est le plugin qu'on "
        "active quand le travail porte effectivement sur M. tuberculosis."
    ),
    "bio_population_genetics": (
        "Contexte hôte et outillage générique. Pour une étude M. tuberculosis, "
        "l'histoire des populations humaines, les migrations, la paléoclimatologie "
        "et l'archéologie éclairent la co-évolution hôte-pathogène et la dispersion "
        "des lignées du MTBC. Le plugin porte aussi les briques transversales "
        "(phylogénétique, statistiques, fouille de littérature) réutilisées par les "
        "analyses MTBC elles-mêmes."
    ),
    "bio_redac": (
        "Phase hybride analyse et rédaction. Agrège par symlink les skills des "
        "autres plugins pour le moment où l'on passe des résultats phylogénomiques "
        "M. tuberculosis (arbre daté, profils de résistance, figures) au manuscrit."
    ),
    "redac": (
        "Rédaction et contrôle qualité du manuscrit M. tuberculosis : mise en forme "
        "LaTeX, vérification des affirmations et des références, nettoyage "
        "stylistique, réponse aux relecteurs, dépôt Zenodo et pont Overleaf."
    ),
    "ia": (
        "Machine learning et data science au service des analyses MTBC : "
        "classification de lignées, prédiction de phénotypes de résistance à partir "
        "de génotypes, réduction de dimension sur des matrices de SNP, explication "
        "des modèles obtenus."
    ),
    "multimedia": (
        "Outillage périphérique (audio, vidéo, synthèse vocale, sous-titrage). Utile "
        "à la valorisation et à la communication d'un projet M. tuberculosis "
        "(séminaires, supports pédagogiques), pas à l'analyse génomique."
    ),
    "ops": (
        "Projets applicatifs du groupe (PrédictOps, OptimOps, DoctrinOps), hors du "
        "champ M. tuberculosis ; présents dans la collection pour d'autres travaux."
    ),
    "web": (
        "Développement et test d'applications web, transverse. Par exemple pour "
        "exposer une base ou un tableau de bord de résultats MTBC."
    ),
    "maboss": (
        "Projet distinct. maboss / CoLoMoTo n'appartient pas au programme "
        "M. tuberculosis : il concerne la modélisation booléenne stochastique de "
        "réseaux de signalisation (signalisation cancéreuse, projet mabossDemo). "
        "Il est documenté ici uniquement parce qu'il partage le même dépôt de "
        "plugins, et reste hors du pipeline de recherche M. tuberculosis."
    ),
}

# Pipeline de recherche M. tuberculosis : narration structurante de l'index.
PIPELINE_MD = """\
## Pipeline de recherche M. tuberculosis

La collection se lit comme la chaîne de production d'un article de phylogénomique
évolutive du complexe *Mycobacterium tuberculosis* (MTBC), du choix du problème
au dépôt final. Les skills cités sont indicatifs ; le catalogue complet suit.

| Étape | Ce qu'on fait | Skills clés | Plugin d'origine |
|-------|---------------|-------------|------------------|
| 1. Cadrage et littérature | Choisir la question, revue de l'état de l'art MTBC | `scientific-problem-selection`, `lit-review`, `pubmed-database`, `openalex`, `europe-pmc`, `read-scientific-pdf` | ia, redac, bio_population_genetics |
| 2. Acquisition des génomes | Récupérer génomes de référence et isolats publiés | `ncbi-pathogen-detection`, `pathogens-portal`, `tb-cli`, `biopython`, `pysam` | bio_pathogens, bio_population_genetics |
| 3. Variants, résistance, lignées | Génomique comparative, allèles de résistance, lignée | `resistance-profiler`, `mbovis`, `mycobacterium-leprae`, `scikit-bio` | bio_pathogens, bio_population_genetics |
| 4. Phylogénie et datation | Arbre, horloge moléculaire, skyline démographique | `iqtree-lsd2`, `bayesian-skyline`, `beast2-phylogeography`, `pastml` | bio_population_genetics, bio_pathogens |
| 5. Phylogéographie, contexte hôte | Dispersion, migrations humaines, paléoclimat | `geo-map`, `nextstrain`, `migration-data`, `itol` | bio_population_genetics |
| 6. Modélisation, stats, ML | Tests statistiques, classification, modèles | `statsmodels`, `scikit-learn`, `scanpy` | ia, bio_population_genetics |
| 7. Visualisation | Figures publication, arbres annotés, cartes | `create-viz`, `seaborn`, `matplotlib`, `plotly`, `itol` | bio_population_genetics, ia, redac |
| 8. Rédaction | Manuscrit LaTeX, slides, bibliographie | `latex-document`, `latex-writing`, `biblatex`, `deai-latex`, `beamer-slides` | redac |
| 9. Vérification, réponse aux relecteurs | Affirmations, références, figures, supplémentaires, rebuttal | `claim-check`, `bib-check`, `fig-check`, `supp-check`, `manuscript-review`, `reviewer-response` | redac |
| 10. Valorisation et dépôt | DOI Zenodo, Overleaf, financements, CV | `zenodo-deposit`, `overleaf-bridge`, `grant-proposal`, `cv` | redac |

Les skills sans lien direct avec M. tuberculosis (outillage générique de fichiers,
web, multimédia, ops) servent de support à toute étape ; ils sont listés sous leur
plugin. Le plugin `maboss` relève d'un autre projet et est documenté à part.
"""

TRIGGER_RE = re.compile(
    r"(?is)\b(use when|use this skill|trigger[s]?(?:\s+include|\s+phrases)?|"
    r"triggers on|déclencheurs?|utiliser quand|utilise ce skill|"
    r"trigger with|triggering)\b\s*[:.-]?\s*"
)


def clean(s: str | None) -> str:
    s = re.sub(r"\s+", " ", (s or "").strip())
    # Normalise les tirets cadratin/demi-cadratin (marqueurs de texte IA).
    s = s.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", ", ")
    s = s.replace(" -- ", ", ")
    return re.sub(r"\s+", " ", s).strip()


def read_frontmatter(skill_md: Path) -> dict:
    text = skill_md.read_text(encoding="utf-8", errors="replace")
    if not text.lstrip().startswith("---"):
        return {}
    lines = text.splitlines()
    try:
        start = next(i for i, l in enumerate(lines) if l.strip() == "---")
        end = next(i for i in range(start + 1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        return {}
    try:
        data = yaml.safe_load("\n".join(lines[start + 1 : end])) or {}
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def split_description(desc: str):
    desc = re.sub(r"\s+", " ", (desc or "").strip())
    m = TRIGGER_RE.search(desc)
    if not m:
        return clean(desc), ""
    raison = desc[: m.start()].strip(" .;:-")
    quand = desc[m.end() :].strip(" .;:-")
    if len(raison) < 15:
        return clean(desc), ""
    return clean(raison), clean(quand)


def to_bullets(quand: str):
    if not quand:
        return []
    parts = re.split(r"(?:;|\.\s+|\s\|\s)", quand)
    out, seen = [], set()
    for p in parts:
        b = clean(p).strip('"«».,')
        if len(b) > 3 and b.lower() not in seen:
            seen.add(b.lower())
            out.append(b)
    return out[:8]


def collect():
    plugin_desc, canonical, appears = {}, {}, {}
    for plugin in ALL_PLUGINS:
        pj = ROOT / plugin / ".claude-plugin" / "plugin.json"
        if pj.exists():
            plugin_desc[plugin] = json.loads(pj.read_text(encoding="utf-8")).get("description", "")
        skills_dir = ROOT / plugin / "skills"
        if not skills_dir.is_dir():
            continue
        for entry in sorted(skills_dir.iterdir()):
            if not entry.is_dir() or not (entry / "SKILL.md").exists():
                continue
            name = entry.name
            appears.setdefault(name, set()).add(plugin)
            is_symlink = entry.is_symlink()
            if is_symlink and name in canonical:
                continue
            fm = read_frontmatter((entry / "SKILL.md").resolve())
            raison, quand = split_description(fm.get("description", ""))
            home = plugin
            if is_symlink:
                try:
                    home = entry.resolve().relative_to(ROOT).parts[0]
                except ValueError:
                    home = plugin
            if name not in canonical or not is_symlink:
                canonical[name] = {"name": name, "raison": raison, "quand": quand, "home": home}

    # Superpose les versions françaises (docs/skills_fr.json) sur le frontmatter.
    fr_path = DOCS / "skills_fr.json"
    if fr_path.exists():
        fr = json.loads(fr_path.read_text(encoding="utf-8"))
        for name, tr in fr.items():
            if name.startswith("_") or name not in canonical or not isinstance(tr, dict):
                continue
            if tr.get("raison"):
                canonical[name]["raison"] = clean(tr["raison"])
            canonical[name]["quand"] = clean(tr.get("quand", ""))
    return plugin_desc, canonical, appears


def render_skill(rec) -> str:
    out = [f"### {rec['name']}", "", rec["raison"] or "_(pas de description)_", ""]
    bullets = to_bullets(rec["quand"])
    if bullets:
        out.append("Compétences : " + " ; ".join(bullets))
        out.append("")
    return "\n".join(out)


def render_plugin_page(plugin, plugin_desc, canonical, appears, by_home):
    own = by_home.get(plugin, [])
    shared = sorted(n for n, ps in appears.items() if plugin in ps and canonical[n]["home"] != plugin)
    lines = [f"# Plugin `{plugin}`", ""]
    if plugin_desc.get(plugin):
        lines += [f"> {clean(plugin_desc[plugin])}", ""]
    if MTB_ANGLE.get(plugin):
        label = "## Positionnement" if plugin in SEPARATE else "## Rôle dans un projet M. tuberculosis"
        lines += [label, "", MTB_ANGLE[plugin], ""]
    lines += [
        f"Skills propres (canoniques) : **{len(own)}** ; skills partagés utilisés "
        f"(symlinks) : **{len(shared)}**.",
        "",
        "[Retour à l'index de la documentation](README.md)",
        "",
    ]
    if own:
        lines += ["## Skills propres", "",
                  "Sommaire : " + " ; ".join(f"[{r['name']}](#{r['name']})" for r in own), ""]
        for rec in own:
            lines.append(render_skill(rec))
    if shared:
        lines += ["## Skills partagés (via symlink)", "",
                  "Documentés sur la page de leur plugin d'origine.", "",
                  "| Skill | Origine |", "|-------|---------|"]
        for n in shared:
            home = canonical[n]["home"]
            lines.append(f"| [{n}]({home}.md#{n}) | `{home}` |")
        lines.append("")
    return "\n".join(lines) + "\n"


def main():
    DOCS.mkdir(exist_ok=True)
    plugin_desc, canonical, appears = collect()

    by_home = {p: [] for p in ALL_PLUGINS}
    for rec in canonical.values():
        by_home.setdefault(rec["home"], []).append(rec)
    for p in by_home:
        by_home[p].sort(key=lambda r: r["name"])

    for plugin in ALL_PLUGINS:
        (DOCS / f"{plugin}.md").write_text(
            render_plugin_page(plugin, plugin_desc, canonical, appears, by_home), encoding="utf-8"
        )

    core_total = sum(len(by_home.get(p, [])) for p in PLUGINS)
    sep_total = sum(len(by_home.get(p, [])) for p in SEPARATE)

    idx = [
        "# Documentation des skills : boîte à outils de recherche M. tuberculosis",
        "",
        f"Cette collection outille le programme de recherche du groupe Guyeux "
        f"(FEMTO-ST) en phylogénomique évolutive du complexe *Mycobacterium "
        f"tuberculosis* (MTBC), de l'accès aux génomes publiés jusqu'au manuscrit. "
        f"Elle réunit **{core_total} skills canoniques** sur "
        f"**{len([p for p in PLUGINS if by_home.get(p)])} plugins**. Chaque skill "
        f"est décrit par sa raison d'être et ses compétences ; les skills partagés "
        f"entre plugins (symlinks) sont documentés une seule fois, sur la page de "
        f"leur plugin d'origine.",
        "",
        "[Retour au README du dépôt](../README.md)",
        "",
        "> Pages générées par `docs/build_docs.py` à partir du frontmatter des "
        "`SKILL.md`. Régénérer après tout ajout de skill.",
        "",
        PIPELINE_MD,
        "## Plugins de la collection",
        "",
        "| Plugin | Rôle dans un projet M. tuberculosis | Skills propres |",
        "|--------|-------------------------------------|----------------|",
    ]
    for plugin in PLUGINS:
        role = clean(MTB_ANGLE.get(plugin, plugin_desc.get(plugin, "")))
        if len(role) > 150:
            role = role[:147].rstrip() + "…"
        idx.append(f"| [{plugin}]({plugin}.md) | {role} | {len(by_home.get(plugin, []))} |")

    if sep_total:
        idx += ["", "## Autre projet (hors angle M. tuberculosis)", "",
                "| Plugin | Objet | Skills propres |", "|--------|-------|----------------|"]
        for plugin in SEPARATE:
            role = clean(MTB_ANGLE.get(plugin, plugin_desc.get(plugin, "")))
            if len(role) > 150:
                role = role[:147].rstrip() + "…"
            idx.append(f"| [{plugin}]({plugin}.md) | {role} | {len(by_home.get(plugin, []))} |")

    idx += ["", "## Index alphabétique des skills", ""]
    for name in sorted(canonical):
        home = canonical[name]["home"]
        raison = canonical[name]["raison"]
        short = raison[:90].rstrip() + ("…" if len(raison) > 90 else "")
        tag = " _(autre projet)_" if home in SEPARATE else ""
        idx.append(f"- [`{name}`]({home}.md#{name}){tag} : {short}")
    (DOCS / "README.md").write_text("\n".join(idx) + "\n", encoding="utf-8")

    print(f"OK : {core_total} skills (collection M. tuberculosis) + {sep_total} (autre projet).")
    for plugin in ALL_PLUGINS:
        print(f"  {plugin:26} propres={len(by_home.get(plugin, [])):3}")


if __name__ == "__main__":
    main()
