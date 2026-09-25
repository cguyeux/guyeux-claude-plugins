#!/usr/bin/env python3
"""Objet   : rendre l'etat COURANT de chaque piste et sous-piste d'un projet, en ne
            lisant QUE les lignes de DEFINITION et jamais la prose. Repond a une
            erreur reproduite trois fois de suite le 2026-09-05 sur
            `nucs_deletion_mutators` : un `grep "\\[a faire\\]"` sur `pistes.md` /
            `pistes/Px.md` remonte massivement des TRACES HISTORIQUES (« nouvelle
            sous-piste ouverte : P2.15.2.1 [a faire] », ecrit dans le recit d'un tour
            de /mtbc-prospect et jamais mis a jour depuis) et fait passer pour
            ouvertes des pistes closes depuis des jours. Trois listes de pistes
            fausses ont ete presentees a l'utilisateur avant que la cause soit vue.
Entrees : <projet>/pistes.md et <projet>/pistes/P*.md (racine = premier parent
            portant `cahier_de_labo.md`, 5 niveaux max, comme le skill).
Sorties : stdout, TSV `id<TAB>etat<TAB>fichier:ligne<TAB>libelle` trie par
            numerotation naturelle ; `--open` pour ne rendre que ce qui est ouvert ;
            `--json` pour une sortie machine ; `--audit` pour lister les mentions en
            prose qui CONTREDISENT l'etat courant (le piege lui-meme), les pistes
            ABSENTES du registre pour cause de forme non conforme, et les etats HORS
            NOMENCLATURE.
Reutilisable : OUI, tout projet suivant la convention `pistes.md` + `pistes/Px.md`.
Projet  : skill `pistes` (canonique ${CLAUDE_PLUGIN_ROOT}/skills/pistes/)
Date    : 2026-09-05

REGLE DE PARSING, la seule qui distingue definition et prose :

  Une piste n'est DEFINIE que par (a) un titre de section `## Px. <titre> [etat]`
  dans l'index, ou (b) un item de liste dont le PREMIER token est l'identifiant :
  `- P2.15.2.1 <titre> ... [etat]` (gras `**Px**` tolere). Son etat est le PREMIER
  marqueur d'etat rencontre a partir de la ligne de definition, le titre pouvant
  courir sur plusieurs lignes. Tout marqueur ulterieur, jusqu'a la definition
  suivante, est de la PROSE : historique, verdict, renvoi a une autre piste --
  jamais l'etat courant.

  Corollaire : `- P2.12 ... [realise]` suivi trois cents lignes plus bas de
  « nouvelle sous-piste P2.15.2.1 [a faire] » ne rend PAS P2.15.2.1 ouverte ; cette
  mention est un fait date, pas un etat. Seule la definition de P2.15.2.1
  elle-meme fait foi. Quand le detail `pistes/Px.md` existe, il prime sur l'index
  `pistes.md`, qui n'est qu'un resume.
"""

import argparse
import json
import os
import re
import sys

ETATS = ("à faire", "en cours", "réalisé", "abandonné")

# Numerotation latine effectivement employee dans ce depot (`P16.2a-sexies-bis.4`). Tout
# AUTRE mot de 4 lettres ou plus colle a un identifiant est un qualificatif de prose
# (`P2.14.1-style`), pas un segment de numerotation. Defini ICI et non plus bas parce que
# `RE_HEAD`/`RE_ITEM` en ont besoin (cf. `SUFFIXE_RACINE`).
ORDINAUX = {"bis", "ter", "quater", "quinquies", "sexies", "septies", "octies",
            "novies", "decies", "undecies", "duodecies"}

# Un ordinal latin peut suivre le numero de RACINE sans separateur : « ## P8bis. ».
# Sans cette alternative, `P8bis` n'etait pas un identifiant du tout -- la ligne cessait
# d'etre une definition et devenait de la PROSE, ou `prose_mentions` lisait « P8 [RÉALISÉ] »
# et signalait une contradiction avec l'etat reel de P8. Une piste MAJEURE entiere etait
# donc invisible au registre, et son absence se manifestait sous la forme d'un faux positif
# portant sur une AUTRE piste -- le pire des symptomes, qui envoie chercher au mauvais
# endroit. Mesure du 2026-09-08 : `P8bis` sur `predictops`, `P3bis` et sa sous-piste
# `P3bis.1` sur `voynich`, aucune piste perdue ailleurs, aucun autre compteur modifie.
SUFFIXE_RACINE = r"(?:" + "|".join(sorted(ORDINAUX, key=len, reverse=True)) + r")?"
# Un marqueur peut porter un qualificatif ("[partiellement réalisé, ...]") et,
# surtout, ETRE COUPE PAR UN RETOUR A LA LIGNE : la recherche se fait donc sur le
# bloc de definition RECOLLE, jamais ligne a ligne (bug qui rendait P2.3.3 « à
# faire » alors que sa definition porte « [réalisé, 2026-09-02 — verdict\n# NUANCÉ...] » a cheval sur deux lignes).
# Etiquette de routage modele/effort, convention 2026-09-13 (cf.
# ~/.agents/knowledge/model-routing.md) : `[Sonnet:xhigh]`, `[Haiku]`, `[Sonnet:xhigh +Opus]`,
# posee AVANT le crochet d'etat sur les pistes FEUILLES. Elle ne contient aucun des quatre mots
# d'etat, donc `RE_ETAT` ne la confond jamais avec un etat ; il faut en revanche la retirer du
# libelle, sinon elle se retrouve dans le TSV et dans l'index de `carrefour.py`.
RE_TAG = re.compile(r"\[(Haiku|Sonnet|Opus|Fable)(?::(low|medium|high|xhigh|max))?(?:\s*\+(Sonnet|Opus|Fable))?\]")

# {pid: "[Sonnet:xhigh]"} rempli par `parse_file`, lu par `--json`, le TSV et l'audit.
ETIQUETTES = {}

RE_ETAT = re.compile(r"\[([^\]]{0,24}?)(" + "|".join(ETATS) + r")([^\]]*)\]",
                     re.S | re.I)

# --------------------------------------------------------------------------------
# LETTRE(S) DE RACINE des identifiants de piste (2026-09-20, `archeo_crispr`)
#
# `P[0-9]+` etait hardcode partout : un projet numerotant ses pistes autrement (ici
# `A1`-`A7`, « axe », convention anterieure a `P` sur ce projet) rendait TOUTES les
# fonctions de ce script muettes -- zero piste, silencieusement, sans erreur. Exactement
# le mode de panne que ce script existe pour empecher ailleurs (cf. l'en-tete du fichier
# sur les listes fausses de `nucs_deletion_mutators`).
#
# Correctif retenu : DETECTER la ou les lettres de racine reellement utilisees par CE
# projet (`detecter_prefixes`, appele une fois dans `main()` juste apres avoir resolu la
# racine), plutot que d'accepter n'importe quelle lettre majuscule partout. La difference
# compte : ce script tourne aussi sur les cahiers du domaine MTBC, ou `L4`, `L6.5`, `L1`
# (codes de lignee) et `T18142` (identifiants de tache `agentctl`) sont omnipresents dans
# la PROSE des cahiers -- une classe `[A-Z][0-9]+` non filtree aurait fait passer des
# centaines de mentions de lignees pour des identifiants de sous-piste perdus sur la
# quasi-totalite des ~123 projets MTBC du depot. En ne retenant QUE les lettres
# effectivement vues dans `pistes.md`/`pistes/*.md` DE CE PROJET, la detection ne peut
# jamais entrer en collision avec un vocabulaire de domaine qui n'y figure pas.
PREFIXES = {"P"}   # valeur par defaut, ecrasee par `compiler_identifiants` dans `main()`


def _lettres_str(lettres=None):
    return "".join(sorted(lettres if lettres is not None else PREFIXES))


def _classe_lettres(lettres=None):
    """Fragment de regex pour la ou les lettres/prefixes de racine : `P` seule si un
    seul prefixe d'UNE lettre (comportement HISTORIQUE inchange, chaine identique a
    l'ancien litteral), `[AP]` si plusieurs prefixes d'une lettre chacun (migration en
    cours, ou registre mixte -- comportement historique inchange aussi).

    Des qu'AU MOINS UN prefixe compte deux lettres ou plus (`AA`, `AB`... convention
    2026-09-21 de ce depot lui-meme, cf. piste AC), une classe de caracteres ne peut
    plus representer l'ensemble : `[AAP]` ne reconnait qu'UNE lettre a la fois, jamais
    la PAIRE -- `AA1` n'est alors jamais reconnu comme un tout (la premiere lettre `A`
    consommee, le caractere suivant `A` n'etant pas un chiffre). On bascule donc sur
    une ALTERNANCE `(?:AA|AB|P|...)`, triee par longueur decroissante pour que les
    prefixes a deux lettres soient tentes avant une lettre seule qui existerait aussi
    (l'ancrage `[0-9]+` juste apres suffit en pratique a lever l'ambiguite meme sans ce
    tri, mais le tri evite tout retour arriere inutile et documente l'intention)."""
    s = set(lettres) if lettres is not None else set(PREFIXES)
    if any(len(p) > 1 for p in s):
        return "(?:" + "|".join(sorted(s, key=len, reverse=True)) + ")"
    joined = _lettres_str(s)
    return joined if len(joined) == 1 else "[" + joined + "]"


