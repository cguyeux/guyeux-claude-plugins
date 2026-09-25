#!/usr/bin/env python3
"""
Objet     : index dérivé inter-projets des questions ouvertes, acquis, réfutés et
            causes de clôture d'un dépôt de recherche multi-projets ; appariement
            lexical (BM25 + entités) d'un texte libre contre cet index, pour
            chercher un DESTINATAIRE à une découverte au lieu de la verser
            mécaniquement au registre du dépôt.
Entrées   : racine du dépôt (auto-détectée, ou --root) ; parcourt
            <racine>/*/pistes.md, <racine>/*/pistes/P*.md (architecture
            index + détail), <racine>/*/etat_des_decouvertes.md, <racine>/pistes.md
            (registre de sérendipité), et les mêmes fichiers plus ARCHIVE_NOTE.md
            sous les cinq répertoires de statut (en_cours/, clos_soumis/,
            clos_accepte/, clos/, clos_abandonne/). En REPLI seulement, pour les projets
            dépourvus de registre exploitable, <racine>/*/cahier_de_labo.md.
Sorties   : .carrefour/index.jsonl + index.meta.json (index dérivé, régénérable,
            jamais lu par un agent), stdout compact (10-20 lignes) pour `match`.
Réutilisable : oui — générique à tout dépôt suivant la convention des cinq
            artefacts (cahier / état / pistes). Aucune dépendance externe.
Projet    : mtbc/ (outillage transverse) — canonique, exposé par `/pistes match`
Date      : 2026-08-26

Garde-fou : un match n'est PAS une décision. Ce script rend des candidats
classés, jamais un verdict. Écrire chez un projet voisin lui coûte du travail :
ne le faire que si le fait est ACTIONNABLE pour lui, jamais « pour information ».
Un score élevé ne prouve rien : le doublon le mieux classé du dépôt est
parfaitement sain et assumé, et les scores qui le dépassent sont des projets
distincts partageant le texte de cadrage de la passe qui les a créés.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

# Les cinq statuts d'un projet du dépôt (règle gravée le 2026-09-16) : un projet
# vit dans `en_cours/` ou dans l'un des quatre répertoires de clôture. Les globs
# ci-dessous en sont dérivés plutôt qu'écrits à la main, pour qu'un sixième nom
# ne puisse pas être ajouté ici sans l'être partout.
CLOS_DIRS = ("clos_soumis", "clos_accepte", "clos", "clos_abandonne")
STATUT_DIRS = ("en_cours",) + CLOS_DIRS

_FEUILLES = ("pistes.md", "pistes/P*.md", "etat_des_decouvertes.md", "ARCHIVE_NOTE.md")

INDEX_DIR = ".carrefour"
INDEX_FILE = "index.jsonl"
META_FILE = "index.meta.json"
# Incrémenter à chaque changement du format d'index : force la réindexation.
INDEX_VERSION = 8

# --- Types d'items indexés -------------------------------------------------
# question    : piste ouverte (à faire / en cours / partiel) -> ce que le projet CHERCHE
# incertain   : §"Incertain / en cours d'arbitrage" -> question ouverte déjà rédigée
# angle-mort  : §"Angles morts / contre-arguments non levés" -> question ouverte
# acquis      : §"Acquis — ce qui est démontré" -> ce que le projet SAIT (peut répondre ailleurs)
# refute      : §"Réfuté / écarté" -> négatif propre (évite de refaire)
# objectif    : §"Question de recherche et objectifs" -> le cadrage du projet
# cloture     : cause de clôture normalisée d'un projet archivé (cf. ARCHIVE_NOTE.md)
# abandon     : corps d'une note d'archive
# question-cahier / objectif-cahier : REPLI pour un projet sans registre exploitable
#               (cf. parse_cahier) — fraîcheur non garantie, date affichée.
QUESTION_TYPES = {"question", "incertain", "angle-mort", "question-cahier"}
CAHIER_TYPES = {"question-cahier", "objectif-cahier"}

SECTION_MAP = [
    (r"question de recherche|objectif", "objectif"),
    (r"acquis", "acquis"),
    (r"r[ée]fut[ée]|[ée]cart[ée]", "refute"),
    (r"incertain|arbitrage|en d[ée]bat", "incertain"),
    (r"angles? morts?|contre-arguments?", "angle-mort"),
    (r"hors p[ée]rim[èe]tre", "hors-perimetre"),
    (r"verdict", "verdict"),
]

OPEN_STATES = ("à faire", "a faire", "en cours", "partiel", "partiellement")
STATE_RE = re.compile(r"\[([^\]\n]{2,30})\]")

# Signature lexicale d'un EMPÊCHEMENT. C'est ce qui sépare un verrou d'un thème :
# quatre projets qui parlent de datation ne sont pas quatre projets bloqués par
# la datation. On ne cherche donc pas un sujet partagé mais l'aveu qu'on ne peut
# pas — et on le cherche dans la tournure (« ne permet pas », « faute de »), qui
# porte le sens, plutôt que dans des mots isolés. Évalué à l'indexation sur le
# texte COMPLET de l'item : le titre d'une piste dit rarement ce qui la bloque,
# c'est son corps qui l'avoue.
IMPEDIMENT_RE = re.compile(
    # aveu d'impossibilité
    r"insuffisan|ne permet(?:tent)? pas|impossibl|faute de|manque de|manquant"
    r"|n[ '’]a pas pu|ne peu(?:t|vent) pas|ne suffi|hors de port[ée]e|emp[êe]ch"
    r"|verrou|obstacle|blocage|bloqu[ée]|indisponibl|non disponibl|introuvabl"
    r"|[ée]chec|non concluant|non r[ée]solu|ne converge pas|sans r[ée]ponse"
    # travail non fait faute de moyen (la forme la plus courante du dépôt)
    r"|non faite?|non r[ée]alis|pas encore|aucune? \w+ (?:encore |n'a )?"
    r"(?:produite?|disponible|faite?)|absente?\b|absence de|n'existe pas"
    # puissance ou signal trop faible pour trancher
    r"|trop (?:peu|petit|court|faible|bruit|instabl|h[ée]t[ée]rog)|pas assez"
    r"|faible (?:puissance|signal|support|couverture|r[ée]solution|effectif)"
    r"|signal \w*\s*\w* faible|puissance (?:statistique )?(?:faible|limit)"
    r"|petit [ée]chantillon|[ée]chantillon (?:trop )?(?:petit|r[ée]duit|faible)"
    r"|limit[ée]e? par|limitation|non calibr|pas de donn[ée]es",
    re.I)

# La négation d'un empêchement en porte tout le vocabulaire : « n'empêche pas le
# tip-dating » est l'inverse exact d'un verrou, et un filtre purement lexical le
# compte comme tel. Mesuré : c'était 1 des 6 candidats du verrou de datation.
NOT_BLOCKED_RE = re.compile(
    r"n[ '’](?:emp[êe]che|est pas bloqu|a pas emp[êe]ch)|ne (?:bloque|limite) pas"
    r"|sans obstacle|verrou lev[ée]|obstacle lev[ée]|plus (?:un |de )?(?:verrou|obstacle)"
    r"|d[ée]bloqu[ée]|n[ '’]est plus (?:un )?(?:verrou|bloqu)",
    re.I)

# Identifiants du domaine : lignées, locus tags, IS, RD, SPDI, accessions.
ENTITY_RE = re.compile(
    r"\b(?:L\d+(?:\.\d+)*[a-z]?"          # L4.15, L2.2.1
    r"|Rv\d{4}[A-Bc]?"                     # Rv0007, Rv2548A
    r"|IS\d{3,4}"                          # IS6110
    r"|RD\d{1,3}[a-z]?"                    # RD303
    r"|BCG(?:\.\w+)?"
    r"|NC_\d+\.\d+"
    r"|SRR\d+|ERR\d+|PRJ[A-Z]{2}\d+"
    r"|M(?:af|tb)?\d*)\b"
)

# Dates, noms de fichiers et références internes : co-occurrents mais non
# informatifs sur l'OBJET, ils apparient deux projets par leur calendrier.
NOISE_RE = re.compile(r"^(?:\d{4}-\d{2}(?:-\d{2})?|\d+|.+\.(?:md|py|tex|tsv|csv|json|png|pdf))$")

STOPWORDS = set("""
a à ai au aux avec ce ces cet cette dans de des du elle en est et eux il ils
je la le les leur lui ma mais me même mes moi mon ne nos notre nous on ou où
par pas peu pour qu que quel quelle qui sa sans se ses son sont sur ta te tes
toi ton tu un une vos votre vous y été être avoir fait faire plus moins très
entre chez déjà encore aussi donc alors comme si non oui tout tous toute toutes
the of and to in for on with is are be by from as at that this it its
projet projets piste pistes analyse analyser étude étudier faire vérifier
detail détail cf voir origine maj
sonnet opus haiku fable low medium high xhigh max amorce
""".split())

# Ponts de vocabulaire : la requête et le registre ne nomment pas toujours la
# même chose pareil. Volontairement court et éditable ; pas d'embeddings.
SYNONYMS = {
    "is6110": ["insertion", "element", "mobile", "transposase"],
    "is": ["insertion", "element", "mobile"],
    "spoligotype": ["spacer", "crispr", "espaceur", "dr"],
    "spacer": ["spoligotype", "crispr", "espaceur"],
    "crispr": ["spacer", "espaceur", "spoligotype", "dr"],
    "sous-lignee": ["sublineage", "clade", "lignee"],
    "clade": ["lignee", "sous-lignee", "sublineage"],
    "datation": ["clock", "horloge", "beast", "temporel", "dating"],
    "horloge": ["datation", "clock", "beast", "temporel"],
    "resistance": ["amr", "mdr", "xdr", "catalogue", "who"],
    "deletion": ["rd", "perte", "region"],
    "geographie": ["phylogeographie", "pays", "migration", "diaspora"],
    "migration": ["phylogeographie", "diaspora", "geographie", "route"],
    "hypothetique": ["dark", "sombre", "inconnu", "orphelin"],
    "dark": ["hypothetique", "sombre", "orphelin"],
    "homoplasie": ["convergence", "convergent", "parallele"],
    "contamination": ["chimere", "melange", "mixte", "misclassifie"],
    "misclassifie": ["contamination", "chimere", "espece", "kansasii"],
}


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def tokenize(text: str) -> list[str]:
    ents = [e.lower() for e in ENTITY_RE.findall(text)]
    low = strip_accents(text.lower())
    words = re.findall(r"[a-z0-9][a-z0-9_.-]{1,}", low)
    out = [w for w in words if w not in STOPWORDS and len(w) > 2
           and not NOISE_RE.match(w)]
    return out + ents


def expand(tokens: list[str]) -> list[str]:
    out = list(tokens)
    for t in tokens:
        out.extend(SYNONYMS.get(t, []))
    return out


# --- Localisation du dépôt -------------------------------------------------

def find_root(start: Path, min_projects: int = 5) -> Path:
    """Racine = premier parent hébergeant au moins `min_projects` projets.

    Un projet est un sous-répertoire portant `cahier_de_labo.md`. Permet
    d'appeler le script depuis n'importe quel répertoire de projet sans
    --root, ce qui est le cas d'usage réel (`/pistes match` depuis le projet
    où la découverte vient d'être faite).
    """
    cur = start.resolve()
    for _ in range(6):
        try:
            n = sum(1 for _ in cur.glob("*/cahier_de_labo.md"))
        except OSError:
            n = 0
        if n >= min_projects:
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    return start.resolve()


# --- Parsing ---------------------------------------------------------------

def project_status(root: Path, path: Path) -> tuple[str, str]:
    """Retourne (nom_projet, statut) — statut ∈ vivant / clos / abandonné.

    Les cinq statuts du dépôt (`en_cours/`, `clos_soumis/`, `clos_accepte/`,
    `clos/`, `clos_abandonne/`, règle gravée le 2026-09-16) se replient ici sur
    les trois valeurs que consomme le reste du module (`MARK`, filtres
    `== "vivant"`) : les quatre nuances de clôture n'ont pas d'usage dans un
    index de questions ouvertes, où seul compte le fait qu'un projet soit encore
    en état de recevoir une réponse.
    """
    rel = path.relative_to(root)
    parts = rel.parts
    if len(parts) == 1:
        return ("«registre du dépôt»", "vivant")
    if parts[0] in CLOS_DIRS:
        return (parts[0] + "/" + parts[1], "abandonné"
                if parts[0] == "clos_abandonne" else "clos")
    if parts[0] == "en_cours":
        return (parts[1], "vivant")
    return (parts[0], "vivant")


def state_of(block: str) -> str:
    """DERNIER tag d'état reconnu du bloc — le tag peut suivre plusieurs lignes de
    texte (une continuation « maj: » plus bas porte l'état le plus récent).

    Balayage en ORDRE INVERSE (2026-09-16) : un corps de piste peut citer la
    syntaxe des tags en exemple (« chercher les pistes encore `[à faire]`/
    `[en cours]` ») avant son propre tag final — prendre le premier crochet
    reconnu du bloc lisait alors l'exemple comme l'état réel (`[réalisé]` cité
    en exemple faisait classer une piste encore ouverte comme close). Le tag
    qui fait foi est conventionnellement le plus proche de la fin du bloc.

    Un crochet entre BACKTICKS (`` `[réalisé]` ``) est ignoré (2026-09-16,
    trouvé en testant `/suite` sur `Q1`, qui documente ce même bug en citant
    `` `[en cours]` `` en exemple APRÈS son propre tag réel — l'inverse du cas
    ci-dessus, donc invisible au seul balayage inversé). Un tag qui fait
    vraiment foi ne s'écrit jamais entre backticks dans ce dépôt ; ce n'est
    donc jamais un vrai positif perdu, seulement des exemples cités en prose.
    """
    for m in reversed(list(STATE_RE.finditer(block))):
        if m.start() > 0 and block[m.start() - 1] == "`":
            continue
        tag = strip_accents(m.group(1).lower().strip())
        for st in OPEN_STATES:
            if tag.startswith(strip_accents(st)):
                return "ouvert"
        if tag.startswith(("realis", "abandonn", "clos", "ferm")):
            return "clos"
    return "indéterminé"


def parse_pistes_tree(path: Path) -> list[dict]:
    """Extrait les pistes MAJEURES (`## Px.`) et leurs SOUS-PISTES (`- Px.y`).

    Le même parseur sert pour `pistes.md` (projets non migrés : tout y est) et
    pour `pistes/Px.md` (architecture index + détail : le corps réel y vit).
    Sans cela, les projets migrés — dont les plus riches du dépôt — n'exposent
    que des titres, et leurs questions ouvertes sont invisibles à l'appariement.
    """
    items: list[dict] = []
    cur: dict | None = None
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()

    def flush() -> None:
        nonlocal cur
        if cur is None:
            return
        block = cur["text"] + " " + " ".join(cur["tail"])
        st = state_of(block) if cur["state"] is None else cur["state"]
        cur["type"] = "question" if st == "ouvert" else "piste-close"
        # Retirer TOUS les crochets terminaux, pas un seul : depuis la convention
        # d'etiquetage 2026-09-13, un libelle finit souvent par « … [Sonnet:xhigh] [en cours] »,
        # et un unique `sub` laissait alors fuiter l'etat dans le texte indexe.
        while True:
            nouveau = re.sub(r"\s*\[[^\]]+\]\s*$", "", cur["text"]).strip()
            if nouveau == cur["text"]:
                break
            cur["text"] = nouveau
        items.append(cur)
        cur = None

    for line in lines:
        # Comme la sous-piste ci-dessous, la majeure hors rail (`## N.`, `## Q.`,
        # `## S.`...) est une lettre SEULE, sans chiffre : `P[\w.\-]+?` la ratait,
        # le titre entier retombait alors dans la QUEUE de la piste précédente
        # encore ouverte, jusqu'à la prochaine définition reconnue. Sur ce
        # dépôt, ça a fait déborder la recherche d'état de `Q1` (P.md) sur les
        # ~35 lignes suivantes, jusqu'au tag `[en cours]` cité en EXEMPLE dans le
        # propre corps de `Q1`, classant à tort une piste `[réalisé]` comme
        # ouverte — trouvé le 2026-09-16 en testant `/suite`.
        # BORNE A 1-3 LETTRES (2026-09-21, piste AD2) : au-delà d'`[A-Z]` seule, une
        # racine à DEUX lettres ou plus (`AA`, `AC`... convention du dépôt lui-même,
        # cf. piste AC) n'était jamais reconnue par une classe de caractères — même
        # défaut de NAMESPACE que celui réglé par AC1 dans `status.py`, mais ici pas
        # besoin de la racine du projet (`detecter_prefixes`) : le format `## <ref>.`
        # est assez contraint (ancré en tête de ligne, point + espace juste après)
        # pour que borner à 1-3 lettres, comme `detecter_prefixes` le fait déjà pour
        # les noms de fichiers, suffise sans faire remonter le paramètre `root`
        # jusqu'ici (option plus invasive, tous les appelants à revoir).
        m = re.match(r"^## ((?:P\d[\w.\-]*|[A-Z]{1,3})(?<!P))\.?\s+(.+?)\s*$", line)
        if m:
            flush()
            cur = {"ref": m.group(1), "text": m.group(2), "body": [], "tail": [],
                   "state": None}
            continue
        # Convention normale : `P<chiffres>` (P7, P8.2). Au moins deux projets
        # (mtbc, environnement) numérotent aussi des chantiers HORS RAIL avec une
        # autre lettre (`N7`, `N8.a`, `O1`, `Q1`), et environnement lui-même des
        # sous-pistes à préfixe DEUX lettres (`AC1`, `AD2`) — sans cette alternative
        # élargie à 1-3 lettres (même borne et même raison qu'au-dessus), ces
        # sous-pistes étaient invisibles à l'indexation, alors que `## N.` / `## AC.`
        # sont bien les titres de section qui les portent.
        m = re.match(r"^\s*[-*]\s+((?:P\d|[A-Z]{1,3}\d)[\w.\-]*)[.)]?\s+(.+?)\s*$", line)
        if m and len(m.group(2)) > 12:
            flush()
            cur = {"ref": m.group(1), "text": m.group(2), "body": [], "tail": [],
                   "state": None}
            continue
        if cur is not None and line.strip() and not line.startswith("#"):
            # Le corps indexé reste borné à 4 lignes (économie de tokens), mais
            # l'ÉTAT se cherche sur le bloc entier : une piste dont le tag
            # `[à faire]` arrive en sixième ligne était sinon lue comme close,
            # et disparaissait des questions ouvertes — le cœur du dispositif.
            cur["tail"].append(line.strip())
            if len(cur["body"]) < 4:
                cur["body"].append(line.strip())
    flush()
    return items


def parse_etat(path: Path) -> list[dict]:
    items = []
    section, secnum = None, ""
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"^##\s*(\d+)?\.?\s*(.+?)\s*$", line)
        if m and line.startswith("## "):
            secnum = m.group(1) or ""
            label = strip_accents(m.group(2).lower())
            section = None
            for pat, typ in SECTION_MAP:
                if re.search(strip_accents(pat), label):
                    section = typ
                    break
            continue
        if section and re.match(r"^[-*]\s+\S", line):
            txt = re.sub(r"^[-*]\s+", "", line).strip()
            if len(txt) > 25:
                items.append({"type": section, "ref": f"§{secnum}", "text": txt[:400],
                              "body": []})
    return items


def parse_archive_note(path: Path) -> list[dict]:
    """Lit une note de clôture ; isole le bloc normalisé s'il est présent.

    Le bloc normalisé (`cause :` / `réouverture :`, cf. `/pistes match`,
    section « Projets archivés ») est indexé à part, en type `cloture` : c'est
    lui que le critère de réouverture apparie, car un projet clos ne se rouvre
    que si le fait nouveau lève la cause qui l'a clos.
    """
    txt = path.read_text(encoding="utf-8", errors="replace")
    out: list[dict] = []
    cause = re.search(r"^\s*cause\s*:\s*(.+)$", txt, re.M | re.I)
    if cause:
        # Le bloc entier, pas la seule ligne `réouverture :` — la condition de
        # réouverture tient sur plusieurs lignes de continuation indentées, et
        # c'est justement le texte le plus riche à apparier : c'est lui qui dit
        # quel fait nouveau lèverait la cause.
        bloc = [l.strip() for l in txt.splitlines()
                if re.match(r"^[ \t]{4,}\S", l)][:24]
        flat = " ".join(bloc)
        head = f"[{cause.group(1).strip()}] " + flat
        out.append({"type": "cloture", "ref": "cause", "text": head[:300],
                    "body": [flat]})
    head = "\n".join(txt.splitlines()[:60])
    out.append({"type": "abandon", "ref": path.name[:18], "text": head[:600], "body": []})
    return out


# --- Repli sur le cahier ---------------------------------------------------
# Sections d'une entrée de cahier qui portent une question OUVERTE, et marqueurs
# de prose pour les entrées non sectionnées (les seeds de projet, notamment).
CAHIER_SECTION_RE = re.compile(
    r"points? ouverts?|suites? sugg|prochaines? [ée]tapes?|questions? ouvertes?"
    r"|verrous?|[àa] faire|next", re.I)
CAHIER_MARK_RE = re.compile(
    r"[àa] trancher|point ouvert|prochaines? [ée]tapes?|reste [àa] |test qui"
    r"|[àa] v[ée]rifier|non r[ée]solu|hypoth[èe]se de travail|[àa] falsifier"
    r"|test falsifiant|[àa] d[ée]terminer|suite\s*:", re.I)
# La date d'entrée s'écrit `## 2026-06-04 — …` mais aussi `## [2026-06-04 16:18] …`
# selon l'ancienneté du projet : sans le crochet optionnel, un cahier entier
# devient invisible sans que rien ne le signale.
ENTRY_RE = re.compile(r"^##\s*\[?(\d{4}-\d{2}-\d{2})")


def parse_cahier(path: Path, last_n: int = 4) -> list[dict]:
    """REPLI : extrait les questions ouvertes des `last_n` dernières entrées.

    N'est appelé que pour les projets dont le registre est absent ou entièrement
    constitué de gabarit `/init-project` non rempli — là où l'alternative n'est
    pas une information moins bonne mais AUCUNE information. Le cahier reste une
    source de second rang : il est append-only, donc un point ouvert y vieillit
    sans que rien ne vienne l'invalider. D'où trois précautions : seules les
    dernières entrées comptent, le type est distinct (`question-cahier`), et la
    date de l'entrée est portée dans la référence pour que le lecteur sache ce
    qu'il doit revérifier avant d'agir.
    """
    txt = path.read_text(encoding="utf-8", errors="replace")
    lines = txt.splitlines()
    items: list[dict] = []

    # En-tête : `**Projet :** <intitulé>` — souvent la seule formulation de
    # l'objet d'un projet dépourvu d'état des découvertes.
    m = re.search(r"^\*\*Projet\s*:\*\*\s*(.+)$", txt, re.M)
    if m and len(m.group(1).strip()) > 10:
        items.append({"type": "objectif-cahier", "ref": "cahier",
                      "text": m.group(1).strip()[:300], "body": []})

    heads = [(i, m.group(1)) for i, l in enumerate(lines)
             if (m := ENTRY_RE.match(l))]
    ends = [i for i, _ in heads[1:]] + [len(lines)]
    for (i, date), end in list(zip(heads, ends))[-last_n:]:
        block, keep, para = lines[i + 1:end], False, []

        def flush(para: list[str], keep: bool) -> None:
            if not para:
                return
            t = " ".join(para).strip()
            t = re.sub(r"^[-*]\s+", "", t)
            if t.startswith("|") or t.count("|") > 4:
                return                     # tableau de suivi : mise en forme, pas un fait
            if len(t) > 30 and (keep or CAHIER_MARK_RE.search(t)):
                items.append({"type": "question-cahier", "ref": date,
                              "text": t[:300], "body": []})

        for line in block:
            if line.startswith("#"):
                flush(para, keep)
                para = []
                keep = bool(CAHIER_SECTION_RE.search(line))
                continue
            if not line.strip():
                flush(para, keep)
                para = []
                continue
            para.append(line.strip())
        flush(para, keep)
    return items[:14]      # borne dure : un cahier ne doit pas noyer l'index


SOURCE_GLOBS = (
    "pistes.md",                                   # registre de sérendipité du dépôt
    "*/pistes.md", "*/pistes/P*.md", "*/etat_des_decouvertes.md",
) + tuple(f"{d}/*/{f}" for d in STATUT_DIRS for f in _FEUILLES)


CAHIER_GLOBS = ("*/cahier_de_labo.md",) + tuple(
    f"{d}/*/cahier_de_labo.md" for d in STATUT_DIRS)


def sources(root: Path) -> list[Path]:
    out: list[Path] = []
    for pat in SOURCE_GLOBS + CAHIER_GLOBS:
        out.extend(p for p in root.glob(pat) if INDEX_DIR not in p.parts)
    return sorted(set(out))


def build_index(root: Path) -> list[dict]:
    records = []
    for path in sources(root):
        if path.name == "cahier_de_labo.md":
            continue                        # repli, traité après drop_boilerplate
        proj, status = project_status(root, path)
        try:
            if path.name == "pistes.md" or path.parent.name == "pistes":
                items = parse_pistes_tree(path)
            elif path.name == "etat_des_decouvertes.md":
                items = parse_etat(path)
            else:
                items = parse_archive_note(path)
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] {path}: {exc}", file=sys.stderr)
            continue
        for it in items:
            full = it["text"] + " " + " ".join(it.get("body", []))
            records.append({
                "projet": proj, "statut": status, "type": it["type"],
                "ref": it["ref"], "text": it["text"][:300],
                "tokens": tokenize(full), "file": str(path.relative_to(root)),
                "bloque": bool(IMPEDIMENT_RE.search(full))
                          and not NOT_BLOCKED_RE.search(full),
            })
    return add_cahier_fallback(root, dedupe(drop_boilerplate(records)))


def add_cahier_fallback(root: Path, records: list[dict]) -> list[dict]:
    """Complète l'index par le cahier des projets que le registre laisse muets.

    Un projet est muet quand son registre ne produit AUCUN item après le retrait
    du gabarit : soit qu'il n'ait ni `pistes.md` ni `etat_des_decouvertes.md`
    (58 des 127 projets vivants au 2026-08-26, dont les plus productifs, tous
    antérieurs à la convention des cinq artefacts), soit que son registre soit
    intégralement du scaffold `/init-project` jamais renseigné (les projets
    `Rv####` seedés depuis l'atlas). Dans les deux cas l'appariement ne le voit
    pas, et l'absence se lit à tort comme « ce projet ne cherche rien ».
    """
    # Seuil et non simple présence : un projet dont tout le registre tient en un
    # ou deux items — souvent un « Pointeur croisé : <autre projet> » — est aussi
    # muet qu'un projet sans registre, et son profil est en plus dégénéré (deux
    # tels projets partageant leur unique pointeur ont sorti un recouvrement de
    # 0,78, au-dessus du plus haut doublon réel du dépôt).
    counts = Counter(r["projet"] for r in records)
    voiced = {p for p, n in counts.items() if n >= 3}
    added = 0
    # Passer par CAHIER_GLOBS, jamais par un glob écrit ici : un `*/` en dur ne
    # voit que les projets à plat à la racine. Le défaut est resté invisible tant
    # que les projets vivants y étaient tous ; la migration vers `en_cours/` du
    # 2026-09-16 l'a révélé d'un coup — 205 items de repli perdus, 68 projets
    # muets redevenus inappariables.
    cahiers = sorted({p for pat in CAHIER_GLOBS for p in root.glob(pat)})
    for path in cahiers:
        proj, status = project_status(root, path)
        if proj in voiced:
            continue
        try:
            items = parse_cahier(path)
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] {path}: {exc}", file=sys.stderr)
            continue
        for it in items:
            full = it["text"] + " " + " ".join(it.get("body", []))
            records.append({
                "projet": proj, "statut": status, "type": it["type"],
                "ref": it["ref"], "text": it["text"][:300],
                "tokens": tokenize(full), "file": str(path.relative_to(root)),
                "bloque": bool(IMPEDIMENT_RE.search(full))
                          and not NOT_BLOCKED_RE.search(full),
            })
        added += bool(items)
    if added:
        print(f"[info] repli cahier : {added} projets muets rendus appariables",
              file=sys.stderr)
    return records


def dedupe(records: list[dict]) -> list[dict]:
    """Une piste majeure vit à la fois dans l'index et dans son fichier de détail."""
    seen, kept = set(), []
    for r in records:
        key = (r["projet"], r["type"], r["ref"], r["text"][:60])
        if key in seen:
            continue
        seen.add(key)
        kept.append(r)
    return kept


def drop_boilerplate(records: list[dict], min_projects: int = 3) -> list[dict]:
    """Écarte le texte de gabarit non rempli.

    Un item dont le texte normalisé apparaît à l'identique dans `min_projects`
    projets distincts n'est pas un fait : c'est du scaffold `/init-project` que
    personne n'a rempli. Le laisser dans l'index apparie tous les projets vides
    entre eux et noie les vrais rapprochements.
    """
    key = lambda r: strip_accents(re.sub(r"\W+", " ", r["text"].lower())).strip()  # noqa: E731
    owners: dict[str, set[str]] = {}
    for r in records:
        owners.setdefault(key(r), set()).add(r["projet"])
    kept = [r for r in records if len(owners[key(r)]) < min_projects]
    dropped = len(records) - len(kept)
    if dropped:
        print(f"[info] {dropped} items de gabarit écartés "
              f"(texte identique dans ≥{min_projects} projets)", file=sys.stderr)
    return kept


# --- Index sur disque : fraîcheur par mtime --------------------------------

def signature(root: Path) -> dict:
    paths = sources(root)
    mt = max((p.stat().st_mtime for p in paths), default=0.0)
    return {"version": INDEX_VERSION, "n_sources": len(paths), "mtime": mt}


def save(root: Path, records: list[dict]) -> None:
    d = root / INDEX_DIR
    d.mkdir(exist_ok=True)
    with (d / INDEX_FILE).open("w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    (d / META_FILE).write_text(json.dumps(signature(root)), encoding="utf-8")


def load(root: Path, quiet: bool = True) -> list[dict]:
    """Charge l'index, en le régénérant si une source a bougé depuis.

    Le contrôle de fraîcheur ne LIT aucune source : il compare le nombre de
    fichiers et le mtime le plus récent au couple mémorisé à la dernière
    indexation. Quelques centaines de stat(), soit un coût négligeable devant
    la garantie de ne jamais apparier contre un état périmé du dépôt.
    """
    idx = root / INDEX_DIR / INDEX_FILE
    meta = root / INDEX_DIR / META_FILE
    fresh = False
    if idx.exists() and meta.exists():
        try:
            fresh = json.loads(meta.read_text()) == signature(root)
        except (OSError, ValueError):
            fresh = False
    if not fresh:
        if not quiet:
            print("[info] index périmé ou absent — réindexation", file=sys.stderr)
        records = build_index(root)
        save(root, records)
        return records
    return [json.loads(l) for l in idx.read_text(encoding="utf-8").splitlines()]


# --- Recherche -------------------------------------------------------------

def bm25(query: list[str], records: list[dict], k1=1.4, b=0.6) -> list[tuple[float, dict, list[str]]]:
    N = len(records)
    df = Counter()
    for r in records:
        for t in set(r["tokens"]):
            df[t] += 1
    avgdl = sum(len(r["tokens"]) for r in records) / max(N, 1)
    qents = {t for t in query if ENTITY_RE.fullmatch(t.upper()) or ENTITY_RE.match(t)}
    scored = []
    for r in records:
        tf = Counter(r["tokens"])
        dl = len(r["tokens"]) or 1
        s = 0.0
        contrib: list[tuple[float, str]] = []
        for t in set(query):
            if t not in tf:
                continue
            idf = math.log(1 + (N - df[t] + 0.5) / (df[t] + 0.5))
            c = idf * tf[t] * (k1 + 1) / (tf[t] + k1 * (1 - b + b * dl / avgdl))
            if t in qents:
                c += 2.5 * idf          # une entité partagée pèse lourd
            s += c
            contrib.append((c, t))
        if s > 0:
            contrib.sort(reverse=True)
            scored.append((s, r, [t for _, t in contrib[:3]]))
    scored.sort(key=lambda x: -x[0])
    return scored


MARK = {"vivant": " ", "clos": "C", "abandonné": "A"}


def cmd_match(root: Path, query: str, k: int, types: str | None,
              include_closed: bool) -> None:
    records = load(root)
    if types:
        wanted = set(types.split(","))
        records = [r for r in records if r["type"] in wanted]
    if not include_closed:
        # Un projet clos ne CHERCHE plus rien, mais il SAIT (acquis, réfuté) et
        # il porte la cause qui l'a clos — la seule matière d'une réouverture.
        records = [r for r in records if r["statut"] == "vivant"
                   or r["type"] in ("refute", "abandon", "acquis", "cloture")]
    q = expand(tokenize(query))
    scored = bm25(q, records)
    if not scored:
        print("aucun rapprochement — destinataire à créer (registre du dépôt)")
        return
    top = scored[0][0] or 1.0
    seen, shown = set(), 0
    for s, r, why in scored:
        key = (r["projet"], r["type"], r["ref"])
        if key in seen:
            continue
        seen.add(key)
        print(f"{s / top:4.2f} {MARK[r['statut']]} {r['projet'][:30]:30s} "
              f"{r['type'][:10]:10s} {r['ref'][:8]:8s} {r['text'][:78]:78s} "
              f"| {','.join(why)}")
        shown += 1
        if shown >= k:
            break
    print(f"\n{len(records)} items appariés · un match n'est pas une décision : "
          f"n'écrire chez un voisin que si le fait lui est ACTIONNABLE.")


def cmd_overlap(root: Path, k: int, min_score: float) -> None:
    """Paires de projets dont l'OBJET se recouvre — matière du verdict FUSIONNER.

    Profil d'un projet = ses objectifs (§1) + acquis (§2) + questions ouvertes,
    vectorisés en TF-IDF. Ne tranche rien : deux projets peuvent légitimement
    partager un objet (L4.15 et L4.16 sont voisins sans devoir fusionner), et
    le plus haut score du dépôt est un doublon déclaré et sain.
    """
    records = load(root)
    profiles: dict[str, Counter] = {}
    status: dict[str, str] = {}
    for r in records:
        # Les items de repli comptent ici comme ailleurs : sans eux, un projet
        # muet n'a pas de profil du tout, et deux projets réduits à un même
        # « Pointeur croisé : … » se ressemblent parfaitement sans rien partager.
        if r["type"] not in ("objectif", "acquis", "question", "incertain",
                             "objectif-cahier", "question-cahier"):
            continue
        w = 3 if r["type"].startswith("objectif") else 1
        p = profiles.setdefault(r["projet"], Counter())
        status[r["projet"]] = r["statut"]
        for t in r["tokens"]:
            p[t] += w
    N = len(profiles)
    df = Counter()
    for p in profiles.values():
        for t in p:
            df[t] += 1
    # Un token présent dans plus d'un tiers des projets ne discrimine rien
    # (« lignée », « souche », « mtbc »…) : il est écarté, pas seulement pondéré.
    vecs = {}
    for name, p in profiles.items():
        if len(p) < 12:
            continue      # profil trop maigre : le cosinus y est dégénéré, pas informatif
        v = {t: c * math.log(N / df[t]) for t, c in p.items() if df[t] <= N / 3}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        vecs[name] = ({t: x / norm for t, x in v.items()}, v)
    pairs = []
    names = sorted(vecs)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            va, _ = vecs[a]
            vb, _ = vecs[b]
            small, big = (va, vb) if len(va) < len(vb) else (vb, va)
            s = sum(x * big.get(t, 0.0) for t, x in small.items())
            if s >= min_score:
                shared = sorted(
                    (t for t in small if t in big),
                    key=lambda t: -(small[t] * big[t]))[:5]
                pairs.append((s, a, b, shared))
    pairs.sort(key=lambda x: -x[0])
    if not pairs:
        print("aucun recouvrement au-dessus du seuil")
        return
    for s, a, b, shared in pairs[:k]:
        print(f"{s:4.2f} {MARK[status.get(a, 'vivant')]}{a[:30]:30s} ~ "
              f"{MARK[status.get(b, 'vivant')]}{b[:30]:30s} | {', '.join(shared)}")


def _clusters(items: list[dict], min_sim: float, min_projects: int) -> list[list[dict]]:
    """Regroupement par chef de file sur cosinus TF-IDF.

    Volontairement le plus simple qui marche : les items sont peu nombreux
    (quelques centaines après le filtre d'empêchement) et le résultat doit être
    lisible et défendable, pas optimal. Un item rejoint le premier chef de file
    dont il est assez proche, sinon il en devient un.
    """
    N = len(items)
    # Les synonymes sont appliqués ICI et pas seulement à la requête de `match` :
    # deux projets bloqués par le même verrou l'écrivent rarement avec les mêmes
    # mots (« horloge non calibrable » et « signal temporel insuffisant » ne
    # partagent aucun token littéral), et sans ce pont le clustering ne voit que
    # des coïncidences de vocabulaire.
    toks = [expand(it["tokens"]) for it in items]
    df = Counter()
    for tk in toks:
        for t in set(tk):
            df[t] += 1
    vecs = []
    for tk in toks:
        tf = Counter(tk)
        v = {t: c * math.log(1 + N / df[t]) for t, c in tf.items() if df[t] <= N / 3}
        n = math.sqrt(sum(x * x for x in v.values())) or 1.0
        vecs.append({t: x / n for t, x in v.items()})
    heads: list[int] = []
    members: list[list[int]] = []
    for i in range(N):
        best, bs = -1, min_sim
        for hi, h in enumerate(heads):
            small, big = ((vecs[i], vecs[h]) if len(vecs[i]) < len(vecs[h])
                          else (vecs[h], vecs[i]))
            s = sum(x * big.get(t, 0.0) for t, x in small.items())
            if s >= bs:
                best, bs = hi, s
        if best < 0:
            heads.append(i)
            members.append([i])
        else:
            members[best].append(i)
    out = []
    for grp in members:
        projets = {items[i]["projet"] for i in grp}
        if len(projets) >= min_projects:
            out.append([items[i] for i in grp])
    out.sort(key=lambda g: -len({m["projet"] for m in g}))
    return out


def cmd_locks(root: Path, k: int, min_sim: float, min_projects: int,
              null_runs: int) -> None:
    """Verrous PARTAGÉS : un même obstacle qui bloque plusieurs projets à la fois.

    L'intérêt n'est pas documentaire : un investissement méthodologique sur un
    verrou partagé s'amortit autant de fois qu'il y a de projets bloqués, ce que
    ni le registre d'un projet ni `match` (qui suppose de savoir quoi chercher)
    ne peuvent faire apparaître.
    """
    recs = load(root)
    pool = [r for r in recs if r["type"] in QUESTION_TYPES and r["statut"] == "vivant"]
    locked = [r for r in pool if r.get("bloque")]
    groups = _clusters(locked, min_sim, min_projects)
    print(f"{len(locked)} questions ouvertes portant un empêchement "
          f"(sur {len(pool)}) · {len(groups)} verrous partagés par ≥{min_projects} projets\n")
    for g in groups[:k]:
        projets = sorted({m["projet"] for m in g})
        shared = Counter(t for m in g for t in set(m["tokens"]))
        top = [t for t, c in shared.most_common(30) if c >= max(2, len(g) // 2)][:6]
        print(f"▸ {len(projets)} projets · {', '.join(top)}")
        for m in g:
            print(f"    {MARK[m['statut']]} {m['projet'][:28]:28s} {m['ref'][:10]:10s} "
                  f"{m['text'][:96]}")
        print()
    if null_runs:
        # Modèle nul : le filtre d'empêchement fait-il mieux qu'un tirage de même
        # effectif dans les questions ouvertes ? Sans cet écart, `locks` ne
        # détecterait que du vocabulaire partagé, et ne mériterait pas d'exister.
        import random
        obs = len(groups)
        rng = random.Random(20260826)
        counts = []
        for _ in range(null_runs):
            sample = rng.sample(pool, min(len(locked), len(pool)))
            counts.append(len(_clusters(sample, min_sim, min_projects)))
        mean = sum(counts) / len(counts)
        ge = sum(1 for c in counts if c >= obs)
        print(f"[modèle nul] {null_runs} tirages de {len(locked)} questions au hasard : "
              f"{mean:.1f} verrous en moyenne (min {min(counts)}, max {max(counts)}) "
              f"contre {obs} observés · p ≈ {(ge + 1) / (null_runs + 1):.3f}")


def cmd_hollow(root: Path) -> None:
    """Couverture de l'index : quels projets ne peuvent PAS être appariés, et pourquoi.

    Un projet muet n'est pas un projet sans questions : c'est un projet dont les
    questions ne sont écrites nulle part où l'appariement les voit. La distinction
    compte, parce que le remède diffère — remplir un gabarit, migrer un projet
    ancien, ou accepter le repli sur le cahier.
    """
    recs = load(root)
    by_proj: dict[str, Counter] = {}
    for r in recs:
        by_proj.setdefault(r["projet"], Counter())[r["type"]] += 1
    rows = []
    for path in sorted(root.glob("*/cahier_de_labo.md")):
        proj = path.parent.name
        c = by_proj.get(proj, Counter())
        registre = sum(n for t, n in c.items() if t not in CAHIER_TYPES)
        cahier = sum(n for t, n in c.items() if t in CAHIER_TYPES)
        has_reg = (path.parent / "pistes.md").exists() or \
                  (path.parent / "etat_des_decouvertes.md").exists()
        if registre:
            continue
        rows.append((proj, "gabarit-seul" if has_reg else "sans-registre", cahier))
    if not rows:
        print("aucun projet muet : tous ont un registre exploitable")
        return
    n_gab = sum(1 for _, k, _ in rows if k == "gabarit-seul")
    print(f"{len(rows)} projets sans aucun item de REGISTRE "
          f"({n_gab} au gabarit seul, {len(rows) - n_gab} sans registre du tout) — "
          f"appariables uniquement par le repli cahier :")
    for proj, kind, cahier in sorted(rows, key=lambda r: (r[2], r[0])):
        flag = "  ⚠ MUET" if cahier == 0 else ""
        print(f"  {proj[:34]:34s} {kind:14s} {cahier:2d} items de cahier{flag}")


def cmd_stats(root: Path) -> None:
    recs = load(root)
    types = Counter(r["type"] for r in recs)
    print(f"{len(recs)} items · {len({r['projet'] for r in recs})} projets · "
          f"{len(sources(root))} fichiers source")
    print("types   :", ", ".join(f"{t}={n}" for t, n in types.most_common()))
    print("statuts :", ", ".join(f"{s}={n}" for s, n in
                                 Counter(r["statut"] for r in recs).most_common()))
    print(f"questions ouvertes : {sum(types[t] for t in QUESTION_TYPES)}")
    archived = {r["projet"] for r in recs if r["statut"] in ("clos", "abandonné")}
    with_cause = {r["projet"] for r in recs if r["type"] == "cloture"}
    if archived - with_cause:
        print(f"[dette] {len(archived - with_cause)} projets archivés sans cause "
              f"normalisée : {', '.join(sorted(archived - with_cause))}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("cmd", choices=["reindex", "match", "stats", "overlap",
                                    "locks", "hollow"])
    ap.add_argument("query", nargs="?", default="")
    ap.add_argument("--root", default=None,
                    help="racine du dépôt (défaut : auto-détectée depuis le cwd)")
    ap.add_argument("-k", type=int, default=12)
    ap.add_argument("--types", default=None,
                    help="filtre, ex. question,incertain,angle-mort")
    ap.add_argument("--include-closed", action="store_true",
                    help="inclut aussi les questions ouvertes des projets archivés")
    ap.add_argument("--min-score", type=float, default=0.25)
    ap.add_argument("--min-sim", type=float, default=0.18,
                    help="locks : cosinus minimal pour rejoindre un verrou")
    ap.add_argument("--min-projects", type=int, default=3,
                    help="locks : nombre de projets distincts pour qu'un verrou compte")
    ap.add_argument("--null", type=int, default=0,
                    help="locks : nombre de tirages du modèle nul (0 = aucun)")
    a = ap.parse_args()
    root = Path(a.root).resolve() if a.root else find_root(Path.cwd())

    if a.cmd == "reindex":
        recs = build_index(root)
        save(root, recs)
        print(f"{len(recs)} items indexés depuis {root}")
    elif a.cmd == "stats":
        cmd_stats(root)
    elif a.cmd == "overlap":
        cmd_overlap(root, a.k, a.min_score)
    elif a.cmd == "locks":
        cmd_locks(root, a.k, a.min_sim, a.min_projects, a.null)
    elif a.cmd == "hollow":
        cmd_hollow(root)
    else:
        if not a.query.strip():
            print("usage : carrefour.py match \"<texte libre de la découverte>\"",
                  file=sys.stderr)
            return 2
        cmd_match(root, a.query, a.k, a.types, a.include_closed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
