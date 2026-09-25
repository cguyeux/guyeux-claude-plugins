#!/usr/bin/env python3
"""
Objet: remplacer la LECTURE d'un nichage par un TEST. Lire à l'oeil qu'une protéine bactérienne
    tombe « dans » les eucaryotes ne dit pas si l'arbre alternatif — les bactéries monophylétiques,
    donc pas de transfert — est significativement moins bon. Ce script écrit les contraintes
    topologiques des hypothèses concurrentes, la recette IQ-TREE qui les compare par le test
    d'approximately unbiased (AU), puis lit le tableau produit et rend le verdict.
Entrées: `constraints` : --taxonomy (TSV étiquette<TAB>domaine, domaine dans BACTERIA/EUKARYOTA/
    ARCHAEA/VIRUS/AUTRE), --query (étiquette de la séquence testée), --alignment, --out ;
    `read` : --iqtree (fichier .iqtree du run `-z`), --order (écrit par `constraints`).
Sorties: les contraintes Newick (global) ou les arbres fixés `trees_local.nwk` (local),
    `commandes.sh`, `trees_order.txt` ; puis un rapport et une dernière ligne
    `VERDICT_TOPOLOGIE: TRANSFERT_SOUTENU|VERTICAL_SOUTENU|INDECIDABLE|NON_VALIDE`.
Réutilisable: oui, c'est l'étape 3 du skill hgt-interdomain-check.
Projet: écrit pour environnement/pistes.md AG2 (manque (3) du constat du 2026-09-22).
Date: 2026-09-22.

Ce que le test ajoute au nichage. Le nichage est une propriété de l'arbre ML retenu ; il ne dit
rien de la marge. Le test AU demande : l'arbre où les bactéries restent monophylétiques est-il
REJETÉ par les données ? S'il ne l'est pas, le nichage observé est compatible avec l'absence de
transfert, et il n'y a pas de résultat — c'est la situation la plus fréquente sur des familles
anciennes et courtes, et c'est exactement la conclusion à laquelle Alvarez-Venegas et al. (2007)
sont parvenus pour les gènes à domaine SET des bactéries.

Piège d'outillage. Le bloc « USER TREES » du .iqtree marque d'un `+`/`-` les tests significatifs
et les colonnes changent selon les options (`-zb`, `-au`, `-zw`). On repère donc p-AU par son
INDICE DE COLONNE lu dans l'en-tête, jamais par sa position supposée.

Mode `constraints --local` (AG3, 2026-09-24, refait le 2026-09-25). Les contraintes GLOBALES
(H1/H2) imposent la monophylie de tout un domaine : sur une famille à histoire réticulée, les deux
arbres contraints sont pénalisés pour une raison étrangère à la requête, et le test est muet
(mesuré sur PF00856 : ni bactéries, ni eucaryotes, ni archées, ni même Spirochaetota
monophylétiques ; les deux hypothèses rejetées). Le mode local ne teste que le PLACEMENT :
  - ensembles de référence lus sur l'arbre inféré SANS la requête (jamais sur celui qui la
    contient, ce serait circulaire) : côté vertical, chaque clade maximal pur du groupe fin de
    la requête ; côté transfert, chaque clade maximal pur du domaine donneur. Tous sont testés,
    aucun n'est élu : le clade « le plus proche » change selon la métrique (topologique ou
    patristique) et ne survit pas toujours à l'ajout de la requête ;
  - unité déplacée = le CLADE FOCAL F : le clade vertical V_k qui contient le plus proche
    congénère de la requête dans l'arbre ML, plus la requête greffée là où l'arbre ML la place
    parmi ses membres. Déplacer la requête seule loin d'un congénère à 98,5 % d'identité serait
    rejeté partout, trivialement, sans rien dire d'un transfert vers l'ancêtre du genre ;
  - arbres FIXÉS sur un squelette commun (l'arbre de référence privé de V_k) : F à sa place
    (HV1), ou sur la tige de chaque autre ensemble. Aucune recherche, IQ-TREE ne réoptimise que
    les longueurs de branches. Le premier correctif (contrainte partielle {requête} ∪ C | autres
    ensembles, reste libre) était FAUX : ce partage se satisfait aussi en déplaçant C contre la
    requête, et l'optimiseur prend le moins coûteux (PF00856 : dans les quatre arbres
    contraints, la requête est restée à 0,019 de son congénère, chaque clade eucaryote a été
    logé dans Leptospira, et le seul non rejeté portait la tige la plus longue du panel). Un
    `trees_order.txt` sans marqueur `#mode` vient de cet ancien mode et se lit NON_VALIDE ;
  - l'arbre ML libre N'EST PAS dans le jeu testé : il diffère du squelette ailleurs, et tous les
    arbres fixés seraient pénalisés pour cette raison étrangère au placement ;
  - deux hypothèses de même topologie (un clade donneur déjà frère de V_k) sont reprises par
    ALIAS — deux arbres identiques se partageraient les victoires RELL et fausseraient leurs
    p-AU — et `read` les dit indiscernables ;
  - contrôle « qui a bougé », à la génération puis dans `read` sur les arbres réellement évalués :
    F est un clade de chaque arbre, frère de l'ensemble visé, et F ôté, tous les arbres sont
    identiques. Échec = `NON_VALIDE`.
"""

import argparse
import copy
import re
import sys
from pathlib import Path

DOMAINES = ("BACTERIA", "EUKARYOTA", "ARCHAEA", "VIRUS", "AUTRE")
FAMILLES = ("ML", "V", "T")
# Marqueur de trees_order.txt : arbres fixés sur squelette commun (AG3, 2026-09-25). Son absence
# désigne l'ancien mode local à contrainte partielle, dont la lecture reste NON_VALIDE.
MODE_FIXE = "squelette_fixe"


def lit_taxonomie(chemin):
    tax = {}
    for brut in Path(chemin).read_text(encoding="utf-8").splitlines():
        if not brut.strip() or brut.startswith("#"):
            continue
        champs = brut.split("\t") if "\t" in brut else brut.split(",")
        if len(champs) < 2:
            continue
        etiquette, domaine = champs[0].strip(), champs[1].strip().upper()
        if domaine not in DOMAINES:
            raise SystemExit(f"domaine inconnu « {domaine} » pour {etiquette} ; attendus : "
                             + ", ".join(DOMAINES))
        tax[etiquette] = domaine
    if not tax:
        raise SystemExit(f"aucune ligne exploitable dans {chemin}")
    return tax


