#!/usr/bin/env python3
"""
spdi_to_vcf.py — Pont de format SPDI présence/absence -> VCF, pour les outils
de placement phylogénétique (UShER/matUtils en premier lieu, cf. skill
phylo-placement, piste Bovis_full P10.2).

Réutilise bdd_query.py (list_strains, list_strains_recursive, read_spdi,
load_mask, strain_deletions, load_rd_table, in_ranges) pour ne pas dupliquer
la lecture de bdd/actuelle/. Stdlib pure, aucune dépendance.

Une position SPDI variante = une ligne VCF (CHROM=accession de référence,
POS, REF, ALT). Génotype par souche : encodage HAPLOÏDE à valeur unique
(VCFv4.2 §1.6.2 : un seul allèle pour un échantillon haploïde) — "1" si le
SPDI est présent chez la souche, "0" si absent, "." si la position tombe dans
une délétion RD connue de cette souche (report.json/missing_rd, --rd-table
comme `bdd_query align` ; --no-rd pour désactiver).

⚠ ENCODAGE NON VALIDÉ EMPIRIQUEMENT contre `usher --vcf` au moment de
l'écriture (2026-09-20) : la documentation UShER consultée ne précise pas si
le parseur attend un GT haploïde à valeur unique ("1") ou pseudo-diploïde
("1/1", convention historique de `faToVcf`/UCSC reprise par le pipeline
SARS-CoV-2 pour encoder l'incertitude IUPAC). --gt-style permet de basculer
sans réécrire le script. NE PAS faire confiance à un MAT construit avec cet
outil avant d'avoir testé `usher --vcf` sur le VCF jouet produit par
`--self-test` (quelques souches connues) et vérifié que le placement retombe
sur leur position attendue — vérification avant calcul, pas de présomption.

Limite connue : un site MULTI-ALLÉLIQUE (même POS, ALT différents selon la
souche) est fusionné en une seule ligne VCF avec ALT="a1,a2,..." et génotype
"1"/"2"/... — signalé sur stderr si le compte est non nul. Peu attendu sur des
SNP bactériens clonaux (le modèle BIN+G utilisé pour RAxML-NG présume déjà
chaque position biallélique), mais pas vérifié en amont : auditer si le
compte surprend.

⚠ UShER "ignore actuellement les indels" (doc officielle, 2026-09-20) : les
SPDI dont ref/alt ont une longueur différente (frameshift, insertion/
délétion courte) sont écrits dans le VCF comme n'importe quel autre variant
(le pont ne filtre rien), mais ne compteront probablement pas dans le
placement parcimonieux côté UShER — à confirmer sur le run réel, pas supposé.

Sous-commandes :
    vcf <clade...>       Construit le VCF (fichier ou stdout)
    self-test             Fabrique un jeu jouet (3 souches synthétiques,
                          quelques SPDI) et écrit son VCF dans un répertoire
                          temporaire, pour tester `usher --vcf` sans toucher
                          à la vraie bdd avant d'avoir confiance dans le pont.
"""
import argparse
import os
import sys
import tempfile
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bdd_query as bq


def collect_pairs(bdd, clades, recursive):
    pairs = []
    for c in clades:
        if recursive:
            pairs.extend(bq.list_strains_recursive(bdd, c))
        else:
            pairs.extend((c, s) for s in bq.list_strains(bdd, c))
    return pairs


