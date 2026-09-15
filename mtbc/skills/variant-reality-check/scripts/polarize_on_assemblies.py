#!/usr/bin/env python3
"""
Objet: Polariser un variant sur des GENOMES COMPLETS FERMES plutot que sur des appels
       de variants. Derive automatiquement les flancs uniques du site depuis un SPDI et
       un FASTA de reference, localise le site par ces flancs dans chaque assemblage du
       panel (les coordonnees different d'un assemblage a l'autre), et rend un tableau
       presence / absence avec l'ecart mesure entre flancs.
Entrées: --spdi (0-based), --genome (FASTA de reference), --panel (TSV accession /
       etiquette / groupe, ou le panel MTBC par defaut), acces NCBI E-utilities.
Sorties: TSV et rapport texte ; cache des genomes sous --cache.
Réutilisable: oui, tout est parametre. Panel par defaut = MTBC + M. canettii.
Projet: forge dans mtbc/Rv3896c-Rv3898c (P2), generalise en skill.
Date: 2026-09-10
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.request
from pathlib import Path

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
TR = str.maketrans("ACGT", "TGCA")

# accession, etiquette, groupe. Modifiable par --panel.
#
# ATTENTION, deux limites de ce panel par defaut, a lire avant de s'en servir.
#
# 1. Les etiquettes de lignee viennent de la LITTERATURE sur ces souches, pas d'un
#    genotypage refait ici. Elles sont indicatives. Le piege est atteste : KZN 1435 a
#    d'abord ete etiquetee L2 dans ce panel parce qu'elle est XDR et sud-africaine,
#    alors qu'elle est F15/LAM4/KZN, donc L4. L'erreur a fabrique une fausse anomalie
#    (« une souche L2 se comporte comme L4 ») avant d'etre reperee. Ne jamais tirer
#    une conclusion de lignee du seul nom d'une souche : la verifier au barcode.
# 2. Le panel ne couvre PAS L1, L2, L3, L5, L7, L8, L9 ni L10. Il permet d'opposer la
#    reference, d'autres L4, le clade animal, L6 et l'outgroup ; il ne permet pas de
#    dire qu'un allele est present « dans toutes les lignees humaines ».
PANEL_MTBC = [
    ("NC_000962.3", "H37Rv (reference)", "L4.9"),
    ("CP007027.1", "H37RvSiena", "L4.9"),
    ("CP003248.2", "H37Rv TBSGC", "L4.9"),
    ("CP110619.1", "H37Rv(new), Chitale 2022", "L4.9"),
    ("NC_009525.1", "H37Ra (derive de H37, 1934)", "L4.9"),
    ("NC_002755.2", "CDC1551", "L4"),
    ("NC_009565.1", "F11", "L4"),
    ("AP012340.1", "Erdman", "L4"),
    ("NC_012943.1", "KZN 1435 (F15/LAM4/KZN)", "L4"),
    ("NC_015758.1", "M. africanum GM041182", "L6"),
    ("NC_008769.1", "M. bovis BCG Pasteur", "Bovis"),
    ("LT708304.1", "M. bovis AF2122/97", "Bovis"),
    ("NC_015848.1", "M. canettii CIPT 140010059", "OUTGROUP"),
]


def load(p: Path) -> str:
    return "".join(l.strip() for l in p.read_text().splitlines()
                   if not l.startswith(">")).upper()


def fetch(acc: str, cache: Path) -> Path:
    p = cache / f"{acc}.fa"
    if p.exists() and p.stat().st_size > 1000:
        return p
    cache.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(
            f"{EUTILS}?db=nuccore&id={acc}&rettype=fasta&retmode=text",
            timeout=300) as r:
        p.write_bytes(r.read())
    return p


def parse_spdi(s: str) -> tuple[int, str, str]:
    parts = s.split(":")
    if len(parts) == 4:
        parts = parts[1:]
    return int(parts[0]), parts[1].upper(), parts[2].upper()


def derive_flanks(genome: str, pos0: int, ref: str, alt: str,
                  n_left: int = 13, n_right: int = 22,
                  grow: int = 40) -> tuple[str, str, int]:
    """Flancs UNIQUES encadrant le site, et ecart attendu chez la reference.

    Les flancs sont allonges tant qu'ils ne sont pas uniques dans le chromosome :
    un flanc repete ferait pointer le test sur un paralogue. L'ecart de reference
    est len(ref) - len(la partie commune), c'est-a-dire 0 pour une insertion
    ecrite depuis une reference qui ne la porte pas.
    """
    i0 = pos0                      # SPDI 0-based -> index 0-based direct
    if genome[i0 : i0 + len(ref)] != ref:
        raise SystemExit(
            f"allele de reference non retrouve a {pos0} (0-based) : "
            f"lu {genome[i0:i0+len(ref)]!r}, attendu {ref!r}. "
            "Verifier la convention de coordonnees avant d'aller plus loin.")
    common = 0
    while common < min(len(ref), len(alt)) and ref[common] == alt[common]:
        common += 1
    site_end = i0 + len(ref)
    for extra in range(0, grow + 1):
        L = genome[i0 + common - (n_left + extra) : i0 + common]
        R = genome[site_end : site_end + n_right + extra]
        if genome.count(L) == 1 and genome.count(R) == 1:
            return L, R, len(ref) - common
    raise SystemExit("impossible d'obtenir des flancs uniques : region repetee, "
                     "un test par flancs n'y est pas fiable.")


def locate(seq: str, L: str, R: str, window: int = 200) -> tuple[str, str, int] | None:
    """Ecart entre les deux flancs, sur les deux brins. Rend None si introuvable.

    Ce qui est mesure est la DISTANCE entre flancs, jamais l'identite de ce qu'il
    y a entre eux : un outgroup divergent peut porter le meme nombre de bases avec
    une substitution, et un test d'egalite de chaine inverserait la conclusion.
    """
    for src, strand in ((seq, "+"), (seq.translate(TR)[::-1], "-")):
        hits = [m.start() for m in re.finditer(re.escape(L), src)]
        if len(hits) != 1:
            continue
        i = hits[0] + len(L)
        j = src.find(R, i, i + window)
        if j < 0:
            continue
        return src[i : j + 20], strand, j - i
    return None


def locate_by_blast(target: Path, ref_fasta: Path, pos0: int,
                    ref: str, L: str, R: str, pad: int = 250):
    """Repli pour un genome trop divergent pour la correspondance exacte des flancs.

    Aligne une fenetre de la reference autour du site et lit l'ecart depuis
    l'alignement. Necessaire pour un outgroup : chez M. canettii, un flanc de
    13 pb peut porter une substitution et devenir introuvable, alors que la
    region est parfaitement orthologue.
    """
    import shutil, subprocess, tempfile
    if not shutil.which("blastn"):
        return None
    g = load(ref_fasta)
    lo, hi = max(0, pos0 - pad), min(len(g), pos0 + len(ref) + pad)
    with tempfile.NamedTemporaryFile("w", suffix=".fa", delete=False) as f:
        f.write(f">q\n{g[lo:hi]}\n")
        qp = f.name
    r = subprocess.run(["blastn", "-query", qp, "-subject", str(target),
                        "-outfmt", "6 sstart send length sstrand"],
                       capture_output=True, text=True)
    Path(qp).unlink(missing_ok=True)
    if not r.stdout.strip():
        return None
    ss, se, ln, strand = r.stdout.split("\n")[0].split("\t")
    a, b = sorted((int(ss), int(se)))
    seg = load(target)[a - 1 : b]
    if strand == "minus":
        seg = seg.translate(TR)[::-1]
    # relocaliser par un demi-flanc, plus tolerant a une substitution
    i = seg.find(L[-7:])
    if i < 0:
        return None
    i += 7
    j = seg.find(R[:10], i, i + 200)
    if j < 0:
        return None
    return seg[i : j + 20], "blastn", j - i


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--spdi", required=True, help="variant SPDI 0-based pos:ref:alt")
    ap.add_argument("--genome", required=True, help="FASTA du genome de reference")
    ap.add_argument("--panel", default=None,
                    help="TSV accession<TAB>etiquette<TAB>groupe ; defaut = panel MTBC")
    ap.add_argument("--cache", default="genomes_complets")
    ap.add_argument("--out-tsv", default=None)
    a = ap.parse_args()

    genome = load(Path(a.genome))
    pos0, ref, alt = parse_spdi(a.spdi)
    L, R, ecart_ref = derive_flanks(genome, pos0, ref, alt)
    common_len = 0
    while common_len < min(len(ref), len(alt)) and ref[common_len] == alt[common_len]:
        common_len += 1
    attendu = ecart_ref + (len(alt) - len(ref))

    panel = PANEL_MTBC
    if a.panel:
        panel = [tuple(l.split("\t")[:3])
                 for l in Path(a.panel).read_text().splitlines()
                 if l.strip() and not l.startswith("#")]

    cache = Path(a.cache)
    rows = []
    for acc, label, grp in panel:
        local = Path(a.genome) if acc in Path(a.genome).name else None
        try:
            fasta = local if local and local.exists() else fetch(acc, cache)
            hit = locate(load(fasta), L, R)
        except Exception as e:                       # reseau, accession retiree...
            rows.append((acc, label, grp, "?", "", f"ERREUR {type(e).__name__}"))
            continue
        if hit is None:
            hit = locate_by_blast(fasta, Path(a.genome), pos0, ref, L, R)
            if hit is None:
                rows.append((acc, label, grp, "?", "",
                             "flancs introuvables meme par blastn"))
                continue
        between, strand, ecart = hit
        if len(ref) == len(alt):
            # substitution : l'ecart ne distingue rien, il faut lire la base
            seg_ref = ref[common_len:] or ref
            seg_alt = alt[common_len:] or alt
            obs = between[:len(seg_ref)]
            etat = ("comme ALT" if obs == seg_alt
                    else "comme REF" if obs == seg_ref else f"tiers ({obs})")
        else:
            etat = ("comme ALT" if ecart == attendu
                    else "comme REF" if ecart == ecart_ref else f"autre ({ecart} pb)")
        rows.append((acc, label, grp, etat, f"{ecart} pb", f"brin {strand}, {between[:24]}"))

    hdr = ["accession", "souche", "groupe", "etat", "ecart_entre_flancs", "note"]
    tsv = ["\t".join(hdr)] + ["\t".join(map(str, r)) for r in rows]
    if a.out_tsv:
        Path(a.out_tsv).write_text("\n".join(tsv) + "\n")

    print(f"Variant {a.spdi}   type "
          f"{'insertion' if len(alt) > len(ref) else 'deletion' if len(alt) < len(ref) else 'substitution'}")
    print(f"Flanc amont {L}  |  flanc aval {R}")
    print(f"Ecart attendu : {ecart_ref} pb si comme la REFERENCE, "
          f"{attendu} pb si comme l'ALTERNATIF\n")
    print(f"{'souche':32s} {'groupe':10s} {'etat':12s} {'ecart':8s} note")
    print("-" * 108)
    for acc, label, grp, etat, ecart, note in rows:
        print(f"{label:32s} {grp:10s} {etat:12s} {ecart:8s} {note}")
    print("\nGenomes COMPLETS FERMES : ni defaut de couverture, ni ambiguite de mapping,")
    print("ni seuil d'appel. Un desaccord avec le `spdi.txt` accuse l'appel, pas l'assemblage.")


if __name__ == "__main__":
    main()
