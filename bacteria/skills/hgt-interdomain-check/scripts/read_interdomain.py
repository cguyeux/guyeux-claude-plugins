#!/usr/bin/env python3
"""
Objet: prononcer — ou refuser de prononcer — le verdict d'un transfert horizontal INTER-DOMAINE.
    Lit le placement de la séquence requête dans l'arbre de famille, sa concordance TAXONOMIQUE
    (et non d'hôte : un donneur eucaryote libre n'a pas d'hôte), sa survie au retrait de la
    requête et au recodage, puis refuse de conclure tant que les portes amont — contamination
    d'assemblage, composition, test topologique — n'ont pas rendu leur verdict.
Entrées: --tree, --tree-control (inféré INDÉPENDAMMENT sans la requête), --tree-recoded
    (facultatif, exigé dès que la composition n'est pas homogène), --taxonomy
    (TSV étiquette<TAB>domaine<TAB>groupe_fin), --query, et les rapports des trois étapes amont.
Sorties: rapport sur stdout et --out, dernière ligne `VERDICT_INTERDOMAINE: ...`.
Réutilisable: oui, c'est l'étape 4 — la dernière — du skill hgt-interdomain-check.
Projet: écrit pour environnement/pistes.md AG2 (manque (4) du constat du 2026-09-22).
Date: 2026-09-22.

Ce script N'EST PAS une copie de read_direction.py : il en IMPORTE le socle (lecture d'un
Newick à support composite `SH-aLRT/UFBoot`, que Biopython rend autrement `confidence = None` ;
parcours des clades ; format des tableaux). Ce qui change est ce qui devait changer :

- la concordance d'hôte est remplacée par une concordance TAXONOMIQUE du voisinage, parce que
  la question n'est plus « cette séquence est-elle près des homologues du taxon de son hôte »
  mais « ses plus proches voisins forment-ils un groupe taxonomique cohérent, ou un assortiment
  de lignées distantes, ce qui est la signature d'un artefact » ;
- la seule survie au retrait des donneurs ne suffit plus : le placement doit aussi survivre au
  RECODAGE, seul contrôle de l'hétérogénéité de composition entre domaines du vivant ;
- et rien n'est prononcé sans la porte de contamination, qui est le premier suspect de tout
  « gène eucaryote chez une bactérie ».
"""

import argparse
import importlib.util
import re
import sys
from pathlib import Path

SOCLE_DEFAUT = (Path(__file__).resolve().parents[2]
                / "hgt-direction-check" / "scripts" / "read_direction.py")
FRACTION_NICHAGE = 0.5