def compiler_identifiants(lettres, nues=()):
    """(Re)compile les regex de RECONNAISSANCE D'IDENTIFIANT pour la ou les lettres de
    racine du projet courant. Modifie des GLOBALES (meme logique que `ETIQUETTES`) : ces
    regex sont lues par une douzaine de fonctions qui ne recoivent pas le projet en
    parametre, les threader partout aurait ete un remaniement bien plus risque pour un
    script de cette taille deja partage par ~270 projets."""
    global RE_HEAD, RE_ITEM, RE_ORPHELIN, RE_PID_CAHIER, PREFIXES
    PREFIXES = set(lettres) or {"P"}
    id_racine = _classe_lettres() + r"[0-9]+"
    globals()["RACINES_NUES"] = set(nues)
    # MAJEURE NUE (2026-09-21, piste AE) : `## S.`, `## AA.` -- une piste majeure dont la
    # numerotation ne commence qu'aux sous-pistes. Branche ajoutee au SEUL `RE_HEAD`, et
    # seulement pour les prefixes que `amorcer()` a vus DECLARES PAR UN FICHIER
    # `pistes/<PREFIXE>.md` : c'est le critere qu'AC1 a valide comme le seul fiable, apres
    # que l'elargissement symetrique cote titres eut fabrique 117 pseudo-pistes sur
    # `droit-shs/rohonczi` (dont les titres `### PA1` sont une sous-serie interne, pas une
    # racine). `RE_ITEM`, `RE_ORPHELIN` et surtout `RE_PID_CAHIER` -- qui balaie la PROSE
    # des cahiers, ou une majuscule suivie d'un point est monnaie courante -- n'en heritent
    # PAS : une racine nue ne se declare que dans un titre, jamais dans un item ni un recit.
    tete = id_racine
    if nues:
        alt_nues = "|".join(sorted(nues, key=len, reverse=True))
        tete = r"(?:" + id_racine + r"|" + alt_nues + r")"
    RE_HEAD = re.compile(r"^[ \t]{0,7}#{1,6}\s+\*{0,2}(" + tete + SUFFIXE_RACINE
                         + r"(?:[.\-][0-9A-Za-z]+)*)\*{0,2}[.\s]")
    RE_ITEM = re.compile(r"^(\s*)[-*]\s+\*{0,2}(" + id_racine + SUFFIXE_RACINE
                         + r"(?:[.\-][0-9A-Za-z]+)*)\*{0,2}\.?(?![0-9A-Za-z.\-])")
    RE_ORPHELIN = re.compile(r"^\s*(?:#{1,6}\s+)?\*{0,2}(" + id_racine + r"(?:[.\-][0-9A-Za-z]+)*)\*{0,2}"
                             r"(?![0-9A-Za-z.\-])[^\n\[]{0,3}\["
                             r"[^\]]{0,24}?(" + "|".join(ETATS) + r")", re.I)
    RE_PID_CAHIER = re.compile(r"\b(" + id_racine + r"(?:[.\-][0-9A-Za-z]+)+)\.?(?![0-9A-Za-z.\-])")


RACINES_NUES = set()   # prefixes dont la MAJEURE est nue (`pistes/S.md`), cf. `racine()`


def amorcer(root):
    """Prepare les globales de reconnaissance pour CE projet : prefixes, regex, et les
    racines nues. Point d'entree unique et IDEMPOTENT, a appeler avant toute lecture.

    Existe parce que l'amorçage n'etait fait que dans `main()` (2026-09-21, piste AE) :
    tout appelant qui importe ce module comme bibliotheque -- `audit_signals.py`, donc les
    hooks `SessionStart` et `Stop` -- travaillait avec `PREFIXES = {"P"}`, la valeur par
    defaut, et ne voyait donc du registre que ce qui commence par `P`. Symptome mesure :
    `status.py --audit` annoncait 0 divergence de date index/detail la ou `audit_signals.py
    --quiet`, sur le MEME projet a la MEME seconde, en annoncait une (`P8`) -- deux verdicts
    contradictoires issus du meme code, l'un amorce et l'autre non. Un module dont la
    correction depend d'un preambule que chaque appelant doit se rappeler finit toujours par
    rencontrer l'appelant qui l'oublie : l'amorçage appartient donc au module, pas a eux."""
    prefixes = detecter_prefixes(root)
    nues = set()
    ddir = os.path.join(root, "pistes")
    if os.path.isdir(ddir):
        for fn in os.listdir(ddir):
            m = re.match(r"^([A-Z]{1,3})\.md$", fn)
            if m and m.group(1) in prefixes:
                nues.add(m.group(1))
    compiler_identifiants(prefixes, nues)
    return prefixes


