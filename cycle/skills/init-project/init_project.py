#!/usr/bin/env python3
"""Initialize a research project with the standard structure.

Usage:
    python init_project.py <name> [--title "..."] [--at <parent-dir>]
                                  [--famille pompiers|mtbc|bio|ia|shs|cours|admin|outillage|archives|autre]
                                  [--voie article[,réponse][,réoutillage][,coordination]]
                                  [--domain generic|mtbc|bacterio|droit] [--no-classify]
                                  [--no-git] [--no-parent-gitignore]

Creates the canonical tree :
    <name>/
        CLAUDE.md, cahier_de_labo.md, etat_des_decouvertes.md, pistes.md, JOURNAL.md
        analyses/, data/, résultats/, experiments/, litterature_review/
        article/         (voie ARTICLE seulement : its own git repo, GitHub <-> Overleaf)
            main.tex, references.bib, Makefile, .gitignore
            figures/, supplementary_materials/, review/INDEX.md
        reponse/         (voie RÉPONSE seulement : brouillons du mail et notes de soutien)

Le CLAUDE.md du projet ne porte QUE le contexte scientifique, la structure et des
pointeurs (refonte P2.3, 2026-09-13) : mémoire à cinq artefacts, cycle de vie,
vérification avant calcul, pipeline manuscrit et calcul distant sont hérités de
`~/docs/codes/CLAUDE.md` (et `codes/mtbc/CLAUDE.md` pour la famille mtbc) et ne se
répètent pas dans chaque projet.

La VOIE (article, réponse, réoutillage, coordination ; cumulables) est déclarée
dans l'en-tête de `etat_des_decouvertes.md`, seule copie ; `article/` n'existe que
sur la voie article. La voie coordination sert un projet qui anime une structure
ou un collectif dans la durée (GIS, réseau, plateforme, comité) : pas de cycle en
cinq phases, pas de porte de clôture unique. La FAMILLE (rangement de `codes/`)
est inscrite dans le CLAUDE.md et sert de repli au futur profil d'activation des
plugins.

No external dependencies — stdlib only.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from textwrap import dedent


# ── identité de l'auteur, configurable (jamais un défaut qui redivulgue une identité réelle) ──

def _config_auteur() -> dict[str, str]:
    """Résout responsable/e-mail/affiliation/marketplace pour les gabarits générés.

    Ordre : variables d'environnement `CYCLE_AUTHOR_NAME`/`CYCLE_AUTHOR_EMAIL`/
    `CYCLE_AUTHOR_AFFILIATION`/`CYCLE_MARKETPLACE_NAME`, puis `~/.claude/cycle.local.md`
    (bloc `clé: valeur` simple entre deux lignes `---`, pas un frontmatter YAML complet :
    ce script reste stdlib-only), puis repli générique. Un projet créé sans configuration
    porte un placeholder qui dit comment se configurer, jamais le nom de quelqu'un d'autre.
    """
    valeurs = {
        "responsable": os.environ.get("CYCLE_AUTHOR_NAME", ""),
        "email": os.environ.get("CYCLE_AUTHOR_EMAIL", ""),
        "affiliation": os.environ.get("CYCLE_AUTHOR_AFFILIATION", ""),
        "marketplace": os.environ.get("CYCLE_MARKETPLACE_NAME", ""),
    }
    local = Path.home() / ".claude" / "cycle.local.md"
    if local.is_file() and not all(valeurs.values()):
        try:
            texte = local.read_text(encoding="utf-8")
        except OSError:
            texte = ""
        if texte.startswith("---"):
            fin = texte.find("\n---", 3)
            bloc = texte[3:fin] if fin != -1 else texte[3:]
            for ligne in bloc.splitlines():
                cle, sep, val = ligne.partition(":")
                cle, val = cle.strip(), val.strip()
                if sep and cle in valeurs and not valeurs[cle]:
                    valeurs[cle] = val
    valeurs.setdefault("marketplace", valeurs["marketplace"] or "")
    return valeurs


_AUTEUR = _config_auteur()


# ── CLAUDE.md ───────────────────────────────────────────────────────────────

# Les familles sont les répertoires RÉELS de `~/docs/codes/` : la famille des
# sciences humaines et du droit s'appelle `droit-shs` sur le disque depuis P3.3, et
# `--famille shs` cherchait donc un `codes/shs/` qui n'existe pas. L'ancien nom
# reste accepté et normalisé, pour ne pas casser une habitude ni un script.
FAMILLES = ("pompiers", "mtbc", "bio", "ia", "droit-shs", "shs", "cours", "admin",
            "outillage", "archives", "autre")
FAMILLES_ALIAS = {"shs": "droit-shs"}
# Le domaine `mtbc` porte en réalité les templates de phylogénomique bactérienne
# (macros LaTeX du groupe, conventions SPDI/RAxML-NG), valables pour tout pathogène
# clonal : seule la référence change. Le nom interne reste `mtbc` pour ne rien casser,
# `bacterio` est l'alias honnête à employer pour un projet d'un autre genre.
DOMAINES_ALIAS = {"bacterio": "mtbc"}
VOIES = ("article", "réponse", "réoutillage", "coordination")
VOIES_ALIAS = {"reponse": "réponse", "reoutillage": "réoutillage",
               "outillage": "réoutillage", "coord": "coordination"}


def parse_voies(valeur: str | None) -> tuple[str, ...]:
    """`--voie article,réoutillage` -> ('article', 'réoutillage'). Défaut : article."""
    if not valeur:
        return ("article",)
    out: list[str] = []
    for v in valeur.split(","):
        v = VOIES_ALIAS.get(v.strip().lower(), v.strip().lower())
        if v not in VOIES:
            raise ValueError(f"voie inconnue : {v!r} (attendu : {', '.join(VOIES)})")
        if v not in out:
            out.append(v)
    return tuple(out)


def deviner_famille(parent_dir: Path) -> str | None:
    """Famille déduite du chemin : `~/docs/codes/<famille>/...` -> famille, sinon None."""
    codes = Path.home() / "docs" / "codes"
    try:
        rel = parent_dir.resolve().relative_to(codes.resolve())
    except ValueError:
        return None
    tete = rel.parts[0] if rel.parts else None
    return tete if tete in FAMILLES else None


def claude_md_template(name: str, title: str, domain: str,
                       voies: tuple[str, ...] = ("article",),
                       famille: str | None = None) -> str:
    """CLAUDE.md de projet : contexte, structure, pointeurs. Rien d'hérité.

    Ce qui n'est PAS ici, et ne doit pas y revenir : cahier, état et pistes, cycle
    de vie et portes, vérification avant calcul, pipeline qualité, calcul distant.
    Tout cela vit dans `~/docs/codes/CLAUDE.md`, chargé automatiquement par toute
    session ouverte sous `codes/` (mesuré : P2.1, 2026-09-13). Le répéter ici
    ferait lire la même règle deux fois à chaque session et figerait dans 300
    projets une version qui divergerait de la source à la première retouche.
    """
    article = "article" in voies
    reponse = "réponse" in voies
    reoutillage = "réoutillage" in voies
    coordination = "coordination" in voies
    voies_txt = " + ".join(voies)

    # ── en-tête : famille, voie, héritage ──
    fam = famille or "non déclarée"
    heritage = "`~/docs/codes/CLAUDE.md`"
    if domain == "mtbc" or famille == "mtbc":
        heritage += " et `~/docs/codes/mtbc/CLAUDE.md`"
    entete = (
        f"# CLAUDE.md — {name}\n\n"
        f"**Famille :** {fam}    **Voie :** {voies_txt} (déclarée dans l'en-tête de "
        "`etat_des_decouvertes.md`, seule copie, avec la phase quand la voie est article)\n\n"
        f"Les règles de projet de recherche (mémoire à cinq artefacts, cycle et portes, "
        f"vérification avant calcul, pipeline manuscrit, calcul distant) sont héritées de "
        f"{heritage} ; ce fichier ne les répète pas et ne porte que ce qui est propre au projet.\n\n"
    )

    # ── contexte : une section par voie, ce qu'on doit savoir pour travailler ──
    contexte = ""
    if article:
        auteur_biblio = _AUTEUR["responsable"] or "(auteur à renseigner)"
        contexte += (
            "## Contexte scientifique\n\n"
            f"> **{auteur_biblio}** *{title}.* (en préparation)\n\n"
            "[Décrire ici la question de recherche, l'échantillon ou les données, ce qui est "
            "attendu, et ce qui distingue ce projet de ses voisins.]\n\n"
        )
    if reponse:
        contexte += (
            "## Demande d'origine\n\n"
            + ("" if article else f"*{title}*\n\n")
            + "[Qui a posé la question, quand, par quel canal ; ce qu'il attend exactement ; "
            "ce qui est déjà connu. Le livrable est un mail argumenté et les notes qui le "
            "soutiennent ; cette voie est close quand la réponse est partie.]\n\n"
        )
    if reoutillage:
        contexte += (
            "## Besoin technique\n\n"
            + ("" if (article or reponse) else f"*{title}*\n\n")
            + "[Quel outil, skill, fiche de connaissances ou ticket amont est en cause ; ce qui "
            "ne marche pas ou manque ; à quoi on reconnaîtra que l'outil est reforgé. Cette "
            "voie est close quand l'outil l'est.]\n\n"
        )
    if coordination:
        contexte += (
            "## Nature du projet\n\n"
            + ("" if (article or reponse or reoutillage) else f"*{title}*\n\n")
            + "[Quelle structure ou quel collectif ce projet coordonne (GIS, réseau, "
            "plateforme, comité de pilotage...) ; quels artefacts vivants il porte (site, "
            "listes de diffusion, annuaire, conventions, comptes rendus, séminaires) ; à qui "
            "il sert. Pas de porte de clôture unique : cette voie dure tant que la structure "
            "existe, elle se referme quand la structure elle-même se dissout ou change de "
            "porteur, pas quand une tâche donnée est faite.]\n\n"
        )

    # ── structure : seulement ce qui existe vraiment ──
    lignes = [
        f"{name}/",
        "├── CLAUDE.md               # ce fichier : contexte, structure, pointeurs",
        "├── cahier_de_labo.md       # append-only, horodaté",
        "├── etat_des_decouvertes.md # état consolidé ; en-tête = voie (+ phase)",
        "├── pistes.md               # arbre des directions",
        "├── JOURNAL.md              # faits horodatés (option)",
    ]
    if article:
        lignes += [
            "├── article/                # dépôt git AUTONOME (GitHub puis Overleaf) ; `make` compile",
            "│   ├── main.tex, references.bib, Makefile",
            "│   ├── figures/, supplementary_materials/",
            "│   └── review/INDEX.md",
        ]
    if reponse:
        lignes += [
            "├── reponse/                # brouillons du mail et notes de soutien",
        ]
    lignes += [
        "├── analyses/               # scripts phasés (phase1_*.py, ...)",
        "├── data/                   # données d'entrée ; documents reçus -> /corpus-ingest avant lecture",
        "├── corpus/                 # dérivé de data/ par /corpus-ingest",
        "├── résultats/              # sorties générées",
        "├── experiments/            # YYYY-MM-DD_description/",
        "└── litterature_review/     # index.md, references.bib (/lit-review)",
    ]
    structure = "## Structure du répertoire\n\n```\n" + "\n".join(lignes) + "\n```\n\n"

    # ── pointeurs : où va ce que produit le projet ──
    pointeurs = ["## Pointeurs\n"]
    if article:
        pointeurs.append(
            "- Manuscrit : `article/` ; publier par `cd article && gh repo create <repo> --private "
            "--source=. --push`, puis Overleaf -> Menu -> GitHub.")
    if reponse:
        pointeurs.append(
            "- Réponse : brouillons dans `reponse/`, version envoyée recopiée dans le cahier avec "
            "sa date ; si vous tenez un annuaire de contacts, y consulter le registre du "
            "destinataire (tutoiement, ton, historique) avant d'écrire.")
    if reoutillage:
        pointeurs.append(
            "- Outillage : un skill se crée ou se corrige à sa source, jamais dans une copie "
            "miroir ; une leçon inter-projets va dans votre base de connaissances partagée, "
            "si vous en tenez une, par `/reflect`.")
    if coordination:
        pointeurs.append(
            "- Coordination : les artefacts vivants (site, listes de diffusion, annuaire, "
            "conventions...) sont la trace principale, pas ce fichier ; le cahier consigne "
            "les décisions et échanges au fil de l'eau, `pistes.md` seulement si le volume "
            "de directions ouvertes le justifie.")
    pointeurs.append(
        "- Sérendipité : ce qui sort du périmètre va dans le `pistes.md` du répertoire parent "
        "(`/recadrage`), jamais dans une piste locale oubliée.")
    pointeurs_txt = "\n".join(pointeurs) + "\n"

    # ── conventions propres au domaine ; le reste est hérité ──
    if domain == "mtbc":
        domain_block = (
            "\n## Conventions\n\n"
            "Conventions de phylogénomique bactérienne (SPDI, H37Rv, RAxML-NG, figures) : "
            "héritées de `~/docs/codes/mtbc/CLAUDE.md`. N'ajouter ici que ce que ce projet "
            "fait autrement, avec son motif.\n"
        )
    elif domain == "droit":
        marketplace_nom = _AUTEUR["marketplace"] or "guyeux-claude-plugins"
        domain_block = (
            "\n## Conventions (projet de DROIT)\n\n"
            "**Plugin de domaine : `droit`.** Il est activé pour ce projet dans "
            "`.claude/settings.json`. Si les skills juridiques ne se chargent pas, "
            f"l'activer à la main : `/plugin` puis `droit@{marketplace_nom}`.\n\n"
            "- **Les références vont en NOTES DE BAS DE PAGE, détaillées**, jamais en "
            "appel abrégé dans le corps. Norme : celle de la thèse de Camille Aynès "
            "(référente du domaine). Le skill `/notes-et-citations` s'exécute **avant "
            "toute production de livrable**, pas après.\n"
            "- **Aucune citation de jurisprudence ou de texte normatif sans "
            "vérification** à la source officielle (`/legifrance` pour Légifrance et "
            "le Conseil constitutionnel). Un numéro de décision juste portant une "
            "citation fausse est le pire cas : il rend la note vérifiable en "
            "apparence.\n"
        )
    else:
        domain_block = ""

    return entete + contexte + structure + pointeurs_txt + domain_block


# ── cahier de labo + JOURNAL ─────────────────────────────────────────────────

def cahier_de_labo_template(name: str, title: str, project_dir: Path) -> str:
    today = date.today().isoformat()
    responsable = _AUTEUR["responsable"] or "(à renseigner — CYCLE_AUTHOR_NAME ou ~/.claude/cycle.local.md)"
    if _AUTEUR["affiliation"]:
        responsable += f" ({_AUTEUR['affiliation']})"
    return dedent(f"""\
        # Cahier de laboratoire — {name}

        **Projet :** {title}
        **Responsable :** {responsable}
        **Créé le :** {today}
        **Répertoire :** {project_dir}

        ---

        Journal append-only. Ne jamais modifier les entrées passées.
        Mise à jour via `/cahier-de-labo update`.

        ---
        """)


def journal_md_template(name: str) -> str:
    today = date.today().isoformat()
    return dedent(f"""\
        # JOURNAL — {name}

        Faits horodatés (dates, résultats, décisions, sessions de travail).
        Format : `## YYYY-MM-DD` puis liste de faits.

        ## {today}

        - Initialisation du projet via `/init-project`.
        """)


# ── état des découvertes + pistes ────────────────────────────────────────────

def cahier_maturity(project_dir: Path) -> int:
    """Nombre d'entrées du cahier de labo (0 si absent ou vide).

    Sert à ne PAS poser un squelette qui AFFIRME un état vierge sur un projet
    qui a déjà travaillé. Un état faux est pire qu'un état absent : les hooks
    Stop s'appuient ensuite dessus, et un lecteur (humain ou assistant) prend le
    squelette pour la vérité du projet. Le script ne peut pas lire le cahier au
    sens sémantique (il faudrait un modèle de langage) ; il peut en revanche
    reconnaître qu'il a quelque chose à dire et le déclarer honnêtement.
    """
    for fname in ("cahier_de_labo.md", "JOURNAL.md"):
        f = project_dir / fname
        if f.exists():
            txt = f.read_text(encoding="utf-8", errors="replace")
            n = sum(1 for line in txt.splitlines() if line.startswith("## "))
            if n:
                return n
    return 0


ENV_VERSION_SCRIPT = Path.home() / "docs" / "environnement" / "outils" / "env_version.py"


def _version_environnement_courante() -> str | None:
    """Version bumpée de l'environnement au moment de la création (piste Z2).

    Défensif à dessein : `init-project` sert bien au-delà de `~/docs/environnement`
    (274 projets sous `codes/` seul), donc un appel en subprocess plutôt qu'un import
    direct du module, et un échec (script absent, sortie inattendue, futur renommage)
    ne doit jamais empêcher la création d'un projet — juste omettre la ligne.
    """
    if not ENV_VERSION_SCRIPT.is_file():
        return None
    try:
        sortie = subprocess.run(
            ["python3", str(ENV_VERSION_SCRIPT), "etat", "--json"],
            capture_output=True, text=True, timeout=10, check=True,
        ).stdout
        v = json.loads(sortie).get("version")
        return v if isinstance(v, str) else None
    except Exception:
        return None


def etat_des_decouvertes_template(name: str, n_entrees: int = 0,
                                  voies: tuple[str, ...] = ("article",)) -> str:
    today = date.today().isoformat()
    version_env = _version_environnement_courante()
    ligne_environnement = (
        f"**Environnement :** v{version_env} (rattaché le {today})\n" if version_env else ""
    )
    voies_txt = " + ".join(voies)
    # La phase n'a de sens que sur la voie article (cycle-projet, arbitrage CG du
    # 2026-09-11) ; ailleurs elle cède la place à un état libre, sinon le hook de
    # démarrage réclame à chaque session une phase qui n'existe pas.
    if "article" in voies:
        ligne_etat = (f"**Itération :** 0    **Voie :** {voies_txt}    "
                      f"**Phase :** 1/5 — analyse primaire    **Réécrit le :** {today}")
        regle_phase = (
            "La ligne `**Phase :**` situe le projet dans son cycle de vie (cf. `/cycle-projet`) :\n"
            "1 analyse primaire, 2 valorisation et squelette, 3 itération draft, 4 finalisation\n"
            "et soumission, 5 clôture. La faire avancer seulement quand la PORTE de la phase\n"
            "courante est franchie, c'est-à-dire démontrée par un point fixe, jamais supposée.")
    elif "coordination" in voies:
        ligne_etat = (f"**Itération :** 0    **Voie :** {voies_txt}    "
                      f"**Phase :** non applicable (voie coordination, hors cycle article)    "
                      f"**Réécrit le :** {today}")
        regle_phase = (
            "Cette voie n'a pas de cycle en cinq phases : elle dure tant que la structure\n"
            "coordonnée existe, et se referme quand la structure elle-même se dissout ou\n"
            "change de porteur, pas quand une tâche donnée est faite. Pas de porte de clôture\n"
            "unique. Si le travail révèle un résultat neuf et généralisable, ajouter `article`\n"
            "à la voie, poser une `**Phase :**` et tracer la bascule dans le cahier.")
    else:
        ligne_etat = (f"**Itération :** 0    **Voie :** {voies_txt}    "
                      f"**État :** ouvert, besoin à cadrer    **Réécrit le :** {today}")
        regle_phase = (
            "Sur cette voie les cinq phases et les portes ne s'appliquent pas : la ligne\n"
            "`**État :**` dit librement où en est le livrable (réponse partie, outil reforgé,\n"
            "ticket déposé…). Si le travail révèle un résultat neuf et généralisable, ajouter\n"
            "`article` à la voie, poser une `**Phase :**` et tracer la bascule dans le cahier.")
    if n_entrees:
        placeholder = (f"[À REGÉNÉRER depuis le cahier — {n_entrees} entrées "
                       f"non encore dépouillées]")
        verdict = (
            f"NON RENSEIGNÉ. Ce squelette a été posé le {today} sur un projet qui a DÉJÀ "
            f"travaillé\n({n_entrees} entrées de cahier). Il ne décrit pas l'état réel du projet : "
            "il le réclame.\nLancer `/etat update` pour le régénérer depuis `cahier_de_labo.md` "
            "AVANT de s'y fier.")
        entete = (f"\n> ⚠ SQUELETTE NON RENSEIGNÉ, posé par `--migrate` sur un projet à "
                  f"{n_entrees} entrées de cahier.\n> Ne rien conclure de ce fichier tant que "
                  "`/etat update` n'a pas été passé.\n")
    else:
        placeholder = "[à renseigner]"
        verdict = ("Projet initialisé ; objectifs à cadrer, revue de littérature à faire "
                   "avant tout calcul.")
        entete = ""
    ligne_donnees = (
        f"**Données :** {placeholder} (skill `bdd` : citer `<store>@<version>` par base lue)\n"
        if n_entrees else "**Données :** -\n"
    )
    rien = placeholder if n_entrees else "(rien encore)"
    litterature = placeholder if n_entrees else "[à renseigner après /lit-review]"
    redemontre = placeholder if n_entrees else "—"
    # dedent AVANT substitution : les variables `entete` et `verdict` sont
    # multi-lignes et non indentées ; les interpoler d'abord ferait chuter
    # l'indentation commune à zéro et le dedent ne retirerait plus rien.
    return dedent("""\
        # État des découvertes — {name}

        {ligne_etat}
        {ligne_environnement}{ligne_donnees}Règle : fichier RÉÉCRIT en entier à chaque fin d'itération (via `/etat update`),
        régénérable depuis `cahier_de_labo.md`. Pas d'historique ici (il est dans le cahier).
        Ce fichier est LA VÉRITÉ du projet, et le reste pendant toute la rédaction : la
        littérature (dûment citée) et les résultats in silico y vivent au même niveau
        d'exigence. Chaque acquis de §2 porte une `destination :` A (article en cours) / B
        (second papier) / C (essaimé hors projet) / D (classé), attribuée par `/recadrage`.
        {regle_phase}
        {entete}
        ## 1. Question de recherche et objectifs (évolutifs)
        - Objectif principal : {placeholder}
        - Sous-objectifs : {placeholder}

        ## 2. Acquis — ce qui est démontré
        - {rien}

        ## 3. Réfuté / écarté
        - {rien}

        ## 4. Incertain / en cours d'arbitrage
        - {rien}

        ## 5. Position vs littérature
        - Nouveau par rapport à l'état de l'art : {litterature}
        - Re-démontré (déjà publié) : {redemontre}

        ## 6. Grandes directions en cours
        - {placeholder}

        ## 7. Angles morts / contre-arguments non levés
        - {placeholder}

        ## 8. Verdict en une phrase
        {verdict}

        ## 9. Hors périmètre — essaimé / classé
        - néant à ce jour
        """).format(name=name, ligne_etat=ligne_etat, ligne_environnement=ligne_environnement,
                    ligne_donnees=ligne_donnees,
                    regle_phase=regle_phase, entete=entete,
                    placeholder=placeholder, rien=rien, litterature=litterature,
                    redemontre=redemontre, verdict=verdict)


def pistes_template(name: str, n_entrees: int = 0,
                    voies: tuple[str, ...] = ("article",)) -> str:
    today = date.today().isoformat()
    if n_entrees:
        return dedent(f"""\
            # Pistes — {name}

            Règle : édité par mutation locale (jamais réécrit en bloc), uniquement via `/pistes`.
            Une piste [réalisé]/[abandonné] n'est jamais supprimée (traçabilité).
            États : [à faire] [en cours] [réalisé] [abandonné].
            Une direction qui ne relève PLUS de ce projet ne vient pas ici : elle va dans le
            `pistes.md` du répertoire parent, format `[SÉRENDIPITÉ ← {name}]` (cf. `/recadrage`).

            > ⚠ SQUELETTE NON RENSEIGNÉ, posé par `--migrate` sur un projet à {n_entrees} entrées
            > de cahier. Les pistes réelles de ce projet sont dans `cahier_de_labo.md`
            > (sections « Points ouverts » et « Suite suggérée » de chaque entrée) et n'ont pas
            > encore été remontées ici. Lancer `/pistes` pour les reconstruire.

            ## P0. Reconstruire cet arbre depuis le cahier [à faire]
              origine : /init-project --migrate    maj : {today}
              - P0.1 Dépouiller les {n_entrees} entrées du cahier, en extraire les directions
                    ouvertes et leur donner une ligne dédiée ici [à faire]
              - P0.2 Régénérer `etat_des_decouvertes.md` via `/etat update` [à faire]
              - P0.3 Supprimer ce bloc P0 une fois l'arbre reconstruit (c'est la seule
                    exception à la règle de non-suppression : P0 est un échafaudage,
                    pas une piste de recherche) [à faire]
            """)
    tete = dedent(f"""\
        # Pistes — {name}

        Règle : édité par mutation locale (jamais réécrit en bloc), uniquement via `/pistes`.
        Une piste [réalisé]/[abandonné] n'est jamais supprimée (traçabilité).
        États : [à faire] [en cours] [réalisé] [abandonné].
        Une direction qui ne relève PLUS de ce projet ne vient pas ici : elle va dans le
        `pistes.md` du répertoire parent, format `[SÉRENDIPITÉ ← {name}]` (cf. `/recadrage`).

        """)
    # Le premier bloc dépend du livrable : la revue de littérature et la porte 1 sont
    # le premier geste d'un ARTICLE ; une RÉPONSE commence par cerner la demande ; un
    # RÉOUTILLAGE, par reproduire le défaut. Un projet à plusieurs voies reçoit un
    # bloc par voie, numérotés P1, P2, ...
    blocs = []
    if "article" in voies:
        blocs.append(dedent(f"""\
        ## P{{n}}. PHASE 1 — Revue de littérature initiale et cadrage des objectifs [à faire]
          origine : /init-project    maj : {today}
          Premier geste du cycle de vie (cf. `/cycle-projet`) : rien ne se calcule avant.
          - P{{n}}.1 Faire /lit-review sur le sujet central AVANT tout calcul [à faire]
          - P{{n}}.2 Renseigner les objectifs dans etat_des_decouvertes.md §1 [à faire]
          - P{{n}}.3 Ouvrir les premières pistes techniques depuis ce que la revue a montré
                manquant, chacune passée au crible /challenge avant lancement [à faire]
          - P{{n}}.4 PORTE 1 : point fixe d'analyse — deux tours à vide consécutifs
                (/mtbc-prospect ne rend rien d'instruisible, /lit-review n'ouvre aucun
                angle neuf, aucune piste technique ouverte). Ne PAS commencer à rédiger
                avant. Passer alors la phase à 2/5 dans l'en-tête de l'état [à faire]
        """))
    if "réponse" in voies:
        blocs.append(dedent(f"""\
        ## P{{n}}. RÉPONSE — Comprendre la demande et y répondre [à faire]
          origine : /init-project --voie réponse    maj : {today}
          Le livrable est un mail argumenté et ses notes ; fini quand la réponse est partie.
          - P{{n}}.1 Reformuler la question posée, le destinataire, ce qu'il attend et pour
                quand ; si vous tenez un annuaire de contacts, y relire sa fiche pour le
                registre [à faire]
          - P{{n}}.2 Vérifier ce qui est déjà su : KB inter-projets, cahiers voisins, littérature
                (/lit-review court si la question est scientifique) [à faire]
          - P{{n}}.3 Faire ce qui manque pour répondre, chaque calcul passé au crible /challenge
                et consigné au cahier [à faire]
          - P{{n}}.4 Rédiger la réponse dans `reponse/` au registre du destinataire, la faire
                valider, l'envoyer, recopier la version partie dans le cahier avec sa date ;
                si la mesure faite s'avère neuve et généralisable, ajouter `article` à la voie
                dans l'en-tête de l'état et ouvrir la phase 1 [à faire]
        """))
    if "réoutillage" in voies:
        blocs.append(dedent(f"""\
        ## P{{n}}. RÉOUTILLAGE — Reforger l'outil [à faire]
          origine : /init-project --voie réoutillage    maj : {today}
          Le livrable est un skill créé ou corrigé, une fiche KB, un ticket amont ; fini quand
          l'outil est reforgé et son test passe.
          - P{{n}}.1 Reproduire le défaut ou cerner le besoin par un cas minimal rejouable,
                consigné au cahier [à faire]
          - P{{n}}.2 Vérifier ce qui existe déjà : skill homonyme ou voisin, fiche KB,
                bug déjà documenté [à faire]
          - P{{n}}.3 Corriger ou créer à sa source, jamais dans une copie miroir, avec un
                test de non-régression rejouable [à faire]
          - P{{n}}.4 Consigner la leçon (/reflect vers la KB, ticket chez qui détient le code
                si l'amont est externe) et passer l'État de l'en-tête à « outil reforgé » ;
                si le travail a révélé un résultat neuf et généralisable, ajouter `article` à la
                voie et ouvrir la phase 1 [à faire]
        """))
    if "coordination" in voies:
        blocs.append(dedent(f"""\
        ## P{{n}}. COORDINATION — Structurer le suivi [à faire]
          origine : /init-project --voie coordination    maj : {today}
          Le livrable est l'ensemble vivant des artefacts de communication et de gouvernance
          de la structure coordonnée ; pas de porte de clôture unique, cette voie dure tant
          que la structure existe.
          - P{{n}}.1 Lister les artefacts à tenir à jour (site, listes de diffusion, annuaire,
                conventions, comptes rendus, séminaires...) et leur état actuel [à faire]
          - P{{n}}.2 Identifier les verrous externes en cours (juridique, institutionnel,
                technique) et qui peut les lever [à faire]
          - P{{n}}.3 Si un travail mené ici révèle un résultat neuf et généralisable, ajouter
                `article` à la voie dans l'en-tête de l'état et ouvrir la phase 1 [à faire]
        """))
    corps = "\n".join(b.replace("{n}", str(i)) for i, b in enumerate(blocs, start=1))
    return tete + corps


# ── article/main.tex ─────────────────────────────────────────────────────────

def latex_escape(text: str) -> str:
    """Échapper les caractères actifs de LaTeX dans un texte injecté tel quel.

    Indispensable : un nom de projet contenant un underscore (`L4_15`,
    `NTM_unidentified`, `animal_vs_human`…) produisait un `main.tex` qui
    déclenche « Missing $ inserted » dès la première compilation, car `_` est
    l'indice mathématique. Le PDF sortait quand même en `-interaction=
    nonstopmode`, ce qui masquait le défaut, mais toute compilation stricte
    (`-halt-on-error`, latexmk, Overleaf) échouait.

    Le backslash est traité en premier, sinon les remplacements suivants
    seraient eux-mêmes ré-échappés.
    """
    out = text.replace("\\", r"\textbackslash{}")
    for char in ("&", "%", "$", "#", "_", "{", "}"):
        out = out.replace(char, "\\" + char)
    out = out.replace("~", r"\textasciitilde{}")
    out = out.replace("^", r"\textasciicircum{}")
    return out


def main_tex_template(name: str, title: str, domain: str) -> str:
    name_tex = latex_escape(name)
    title_tex = latex_escape(title)
    auteur_tex = latex_escape(_AUTEUR["responsable"]) if _AUTEUR["responsable"] else "Auteur (a renseigner)"
    affiliation_tex = (latex_escape(_AUTEUR["affiliation"]) if _AUTEUR["affiliation"]
                        else "Affiliation a renseigner")
    email_tex = _AUTEUR["email"] or "you@example.com"

    if domain == "mtbc":
        domain_macros = (
            r"\newcommand{\mtb}{\textit{Mycobacterium tuberculosis}}" + "\n"
            r"\newcommand{\spdi}[1]{\texttt{#1}}" + "\n"
            r"\newcommand{\lignee}[1]{\textsf{#1}}" + "\n"
        )
        domain_keywords = (
            r"\textit{Mycobacterium tuberculosis}, MTBC, "
            f"\\lignee{{{name_tex}}}, "
            r"phylogenomics, TBannotator"
        )
    else:
        domain_macros = ""
        domain_keywords = name_tex

    return (
        "\\documentclass[11pt,a4paper]{article}\n\n"
        "% -- Encodage et langue --\n"
        "\\usepackage[utf8]{inputenc}\n"
        "\\usepackage[T1]{fontenc}\n"
        "\\usepackage[english]{babel}\n"
        "% Caracteres Unicode grecs / fleches presents dans certains titres de\n"
        "% references.bib (ex. TGF-beta) que la fonte T1 ne rend pas par defaut.\n"
        "\\DeclareUnicodeCharacter{03B1}{\\ensuremath{\\alpha}}\n"
        "\\DeclareUnicodeCharacter{03B2}{\\ensuremath{\\beta}}\n"
        "\\DeclareUnicodeCharacter{03B3}{\\ensuremath{\\gamma}}\n"
        "\\DeclareUnicodeCharacter{0394}{\\ensuremath{\\Delta}}\n"
        "\\DeclareUnicodeCharacter{03BA}{\\ensuremath{\\kappa}}\n"
        "\\DeclareUnicodeCharacter{2194}{\\ensuremath{\\leftrightarrow}}\n\n"
        "% -- Mise en page --\n"
        "\\usepackage[margin=2.5cm]{geometry}\n"
        "\\usepackage{setspace}\n"
        "\\onehalfspacing\n\n"
        "% -- Packages scientifiques --\n"
        "\\usepackage{amsmath,amssymb}\n"
        "\\usepackage{graphicx}\n"
        "\\usepackage{booktabs}\n"
        "\\usepackage{longtable}\n"
        "\\usepackage{multirow}\n"
        "\\usepackage{xcolor}\n"
        "\\usepackage{placeins}\n"
        "\\usepackage{lineno}\n"
        "\\usepackage{hyperref}\n"
        "\\hypersetup{\n"
        "    colorlinks=true,\n"
        "    linkcolor=blue!60!black,\n"
        "    citecolor=green!50!black,\n"
        "    urlcolor=blue!70!black\n"
        "}\n\n"
        "% -- Bibliographie --\n"
        "\\usepackage[numbers,sort&compress]{natbib}\n\n"
        "% -- Commandes personnalisees --\n"
        "\\newcommand{\\todo}[1]{\\textcolor{red}{\\textbf{[TODO: #1]}}}\n"
        + domain_macros + "\n"
        f"\\title{{{title_tex}}}\n\n"
        f"\\author{{{auteur_tex}$^{{1,*}}$\\\\[6pt]\n"
        "  \\parbox{\\textwidth}{\\centering\\small\n"
        f"    $^{{1}}${affiliation_tex}\\\\[3pt]\n"
        f"    $^{{*}}$Corresponding author: \\texttt{{{email_tex}}}\n"
        "  }\n"
        "}\n\n"
        "\\date{}\n\n"
        "% ===========================================================\n"
        "\\begin{document}\n"
        "\\linenumbers\n"
        "\\maketitle\n\n"
        "\\begin{abstract}\n"
        "\\todo{Write abstract}\n"
        "\\end{abstract}\n\n"
        f"\\textbf{{Keywords:}} {domain_keywords}\n\n"
        "\\section{Introduction}\n\n"
        "\\todo{Write introduction}\n\n"
        "\\section{Materials and Methods}\n\n"
        "\\todo{Describe data and pipeline}\n\n"
        "\\section{Results}\n\n"
        "\\todo{Write results}\n\n"
        "\\section{Discussion}\n\n"
        "\\todo{Write discussion}\n\n"
        "\\section{Conclusion}\n\n"
        "\\todo{Write conclusion}\n\n"
        "\\bibliographystyle{unsrtnat}\n"
        "\\bibliography{references}\n\n"
        "\\end{document}\n"
    )


MAKEFILE = dedent(
    "# Makefile for article compilation\n"
    "# Usage: make        -> compile PDF\n"
    "#        make clean  -> remove build artifacts\n"
    "#        make watch  -> continuous compilation (requires latexmk)\n"
    "\n"
    "MAIN = main\n"
    "\n"
    ".PHONY: all clean watch view\n"
    "\n"
    "all: $(MAIN).pdf\n"
    "\n"
    "# -halt-on-error est INDISPENSABLE : en nonstopmode seul, pdflatex signale\n"
    "# l'erreur mais continue et produit un PDF defectueux avec un retour 0, donc\n"
    "# make ne bloque pas et le defaut passe inapercu. Les warnings de reference\n"
    "# ou citation non definie ne stoppent pas : le flux 3 passes reste sur.\n"
    "$(MAIN).pdf: $(MAIN).tex references.bib\n"
    "\tpdflatex -interaction=nonstopmode -halt-on-error $(MAIN).tex\n"
    "\tbibtex $(MAIN) || true\n"
    "\tpdflatex -interaction=nonstopmode -halt-on-error $(MAIN).tex\n"
    "\tpdflatex -interaction=nonstopmode -halt-on-error $(MAIN).tex\n"
    "\n"
    "# Convention du groupe : jamais `rm`, toujours la corbeille (gio trash).\n"
    "# gio trash echoue sur les montages systemes (tmpfs) : on le signale au\n"
    "# lieu de le taire, le fichier est alors conserve.\n"
    "clean:\n"
    "\t@for f in $(MAIN).pdf $(MAIN).aux $(MAIN).log $(MAIN).out \\\n"
    "\t\t$(MAIN).toc $(MAIN).bbl $(MAIN).blg $(MAIN).nav $(MAIN).snm \\\n"
    "\t\t$(MAIN).fls $(MAIN).fdb_latexmk $(MAIN).synctex.gz; do \\\n"
    "\t\t[ -e \"$$f\" ] || continue; \\\n"
    "\t\tgio trash \"$$f\" || echo \"clean: $$f conserve (gio trash indisponible ici)\"; \\\n"
    "\tdone\n"
    "\n"
    "watch:\n"
    "\tlatexmk -pdf -pvc -interaction=nonstopmode $(MAIN).tex\n"
    "\n"
    "view: $(MAIN).pdf\n"
    "\txdg-open $(MAIN).pdf 2>/dev/null || open $(MAIN).pdf\n"
)


ARTICLE_GITIGNORE = dedent("""\
    # LaTeX build artifacts
    *.aux
    *.bbl
    *.blg
    *.fdb_latexmk
    *.fls
    *.log
    *.out
    *.synctex.gz
    *.toc
    *.nav
    *.snm
    *.dvi
    main.pdf

    # Editor / OS
    .DS_Store
    *.swp
    *.swo
    """)


PARENT_GITIGNORE_LINES = [
    "# article/ is its own git repo (paired with GitHub <-> Overleaf)",
    "article/",
]


def review_index_template() -> str:
    today = date.today().isoformat()
    return dedent(f"""\
        # Index des reviews

        **Créé le :** {today}

        | Date | Score | Fichier | Résumé |
        |------|-------|---------|--------|
        """)


def litterature_review_index(name: str) -> str:
    today = date.today().isoformat()
    return dedent(f"""\
        # Revue de littérature

        **Projet :** {name}
        **Créé le :** {today}
        **Dernière mise à jour :** {today}

        ## Sujets explorés

        | Sujet | Fichier | Articles | Dernière exploration | Directions couvertes |
        |-------|---------|----------|----------------------|----------------------|

        ## Statistiques

        - Articles totaux dans references.bib : 0
        - Sujets explorés : 0
        - Dernière exploration : —
        """)


REFERENCES_BIB = dedent("""\
    % Bibliography for this project
    % Add BibTeX entries below
    """)


# ── Découverte : KB, projets voisins, piste source ──────────────────────────
#
# Un bon `/init-project` ne scaffold pas dans le vide : avant de créer de la
# matière neuve, il regarde ce qui existe déjà (connaissances inter-projets,
# projets voisins) et, si le projet naît d'une piste déjà écrite quelque part
# (`mtbc/pistes.md` en particulier), il en récupère le texte au lieu de faire
# repartir l'utilisateur d'une page blanche — et il MARQUE cette piste comme
# migrée, sinon le registre source affirme encore une direction ouverte alors
# qu'elle a un foyer désormais. Le script ne fait AUCUNE lecture sémantique
# (pas de LLM ici) : c'est un grep de mots-clés, honnêtement annoncé comme tel,
# à vérifier à la main — pas une preuve de doublon ou de pertinence.

STOPWORDS = {
    "the", "and", "for", "with", "from", "this", "that", "projet", "project",
    "etude", "étude", "analyse", "analysis", "sur", "dans", "des", "les",
    "une", "un", "de", "du", "la", "le", "et", "en", "au", "aux", "pour",
    "par", "est", "son", "sa", "ses", "of", "to", "vers", "avec", "sans",
}

# Mots omniprésents dans le boilerplate `--domain mtbc` (cf. claude_md_template /
# main_tex_template : "Mycobacterium tuberculosis, MTBC" apparaît dans le CLAUDE.md
# de CHAQUE projet mtbc). Sans ce filtre, le scan de projets voisins ne renvoie que
# du bruit sur un dépôt à 130+ projets MTBC : vécu le 2026-08-12, où "tuberculosis"
# seul a noyé les deux vrais signaux (deux projets réellement adjacents) sous une
# centaine de faux positifs partageant juste le mot du domaine.
MTBC_STOPWORDS = frozenset({
    "tuberculosis", "mycobacterium", "mtbc", "lineage", "lineages", "complex",
    "genomics", "phylogenomics", "strain", "strains",
})


def extract_keywords(*texts: str, extra_stopwords: frozenset[str] = frozenset()) -> list[str]:
    """Mots-clés grossiers (>=4 caractères, hors stopwords) tirés de textes.

    Base de tout le reste de cette section : pas de NLP, juste des tokens à
    faire correspondre par sous-chaîne. Volontairement permissif (les
    faux positifs sont pour l'humain à trier, pas pour le script à éliminer) —
    mais `extra_stopwords` existe pour retirer le bruit STRUCTUREL d'un corpus
    donné (ex. le boilerplate de domaine), qui n'est pas un faux positif à
    trier au cas par cas mais un défaut systématique du signal lui-même.
    """
    tokens: set[str] = set()
    for text in texts:
        for tok in re.split(r"[^A-Za-zÀ-ÿ0-9]+", text.lower()):
            if len(tok) >= 4 and tok not in STOPWORDS and tok not in extra_stopwords:
                tokens.add(tok)
    return sorted(tokens)


def scan_knowledge_base(keywords: list[str]) -> list[tuple[str, str, list[str]]]:
    """Cherche les mots-clés dans l'INDEX `~/.claude/knowledge/KNOWLEDGE.md`.

    Lit l'index curaté, pas les fichiers de détail : l'index est déjà la
    synthèse à un paragraphe par domaine, donc le bon niveau pour un grep de
    mots-clés. Renvoie (libellé, fichier, mots-clés touchés) par entrée.
    """
    kb_index = Path("~/.claude/knowledge/KNOWLEDGE.md").expanduser()
    if not keywords or not kb_index.exists():
        return []
    hits = []
    for line in kb_index.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.startswith("- ["):
            continue
        low = line.lower()
        matched = [kw for kw in keywords if kw in low]
        if matched:
            m = re.match(r"- \[([^\]]+)\]\(([^)]+)\)", line)
            label = m.group(1) if m else line[:60]
            fname = m.group(2) if m else "?"
            hits.append((label, fname, matched))
    return hits


def scan_sibling_projects(parent_dir: Path, new_name: str,
                          keywords: list[str]) -> list[tuple[str, list[str]]]:
    """Cherche un chevauchement de mots-clés avec les `CLAUDE.md` voisins.

    « Voisin » = autre répertoire direct de `parent_dir` portant un
    `CLAUDE.md`. Un chevauchement n'est PAS une preuve de doublon (deux
    projets sur le même gène, une méthode partagée...) : c'est un signal à
    vérifier avant de créer un projet redondant, pas un verdict automatique.
    """
    hits = []
    if not keywords or not parent_dir.exists():
        return hits
    for sibling in sorted(parent_dir.iterdir()):
        if not sibling.is_dir() or sibling.name == new_name or sibling.name.startswith("."):
            continue
        cl = sibling / "CLAUDE.md"
        if not cl.exists():
            continue
        try:
            txt = cl.read_text(encoding="utf-8", errors="replace").lower()
        except OSError:
            continue
        matched = [kw for kw in keywords if kw in txt]
        if matched:
            hits.append((sibling.name, matched))
    # Trié par nombre de mots-clés touchés, décroissant : sur un dépôt à 100+
    # projets, un ordre alphabétique noie les vrais signaux (plusieurs
    # correspondances) sous la masse des coïncidences à un seul mot (vécu
    # 2026-08-12). Le nombre de matches n'est toujours qu'un indice, pas une
    # preuve, mais un ordre par pertinence décroissante reste strictement plus
    # utile qu'un ordre alphabétique.
    hits.sort(key=lambda h: len(h[1]), reverse=True)
    return hits


HEADER_MAX_CHARS = 400
SCRIPT_SCAN_MAX_FILES = 600


def read_script_header(path: Path, max_chars: int = HEADER_MAX_CHARS) -> str | None:
    """Extrait le docstring de module en tête d'un script — jamais le corps.

    Renvoie None si le fichier ne commence pas par un docstring (triple
    quote) reconnaissable : c'est le signal « pas d'en-tête normalisée »,
    pas une erreur. Convention détaillée dans
    `~/.agents/knowledge/python-patterns.md` (entrée du 2026-08-26) : un
    script sans en-tête n'est pas rétrofité en masse, elle se crée la
    première fois qu'un agent lit ce script en entier pour une autre raison.
    """
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    stripped = text.lstrip()
    for quote in ('"""', "'''"):
        if stripped.startswith(quote):
            end = stripped.find(quote, len(quote))
            if end == -1:
                return None
            return stripped[len(quote):end].strip()[:max_chars]
    return None


def scan_sibling_scripts(parent_dir: Path, new_name: str, keywords: list[str],
                         max_files: int = SCRIPT_SCAN_MAX_FILES
                         ) -> tuple[list[tuple[str, str, str, list[str]]],
                                    list[tuple[str, str]]]:
    """Cherche un chevauchement de mots-clés dans les EN-TÊTES des scripts voisins.

    Ne lit jamais le corps d'un script pour juger de sa pertinence — seule
    son en-tête (docstring de module) est comparée aux mots-clés, ce qui
    garde ce scan bon marché même sur un dépôt à 100+ projets. Renvoie deux
    listes : (a) les scripts AVEC en-tête dont l'en-tête chevauche les
    mots-clés — (projet, chemin relatif, en-tête, mots-clés touchés) — et
    (b) les scripts SANS en-tête dont seul le NOM DE FICHIER chevauche les
    mots-clés — (projet, chemin relatif), à inspecter manuellement, backfill
    différé au prochain `Read` complet plutôt que forcé ici.
    """
    hits: list[tuple[str, str, str, list[str]]] = []
    missing: list[tuple[str, str]] = []
    if not keywords or not parent_dir.exists():
        return hits, missing
    scanned = 0
    for sibling in sorted(parent_dir.iterdir()):
        if not sibling.is_dir() or sibling.name == new_name or sibling.name.startswith("."):
            continue
        candidates: list[Path] = []
        analyses = sibling / "analyses"
        if analyses.is_dir():
            candidates.extend(analyses.rglob("*.py"))
        candidates.extend(sibling.glob("*.py"))
        for script in candidates:
            if scanned >= max_files:
                break
            scanned += 1
            rel = str(script.relative_to(sibling))
            header = read_script_header(script)
            if header:
                low = header.lower()
                matched = [kw for kw in keywords if kw in low]
                if matched:
                    hits.append((sibling.name, rel, header, matched))
            else:
                matched = [kw for kw in keywords if kw in script.name.lower()]
                if matched:
                    missing.append((sibling.name, rel))
        if scanned >= max_files:
            break
    hits.sort(key=lambda h: len(h[3]), reverse=True)
    return hits, missing


def print_discovery_report(name: str, title: str, parent_dir: Path,
                           domain: str = "generic") -> None:
    """Affiche le scan KB / projets voisins / scripts voisins, jamais silencieux.

    Un scan qui ne trouve rien le DIT explicitement (pas de silence
    ambigu entre « rien cherché » et « rien trouvé »).
    """
    extra = MTBC_STOPWORDS if domain == "mtbc" else frozenset()
    keywords = extract_keywords(name, title, extra_stopwords=extra)
    print()
    print(f"  Mots-clés retenus pour la découverte : {', '.join(keywords) or '(aucun)'}")

    kb_hits = scan_knowledge_base(keywords)
    if kb_hits:
        print("  Connaissances potentiellement pertinentes (~/.claude/knowledge/) :")
        for label, fname, matched in kb_hits:
            print(f"    - {label} ({fname}) — mots-clés : {', '.join(matched)}")
        print("    -> lire AVANT de commencer ; ne pas re-dériver ce qui y est déjà documenté.")
    else:
        print("  (aucune entrée de KNOWLEDGE.md ne correspond aux mots-clés du projet)")

    sibling_hits = scan_sibling_projects(parent_dir, name, keywords)
    if sibling_hits:
        TOP_N = 10
        print("  Projets voisins avec chevauchement de mots-clés (triés par nb de mots-clés, "
              "à vérifier, pas une preuve de doublon) :")
        for pname, matched in sibling_hits[:TOP_N]:
            print(f"    - {pname} — mots-clés : {', '.join(matched)}")
        if len(sibling_hits) > TOP_N:
            print(f"    ... + {len(sibling_hits) - TOP_N} autres avec un chevauchement plus faible "
                  "(non affichés, pas cachés : comptés ici)")
        print("    -> si l'un d'eux couvre déjà cet objet, envisager de l'étendre plutôt que d'en créer un nouveau.")
    else:
        print("  (aucun projet voisin avec chevauchement de mots-clés détecté)")

    script_hits, script_missing = scan_sibling_scripts(parent_dir, name, keywords)
    if script_hits:
        TOP_N = 10
        print("  Scripts voisins (analyses/) dont l'EN-TÊTE chevauche les mots-clés — "
              "en-tête affichée telle quelle, pas de lecture du corps nécessaire à ce stade :")
        for pname, rel, header, matched in script_hits[:TOP_N]:
            first_line = header.splitlines()[0] if header else ""
            print(f"    - {pname}/{rel} — mots-clés : {', '.join(matched)}")
            print(f"        {first_line}")
        if len(script_hits) > TOP_N:
            print(f"    ... + {len(script_hits) - TOP_N} autres avec un chevauchement plus faible "
                  "(non affichés, pas cachés : comptés ici)")
        print("    -> si l'un d'eux couvre déjà ce besoin, l'étendre ou l'appeler plutôt que d'en réécrire un.")
    else:
        print("  (aucun script voisin avec en-tête chevauchant les mots-clés détecté)")
    if script_missing:
        TOP_N = 10
        print(f"  {len(script_missing)} script(s) voisin(s) sans en-tête normalisée mais dont le NOM "
              "chevauche les mots-clés (à inspecter manuellement — l'en-tête sera créée la prochaine "
              "fois qu'un agent lira ce script en entier, jamais en rétrofit de masse) :")
        for pname, rel in script_missing[:TOP_N]:
            print(f"    - {pname}/{rel}")
        if len(script_missing) > TOP_N:
            print(f"    ... + {len(script_missing) - TOP_N} autres (non affichés, pas cachés : comptés ici)")


def find_piste_block(registry_text: str, piste_id: str):
    """Localise le bloc d'une piste `## P<n>. ...` dans un texte de pistes.md.

    Renvoie (bloc, début, fin) en indices caractères — le bloc va de la ligne
    `## P<n>.` jusqu'à la ligne précédant la prochaine `## P<m>.` (ou la fin du
    fichier). Renvoie None si l'id n'est pas trouvé.
    """
    lines = registry_text.splitlines(keepends=True)
    start_idx = None
    for i, line in enumerate(lines):
        if re.match(rf"^## {re.escape(piste_id)}\.", line):
            start_idx = i
            break
    if start_idx is None:
        return None
    end_idx = len(lines)
    for j in range(start_idx + 1, len(lines)):
        if re.match(r"^## P\d+\.", lines[j]):
            end_idx = j
            break
    block = "".join(lines[start_idx:end_idx])
    start_char = sum(len(l) for l in lines[:start_idx])
    end_char = sum(len(l) for l in lines[:end_idx])
    return block, start_char, end_char


def mark_piste_migrated(registry_path: Path, piste_id: str, new_project: str) -> str:
    """Marque une piste comme migrée, par MUTATION LOCALE — jamais de réécriture
    du fichier entier (cf. convention `/pistes` : une piste n'est jamais
    supprimée). Le tag `[à faire]`/`[en cours]` de la ligne de titre passe à
    `[abandonné]` (l'état `[réalisé]` n'est jamais rétrogradé) et une ligne de
    migration est insérée juste après ; rien d'autre du bloc n'est modifié.
    """
    today = date.today().isoformat()
    text = registry_path.read_text(encoding="utf-8")
    found = find_piste_block(text, piste_id)
    if found is None:
        return f"⚠ {piste_id} introuvable dans {registry_path} — rien modifié."
    block, start, end = found
    lines = block.splitlines(keepends=True)
    title_line = lines[0]
    if re.search(r"\[(à faire|en cours)\]\s*\n?$", title_line):
        lines[0] = re.sub(r"\[(à faire|en cours)\](\s*\n?)$",
                           r"[abandonné]\2", title_line)
    migration_note = (
        f"  MIGRÉ vers {new_project} ({today}) — raison : matière jugée suffisante "
        f"pour un projet autonome (`/init-project --from-piste {piste_id}`)\n"
    )
    insert_at = 2 if len(lines) > 1 and "origine" in lines[1] else 1
    lines.insert(insert_at, migration_note)
    new_text = text[:start] + "".join(lines) + text[end:]
    registry_path.write_text(new_text, encoding="utf-8")
    return f"✔ {piste_id} marquée [abandonné] + note de migration dans {registry_path}"


def seed_from_piste(project_dir: Path, piste_block: str, piste_id: str) -> None:
    """Recopie le texte d'une piste source dans une première entrée de cahier.

    Objectif : la matière qui a justifié la création du projet ne doit jamais
    passer derrière un squelette vide. Le texte brut est conservé tel quel
    (aucune synthèse ici, le script ne lit pas sémantiquement) ; le dépouillement
    vers `etat_des_decouvertes.md` reste un geste humain/assistant via `/etat update`.
    """
    today = date.today().isoformat()
    cahier = project_dir / "cahier_de_labo.md"
    entry = (
        f"\n## {today} — Reprise de la piste {piste_id}\n\n"
        f"Projet créé via `/init-project --from-piste {piste_id}` à partir du texte "
        "suivant, recopié tel quel pour ne rien en perdre :\n\n"
        "```markdown\n" + piste_block.rstrip() + "\n```\n\n"
        "À faire : dépouiller ce texte pour renseigner `etat_des_decouvertes.md` "
        "(§1 objectifs, §2 acquis) via `/etat update`, et recréer les sous-pistes de "
        f"{piste_id} dans le `pistes.md` de CE projet, renumérotées, en conservant "
        "leur `origine:` d'origine.\n"
    )
    with cahier.open("a", encoding="utf-8") as f:
        f.write(entry)


# ── Project creation ─────────────────────────────────────────────────────────

def init_article_git_repo(article_dir: Path) -> tuple[bool, str]:
    """Initialize git in article/ and create an initial commit.

    Returns (ok, message). If git is not available or the user has no
    git identity configured, returns ok=False with a hint.
    """
    try:
        subprocess.run(
            ["git", "init", "-q", "-b", "main"],
            cwd=article_dir, check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        return False, f"git init failed: {exc}"

    # Check identity is configured (user.name + user.email)
    try:
        name = subprocess.run(
            ["git", "config", "--get", "user.name"],
            cwd=article_dir, capture_output=True, text=True,
        ).stdout.strip()
        email = subprocess.run(
            ["git", "config", "--get", "user.email"],
            cwd=article_dir, capture_output=True, text=True,
        ).stdout.strip()
    except Exception:
        name, email = "", ""

    if not name or not email:
        return False, (
            "git identity not configured. The repo was initialized but no "
            "initial commit was made. Run :\n"
            "  git config --global user.name  \"Your Name\"\n"
            "  git config --global user.email \"you@example.com\"\n"
            f"then : cd {article_dir} && git add . && "
            "git commit -m 'Initial scaffold'"
        )

    try:
        subprocess.run(["git", "add", "."], cwd=article_dir, check=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", "Initial article scaffold"],
            cwd=article_dir, check=True,
        )
    except subprocess.CalledProcessError as exc:
        return False, f"initial commit failed: {exc}"
    return True, "git repo initialized with one commit on branch 'main'"


def update_parent_gitignore(parent_dir: Path) -> str:
    """Append `article/` to parent .gitignore (creating it if needed).

    Returns a one-line status.
    """
    gi = parent_dir / ".gitignore"
    existing = gi.read_text(encoding="utf-8") if gi.exists() else ""
    if "article/" in existing.splitlines():
        return f"{gi}: already ignores article/"
    block = "\n".join(PARENT_GITIGNORE_LINES) + "\n"
    if existing and not existing.endswith("\n"):
        block = "\n" + block
    gi.write_text(existing + block, encoding="utf-8")
    return f"{gi}: appended `article/`"


# ── CLASSIFIEUR DE DOMAINE ───────────────────────────────────────────────────
#
# POURQUOI. Les projets de cet environnement sont massivement biologiques, et un
# projet de DROIT y demande des conventions incompatibles : références détaillées
# en notes de bas de page, vérification des citations de jurisprudence, style de
# la doctrine. Charger le mauvais outillage n'est pas neutre — un projet de droit
# rédigé avec les conventions d'un article de génomique se relit intégralement.
#
# COMMENT IL PEUT SE TROMPER, et ce qui est fait contre.
# (a) Faux POSITIF : le vocabulaire juridique déborde largement le droit
#     (« code », « article », « loi », « sanction » sont partout en science).
#     Parade : ces mots-là ne comptent pas, le lexique fort ne retient que ce qui
#     n'a pas d'autre emploi crédible ici (QPC, Légifrance, Conseil d'État…), et
#     un ANTI-LEXIQUE biologique oppose son veto.
# (b) Faux NÉGATIF : un projet de droit dont le nom ne dit rien. Parade : on lit
#     aussi le titre et, en migration, le contenu du répertoire.
# (c) Le pire, un classifieur MUET : il déciderait sans qu'on puisse le
#     contredire. Parade : il AFFICHE toujours ses preuves (les termes trouvés et
#     où), il ne bascule jamais en silence, et `--domain` explicite le désarme.
#
# Le seuil ci-dessous est un JUGEMENT, pas une mesure : deux termes forts
# distincts au moins, et un score d'au moins quatre. Il est réglé pour rater un
# projet limite plutôt que pour capturer un projet de biologie — dans le doute,
# c'est l'humain qui tranche, et il a l'écran sous les yeux pour le faire.

LEXIQUE_DROIT_FORT = (
    "jurisprudence", "jurisprudentiel", "qpc", "conseil constitutionnel",
    "conseil d'état", "conseil d'etat", "cour de cassation", "légifrance",
    "legifrance", "cedh", "cour européenne des droits de l'homme",
    "code civil", "code pénal", "code electoral", "code électoral",
    "code de la nationalité", "jorf", "droit public", "droit privé",
    "droit pénal", "droit constitutionnel", "droit administratif",
    "droit de la nationalité", "naturalisation", "citoyenneté", "nationalité",
    "déchéance", "dégradation civique", "exposé des motifs",
    "travaux parlementaires", "doctrine juridique", "arrêt", "pourvoi",
    "justiciable", "contentieux", "juridiction", "jurisconsulte",
)
LEXIQUE_DROIT_FAIBLE = (
    "juridique", "légal", "légalité", "juge", "tribunal", "requérant",
    "décret", "ordonnance", "sanction", "peine", "procédure", "statut",
    "doctrine", "considérant", "sénat", "assemblée nationale", "colloque",
)
# Le veto. Un projet qui parle de génomes n'est pas un projet de droit, même
# s'il parle aussi de nationalité (c'est le cas de la phylogéographie humaine).
ANTI_LEXIQUE = (
    "génome", "genome", "génomique", "phylogén", "phylogen", "séquençage",
    "sequencing", "souche", "lignée", "lineage", "snp", "spdi", "mtbc",
    "tuberculosis", "mycobacterium", "bactérie", "bacterial", "protéine",
    "protein", "adn", "pcr", "alignement", "bioinformatique", "transcriptome",
    "apprentissage automatique", "machine learning", "réseau de neurones",
)


def _occurrences(termes, textes):
    """Termes distincts trouvés, avec un extrait qui le prouve.

    Rend une liste de couples (terme, extrait) : le classifieur doit pouvoir
    MONTRER, pas seulement compter. Un décompte ne se relit pas ; un extrait si.
    """
    trouves, vus = [], set()
    for t in textes:
        bas = t.lower()
        for terme in termes:
            if terme in vus or terme not in bas:
                continue
            i = bas.index(terme)
            extrait = " ".join(t[max(0, i - 40): i + len(terme) + 40].split())
            trouves.append((terme, extrait))
            vus.add(terme)
    return trouves


def classer_domaine(textes: list[str]) -> tuple[str, int, dict]:
    """Devine le domaine d'un projet. Rend (domaine, score, preuves)."""
    forts = _occurrences(LEXIQUE_DROIT_FORT, textes)
    faibles = _occurrences(LEXIQUE_DROIT_FAIBLE, textes)
    anti = _occurrences(ANTI_LEXIQUE, textes)

    score = 2 * len(forts) + len(faibles)
    veto = len(anti) >= 2 and len(forts) < 3
    domaine = "droit" if (len(forts) >= 2 and score >= 4 and not veto) else "generic"
    return domaine, score, {"forts": forts, "faibles": faibles,
                            "anti": anti, "veto": veto}


