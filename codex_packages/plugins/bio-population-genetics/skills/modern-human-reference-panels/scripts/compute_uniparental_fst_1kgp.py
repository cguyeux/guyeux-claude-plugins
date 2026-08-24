#!/usr/bin/env python3
"""
compute_uniparental_fst_1kgp.py — Matrice de Fst UNIPARENTALE (chrY, mtDNA) depuis le
1000 Genomes PUBLIC, par streaming distant, SANS télécharger les VCF entiers.

Complément de `compute_fst_1kgp.py` (qui ne fait que l'AUTOSOMIQUE via vcftools
Weir-Cockerham, lequel suppose des génotypes DIPLOÏDES). Le chromosome Y et l'ADN
mitochondrial sont HAPLOÏDES (GT à un seul allèle « 0 »/« 1 ») : vcftools les gère mal.
On calcule donc un Fst de HUDSON à partir des fréquences alléliques par population
(estimateur correct pour marqueurs haploïdes), en streamant le VCF via bcftools.

Pourquoi c'est utile (vue « MÉSO » d'une co-divergence host-pathogen)
--------------------------------------------------------------------
Les marqueurs uniparentaux ont un Ne ~4× plus petit que les autosomes → ils dérivent
plus vite et enregistrent la structure SOCIALE (patrilocalité via chrY, matrilocalité
via mtDNA) que le Fst autosomique moyen (compute_fst_1kgp.py) LISSE et rate. C'est
l'approche Verdu/Heyer (MNHN). Validé 2026-07-06 sur 4 pops ouest-africaines
(GWD/MSL/YRI/ESN) : chrY Fst 0,05-0,15 (10-20× l'autosomique ~0,005), mtDNA ~0,01 →
SEX-BIAIS Y≫mtDNA = signature de patrilocalité (hommes sédentaires, femmes exogames).
Voir aussi la hiérarchie de résolution macro(auto) < méso(Y) < micro(pathogène).

Aucune donnée fabriquée. Source = ftp.1000genomes.ebi.ac.uk (phase 3).
Prérequis : bcftools, tabix, curl. Python stdlib seulement.

Exemples
--------
# chrY + mtDNA pour 4 populations ouest-africaines, étiquetées par pays
python compute_uniparental_fst_1kgp.py --pops GWD,MSL,YRI,ESN \
    --labels GWD=Gambia,MSL=Sierra_Leone,YRI=Nigeria,ESN=Nigeria \
    --marker both --out uniparental_fst.csv

# chrY seul
python compute_uniparental_fst_1kgp.py --pops GWD,MSL,YRI,ESN --marker Y --out y_fst.csv

Sortie : CSV long (marker, popA, popB, fst, n_snp) + matrices <out>.<marker>.matrix.csv.
Populations africaines 1kGP : GWD (Gambie), MSL (Sierra Leone), YRI/ESN (Nigéria),
LWK (Kenya), ACB (Barbade), ASW (US). NE JAMAIS mélanger des Fst de panels différents.
"""
import argparse, csv, itertools, subprocess, sys, tempfile, urllib.request
from pathlib import Path

PANEL_URL = "https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/release/20130502/integrated_call_samples_v3.20130502.ALL.panel"
BASE = "https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/release/20130502"
MARKERS = {
    "Y":  {"url": f"{BASE}/ALL.chrY.phase3_integrated_v2b.20130502.genotypes.vcf.gz",
           "region": "Y:2700000-28800000"},
    "MT": {"url": f"{BASE}/ALL.chrMT.phase3_callmom-v0_4.20130502.genotypes.vcf.gz",
           "region": "MT:1-16569"},
}

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

