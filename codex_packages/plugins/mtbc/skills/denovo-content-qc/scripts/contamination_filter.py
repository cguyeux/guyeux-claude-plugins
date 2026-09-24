#!/usr/bin/env python3
"""
contamination_filter.py — tri des contigs "îlots" absents de H37Rv.

CE QUE CE FILTRE PEUT ET NE PEUT PAS DIRE (lire avant d'interpréter)
-------------------------------------------------------------------
On assemble de novo les reads NON mappés sur H37Rv, puis on demande, pour chaque contig :
est-ce un vrai module génomique de L8, ou un CONTAMINANT (ADN étranger dans la run) ?

Le seul génome L8 FERMÉ disponible est CP048071.1 (souche RW-TB008). ATTENTION : une lignée
bactérienne a un PANGÉNOME = génome cœur (partagé) + génome ACCESSOIRE variable d'une souche à
l'autre. Donc :
  - PRÉSENT dans CP048071.1  => SUFFISANT pour conclure "vrai contenu L8" (cœur ou propre à RW-TB008).
  - ABSENT de CP048071.1     => N'EST PAS suffisant pour conclure "contaminant" : ce peut être un
                                élément ACCESSOIRE authentique présent chez une AUTRE souche L8
                                (ex. B2 7505) mais pas chez RW-TB008. L'absence flague pour ARBITRAGE.

Discriminants pour trancher un contig absent du génome fermé :
  (1) présence dans >=2 souches L8 (assemblages) -> candidat ACCESSOIRE de pangénome (probablement réel) ;
      présent dans 1 seule souche -> "singleton" (contaminant OU élément mobile privé) ;
  (2) nature taxonomique : hit sur un panel mycobactérien (M. bovis, M. leprae) -> mycobactérien
      (accessoire possible) ; aucun hit + domaine de plasmide/phage + GC hors ~65 % -> plutôt étranger ;
  (3) couverture cohérente avec la souche, et (hors de ce script) ID d'espèce par BLAST nt / skani.

Ce script fournit (1) et (2) et écrit un TSV ; la décision finale reste humaine, éclairée par
l'ID d'espèce (que ce script ne fait pas : BLAST nt distant / skani à lancer sur les singletons).

Sortie : résultats/contamination_filter.tsv
Dépend de blastn/makeblastdb + data/ref/CP048071_db (génome L8 fermé). Panel mycobactérien
optionnel : ../investigate_phylo/resources/{LT708304.1,NC_002677.1}.fasta (M. bovis, M. leprae).
"""

import os
import re
import glob
import subprocess
import tempfile


def _project_root(start):
    d = os.path.dirname(os.path.abspath(start))
    while d != os.path.dirname(d):
        if os.path.exists(os.path.join(d, "cahier_de_labo.md")):
            return d
        d = os.path.dirname(d)
    raise RuntimeError("Racine projet (cahier_de_labo.md) introuvable")


ROOT = _project_root(__file__)
REF_DB = os.path.join(ROOT, "data", "ref", "CP048071_db")          # génome L8 fermé (BLAST db)
ASSEMBLIES = sorted(glob.glob(os.path.join(ROOT, "résultats", "assemblies",
                                            "spades_*_unmapped", "contigs.fasta")))
RESOURCES = os.path.join(ROOT, "..", "investigate_phylo", "resources")
MYCO_PANEL = [os.path.join(RESOURCES, "LT708304.1.fasta"),         # M. bovis AF2122/97
              os.path.join(RESOURCES, "NC_002677.1.fasta")]        # M. leprae TN
OUT = os.path.join(ROOT, "résultats", "contamination_filter.tsv")

MIN_IDENT = 90.0      # % identité pour "présent"
MIN_QCOV = 50.0       # % de la longueur du contig couverte
MYCO_QCOV = 20.0      # seuil plus permissif pour "mycobactérien ailleurs" (homologie partielle)
MIN_LEN = 300

_COV_RE = re.compile(r"_cov_([0-9.]+)")


def read_fasta(path):
    name, seq = None, []
    with open(path) as f:
        for line in f:
            line = line.rstrip()
            if line.startswith(">"):
                if name is not None:
                    yield name, "".join(seq)
                name, seq = line[1:].split()[0], []
            else:
                seq.append(line)
    if name is not None:
        yield name, "".join(seq)


def gc_pct(seq):
    s = seq.upper()
    return 100.0 * (s.count("G") + s.count("C")) / (len(s) or 1)


def spades_cov(name):
    m = _COV_RE.search(name)
    return float(m.group(1)) if m else float("nan")


