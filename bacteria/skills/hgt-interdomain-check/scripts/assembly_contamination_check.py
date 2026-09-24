#!/usr/bin/env python3
"""
Objet: PORTE 0 d'un cas de transfert horizontal inter-domaine. Avant toute phylogénie, écarter
    l'explication la plus banale d'un « gène eucaryote chez une bactérie » : le gène n'est pas
    dans le génome, il est dans l'ASSEMBLAGE — contig d'hôte, de réactif, de co-culture ou de
    barcode voisin. Un contaminant produit exactement la signature qu'on s'apprête à publier.
Entrées: --protein-accession (interroge la base Identical Protein Groups du NCBI et compte les
    assemblages INDÉPENDANTS qui portent la même protéine) ou --presence-tsv (même information
    calculée hors ligne : une ligne par assemblage, colonnes assemblage<TAB>organisme) ;
    --genbank + --locus-tag pour le contexte génomique (GC, position, voisinage) ;
    --experimental-support pour consigner un appui de paillasse.
Sorties: un rapport lisible sur stdout, --out pour le fichier, et une dernière ligne
    machine-lisible `VERDICT_CONTAMINATION: PASSE|SUSPECT|BLOQUE|NON_CONCLUANT` que
    read_interdomain.py exige avant de prononcer le moindre verdict de transfert.
Réutilisable: oui, c'est l'étape 0 du skill hgt-interdomain-check.
Projet: écrit pour environnement/pistes.md AG2 (manque (1) du constat du 2026-09-22).
Date: 2026-09-22.

Le critère décisif n'est pas la phylogénie, c'est la RÉPÉTITION INDÉPENDANTE. Une protéine
portée à l'identique par des centaines d'assemblages produits par des laboratoires, des
plateformes et des années différents n'est pas un artefact d'assemblage : il faudrait que la
même contamination se soit produite partout. À l'inverse, un gène vu dans un seul assemblage,
en bout de contig court, à GC aberrant, est un contaminant jusqu'à preuve du contraire — et
c'est ainsi qu'ont été retirés les transferts massifs annoncés chez les tardigrades en 2015.

Les seuils sont déclarés ici, AVANT de voir les données, et ne doivent pas être ajustés après
coup. Les modifier pour un cas particulier se fait en ligne de commande et se consigne.
"""

import argparse
import statistics
import sys
import urllib.parse
import urllib.request
from pathlib import Path

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

# Seuils déclarés d'avance.
N_ASSEMBLAGES_FORT = 5      # au-delà, la répétition indépendante écarte la contamination
Z_GC_ALERTE = 3.0           # écart de GC au reste des CDS de longueur comparable
Z_COUV_ALERTE = 3.0         # écart de couverture déclarée entre contigs
CONTIG_COURT_PB = 50_000    # un contig plus court est un support fragile
BORD_PB = 5_000             # distance au bord en deçà de laquelle la position est fragile
FRACTION_VOISINS_MUETS = 0.8  # au-delà, voisinage non informatif (que des `hypothetical`)
MOBILITE = ("transposase", "integrase", "recombinase", "phage", "insertion sequence",
            "IS element", "conjugal", "relaxase", "mobile element")


def ipg_table(accession, email=None, api_key=None):
    """Table Identical Protein Groups du NCBI : une ligne par occurrence de la MÊME protéine
    dans un assemblage. C'est la mesure de répétition indépendante, en une requête."""
    params = {"db": "protein", "id": accession, "rettype": "ipg", "retmode": "text"}
    if email:
        params["email"] = email
    if api_key:
        params["api_key"] = api_key
    url = EUTILS + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=120) as r:
        texte = r.read().decode("utf-8", "replace")
    lignes = [l.split("\t") for l in texte.strip().split("\n") if l.strip()]
    if not lignes or not lignes[0][0].startswith("Id"):
        raise SystemExit(f"réponse IPG inattendue pour {accession} :\n{texte[:400]}")
    entete = lignes[0]
    return [dict(zip(entete, row)) for row in lignes[1:] if len(row) >= len(entete) - 2]


def presence_depuis_tsv(chemin):
    lignes = []
    for brut in Path(chemin).read_text(encoding="utf-8").splitlines():
        if not brut.strip() or brut.startswith("#"):
            continue
        champs = brut.split("\t") if "\t" in brut else brut.split(",")
        lignes.append({"Assembly": champs[0].strip(),
                       "Organism": champs[1].strip() if len(champs) > 1 else "",
                       "Strain": champs[2].strip() if len(champs) > 2 else ""})
    return lignes


def gc(seq):
    s = str(seq).upper()
    utiles = sum(s.count(b) for b in "ACGT")
    return (s.count("G") + s.count("C")) / utiles if utiles else float("nan")


