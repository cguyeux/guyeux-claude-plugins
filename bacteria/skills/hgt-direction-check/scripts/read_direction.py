#!/usr/bin/env python3
"""
Objet: trancher le SENS d'un transfert horizontal depuis deux arbres de famille de gènes. Pour
    chaque séquence portée par un donneur candidat (phage, plasmide, intégron) : est-elle
    NICHÉE dans la diversité cellulaire (capture cellule -> donneur) ou BASALE à elle (la
    famille proviendrait du donneur) ? Applique la concordance de taxon d'hôte et le contrôle
    d'attraction des longues branches, sans lesquels le nichage ne conclut rien.
Entrées: --tree (arbre complet), --tree-control (arbre inféré INDÉPENDAMMENT sur le seul panel
    cellulaire), --hosts (TSV: etiquette<TAB>taxon_hote<TAB>groupe), --origins (TSV ou CSV:
    nom_reference<TAB>organisme), et le préfixe des étiquettes donneuses (--donor-prefix).
Sorties: le verdict sur stdout et, avec --out, dans un fichier.
Réutilisable: oui, c'est l'objet du skill hgt-direction-check.
Projet: généralisé depuis SpacerEgalVirus/analyses/phase61b_p68_2_lecture_arbre.py (P68.2).
Date: 2026-09-12.

Trois mesures, et aucune ne conclut seule.

1. NICHAGE. Pour chaque feuille donneuse, on remonte vers la racine jusqu'au premier ancêtre
   dont la descendance contient une référence cellulaire. Si ce plus petit clade est petit
   devant l'arbre, la séquence est profondément nichée ; une séquence BASALE n'a de cellulaires
   qu'à un ancêtre très haut, et le rapport des tailles le dit.

2. CONCORDANCE DE TAXON D'HÔTE. Le nichage ne suffit pas : la séquence donneuse doit se ranger
   près des homologues du taxon de son PROPRE hôte. C'est ce qui sépare une capture réelle d'un
   placement quelconque, et ce qui transforme plusieurs cas en résultat répété.

3. CONTRÔLE LBA. Le clade d'accueil doit exister dans l'arbre calculé SANS les séquences
   donneuses. Sinon le nichage est une construction de l'analyse. Ne JAMAIS fabriquer cet arbre
   en élaguant le premier : il rendrait les mêmes partitions, donc un contrôle trivialement
   satisfait. En l'absence d'arbre de contrôle, ce script rend le nichage et les supports en
   marquant le contrôle « NON MESURÉ » et ne prononce AUCUN verdict.
"""

import argparse
import csv
import io
import re
import sys
from pathlib import Path

from Bio import Phylo

TOLERANCE_FEUILLE = 1  # écart de feuilles toléré entre clade d'accueil et partition de contrôle
FRACTION_NICHAGE = 0.5  # au-delà, le clade d'accueil est trop gros pour parler de nichage


def charge_tsv(chemin, colonnes_min=2):
    """Lit un TSV ou CSV à deux colonnes ou plus, en ignorant les lignes trop courtes."""
    lignes = []
    texte = Path(chemin).read_text(encoding="utf-8")
    delim = "\t" if "\t" in texte.split("\n")[0] else ","
    for row in csv.reader(io.StringIO(texte), delimiter=delim):
        if len(row) >= colonnes_min and row[0] and not row[0].startswith("#"):
            lignes.append(row)
    return lignes


def charge_hotes(chemin):
    """etiquette -> (taxon de l'hôte, groupe taxonomique du taxon)."""
    h = {}
    for row in charge_tsv(chemin, 3):
        h[row[0].strip()] = (row[1].strip(), row[2].strip())
    return h


def charge_origines(chemin, col_nom=0, col_org=1):
    """nom de référence -> organisme d'origine. Accepte un CSV large (ex. ISfinder IS.csv) :
    seules deux colonnes sont lues, données par --origins-cols."""
    o = {}
    for row in charge_tsv(chemin, max(col_nom, col_org) + 1):
        if len(row) > max(col_nom, col_org):
            o[row[col_nom].strip()] = row[col_org].strip()
    return o


def charge_groupes(chemin):
    """genre ou préfixe d'organisme -> groupe taxonomique. Le rattachement doit être INSTRUIT,
    pas devine : un genre oublié fait compter un voisinage concordant comme discordant."""
    g = {}
    for row in charge_tsv(chemin, 2):
        g[row[0].strip()] = row[1].strip()
    return g