def best_hit_qcov(seq, db):
    """Renvoie (max_pident, qcov%) : identité max et % de la longueur du contig couvert (>= MIN_IDENT)."""
    with tempfile.NamedTemporaryFile("w", suffix=".fa", delete=False) as tf:
        tf.write(">q\n" + seq + "\n")
        qpath = tf.name
    try:
        res = subprocess.run(
            ["blastn", "-query", qpath, "-db", db, "-outfmt",
             "6 pident length qstart qend", "-max_target_seqs", "50"],
            capture_output=True, text=True, timeout=120)
        covered, best_pid = set(), 0.0
        for line in res.stdout.splitlines():
            pid, _, qs, qe = line.split("\t")
            pid = float(pid)
            if pid < MIN_IDENT:
                continue
            a, b = sorted((int(qs), int(qe)))
            covered.update(range(a, b + 1))
            best_pid = max(best_pid, pid)
        return best_pid, 100.0 * len(covered) / (len(seq) or 1)
    finally:
        os.unlink(qpath)


def make_db(fasta, out):
    subprocess.run(["makeblastdb", "-in", fasta, "-dbtype", "nucl", "-out", out],
                   capture_output=True, text=True)


def main():
    if not glob.glob(REF_DB + ".n*"):
        raise SystemExit(f"BLAST db du génome L8 fermé introuvable : {REF_DB}")
    if not ASSEMBLIES:
        raise SystemExit("Aucun assemblage spades_*_unmapped dans résultats/assemblies/")

    tmp = tempfile.mkdtemp(prefix="cf_")
    # bases par souche (présence inter-souches = pangénome)
    strain_dbs = {}
    for asm in ASSEMBLIES:
        strain = os.path.basename(os.path.dirname(asm)).replace("spades_", "").replace("_unmapped", "")
        db = os.path.join(tmp, strain)
        make_db(asm, db)
        strain_dbs[strain] = db
    # panel mycobactérien (taxonomie des absents), si disponible
    myco_db = None
    panel = [p for p in MYCO_PANEL if os.path.exists(p)]
    if panel:
        cat = os.path.join(tmp, "panel.fasta")
        with open(cat, "w") as out:
            for p in panel:
                with open(p) as f:
                    out.write(f.read())
        myco_db = os.path.join(tmp, "myco_panel")
        make_db(cat, myco_db)

    rows = []
    for asm in ASSEMBLIES:
        strain = os.path.basename(os.path.dirname(asm)).replace("spades_", "").replace("_unmapped", "")
        for name, seq in read_fasta(asm):
            if len(seq) < MIN_LEN:
                continue
            pid, qcov = best_hit_qcov(seq, REF_DB)
            in_closed = qcov >= MIN_QCOV and pid >= MIN_IDENT
            # nombre de souches L8 (assemblages) portant le contig
            n_strains = 1 + sum(1 for s, db in strain_dbs.items()
                                if s != strain and best_hit_qcov(seq, db)[1] >= MIN_QCOV)
            # taxonomie : mycobactérien ailleurs (M. bovis / M. leprae) ?
            myco = "n/a"
            if not in_closed and myco_db:
                mpid, mqcov = best_hit_qcov(seq, myco_db)
                myco = f"{mpid:.0f}/{mqcov:.0f}" if mqcov >= MYCO_QCOV else "none"

            if in_closed:
                verdict = "L8_CLOSED_GENOME"                 # présent dans CP048071.1 -> vrai contenu L8
            elif n_strains >= 2:
                verdict = "PANGENOME_CANDIDATE"              # >=2 souches, pas dans RW-TB008 -> accessoire probable
            elif spades_cov(name) < 5:
                verdict = "LOW_COV_SINGLETON"                # 1 souche, absent, faible cov -> suspect fort
            else:
                verdict = "SINGLETON_REVIEW"                 # 1 souche, absent, cov ok -> contaminant OU privé (ID espèce requis)
            rows.append((strain, name, len(seq), f"{gc_pct(seq):.1f}", f"{spades_cov(name):.1f}",
                         f"{pid:.1f}", f"{qcov:.1f}", n_strains, myco, verdict))

    order = {"L8_CLOSED_GENOME": 0, "PANGENOME_CANDIDATE": 1, "SINGLETON_REVIEW": 2,
             "LOW_COV_SINGLETON": 3}
    rows.sort(key=lambda r: (order.get(r[9], 9), r[0], -r[2]))
    with open(OUT, "w") as f:
        f.write("strain\tcontig\tlen\tGC%\tspades_cov\tbest_pident_L8\tqcov_L8%\t"
                "n_L8_strains\tmyco_panel(pid/qcov)\tverdict\n")
        for r in rows:
            f.write("\t".join(str(x) for x in r) + "\n")

    from collections import Counter
    c = Counter(r[9] for r in rows)
    print(f"{len(rows)} contigs -> {OUT}")
    for v in ["L8_CLOSED_GENOME", "PANGENOME_CANDIDATE", "SINGLETON_REVIEW", "LOW_COV_SINGLETON"]:
        print(f"  {v:20s}: {c.get(v, 0)}")
    print("\nContigs ABSENTS du génome L8 fermé (à arbitrer ; myco_panel = hit M.bovis/M.leprae) :")
    for r in rows:
        if r[9] != "L8_CLOSED_GENOME":
            print(f"  {r[0]:13s} {r[1]:40s} len={r[2]} GC={r[3]} cov={r[4]} "
                  f"n_souches={r[7]} myco={r[8]} -> {r[9]}")


if __name__ == "__main__":
    main()