def contexte_genbank(chemin, locus_tag, flanc):
    """GC du gène contre la distribution des CDS de longueur comparable, position dans le
    réplicon, et voisinage annoté. Le z-score est calculé sur les CDS de longueur voisine
    (±50 %) parce que le GC d'un gène court varie mécaniquement plus : comparer un gène de
    143 codons à la moyenne de tous les CDS fabrique une anomalie qui n'en est pas une."""
    from Bio import SeqIO

    for rec in SeqIO.parse(chemin, "genbank"):
        cds = [f for f in rec.features if f.type == "CDS"]
        cible = [f for f in cds if locus_tag in f.qualifiers.get("locus_tag", [])]
        if not cible:
            continue
        f = cible[0]
        deb, fin = int(f.location.start), int(f.location.end)
        longueur = fin - deb
        seqs = [(int(c.location.end) - int(c.location.start), gc(c.extract(rec.seq)))
                for c in cds]
        comparables = [g for lg, g in seqs
                       if 0.5 * longueur <= lg <= 1.5 * longueur and g == g]
        gc_gene = gc(f.extract(rec.seq))
        z = float("nan")
        if len(comparables) >= 20:
            mu, sigma = statistics.fmean(comparables), statistics.pstdev(comparables)
            if sigma > 0:
                z = (gc_gene - mu) / sigma
        ordre = sorted(cds, key=lambda c: int(c.location.start))
        i = next(k for k, c in enumerate(ordre) if c is f)
        voisins = ordre[max(0, i - flanc):i] + ordre[i + 1:i + 1 + flanc]
        produits = [v.qualifiers.get("product", ["?"])[0] for v in voisins]
        muets = sum(1 for p in produits if "hypothetical" in p.lower() or p == "?")
        mobiles = [p for p in produits if any(m.lower() in p.lower() for m in MOBILITE)]
        return {
            "replicon": rec.id, "taille_replicon": len(rec.seq), "n_cds": len(cds),
            "debut": deb, "fin": fin, "longueur": longueur, "gc_gene": gc_gene,
            "gc_replicon": gc(rec.seq), "z_gc": z, "n_comparables": len(comparables),
            "bord": min(deb, len(rec.seq) - fin), "produits_voisins": produits,
            "fraction_muets": muets / len(produits) if produits else float("nan"),
            "mobiles": mobiles,
        }
    raise SystemExit(f"locus_tag {locus_tag} introuvable dans {chemin}")


def ligne(etat, titre, detail):
    return f"  [{etat:^11}] {titre:<38} {detail}"