def build_vcf_rows(bdd, pairs, mask, rd_table, code_rd):
    """Retourne (strains, rows, n_multiallelic, n_indel).

    rows = [(chrom, pos, ref, [alt...], [gt par souche dans l'ordre de strains])]
    triés par position. gt vaut '0' / '<rang allèle>' (1, 2, ...) / '.'.
    """
    strains = [s for _, s in pairs]
    per_strain = {s: set(bq.read_spdi(bdd, c, s)) for c, s in pairs}
    per_del = {
        s: (bq.strain_deletions(bdd, c, s, rd_table) if code_rd else [])
        for c, s in pairs
    }

    by_pos = {}  # (chrom, pos, ref) -> {alt: spdi_original}
    n_indel = 0
    for s in strains:
        for spdi in per_strain[s]:
            parts = spdi.split(":")
            if len(parts) < 4:
                continue
            chrom, pos_s, ref, alt = parts[0], parts[1], parts[2], parts[3]
            try:
                pos = int(pos_s)
            except ValueError:
                continue
            if pos in mask:
                continue
            if len(ref) != len(alt):
                n_indel += 1
            by_pos.setdefault((chrom, pos, ref), {})[alt] = spdi

    # Positions VCF tombant dans une délétion RD, précalculées PAR SOUCHE par bisection sur la
    # liste triée des positions (souches × RD × log P). L'appel direct de bq.in_ranges dans la
    # boucle position × souche est linéaire en RD et coûtait ~10^9 tests pour 1 763 souches
    # (Bovis_full P10.6, 2026-09-20 : > 10 min au lieu de secondes).
    from bisect import bisect_left, bisect_right
    sorted_pos = sorted({pos for (_, pos, _) in by_pos})
    del_pos = {}
    for s in strains:
        hit = set()
        for a, b in per_del[s]:
            lo, hi = bisect_left(sorted_pos, a), bisect_right(sorted_pos, b)
            hit.update(sorted_pos[lo:hi])
        del_pos[s] = hit

    rows = []
    n_multiallelic = 0
    for (chrom, pos, ref), alts in sorted(by_pos.items(), key=lambda kv: kv[0][1]):
        alt_list = sorted(alts)
        if len(alt_list) > 1:
            n_multiallelic += 1
        gts = []
        for s in strains:
            present = per_strain[s]
            allele = None
            for i, a in enumerate(alt_list, start=1):
                if alts[a] in present:
                    allele = i
                    break
            if allele is not None:
                gts.append(str(allele))
            elif pos in del_pos[s]:
                gts.append(".")
            else:
                gts.append("0")
        rows.append((chrom, pos, ref, alt_list, gts))
    return strains, rows, n_multiallelic, n_indel


def gt_field(value, style):
    if style == "haploid":
        return value
    # pseudo-diploïde (convention faToVcf/UCSC) : '.' -> './.', sinon 'v/v'
    return "./." if value == "." else f"{value}/{value}"


def write_vcf(fh, strains, rows, source, gt_style):
    fh.write("##fileformat=VCFv4.2\n")
    fh.write(f"##fileDate={date.today():%Y%m%d}\n")
    fh.write(f"##source={source}\n")
    fh.write(
        '##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype'
        f' ({gt_style})">\n'
    )
    fh.write(
        "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\t"
        + "\t".join(strains)
        + "\n"
    )
    for chrom, pos, ref, alt_list, gts in rows:
        fields = [gt_field(g, gt_style) for g in gts]
        fh.write(
            f"{chrom}\t{pos}\t.\t{ref}\t{','.join(alt_list)}\t.\t.\t.\tGT\t"
            + "\t".join(fields)
            + "\n"
        )


def cmd_vcf(args):
    bdd = bq.find_bdd(args.bdd)
    mask = bq.load_mask(args.mask) if args.mask else set()
    rd_table = bq.load_rd_table(args.rd_table) if args.rd_table else None
    pairs = collect_pairs(bdd, args.clades, args.recursive)
    if not pairs:
        raise SystemExit("aucune souche trouvée pour " + ", ".join(args.clades))
    strains, rows, n_multi, n_indel = build_vcf_rows(
        bdd, pairs, mask, rd_table, not args.no_rd
    )
    out = open(args.out, "w") if args.out else sys.stdout
    try:
        write_vcf(
            out,
            strains,
            rows,
            source=f"spdi_to_vcf.py({','.join(args.clades)})",
            gt_style=args.gt_style,
        )
    finally:
        if args.out:
            out.close()
    msg = f"# {len(strains)} souches, {len(rows)} positions VCF (gt={args.gt_style})"
    if n_multi:
        msg += f", {n_multi} multi-allélique(s) — à auditer"
    if n_indel:
        msg += f", {n_indel} indel(s) (UShER les ignore actuellement)"
    msg += f" -> {args.out or 'stdout'}"
    print(msg, file=sys.stderr)


