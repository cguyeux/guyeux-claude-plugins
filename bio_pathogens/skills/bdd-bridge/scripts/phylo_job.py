#!/usr/bin/env python3
"""
phylo_job.py — Pont d'inférence phylogénétique pour un clade MTBC.

Construit un alignement SNP binaire (0/1 = absence/présence du variant) à partir des
spdi.txt de bdd/actuelle/<clade>/, puis lance RAxML-NG (modèle BIN+G) — soit en LOCAL,
soit en préparant un PAQUET de soumission pour compute distant (SLURM/autre).

Appelable à l'identique depuis Claude Code et Claude Science. Stdlib pure.

Sous-commandes :
    align  <clade>              -> écrit <out>/<clade>.phy (+ .positions.txt)
    run    <clade>              -> align puis exécute raxml-ng localement
    submit <clade>              -> align puis écrit un paquet distant (align + submit.sh + params.json)

Réutilise la lecture BDD de bdd_query.py (même dossier).
"""
import os, sys, json, argparse, subprocess, shutil, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bdd_query as bq  # find_bdd, build_matrix, list_strains

def default_raxml(bdd=None):
    """Cherche le binaire raxml-ng : $RAXML, puis investigate_phylo/ relatif à
    l'outil OU à la BDD résolue (le dépôt mtbc contient investigate_phylo/ et bdd/),
    puis le PATH."""
    env = os.environ.get("RAXML")
    if env and os.path.isfile(env):
        return os.path.abspath(env)
    here = os.path.dirname(os.path.abspath(__file__))
    roots = [here]
    # ancrer sur la BDD réellement utilisée : dépôt = parent de bdd/
    if bdd:
        roots.append(os.path.dirname(os.path.abspath(bdd)))
    for root in roots:
        for up in range(6):
            cand = os.path.join(root, *([".."]*up), "investigate_phylo", "raxml-ng")
            if os.path.isfile(cand):
                return os.path.abspath(cand)
    return shutil.which("raxml-ng")

def write_alignment(bdd, clade, outdir, min_frac, subsample=0, seed=42):
    """Écrit un PHYLIP relaxé binaire. Colonnes = positions SPDI variables (min_frac..1).
    subsample>0 : ne garde que N souches (tirage reproductible par seed) — utile pour
    les pools géants (L2.2.1 ~35k, L3 ~8.7k) trop lourds pour un arbre brut (pistes P4.28)."""
    strains, cols, per_strain, freq, n = bq.build_matrix(bdd, clade, min_frac)
    subsampled = False
    if subsample and 0 < subsample < len(strains):
        import random
        rng = random.Random(seed)
        keep = set(rng.sample(strains, subsample))
        strains = [s for s in strains if s in keep]
        # recalcule la fréquence sur le sous-échantillon
        freq = bq.Counter()
        for s in strains:
            freq.update(per_strain[s])
        n = len(strains)
        subsampled = True
    # Colonnes INFORMATIVES : ni toujours 0 ni toujours 1 (les fixées n'aident pas RAxML).
    informative = [p for p in cols if 0 < freq[p] < n]
    os.makedirs(outdir, exist_ok=True)
    phy = os.path.join(outdir, f"{clade.replace('/','_')}.phy")
    with open(phy, "w") as f:
        f.write(f"{n} {len(informative)}\n")
        for s in strains:
            seq = "".join("1" if p in per_strain[s] else "0" for p in informative)
            f.write(f"{s}  {seq}\n")
    pos = os.path.join(outdir, f"{clade.replace('/','_')}.positions.txt")
    with open(pos, "w") as f:
        f.write("\n".join(informative))
    meta = {"clade": clade, "n_strains": n, "n_sites_total": len(cols),
            "n_sites_informative": len(informative), "min_frac": min_frac,
            "subsampled": subsampled, "subsample_n": subsample if subsampled else None,
            "alignment": phy, "positions": pos, "model": "BIN+G"}
    return meta