def main():
    p = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[1])
    p.add_argument("--protein-accession", help="accession protéique NCBI (ex. AKP24757.1)")
    p.add_argument("--presence-tsv", help="alternative hors ligne : assemblage<TAB>organisme")
    p.add_argument("--genbank", help="GenBank du génome de référence portant le gène")
    p.add_argument("--locus-tag", help="locus_tag du gène dans ce GenBank")
    p.add_argument("--flank", type=int, default=5, help="CDS de part et d'autre (défaut 5)")
    p.add_argument("--coverage-tsv", help="TSV contig<TAB>couverture, si l'assembleur la donne")
    p.add_argument("--contig", help="nom du contig portant le gène, pour --coverage-tsv")
    p.add_argument("--experimental-support", default="",
                   help="appui de paillasse (mutagenèse, RT-PCR, protéomique) ; consigné, "
                        "jamais suffisant à lui seul")
    p.add_argument("--n-assemblages-fort", type=int, default=N_ASSEMBLAGES_FORT)
    p.add_argument("--email")
    p.add_argument("--api-key")
    p.add_argument("--out")
    a = p.parse_args()

    if not a.protein_accession and not a.presence_tsv:
        raise SystemExit("il faut --protein-accession ou --presence-tsv : sans mesure de "
                         "répétition indépendante, cette porte ne peut rien conclure.")

    lignes = ["CONTAMINATION D'ASSEMBLAGE — porte 0 du test inter-domaine",
              "=" * 78, ""]
    alertes_fortes, alertes_faibles, non_mesures, mesures = [], [], [], {}

    # --- critère A : répétition indépendante ------------------------------------------------
    unique = False
    occurrences = (ipg_table(a.protein_accession, a.email, a.api_key) if a.protein_accession
                   else presence_depuis_tsv(a.presence_tsv))
    assemblages = {o.get("Assembly", "").strip() for o in occurrences}
    assemblages.discard("")
    organismes = {o.get("Organism", "").strip() for o in occurrences if o.get("Organism")}
    genres = {org.split()[0] for org in organismes if org}
    mesures["n_assemblages"] = len(assemblages)
    if len(assemblages) >= a.n_assemblages_fort:
        etat, detail = "PASSE", (f"{len(assemblages)} assemblages indépendants, "
                                 f"{len(organismes)} organismes, {len(genres)} genres")
    elif len(assemblages) <= 1:
        etat = "ALERTE FORTE"
        detail = "vu dans un seul assemblage : indiscernable d'un contaminant"
        unique = True
    else:
        etat = "ALERTE"
        detail = f"seulement {len(assemblages)} assemblages : répétition trop faible"
        alertes_faibles.append("répétition indépendante faible")
    lignes.append(ligne(etat, "répétition indépendante", detail))
    if genres:
        lignes.append(f"{'':15}genres porteurs : " + ", ".join(sorted(genres)[:8])
                      + (" ..." if len(genres) > 8 else ""))

    # --- critères B, C, D : contexte génomique ----------------------------------------------
    ctx = None
    if a.genbank and a.locus_tag:
        ctx = contexte_genbank(a.genbank, a.locus_tag, a.flank)
        mesures.update(ctx)
        z = ctx["z_gc"]
        if z != z:
            non_mesures.append("GC normalisé (trop peu de CDS comparables)")
            lignes.append(ligne("NON MESURÉ", "GC du gène",
                                f"{ctx['gc_gene']:.1%} contre {ctx['gc_replicon']:.1%} pour le "
                                f"réplicon ; trop peu de CDS de longueur comparable pour un z"))
        elif abs(z) >= Z_GC_ALERTE:
            alertes_fortes.append(f"GC atypique (z = {z:+.1f})")
            lignes.append(ligne("ALERTE FORTE", "GC du gène",
                                f"{ctx['gc_gene']:.1%} contre {ctx['gc_replicon']:.1%} "
                                f"(z = {z:+.1f} sur {ctx['n_comparables']} CDS comparables)"))
        else:
            lignes.append(ligne("PASSE", "GC du gène",
                                f"{ctx['gc_gene']:.1%} contre {ctx['gc_replicon']:.1%} "
                                f"(z = {z:+.1f} sur {ctx['n_comparables']} CDS comparables)"))

        court = ctx["taille_replicon"] < CONTIG_COURT_PB
        au_bord = ctx["bord"] < BORD_PB
        if court and au_bord:
            alertes_fortes.append("contig court et gène au bord")
            etat, detail = "ALERTE FORTE", (f"contig de {ctx['taille_replicon']} pb, gène à "
                                            f"{ctx['bord']} pb du bord")
        elif court or au_bord:
            alertes_faibles.append("support fragile (contig court OU gène au bord)")
            etat, detail = "ALERTE", (f"réplicon de {ctx['taille_replicon']} pb, gène à "
                                      f"{ctx['bord']} pb du bord")
        else:
            etat, detail = "PASSE", (f"réplicon de {ctx['taille_replicon']} pb, gène à "
                                     f"{ctx['bord']} pb du bord, {ctx['n_cds']} CDS")
        lignes.append(ligne(etat, "position dans l'assemblage", detail))

        fm = ctx["fraction_muets"]
        if fm >= FRACTION_VOISINS_MUETS:
            alertes_faibles.append("voisinage non informatif")
            lignes.append(ligne("ALERTE", "voisinage génique",
                                f"{fm:.0%} des {len(ctx['produits_voisins'])} voisins sont "
                                f"`hypothetical` : le voisinage ne témoigne de rien"))
        else:
            lignes.append(ligne("PASSE", "voisinage génique",
                                f"{1 - fm:.0%} des {len(ctx['produits_voisins'])} voisins "
                                f"portent une fonction annotée"))
        lignes.append(f"{'':15}voisins : " + " | ".join(ctx["produits_voisins"][:6]))
        if ctx["mobiles"]:
            lignes.append(ligne("À LIRE", "éléments de mobilité au voisinage",
                                ", ".join(sorted(set(ctx["mobiles"]))[:4])))
            lignes.append(f"{'':15}un îlot mobile n'est PAS une contamination, mais il change "
                          f"la lecture : le gène peut être récent sans être étranger au taxon.")
    else:
        non_mesures.append("GC, position dans l'assemblage et voisinage génique")
        lignes.append(ligne("NON MESURÉ", "contexte génomique",
                            "ni --genbank ni --locus-tag : GC, position et voisinage non testés"))

    # --- critère E : couverture --------------------------------------------------------------
    if a.coverage_tsv and a.contig:
        couv = {}
        for brut in Path(a.coverage_tsv).read_text(encoding="utf-8").splitlines():
            if brut.strip() and not brut.startswith("#"):
                c, v = brut.split("\t")[:2]
                couv[c.strip()] = float(v)
        if a.contig in couv and len(couv) >= 10:
            vals = list(couv.values())
            mu, sigma = statistics.fmean(vals), statistics.pstdev(vals)
            z = (couv[a.contig] - mu) / sigma if sigma > 0 else 0.0
            if abs(z) >= Z_COUV_ALERTE:
                alertes_fortes.append(f"couverture atypique (z = {z:+.1f})")
                lignes.append(ligne("ALERTE FORTE", "couverture du contig",
                                    f"{couv[a.contig]:.1f}x, z = {z:+.1f} sur {len(vals)} contigs"))
            else:
                lignes.append(ligne("PASSE", "couverture du contig",
                                    f"{couv[a.contig]:.1f}x, z = {z:+.1f} sur {len(vals)} contigs"))
        else:
            non_mesures.append("couverture du contig")
            lignes.append(ligne("NON MESURÉ", "couverture du contig",
                                "contig absent du TSV ou moins de 10 contigs"))
    else:
        non_mesures.append("couverture du contig")
        lignes.append(ligne("NON MESURÉ", "couverture du contig",
                            "assemblage fermé, ou couverture non fournie"))

    # --- critère F : appui expérimental -------------------------------------------------------
    if a.experimental_support:
        lignes.append(ligne("CONSIGNÉ", "appui expérimental", a.experimental_support))
        lignes.append(f"{'':15}un gène sorti essentiel en mutagenèse n'est pas un contaminant, "
                      f"mais cet appui NE REMPLACE PAS la répétition indépendante.")

    # --- verdict -------------------------------------------------------------------------------
    if not assemblages:
        verdict = "NON_CONCLUANT"
        lecture = ["Aucune occurrence lue : la répétition indépendante n'est pas mesurée, donc",
                   "cette porte ne peut ni ouvrir ni fermer. Rien ne doit être inféré ensuite."]
    elif len(assemblages) >= a.n_assemblages_fort and not alertes_fortes:
        verdict = "PASSE"
        lecture = [f"La même protéine est portée par {len(assemblages)} assemblages indépendants"
                   + (f" de {len(genres)} genre(s)" if genres else "") + ". L'hypothèse",
                   "« contig étranger dans un assemblage » est écartée par la répétition seule :",
                   "il faudrait que la même contamination se soit produite dans tous. Le gène",
                   "appartient au génome ; le SENS du transfert reste entier et demande la suite."]
        if non_mesures:
            lecture += ["",
                        "Non mesuré ici, et donc NON invoqué dans ce verdict : "
                        + ", ".join(non_mesures) + ".",
                        "Le verdict tient sur le seul critère A, qui suffit quand il est franc ;",
                        "il ne signifie pas que les autres critères ont été passés avec succès."]
    elif unique and alertes_fortes:
        verdict = "BLOQUE"
        lecture = ["Un seul assemblage porteur ET une anomalie indépendante (" 
                   + " ; ".join(alertes_fortes) + ") : c'est la",
                   "signature d'une contamination d'assemblage, pas d'un transfert. Aucune",
                   "phylogénie ne doit être engagée avant d'avoir cherché le gène dans des",
                   "assemblages indépendants de l'espèce, ou re-séquencé."]
    elif unique:
        verdict = "SUSPECT"
        lecture = ["Le gène n'est vu que dans un assemblage. Aucune autre anomalie n'a été",
                   "relevée, donc rien ne prouve la contamination — mais rien ne l'écarte non",
                   "plus, et c'est le point exact où les transferts massifs annoncés chez les",
                   "tardigrades en 2015 se sont effondrés. Chercher la protéine dans les autres",
                   "assemblages de l'espèce (ou du genre) AVANT toute phylogénie ; si l'espèce",
                   "n'a qu'un génome, le dire dans le manuscrit comme une limite, pas comme un",
                   "détail."]
    else:
        verdict = "SUSPECT"
        lecture = ["La porte ne se ferme pas mais ne s'ouvre pas franchement. Détail des",
                   "réserves ci-dessus ; les lever coûte moins cher qu'un arbre et évite de",
                   "publier un contaminant."]

    bilan = ["", "-- VERDICT " + "-" * 67]
    if alertes_fortes:
        bilan.append("alertes fortes : " + " ; ".join(alertes_fortes))
    if alertes_faibles:
        bilan.append("réserves      : " + " ; ".join(alertes_faibles))
    bilan += [""] + lecture + ["", f"VERDICT_CONTAMINATION: {verdict}"]

    texte = "\n".join(lignes + bilan)
    print(texte)
    if a.out:
        Path(a.out).write_text(texte + "\n", encoding="utf-8")
        print(f"\n[écrit dans {a.out}]", file=sys.stderr)


if __name__ == "__main__":
    main()