def detecter_prefixes(root):
    """Quelles lettres/prefixes de racine ce projet emploie-t-il ? Deux sources, la plus
    fiable d'abord : les noms de fichiers `pistes/X[chiffres].md` (architecture
    index+detail deja appliquee -- le nom de fichier EST la racine, aucune ambiguite
    possible), puis les titres de section `## X[chiffres]` de `pistes.md` (projet pas
    encore eclate). Retombe sur {"P"} si rien n'est trouve (projet vide, ou toutes
    premieres pistes pas encore ecrites), pour ne rien changer au comportement
    historique dans ce cas.

    PREFIXE MULTI-LETTRES (2026-09-21, piste AC de ce projet lui-meme) : un fichier
    `pistes/AA.md` (racine `AA`, PAS de chiffre -- une seule sous-piste ou majeure sans
    encore de detail chiffre attache au nom) et un fichier `pistes/AB3.md` (racine `AB`
    puis chiffre) doivent tous deux ceder la racine `AA`/`AB`, jamais la seule lettre
    `A`. D'ou, POUR LES NOMS DE FICHIERS SEULEMENT, `[A-Z]{1,3}` (borne a 3 : au-dela,
    il ne s'agit plus d'une racine de piste mais d'un acronyme de fichier comme
    `README.md`/`CHANGELOG.md` qu'on ne veut surtout pas prendre pour une racine) suivi
    d'un chiffre optionnel, jamais d'un chiffre obligatoire comme avant. Mesure sur ~270
    projets avant application (echantillon aleatoire de 31, cf. cahier AC1) : aucun
    faux-positif introduit par ce cote-la, le nom de fichier restant aussi fiable qu'avant.

    LE TITRE DE SECTION, EN REVANCHE, N'EST PAS ELARGI (reste `[A-Z][0-9]`, comportement
    HISTORIQUE strict) malgre la tentation symetrique. Mesure sur le meme echantillon :
    `droit-shs/rohonczi` (pas de `pistes/` eclate, tout dans `pistes.md`) ecrit ses propres
    identifiants ad hoc `PA1`, `PN2-AA`, `PW1`... comme titres `### PA1 - ...` -- une
    racine a DEUX lettres aussi valide en apparence qu'`AA`, mais qui n'est ici QUE le
    prefixe `P` suivi d'une sous-serie interne au projet (jamais separee par `.`/`-`
    comme l'exige la convention), jamais une racine de piste au sens de ce script. Le
    nom de fichier ne souffre pas de cette ambiguite (une architecture index+detail
    EST une declaration explicite de racine) ; un titre de section seul n'offre aucun
    signal equivalent pour distinguer les deux cas -- elargir cote titre a fait
    apparaitre 117 pseudo-pistes fantomes (toutes `état non déclaré`) sur ce seul
    projet avant d'etre retire. Consequence : un projet a racines multi-lettres qui
    n'a PAS encore de `pistes/<RACINE>.md` par racine reste invisible a ce mecanisme
    jusqu'a son eclatement (`split_pistes_files.py`) -- degradation acceptee, pas un
    defaut de cette piste."""
    trouve = set()
    ddir = os.path.join(root, "pistes")
    if os.path.isdir(ddir):
        for fn in os.listdir(ddir):
            m = re.match(r"^([A-Z]{1,3})(?:[0-9]+)?\.md$", fn)
            if m:
                trouve.add(m.group(1))
    index = os.path.join(root, "pistes.md")
    if os.path.isfile(index):
        with open(index, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                m = re.match(r"^#{1,6}\s+\*{0,2}([A-Z])[0-9]", line)
                if m:
                    trouve.add(m.group(1))
    return trouve or {"P"}


def normalise(txt):
    """Retire gras et italique : « [**RÉALISÉ, ...**] » doit se lire comme un marqueur
    d'etat, pas comme de la prose. La casse est traitee par re.I.

    NEUTRALISE AUSSI CE QUI EST ENTRE BACKTICKS (2026-09-08). Un marqueur CITE en code inline
    n'est pas l'etat de la piste : c'est du texte qui PARLE d'un etat. Cas reel et savoureux,
    `annotation_mtbc` P22.2 — une piste qui decrit un hook detectant « un tag reste `[a faire]`/
    `[en cours]` » etait elle-meme lue « a faire », alors que son titre se termine par
    `[realise 2026-08-12]` : le parseur d'etats se faisait piéger par une piste qui parle
    d'etats. La convention du depot n'ecrit JAMAIS l'etat courant entre backticks, donc les
    neutraliser ne peut pas masquer un etat reel."""
    # EXCEPTION (2026-09-16, predictops-mcp) : certains depots ecrivent l'etat courant entre
    # backticks JUSTE APRES l'identifiant (« - P14.1 `[à faire]` ... », 106 sous-pistes dans
    # predictops-mcp, toutes lues « etat non declare » avant ce correctif). A cette position
    # precise, l'etiquette ne peut pas etre une citation : on la deplie avant de neutraliser
    # le reste du code inline. Une citation en milieu de phrase reste neutralisee.
    # Une etiquette de routage « [Sonnet:low] » (nue ou en backticks) peut s'intercaler
    # entre l'identifiant et l'etat : « - P11.1 [Sonnet:xhigh] `[réalisé]` ».
    txt = re.sub(r"^(\s*(?:[-*]|#{1,6})\s+\*{0,2}" + _classe_lettres() + r"[0-9][^\s`]*\s+"
                 r"(?:`?\[[A-Za-z]+(?::[a-z]+)?\]`?\s+)?)"
                 r"`(\[[^\]`\n]*\])`", r"\1\2", txt, flags=re.M)
    txt = re.sub(r"`[^`\n]*`", " ", txt)
    return txt.replace("*", "").replace("_", "")
MAX_TITRE = 200  # au-dela, on n'est plus dans le titre mais dans le corps
# Releve de 25 a 200 le 2026-09-22 (bug P8.12, `lineage_navigator`) : le tag d'etat peut
# legitimement se trouver a la toute fin d'une description longue (cause instruite,
# mesures, table de resultats), bien au-dela de 25 lignes -- ici a la ligne 28 du bloc,
# jamais atteint, rendu "etat non declare" par l'audit alors que la piste est bien
# close. Un bornage plus precis (couper la recherche a la premiere ligne "origine :"/
# "maj :" plutot qu'a un compte de lignes) a ete ESSAYE et REJETE : mesure sur 191
# projets du depot (`droit-shs/voynich` P24.1b, `archeo_crispr` A6.1b...), la metadonnee
# precede parfois le tag sur la MEME ligne (« origine : ... maj : ... [realise] »),
# et couper a son occurrence efface alors le vrai tag -- 4 regressions sur l'echantillon
# contre 0 avec le simple relevement de ce plafond, qui ne fait QUE elargir la fenetre
# de recherche existante sans jamais rien exclure. Verifie sur 191 projets de
# `~/docs/codes` (tous ceux portant `pistes.md`+`cahier_de_labo.md`) : 0 regression
# (aucun etat valide auparavant ne change), 57 pistes en plus correctement lues.
# titre de section de l'index : "## P2. Titre [etat]"
# Le titre peut etre INDENTE (jusqu'a 7 espaces) : dans un fichier de piste eclate,
# les sous-pistes de niveau 2 sont parfois ecrites "  ## P2.13. Titre" au lieu de
# "  - P2.13 Titre". Sans cette tolerance, la ligne n'etait NI parsee (RE_HEAD ancre
# en colonne 0) NI signalee comme non conforme (RE_ORPHELIN veut l'identifiant en
# premier token) : la piste disparaissait des DEUX listes -- cas P2.13/P2.14,
# invisibles jusqu'au 2026-09-06. Le plafond de 7 espaces evite de capter une ligne
# du CORPS d'une piste (indente a 8) qui commencerait par un '#'.
# (compilee par `compiler_identifiants`, pour la lettre de racine reellement employee
# par le projet courant -- valeur par defaut posee juste apres sa definition, plus bas)
# item de liste dont le PREMIER token est l'identifiant
#
# Le `\.?` avant le lookahead accepte le POINT SEPARATEUR de la numerotation classique
# (« - P35.4. Export des interventions »), tres repandue a la main. Sans lui, le
# lookahead `(?![0-9A-Za-z.\-])` rejetait la ligne entiere apres backtracking, et la
# sous-piste disparaissait des DEUX listes exactement comme les cas P2.13/P2.14 traites
# le 2026-09-06 : sur `predictops`, les DIX-SEPT sous-pistes de P35 etaient invisibles,
# P35 apparaissant comme une piste majeure « en cours » SANS AUCUNE sous-piste. Elles
# figuraient pourtant toutes, richement documentees, dans `pistes/P35.md` -- le
# controle de completude cahier<->registre les signalait donc comme « perdues » alors
# que seule leur FORME n'etait pas lue (diagnostic du 2026-09-08).
#
# Le point n'est mange QUE s'il n'est pas suivi d'un caractere d'identifiant : « P35.4. »
# rend `P35.4`, tandis que « P35.45 » et « P35.4.5 » restent captes en entier par le
# groupe gourmand qui precede.
# (compilee par `compiler_identifiants`, meme remarque que `RE_HEAD` ci-dessus)

# Valeur par defaut, identique caractere pour caractere a l'ancien comportement
# hardcode "P" -- toute fonction appelee AVANT que `main()` ne detecte la vraie
# lettre du projet (import de ce module comme bibliotheque, par exemple) se comporte
# donc exactement comme avant ce correctif.
compiler_identifiants(PREFIXES)


def project_root(start):
    d = os.path.abspath(start)
    for _ in range(6):
        if os.path.isfile(os.path.join(d, "cahier_de_labo.md")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    return None


def sort_key(pid):
    out = []
    for chunk in re.split(r"[.\-]", pid[1:]):
        m = re.match(r"(\d*)(.*)", chunk)
        out.append((int(m.group(1)) if m.group(1) else 0, m.group(2)))
    return out


def parse_file(path, rel):
    """Rend {id: (etat, 'rel:ligne', libelle)} pour les DEFINITIONS de ce fichier."""
    with open(path, encoding="utf-8") as fh:
        lines = fh.readlines()

    # reperer toutes les lignes de definition
    defs = []
    for i, line in enumerate(lines):
        m = RE_HEAD.match(line) or RE_ITEM.match(line)
        if m:
            pid = m.group(1) if m.re is RE_HEAD else m.group(2)
            defs.append((i, pid))

    found = {}
    for k, (i, pid) in enumerate(defs):
        stop = defs[k + 1][0] if k + 1 < len(defs) else len(lines)
        stop = min(stop, i + MAX_TITRE)
        bloc = normalise("".join(lines[i:stop]))
        txt = re.sub(r"^\s*[-*#]+\s*\*{0,2}" + re.escape(pid) + r"\*{0,2}[.\s]*", "", lines[i])
        # Cherchee dans `bloc` (multi-ligne, comme l'etat juste en dessous), PAS dans la
        # seule premiere ligne `txt` : une etiquette `[Modele:effort]` ecrite sur une ligne
        # de continuation du titre (frequent des que le titre depasse une ligne, cf. les
        # exemples `[etat] [Sonnet:...]` en fin de bloc dans plusieurs projets du depot)
        # etait invisible avant ce correctif, et la piste comptait a tort comme
        # "sans etiquette" -- meme defaut de fond que celui deja corrige pour RE_ETAT.
        tag = RE_TAG.search(bloc)
        libelle = RE_TAG.sub("", RE_ETAT.sub("", txt))
        libelle = re.split(r"\s{2,}(?:maj|origine|MIU)\s*:", libelle)[0]
        libelle = libelle.strip().rstrip("—-  ")[:110]
        m = RE_ETAT.search(bloc)
        etat = (m.group(1).strip() + " " + m.group(2).lower()).strip() if m else "état non déclaré"
        if pid not in found:               # premiere definition rencontree
            found[pid] = (etat, f"{rel}:{i + 1}", libelle)
            if tag:
                ETIQUETTES[pid] = tag.group(0)
    return found


def cloture_non_repercutee(path, rel):
    """Piste dont la LIGNE DE DEFINITION est encore ouverte alors que son propre corps
    annonce plus bas une cloture ([réalisé]/[abandonné] ou « RÉALISÉE », « clôturée »).
    C'est le defaut symetrique de la prose perimee : ici c'est la definition qui est
    perimee, et le travail reellement fait passe pour restant a faire."""
    with open(path, encoding="utf-8") as fh:
        lines = fh.readlines()
    defs = []
    for i, line in enumerate(lines):
        m = RE_HEAD.match(line) or RE_ITEM.match(line)
        if m:
            defs.append((i, m.group(1) if m.re is RE_HEAD else m.group(2)))
    out = []
    for k, (i, pid) in enumerate(defs):
        stop = defs[k + 1][0] if k + 1 < len(defs) else len(lines)
        tete = normalise("".join(lines[i:min(stop, i + MAX_TITRE)]))
        m = RE_ETAT.search(tete)
        if not m or m.group(2).lower() not in ("à faire", "en cours"):
            continue
        # Le corps d'une piste-mere ou d'une porte NARRE l'etat d'AUTRES pistes : un
        # marqueur de cloture sur une ligne qui nomme une autre piste ne dit rien de
        # celle-ci. Seule une cloture annoncee sans autre identifiant sur la ligne
        # (« RUN TERMINÉ [...] : [réalisé] ») porte sur la piste courante.
        autre_id = re.compile(_classe_lettres() + r"[0-9]+(?:[.\-][0-9A-Za-z]+)*")
        # La recherche commence juste APRÈS la ligne où se termine le marqueur d'état, et
        # non à `i + MAX_TITRE` comme au premier jet (2026-09-08). Une sous-piste dont le
        # corps tient en moins de 25 lignes et qui annonce sa clôture à la fin échappait
        # alors aux DEUX mécanismes : `parse_file` ne retient que le premier marqueur (donc
        # « ouvert »), et cette boucle ne regardait jamais la zone. Cas `P11.6` de
        # `predictops` : 13 lignes, définition « VERDICT : Reformuler [en cours] », corps
        # terminé par « DÉJÀ EN PLACE, RIEN À DÉPLOYER [réalisé] » -- close depuis le
        # 2026-07-07 et comptée ouverte deux mois. Idem `P20.1`, « [EN COURS DE
        # DÉPLOIEMENT] » puis « [RÉALISÉ ET VÉRIFIÉ FONCTIONNELLEMENT] ».
        # Impact mesuré avant application : +2 sur `predictops`, +4 sur `annotation_mtbc`,
        # 0 sur `voynich` et `lineaire_a` ; les deux cas de `predictops` vérifiés à la main
        # sont de vrais positifs. Le filtre `autre_id` ci-dessous reste la protection
        # contre le corps d'une piste « porte » qui narre l'état d'autres pistes.
        debut = i + tete[:m.end()].count("\n") + 1
        for j in range(debut, stop):
            ligne = normalise(lines[j])
            mm = RE_ETAT.search(ligne)
            if not mm or mm.group(2).lower() not in ("réalisé", "abandonné"):
                continue
            # L'exclusion « cette ligne nomme une AUTRE piste » doit voir la ligne PRÉCÉDENTE.
            # Un corps qui écrit « Sous-piste P16.25a [réalisé\n 2026-08-18 — ... » place le
            # marqueur sur la ligne suivante, où l'identifiant n'apparaît plus : la clôture d'une
            # sous-piste était alors imputée à sa parente (cas P16.25, trouvé le 2026-09-08 en
            # instruisant les 4 signalements que l'élargissement ci-dessus venait d'ajouter).
            contexte = (normalise(lines[j - 1]) + " " + ligne) if j else ligne
            if any(o != pid for o in autre_id.findall(contexte)):
                continue
            # Une clôture QUALIFIÉE est une clôture PARTIELLE, pas une désynchronisation : « réalisé
            # pour le lot Zur/SigG/LexA », « volet littérature RÉALISÉ ; les volets restants
            # ci-dessous ». La piste reste ouverte à bon droit, et la signaler noie le vrai défaut.
            # Deux des quatre signalements de `annotation_mtbc` étaient de ce type.
            fenetre = ligne[max(0, mm.start() - 60):mm.start() + 30].lower()
            if any(k in fenetre for k in (" pour le lot", " pour la ", "volet ", "partiellement",
                                          " en partie", " pour l'", " restants")):
                continue
            out.append((pid, m.group(2).lower(), mm.group(2).lower(), f"{rel}:{i + 1}"))
            break
    return out


def prose_mentions(path, rel, defs_here):
    """Marqueurs d'etat situes HORS de la zone de titre d'une definition : la prose.

    Un marqueur d'etat en fin de ligne appartient a la piste dont cette ligne est le
    CORPS, pas a l'identifiant qui se trouve cite plus tot sur la meme ligne. Sans cette
    distinction, tout renvoi de la forme « (rejoint P8.2). ... [réalisé] » ou « portée
    plus large que P8.6/P8.9). [à faire] » etait lu comme une affirmation sur la piste
    CITEE et compare a son etat -- alors que le marqueur porte sur la piste courante, qui
    est bien dans cet etat. Mesure du 2026-09-08 : 2 signalements sur 2 pour `predictops`
    et 6 sur 10 pour `annotation_mtbc` etaient de ce type, aucun vrai positif perdu."""
    with open(path, encoding="utf-8") as fh:
        lines = fh.readlines()

    # Bornes des definitions, pour attribuer chaque ligne a la piste dont elle est le corps.
    bornes = []
    for i, line in enumerate(lines):
        m = RE_HEAD.match(line) or RE_ITEM.match(line)
        if m:
            bornes.append((i, m.group(1) if m.re is RE_HEAD else m.group(2)))

    def proprietaire(n):
        cur = None
        for i, pid in bornes:
            if i > n:
                break
            cur = pid
        return cur

    out = []
    for i, line in enumerate(lines):
        for m in re.finditer(r"(" + _classe_lettres() + r"[0-9]+(?:[.\-][0-9A-Za-z]+)*)[^\n\[]{0,80}?"
                             + r"\[(" + "|".join(ETATS) + r")[^\]]*\]",
                             normalise(line), re.I):
            pid, etat = m.group(1), m.group(2).lower()
            if RE_ITEM.match(line) or RE_HEAD.match(line):
                continue                    # c'est une definition, pas de la prose
            ref = defs_here.get(pid)
            if not (ref and not ref[0].endswith(etat)):
                continue
            porteur = proprietaire(i)
            if porteur and porteur != pid:
                etat_porteur = defs_here.get(porteur)
                if etat_porteur and etat_porteur[0].endswith(etat):
                    continue                # le marqueur est celui de la piste COURANTE
            out.append((pid, etat, ref[0], f"{rel}:{i + 1}"))
    return out


# Identifiant en TETE de ligne, suivi d'un marqueur d'etat, mais qui n'est ni un titre
# de section ni un item de liste : forme non conforme. Ex. observe le 2026-09-06 sur
# `nucs_deletion_mutators` : les cinq sous-pistes de P5 etaient ecrites
# «   **P5.1** [realise, ...] — ... », donc INVISIBLES au parseur. P5 apparaissait
# alors comme une piste majeure « en cours » sans aucune sous-piste, et l'audit de
# coherence ne pouvait pas conclure : la piste la plus urgente du classement MIU etait
# en realite close depuis la veille. Symetrique du piege de la prose perimee -- la, un
# etat mort passe pour vivant ; ici, une piste entiere disparait du registre.
# Le marqueur de titre optionnel "#..." est tolere ici pour que le filet de securite
# attrape aussi un titre TROP indente (>7 espaces), que RE_HEAD refuse deliberement.
# (compilee par `compiler_identifiants`, meme remarque que `RE_HEAD` plus haut)


def definitions_non_reconnues(path, rel):
    """Lignes qui RESSEMBLENT a une definition (identifiant en tete + marqueur d'etat)
    sans en avoir la forme. Rendues telles quelles ; c'est l'appelant qui ecarte
    celles dont l'identifiant est defini correctement ailleurs."""
    out = []
    with open(path, encoding="utf-8") as fh:
        for i, line in enumerate(fh):
            if RE_ITEM.match(line) or RE_HEAD.match(line):
                continue
            m = RE_ORPHELIN.match(normalise(line))
            if m:
                out.append((m.group(1), m.group(2).lower(), f"{rel}:{i + 1}"))
    return out


def etats_hors_nomenclature(states):
    """Etat capte avec un QUALIFICATIF EN AMONT (« partiellement realise », « clos
    realise »...). La nomenclature imposee n'a que quatre etats ; tout le reste sort
    silencieusement de `--open` alors que la piste est bel et bien ouverte -- cas
    P2.15.2, `[partiellement realise]`, invisible jusqu'au 2026-09-06."""
    return [(pid, etat, src) for pid, (etat, src, _) in states.items()
            if etat != "état non déclaré" and etat not in ETATS]


# Mots par lesquels un registre annonce une cloture SANS employer la nomenclature.
# Volontairement restreint a ce qui ne peut pas vouloir dire autre chose : « verifie »
# ou « en attente » decrivent aussi une piste ouverte et n'ont donc rien a faire ici.
MOTS_CLOTURE = ("close", "clos", "cloturee", "cloturée", "clôturée", "clôture",
                "déployé", "deploye", "déployée", "réalisé", "realise", "réalisée",
                "résolu", "resolu", "résolue", "abandonné", "abandonne", "abandonnée",
                "réfutée", "refutee", "livré", "livre", "livrée")

# Symetrique du precedent : une etiquette libre qui annonce, en toutes lettres, que le
# travail N'EST PAS fini. Meme discipline de choix -- rien qui puisse vouloir dire autre
# chose. « vérifié » decrit une cloture, « à vérifier » une reserve : la locution entiere
# est donc exigee, jamais le radical. Ces mots servent a trouver les sous-pistes VIVANTES
# enterrees sous une piste majeure close, cas mesure sur `predictops` le 2026-09-08
# (P19.2, « la condition de clôture échoue », sous un P19 « réalisé »).
#
# « reste à » en a ete RETIRE apres mesure : sur les cinq cas rendus par le premier jet,
# P11.7 (« les deux "reste à faire" de P11.6 traités ») etait un faux positif, la locution
# y etant CITEE au passe pour annoncer leur traitement. Un mot qui peut apparaitre dans le
# recit de sa propre levee n'a rien a faire ici -- meme discipline que pour MOTS_CLOTURE.
# Le compteur n'est pas le verdict : c'est en LISANT les cinq qu'on l'a vu (leçon P70.5).
MOTS_RESERVE = ("échec", "echec", "à reprendre", "a reprendre", "en attente",
                "non déployé", "non deploye", "non déployée", "requise", "requis",
                "bloqué", "bloque", "bloquée", "à instruire", "a instruire",
                "à trancher", "a trancher", "à arbitrer",
                "a arbitrer", "à vérifier", "a verifier", "à confirmer", "a confirmer",
                "suspendu", "suspendue", "non traité", "non traite", "non traitée")


def etats_non_declares(states, majeures):
    """Pistes MAJEURES dont l'etiquette d'en-tete ne contient AUCUN des quatre etats.

    Trou decouvert le 2026-09-08 sur `predictops` : 24 pistes majeures sur 69 portaient
    une etiquette libre et descriptive (« [CLOSE POSITIVEMENT 2026-08-22] », « [DÉPLOYÉ,
    RECETTE IMMÉDIATE RÉUSSIE] », « [CAUSE ÉTABLIE, CORRECTIF PRÊT, NON DÉPLOYÉ] ») au
    lieu d'un des quatre etats imposes. Consequences, toutes silencieuses :

      - `--open` les rend TOUTES (choix prudent, ligne `r[1][0] == "état non déclaré"`),
        donc il annoncait 32 pistes ouvertes la ou il y en avait environ 8 -- une liste
        fausse par exces, exactement le defaut que ce script existe pour empecher ;
      - `etats_hors_nomenclature` ne les voit PAS, puisqu'elle exclut explicitement
        « état non déclaré » : une etiquette qui ne contient aucun des quatre mots
        n'etait signalee nulle part ;
      - le desaccord index/detail ne les voit pas non plus quand les DEUX faces portent
        la meme etiquette libre et perimee -- cas `P67` du 2026-09-08, ou l'en-tete
        annoncait « CORRECTIF PRÊT, NON DÉPLOYÉ » des deux cotes alors que le corps de
        la piste consignait le deploiement de la veille. Un faux feu vert de deploiement
        a ete demande a l'utilisateur sur cette base.

    `cloture_probable` distingue le cas le plus couteux : une etiquette qui annonce en
    toutes lettres une cloture que la nomenclature ignore, donc une piste close comptee
    comme ouverte. Les autres sont seulement indecidables.
    """
    out = []
    for pid in sorted(majeures, key=sort_key):
        # `majeures` est un ensemble de RACINES : il peut porter l'identifiant d'une
        # piste majeure jamais definie elle-meme (seules ses sous-pistes existent).
        # Ce cas releve de `definitions_non_reconnues`, pas d'ici.
        if pid not in states:
            continue
        etat, src, lib = states[pid]
        if etat != "état non déclaré":
            continue
        bas = normalise(lib).lower()
        out.append((pid, src, lib, any(m in bas for m in MOTS_CLOTURE)))
    return out


# --------------------------------------------------------------------------
# Clôture ASSUMÉE : une majeure close qui PORTE une sous-piste ouverte
# --------------------------------------------------------------------------
# Ajouté le 2026-09-09, sur arbitrage CG, après trois occurrences de la même
# fausse alerte en une journée sur `mtbc/Rv2566`. Le contrôle
# `majeure_close_sous_piste_ouverte` est juste dans son principe, mais il
# était INEFFAÇABLE : le hook `Stop` demande de « consigner pourquoi c'est
# assumé », et consigner ne décrémentait aucun compteur, faute pour la sonde
# de savoir lire la justification. Un contrôle qui reproche indéfiniment un
# cas justifié cesse d'être lu, ce que l'en-tête du hook identifie lui-même
# comme son principal mode d'échec.
#
# La convention reconnue est celle déjà employée dans le dépôt : une note en
# GRAS `**Assumé**` dans l'en-tête de la piste majeure, qui NOMME la ou les
# sous-pistes laissées ouvertes délibérément. Exiger le nom est ce qui
# empêche une note vague d'absoudre d'un coup toutes les sous-pistes ouvertes
# d'une racine.
RE_ASSUME = re.compile(r"\*\*\s*assum", re.I)


def _entete_majeure(path, ligne_def):
    """Les lignes d'en-tête d'une piste majeure : de sa ligne de définition à sa
    première sous-piste, 80 lignes au plus. Au-delà, c'est du corps, et une note
    perdue au milieu du corps ne vaut pas déclaration."""
    try:
        with open(path, encoding="utf-8") as fh:
            lignes = fh.readlines()
    except OSError:
        return ""
    debut = max(0, ligne_def - 1)
    out = []
    for ln in lignes[debut:debut + 80]:
        if out and RE_ITEM.match(ln):
            break
        out.append(ln)
    return "".join(out)


def cloture_assumee(root, src_majeure, pid_sous):
    """La piste majeure DIT-elle assumer cette sous-piste ouverte ?

    Vrai seulement si son en-tête porte une note en gras `**Assumé**` ET nomme
    explicitement `pid_sous`. Les deux conditions comptent : la première rend la
    déclaration visible à un lecteur humain, la seconde empêche qu'une note
    générale ne neutralise un défaut réel apparu plus tard sous la même racine."""
    rel, sep, num = src_majeure.rpartition(":")
    if not sep:
        return False
    try:
        ligne = int(num)
    except ValueError:
        return False
    txt = _entete_majeure(os.path.join(root, rel), ligne)
    if not RE_ASSUME.search(txt):
        return False
    return re.search(r"\b" + re.escape(pid_sous) + r"(?![0-9A-Za-z.\-])", txt) is not None


def majeure_close_sous_piste_ouverte(states, root=None):
    """Piste MAJEURE close alors qu'une de ses sous-pistes est DÉCLARÉE ouverte.

    Règle arbitrée par l'utilisateur le 2026-09-08 (P70.9 de `predictops`) : une piste
    majeure ne peut pas rester close tant qu'une sous-piste porte `à faire` ou `en cours`.
    Elle repasse `en cours` avec un qualificatif nommant la réserve, le format instauré
    par P70.4 (« [en cours, TRAVAIL PRINCIPAL CLOS, RÉSERVE X OUVERTE] »).

    C'est le SENS D'ERREUR LE PLUS COÛTEUX, et c'est ce qui justifie zéro pour valeur
    cible : un en-tête trop optimiste fait croire qu'un travail est fini. Le cas fondateur
    de tout ce chantier est exactement celui-là -- `P67` annonçait un état périmé, et un
    faux feu vert de déploiement en PRODUCTION a été demandé à l'utilisateur sur cette base.

    Aucune heuristique ici, contrairement à `reliquats_sous_parent_clos` : l'incohérence
    est formelle, les deux états sont déclarés. Le contrôle ne dit pas laquelle des deux
    faces a tort -- une sous-piste peut aussi porter une étiquette périmée, cas mesuré le
    même jour sur `P11.6` et `P19.3`, closes depuis des semaines et comptées ouvertes. LIRE
    avant de rouvrir la majeure : sur douze cas, deux ont été résolus en clôturant la
    sous-piste, pas en rouvrant le parent."""
    out, assumees = [], []
    for pid in sorted(states, key=sort_key):
        rac_pid = racine(pid)
        if pid == rac_pid or rac_pid not in states:
            continue
        etat, src, lib = states[pid]
        if not etat.endswith(("à faire", "en cours")):
            continue
        if not states[rac_pid][0].endswith(("réalisé", "abandonné")):
            continue
        ligne = (pid, mot_etat(etat), rac_pid,
                 mot_etat(states[rac_pid][0]), src, lib)
        if root is not None and cloture_assumee(root, states[rac_pid][1], pid):
            assumees.append(ligne)      # déclaré, donc pas un défaut
        else:
            out.append(ligne)
    return out, assumees


def reliquats_sous_parent_clos(states):
    """SOUS-pistes sans etat declare dont la piste MAJEURE est close, et dont l'etiquette
    annonce au contraire une RESERVE OUVERTE. Ce sont des pistes vivantes enterrees.

    Contexte (P70.8 de `predictops`, 2026-09-08). `etats_non_declares` ne regarde que les
    pistes majeures, choix delibere : sur PredictOps, 0 majeure sans etat mais 112
    SOUS-pistes, dont 83 sous une majeure deja close. Reclamer un etat pour les 83 ferait
    du bruit sans fin ; leur faire HERITER de l'etat du parent a ete teste puis REFUTE sur
    un echantillon stratifie de dix, une par racine :

      - P19.2 « RECETTE SUR BULLETINS RÉELS [ÉCHEC, CORRECTIF À REPRENDRE] », dont le corps
        dit « la condition de clôture échoue », sous un P19 « réalisé » ;
      - P34.1bis « OPTION DE REPLI, COORDINATION NICOLAS REQUISE », dont le corps precise
        qu'« aucun déploiement n'est autorisé par la seule existence du protocole » ;
      - P12.4 « Leçon méthodo générale (KB) », qui n'est ni ouverte ni close mais n'est PAS
        une direction de travail -- troisieme categorie que les quatre etats ne couvrent
        pas, et a laquelle il est vain d'en demander un.

    Heriter aurait donc marque close une piste dont le libelle dit l'inverse : une liste
    fausse par DEFAUT, la pire des deux (cf. P70.7 -- une piste ouverte qui disparait ne se
    signale jamais elle-meme, la ou une liste trop longue est bruyante donc corrigee).

    D'ou ce controle, qui ne compte QUE le cas actionnable et laisse le reste en contexte :
    trouver les quelques pistes vivantes enterrees, pas etiqueter 83 lignes."""
    majeures_closes = {pid for pid, (etat, _s, _l) in states.items()
                       if pid == racine(pid) and etat.endswith(("réalisé", "abandonné"))}
    out, indecidables, closes = [], [], []
    for pid in sorted(states, key=sort_key):
        etat, src, lib = states[pid]
        if etat != "état non déclaré" or pid == racine(pid):
            continue
        if racine(pid) not in majeures_closes:
            continue
        bas = normalise(lib).lower()
        if any(m in bas for m in MOTS_RESERVE):
            out.append((pid, src, lib))
        elif any(m in bas for m in MOTS_CLOTURE):
            closes.append(pid)
        else:
            indecidables.append(pid)
    return out, closes, indecidables


# --------------------------------------------------------------------------------
# CONTROLE BIDIRECTIONNEL cahier <-> detail <-> index (P29.9/P29.10, 2026-09-06)
#
# Les controles ci-dessus ne regardent que la COHERENCE INTERNE du registre. Ils sont
# aveugles aux deux dereglements qui ont fait perdre de la memoire de recherche sur
# `annotation_mtbc` les 2026-08-30 et 2026-09-05, et aucun des deux ne leve d'erreur :
#
#   Sens 1 -- le DETAIL perd son contenu pendant que l'index continue de resumer un
#   travail fait. `pistes/P42.md` reduit a un stub de 4 lignes, `pistes/P40.md` ecrase
#   par une version ANTERIEURE de lui-meme. Le critere employe alors (« contenu utile
#   byte-identique au bloc d'index ») ne voyait ni l'un ni l'autre. Le seul test qui
#   tranche est la confrontation au CAHIER append-only : toute sous-piste `Px.y` nommee
#   par une entree de cahier doit exister dans `pistes/Px.md`.
#
#   Sens 2 -- l'INDEX ment sur un fichier qu'on a justement evite d'ouvrir. Une session
#   met `pistes/P37.md` a jour sans toucher la ligne d'index, qui reste sur l'etat de la
#   veille. C'est le defaut que l'architecture index + detail rend le plus couteux.
#
# D'ou un controle a deux faces, qui SIGNALE sans jamais trancher a la place de l'auteur.
# --------------------------------------------------------------------------------

# Identifiant de SOUS-piste : au moins un separateur. `P8` seul est trop bruyant dans un
# cahier (il y est nomme a chaque entree), `P8.6i` ne l'est pas.
# Le `\.?` hors groupe capturant accepte le point de FIN DE PHRASE : « la sous-piste
# P1.99. » etait sinon perdue en entier, le lookahead rejetant le point puis le
# backtracking echouant -- exactement le piege corrige sur `RE_ITEM` en P70.5, mais resté
# non corrige ici. Faux NEGATIF silencieux, et le pire endroit pour en avoir : ce controle
# existe pour detecter la memoire de recherche perdue, et une sous-piste nommee en fin de
# phrase y echappait. Impact mesure sur quatre projets le 2026-09-08 : +2, +1, +5 et +0
# identifiants captes, aucun changement de compteur (tous ecartes par `pid_plausible` ou
# deja presents au registre) -- meilleur rappel a cout nul.
# (compilee par `compiler_identifiants`, meme remarque que `RE_HEAD` plus haut -- ne
# retient QUE la ou les lettres reellement vues dans le registre DE CE PROJET, jamais
# n'importe quelle lettre majuscule : un cahier MTBC regorge de codes de lignee `L4`,
# `L6.5`... et d'identifiants de tache `agentctl` `T18142`, qui ne sont pas des pistes.)
RE_MAJ = re.compile(r"\bmaj\s*:\s*(\d{4}-\d{2}-\d{2})")

# Un cahier de labo ecrit beaucoup de choses qui RESSEMBLENT a un identifiant sans en etre
# un. Mesure sur `annotation_mtbc` le 2026-09-07 : sans ce crible, 60 % des signalements
# etaient du bruit, et un controle bruyant ne se lit plus -- c'est le mode d'echec le plus
# probable de ce garde-fou, pas le faux negatif.
EXT_FICHIER = {"md", "py", "json", "tsv", "csv", "txt", "sh", "html", "log", "bib",
               "tex", "png", "pdf", "yaml", "yml", "js", "css", "bak"}
PLACEHOLDER = {"x", "y", "z", "n"}


def racine(pid):
    """Racine d'un identifiant, independamment de la lettre de prefixe employee (« P »
    historique, « A » sur `archeo_crispr`...) : le prefixe est celui REELLEMENT en tete
    de `pid`, jamais une lettre hardcodee.

    DEUX CONVENTIONS DE REGISTRE, pas une (2026-09-21, piste AE de `environnement`). Dans
    la convention historique, la piste majeure porte un chiffre (`## P2.`) et ses sous-pistes
    un suffixe pointe (`P2.13`) : la racine de `P2.13` est `P2`, et c'est ce que fait le
    calcul ci-dessous. Dans la convention « hors rail » du meme depot, la majeure est un
    PREFIXE NU (`## S.`, `## AA.`) et ses sous-pistes sont numerotees sans point (`S7`,
    `AA2`) : la racine de `S7` est `S`, alors que le meme calcul rendait `S7` -- chaque
    sous-piste passait donc pour sa propre majeure. Consequence mesuree sur `environnement` :
    le bloc de pistes ouvertes injecte au demarrage de session annoncait « 1 piste majeure
    ouverte sur 10 » la ou le registre en portait 8 sur 29, parce qu'aucune racine nue
    n'etait jamais rapprochee de l'etat de sa majeure. Une piste ouverte absente du contexte
    de demarrage est une piste oubliee : c'est le mode d'echec que ce script existe pour
    empecher, ici par un autre chemin que le `grep` qu'il a remplace.

    On ne devine pas la convention : `RACINES_NUES` ne contient que les prefixes pour
    lesquels `amorcer()` a VU un `pistes/<PREFIXE>.md` sans chiffre, c'est-a-dire une
    declaration explicite de majeure nue. Sur les ~270 projets historiques (tous en
    `pistes/P<n>.md`) cet ensemble est vide et le comportement est inchange PAR
    CONSTRUCTION, pas seulement par mesure."""
    m = re.match(r"^[A-Z]+", pid)
    prefixe = m.group(0) if m else ""
    if prefixe and prefixe in RACINES_NUES:
        return prefixe
    return prefixe + re.split(r"[.\-]", pid[len(prefixe):])[0]


def canon(pid):
    """`P2.09` et `P2.9` sont le meme identifiant : le zero non significatif est une
    coquille de frappe du cahier, pas une sous-piste absente."""
    return re.sub(r"(?<=[.\-" + _lettres_str() + r"])0+(?=[0-9])", "", pid)


def pid_plausible(pid):
    """Ecarte ce qui n'est pas un identifiant de sous-piste. Quatre formes observees :
      - un CHEMIN de fichier -- `pistes/P8.md`, capte comme sous-piste « md » ;
      - une PLAGE -- `P1-P18`, `P2.9-P2.11`, `P16.17-24` (« de P16.17 a P16.24 ») ;
      - un GABARIT -- `P16.2a-sexies-bis.x`, ou `x` tient lieu de numero ;
      - un mot colle -- `P16-like`.
    Le point est le separateur canonique de profondeur (`P16.2a-sexies-bis.4`) : exiger
    au moins un point elimine d'un coup les plages en `-` et les mots colles, sans rien
    perdre de la nomenclature reellement utilisee."""
    if "." not in pid:
        return False
    if re.search(r"-" + _classe_lettres() + r"[0-9]", pid):   # plage « P2.9-P2.11 »
        return False
    # SUFFIXE DE VERSION d'un artefact, pas une sous-piste : « P59.4bis-v1 », le
    # protocole gelé issu de P59.4bis, ou « P59.7bis-v1 », son pilote archivé. Les deux
    # etaient signales comme sous-pistes perdues de `predictops` le 2026-09-08 alors
    # qu'aucune n'a jamais ete une piste. Rejet limite au segment FINAL introduit par un
    # tiret, pour ne pas toucher a une numerotation legitime.
    if re.search(r"-v[0-9]+$", pid, re.I):
        return False
    parts = pid[1:].split("-")
    if any(p.split(".")[0].isdigit() for p in parts[1:]):  # plage « P16.17-24 »
        return False
    segs = [s.lower() for s in re.split(r"[.\-]", pid[1:])]
    if any(s in EXT_FICHIER for s in segs):                # chemin « pistes/P2.md.bak »
        return False
    if segs[-1] in PLACEHOLDER:
        return False
    # mot colle en qualificatif : « P2.14.1-style ». La numerotation latine du depot
    # (`-sexies-bis`) est la seule serie de mots longs legitime.
    return not any(s.isalpha() and len(s) >= 4 and s not in ORDINAUX for s in segs)


def mot_etat(etat):
    """Reduit « **RÉALISÉ, toutes sous-pistes closes** » a « réalisé » : deux faces du
    registre peuvent qualifier le meme etat differemment sans etre en desaccord."""
    for e in ETATS:
        if etat.endswith(e):
            return e
    return etat


def identifiants_cahier(root):
    """{id de sous-piste: [(fichier, ligne), ...]} sur tous les `cahier_de_labo*.md`."""
    out = {}
    if not os.path.isdir(root):
        return out
    for fn in sorted(os.listdir(root)):
        if not (fn.startswith("cahier_de_labo") and fn.endswith(".md")):
            continue
        with open(os.path.join(root, fn), encoding="utf-8", errors="replace") as fh:
            for i, line in enumerate(fh, 1):
                for m in RE_PID_CAHIER.finditer(line):
                    if pid_plausible(m.group(1)):   # group(1) : sans le point final
                        out.setdefault(m.group(1), []).append((fn, i))
    return out


def _porte(txt, pid):
    return any(re.search(re.escape(f) + r"(?![0-9A-Za-z.\-])", txt)
               for f in {pid, canon(pid)})


def completude_cahier(root, ids_cahier, majeures, states):
    """Sens 1. Rend (absents, ailleurs, inconnus) -- trois gravites distinctes, et la
    distinction n'est pas cosmetique : melangees, elles rendent le controle illisible et
    donc inutile.

    `absents` : sous-piste nommee par le cahier et introuvable dans TOUT le registre
    (detail, index, archive figee). C'est le signal fort, celui qui a manque le
    2026-08-30 sur P40/P42. Deux lectures possibles, que l'outil ne tranche pas : le
    registre a perdu la sous-piste, ou elle n'y a jamais ete inscrite (une session l'a
    numerotee dans le recit du cahier sans la porter a l'arbre). Dans les deux cas,
    quelque chose de documente n'est pas dans les pistes.
    `ailleurs` : absente du fichier de detail mais presente dans `pistes_archive.md` ou
    dans l'index -- MIGRATION INCOMPLETE, pas perte. Le corps existe, il n'est pas au bon
    endroit ; observe sur `annotation_mtbc` pour P18.9/P18.17/P18.21, restes dans
    l'archive figee que le decoupage index+detail etait cense vider.
    `inconnus` : identifiant dont meme la piste majeure est etrangere au registre --
    presque toujours un renvoi a un AUTRE projet (`P57.3 du depot`), informationnel.

    Le test est la presence TEXTUELLE de l'identifiant, pas sa presence dans `states` :
    on cherche une perte de CONTENU, une forme de definition non conforme etant deja
    couverte par `definitions_non_reconnues`."""
    absents, ailleurs, inconnus, cache = [], [], [], {}

    def lire(p):
        if p not in cache:
            cache[p] = ""
            if os.path.isfile(p):
                with open(p, encoding="utf-8", errors="replace") as fh:
                    cache[p] = fh.read()
        return cache[p]

    index = os.path.join(root, "pistes.md")
    ddir = os.path.join(root, "pistes")
    # Ordre de secours, du plus benin au plus revelateur. Les DEUX premieres sources ont
    # ete trouvees en mesurant les faux positifs du premier jet sur `annotation_mtbc`
    # (2026-09-07), et chacune correspond a un geste legitime du dispositif :
    #   - un autre `pistes/Py.md` : un REDECOUPAGE (`/recadrage`) deplace des sous-pistes
    #     vers une autre piste majeure sans les renumeroter -- P16.21a-f vivent dans
    #     `pistes/P34.md`, P16.19a-d dans `pistes/P33.md`. Chercher sous la seule racine
    #     de l'identifiant les declarait perdues alors qu'elles etaient rangees.
    #   - le registre du DEPOT PARENT : le cahier d'un projet discute les pistes du
    #     registre de serendipite racine (`mtbc/pistes.md`), qui a sa propre numerotation
    #     -- « P33.2 » y designe autre chose que le P33 local. Collision de registres,
    #     pas piste perdue.
    parent = os.path.join(os.path.dirname(root), "pistes.md")
    for pid, occ in sorted(ids_cahier.items(), key=lambda kv: sort_key(kv[0])):
        major = racine(pid)
        detail = os.path.join(ddir, f"{major}.md")
        if not os.path.isfile(detail):
            if major not in majeures:
                inconnus.append((pid, len(occ), occ[-1]))
                continue
            detail = index                            # projet non encore migre
        rel_detail = os.path.relpath(detail, root)

        # 1. La sous-piste est-elle DEFINIE quelque part ? `states` le sait exactement,
        # la ou une recherche textuelle confondrait une definition avec une mention en
        # prose (« cf. P16.21a ») -- premier jet du 2026-09-07, qui annoncait « corps
        # dans pistes/P18.md » pour une sous-piste dont le corps est dans P34.md.
        src = states.get(pid) or states.get(canon(pid))
        if src:
            fichier = src[1].split(":")[0]
            if fichier != rel_detail:
                ailleurs.append((pid, len(occ), fichier, rel_detail))
            continue
        # 2. Pas de definition : presence textuelle dans son propre fichier ? Alors le
        # corps est la, sous une forme que le parseur ne reconnait pas -- c'est le
        # controle « forme non conforme » qui traite ce cas, pas celui-ci.
        if _porte(lire(detail), pid):
            continue
        secours = next(
            (p for p in [os.path.join(root, "pistes_archive.md"), index, parent]
             if p != detail and _porte(lire(p), pid)), None)
        if secours:
            rel = (os.path.relpath(secours, root) if secours != parent
                   else f"{os.path.basename(os.path.dirname(root))}/pistes.md (dépôt parent)")
            ailleurs.append((pid, len(occ), rel, rel_detail))
        else:
            absents.append((pid, len(occ), occ[-1], rel_detail))
    return absents, ailleurs, inconnus


def blocs_index(path):
    """{Px: texte du bloc d'index}, du titre `## Px.` au titre suivant.

    BORNES DE BLOC ET PREFIXE NU (2026-09-21, piste AE de `environnement`). `RE_HEAD`
    exige un CHIFFRE apres la racine (`id_racine = <lettres> + [0-9]+`), ce qui est juste
    pour une SOUS-piste mais faux pour une piste MAJEURE qui n'est qu'une lettre de racine,
    sa numerotation ne commencant qu'aux sous-pistes : `## S.` + `- S1`, `## AA.` + `- AA1`.
    Ces titres n'etant alors reconnus comme bornes par PERSONNE, le bloc de la derniere
    piste NUMEROTEE qui precede avale tout le texte jusqu'a la prochaine piste numerotee.
    Mesure sur `environnement` : le bloc de `P8` s'etendait jusqu'a `## P9.`, avalant les
    deux titres hors plan plus `N`, `O`, `Q`, `R`, `S`, `T`, `U` -- si bien qu'une ligne
    `maj : <date>` ecrite sous `## S.` etait attribuee a `P8`, et `desaccord_index_detail`
    signalait une divergence de date sur une piste a laquelle cette date n'appartenait pas
    (fausse alerte du hook `Stop`, diagnostiquee le 2026-09-21). Effet de bord voulu du
    correctif : ces pistes majeures entrent ENFIN dans la comparaison index/detail, dont
    elles etaient exclues en silence (faux negatif, jamais visible comme tel).

    On n'elargit PAS `RE_HEAD` lui-meme, lu par une douzaine de fonctions dont le parsing
    d'items : la borne nue est detectee ici seulement, sur les seuls prefixes REELLEMENT
    vus dans ce projet (`_classe_lettres`), avec le point ou l'espace obligatoire apres --
    un titre de prose ne peut donc devenir une borne que s'il commence exactement par un
    prefixe du projet suivi d'un point."""
    out = {}
    with open(path, encoding="utf-8", errors="replace") as fh:
        lines = fh.readlines()
    re_borne_nue = re.compile(r"^[ \t]{0,7}#{1,6}\s+\*{0,2}(" + _classe_lettres()
                              + r")\*{0,2}[.\s]")
    heads = []
    for i, l in enumerate(lines):
        m = RE_HEAD.match(l) or re_borne_nue.match(l)
        if m:
            heads.append((i, m.group(1)))
    for k, (i, pid) in enumerate(heads):
        stop = heads[k + 1][0] if k + 1 < len(heads) else len(lines)
        out.setdefault(pid, "".join(lines[i:stop]))
    return out


def derniere_maj(txt):
    ds = RE_MAJ.findall(txt)
    return max(ds) if ds else None


def desaccord_index_detail(root, index_states, detail_states):
    """Sens 2. Compare les DEUX faces de chaque piste majeure : etat, puis fraicheur.
    Ne tranche pas -- dit seulement laquelle est en retard, et de combien."""
    index = os.path.join(root, "pistes.md")
    ddir = os.path.join(root, "pistes")
    if not (os.path.isfile(index) and os.path.isdir(ddir)):
        return [], []
    blocs = blocs_index(index)
    etats, dates = [], []
    for pid, bloc in sorted(blocs.items(), key=lambda kv: sort_key(kv[0])):
        dpath = os.path.join(ddir, f"{pid}.md")
        if not os.path.isfile(dpath):
            continue
        with open(dpath, encoding="utf-8", errors="replace") as fh:
            dtxt = fh.read()
        ei = mot_etat(index_states.get(pid, ("état non déclaré",))[0])
        ed = mot_etat(detail_states.get(pid, ("état non déclaré",))[0])
        if ei != ed:
            etats.append((pid, ei, ed))
        mi, md = derniere_maj(bloc), derniere_maj(dtxt)
        if mi and md and mi != md:
            dates.append((pid, mi, md, "index" if mi < md else "détail"))
    return etats, dates


# --------------------------------------------------------------------------------
# COLLECTE, separee de l'AFFICHAGE (2026-09-08, P70.6 de `predictops`)
#
# `--audit` n'a longtemps rendu que du texte sur stderr, ce qui suffit tant qu'un
# humain le lance. Rien ne le garantissait : le SKILL.md le prescrit a chaque
# `/pistes read`, mais une consigne n'est pas un mecanisme, et pendant les deux
# jours ou personne ne l'a lance, `P67` a menti sur son etat au point qu'un faux
# feu vert de deploiement en production a ete demande a l'utilisateur.
#
# Pour qu'un HOOK puisse le lancer seul, il faut des COMPTEURS, pas des phrases.
# D'ou cette collecte, qui rend les memes controles sous forme structuree :
# `--audit` n'en est plus qu'un affichage, et la sonde du hook ne peut donc pas
# diverger du texte au premier controle ajoute -- ce qu'une reimplementation cote
# hook aurait garanti a breve echeance.
# --------------------------------------------------------------------------------

# (cle, libelle court pour la sonde, zero attendu d'un registre sain ?)
#
# `zero_attendu` distingue ce qu'un registre sain DOIT afficher a zero du bruit
# structurel connu et deja instruit. La distinction n'est pas cosmetique : une sonde
# qui reclame zero partout parle a chaque session, donc cesse d'etre lue -- mode
# d'echec deja mesure sur `completude_cahier` (cf. son commentaire : 60 % de bruit
# avant crible). Les deux controles tolerants le sont pour une raison etablie le
# 2026-09-08 sur `predictops` (P70.5) : le cahier append-only nomme des identifiants
# qui n'ont jamais ete des pistes -- un script, une piste d'un AUTRE projet, une
# version d'artefact -- et six des huit cas restants n'y sont pas filtrables
# mecaniquement. Ecrire au cahier une analyse qui NOMME des identifiants suffit
# d'ailleurs a en creer de nouveaux, le cahier ne se corrigeant pas.
SECTIONS_AUDIT = (
    ("prose",             "mention(s) en prose contredisant l'état courant",     True),
    ("cloture_muette",    "clôture(s) possiblement non répercutée(s)",           True),
    ("forme",             "piste(s) absente(s) du registre (forme non conforme)", True),
    ("cahier_absents",    "sous-piste(s) du cahier introuvable(s) au registre",  False),
    ("cahier_restees",    "sous-piste(s) restée(s) dans l'archive ou l'index",   True),
    ("cahier_ailleurs",   "sous-piste(s) rangée(s) sous une autre racine",       False),
    ("desaccord_etat",    "piste(s) majeure(s) index/détail en désaccord d'état", True),
    ("desaccord_dates",   "date(s) de `maj :` divergente(s) entre index et détail", True),
    ("hors_nomenclature", "état(s) hors nomenclature",                           True),
    ("non_declares",      "piste(s) majeure(s) sans état déclaré",               True),
    ("reliquats_enterres", "sous-piste(s) VIVANTE(S) sous une piste majeure close", True),
    ("majeure_incoherente", "piste(s) majeure(s) close(s) portant une sous-piste ouverte", True),
    ("sans_etiquette",    "feuille(s) ouverte(s) sans étiquette modèle/effort",   False),
)


def feuilles_sans_etiquette(states):
    """Feuilles OUVERTES (aucune sous-piste sous elles) qui ne portent pas d'étiquette
    `[Modèle:effort]`. Tolérant (`zero_attendu` faux) : l'étiquetage se pose à la
    réouverture d'un projet, jamais en masse, donc un reste est normal et informatif."""
    ouvertes = [pid for pid, (etat, _s, _l) in states.items()
                if etat.endswith("à faire") or etat.endswith("en cours")]
    out = []
    for pid in ouvertes:
        prefixe = pid + "."
        # DEUX CONVENTIONS DE PARENTE, comme dans `racine()` : suffixe pointe (`P1` ->
        # `P1.2`) ET racine nue (`AB` -> `AB7`, sans point). Le seul `startswith(pid + ".")`
        # ne voyait pas la seconde : sur `environnement` (2026-09-22), les trois majeures
        # ouvertes AB/AF/AG etaient comptees comme des FEUILLES sans etiquette, alors qu'une
        # majeure a sous-pistes n'en porte deliberement pas -- 7 signalements la ou 1 etait
        # du. Un controle tolerant qui reproche l'inevitable cesse d'etre lu.
        if any(autre != pid and (autre.startswith(prefixe) or racine(autre) == pid)
               for autre in states):
            continue
        if pid not in ETIQUETTES:
            out.append(pid)
    return sorted(out, key=sort_key)


def sources_registre(root):
    """[(chemin, libelle relatif)] : l'index d'abord (pistes majeures), les details
    ensuite -- ils PRIMENT, l'index n'etant qu'un resume."""
    out = []
    index = os.path.join(root, "pistes.md")
    detail_dir = os.path.join(root, "pistes")
    if os.path.isfile(index):
        out.append((index, "pistes.md"))
    if os.path.isdir(detail_dir):
        for fn in sorted(os.listdir(detail_dir)):
            if fn.endswith(".md"):
                out.append((os.path.join(detail_dir, fn), f"pistes/{fn}"))
    return out


def lire_registre(root, avec_audit=False, amorce=True):
    """Rend (states, index_states, detail_states, prose, stale, orphelins).

    Amorce le module pour `root` par defaut (cf. `amorcer`) : c'est la porte d'entree de
    tous les appelants-bibliotheque, et l'amorçage y est idempotent. `amorce=False` pour
    un appelant qui a deja amorce lui-meme et veut eviter le second `listdir`."""
    if amorce:
        amorcer(root)
    states, prose, stale, orphelins = {}, [], [], []
    index_states, detail_states = {}, {}
    for path, rel in sources_registre(root):
        here = parse_file(path, rel)
        (index_states if rel == "pistes.md" else detail_states).update(here)
        states.update(here)                 # le détail écrase l'index
        if avec_audit:
            prose += prose_mentions(path, rel, here)
            # L'index `pistes.md` est narratif par construction (il resume l'etat de
            # dizaines de sous-pistes dans la prose d'une piste majeure) : ce controle
            # n'y produirait que du bruit. Seuls les fichiers de detail font foi.
            if rel != "pistes.md":
                stale += cloture_non_repercutee(path, rel)
                orphelins += definitions_non_reconnues(path, rel)
    return states, index_states, detail_states, prose, stale, orphelins


def collecte_audit(root, lu=None):
    """Rend {cle: {"n": int, "zero_attendu": bool, "libelle": str, "items": [...]}}
    pour les dix controles, plus `inconnus` (informationnel, jamais compte). Aucune
    impression : c'est l'appelant qui decide d'en faire du texte ou un compteur."""
    amorcer(root)          # idempotent : `lu` a pu etre lu par un appelant non amorce
    states, index_states, detail_states, prose, stale, orphelins = (
        lu if lu is not None else lire_registre(root, avec_audit=True, amorce=False))

    muettes = [o for o in orphelins if o[0] not in states]
    majeures = {racine(pid) for pid in states}
    absents, ailleurs, inconnus = completude_cahier(
        root, identifiants_cahier(root), majeures, states)

    # `ailleurs` est domine par un geste LEGITIME et massif -- un redecoupage
    # `/recadrage` deplace des dizaines de sous-pistes d'un coup. Seul le deuxieme
    # groupe appelle une action, d'ou la ventilation ici et non a l'affichage.
    groupes, restees, empruntes = {}, [], []
    for pid, n, src, dest in ailleurs:
        if "(dépôt parent)" in src:
            empruntes.append(pid)
        elif src in ("pistes_archive.md", "pistes.md"):
            restees.append((pid, n, src, dest))
        else:
            groupes.setdefault((racine(pid), src), []).append(pid)
    # Rendu en LISTE et non en dict a cles tuple : la sortie doit rester serialisable
    # en JSON, `--audit-json` etant la raison d'etre de cette collecte.
    redecoupe = [[rac, src, sorted(pids, key=sort_key)]
                 for (rac, src), pids in sorted(groupes.items())]

    det, dat = desaccord_index_detail(root, index_states, detail_states)
    muets = etats_non_declares(states, majeures)
    enterres, sous_closes, sous_indecidables = reliquats_sous_parent_clos(states)
    incoherentes, assumees = majeure_close_sous_piste_ouverte(states, root)

    brut = {
        "prose": prose,
        "cloture_muette": stale,
        "forme": muettes,
        "cahier_absents": absents,
        "cahier_restees": restees,
        "cahier_ailleurs": ailleurs,
        "desaccord_etat": det,
        "desaccord_dates": dat,
        "hors_nomenclature": etats_hors_nomenclature(states),
        "non_declares": muets,
        "reliquats_enterres": enterres,
        "majeure_incoherente": incoherentes,
        "sans_etiquette": feuilles_sans_etiquette(states),
    }
    out = {cle: {"n": len(brut[cle]), "zero_attendu": zero,
                 "libelle": lib, "items": brut[cle]}
           for cle, lib, zero in SECTIONS_AUDIT}
    # Contexte non compte : ni anomalie, ni action attendue.
    out["_contexte"] = {"redecoupe": redecoupe, "empruntes": empruntes,
                        "majeure_assumee": assumees,
                        "inconnus": inconnus,
                        "sous_muettes_closes": sous_closes,
                        "sous_muettes_indecidables": sous_indecidables,
                        "n_pistes": len(states), "n_majeures": len(majeures)}
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("path", nargs="?", default=".")
    ap.add_argument("--open", action="store_true", help="ne rendre que [à faire]/[en cours]")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--audit", action="store_true",
                    help="lister les mentions en prose qui contredisent l'état courant")
    ap.add_argument("--audit-json", action="store_true",
                    help="les mêmes contrôles, en JSON sur stdout (compteurs pour un hook)")
    args = ap.parse_args()

    root = project_root(args.path)
    if not root:
        print("Aucun projet structuré trouvé (pas de cahier_de_labo.md en remontant).",
              file=sys.stderr)
        return 1

    amorcer(root)

    lu = lire_registre(root, avec_audit=args.audit or args.audit_json)
    states = lu[0]

    if args.audit_json:
        col = collecte_audit(root, lu)
        print(json.dumps({"racine": root, "sections": col}, ensure_ascii=False,
                         indent=2, default=list))
        return 0

    audit, stale = lu[3], lu[4]
    rows = sorted(states.items(), key=lambda kv: sort_key(kv[0]))
    if args.open:
        rows = [r for r in rows
                if r[1][0].endswith("à faire") or r[1][0].endswith("en cours")
                or r[1][0] == "état non déclaré"]

    if args.json:
        print(json.dumps({k: {"etat": v[0], "source": v[1], "libelle": v[2],
                              "etiquette": ETIQUETTES.get(k)}
                          for k, v in rows}, ensure_ascii=False, indent=2))
    else:
        for pid, (etat, src, lib) in rows:
            print(f"{pid}\t{etat}\t{src}\t{lib}\t{ETIQUETTES.get(pid, '')}")

    if args.audit:
        col = collecte_audit(root, lu)
        stale = col["cloture_muette"]["items"]
        muettes = col["forme"]["items"]
        absents = col["cahier_absents"]["items"]
        ailleurs = col["cahier_ailleurs"]["items"]
        restees = col["cahier_restees"]["items"]
        det, dat = col["desaccord_etat"]["items"], col["desaccord_dates"]["items"]
        hors, muets = col["hors_nomenclature"]["items"], col["non_declares"]["items"]
        redecoupe = col["_contexte"]["redecoupe"]
        empruntes, inconnus = col["_contexte"]["empruntes"], col["_contexte"]["inconnus"]

        print(f"\n# AUDIT — {len(audit)} mention(s) en prose contredisant l'état courant",
              file=sys.stderr)
        for pid, dit, vrai, src in audit:
            print(f"#   {pid} : la prose dit [{dit}], l'état courant est [{vrai}]  ({src})",
                  file=sys.stderr)
        print(f"\n# AUDIT — {len(stale)} clôture(s) POSSIBLEMENT non répercutée(s) sur la "
              f"ligne de définition (heuristique, à vérifier à la main : le corps d'une piste "
              f"« porte » narre légitimement l'état d'autres pistes)", file=sys.stderr)
        for pid, tete, corps, src in stale:
            print(f"#   {pid} : définition [{tete}] mais le corps annonce [{corps}]  ({src})",
                  file=sys.stderr)

        print(f"\n# AUDIT — {len(muettes)} piste(s) ABSENTE(S) du registre : identifiant en "
              f"tête de ligne avec un marqueur d'état, mais forme non conforme (ni titre "
              f"`## Px.`, ni item de liste), donc jamais parsée. Corriger la FORME de la "
              f"ligne, pas l'état.", file=sys.stderr)
        for pid, etat, src in muettes:
            print(f"#   {pid} : [{etat}] écrit hors forme de définition  ({src})",
                  file=sys.stderr)

        print(f"\n# AUDIT — {len(absents)} sous-piste(s) NOMMÉE(S) AU CAHIER et INTROUVABLE(S) "
              f"dans tout le registre. Le cahier est append-only : il fait foi sur ce qui a "
              f"existé. Deux lectures, à trancher à la main : le registre a perdu la sous-piste "
              f"(cas P40/P42, 2026-08-30 — reconstituer le corps depuis le cahier), ou elle n'y "
              f"a jamais été inscrite (une session l'a numérotée dans son récit sans la porter "
              f"à l'arbre — l'y inscrire, ou renoncer sciemment).", file=sys.stderr)
        for pid, n, (fn, ln), dest in absents:
            print(f"#   {pid} : {n} mention(s) au cahier (dernière {fn}:{ln}), absente de {dest}",
                  file=sys.stderr)
        # Le tri de `ailleurs` (redécoupage légitime / resté à ranger / emprunté au
        # dépôt parent) est fait par `collecte_audit` : les lister une à une noierait
        # les deux ou trois cas qui demandent, eux, une action.
        print(f"\n# AUDIT — {len(ailleurs)} sous-piste(s) définie(s) AILLEURS que dans le "
              f"fichier de leur racine. Aucune n'est perdue ; seules les {len(restees)} du "
              f"deuxième bloc appellent un geste.", file=sys.stderr)
        if redecoupe:
            print(f"# · rangées sous une autre piste majeure sans renumérotation "
                  f"(redécoupage `/recadrage`) — rien à faire :", file=sys.stderr)
            for rac, src, pids in redecoupe:
                print(f"#   {rac}.* : {len(pids)} sous-piste(s) dans {src} "
                      f"({', '.join(pids[:4])}"
                      f"{', …' if len(pids) > 4 else ''})", file=sys.stderr)
        if restees:
            print(f"# · restées dans l'archive figée ou l'index, que la migration "
                  f"index+détail devait vider — rapatrier le corps dans `pistes/Px.md` :",
                  file=sys.stderr)
            for pid, n, src, dest in restees:
                print(f"#   {pid} : {n} mention(s) au cahier, corps dans {src}, absent de {dest}",
                      file=sys.stderr)
        if empruntes:
            print(f"# · {len(empruntes)} identifiant(s) du registre du dépôt PARENT, "
                  f"numérotation indépendante — collision, pas anomalie : "
                  f"{', '.join(sorted(empruntes, key=sort_key))}", file=sys.stderr)
        if inconnus:
            print(f"# ({len(inconnus)} identifiant(s) dont la piste majeure est étrangère au "
                  f"registre — renvoi à un autre projet, informationnel : "
                  f"{', '.join(p for p, _, _ in inconnus[:12])}"
                  f"{' …' if len(inconnus) > 12 else ''})", file=sys.stderr)

        print(f"\n# AUDIT — {len(det)} piste(s) majeure(s) dont l'INDEX et le DÉTAIL sont en "
              f"désaccord d'état, et {len(dat)} dont les dates de `maj :` divergent. Le détail "
              f"fait foi sur le contenu, l'index sur la vue d'ensemble : dire laquelle est en "
              f"retard, ne pas trancher mécaniquement.", file=sys.stderr)
        for pid, ei, ed in det:
            print(f"#   {pid} : index [{ei}] / détail [{ed}]", file=sys.stderr)
        for pid, mi, md, retard in dat:
            print(f"#   {pid} : maj index {mi} / détail {md} — {retard} en retard",
                  file=sys.stderr)

        print(f"\n# AUDIT — {len(hors)} état(s) HORS NOMENCLATURE (imposée : "
              f"{', '.join(ETATS)}) : ni ouvert ni clos aux yeux de `--open`, donc absent "
              f"des deux listes. Trancher vers un des quatre états.", file=sys.stderr)
        for pid, etat, src in hors:
            print(f"#   {pid} : [{etat}]  ({src})", file=sys.stderr)

        clos = [m for m in muets if m[3]]
        print(f"\n# AUDIT — {len(muets)} piste(s) MAJEURE(S) sans aucun des quatre états dans "
              f"leur étiquette d'en-tête, dont {len(clos)} qui annonce(nt) une clôture en toutes "
              f"lettres. `--open` les rend TOUTES par prudence : chacune gonfle donc la liste "
              f"des pistes ouvertes, et une étiquette libre périmée des DEUX côtés échappe aussi "
              f"au contrôle index/détail. Poser un des quatre états ; le qualificatif descriptif "
              f"peut rester à côté.", file=sys.stderr)
        for pid, src, lib, cloture in muets:
            marque = "clôture annoncée" if cloture else "indécidable"
            print(f"#   {pid} : {marque} — {lib[:70]}  ({src})", file=sys.stderr)

        enterres = col["reliquats_enterres"]["items"]
        ctx = col["_contexte"]
        n_cl, n_ind = len(ctx["sous_muettes_closes"]), len(ctx["sous_muettes_indecidables"])
        print(f"\n# AUDIT — {len(enterres)} SOUS-piste(s) sans état déclaré sous une piste "
              f"majeure CLOSE dont l'étiquette annonce une RÉSERVE OUVERTE : du travail vivant "
              f"enterré sous un parent clos, que ni `--open` (qui les noie dans les muettes) ni "
              f"le contrôle des majeures ne montrent. Les rouvrir explicitement, ou constater "
              f"que la réserve est levée. ({n_cl} autre(s) annoncent une clôture, {n_ind} sont "
              f"indécidables : celles-là ne demandent rien d'urgent — et certaines ne sont même "
              f"pas des directions de travail, mais des leçons ou des constats numérotés, "
              f"auxquels réclamer un des quatre états est une erreur de catégorie.)",
              file=sys.stderr)
        for pid, src, lib in enterres:
            print(f"#   {pid} : {lib[:70]}  ({src})", file=sys.stderr)

        inc = col["majeure_incoherente"]["items"]
        ass = col["_contexte"].get("majeure_assumee", [])
        if ass:
            print(f"\n# CONTEXTE — {len(ass)} sous-piste(s) ouverte(s) sous une majeure close "
                  f"dont l'en-tête porte une note `**Assumé**` la NOMMANT : déclaration "
                  f"explicite, donc pas un défaut et non comptée. Reconnu depuis le "
                  f"2026-09-09 : sans cela, consigner la justification — ce que le hook "
                  f"`Stop` demande — ne décrémentait aucun compteur et l'alerte était "
                  f"ineffaçable.", file=sys.stderr)
            for pid, e, rac_pid, er, src, lib in ass:
                print(f"#   {pid} [{e}] sous {rac_pid} [{er}], assumé — {lib[:44]}  ({src})",
                      file=sys.stderr)
        print(f"\n# AUDIT — {len(inc)} sous-piste(s) DÉCLARÉE(S) ouverte(s) sous une piste "
              f"majeure CLOSE. Règle arbitrée le 2026-09-08 : une majeure ne peut pas rester "
              f"close tant qu'une sous-piste est ouverte — elle repasse `en cours` avec un "
              f"qualificatif nommant la réserve. C'est le sens d'erreur le plus coûteux, un "
              f"en-tête trop optimiste faisant croire qu'un travail est fini (cas fondateur "
              f"P67 : faux feu vert de déploiement en production). LIRE avant de rouvrir : la "
              f"sous-piste peut aussi porter une étiquette périmée. Une clôture "
              f"DÉLIBÉRÉE se déclare par une note `**Assumé**` nommant la sous-piste, "
              f"dans l'en-tête de la majeure.", file=sys.stderr)
        for pid, e, rac_pid, er, src, lib in inc:
            print(f"#   {pid} [{e}] sous {rac_pid} [{er}] — {lib[:52]}  ({src})", file=sys.stderr)

        sans = col["sans_etiquette"]["items"]
        if sans:
            print(f"\n# AUDIT — {len(sans)} feuille(s) ouverte(s) sans étiquette modèle/effort "
                  f"`[Modèle:effort]` (convention 2026-09-13, cf. "
                  f"~/.agents/knowledge/model-routing.md). Sans elle, la piste se lance sur le "
                  f"modèle de la session en cours, souvent le plus cher, et sa consommation "
                  f"n'est pas comparable à sa prévision. Ce contrôle est TOLÉRANT : "
                  f"l'étiquetage se pose à la réouverture d'un projet, jamais en masse. "
                  f"Propositions : "
                  f"`python3 ${CLAUDE_PLUGIN_ROOT}/skills/routage/scripts/routage.py etiqueter <projet>`.",
                  file=sys.stderr)
            apercu = ", ".join(sans[:8])
            print(f"#   {apercu}" + (f", … (+{len(sans) - 8})" if len(sans) > 8 else ""),
                  file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