def cmd_detect_raxml(bdd, args):
    rax = args.raxml or default_raxml(bdd)
    return {"raxml": rax, "found": bool(rax and os.path.isfile(rax)),
            "source": "explicit --raxml" if args.raxml else
                      ("$RAXML" if os.environ.get("RAXML") else "investigate_phylo/ ou PATH")}

def cmd_align(bdd, args):
    return write_alignment(bdd, args.clade, args.out, args.min_frac, args.subsample, args.seed)

def cmd_run(bdd, args):
    meta = write_alignment(bdd, args.clade, args.out, args.min_frac, args.subsample, args.seed)
    rax = args.raxml or default_raxml(bdd)
    if not rax or not os.path.isfile(rax):
        raise SystemExit("raxml-ng introuvable (utilisez --raxml <chemin>)")
    prefix = os.path.join(args.out, args.clade.replace('/','_'))
    cmd = [rax, "--all" if args.all else "--search",
           "--msa", meta["alignment"], "--model", "BIN+G",
           "--prefix", prefix, "--threads", str(args.threads), "--seed", str(args.seed)]
    if args.all:
        cmd += ["--bs-trees", str(args.bs)]
    t0 = time.time()
    proc = subprocess.run(cmd, capture_output=True, text=True)
    meta.update({"raxml": rax, "cmd": " ".join(cmd), "returncode": proc.returncode,
                 "seconds": round(time.time()-t0, 1),
                 "best_tree": prefix + ".raxml.bestTree" if proc.returncode == 0 else None,
                 "stdout_tail": proc.stdout[-1500:], "stderr_tail": proc.stderr[-800:]})
    return meta

def cmd_submit(bdd, args):
    """Paquet portable : alignement + submit.sh + params.json, prêt à rsync/sbatch."""
    meta = write_alignment(bdd, args.clade, args.out, args.min_frac, args.subsample, args.seed)
    prefix = args.clade.replace('/','_')
    submit = os.path.join(args.out, "submit.sh")
    with open(submit, "w") as f:
        f.write(f"""#!/bin/bash
#SBATCH --job-name=raxml_{prefix}
#SBATCH --cpus-per-task={args.threads}
#SBATCH --time=24:00:00
# Paquet phylo autoportant — placer raxml-ng dans le PATH ou éditer $RAXML
set -euo pipefail
RAXML=${{RAXML:-raxml-ng}}
"$RAXML" --all --msa {prefix}.phy --model BIN+G \\
    --prefix {prefix} --threads {args.threads} --seed {args.seed} --bs-trees {args.bs}
""")
    os.chmod(submit, 0o755)
    json.dump(meta, open(os.path.join(args.out, "params.json"), "w"), indent=2)
    meta["submit_script"] = submit
    meta["note"] = "Paquet prêt : rsync le dossier vers le cluster puis `sbatch submit.sh`."
    return meta

def main():
    ap = argparse.ArgumentParser(description="Pont phylo (RAxML-NG BIN+G) pour un clade MTBC")
    ap.add_argument("--bdd"); ap.add_argument("--out", default="phylo_out")
    ap.add_argument("--min-frac", type=float, default=0.0, dest="min_frac",
                    help="fréquence min d'un variant pour entrer dans l'alignement")
    ap.add_argument("--raxml", help="chemin du binaire raxml-ng")
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--bs", type=int, default=100, help="nb de bootstraps (mode --all)")
    ap.add_argument("--all", action="store_true", help="ML + bootstrap (sinon search seul)")
    ap.add_argument("--subsample", type=int, default=0,
                    help="ne garder que N souches (tirage reproductible) — pools géants")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("detect-raxml")
    for c in ("align", "run", "submit"):
        p = sub.add_parser(c); p.add_argument("clade")
    args = ap.parse_args()

    bdd = bq.find_bdd(args.bdd)
    if args.cmd != "detect-raxml" and not os.path.isdir(bq.actuelle(bdd)):
        raise SystemExit(f"bdd/actuelle introuvable sous : {bdd}")
    fn = {"detect-raxml": cmd_detect_raxml, "align": cmd_align,
          "run": cmd_run, "submit": cmd_submit}[args.cmd]
    print(json.dumps(fn(bdd, args), ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