def lit_groupes_fins(chemin):
    groupes = {}
    for brut in Path(chemin).read_text(encoding="utf-8").splitlines():
        if not brut.strip() or brut.startswith("#"):
            continue
        champs = brut.split("\t") if "\t" in brut else brut.split(",")
        if len(champs) >= 3 and champs[2].strip():
            groupes[champs[0].strip()] = champs[2].strip()
    return groupes


def etiquettes_alignement(chemin):
    return [l[1:].split()[0] for l in Path(chemin).read_text(encoding="utf-8").splitlines()
            if l.startswith(">")]


# --- mode local : ensembles de référence et contraintes de placement -----------------------------

def lit_arbre(chemin):
    from Bio import Phylo  # import tardif : le mode global n'exige pas Biopython
    # Les parcours de clades sont récursifs ; 246 feuilles dépassaient déjà la limite par défaut
    # sous Python 3.14 / Biopython 1.87 (constaté en AG2 sur le skill frère).
    sys.setrecursionlimit(max(sys.getrecursionlimit(), 10000))
    return Phylo.read(str(chemin), "newick")


def cotes_aretes(arbre):
    """Les deux côtés de chaque arête interne, en ensembles d'étiquettes (arbre non raciné)."""
    feuilles = frozenset(t.name for t in arbre.get_terminals())
    cotes = set()
    for c in arbre.find_clades():
        if c is arbre.root:
            continue
        s = frozenset(t.name for t in c.get_terminals())
        if 1 < len(s) < len(feuilles) - 1:
            cotes.add(s)
            cotes.add(feuilles - s)
    return feuilles, cotes


def clades_purs_maximaux(cotes, predicat, taille_min):
    purs = sorted({s for s in cotes if all(predicat(x) for x in s)}, key=len, reverse=True)
    maximaux = []
    for s in purs:
        if not any(s < m for m in maximaux):
            maximaux.append(s)
    return [m for m in maximaux if len(m) >= taille_min]


def feuilles_de(clade):
    return frozenset(t.name for t in clade.get_terminals())


def parent_de(arbre, noeud):
    chemin = arbre.get_path(noeud)
    return chemin[-2] if len(chemin) > 1 else arbre.root


def clade_exact(arbre, ensemble, quoi):
    """Enracine `arbre` hors de `ensemble` et rend le nœud qui porte exactement ces feuilles."""
    ensemble = frozenset(ensemble)
    arbre.root_with_outgroup(next(t for t in arbre.get_terminals() if t.name not in ensemble))
    cibles = [t for t in arbre.get_terminals() if t.name in ensemble]
    noeud = cibles[0] if len(cibles) == 1 else arbre.common_ancestor(cibles)
    if feuilles_de(noeud) != ensemble:
        raise SystemExit(f"{quoi} : ces {len(ensemble)} séquences ne forment pas un clade de "
                         f"l'arbre attendu — ont-elles été lues sur un autre arbre ?")
    return noeud


def retire(arbre, noeud):
    """Ôte `noeud` et son sous-arbre, puis résorbe le nœud devenu unaire."""
    parent = parent_de(arbre, noeud)
    parent.clades.remove(noeud)
    if len(parent.clades) != 1:
        return
    seul = parent.clades[0]
    if parent is arbre.root:
        arbre.root = seul
    else:
        grand = parent_de(arbre, parent)
        seul.branch_length = (seul.branch_length or 0) + (parent.branch_length or 0)
        grand.clades[grand.clades.index(parent)] = seul


def greffe_sur_tige(arbre, ensemble, greffon, quoi):
    """Greffe `greffon` en frère du côté `ensemble`, au milieu de sa tige."""
    from Bio.Phylo.BaseTree import Clade
    noeud = clade_exact(arbre, ensemble, quoi)
    parent = parent_de(arbre, noeud)
    lg = noeud.branch_length or 0.0
    noeud.branch_length = lg / 2
    parent.clades[parent.clades.index(noeud)] = Clade(branch_length=lg / 2,
                                                      clades=[noeud, greffon])


def clade_focal(ref, ml, requete, vk):
    """Sous-arbre F : le clade vertical V_k tel que l'arbre de référence le donne, la requête
    greffée là où l'arbre ML la place parmi ses membres.

    La topologie interne de F est la MÊME dans tous les arbres testés : seul son point
    d'attache varie. On lit dans l'arbre ML le plus petit clade qui contient la requête et au
    moins un membre de V_k ; si ces membres forment un clade de V_k, la requête se greffe sur sa
    tige, sinon sur la branche terminale de son plus proche voisin patristique."""
    from Bio.Phylo.BaseTree import Clade, Tree
    f = copy.deepcopy(clade_exact(copy.deepcopy(ref), vk, "clade focal"))
    tige = f.branch_length if f.branch_length else 0.1
    ml2 = copy.deepcopy(ml)
    ml2.root_with_outgroup(next(t for t in ml2.get_terminals()
                                if t.name not in vk and t.name != requete))
    q = next(t for t in ml2.get_terminals() if t.name == requete)
    lg_q = q.branch_length if q.branch_length else 0.01
    soeurs = frozenset()
    for anc in list(reversed(ml2.get_path(q)[:-1])) + [ml2.root]:
        soeurs = feuilles_de(anc) & vk
        if soeurs:
            break
    feuille_q = Clade(name=requete, branch_length=lg_q)
    if soeurs == vk:
        f.branch_length = tige / 2
        return Clade(branch_length=tige / 2, clades=[f, feuille_q]), \
            f"sœur de tout le clade (comme dans l'arbre ML)"
    sous = Tree(root=f, rooted=True)
    cibles = [t for t in sous.get_terminals() if t.name in soeurs]
    noeud = cibles[0] if len(cibles) == 1 else sous.common_ancestor(cibles)
    if feuilles_de(noeud) == soeurs:
        mode = f"sœur de {len(soeurs)} congénère(s), comme dans l'arbre ML"
    else:
        voisin = min(soeurs, key=lambda x: ml.distance(requete, x))
        noeud = next(t for t in sous.get_terminals() if t.name == voisin)
        mode = (f"sœur de {voisin}, son plus proche voisin patristique (ses sœurs dans l'arbre "
                f"ML ne forment pas un clade du clade de référence)")
        soeurs = frozenset({voisin})
    parent = parent_de(sous, noeud)
    lg = noeud.branch_length or 0.0
    noeud.branch_length = lg / 2
    parent.clades[parent.clades.index(noeud)] = Clade(branch_length=lg / 2,
                                                      clades=[noeud, feuille_q])
    f.branch_length = tige
    return f, mode


def support_cote(arbre, cote):
    for c in arbre.find_clades():
        if c is arbre.root:
            continue
        s = frozenset(t.name for t in c.get_terminals())
        if s == cote or len(s) + len(cote) == len(arbre.get_terminals()) and not (s & cote):
            return c.name or ("" if c.confidence is None else str(c.confidence))
    return ""