def groupe_de(organisme, groupes, non_classes):
    if not organisme:
        return "?"
    for prefixe, grp in groupes.items():
        if organisme.startswith(prefixe):
            return grp
    non_classes.add(organisme.split()[0] if organisme.split() else organisme)
    return "non-classé"


def feuilles(clade):
    return [t.name for t in clade.get_terminals()]


def lit_arbre(chemin):
    """Lit un treefile IQ-TREE produit avec `-B` et `-alrt`, dont les supports internes sont
    écrits `SH-aLRT/UFBoot` (par exemple `94.4/100`). Biopython ne sait pas parser ce champ
    composite et rend `confidence = None`, ce qui ferait passer un nœud parfaitement soutenu
    pour un nœud sans support. On lit donc deux fois le même arbre, une fois avec chaque
    moitié du champ, et on porte les deux valeurs sur les clades du premier."""
    # Les parcours de clades de Biopython sont RÉCURSIFS (générateurs imbriqués, plusieurs
    # cadres par nœud) : sur un arbre de quelques centaines de feuilles un peu déséquilibré,
    # `get_terminals()` dépasse la limite par défaut et lève un `RecursionError` au milieu de
    # l'analyse. Mesuré le 2026-09-22 en rejouant le cas fondateur (246 feuilles) sous
    # Python 3.14 / Biopython 1.87, où il passait auparavant.
    sys.setrecursionlimit(max(sys.getrecursionlimit(), 50_000))
    brut = Path(chemin).read_text(encoding="utf-8")
    compose = re.compile(r"\)(\d+(?:\.\d+)?)/(\d+(?:\.\d+)?)")
    if not compose.search(brut):
        return Phylo.read(chemin, "newick")

    def variante(indice):
        return Phylo.read(io.StringIO(compose.sub(lambda m: ")" + m.group(indice), brut)), "newick")

    arbre, arbre_alrt = variante(2), variante(1)
    for clade, clade_alrt in zip(arbre.get_nonterminals(), arbre_alrt.get_nonterminals()):
        clade.ufboot = clade.confidence
        clade.alrt = clade_alrt.confidence
    return arbre


def racine_mediane(arbre, quoi="l'arbre"):
    """Racine au point médian quand c'est possible. Un Newick SANS longueurs de branche (un
    arbre de contrainte, une topologie copiée à la main, un treefile élagué par un outil tiers)
    fait échouer `root_at_midpoint` de Biopython sur un `UnboundLocalError: tip1` parfaitement
    illisible. On le détecte avant plutôt que de laisser tomber le script : « basal » perd alors
    son sens, mais le nichage, qui est la mesure qui porte la conclusion, n'en dépend pas."""
    if any(t.branch_length for t in arbre.get_terminals()):
        arbre.root_at_midpoint()
        return True
    print(f"[note] {quoi} n'a pas de longueurs de branche : pas de racinage au point médian. "
          f"Le nichage reste lisible, la notion de « basal » non.", file=sys.stderr)
    return False


def support(clade):
    ufb, alrt = getattr(clade, "ufboot", None), getattr(clade, "alrt", None)
    if ufb is None and alrt is None:
        return "support non renseigné"
    return f"SH-aLRT {alrt}, UFBoot {ufb}"