def textes_du_repertoire(d: Path, limite: int = 12) -> list[str]:
    """Échantillon lisible d'un projet existant, pour classer une migration.

    On lit peu et on lit court : les fichiers de tête d'un projet suffisent à le
    situer, et lire tout un dépôt ferait entrer dans le calcul des dépendances,
    des données et du code qui ne disent rien de la discipline.
    """
    textes = []
    for motif in ("CLAUDE.md", "README.md", "etat_des_decouvertes.md",
                  "cahier_de_labo.md", "*.tex", "*.md"):
        for f in sorted(d.glob(motif))[:limite]:
            try:
                textes.append(f.read_text(errors="ignore")[:20000])
            except OSError:
                continue
            if len(textes) >= limite:
                return textes
    return textes


def afficher_classement(domaine: str, score: int, preuves: dict) -> None:
    """Rend le verdict CONTESTABLE : sans ses preuves, il ne vaut rien."""
    print(f"\nClassifieur de domaine : {domaine.upper()} (score {score})")
    for cle, etiquette in (("forts", "termes forts"), ("faibles", "termes faibles"),
                           ("anti", "termes biologiques (veto)")):
        items = preuves[cle]
        if not items:
            continue
        noms = ", ".join(t for t, _ in items[:8])
        print(f"  {etiquette:28} {len(items):2}  {noms}")
        if cle == "forts" and items:
            _, extrait = items[0]
            print(f"  {'exemple':28}     « …{extrait}… »")
    if preuves["veto"]:
        print("  → VETO : vocabulaire biologique dominant, le domaine `droit` "
              "n'est pas retenu malgré les termes juridiques.")
    print("  (classement indicatif : `--domain <valeur>` le remplace sans discuter)")