def deracine(arbre):
    """Réduit une racine bifurquante en trifurcation : un arbre non raciné pour IQ-TREE."""
    racine = arbre.root
    if len(racine.clades) == 2:
        interne = next((c for c in racine.clades if c.clades), None)
        if interne is not None:
            autre = racine.clades[0] if racine.clades[1] is interne else racine.clades[1]
            autre.branch_length = (autre.branch_length or 0) + (interne.branch_length or 0)
            racine.clades = [autre] + interne.clades


def arbres_places(ref, ml, requete, ens):
    """Construit un arbre fixé par hypothèse ; rend (F, mode de greffe, V_k, [(…, arbre)]).

    Squelette = arbre de référence privé du clade focal V_k ; F = V_k + requête. V_k lui-même
    reçoit F à sa place d'origine ; chaque autre ensemble reçoit F sur sa tige. Seul le point
    d'attache de F diffère d'un arbre à l'autre."""
    verticaux = [c for _n, fam, c, _s in ens if fam == "V"]
    voisin = min(frozenset().union(*verticaux), key=lambda x: ml.distance(requete, x))
    vk = next(c for c in verticaux if voisin in c)
    greffon, mode = clade_focal(ref, ml, requete, vk)
    focal = feuilles_de(greffon)
    squelette = copy.deepcopy(ref)
    retire(squelette, clade_exact(squelette, vk, "clade focal"))
    res = []
    for nom, fam, clade, sup in ens:
        if clade == vk:
            arbre = copy.deepcopy(ref)
            noeud = clade_exact(arbre, vk, "clade focal")
            parent = parent_de(arbre, noeud)
            parent.clades[parent.clades.index(noeud)] = copy.deepcopy(greffon)
        else:
            arbre = copy.deepcopy(squelette)
            greffe_sur_tige(arbre, clade, copy.deepcopy(greffon), nom)
        for c in arbre.get_nonterminals():
            c.name, c.confidence = None, None
        deracine(arbre)
        res.append((nom, fam, clade, sup, clade == vk, arbre))
    return focal, mode, vk, res


def controle_placements(arbres, focal, attaches):
    """« Qui a bougé » : rend la liste des écarts à la règle « seul F change de place ».

    `arbres` : [(nom, arbre)] ; `attaches` : {nom: côté auquel F doit être frère, ou None pour
    l'hypothèse « en place »}. Chaque arbre doit porter F en clade et F ∪ attache en clade ; une
    fois F ôté, tous les arbres doivent être IDENTIQUES (même squelette)."""
    ecarts, squelettes = [], {}
    for nom, arbre in arbres:
        _f, cotes = cotes_aretes(arbre)
        if focal not in cotes:
            ecarts.append(f"{nom} : le clade focal ({len(focal)} séq.) n'y est pas un clade")
        att = attaches.get(nom)
        if att and (focal | att) not in cotes:
            ecarts.append(f"{nom} : le clade focal n'y est pas frère de l'ensemble visé "
                          f"({len(att)} séq.)")
        elague = copy.deepcopy(arbre)
        for x in focal:
            elague.prune(x)
        squelettes[nom] = cotes_aretes(elague)[1]
    if squelettes:
        noms = list(squelettes)
        for n in noms[1:]:
            if squelettes[n] != squelettes[noms[0]]:
                d = len(squelettes[n] ^ squelettes[noms[0]]) // 2
                ecarts.append(f"{n} : une fois le clade focal ôté, {d} bipartition(s) diffèrent "
                              f"de {noms[0]} — autre chose que F a bougé")
    return ecarts


def ensembles_reference(arbre_reference, tax, groupes, requete, domaine_donneur, taille_min,
                        clade_donneur=None):
    """Rend [(nom, famille, ensemble, support)], famille V (vertical) ou T (transfert)."""
    _feuilles, cotes = cotes_aretes(arbre_reference)
    groupe_q = groupes.get(requete)
    if not groupe_q:
        raise SystemExit(f"--local exige le groupe fin de la requête (3e colonne de --taxonomy) : "
                         f"absent pour {requete}. C'est lui qui définit la lignée « verticale ».")
    dom_q = tax[requete]
    verticaux = clades_purs_maximaux(
        cotes, lambda x: tax.get(x) == dom_q and groupes.get(x) == groupe_q, taille_min)
    if not verticaux:
        raise SystemExit(
            f"aucun clade d'au moins {taille_min} séquences du groupe fin « {groupe_q} » dans "
            f"l'arbre de référence : l'hypothèse verticale n'a pas d'ensemble auquel se rattacher "
            f"à ce rang. Élargir le groupe fin (3e colonne de --taxonomy) plutôt que de l'inventer.")
    if clade_donneur:
        donneurs = frozenset(clade_donneur)
        if donneurs not in cotes:
            raise SystemExit(
                "--donor-clade ne forme pas un clade de l'arbre de référence : le partage "
                "{requête} ∪ donneur | reste y serait déjà faux sans la requête, et son rejet "
                "ne dirait rien d'elle. Désigner un clade réel de cet arbre.")
        transferts = [donneurs]
    else:
        transferts = clades_purs_maximaux(cotes, lambda x: tax.get(x) == domaine_donneur,
                                          taille_min)
    if not transferts:
        raise SystemExit(f"aucun clade d'au moins {taille_min} séquences {domaine_donneur} dans "
                         f"l'arbre de référence : l'hypothèse de transfert est sans objet.")
    res = []
    for i, c in enumerate(sorted(verticaux, key=len, reverse=True), 1):
        res.append((f"HV{i}_requete_avec_{groupe_q}_{len(c)}", "V", c,
                    support_cote(arbre_reference, c)))
    for i, c in enumerate(sorted(transferts, key=len, reverse=True), 1):
        res.append((f"HT{i}_requete_dans_{domaine_donneur.lower()}_{len(c)}", "T", c,
                    support_cote(arbre_reference, c)))
    return res


