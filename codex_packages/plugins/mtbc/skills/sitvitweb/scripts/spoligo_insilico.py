#!/usr/bin/env python3
"""Spoligotype IN SILICO depuis le pipeline `mp` (136 822 souches MTBC).

Établi et calibré le 2026-07-11 (projet L5L6-codivergence). Voir SKILL.md pour le contexte.

USAGE (le script doit tourner SUR mp, où sont les résultats du pipeline) :

    # 1) envoyer le script et la liste de souches
    scp spoligo_insilico.py mp:/tmp/
    printf 'SRR8952882\nERR3806599\n' > /tmp/sras.txt && scp /tmp/sras.txt mp:/tmp/

    # 2) appels individuels -> CSV
    ssh mp 'python3 /tmp/spoligo_insilico.py /tmp/sras.txt > /tmp/spolo.csv'

    # 3) profils CONSENSUS par groupe (2 colonnes : groupe<TAB>SRA)
    ssh mp 'python3 /tmp/spoligo_insilico.py --consensus /tmp/groupes.tsv'

    # 4) calibration (contrôle qualité obligatoire, cf. plus bas)
    ssh mp 'python3 /tmp/spoligo_insilico.py --calibrate /tmp/beijing_sras.txt'

------------------------------------------------------------------------------
⚠ TROIS PIÈGES, tous rencontrés et tous coûteux
------------------------------------------------------------------------------
1. **NE PAS utiliser `known_coverage/DR*` du `report.json`** : c'est du BRUIT. Le locus DR y est à
   profondeur médiane ~2x quand le génome est à 100-190x (les reads du DR, répétitif, sont jetés par
   le filtre mapq). Diagnostic en 30 s : 8 souches Beijing à >100x donnent 8 motifs DR DIFFÉRENTS,
   alors que le spoligotype Beijing est invariant. La bonne source est `known_coverage_stats.tsv`,
   entrées `ESP*` (espaceurs).

2. **Les 43 spacers standards NE SONT PAS `ESP1..ESP43`.** Ce sont un sous-ensemble DISPERSÉ des 68
   (voir SPACER_TO_ESP ci-dessous, établi par appariement de séquences avec
   `~/Documents/codes/MTBC/TB-tools/data/fastas/spoligo_old.fasta`). Prendre les 43 premiers donne
   000000000000000 pour toutes les Beijing — c'est le symptôme.

3. **L'appel individuel est BRUITÉ** : sensibilité ≈ 90 % par spacer, donc l'octal exact d'une
   Beijing (9 spacers présents) ne sort que dans ~40 % des cas (0,90^9). Le dropout est un biais de
   FAUSSE ABSENCE ⇒ il S'ANNULE PAR VOTE MAJORITAIRE. **Fiable en CONSENSUS de sous-lignée, JAMAIS
   souche par souche.** Ne jamais conclure d'un octal individuel.

⇒ TOUJOURS lancer `--calibrate` sur un lot de Beijing avant d'exploiter les résultats.
"""
import os
import re
import sys
from collections import defaultdict

RESULTS = "/data/current/run/results"

# spacer standard (1-43) -> numéro d'espaceur ESP dans le référentiel 68 du pipeline.
# Établi par appariement de SÉQUENCES (43/43) entre spoligo_old.fasta et known_sequences.fasta.
SPACER_TO_ESP = {
    1: 2,   2: 3,   3: 4,   4: 12,  5: 13,  6: 14,  7: 15,  8: 18,  9: 19,  10: 20,
    11: 21, 12: 22, 13: 23, 14: 24, 15: 25, 16: 26, 17: 27, 18: 28, 19: 29, 20: 30,
    21: 31, 22: 32, 23: 33, 24: 34, 25: 35, 26: 36, 27: 37, 28: 38, 29: 39, 30: 40,
    31: 41, 32: 42, 33: 43, 34: 44, 35: 46, 36: 47, 37: 51, 38: 52, 39: 53, 40: 62,
    41: 63, 42: 64, 43: 65,
}

BEIJING_OCTAL = "000000000003771"   # référence de calibration (invariant)
H37RV_OCTAL   = "777777477760771"

_ESP_RE = re.compile(r"ESP(\d+)(_\d+)?$")