PROFIL_PLUGINS = (Path.home() / "docs" / "environnement" / "outils"
                  / "profil_plugins.py")


def ecrire_profil_plugins(project_dir: Path, famille: str | None = None) -> bool:
    """Écrit le profil d'activation des plugins du projet (piste P5.5).

    Un projet neuf n'a pas besoin des dix-sept plugins du marketplace : son profil
    est `socle + blocs de sa famille + blocs de sa phase`, et c'est
    `~/docs/environnement/profils/profils.json` qui en décide, pas ce script — le
    même fichier sert à `cycle-projet` aux portes et à la passe de migration sur
    les projets déjà existants. Un projet neuf est en phase 1 (ou hors rail) : il
    n'aura donc ni `redaction` ni `diffusion`, que la porte 1 lui apportera.

    Échec assumé et ANNONCÉ si l'outillage est introuvable : mieux vaut un projet
    sans profil et une ligne qui le dit qu'un profil silencieusement absent.
    """
    if not PROFIL_PLUGINS.is_file():
        print(f"  ⚠ profil de plugins non écrit : {PROFIL_PLUGINS} introuvable.")
        print("    Le projet verra les plugins activés au niveau utilisateur.")
        return False
    cmd = [sys.executable, str(PROFIL_PLUGINS), "--apply", str(project_dir), "--write"]
    if famille:
        cmd += ["--famille", famille]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        print(f"  ⚠ profil de plugins non écrit : {(r.stderr or r.stdout).strip()[:200]}")
        return False
    for ligne in (r.stdout or "").splitlines():
        if ligne.startswith(("Famille", "Blocs", "Activés")):
            print(f"  {ligne}")
    print("  ✔ profil de plugins écrit dans .claude/settings.json "
          "(portée projet, réglages globaux intacts)")
    return True