def ecrit_contraintes_locales(a, tax, feuilles):
    groupes = lit_groupes_fins(a.taxonomy)
    ref = lit_arbre(a.reference_tree)
    feuilles_ref = {t.name for t in ref.get_terminals()}
    attendues = set(feuilles) - {a.query}
    if feuilles_ref != attendues:
        manque, trop = sorted(attendues - feuilles_ref), sorted(feuilles_ref - attendues)
        raise SystemExit("--reference-tree doit porter exactement les séquences de l'alignement "
                         f"SANS la requête. Absentes : {manque[:6]} ; en trop : {trop[:6]}")
    dom_q = tax[a.query]
    donneur = a.donor_domain or ("EUKARYOTA" if dom_q == "BACTERIA" else "BACTERIA")
    clade_donneur = ([d.strip() for d in a.donor_clade.split(",") if d.strip()]
                     if a.donor_clade else None)
    ens = ensembles_reference(ref, tax, groupes, a.query, donneur, a.min_clade, clade_donneur)

    ml = lit_arbre(a.ml_tree)
    if {t.name for t in ml.get_terminals()} != set(feuilles):
        raise SystemExit("--ml-tree ne porte pas exactement les séquences de l'alignement")
    focal, mode, vk, places = arbres_places(ref, ml, a.query, ens)

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    groupe_q = groupes.get(a.query)
    ordre = [f"#mode\t{MODE_FIXE}"]
    tsv = ["nom\tfamille\ttaille\tsupport_ref\tgroupes\tidentique_a\tmembres"]
    distincts, arbres_ok, attaches, n_v, n_t = [], [], {}, 0, 0
    for _ancien, fam, clade, sup, en_place, arbre in places:
        if fam == "V":
            n_v += 1
            nom = (f"HV{n_v}_focal_en_place_{groupe_q}_{len(clade)}" if en_place
                   else f"HV{n_v}_focal_sur_{groupe_q}_{len(clade)}")
        else:
            n_t += 1
            nom = f"HT{n_t}_focal_sur_{donneur.lower()}_{len(clade)}"
        compo = {}
        for x in clade:
            compo[groupes.get(x, "?")] = compo.get(groupes.get(x, "?"), 0) + 1
        compo_txt = ", ".join(f"{g} {n}" for g, n in sorted(compo.items(), key=lambda kv: -kv[1]))
        if en_place:
            libelle = (f"clade focal à sa place : requête + {len(clade)} congénères ({compo_txt})")
        else:
            libelle = (f"clade focal frère de ce clade "
                       + ("de sa propre lignée" if fam == "V" else donneur)
                       + f" ({len(clade)} séq. : {compo_txt})")
        cotes = cotes_aretes(arbre)[1]
        double = next((n for n, c in distincts if c == cotes), None)
        if double:
            ordre.append(f"{nom}\t{fam}\t{libelle}\t={double}")
        else:
            distincts.append((nom, cotes))
            arbres_ok.append((nom, arbre))
            from Bio import Phylo
            Phylo.write(arbre, str(out / f"{nom}.nwk"), "newick")
            ordre.append(f"{nom}\t{fam}\t{libelle}\tarbre")
        attaches[nom] = None if en_place else frozenset(clade)
        tsv.append(f"{nom}\t{fam}\t{len(clade)}\t{sup}\t{compo_txt}\t{double or ''}\t"
                   + ",".join(sorted(clade)))

    ecarts = controle_placements(arbres_ok, focal, attaches)
    if ecarts:
        raise SystemExit("construction incohérente, rien n'est à lancer :\n  " + "\n  ".join(ecarts))
    (out / "trees_local.nwk").write_text(
        "".join((out / f"{n}.nwk").read_text(encoding="utf-8") for n, _a in arbres_ok),
        encoding="utf-8")
    (out / "trees_order.txt").write_text("\n".join(ordre) + "\n", encoding="utf-8")
    (out / "ensembles_reference.tsv").write_text("\n".join(tsv) + "\n", encoding="utf-8")
    (out / "clade_focal.tsv").write_text(
        f"requete\t{a.query}\nclade_vertical\t{','.join(sorted(vk))}\n"
        f"greffe_requete\t{mode}\nmembres\t{','.join(sorted(focal))}\n", encoding="utf-8")
    script = ["#!/bin/bash",
              "# Test AU LOCAL sur squelette fixé — à lancer sur mp ou mh (quelques minutes).",
              "# Arbres FIXÉS écrits par `constraints --local` : aucune recherche, IQ-TREE",
              "# réoptimise seulement les longueurs de branches de chacun. Paramètres du modèle",
              "# estimés sur l'arbre ML libre fixé (--tree-fix) : sur le cas SET, même verdict",
              "# qu'avec l'arbre de parcimonie initial (ΔlogL à 0,3 près) et 8 fois plus rapide.",
              f"# Prérequis dans ce répertoire : {Path(a.ml_tree).name} (arbre ML libre).",
              "set -euo pipefail",
              f'IQ="${{IQ:-{a.iqtree_bin}}}"',
              f'ALN="${{ALN:-{Path(a.alignment).name}}}"',
              'cd "$(dirname "$0")"', "",
              f"$IQ -s $ALN -m {a.model} -t {Path(a.ml_tree).name} --tree-fix -z trees_local.nwk "
              f"-zb 10000 -au -pre au_local -T {a.remote_threads}", "",
              "# lecture, en local (contrôle « qui a bougé » compris) :",
              "#    python3 topology_test.py read --iqtree au_local.iqtree --order trees_order.txt"]
    (out / "commandes.sh").write_text("\n".join(script) + "\n", encoding="utf-8")

    print(f"mode local, squelette fixé : requête {a.query} ({dom_q}/{groupe_q}), donneur {donneur}")
    print(f"  clade focal : requête + {len(vk)} congénères, requête {mode}")
    print(f"  squelette : arbre de référence ({len(feuilles_ref)} feuilles) privé du clade focal")
    for l in tsv[1:]:
        c = l.split("\t")
        print(f"  {c[1]}  {c[0]:<44} {c[2]:>3} séq.  support {c[3] or '?'}"
              + (f"  (= {c[5]})" if c[5] else ""))
    print(f"{len(arbres_ok)} arbre(s) distinct(s) à évaluer, {len(places) - len(arbres_ok)} "
          f"alias ; contrôle « qui a bougé » passé ; recette dans {out}/commandes.sh")


def groupe(noms):
    return "(" + ",".join(noms) + ")"