def analyse(arbre, arbre_sans, origine, hotes, groupes, prefixe, controle_fait, non_classes):
    lignes, verdicts = [], {}
    total = len(arbre.get_terminals())
    noms_donneurs = [n for n in feuilles(arbre) if n.startswith(prefixe)]
    cellulaires_sans = set(feuilles(arbre_sans))
    partitions_sans = {frozenset(feuilles(c)) for c in arbre_sans.get_nonterminals()}

    for nom in sorted(noms_donneurs):
        chemin = arbre.get_path(nom)
        accueil = None
        for clade in reversed(chemin[:-1]):
            if any(not f.startswith(prefixe) for f in feuilles(clade)):
                accueil = clade
                break
        if accueil is None:
            lignes.append(f"{nom} : aucun ancêtre contenant une référence cellulaire (anormal)")
            continue

        fs = feuilles(accueil)
        cellulaires = [f for f in fs if not f.startswith(prefixe)]
        donneurs_dedans = [f for f in fs if f.startswith(prefixe)]
        fraction = len(fs) / total

        org_voisins = [(c, origine.get(c, "?")) for c in cellulaires]
        compte = {}
        for _c, org in org_voisins:
            g = groupe_de(org, groupes, non_classes)
            compte[g] = compte.get(g, 0) + 1
        dominant = max(compte, key=lambda k: compte[k]) if compte else "?"
        hote, groupe_hote = hotes.get(nom, ("?", "?"))

        # Un clade d'accueil réduit à UNE cellulaire n'est pas testable par partition : une
        # feuille seule n'est jamais une partition interne, et le contrôle rendrait NON par
        # construction. On remonte au premier ancêtre portant au moins deux cellulaires.
        cellulaires_ctrl, elargi = cellulaires, False
        if len(cellulaires) < 2:
            for clade in reversed(chemin[:-1]):
                cc = [f for f in feuilles(clade) if not f.startswith(prefixe)]
                if len(cc) >= 2:
                    cellulaires_ctrl, elargi = cc, True
                    break

        cible = frozenset(c for c in cellulaires_ctrl if c in cellulaires_sans)
        survit = cible in partitions_sans
        proche = bool(cible) and not survit and any(
            len(part ^ cible) <= TOLERANCE_FEUILLE for part in partitions_sans
        )

        niche = fraction < FRACTION_NICHAGE and len(cellulaires) >= 1
        concorde = dominant == groupe_hote and groupe_hote != "?"
        verdicts[nom] = (niche, concorde, (survit or proche) if controle_fait else False)

        etat_ctrl = ("NON MESURÉ — arbre de contrôle absent" if not controle_fait
                     else ("OUI" if survit
                           else ("OUI, à une feuille près" if proche else "NON"))
                     + (f" [testé sur {len(cellulaires_ctrl)} cellulaires]" if elargi else ""))
        lignes += [
            f"-- {nom} " + "-" * max(3, 74 - len(nom)),
            f"   hôte du donneur          : {hote} ({groupe_hote})",
            f"   support du clade d'accueil : {support(accueil)}",
            f"   plus petit clade avec du cellulaire : {len(fs)} feuilles"
            f" ({fraction:.1%} de l'arbre), dont {len(cellulaires)} cellulaires"
            + (f" et {len(donneurs_dedans)} donneuses" if len(donneurs_dedans) > 1 else ""),
            "   voisins cellulaires      : "
            + ", ".join(f"{c} ({org})" for c, org in org_voisins[:6])
            + (" ..." if len(org_voisins) > 6 else ""),
            f"   groupe dominant des voisins : {dominant}"
            f"  -> {'CONCORDE' if concorde else 'DISCORDE'} avec l'hôte",
            f"   nichée dans la diversité cellulaire : {'OUI' if niche else 'NON'}",
            f"   clade d'accueil présent sans les donneuses (contrôle LBA"
            f"{', élargi' if elargi else ''}) : {etat_ctrl}",
            "",
        ]
    return lignes, verdicts