def ecrire_activation_plugin(project_dir: Path, plugin: str,
                             marketplace: str = _AUTEUR["marketplace"] or "guyeux-claude-plugins") -> str:
    """Installe un plugin POUR CE PROJET, sans toucher aux réglages globaux.

    La portée est le point important : le plugin de droit n'a rien à faire dans
    une session de phylogénomique, et l'activer globalement le ferait peser sur
    toutes les sessions (voir la KB `claude-plugins-aup` : les descriptions de
    skills s'injectent dans le prompt système).

    ATTENTION, VÉRIFIÉ À L'USAGE ET NON SUPPOSÉ (2026-08-17). Écrire le
    `enabledPlugins` du projet NE SUFFIT PAS : `enabledPlugins` n'active qu'un
    plugin déjà INSTALLÉ. L'installation, elle, crée deux choses de plus qu'un
    fichier de réglages ne peut fabriquer : une entrée dans le registre global
    `~/.claude/plugins/installed_plugins.json` (avec sa portée, son
    `projectPath` et son `gitCommitSha`) et une COPIE EN CACHE du plugin sous
    `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>`. On délègue donc
    au CLI, qui est la seule voie qui fasse les trois.

    Contrôle qui a établi le point : `claude plugin install --scope project`
    lancé dans un répertoire VIERGE y écrit très exactement le `settings.json`
    que cette fonction écrivait à la main — la ressemblance du fichier était donc
    trompeuse, et seul l'examen du registre a montré ce qui manquait.

    Repli : si le CLI est absent, échoue ou n'aboutit pas, on écrit au moins le
    réglage et on rend la commande à taper. Un repli qui ANNONCE ce qu'il n'a pas
    pu faire vaut mieux qu'un succès apparent.
    """
    import json as _json

    cle = f"{plugin}@{marketplace}"
    conf_dir = project_dir / ".claude"
    conf_dir.mkdir(exist_ok=True)

    try:
        r = subprocess.run(
            ["claude", "plugin", "install", cle, "--scope", "project", "-y"],
            cwd=project_dir, capture_output=True, text=True, timeout=120)
        if r.returncode == 0 or "Successfully installed" in (r.stdout or ""):
            return cle
        raison = (r.stderr or r.stdout or "").strip().splitlines()
        print(f"  ⚠ `claude plugin install` n'a pas abouti : "
              f"{raison[-1] if raison else 'raison inconnue'}")
    except (OSError, subprocess.SubprocessError) as e:
        print(f"  ⚠ `claude plugin install` injouable ici ({e.__class__.__name__}).")

    f = conf_dir / "settings.json"
    conf = {}
    if f.exists():
        try:
            conf = _json.loads(f.read_text())
        except ValueError:
            conf = {}
    conf.setdefault("enabledPlugins", {})[cle] = True
    f.write_text(_json.dumps(conf, indent=2, ensure_ascii=False) + "\n")
    print(f"  ⚠ Réglage écrit, mais le plugin n'est PAS installé : le lancer à la main")
    print(f"    cd {project_dir} && claude plugin install {cle} --scope project")
    return cle


