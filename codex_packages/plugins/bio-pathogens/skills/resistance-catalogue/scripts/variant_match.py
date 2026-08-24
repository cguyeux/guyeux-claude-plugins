"""Matching variant observé ↔ déterminant catalogué, au niveau représentation.

Une souche « porte un déterminant catalogué » si l'un de ses variants observés
correspond, après décomposition, à un SNP R-associé du catalogue. Gère les trois
angles morts de représentation (cf. cahier 2026-05-31) :
  1. codons synonymes  → déjà dans le catalogue via `aa_propagation` (phase8) ;
  2. déterminants rares → inclus dans la matrice de features (phase4) ;
  3. MNV vs SNP         → décomposition des MNV observés en SNP composants (ici).

Utilisé par le baseline déterministe, l'exclusion de la GWAS (phase7) et le futur
prédicteur, pour ne pas sous-estimer la résistance (FQ surtout : +55 pts sur MXF).
"""


def parse_spdi(spdi):
    _, p0, ref, alt = spdi.split(":")
    return int(p0), ref, alt


def decompose(spdi):
    """SNP mono-base composants d'une substitution (SNP→lui-même ; MNV→bases différentes).

    [] pour les indels (longueurs ref/alt différentes), non décomposables ainsi.
    """
    p0, ref, alt = parse_spdi(spdi)
    if len(ref) != len(alt):
        return []
    return [f"NC_000962.3:{p0 + i}:{ref[i]}:{alt[i]}"
            for i in range(len(ref)) if ref[i] != alt[i]]


def determinant_snp_set(catalogue, drug=None, calls=("R-associated",)):
    """Ensemble des SPDI catalogués (SNP mono-base ET indels/MNV), filtrable.

    Les SNP mono-base servent au matching par décomposition (SNP+MNV) ; les indels
    et MNV au matching exact (4e angle mort : indels résolus depuis phase1)."""
    df = catalogue[catalogue["call"].isin(calls) & (catalogue["spdi"] != "")]
    if drug is not None:
        df = df[df["drug"] == drug]
    return set(df["spdi"])


def carrier_columns(features, fidx, det):
    """Indices des features indiquant un déterminant catalogué.

    SNP mono-base : match exact ; MNV substitution : décomposition ∩ SNP catalogués ;
    indel : match exact.
    """
    snp_det = {s for s in det if (lambda p: len(p[1]) == 1 and len(p[2]) == 1)(parse_spdi(s))}
    cols = set()
    for s in features:
        _, ref, alt = parse_spdi(s)
        if len(ref) == 1 and len(alt) == 1:                 # SNP
            if s in det:
                cols.add(fidx[s])
        elif len(ref) == len(alt):                          # MNV substitution
            if s in det or (set(decompose(s)) & snp_det):
                cols.add(fidx[s])
        else:                                               # indel
            if s in det:
                cols.add(fidx[s])
    return sorted(cols)


def carries(X_subset, features, fidx, det_snps):
    """Vecteur booléen (souches) : porte ≥1 déterminant (réconcilié SNP+MNV)."""
    import numpy as np
    cols = carrier_columns(features, fidx, det_snps)
    if not cols:
        return np.zeros(X_subset.shape[0], dtype=bool)
    return (X_subset[:, cols].sum(axis=1).A1 > 0)