def esp_reads(sra):
    """Lit known_coverage_stats.tsv -> {numéro ESP de base: max(numreads sur les variants alléliques)}."""
    path = os.path.join(RESULTS, sra, "known_coverage_stats.tsv")
    if not os.path.exists(path):
        return None
    reads = {}
    with open(path) as fh:
        for line in fh:
            if line.startswith("#"):
                continue
            cols = line.rstrip("\n").split("\t")
            m = _ESP_RE.match(cols[0])
            if not m:
                continue
            base = int(m.group(1))
            try:
                n = int(cols[3])          # colonne numreads
            except (IndexError, ValueError):
                n = 0
            # les variants ESPn_1, ESPn_2… sont des allèles du MÊME spacer -> on prend le max
            reads[base] = max(reads.get(base, 0), n)
    return reads


def to_binary43(reads, minreads=1):
    """Spacer présent ssi UN de ses variants ESP a >= minreads reads."""
    return "".join(
        "1" if reads.get(SPACER_TO_ESP[k], 0) >= minreads else "0"
        for k in range(1, 44)
    )


def to_octal(bits43):
    """43 bits -> octal 15 caractères (14 triplets + 1 bit)."""
    return "".join(str(int(bits43[3 * i:3 * i + 3], 2)) for i in range(14)) + bits43[42]


def spoligotype(sra, minreads=1):
    reads = esp_reads(sra)
    if not reads:
        return None
    bits = to_binary43(reads, minreads)
    present = [reads[SPACER_TO_ESP[k]] for k in range(1, 44) if bits[k - 1] == "1"]
    return {
        "sra": sra,
        "binary": bits,
        "octal": to_octal(bits),
        "n_spacers_present": bits.count("1"),
        "mean_reads_present": (sum(present) / len(present)) if present else 0.0,
    }


def consensus(binaries):
    """Vote majoritaire : c'est CELA qui rend l'appel fiable (le dropout est une fausse absence)."""
    n = len(binaries)
    cols = [sum(int(b[i]) for b in binaries) / n for i in range(43)]
    bits = "".join("1" if c > 0.5 else "0" for c in cols)
    ambiguous = [i + 1 for i, c in enumerate(cols) if 0.25 < c < 0.75]
    return bits, to_octal(bits), ambiguous


def main():
    args = [a for a in sys.argv[1:]]
    mode = "single"
    if args and args[0] in ("--consensus", "--calibrate"):
        mode = args.pop(0)[2:]
    if not args:
        sys.exit(__doc__)
    path = args[0]

    if mode == "calibrate":
        # contrôle qualité OBLIGATOIRE : fraction de Beijing retrouvant l'octal canonique
        sras = [l.strip() for l in open(path) if l.strip()]
        ok = tot = 0
        for s in sras:
            r = spoligotype(s)
            if not r:
                continue
            tot += 1
            ok += (r["octal"] == BEIJING_OCTAL)
        print("CALIBRATION Beijing (octal canonique %s)" % BEIJING_OCTAL)
        print("  octal exact retrouvé : %d/%d = %.0f%%" % (ok, tot, 100 * ok / tot if tot else 0))
        print("  ATTENDU 30-40% (sensibilité/spacer ~90%, Beijing n'a que 9 spacers présents : 0.9^9).")
        print("  Si BEAUCOUP PLUS BAS (ex. 0%) -> le mapping SPACER_TO_ESP est FAUX : ne rien exploiter.")
        print("  => l'appel individuel est bruité PAR CONSTRUCTION : n'exploiter qu'en CONSENSUS.")
        return

    if mode == "consensus":
        groups = defaultdict(list)
        for line in open(path):
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 2:
                continue
            r = spoligotype(parts[1])
            if r and r["mean_reads_present"] >= 3 and r["n_spacers_present"] >= 10:
                groups[parts[0]].append(r["binary"])
        print("groupe\tn\toctal_consensus\tbinaire_consensus\tspacers_ambigus")
        for g, bins in sorted(groups.items()):
            if len(bins) < 5:
                continue    # en dessous, le vote majoritaire n'amortit pas le dropout
            bits, oct_, amb = consensus(bins)
            print("%s\t%d\t%s\t%s\t%s" % (g, len(bins), oct_, bits, amb))
        return

    # mode single
    print("sra,octal,binary,n_spacers_present,mean_reads_present")
    for line in open(path):
        s = line.strip()
        if not s:
            continue
        r = spoligotype(s)
        if not r:
            continue
        print("%s,%s,%s,%d,%.2f" % (r["sra"], r["octal"], r["binary"],
                                    r["n_spacers_present"], r["mean_reads_present"]))


if __name__ == "__main__":
    main()