def create_project(name: str, title: str, parent_dir: Path,
                   domain: str, do_git: bool, do_parent_gi: bool,
                   from_piste: str | None = None,
                   registry: Path | None = None,
                   voies: tuple[str, ...] = ("article",),
                   famille: str | None = None) -> None:
    project_dir = parent_dir / name
    article = "article" in voies

    if project_dir.exists():
        print(f"Erreur : {project_dir} existe déjà.", file=sys.stderr)
        sys.exit(1)

    # `article/` n'existe que sur la voie article : un projet qui répond à un mail
    # ou reforge un outil n'a pas de manuscrit, et lui poser un dépôt git vide
    # donnerait l'illusion d'un versionnement (leçon KB du 2026-07-31).
    dirs = [
        project_dir / "analyses",
        project_dir / "data",
        project_dir / "résultats",
        project_dir / "experiments",
        project_dir / "litterature_review",
    ]
    if article:
        dirs = [
            project_dir / "article" / "figures",
            project_dir / "article" / "supplementary_materials",
            project_dir / "article" / "review",
        ] + dirs
    if "réponse" in voies:
        dirs.append(project_dir / "reponse")
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    files = {
        project_dir / "CLAUDE.md":
            claude_md_template(name, title, domain, voies, famille),
        project_dir / "cahier_de_labo.md":
            cahier_de_labo_template(name, title, project_dir),
        project_dir / "etat_des_decouvertes.md":
            etat_des_decouvertes_template(name, voies=voies),
        project_dir / "pistes.md":
            pistes_template(name, voies=voies),
        project_dir / "JOURNAL.md":
            journal_md_template(name),
        project_dir / "litterature_review" / "index.md":
            litterature_review_index(name),
        project_dir / "litterature_review" / "references.bib":
            REFERENCES_BIB,
    }
    if article:
        files.update({
            project_dir / "article" / "main.tex":
                main_tex_template(name, title, domain),
            project_dir / "article" / "references.bib":
                REFERENCES_BIB,
            project_dir / "article" / "Makefile":
                MAKEFILE,
            project_dir / "article" / ".gitignore":
                ARTICLE_GITIGNORE,
            project_dir / "article" / "review" / "INDEX.md":
                review_index_template(),
        })
    for path, content in files.items():
        path.write_text(content, encoding="utf-8")

    print(f"Projet {name} initialisé dans {project_dir}")
    print(f"  famille : {famille or 'non déclarée'}    voie : {' + '.join(voies)}")
    print(f"  {len(dirs)} répertoires créés")
    print(f"  {len(files)} fichiers générés")

    if not article:
        print("  (pas de article/ : la voie ne produit pas de manuscrit)")
    elif do_git:
        # Initialize article/ as its own git repo
        ok, msg = init_article_git_repo(project_dir / "article")
        prefix = "  ✔" if ok else "  ⚠"
        print(f"{prefix} {msg}")
    else:
        print("  (git init dans article/ : sauté --no-git)")

    # Add article/ to parent .gitignore
    if article and do_parent_gi:
        msg = update_parent_gitignore(project_dir)
        print(f"  ✔ {msg}")

    # Registre parent (sérendipité) : signaler son absence, ne pas l'écrire soi-même.
    # C'est là qu'atterrissent les découvertes qui sortiront du périmètre de ce
    # projet ; sans lui, elles n'ont nulle part où aller et se perdent à la clôture.
    registre = project_dir.parent / "pistes.md"
    if not registre.exists():
        print(f"  ⚠ Registre parent absent : {registre}")
        print("    (il accueille les découvertes hors périmètre ; /recadrage le créera)")

    # Découverte : ce qui existe déjà (KB inter-projets + projets voisins), pour
    # ne pas re-dériver ou dupliquer par ignorance plutôt que par choix.
    print_discovery_report(name, title, parent_dir, domain)

    # Piste source : si ce projet naît d'une piste déjà écrite (typiquement une
    # sérendipité `mtbc/pistes.md` promue), en récupérer le texte et la marquer
    # migrée — sinon le registre affirme encore une direction ouverte qui a
    # désormais un foyer, et la matière d'origine resterait dupliquée nulle part.
    if from_piste:
        print()
        if registry is None or not registry.exists():
            print(f"  ⚠ --from-piste {from_piste} demandé mais --registry introuvable "
                  "— piste non marquée, rien seedé.", file=sys.stderr)
        else:
            found = find_piste_block(registry.read_text(encoding="utf-8"), from_piste)
            if found is None:
                print(f"  ⚠ {from_piste} introuvable dans {registry} — rien seedé.",
                      file=sys.stderr)
            else:
                block, _, _ = found
                seed_from_piste(project_dir, block, from_piste)
                print(f"  ✔ Texte de {from_piste} recopié dans {name}/cahier_de_labo.md")
                msg = mark_piste_migrated(registry, from_piste, name)
                print(f"  {msg}")

    # Les plugins s'activent POUR CE PROJET, par profil (famille × phase, P5.5).
    # Fait ici et non dans main() pour que les deux chemins (création et migration)
    # posent le même réglage : une activation qui ne vaudrait que pour les projets
    # neufs laisserait sans outillage précisément les projets déjà en cours, qui en
    # ont le plus besoin.
    ecrire_profil_plugins(project_dir, famille)

    print()
    print("Prochaines étapes :")
    if domain == "droit":
        print("  0. `/notes-et-citations` AVANT toute production de livrable "
              "(conventions de notes, puis vérification des citations).")
    etapes = [f"Renseigner les objectifs dans {name}/etat_des_decouvertes.md (§1)."]
    if article:
        etapes.append("/lit-review <sujet> AVANT le premier calcul (cadrer l'état de l'art).")
    etapes.append(f"Compléter {name}/CLAUDE.md (contexte, sans y recopier les règles héritées).")
    etapes.append("Démarrer le cahier : /cahier-de-labo update")
    if article:
        etapes.append("Publier le repo article :\n"
                      f"     cd {name}/article && gh repo create <repo-name> --private --source=. --push\n"
                      "     puis Overleaf -> Menu -> GitHub -> Import project.")
    if "réponse" in voies:
        etapes.append("Relire la fiche du destinataire (`/collaborateur`) avant le premier brouillon "
                      f"dans {name}/reponse/.")
    if "réoutillage" in voies:
        etapes.append("Reproduire le défaut par un cas minimal rejouable avant de toucher à l'outil.")
    if "coordination" in voies:
        etapes.append("Lister les artefacts vivants à tenir à jour (site, listes, annuaire, "
                      "conventions...) dans pistes.md P1.1.")
    for i, e in enumerate(etapes, start=1):
        print(f"  {i}. {e}")