def ecrit_contraintes(a):
    tax = lit_taxonomie(a.taxonomy)
    feuilles = etiquettes_alignement(a.alignment)
    manquantes = [f for f in feuilles if f not in tax]
    if manquantes:
        raise SystemExit(f"{len(manquantes)} séquence(s) de l'alignement sans domaine dans "
                         f"--taxonomy : " + ", ".join(manquantes[:8])
                         + "\nLe rattachement doit être INSTRUIT, jamais deviné : une séquence "
                           "non rattachée déplacerait silencieusement une contrainte.")
    if a.query not in tax:
        raise SystemExit(f"--query {a.query} absent de --taxonomy")
    if tax[a.query] != "BACTERIA":
        print(f"[note] la requête {a.query} est déclarée {tax[a.query]} et non BACTERIA : les "
              f"hypothèses gardent leur forme mais relisez leur libellé.", file=sys.stderr)
    if a.local:
        if not a.reference_tree or not a.ml_tree:
            raise SystemExit(
                "--local exige --reference-tree (arbre ML inféré SANS la requête : c'est sur lui "
                "que se lisent les ensembles, sans circularité) et --ml-tree (arbre ML libre : "
                "sans lui, l'hypothèse qu'il satisfait déjà serait inférée à nouveau et figurerait "
                "en double dans le test AU, où deux arbres identiques faussent leurs p-AU).")
        return ecrit_contraintes_locales(a, tax, feuilles)

    bact = [f for f in feuilles if tax[f] == "BACTERIA" and f != a.query]
    euc = [f for f in feuilles if tax[f] == "EUKARYOTA" and f != a.query]
    autres = [f for f in feuilles if tax[f] not in ("BACTERIA", "EUKARYOTA")]
    if len(bact) < 2 or len(euc) < 2:
        raise SystemExit(f"panel trop maigre pour un test inter-domaine : {len(bact)} bactéries "
                         f"hors requête, {len(euc)} eucaryotes. Élargir le panel d'abord — et se "
                         f"souvenir qu'un panel restreint aux espèces pathogènes et symbiotiques "
                         f"a produit, pour les domaines SET, un transfert qui n'existait pas.")

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    hypotheses = [
        ("H1_bacteries_monophyletiques",
         "les bactéries, requête comprise, forment un clade : pas de transfert récent, "
         "origine verticale ou ancienne",
         groupe(bact + [a.query]) + "," + groupe(euc)),
        ("H2_requete_dans_eucaryotes",
         "la requête se range avec les eucaryotes à l'exclusion des autres bactéries : "
         "transfert entre domaines",
         groupe(euc + [a.query]) + "," + groupe(bact)),
    ]
    if a.donor_clade:
        donneurs = [d.strip() for d in a.donor_clade.split(",") if d.strip()]
        inconnus = [d for d in donneurs if d not in tax]
        if inconnus:
            raise SystemExit("--donor-clade : étiquettes inconnues " + ", ".join(inconnus))
        hypotheses.append(
            ("H3_requete_avec_donneur_designe",
             "la requête est sœur du clade donneur désigné (" + ", ".join(donneurs[:4])
             + (" ..." if len(donneurs) > 4 else "") + ")",
             groupe(donneurs + [a.query])))

    ordre, lignes_cmd = [], []
    for nom, libelle, corps in hypotheses:
        chemin = out / f"{nom}.constraint.nwk"
        chemin.write_text("(" + corps + ");\n", encoding="utf-8")
        ordre.append(f"{nom}\t{libelle}")
        lignes_cmd.append(
            f"$IQ -s $ALN -m {a.model} -g {chemin.name} -pre {nom} -T {a.remote_threads}")
    (out / "trees_order.txt").write_text(
        "ML_libre\tarbre ML sans contrainte\n" + "\n".join(ordre) + "\n", encoding="utf-8")

    noms = [n for n, _l, _c in hypotheses]
    script = ["#!/bin/bash",
              "# Comparaison topologique par test AU — à lancer sur mp ou mh",
              "# (cf. skill science-commun:remote-compute ; ni IQ-TREE ni MAFFT en local).",
              "# Sur mh le binaire s'appelle `iqtree` et NON `iqtree2`, et son environnement",
              "# micromamba exige LD_LIBRARY_PATH : d'où IQ et ALN paramétrables.",
              "set -euo pipefail",
              f'IQ="${{IQ:-{a.iqtree_bin}}}"',
              f'ALN="${{ALN:-{Path(a.alignment).name}}}"',
              'cd "$(dirname "$0")"', "",
              "# 1. arbre ML sans contrainte",
              f"$IQ -s $ALN -m {a.model} -pre ML_libre -T {a.remote_threads}", "",
              "# 2. un arbre ML par hypothèse contrainte"] + lignes_cmd + [
              "", "# 3. les arbres dans l'ORDRE de trees_order.txt, puis le test AU",
              "cat ML_libre.treefile " + " ".join(f"{n}.treefile" for n in noms) + " > trees.nwk",
              f"$IQ -s $ALN -m {a.model} -z trees.nwk -n 0 -zb 10000 -au "
              f"-pre au_test -T {a.remote_threads}", "",
              "# 4. lecture du verdict, en local :",
              "#    python3 topology_test.py read --iqtree au_test.iqtree "
              "--order trees_order.txt"]
    (out / "commandes.sh").write_text("\n".join(script) + "\n", encoding="utf-8")

    print(f"panel : {len(bact) + 1} bactéries (dont la requête), {len(euc)} eucaryotes, "
          f"{len(autres)} autres")
    print(f"{len(hypotheses)} contrainte(s) écrite(s) dans {out}/ ; recette dans "
          f"{out}/commandes.sh")
    print("Le modèle passé est « " + a.model + " » : sur un jeu déclaré HETEROGENE ou SATURE par "
          "composition_saturation.py,\nprendre un modèle à profils hétérogènes (par exemple "
          "LG+C60+F+G ou PMSF) — un test AU sous modèle\nhomogène hérite de l'artefact qu'il est "
          "censé arbitrer.")


def mode_ordre(ordre_chemin):
    for brut in Path(ordre_chemin).read_text(encoding="utf-8").splitlines():
        if brut.startswith("#mode\t"):
            return brut.split("\t", 1)[1].strip()
    return None