def main():
    p = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[1])
    p.add_argument("--tree", required=True, help="arbre complet (panel cellulaire + donneurs)")
    p.add_argument("--tree-control", help="arbre inféré INDÉPENDAMMENT sur le seul panel "
                                          "cellulaire ; sans lui, aucun verdict n'est rendu")
    p.add_argument("--hosts", required=True,
                   help="TSV : etiquette<TAB>taxon_hote<TAB>groupe_taxonomique")
    p.add_argument("--origins", required=True,
                   help="TSV/CSV : nom_reference<TAB>organisme d'origine")
    p.add_argument("--origins-cols", default="0,1",
                   help="indices des colonnes nom,organisme dans --origins (défaut 0,1)")
    p.add_argument("--groups", required=True,
                   help="TSV : prefixe_organisme<TAB>groupe_taxonomique ; rattachement INSTRUIT")
    p.add_argument("--donor-prefix", default="DONOR_",
                   help="préfixe des étiquettes des séquences portées par le donneur")
    p.add_argument("--out", help="fichier de sortie en plus de stdout")
    a = p.parse_args()

    col_nom, col_org = (int(x) for x in a.origins_cols.split(","))
    arbre = lit_arbre(a.tree)
    origine = charge_origines(a.origins, col_nom, col_org)
    hotes = charge_hotes(a.hosts)
    groupes = charge_groupes(a.groups)
    non_classes = set()

    controle_fait = bool(a.tree_control) and Path(a.tree_control).exists()
    if controle_fait:
        arbre_sans = lit_arbre(a.tree_control)
        racine_mediane(arbre_sans, "l'arbre de contrôle")
    else:
        # Substitut obtenu par élagage : il rend les MÊMES partitions que l'arbre complet, donc
        # le contrôle qu'il donnerait serait trivialement satisfait. Il ne sert qu'à faire
        # tourner le code, et son résultat est ignoré (controle_fait est faux).
        arbre_sans = lit_arbre(a.tree)
        for f in [t for t in arbre_sans.get_terminals() if t.name.startswith(a.donor_prefix)]:
            arbre_sans.prune(f)

    # IQ-TREE rend un arbre non raciné et « basal » n'a pas de sens sans racine. Le point médian
    # est une convention explicite, pas une vérité biologique ; le nichage n'en dépend pas.
    racine_mediane(arbre, "l'arbre complet")

    lignes, verdicts = analyse(arbre, arbre_sans, origine, hotes, groupes,
                               a.donor_prefix, controle_fait, non_classes)

    niches = sum(1 for n, _c, _l in verdicts.values() if n)
    concordants = sum(1 for n, c, _l in verdicts.values() if n and c)
    controles = sum(1 for n, _c, l in verdicts.values() if n and l) if controle_fait else 0

    entete = [
        "SENS DU TRANSFERT HORIZONTAL — lecture topologique",
        "=" * 78,
        "",
        f"arbre complet      : {len(arbre.get_terminals())} feuilles"
        f" ({len(verdicts)} portées par un donneur)",
        f"arbre de contrôle  : {len(arbre_sans.get_terminals())} feuilles"
        + ("  (inféré indépendamment)" if controle_fait
           else "  [ÉLAGUÉ — le contrôle LBA n'a PAS tourné]"),
        "",
    ]
    bilan = [
        "-- VERDICT " + "-" * 67,
        f"séquences donneuses nichées dans la diversité cellulaire : {niches}/{len(verdicts)}",
        f"   dont le groupe des voisins concorde avec l'hôte : {concordants}",
        "   dont le clade d'accueil survit au retrait des donneuses  : "
        + (str(controles) if controle_fait else "NON MESURÉ (arbre de contrôle absent)"),
        "",
    ]
    if not controle_fait:
        bilan += [
            "AUCUN VERDICT n'est prononcé : le contrôle d'attraction des longues branches",
            "exige l'arbre inféré INDÉPENDAMMENT sur le seul panel cellulaire, et il manque.",
            "Le nichage et la concordance ci-dessus sont acquis et n'en dépendent pas ; ce qui",
            "reste à écarter est qu'un clade d'accueil ait été FABRIQUÉ par la présence des",
            "séquences donneuses. Relancer dès que l'arbre de contrôle est disponible.",
        ]
    elif verdicts and niches == len(verdicts) == concordants == controles:
        bilan += [
            "Lecture : toutes les séquences portées par le donneur sont nichées dans la",
            "diversité cellulaire, chacune auprès des homologues du taxon de son propre hôte,",
            "et chaque clade d'accueil existe indépendamment d'elles. Le sens du transfert est",
            "CELLULE -> DONNEUR. Une identité élevée au gène du donneur ne porte donc aucune",
            "information de capture par lui : elle mesure une position dans la structure de la",
            "famille.",
        ]
    elif niches == 0:
        bilan += [
            "Lecture : aucune séquence donneuse n'est nichée. La lecture inverse (la famille",
            "proviendrait du donneur) devient défendable, ce qui serait un résultat fort et",
            "demanderait un panel élargi avant toute affirmation.",
        ]
    else:
        bilan += [
            "Lecture : le résultat est MIXTE et ne tranche pas seul. Détailler cas par cas",
            "ci-dessus ; un nichage sans concordance de taxon, ou sans survie du clade",
            "d'accueil, ne vaut pas démonstration.",
        ]
    if non_classes:
        bilan += [
            "",
            f"ATTENTION : {len(non_classes)} organisme(s) sans groupe instruit dans --groups, "
            "comptés à part",
            "  et non versés dans une discordance : " + ", ".join(sorted(non_classes)[:12]),
            "  Les rattacher AVANT de lire une discordance comme un fait.",
        ]

    texte = "\n".join(entete + lignes + bilan)
    print(texte)
    if a.out:
        Path(a.out).write_text(texte, encoding="utf-8")
        print(f"\n[écrit dans {a.out}]", file=sys.stderr)


if __name__ == "__main__":
    main()