def migrate_project(project_dir: Path, voies: tuple[str, ...] = ("article",)) -> None:
    """Réaligner un projet existant : poser les squelettes état + pistes.

    Idempotent et non destructif : ne crée que les fichiers absents, n'écrase
    jamais, ne supprime rien.

    Preuve qu'il s'agit d'un vrai projet (et non d'un répertoire quelconque
    qu'on scafferait par erreur) : la présence d'un `cahier_de_labo.md` OU
    d'un `CLAUDE.md`. Accepter le CLAUDE.md est indispensable, sinon un projet
    réel mais jamais aligné est impossible à aligner : exiger le cahier comme
    unique preuve reviendrait à réclamer le fichier même que la migration doit
    poser. Dans ce cas, le cahier est créé lui aussi.

    `voies` défaut à `("article",)` pour ne rien changer au comportement
    historique des migrations déjà en usage sur ~274 projets ; c'est
    précisément ce défaut silencieux qui a posé `Voie : article` sur le
    projet `gis` (coordination institutionnelle, aucun article visé) le
    2026-09-16 — passer `--voie` explicitement à `--migrate` l'évite.
    """
    has_cahier = (project_dir / "cahier_de_labo.md").exists()
    if not has_cahier and not (project_dir / "CLAUDE.md").exists():
        print(f"Erreur : {project_dir} n'a ni cahier_de_labo.md ni CLAUDE.md "
              "(pas un projet). Migration annulée.", file=sys.stderr)
        sys.exit(1)

    name = project_dir.name
    n_entrees = cahier_maturity(project_dir)
    created, skipped = [], []
    targets = {
        project_dir / "etat_des_decouvertes.md":
            etat_des_decouvertes_template(name, n_entrees, voies=voies),
        project_dir / "pistes.md":
            pistes_template(name, n_entrees, voies=voies),
    }
    if not has_cahier:
        targets[project_dir / "cahier_de_labo.md"] = cahier_de_labo_template(
            name, name, project_dir)
    for path, content in targets.items():
        if path.exists():
            skipped.append(path.name)
        else:
            path.write_text(content, encoding="utf-8")
            created.append(path.name)

    cl = project_dir / "CLAUDE.md"
    pointer_status = "CLAUDE.md absent"
    if cl.exists():
        txt = cl.read_text(encoding="utf-8")
        if "etat_des_decouvertes.md" in txt:
            pointer_status = "déjà présent"
        else:
            pointer = (
                "\n## État et pistes\n\n"
                "- `etat_des_decouvertes.md` — état consolidé (prouvé/infirmé/ouvert), "
                "réécrit via `/etat update`.\n"
                "- `pistes.md` — arbre des pistes (à faire/en cours/réalisé/abandonné), "
                "géré via `/pistes`. À consulter avant de relancer un calcul.\n"
            )
            cl.write_text(txt.rstrip() + "\n" + pointer, encoding="utf-8")
            pointer_status = "ajouté"

    print(f"Migration de {name} ({project_dir}) :")
    print(f"  créés   : {', '.join(created) if created else '—'}")
    print(f"  laissés : {', '.join(skipped) if skipped else '—'} (déjà présents, non écrasés)")
    print(f"  pointeur CLAUDE.md : {pointer_status}")
    if n_entrees and created:
        print(f"\n  ⚠ Projet MATURE ({n_entrees} entrées de cahier) : les squelettes posés sont")
        print("    marqués NON RENSEIGNÉS, ils n'affirment aucun état. Enchaîner sur")
        print("    `/etat update` puis `/pistes` pour les régénérer depuis le cahier.")

    # --migrate ne reçoit pas de --domain explicite : la chaîne "mtbc" dans le
    # chemin est l'indice le plus fiable disponible sans le redemander.
    inferred_domain = "mtbc" if "mtbc" in str(project_dir).lower() else "generic"
    print_discovery_report(name, name, project_dir.parent, inferred_domain)