def lit_au(chemin, ordre_chemin, seuil):
    lignes_fichier = Path(chemin).read_text(encoding="utf-8", errors="replace").splitlines()
    debut = next((i for i, l in enumerate(lignes_fichier) if l.strip().startswith("USER TREES")),
                 None)
    if debut is None:
        raise SystemExit(f"aucun bloc « USER TREES » dans {chemin} : le run a-t-il bien été "
                         f"lancé avec -z ... -au ?")
    # On repère l'en-tête par son contenu (`p-AU`) puis on lit les lignes qui commencent par un
    # numéro d'arbre. Ni la distance à « USER TREES » ni le nombre de lignes vides intercalaires
    # ne sont stables d'une version d'IQ-TREE à l'autre.
    i_entete = next((i for i in range(debut, len(lignes_fichier)) if "p-AU" in lignes_fichier[i]),
                    None)
    if i_entete is None:
        raise SystemExit("le tableau ne contient pas de colonne p-AU : relancer IQ-TREE avec -au")
    colonnes = lignes_fichier[i_entete].split()
    try:
        i_au = colonnes.index("p-AU")
        i_logl = colonnes.index("logL")
        i_delta = colonnes.index("deltaL")
    except ValueError as e:
        raise SystemExit(f"en-tête inattendu du tableau AU : {lignes_fichier[i_entete]!r} ({e})")

    resultats, attendu = [], len(colonnes) - 1
    for l in lignes_fichier[i_entete + 1:]:
        m = re.match(r"\s*(\d+)\s+(-?\d.*)", l)
        if not m:
            if resultats:  # fin du tableau
                break
            continue
        # IQ-TREE marque les tests significatifs d'un `+`/`-` SÉPARÉ par une espace
        # (« 0.588 + »). Les laisser dans la liste décale toutes les colonnes d'un cran et
        # ferait lire un p-KH à la place d'un p-AU, sans aucune erreur visible.
        champs = [c for c in (t.rstrip("+-") for t in m.group(2).split()) if c not in ("", "-")]
        if len(champs) != attendu:
            raise SystemExit(
                f"ligne du tableau AU à {len(champs)} valeurs pour {attendu} colonnes "
                f"annoncées :\n  {l}\nLire ce tableau au jugé ferait prendre une colonne pour "
                f"une autre ; corriger le parseur plutôt que d'ignorer la ligne.")
        resultats.append({
            "rang": int(m.group(1)),
            "logL": float(champs[i_logl - 1]),
            "deltaL": float(champs[i_delta - 1]),
            "p_AU": float(champs[i_au - 1]),
        })
    if not resultats:
        raise SystemExit("tableau AU illisible : aucune ligne numérique reconnue")

    # Deux formats d'ordre : global (nom, libellé) et local (nom, famille, libellé, source), où
    # source vaut « arbre » ou « =<nom> » pour une hypothèse reprise par alias d'un arbre testé.
    entrees = []
    for brut in Path(ordre_chemin).read_text(encoding="utf-8").splitlines():
        if not brut.strip() or brut.startswith("#"):
            continue
        champs = brut.split("\t")
        if len(champs) >= 4 and champs[1] in FAMILLES:
            source = champs[3].strip()
            entrees.append({"nom": champs[0], "famille": champs[1], "libelle": champs[2],
                            "alias": source[1:] if source.startswith("=") else None})
        else:
            entrees.append({"nom": champs[0], "famille": None,
                            "libelle": champs[1] if len(champs) > 1 else "", "alias": None})
    testes = [e for e in entrees if e["alias"] is None]
    if len(testes) != len(resultats):
        raise SystemExit(f"{len(resultats)} arbres testés mais {len(testes)} arbres distincts "
                         f"dans --order : l'appariement serait arbitraire. Vérifier que les "
                         f"arbres ont été concaténés dans l'ordre de trees_order.txt, alias exclus.")
    par_nom = {}
    for r, e in zip(resultats, testes):
        r.update(e)
        r["rejete"] = r["p_AU"] < seuil
        par_nom[e["nom"]] = r
    sortie = []
    for e in entrees:
        if e["alias"] is None:
            sortie.append(par_nom[e["nom"]])
            continue
        cible = par_nom.get(e["alias"])
        if cible is None:
            raise SystemExit(f"{e['nom']} renvoie à « {e['alias']} », absent des arbres testés")
        sortie.append(dict(cible, nom=e["nom"], famille=e["famille"], libelle=e["libelle"],
                           alias=e["alias"]))
    return sortie


AVERTISSEMENT_LOCAL = [
    "Ancien mode local (contrainte partielle, sans marqueur #mode) : il ne teste PAS le",
    "placement de la requête. La contrainte",
    "{requête} ∪ C | reste se satisfait aussi en déplaçant C contre la requête, et",
    "l'optimiseur retient le moins coûteux : pour une requête proche d'un congénère,",
    "c'est C qui bouge (mesuré sur PF00856 dans les quatre arbres contraints). Un rejet",
    "dit « C ne se loge pas là », un non-rejet « C est mal ancré » ; aucun ne juge le",
    "transfert. Conclure sur le placement dans l'arbre libre (read_interdomain.py).",
    "Régénérer avec `constraints --local` (squelette fixé, clade focal) et relancer."]


def controle_depuis_fichiers(arbres_chemin, dossier, res):
    """Rejoue `controle_placements` sur les arbres RÉELLEMENT évalués (trees_local.nwk)."""
    manquants = [c for c in (arbres_chemin, dossier / "clade_focal.tsv",
                             dossier / "ensembles_reference.tsv") if not Path(c).exists()]
    if manquants:
        return ["contrôle impossible, fichier(s) absent(s) : "
                + ", ".join(str(m) for m in manquants)]
    from Bio import Phylo
    sys.setrecursionlimit(max(sys.getrecursionlimit(), 10000))
    info = dict(l.split("\t", 1) for l in (dossier / "clade_focal.tsv")
                .read_text(encoding="utf-8").splitlines() if "\t" in l)
    focal, vk = frozenset(info["membres"].split(",")), frozenset(info["clade_vertical"].split(","))
    attaches = {}
    for l in (dossier / "ensembles_reference.tsv").read_text(encoding="utf-8").splitlines()[1:]:
        c = l.split("\t")
        membres = frozenset(c[6].split(","))
        attaches[c[0]] = None if membres == vk else membres
    testes = [r["nom"] for r in res if not r.get("alias")]
    arbres = list(Phylo.parse(str(arbres_chemin), "newick"))
    if len(arbres) != len(testes):
        return [f"{len(arbres)} arbres dans {Path(arbres_chemin).name} pour {len(testes)} "
                f"arbres distincts dans l'ordre : l'appariement serait arbitraire"]
    return controle_placements(list(zip(testes, arbres)), focal, attaches)


