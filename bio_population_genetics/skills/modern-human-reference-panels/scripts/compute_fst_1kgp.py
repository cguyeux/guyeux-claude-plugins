#!/usr/bin/env python3
"""
compute_fst_1kgp.py — Matrice de Fst inter-populations depuis le 1000 Genomes PUBLIC,
sans télécharger les VCF entiers (streaming distant via bcftools + Fst via vcftools).

Comble le trou entre `modern-human-reference-panels` (métadonnées, PAS les génotypes) et
`coevolution` (test Fst/Mantel, qui ATTEND une matrice) : produit la matrice Fst réelle,
citable (1kGP phase 3), prête à alimenter un test gène-contre-gène de co-divergence
host×pathogen (Mantel partiel host-Fst × pathogen-distance | géo).

Aucune donnée fabriquée. Source = ftp.1000genomes.ebi.ac.uk (phase 3).

Prérequis (tous en apt/conda) : bcftools, vcftools, tabix, curl. Python stdlib seulement.

Exemples
--------
# Fst par paires entre 4 populations ouest-africaines (défaut : chr22:20-32Mb)
python compute_fst_1kgp.py --pops GWD,MSL,YRI,ESN --out fst_wa.csv

# Agréger sur plusieurs régions (estimation plus stable) et étiqueter par PAYS
python compute_fst_1kgp.py --pops GWD,MSL,YRI,ESN \
    --regions 22:20000000-32000000,21:20000000-30000000 \
    --labels GWD=Gambia,MSL=Sierra_Leone,YRI=Nigeria,ESN=Nigeria --out fst_country.csv

Populations africaines 1kGP : GWD (Gambie/Mandinka), MSL (Sierra Leone/Mende),
YRI (Nigéria/Yoruba), ESN (Nigéria/Esan), LWK (Kenya/Luhya), ACB (Barbade), ASW (US SW).
Pour le Sénégal (Mandenka), le Cameroun/Bantou, etc. : étendre avec HGDP/SGDP (mêmes outils,
autres VCF publics ; voir SKILL.md). Ne JAMAIS mélanger des Fst de panels différents dans une
même matrice (valeurs non comparables) : garder une source cohérente.
"""
import argparse, csv, itertools, subprocess, sys, tempfile, urllib.request
from pathlib import Path

PANEL_URL = "https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/release/20130502/integrated_call_samples_v3.20130502.ALL.panel"
VCF_TMPL = ("https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/release/20130502/"
            "ALL.chr{chrom}.phase3_shapeit2_mvncall_integrated_v5b.20130502.genotypes.vcf.gz")

def need(tool):
    if subprocess.run(["bash", "-lc", f"command -v {tool}"], capture_output=True).returncode != 0:
        sys.exit(f"Outil manquant : {tool} (apt install {tool} / conda install -c bioconda {tool})")

def load_panel(workdir):
    p = workdir / "1kg_panel.txt"
    if not p.exists():
        urllib.request.urlretrieve(PANEL_URL, p)
    pop2samples = {}
    with open(p) as f:
        next(f)
        for line in f:
            parts = line.split()
            if len(parts) >= 2:
                pop2samples.setdefault(parts[1], []).append(parts[0])
    return pop2samples

def stream_region(region, samples_file, out_vcf):
    chrom = region.split(":")[0]
    url = VCF_TMPL.format(chrom=chrom)
    cmd = ["bcftools", "view", "-r", region, "-S", str(samples_file), "--force-samples",
           "-v", "snps", "-m2", "-M2", url, "-Oz", "-o", str(out_vcf)]
    subprocess.run(cmd, check=True, stderr=subprocess.DEVNULL)
    subprocess.run(["tabix", "-f", "-p", "vcf", str(out_vcf)], check=True, stderr=subprocess.DEVNULL)

def weir_fst(vcf, popA_file, popB_file, prefix):
    r = subprocess.run(["vcftools", "--gzvcf", str(vcf), "--weir-fst-pop", str(popA_file),
                        "--weir-fst-pop", str(popB_file), "--out", str(prefix)],
                       capture_output=True, text=True)
    for line in (r.stderr + r.stdout).splitlines():
        if "weighted fst" in line.lower():          # vcftools: "Weir and Cockerham weighted Fst estimate: X"
            try:
                return float(line.split(":")[-1].strip())
            except ValueError:
                continue
    return None

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pops", required=True, help="codes populations 1kGP, séparés par des virgules (ex: GWD,MSL,YRI,ESN)")
    ap.add_argument("--regions", default="22:20000000-32000000",
                    help="régions génomiques chrom:start-end, séparées par des virgules (agrégées)")
    ap.add_argument("--labels", default="", help="renommage optionnel POP=Label,... (ex: pays)")
    ap.add_argument("--out", default="fst_matrix.csv", help="CSV de sortie (matrice Fst)")
    ap.add_argument("--workdir", default="", help="répertoire de travail (défaut: temporaire)")
    args = ap.parse_args()
    for t in ("bcftools", "vcftools", "tabix"):
        need(t)
    pops = [p.strip() for p in args.pops.split(",") if p.strip()]
    regions = [r.strip() for r in args.regions.split(",") if r.strip()]
    label = dict(kv.split("=") for kv in args.labels.split(",") if "=" in kv) if args.labels else {}

    workdir = Path(args.workdir) if args.workdir else Path(tempfile.mkdtemp(prefix="fst1kgp_"))
    workdir.mkdir(parents=True, exist_ok=True)
    pop2samples = load_panel(workdir)
    for p in pops:
        if p not in pop2samples:
            sys.exit(f"Population inconnue au 1kGP : {p} (dispo: {sorted(pop2samples)})")
        (workdir / f"{p}.samples").write_text("\n".join(pop2samples[p]) + "\n")
    keep = workdir / "keep.samples"
    keep.write_text("\n".join(s for p in pops for s in pop2samples[p]) + "\n")

    # Fst par paire = moyenne sur les régions (approx. genome-wide stable si assez de SNP)
    pair_vals = {}
    for i, region in enumerate(regions):
        vcf = workdir / f"region{i}.vcf.gz"
        print(f"[stream] {region} ({len(pops)} pops)…", file=sys.stderr)
        stream_region(region, keep, vcf)
        for a, b in itertools.combinations(pops, 2):
            f = weir_fst(vcf, workdir / f"{a}.samples", workdir / f"{b}.samples", workdir / f"{a}_{b}_{i}")
            if f is not None:
                pair_vals.setdefault((a, b), []).append(f)

    fst = {pair: sum(v) / len(v) for pair, v in pair_vals.items()}
    lab = lambda p: label.get(p, p)
    order = pops
    with open(args.out, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow([""] + [lab(p) for p in order])
        for a in order:
            row = [lab(a)]
            for b in order:
                if a == b:
                    row.append("0")
                else:
                    key = (a, b) if (a, b) in fst else (b, a)
                    row.append(f"{fst.get(key, ''):.6f}" if key in fst else "")
            w.writerow(row)
    print(f"[ok] matrice Fst → {args.out}  (régions: {len(regions)}, paires: {len(fst)})", file=sys.stderr)
    for (a, b), v in sorted(fst.items(), key=lambda x: x[1]):
        print(f"  {lab(a):16s} {lab(b):16s} Fst={v:.6f}")

if __name__ == "__main__":
    main()
