#!/usr/bin/env python3
"""
Objet: test MK a DEUX GROUPES DE GENOTYPE (pas lignee-vs-reste) sur une fenetre de gene H37Rv,
    depuis les spdi.txt de production deja sur disque (aucun calling). Contrairement a
    mk_test_and_ascertainment.py / mk_per_gene.py (design lignee-exclusive-vs-reste, divergence
    fixee garantie par construction), ce script ne suppose PAS qu'une classe de divergence
    fixee existe entre les deux groupes : il la detecte, et si elle est absente (Dn=Ds=0, cas
    reel rencontre sur Rv1557/mmpL6 551K vs 551N, cf. tuberculosis.md 2026-08-26), bascule
    explicitement sur une comparaison de polymorphisme SITE-BASED (jamais ponderee par
    occurrences-souches, pour eviter la pseudo-replication phylogenetique : un site fixe dans
    un seul sous-clade d'un groupe ne doit pas etre compte une fois par souche porteuse).
Entrées: TSV sra<TAB>groupe (exactement 2 groupes), racine bdd/actuelle, fenetre de gene
    (positions H37Rv 1-based inclusives ou --gff3 --gene pour resolution auto), GFF3+GenBank
    H37Rv pour l'annotation locale (delegue a spdi-annotation/scripts/annotate_spdis.py).
Sorties: TSV spdi/n_groupe1/n_groupe2/freq_groupe1/freq_groupe2/effect, plus un resume texte
    (nombre de sites fixes detectes, table MK classique si applicable, table site-based sinon).
Réutilisable: oui -- generalise depuis Rv1557/analyses/phase2_p27_mk_cterm.py (2026-08-26),
    pour tout projet MTBC comparant deux groupes de souches deja genotypes (phenotype R/S,
    presence/absence d'un marqueur, etc.) sur un gene ou une fenetre donnee.
Projet: mk-ascertainment (skill partage bio_pathogens)
Date: 2026-08-26
"""
import argparse
import csv
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

SKILLS_ROOT = Path(__file__).resolve().parents[2]  # .../bio_pathogens/skills
ANNOTATE_SCRIPT = SKILLS_ROOT / "spdi-annotation" / "scripts" / "annotate_spdis.py"

FIXED_THRESHOLD = 0.9   # frequence minimale dans un groupe pour candidater "fixe"
ABSENT_THRESHOLD = 0.1  # frequence maximale dans l'autre groupe pour valider la fixation


def find_spdi_index(bdd_root):
    """SRA -> chemin spdi.txt (NC_000962.3 uniquement -- jamais les references alternatives,
    cf. tuberculosis.md 2026-08-25 ; le plus court en cas de doublon de repertoire)."""
    idx = {}
    proc = subprocess.run(
        ["find", str(bdd_root), "-mindepth", "2", "-maxdepth", "20", "-type", "f",
         "-name", "spdi.txt"],
        capture_output=True, text=True, check=True,
    )
    for line in proc.stdout.splitlines():
        if not line.endswith("/NC_000962.3/spdi.txt"):
            continue
        sra = line.split("/")[-3]
        idx.setdefault(sra, []).append(line)
    return {sra: sorted(paths, key=lambda p: (len(p), p))[0] for sra, paths in idx.items()}


def resolve_gene_window(gff3, gene):
    for line in open(gff3):
        if line.startswith("#"):
            continue
        f = line.rstrip("\n").split("\t")
        if len(f) < 9 or f[2] != "gene":
            continue
        if f"gene={gene};" in f[8] or f[8].endswith(f"gene={gene}") or f";gene={gene};" in f[8]:
            return int(f[3]), int(f[4])
    raise SystemExit(f"Gene {gene} introuvable dans {gff3}")