def verdict_local(res, fixe=False):
    v = [r for r in res if r["famille"] == "V"]
    t = [r for r in res if r["famille"] == "T"]
    if not v or not t:
        return "INDECIDABLE", ["Il manque une famille d'hypothèses (V ou T) : rejouer `constraints "
                               "--local` plutôt que d'interpréter ce tableau à la main."]
    v_ouvertes = [r for r in v if not r["rejete"]]
    t_ouvertes = [r for r in t if not r["rejete"]]
    if fixe:
        return verdict_fixe(v, t, v_ouvertes, t_ouvertes)
    if v_ouvertes and not t_ouvertes:
        return "VERTICAL_SOUTENU", [
            f"Les {len(t)} placements de la requête dans un clade du domaine donneur sont TOUS",
            "rejetés, et son rattachement à sa propre lignée ne l'est pas ("
            + ", ".join(r["nom"] for r in v_ouvertes) + ").",
            "Limite : seuls les clades d'au moins la taille minimale ont été testés ; une séquence",
            "isolée du domaine donneur n'a pas été proposée comme sœur de la requête."]
    if t_ouvertes and not v_ouvertes:
        return "TRANSFERT_SOUTENU", [
            f"Les {len(v)} rattachements de la requête à sa propre lignée sont TOUS rejetés, et",
            "son placement dans au moins un clade du domaine donneur ne l'est pas ("
            + ", ".join(r["nom"] for r in t_ouvertes) + ").",
            "Le test ne donne pas le SENS du transfert : lire read_interdomain.py, et se",
            "rappeler qu'une composition hétérogène non traitée produit ce même résultat."]
    if v_ouvertes and t_ouvertes:
        return "INDECIDABLE", [
            "Au moins un placement de chaque famille reste compatible avec les données :",
            "  lignée propre : " + ", ".join(r["nom"] for r in v_ouvertes),
            "  domaine donneur : " + ", ".join(r["nom"] for r in t_ouvertes),
            "Le placement de la requête n'est pas tranché. Un clade donneur à tige longue,",
            "mal ancré, se déplace à bas prix : vérifier sa tige avant d'y lire un signal."]
    return "INDECIDABLE", [
        "TOUS les placements testés sont rejetés, ceux de sa lignée comme ceux du domaine",
        "donneur : la requête se range ailleurs (autre groupe de son domaine, troisième",
        "domaine, ou longue branche). Contrairement au mode global, ce double rejet n'est pas",
        "un artefact des contraintes : il décrit la requête. Lire ses voisins dans l'arbre",
        "libre (read_interdomain.py) ; un transfert depuis le domaine donneur reste REJETÉ",
        "pour chacun des clades testés."]


def verdict_fixe(v, t, v_ouvertes, t_ouvertes):
    """Lecture du mode à squelette fixé : chaque ligne compare un POINT D'ATTACHE du clade focal."""
    noms_v = {r["nom"] for r in v}
    confondus = [f"{r['nom']} (= {r['alias']})" for r in t if r.get("alias") in noms_v]
    note = ([] if not confondus else [
        "Indiscernables : " + ", ".join(confondus) + " — ce clade donneur est déjà le frère",
        "du clade focal dans le squelette ; son placement ne se distingue pas de la lignée propre."])
    limites = [
        "Limites : le test est conditionnel au squelette (l'arbre inféré sans la requête) ; seuls",
        "les clades d'au moins la taille minimale ont été proposés comme frères ; un transfert",
        "vers l'ancêtre d'un groupe plus large que le clade focal n'a pas été testé."]
    if v_ouvertes and not t_ouvertes:
        return "VERTICAL_SOUTENU", [
            f"Le clade focal greffé sur chacun des {len(t)} clades du domaine donneur est REJETÉ,",
            "sur un squelette identique ; dans sa lignée il ne l'est pas ("
            + ", ".join(r["nom"] for r in v_ouvertes) + ")."] + limites
    if t_ouvertes and not v_ouvertes:
        return "TRANSFERT_SOUTENU", [
            f"Les {len(v)} placements du clade focal dans sa propre lignée sont TOUS rejetés, et",
            "au moins un placement frère d'un clade du domaine donneur ne l'est pas ("
            + ", ".join(r["nom"] for r in t_ouvertes) + ").",
            "Le test ne donne pas le SENS du transfert : lire read_interdomain.py, et se",
            "rappeler qu'une composition hétérogène non traitée produit ce même résultat."] + limites
    if v_ouvertes and t_ouvertes:
        return "INDECIDABLE", [
            "Au moins un placement de chaque famille reste compatible avec les données :",
            "  lignée propre : " + ", ".join(r["nom"] for r in v_ouvertes),
            "  domaine donneur : " + ", ".join(r["nom"] for r in t_ouvertes),
            "Le squelette étant fixé, ce non-rejet porte bien sur le point d'attache du clade",
            "focal : l'alignement ne suffit pas à le trancher."] + note + limites
    return "INDECIDABLE", [
        "TOUS les placements sont rejetés, y compris le meilleur du jeu : ce n'est pas attendu",
        "d'un test AU sur un jeu fermé. Relire le tableau et le journal IQ-TREE avant tout."]