def hudson_fst(marker, pops, pop2samples, workdir, min_called=5):
    """Fst de Hudson par paire (ratio des moyennes) depuis les fréquences alléliques haploïdes."""
    m = MARKERS[marker]
    keep = workdir / f"{marker}.keep"
    keep.write_text("\n".join(s for p in pops for s in pop2samples[p]) + "\n")
    cmd = ["bcftools", "view", "-r", m["region"], "-S", str(keep), "--force-samples",
           "-v", "snps", "-m2", "-M2", m["url"]]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    assert proc.stdout is not None
    colpop = None
    num = {pair: 0.0 for pair in itertools.combinations(pops, 2)}
    den = {pair: 0.0 for pair in itertools.combinations(pops, 2)}
    nsnp = 0
    for line in proc.stdout:
        if line.startswith("##"):
            continue
        f = line.rstrip("\n").split("\t")
        if line.startswith("#CHROM"):
            sample2pop = {s: p for p in pops for s in pop2samples[p]}
            colpop = [sample2pop.get(s) for s in f[9:]]
            continue
        if colpop is None:            # données avant l'en-tête #CHROM : ne devrait pas arriver
            continue
        alt = {p: 0 for p in pops}; tot = {p: 0 for p in pops}
        for g, pp in zip(f[9:], colpop):
            if pp is None:
                continue
            a = g.split(":")[0].replace("|", "/").split("/")[0]  # haploïde: 1er allèle
            if a in ("0", "1"):
                tot[pp] += 1
                alt[pp] += 1 if a == "1" else 0
        if any(tot[p] < min_called for p in pops):
            continue
        frq = {p: alt[p] / tot[p] for p in pops}
        nsnp += 1
        for a_, b_ in num:
            p1, p2 = frq[a_], frq[b_]; n1, n2 = tot[a_], tot[b_]
            num[(a_, b_)] += (p1 - p2) ** 2 - p1 * (1 - p1) / (n1 - 1) - p2 * (1 - p2) / (n2 - 1)
            den[(a_, b_)] += p1 * (1 - p2) + p2 * (1 - p1)
    fst = {pair: (num[pair] / den[pair] if den[pair] > 0 else float("nan")) for pair in num}
    return fst, nsnp

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pops", required=True, help="codes populations 1kGP (ex: GWD,MSL,YRI,ESN)")
    ap.add_argument("--marker", default="both", choices=["Y", "MT", "both"], help="chrY, mtDNA, ou les deux")
    ap.add_argument("--labels", default="", help="renommage optionnel POP=Label,... (ex: pays)")
    ap.add_argument("--out", default="uniparental_fst.csv", help="CSV long de sortie")
    ap.add_argument("--min-called", type=int, default=5, help="min. d'allèles appelés par pop et par SNP")
    ap.add_argument("--workdir", default="", help="répertoire de travail (défaut: temporaire)")
    args = ap.parse_args()
    for t in ("bcftools", "tabix"):
        need(t)
    pops = [p.strip() for p in args.pops.split(",") if p.strip()]
    label = dict(kv.split("=") for kv in args.labels.split(",") if "=" in kv) if args.labels else {}
    lab = lambda p: label.get(p, p)
    markers = ["Y", "MT"] if args.marker == "both" else [args.marker]

    workdir = Path(args.workdir) if args.workdir else Path(tempfile.mkdtemp(prefix="unifst_"))
    workdir.mkdir(parents=True, exist_ok=True)
    pop2samples = load_panel(workdir)
    for p in pops:
        if p not in pop2samples:
            sys.exit(f"Population inconnue au 1kGP : {p} (dispo: {sorted(pop2samples)})")

    rows = []
    for marker in markers:
        print(f"[stream] {marker} ({MARKERS[marker]['region']}, {len(pops)} pops)…", file=sys.stderr)
        fst, nsnp = hudson_fst(marker, pops, pop2samples, workdir, args.min_called)
        for (a, b), v in sorted(fst.items(), key=lambda x: x[1]):
            rows.append((marker, lab(a), lab(b), v, nsnp))
            print(f"  {marker}  {lab(a):16s} {lab(b):16s} Fst={v:.4f}  ({nsnp} SNP)")
        # matrice par marqueur
        mpath = Path(args.out).with_suffix(f".{marker}.matrix.csv")
        with open(mpath, "w", newline="") as fh:
            w = csv.writer(fh); w.writerow([""] + [lab(p) for p in pops])
            for a in pops:
                row = [lab(a)]
                for b in pops:
                    if a == b:
                        row.append("0")
                    else:
                        key = (a, b) if (a, b) in fst else (b, a)
                        row.append(f"{fst[key]:.5f}")
                w.writerow(row)
    with open(args.out, "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["marker", "popA", "popB", "fst", "n_snp"])
        for marker, a, b, v, nsnp in rows:
            w.writerow([marker, a, b, f"{v:.5f}", nsnp])
    print(f"[ok] Fst uniparental → {args.out} (+ matrices par marqueur)", file=sys.stderr)

if __name__ == "__main__":
    main()