def main():
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n")[0],
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("groups_tsv", help="sra<TAB>groupe, exactement 2 groupes distincts")
    ap.add_argument("--bdd-root", required=True, help="racine bdd/actuelle")
    ap.add_argument("--start", type=int, help="debut fenetre H37Rv (1-based inclusif)")
    ap.add_argument("--end", type=int, help="fin fenetre H37Rv (1-based inclusif)")
    ap.add_argument("--gff3", help="GFF3 H37Rv (pour --gene ou l'annotation)")
    ap.add_argument("--genbank", help="GenBank H37Rv (pour l'annotation)")
    ap.add_argument("--gene", help="nom de gene a resoudre via --gff3 (alternative a --start/--end)")
    ap.add_argument("-o", "--output", required=True, help="TSV de sortie (variants + frequences)")
    args = ap.parse_args()

    if args.gene:
        if not args.gff3:
            raise SystemExit("--gene requiert --gff3")
        start, end = resolve_gene_window(args.gff3, args.gene)
    elif args.start and args.end:
        start, end = args.start, args.end
    else:
        raise SystemExit("Fournir --start/--end ou --gene avec --gff3")

    groups = {}
    for line in open(args.groups_tsv):
        sra, g = line.strip().split("\t")
        groups[sra] = g
    labels = sorted(set(groups.values()))
    if len(labels) != 2:
        raise SystemExit(f"Attendu exactement 2 groupes, trouve {len(labels)} : {labels}")
    g1, g2 = labels
    n1 = sum(1 for v in groups.values() if v == g1)
    n2 = sum(1 for v in groups.values() if v == g2)
    print(f"Groupes : {g1} (n={n1}) vs {g2} (n={n2})", file=sys.stderr)

    idx = find_spdi_index(args.bdd_root)
    missing = [s for s in groups if s not in idx]
    if missing:
        print(f"ATTENTION : {len(missing)} souches sans spdi.txt trouve (ex: {missing[:5]})",
              file=sys.stderr)

    calls = defaultdict(lambda: defaultdict(set))
    for sra, g in groups.items():
        path = idx.get(sra)
        if not path:
            continue
        for l in open(path):
            l = l.strip()
            if not l:
                continue
            _, pos, _, _ = l.split(":")
            pos = int(pos)
            if start <= pos <= end:
                calls[l][g].add(sra)

    variants = sorted(calls.items(), key=lambda x: int(x[0].split(":")[1]))
    if not variants:
        print("Aucun variant trouve dans la fenetre -- rien a tester.", file=sys.stderr)
        return

    effect = {}
    if args.gff3 and args.genbank:
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as tmp_in:
            tmp_in.write("\n".join(v[0] for v in variants) + "\n")
            tmp_in_path = tmp_in.name
        tmp_out_path = tmp_in_path + ".annotated.csv"
        subprocess.run(
            [sys.executable, str(ANNOTATE_SCRIPT), tmp_in_path,
             "--gff3", args.gff3, "--genbank", args.genbank,
             "--skip-tbannotator", "-o", tmp_out_path],
            check=True,
        )
        with open(tmp_out_path) as f:
            for row in csv.DictReader(f):
                effect[row["SPDI"]] = row["Effect"]
        Path(tmp_in_path).unlink(missing_ok=True)
        Path(tmp_out_path).unlink(missing_ok=True)
    else:
        print("(pas de --gff3/--genbank : colonne effect laissee vide)", file=sys.stderr)

    with open(args.output, "w") as out:
        out.write(f"spdi\tn_{g1}\tn_{g2}\tfreq_{g1}\tfreq_{g2}\teffect\n")
        for spdi, d in variants:
            c1, c2 = len(d[g1]), len(d[g2])
            out.write(f"{spdi}\t{c1}\t{c2}\t{c1 / n1:.4f}\t{c2 / n2:.4f}\t"
                      f"{effect.get(spdi, '?')}\n")

    # --- detection de divergence fixee, et bascule site-based si absente ---
    fixed = []
    for spdi, d in variants:
        f1, f2 = len(d[g1]) / n1, len(d[g2]) / n2
        if (f1 >= FIXED_THRESHOLD and f2 <= ABSENT_THRESHOLD) or \
           (f2 >= FIXED_THRESHOLD and f1 <= ABSENT_THRESHOLD):
            fixed.append(spdi)

    print(f"\nÉcrit {args.output} ({len(variants)} variants).", file=sys.stderr)
    if fixed:
        print(f"{len(fixed)} site(s) candidat(s) a une divergence FIXEE (seuils "
              f">= {FIXED_THRESHOLD} vs <= {ABSENT_THRESHOLD}) : {fixed}", file=sys.stderr)
        print("=> le test MK classique (Dn/Ds fixe vs Pn/Ps polymorphe) peut s'appliquer : "
              "isoler ces sites pour Dn/Ds, le reste (sites segregants dans au moins un "
              "groupe) pour Pn/Ps, puis un test de Fisher (cf. mk_test_and_ascertainment.py).",
              file=sys.stderr)
    else:
        print("AUCUNE divergence fixee detectee (Dn=Ds=0) -- le test MK classique est "
              "INAPPLICABLE tel quel (cf. tuberculosis.md 2026-08-26, cas Rv1557/mmpL6).",
              file=sys.stderr)
        print("Reformulation recommandee : comparaison de polymorphisme SITE-BASED (compter "
              "chaque site UNE FOIS par groupe ou il segrege, jamais pondere par occurrences-"
              "souches) -- calcul non fait automatiquement ici (necessite l'annotation NS/S "
              "en colonne 'effect' du fichier de sortie) :", file=sys.stderr)
        print("  from scipy.stats import fisher_exact", file=sys.stderr)
        print("  # Pn_g1 = sites missense avec n_g1>0 ; Ps_g1 = sites synonymous avec n_g1>0 "
              "(idem g2)", file=sys.stderr)
        print("  fisher_exact([[Pn_g1, Ps_g1], [Pn_g2, Ps_g2]])", file=sys.stderr)
        print("ATTENTION : si les souches viennent de sous-clades tres inegalement "
              "representes (ex. un outgroup divergent comme Canettii), verifier la "
              "distribution par sous-clade des sites a frequence intermediaire avant "
              "d'interpreter -- un site peut etre 100% confine a un seul sous-clade "
              "(structure phylogenetique interne), pas un polymorphisme homogene du groupe.",
              file=sys.stderr)


if __name__ == "__main__":
    main()