def commande_read(a):
    res = lit_au(a.iqtree, a.order, a.seuil)
    L = ["TEST TOPOLOGIQUE (AU) — les hypothèses concurrentes", "=" * 78, "",
         f"seuil de rejet : p-AU < {a.seuil}", ""]
    local = any(r.get("famille") for r in res)
    for r in sorted(res, key=lambda r: -r["logL"]):
        fam = f"[{r['famille']}] " if local else ""
        alias = f"  (= {r['alias']})" if r.get("alias") else ""
        L.append(f"  {fam}{r['nom']:<44} logL = {r['logL']:.2f}  deltaL = {r['deltaL']:8.2f}  "
                 f"p-AU = {r['p_AU']:.4f}  {'REJETÉE' if r['rejete'] else 'non rejetée'}{alias}")
        if r["libelle"]:
            L.append(f"{'':8}{r['libelle']}")
    par_nom = {r["nom"]: r for r in res}
    h1, h2 = par_nom.get("H1_bacteries_monophyletiques"), par_nom.get("H2_requete_dans_eucaryotes")
    if mode_ordre(a.order) == MODE_FIXE:
        arbres = (Path(a.trees) if getattr(a, "trees", None)
                  else Path(a.order).parent / "trees_local.nwk")
        ecarts = controle_depuis_fichiers(arbres, Path(a.order).parent, res)
        L.insert(3, "mode LOCAL, squelette fixé : seul le clade focal (requête + congénères) "
                    "change de place")
        if ecarts:
            verdict, lecture = "NON_VALIDE", [
                "Contrôle « qui a bougé » ÉCHOUÉ : le tableau ne compare pas des placements du",
                "seul clade focal sur un squelette commun, et ne se lit donc pas."] \
                + ["  " + e for e in ecarts]
        else:
            verdict, lecture = verdict_local(res, fixe=True)
            lecture = [f"Contrôle « qui a bougé » passé sur {arbres.name} : dans chaque arbre le "
                       "clade focal est",
                       "un clade, frère de l'ensemble visé, et le squelette est identique.", ""] \
                + lecture
    elif local:
        indicatif, lecture_ind = verdict_local(res)
        verdict = "NON_VALIDE"
        lecture = AVERTISSEMENT_LOCAL + ["", f"Lecture indicative, SANS valeur de preuve : {indicatif}"] \
            + ["  " + l for l in lecture_ind]
        L.insert(3, "ancien mode LOCAL : contrainte {requête} ∪ C, NON VALIDE (AG3, 2026-09-25)")
    elif h1 is None or h2 is None:
        verdict, lecture = "INDECIDABLE", [
            "H1 ou H2 absente du tableau : ce script ne sait pas quoi comparer. Rejouer la",
            "génération des contraintes plutôt que d'interpréter ce tableau à la main."]
    elif h1["rejete"] and not h2["rejete"]:
        verdict, lecture = "TRANSFERT_SOUTENU", [
            "La monophylie des bactéries est REJETÉE par les données, et le placement de la",
            "requête parmi les eucaryotes ne l'est pas. Le transfert inter-domaine est soutenu",
            "par un test, pas seulement par une lecture d'arbre. Il reste à en établir le SENS,",
            "que ce test ne donne pas : lire read_interdomain.py, et se rappeler qu'une",
            "composition hétérogène non traitée produit ce même résultat."]
    elif h2["rejete"] and not h1["rejete"]:
        verdict, lecture = "VERTICAL_SOUTENU", [
            "Le placement de la requête parmi les eucaryotes est REJETÉ, la monophylie des",
            "bactéries ne l'est pas : les données soutiennent une histoire bactérienne propre.",
            "C'est un résultat négatif publiable, et c'est la conclusion à laquelle est parvenu",
            "Alvarez-Venegas et al. (2007) pour les gènes bactériens à domaine SET."]
    elif h1["rejete"] and h2["rejete"]:
        moins, plus = sorted((h1, h2), key=lambda r: r["deltaL"])
        verdict, lecture = "INDECIDABLE", [
            "Les DEUX hypothèses sont rejetées : l'arbre libre n'est ni l'une ni l'autre. Ce",
            "n'est PAS le cas « l'alignement ne tranche pas » — il tranche, et contre les deux.",
            "",
            "Les deux contraintes imposent une bipartition GLOBALE des domaines et non le seul",
            "placement de la requête. Si les domaines ne sont pas eux-mêmes monophylétiques sur",
            "ce panel, les deux arbres contraints sont pénalisés pour une raison ÉTRANGÈRE à la",
            "requête, et leur rejet ne dit alors rien de son origine. Contrôler la monophylie de",
            "chaque domaine dans l'arbre libre AVANT de relire ce tableau : sur un domaine à",
            "histoire réticulée, ce rejet double est attendu quel que soit le placement.",
            "",
            f"Écart entre les deux : {plus['nom']} est",
            f"à {plus['deltaL'] - moins['deltaL']:.1f} unités de logL de plus que "
            f"{moins['nom']} de l'arbre",
            f"libre (p-AU {plus['p_AU']:.2e} contre {moins['p_AU']:.2e}). Cet écart est la seule "
            f"information",
            "exploitable du tableau, et il n'autorise PAS à retenir la moins rejetée : la lecture",
            "revient au placement dans l'arbre libre et à son support (read_interdomain.py), que",
            "ce test ne remplace pas ici."]
    else:
        verdict, lecture = "INDECIDABLE", [
            "Aucune des deux hypothèses n'est rejetée : l'alignement ne tranche pas. C'est le",
            "cas le plus fréquent sur un domaine court et ancien, et c'est une réponse, pas un",
            "échec : ni le transfert ni son absence ne peuvent être affirmés. Élargir le panel",
            "ou allonger l'alignement avant de conclure."]
    L += ["", "-- VERDICT " + "-" * 67] + lecture + ["", f"VERDICT_TOPOLOGIE: {verdict}"]
    texte = "\n".join(L)
    print(texte)
    if a.out:
        Path(a.out).write_text(texte + "\n", encoding="utf-8")
        print(f"\n[écrit dans {a.out}]", file=sys.stderr)


def main():
    p = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[1])
    sub = p.add_subparsers(dest="commande", required=True)

    c = sub.add_parser("constraints", help="écrit les contraintes et la recette IQ-TREE")
    c.add_argument("--alignment", required=True)
    c.add_argument("--taxonomy", required=True, help="TSV étiquette<TAB>domaine")
    c.add_argument("--query", required=True, help="étiquette de la séquence testée")
    c.add_argument("--donor-clade", help="étiquettes du donneur désigné, séparées par des "
                                         "virgules (hypothèse H3, facultative)")
    c.add_argument("--model", default="LG+C60+F+G",
                   help="modèle IQ-TREE (défaut : profils hétérogènes, adapté à l'inter-domaine)")
    # Nommée `--remote-threads` et non `--threads` : ce nombre ne décrit QUE le job écrit dans
    # commandes.sh, qui tournera sur mp ou mh. Ce script-ci n'écrit que des fichiers texte. Le
    # nom court faisait lire la commande comme un calcul local à N cœurs, par un humain comme
    # par le garde-fou de ressources partagées, qui l'a refusée à ce titre le 2026-09-22.
    c.add_argument("--remote-threads", "--threads", dest="remote_threads", default="16",
                   help="cœurs demandés par le job DISTANT écrit dans commandes.sh")
    c.add_argument("--iqtree-bin", default="iqtree2",
                   help="nom du binaire IQ-TREE ; sur mh c'est `iqtree`, pas `iqtree2`")
    c.add_argument("--local", action="store_true",
                   help="contraintes sur le seul PLACEMENT de la requête (recommandé dès qu'un "
                        "domaine n'est pas monophylétique dans l'arbre libre)")
    c.add_argument("--reference-tree",
                   help="--local : arbre ML inféré SANS la requête, où se lisent les ensembles")
    c.add_argument("--ml-tree", help="--local : arbre ML libre, avec la requête")
    c.add_argument("--donor-domain", choices=DOMAINES,
                   help="--local : domaine donneur (défaut : EUKARYOTA pour une requête "
                        "bactérienne, BACTERIA sinon)")
    c.add_argument("--min-clade", type=int, default=2,
                   help="--local : taille minimale d'un ensemble de référence (défaut 2)")
    c.add_argument("--out", required=True)

    r = sub.add_parser("read", help="lit le tableau AU d'un .iqtree et rend le verdict")
    r.add_argument("--iqtree", required=True)
    r.add_argument("--order", required=True, help="trees_order.txt écrit par `constraints`")
    r.add_argument("--trees", help="mode à squelette fixé : arbres évalués, pour le contrôle "
                                   "« qui a bougé » (défaut : trees_local.nwk à côté de --order)")
    r.add_argument("--seuil", type=float, default=0.05)
    r.add_argument("--out")

    a = p.parse_args()
    (ecrit_contraintes if a.commande == "constraints" else commande_read)(a)


if __name__ == "__main__":
    main()