def charge_socle(chemin):
    chemin = Path(chemin)
    if not chemin.exists():
        raise SystemExit(
            f"socle introuvable : {chemin}\nread_interdomain.py réutilise volontairement "
            f"read_direction.py (skill hgt-direction-check du même plugin) plutôt que d'en "
            f"recopier le parseur Newick. Installer le plugin `bacteria` en entier, ou passer "
            f"--socle <chemin de read_direction.py>.")
    spec = importlib.util.spec_from_file_location("socle_hgt", chemin)
    if spec is None or spec.loader is None:
        raise SystemExit(f"socle illisible : {chemin}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def charge_taxonomie(chemin):
    tax = {}
    for brut in Path(chemin).read_text(encoding="utf-8").splitlines():
        if not brut.strip() or brut.startswith("#"):
            continue
        champs = (brut.split("\t") if "\t" in brut else brut.split(","))
        if len(champs) < 2:
            continue
        tax[champs[0].strip()] = (champs[1].strip().upper(),
                                  champs[2].strip() if len(champs) > 2 else "?")
    return tax


def lit_verdict(chemin, cle):
    """Relit la ligne machine-lisible laissée par une étape amont. Un rapport absent n'est PAS
    un rapport favorable : il rend None, et l'appelant refuse alors de conclure."""
    if not chemin:
        return None
    p = Path(chemin)
    if not p.exists():
        raise SystemExit(f"rapport annoncé mais introuvable : {chemin}")
    m = re.search(rf"^{cle}:\s*(\S+)\s*$", p.read_text(encoding="utf-8"), re.M)
    if not m:
        raise SystemExit(f"{chemin} ne porte pas de ligne « {cle}: » : ce n'est pas la sortie "
                         f"attendue, ou elle a été tronquée.")
    return m.group(1)


def clade_accueil(arbre, requete, mini_voisins):
    """Plus petit ancêtre de la requête portant au moins `mini_voisins` autres feuilles."""
    chemin = arbre.get_path(requete)
    for clade in reversed(chemin[:-1]):
        autres = [f for f in (t.name for t in clade.get_terminals()) if f != requete]
        if len(autres) >= mini_voisins:
            return clade, autres
    return None, []


def profondeur_nichage(arbre, requete, tax, domaine):
    """Taille du plus GRAND clade contenant la requête dont toutes les autres feuilles
    appartiennent à `domaine`. Une requête bactérienne enfouie sous douze eucaryotes successifs
    n'est pas dans la même situation qu'une requête simplement sœur du groupe eucaryote."""
    chemin = arbre.get_path(requete)
    meilleur = 0
    for clade in reversed(chemin[:-1]):
        autres = [f for f in (t.name for t in clade.get_terminals()) if f != requete]
        if autres and all(tax.get(f, ("?", "?"))[0] == domaine for f in autres):
            meilleur = max(meilleur, len(autres))
        else:
            break
    return meilleur


def est_clade(arbre, cible):
    cible = frozenset(cible)
    return any(frozenset(t.name for t in c.get_terminals()) == cible
               for c in arbre.get_nonterminals())


def main():
    p = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[1])
    p.add_argument("--tree", required=True)
    p.add_argument("--tree-control", help="arbre inféré INDÉPENDAMMENT sans la requête")
    p.add_argument("--tree-recoded", help="arbre inféré sur l'alignement recodé")
    p.add_argument("--taxonomy", required=True,
                   help="TSV étiquette<TAB>domaine<TAB>groupe_fin (rattachement INSTRUIT)")
    p.add_argument("--query", required=True)
    p.add_argument("--contamination-report", help="sortie de assembly_contamination_check.py")
    p.add_argument("--composition-report", help="sortie de composition_saturation.py")
    p.add_argument("--topology-report", help="sortie de topology_test.py read")
    p.add_argument("--socle", default=str(SOCLE_DEFAUT))
    p.add_argument("--out")
    a = p.parse_args()

    socle = charge_socle(a.socle)
    tax = charge_taxonomie(a.taxonomy)
    arbre = socle.lit_arbre(a.tree)
    socle.racine_mediane(arbre, "l'arbre complet")
    noms = [t.name for t in arbre.get_terminals()]
    if a.query not in noms:
        raise SystemExit(f"--query {a.query} absente de l'arbre ({len(noms)} feuilles)")
    sans_tax = [n for n in noms if n not in tax]

    L = ["TRANSFERT INTER-DOMAINE — lecture, contrôles et portes", "=" * 78, "",
         f"arbre      : {len(noms)} feuilles", f"requête    : {a.query}", ""]

    # --- portes amont -----------------------------------------------------------------------
    v_cont = lit_verdict(a.contamination_report, "VERDICT_CONTAMINATION")
    v_comp = lit_verdict(a.composition_report, "VERDICT_COMPOSITION")
    v_topo = lit_verdict(a.topology_report, "VERDICT_TOPOLOGIE")
    L += ["-- portes amont",
          f"   contamination d'assemblage : {v_cont or 'NON FOURNIE'}",
          f"   composition et saturation  : {v_comp or 'NON FOURNIE'}",
          f"   test topologique (AU)      : {v_topo or 'NON FOURNI'}", ""]

    # --- placement ---------------------------------------------------------------------------
    accueil, voisins = clade_accueil(arbre, a.query, 2)
    if accueil is None:
        raise SystemExit("aucun ancêtre de la requête ne porte deux autres feuilles : arbre "
                         "dégénéré ou étiquette erronée.")
    fraction = (len(voisins) + 1) / len(noms)
    domaines = {}
    groupes = {}
    for v in voisins:
        d, g = tax.get(v, ("?", "?"))
        domaines[d] = domaines.get(d, 0) + 1
        groupes[g] = groupes.get(g, 0) + 1
    dominant = max(domaines, key=lambda k: domaines[k])
    part_dominant = domaines[dominant] / len(voisins)
    groupe_dominant = max(groupes, key=lambda k: groupes[k])
    part_groupe = groupes[groupe_dominant] / len(voisins)
    dom_requete = tax.get(a.query, ("?", "?"))[0]

    L += ["-- placement de la requête",
          f"   plus petit clade la contenant avec 2 voisins : {len(voisins) + 1} feuilles "
          f"({fraction:.1%} de l'arbre)",
          f"   support de ce clade      : {socle.support(accueil)}",
          f"   voisins                  : " + ", ".join(
              f"{v} [{tax.get(v, ('?', '?'))[0]}/{tax.get(v, ('?', '?'))[1]}]"
              for v in voisins[:6]) + (" ..." if len(voisins) > 6 else ""),
          f"   domaine dominant         : {dominant} ({part_dominant:.0%} des voisins)",
          f"   groupe taxonomique fin dominant : {groupe_dominant} ({part_groupe:.0%})"]

    autre_domaine = dominant != dom_requete and dominant != "?"
    prof = profondeur_nichage(arbre, a.query, tax, dominant) if autre_domaine else 0
    if autre_domaine:
        L.append(f"   enfouissement dans {dominant} : {prof} feuille(s) du même domaine "
                 f"au-dessus d'elle sans interruption")
    coherent = part_groupe >= 0.6
    L.append(f"   cohérence taxonomique du voisinage : "
             + ("COHÉRENT" if coherent else "DISPERSÉ — voisins de groupes distants, "
                                            "signature usuelle d'un artefact"))

    # --- contrôles ---------------------------------------------------------------------------
    controle = None
    if a.tree_control and Path(a.tree_control).exists():
        arbre_ctrl = socle.lit_arbre(a.tree_control)
        socle.racine_mediane(arbre_ctrl, "l'arbre de contrôle")
        presentes = [v for v in voisins if v in {t.name for t in arbre_ctrl.get_terminals()}]
        controle = est_clade(arbre_ctrl, presentes) if len(presentes) >= 2 else None
        L += ["", "-- contrôles",
              f"   clade d'accueil sans la requête : "
              + ("OUI, il existe indépendamment" if controle
                 else ("NON — il a été fabriqué par la présence de la requête"
                       if controle is False else "non testable (moins de 2 voisins présents)"))]
    else:
        L += ["", "-- contrôles",
              "   clade d'accueil sans la requête : NON MESURÉ (arbre de contrôle absent)"]

    recodage = None
    if a.tree_recoded and Path(a.tree_recoded).exists():
        arbre_rec = socle.lit_arbre(a.tree_recoded)
        socle.racine_mediane(arbre_rec, "l'arbre recodé")
        _acc_r, voisins_r = clade_accueil(arbre_rec, a.query, 2)
        dom_r = {}
        for v in voisins_r:
            d = tax.get(v, ("?", "?"))[0]
            dom_r[d] = dom_r.get(d, 0) + 1
        dominant_r = max(dom_r, key=lambda k: dom_r[k]) if dom_r else "?"
        recodage = dominant_r == dominant
        L.append(f"   placement après recodage        : voisinage dominé par {dominant_r} "
                 + ("(INCHANGÉ)" if recodage else "(CHANGÉ — le placement tenait à la "
                                                  "composition, pas à l'ascendance)"))
    else:
        L.append("   placement après recodage        : NON MESURÉ (arbre recodé absent)")

    # --- verdict -------------------------------------------------------------------------------
    manques = []
    if v_cont is None:
        manques.append("le contrôle de contamination d'assemblage (porte 0)")
    if v_comp is None:
        manques.append("le diagnostic de composition et de saturation")
    if v_topo is None:
        manques.append("le test topologique AU")
    if controle is None:
        manques.append("l'arbre de contrôle inféré sans la requête")
    if recodage is None and v_comp not in (None, "HOMOGENE"):
        manques.append("l'arbre recodé, exigé dès que la composition n'est pas homogène")

    if v_cont == "BLOQUE":
        verdict = "CONTAMINATION_PROBABLE"
        lecture = ["La porte 0 a bloqué : le gène n'est pas établi comme appartenant au génome.",
                   "Un contaminant d'assemblage produit exactement le placement lu ci-dessus.",
                   "Tout le reste de ce rapport est sans portée tant que cette porte est fermée."]
    elif v_cont in (None, "NON_CONCLUANT", "SUSPECT") or manques:
        verdict = "AUCUN_VERDICT"
        lecture = ["Aucun verdict n'est prononcé. Manque : " + " ; ".join(manques or
                   ["un verdict de contamination franc"]) + ".",
                   "",
                   "Le placement décrit plus haut est acquis et ne dépend pas de ces manques ;",
                   "ce qui reste à écarter est qu'il soit fabriqué — par un contig étranger, par",
                   "une composition hétérogène, ou par le seul hasard d'un signal épuisé. Une",
                   "version antérieure du skill frère prononçait « OUI » dans cette situation :",
                   "c'était le faux positif que tout le dispositif existe pour empêcher."]
    elif (autre_domaine and prof >= 2 and coherent and controle
          and recodage is not False and v_topo == "TRANSFERT_SOUTENU"):
        verdict = "TRANSFERT_INTER_DOMAINE_SOUTENU"
        lecture = [f"La requête ({dom_requete}) est enfouie sous {prof} feuilles {dominant} d'un",
                   f"groupe taxonomique cohérent ({groupe_dominant}), ce clade existe sans elle,",
                   "le placement survit au recodage, et le test AU rejette la monophylie du",
                   "domaine de la requête. Les quatre mesures convergent : un transfert entre",
                   "domaines du vivant est soutenu.",
                   "",
                   "Ce qui reste hors de portée de ce dispositif : la DATE du transfert, son",
                   "nombre d'occurrences, et l'identification de l'espèce donneuse précise — un",
                   "voisinage cohérent désigne un groupe, jamais une espèce."]
    elif v_topo == "VERTICAL_SOUTENU" or (not autre_domaine and v_topo != "TRANSFERT_SOUTENU"):
        verdict = "ORIGINE_PROPRE_AU_DOMAINE"
        if v_topo == "VERTICAL_SOUTENU":
            # « le placement dans l'autre domaine » disait plus que le test : il ne rejette que
            # les placements PROPOSÉS (en mode local, le clade focal frère de chaque clade
            # donneur d'au moins --min-clade séquences, sur un squelette fixé). AG3, 2026-09-25.
            appui = ["Les données ne soutiennent pas un transfert : le test AU rejette chacun des",
                     "placements proposés de la requête (en mode local : son clade focal frère de",
                     "chaque clade testé) dans l'autre domaine ; ses limites sont dans son rapport."]
        else:
            # Un « ou » ici laissait croire que le test AU avait tranché (AG3, 2026-09-25).
            appui = ["Les données ne soutiennent pas un transfert : la requête se range avec les",
                     f"séquences de son propre domaine ({dom_requete}). Ce verdict repose sur ce SEUL",
                     f"placement : le test AU ({v_topo}) n'exclut pas tout placement dans l'autre",
                     "domaine. C'est l'hypothèse nulle retenue faute de preuve d'un transfert, pas",
                     "une origine démontrée : ne pas l'écrire plus fort que cela."]
        lecture = appui + [
                   "C'est un résultat négatif publiable, du même type que celui d'Alvarez-Venegas",
                   "et al. (2007) sur les gènes bactériens à domaine SET : la présence d'un domaine",
                   "« eucaryote » chez une bactérie n'est pas en soi la trace d'une acquisition."]
    else:
        verdict = "INDECIDABLE"
        lecture = ["Les mesures ne convergent pas. Un nichage sans cohérence taxonomique du",
                   "voisinage, ou qui ne survit pas au recodage, ou que le test AU ne distingue",
                   "pas de l'hypothèse verticale, ne vaut pas démonstration. Détail ci-dessus ;",
                   "élargir le panel — en particulier aux espèces LIBRES et environnementales du",
                   "genre, dont l'absence a produit un faux transfert dans la littérature SET —",
                   "avant de trancher."]

    if sans_tax:
        L += ["", f"ATTENTION : {len(sans_tax)} feuille(s) sans domaine instruit dans --taxonomy, "
                  f"comptées « ? » et", "  jamais versées dans un domaine : "
              + ", ".join(sorted(sans_tax)[:10]),
              "  Les rattacher AVANT de lire une discordance comme un fait."]

    L += ["", "-- VERDICT " + "-" * 67] + lecture + ["", f"VERDICT_INTERDOMAINE: {verdict}"]
    texte = "\n".join(L)
    print(texte)
    if a.out:
        Path(a.out).write_text(texte + "\n", encoding="utf-8")
        print(f"\n[écrit dans {a.out}]", file=sys.stderr)


if __name__ == "__main__":
    main()