def main():
    parser = argparse.ArgumentParser(
        description="Initialiser un nouveau projet de recherche.",
        epilog=("Exemple : python init_project.py L4.17 "
                "--title 'Caractérisation de L4.17' --domain mtbc"),
    )
    parser.add_argument("name", nargs="?", help="Nom du répertoire à créer.")
    parser.add_argument(
        "--migrate", metavar="DIR",
        help="Réaligner un projet EXISTANT : poser les squelettes "
             "etat_des_decouvertes.md + pistes.md (idempotent, non destructif).",
    )
    parser.add_argument("--title", help="Titre complet du projet.")
    parser.add_argument(
        "--at", default=None,
        help="Répertoire parent où créer <name>/ (défaut : ~/docs/codes/<famille>/ si "
             "--famille est donné et que le CWD n'y est pas déjà, sinon CWD).",
    )
    parser.add_argument(
        "--famille", choices=FAMILLES, default=None,
        help="Famille de rangement de codes/ (pompiers, mtbc, bio, ia, shs, cours, admin, "
             "outillage, archives, autre). Devinée depuis le chemin si omise. Inscrite dans "
             "CLAUDE.md ; `mtbc` implique --domain mtbc.",
    )
    parser.add_argument(
        "--voie", default=None,
        help="Voie(s) du projet, séparées par des virgules : article (défaut), réponse, "
             "réoutillage, coordination. Déclarée dans l'en-tête de etat_des_decouvertes.md. "
             "Sans `article`, aucun article/ n'est créé et aucune phase n'est posée. Avec "
             "--migrate, s'applique aussi (défaut historique : article, pour ne pas changer "
             "le comportement des migrations existantes).",
    )
    parser.add_argument(
        "--domain", choices=["generic", "mtbc", "bacterio", "droit"], default=None,
        help="Templates spécialisés : 'mtbc' (alias 'bacterio') active les macros LaTeX "
             "de phylogénomique bactérienne et les conventions SPDI/RAxML-NG — le domaine "
             "vaut pour tout pathogène bactérien clonal, seule la référence change "
             "(H37Rv pour le MTBC, CO92 pour Y. pestis) ; 'droit' active les conventions "
             "de citation en notes de bas de page et le plugin `droit`. Par défaut, le "
             "domaine est DEVINÉ par le classifieur (voir --no-classify).",
    )
    parser.add_argument(
        "--no-classify", action="store_true",
        help="Désarmer le classifieur de domaine : le projet est créé en "
             "'generic' si --domain n'est pas donné.",
    )
    parser.add_argument(
        "--no-git", action="store_true",
        help="Ne pas initialiser de repo git dans article/.",
    )
    parser.add_argument(
        "--no-parent-gitignore", action="store_true",
        help="Ne pas ajouter article/ au .gitignore parent.",
    )
    parser.add_argument(
        "--from-piste", metavar="Pxx",
        help="Id de piste source (ex. P27) à l'origine de ce projet — typiquement "
             "une sérendipité promue depuis un registre `pistes.md`. Recopie son "
             "texte dans le cahier du nouveau projet et la marque MIGRÉE dans "
             "--registry (mutation locale, rien n'est supprimé ni réécrit en bloc).",
    )
    parser.add_argument(
        "--registry", metavar="FILE",
        help="Chemin du pistes.md source contenant --from-piste. Requis si "
             "--from-piste est utilisé.",
    )
    args = parser.parse_args()

    if args.migrate:
        try:
            voies_migrate = parse_voies(args.voie)
        except ValueError as e:
            parser.error(str(e))
        cible = Path(args.migrate).expanduser().resolve()
        migrate_project(cible, voies=voies_migrate)
        # Sur une migration, le classifieur a une matière que la création n'a
        # pas : le projet EXISTE et se lit. C'est le cas le plus favorable, et
        # c'est aussi celui où un projet de droit rédigé depuis des mois avec les
        # mauvaises conventions peut enfin être repéré.
        if not args.no_classify:
            dom, score, preuves = classer_domaine(
                [cible.name] + textes_du_repertoire(cible))
            afficher_classement(dom, score, preuves)
            ecrire_profil_plugins(cible)
            if dom == "droit":
                print("    Enchaîner sur `/notes-et-citations` AVANT toute "
                      "production de livrable.")
        return
    if not args.name:
        parser.error("le nom du projet est requis (ou utiliser --migrate <dir>)")
    if args.from_piste and not args.registry:
        parser.error("--from-piste nécessite --registry <pistes.md>")

    if args.title:
        title = args.title
    else:
        title = args.name.replace("-", " ").replace("_", " ")

    try:
        voies = parse_voies(args.voie)
    except ValueError as e:
        parser.error(str(e))

    # Le parent : --at explicite, sinon la famille dit où l'on range (sauf si le CWD
    # est déjà dans cette famille : les scans de voisinage doivent s'y faire), sinon
    # le CWD. Une famille demandée dont le répertoire n'existe pas est une erreur,
    # pas une création silencieuse : le rangement de codes/ (P3) se décide ailleurs.
    cwd = Path(os.getcwd()).resolve()
    if args.famille in FAMILLES_ALIAS:
        args.famille = FAMILLES_ALIAS[args.famille]
        print(f"Famille normalisée : {args.famille} (nom du répertoire réel)")
    if args.domain in DOMAINES_ALIAS:
        args.domain = DOMAINES_ALIAS[args.domain]
        print(f"Domaine normalisé : {args.domain} (nom interne des templates)")
    if args.at:
        parent = Path(args.at).expanduser().resolve()
    elif args.famille and deviner_famille(cwd) != args.famille:
        parent = Path.home() / "docs" / "codes" / args.famille
        if not parent.is_dir():
            print(f"Erreur : la famille {args.famille} n'a pas de répertoire {parent} ; "
                  "le créer d'abord ou donner --at.", file=sys.stderr)
            sys.exit(1)
        print(f"Famille {args.famille} : le projet sera créé dans {parent}")
    else:
        parent = cwd
    if not parent.exists():
        print(f"Erreur : parent {parent} n'existe pas.", file=sys.stderr)
        sys.exit(1)

    # Convention des cinq emplacements (`codes/CLAUDE.md`, gravée le 2026-09-16) : dans
    # une famille qui l'a adoptée, le travail VIVANT est dans `en_cours/` et les quatre
    # `clos*/` portent le statut. Le statut d'un projet est son emplacement sur le
    # disque : un projet neuf scaffoldé à la racine de la famille n'a donc pas de statut
    # lisible, et se retrouve mélangé aux artefacts du dépôt hub. La convention se
    # DÉTECTE (présence d'un `en_cours/`) au lieu d'être codée en dur sur une famille,
    # de sorte qu'une famille qui l'adoptera plus tard en bénéficie sans retoucher ce
    # script. `--at` explicite reste souverain : on avertit sans rediriger.
    en_cours = parent / "en_cours"
    if en_cours.is_dir():
        if args.at:
            print(f"Attention : {parent} suit la convention des cinq emplacements "
                  f"(en_cours/ + clos*/), mais --at a été donné explicitement — le "
                  f"projet est créé dans {parent}, sans statut lisible sur le disque.")
        else:
            parent = en_cours
            print(f"Convention des cinq emplacements détectée : le projet sera créé "
                  f"dans {parent} (travail vivant).")

    famille = args.famille or deviner_famille(parent)
    if famille and not args.famille:
        print(f"Famille devinée depuis le chemin : {famille}")

    # Le domaine : donné, impliqué par la famille mtbc, ou deviné. À la création, le
    # classifieur ne dispose que du nom et du titre — c'est peu, et c'est assumé :
    # mieux vaut un classement prudent sur peu de matière qu'un classement confiant
    # sur du bruit.
    domain = args.domain
    if domain is None and famille == "mtbc":
        domain = "mtbc"
    if domain is None:
        if args.no_classify:
            domain = "generic"
        else:
            domain, score, preuves = classer_domaine([args.name, title])
            afficher_classement(domain, score, preuves)

    create_project(
        name=args.name,
        title=title,
        parent_dir=parent,
        domain=domain,
        do_git=not args.no_git,
        do_parent_gi=not args.no_parent_gitignore,
        from_piste=args.from_piste,
        registry=Path(args.registry).expanduser().resolve() if args.registry else None,
        voies=voies,
        famille=famille,
    )


if __name__ == "__main__":
    main()