def cmd_self_test(args):
    """Jeu jouet : 3 souches synthétiques, 5 SPDI, aucune lecture de bdd/.
    Écrit le VCF dans un répertoire temporaire et affiche la commande usher
    à lancer pour valider l'encodage GT avant tout usage sur la vraie bdd."""
    chrom = "NC_000962.3"
    variants = [
        (100, "A", "G"),
        (5000, "C", "T"),
        (5000, "C", "A"),  # multi-allélique volontaire, pour tester ce chemin
        (200000, "GG", "G"),  # indel volontaire
    ]
    strains = ["toy_s1", "toy_s2", "toy_s3"]
    # s1 : porte les 2 premiers ; s2 : porte le 3e (allèle alt du site multi) ;
    # s3 : ne porte rien (référence pure).
    presence = {
        "toy_s1": {(100, "A", "G"), (5000, "C", "T")},
        "toy_s2": {(5000, "C", "A")},
        "toy_s3": {(200000, "GG", "G")},
    }
    by_pos = {}
    for pos, ref, alt in variants:
        by_pos.setdefault((chrom, pos, ref), {})[alt] = f"{chrom}:{pos}:{ref}:{alt}"
    rows = []
    for (c, pos, ref), alts in sorted(by_pos.items(), key=lambda kv: kv[0][1]):
        alt_list = sorted(alts)
        gts = []
        for s in strains:
            allele = None
            for i, a in enumerate(alt_list, start=1):
                if (pos, ref, a) in presence[s]:
                    allele = i
                    break
            gts.append(str(allele) if allele is not None else "0")
        rows.append((c, pos, ref, alt_list, gts))

    tmp_dir = tempfile.mkdtemp(prefix="spdi_to_vcf_selftest_")
    out_path = os.path.join(tmp_dir, "toy.vcf")
    with open(out_path, "w") as fh:
        write_vcf(
            fh, strains, rows, source="spdi_to_vcf.py --self-test", gt_style=args.gt_style
        )
    print(f"VCF jouet écrit : {out_path}", file=sys.stderr)
    print(
        "Pour valider l'encodage GT avant tout usage réel (aucune commande "
        "lancée par ce script) :",
        file=sys.stderr,
    )
    print(
        "  1. construire un Newick jouet à 3 feuilles (toy_s1,toy_s2,toy_s3) "
        "+ un outgroup fictif si usher l'exige au premier import",
        file=sys.stderr,
    )
    print(f"  2. usher --vcf {out_path} --tree <toy.nwk> --output-mat toy.pb", file=sys.stderr)
    print(
        "  3. vérifier l'absence d'erreur de parsing GT, puis matUtils summary "
        "sur toy.pb pour confirmer que les 2 SNP simples et le site "
        "multi-allélique sont bien vus ; si usher rejette --gt-style haploid, "
        "relancer --self-test --gt-style diploid",
        file=sys.stderr,
    )


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--bdd", help="chemin racine bdd/ (défaut : $TBANNOTATOR_BDD ou ../bdd)"
    )
    ap.add_argument(
        "--gt-style",
        dest="gt_style",
        choices=["haploid", "diploid"],
        default="haploid",
        help="encodage du génotype : valeur unique '1' (VCFv4.2 haploïde, "
        "défaut) ou pseudo-diploïde '1/1' (convention faToVcf/UCSC) — "
        "à trancher empiriquement contre `usher --vcf`, cf. --self-test",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("vcf", help="construit le VCF depuis bdd/actuelle/")
    p.add_argument("clades", nargs="+", help="un ou plusieurs clades")
    p.add_argument(
        "--recursive",
        action="store_true",
        help="agréger clade + tout son sous-arbre clade.*",
    )
    p.add_argument("--mask", help="positions à exclure (format bdd_query load_mask)")
    p.add_argument(
        "--rd-table",
        dest="rd_table",
        help="table RD nommés (bespiatykh_canonical_rd.csv)",
    )
    p.add_argument(
        "--no-rd",
        action="store_true",
        help="ne pas coder les délétions RD en génotype manquant",
    )
    p.add_argument("--out", help="fichier VCF de sortie (défaut : stdout)")
    p.set_defaults(func=cmd_vcf)

    p = sub.add_parser(
        "self-test",
        help="VCF jouet (3 souches synthétiques) pour valider l'encodage GT "
        "contre usher avant tout usage réel",
    )
    p.set_defaults(func=cmd_self_test)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
