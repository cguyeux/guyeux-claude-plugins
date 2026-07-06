#!/usr/bin/env python3
"""
Co-evolution Statistical Tests for MTBC-Human Co-divergence

Mantel test, partial Mantel, isolation by distance, PACo (Procrustean Approach
to Cophylogeny), FST (Weir & Cockerham), and AMOVA.

Usage:
    python3 coevolution.py distances.csv geo_data.csv --test mantel -o results.csv
    python3 coevolution.py distances.csv geo_data.csv --test fst --group-column country
    python3 coevolution.py distances.csv geo_data.csv --test paco \
        --host-distances human_fst.csv --host-parasite-links hp_links.csv
"""

import argparse
import json
import sys
from collections import defaultdict
from math import radians, cos, sin, asin, sqrt

import numpy as np
import pandas as pd
from scipy import stats
from scipy.spatial.distance import squareform, pdist

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    HAS_PLOT = True
except ImportError:
    HAS_PLOT = False

try:
    from sklearn.utils import check_random_state
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


# ---------------------------------------------------------------------------
# Country centroids (lat, lon) for geographic distance computation
# ---------------------------------------------------------------------------

COUNTRY_CENTROIDS = {
    "Afghanistan": (33.9, 67.7), "Albania": (41.2, 20.2), "Algeria": (28.0, 1.7),
    "Angola": (-11.2, 17.9), "Argentina": (-38.4, -63.6), "Armenia": (40.1, 45.0),
    "Australia": (-25.3, 133.8), "Austria": (47.5, 14.6), "Azerbaijan": (40.1, 47.6),
    "Bangladesh": (23.7, 90.4), "Belarus": (53.7, 27.9), "Belgium": (50.8, 4.5),
    "Benin": (9.3, 2.3), "Bhutan": (27.5, 90.4), "Bolivia": (-16.3, -63.6),
    "Bosnia and Herzegovina": (43.9, 17.7), "Botswana": (-22.3, 24.7),
    "Brazil": (-14.2, -51.9), "Brunei": (4.5, 114.7), "Bulgaria": (42.7, 25.5),
    "Burkina Faso": (12.4, -1.6), "Burundi": (-3.4, 29.9), "Cambodia": (12.6, 105.0),
    "Cameroon": (7.4, 12.4), "Canada": (56.1, -106.3), "Central African Republic": (6.6, 20.9),
    "Chad": (15.5, 18.7), "Chile": (-35.7, -71.5), "China": (35.9, 104.2),
    "Colombia": (4.6, -74.3), "Comoros": (-11.9, 43.9), "Congo": (-0.2, 15.8),
    "Costa Rica": (9.7, -83.8), "Croatia": (45.1, 15.2), "Cuba": (21.5, -77.8),
    "Cyprus": (35.1, 33.4), "Czech Republic": (49.8, 15.5), "Czechia": (49.8, 15.5),
    "DR Congo": (-4.0, 21.8), "Dem. Rep. Congo": (-4.0, 21.8),
    "Denmark": (56.3, 9.5), "Djibouti": (11.8, 42.6),
    "Dominican Republic": (18.7, -70.2), "Ecuador": (-1.8, -78.2),
    "Egypt": (26.8, 30.8), "El Salvador": (13.8, -88.9),
    "Equatorial Guinea": (1.7, 10.3), "Eritrea": (15.2, 39.8),
    "Estonia": (58.6, 25.0), "Eswatini": (-26.5, 31.5), "eSwatini": (-26.5, 31.5),
    "Ethiopia": (9.1, 40.5), "Fiji": (-17.7, 178.1),
    "Finland": (61.9, 25.7), "France": (46.2, 2.2),
    "Gabon": (-0.8, 11.6), "Gambia": (13.4, -16.6), "Georgia": (42.3, 43.4),
    "Germany": (51.2, 10.4), "Ghana": (7.9, -1.0), "Greece": (39.1, 21.8),
    "Guatemala": (15.8, -90.2), "Guinea": (9.9, -9.7), "Guinea-Bissau": (12.0, -15.2),
    "Guyana": (5.0, -58.9), "Haiti": (19.0, -72.3), "Honduras": (15.2, -86.2),
    "Hungary": (47.2, 19.5), "Iceland": (65.0, -19.0), "India": (20.6, 78.9),
    "Indonesia": (-0.8, 113.9), "Iran": (32.4, 53.7), "Iraq": (33.2, 43.7),
    "Ireland": (53.4, -8.2), "Israel": (31.0, 34.9), "Italy": (41.9, 12.6),
    "Ivory Coast": (7.5, -5.5), "Jamaica": (18.1, -77.3),
    "Japan": (36.2, 138.3), "Jordan": (31.0, 36.8),
    "Kazakhstan": (48.0, 68.0), "Kenya": (-0.0, 37.9),
    "Kuwait": (29.3, 47.5), "Kyrgyzstan": (41.2, 74.8),
    "Laos": (19.9, 102.5), "Latvia": (56.9, 24.1),
    "Lebanon": (33.9, 35.9), "Lesotho": (-29.6, 28.2),
    "Liberia": (6.4, -9.4), "Libya": (26.3, 17.2),
    "Lithuania": (55.2, 24.0), "Luxembourg": (49.8, 6.1),
    "Madagascar": (-18.8, 46.9), "Malawi": (-13.3, 34.3),
    "Malaysia": (4.2, 101.9), "Mali": (17.6, -4.0),
    "Mauritania": (21.0, -10.9), "Mauritius": (-20.3, 57.6),
    "Mexico": (23.6, -102.6), "Moldova": (47.4, 28.4),
    "Mongolia": (46.9, 103.8), "Montenegro": (42.7, 19.4),
    "Morocco": (31.8, -7.1), "Mozambique": (-18.7, 35.5),
    "Myanmar": (21.9, 96.0), "Namibia": (-22.6, 17.1),
    "Nepal": (28.4, 84.1), "Netherlands": (52.1, 5.3),
    "New Zealand": (-40.9, 174.9), "Nicaragua": (12.9, -85.2),
    "Niger": (17.6, 8.1), "Nigeria": (9.1, 8.7),
    "North Korea": (40.3, 127.5), "North Macedonia": (41.5, 21.7),
    "Norway": (60.5, 8.5), "Oman": (21.5, 56.0),
    "Pakistan": (30.4, 69.3), "Palestine": (31.9, 35.2),
    "Panama": (8.5, -80.8), "Papua New Guinea": (-6.3, 143.9),
    "Paraguay": (-23.4, -58.4), "Peru": (-9.2, -75.0),
    "Philippines": (12.9, 121.8), "Poland": (51.9, 19.1),
    "Portugal": (39.4, -8.2), "Qatar": (25.4, 51.2),
    "Romania": (45.9, 25.0), "Russia": (61.5, 105.3),
    "Rwanda": (-1.9, 29.9), "Saudi Arabia": (23.9, 45.1),
    "Senegal": (14.5, -14.5), "Serbia": (44.0, 21.0),
    "Sierra Leone": (8.5, -11.8), "Singapore": (1.4, 103.8),
    "Slovakia": (48.7, 19.7), "Slovenia": (46.2, 15.0),
    "Somalia": (5.2, 46.2), "South Africa": (-30.6, 22.9),
    "South Korea": (35.9, 128.0), "South Sudan": (6.9, 31.3),
    "Spain": (40.5, -3.7), "Sri Lanka": (7.9, 80.8),
    "Sudan": (12.9, 30.2), "Suriname": (4.0, -56.0),
    "Sweden": (60.1, 18.6), "Switzerland": (46.8, 8.2),
    "Syria": (34.8, 38.9), "Taiwan": (23.7, 121.0),
    "Tajikistan": (38.9, 71.3), "Tanzania": (-6.4, 34.9),
    "Thailand": (15.9, 101.0), "Togo": (8.6, 1.2),
    "Trinidad and Tobago": (10.7, -61.2), "Tunisia": (33.9, 9.5),
    "Turkey": (38.9, 35.2), "Turkmenistan": (39.0, 59.6),
    "Uganda": (1.4, 32.3), "Ukraine": (48.4, 31.2),
    "United Arab Emirates": (23.4, 53.8), "United Kingdom": (55.4, -3.4),
    "United States": (37.1, -95.7), "United States of America": (37.1, -95.7),
    "USA": (37.1, -95.7), "UK": (55.4, -3.4),
    "Uruguay": (-32.5, -55.8), "Uzbekistan": (41.4, 64.6),
    "Venezuela": (6.4, -66.6), "Vietnam": (14.1, 108.3),
    "Yemen": (15.6, 48.5), "Zambia": (-13.1, 27.8), "Zimbabwe": (-19.0, 29.2),
    "Cote d'Ivoire": (7.5, -5.5),
}


# ---------------------------------------------------------------------------
# Haversine distance
# ---------------------------------------------------------------------------

def haversine(lat1, lon1, lat2, lon2):
    """Haversine distance in km between two (lat, lon) points."""
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return 6371 * 2 * asin(sqrt(a))


def geographic_distance_matrix(geo_data: pd.DataFrame) -> tuple:
    """Build geographic distance matrix from coordinates or country names.

    Returns (distance_matrix as np.ndarray, ordered strain_ids).
    """
    strain_ids = geo_data["strain_id"].astype(str).tolist()

    if "latitude" in geo_data.columns and "longitude" in geo_data.columns:
        coords = geo_data[["latitude", "longitude"]].values
    elif "country" in geo_data.columns:
        coords = []
        for country in geo_data["country"]:
            c = COUNTRY_CENTROIDS.get(country)
            if c is None:
                print(f"Warning: no centroid for '{country}', using (0, 0).", file=sys.stderr)
                c = (0, 0)
            coords.append(c)
        coords = np.array(coords)
    else:
        raise ValueError("geo_data must have latitude/longitude or country columns.")

    n = len(strain_ids)
    dist = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            d = haversine(coords[i][0], coords[i][1], coords[j][0], coords[j][1])
            dist[i, j] = d
            dist[j, i] = d

    return dist, strain_ids


# ---------------------------------------------------------------------------
# Load distance matrix
# ---------------------------------------------------------------------------

def load_distance_matrix(path: str) -> tuple:
    """Load a square distance matrix CSV. Returns (matrix, labels)."""
    df = pd.read_csv(path, index_col=0)
    labels = df.index.astype(str).tolist()
    return df.values.astype(float), labels


# ---------------------------------------------------------------------------
# Mantel test
# ---------------------------------------------------------------------------

def mantel_test(
    dist_a: np.ndarray, dist_b: np.ndarray,
    n_perm: int = 9999, method: str = "pearson"
) -> dict:
    """Mantel test: correlation between two distance matrices.

    Uses permutation of rows/columns for p-value.
    """
    n = dist_a.shape[0]
    # Extract upper triangle
    idx = np.triu_indices(n, k=1)
    va = dist_a[idx]
    vb = dist_b[idx]

    if method == "spearman":
        obs_r, _ = stats.spearmanr(va, vb)
    else:
        obs_r, _ = stats.pearsonr(va, vb)

    # Permutation test
    count = 0
    rng = np.random.default_rng(42)
    for _ in range(n_perm):
        perm = rng.permutation(n)
        dist_b_perm = dist_b[np.ix_(perm, perm)]
        vb_perm = dist_b_perm[idx]
        if method == "spearman":
            r_perm, _ = stats.spearmanr(va, vb_perm)
        else:
            r_perm, _ = stats.pearsonr(va, vb_perm)
        if r_perm >= obs_r:
            count += 1

    p_value = (count + 1) / (n_perm + 1)

    return {
        "test": "mantel",
        "method": method,
        "r": float(obs_r),
        "p_value": float(p_value),
        "n_samples": n,
        "n_permutations": n_perm,
        "significant": p_value < 0.05,
    }


# ---------------------------------------------------------------------------
# Partial Mantel test
# ---------------------------------------------------------------------------

def partial_mantel(
    dist_a: np.ndarray, dist_b: np.ndarray, dist_c: np.ndarray,
    n_perm: int = 9999
) -> dict:
    """Partial Mantel test: correlation between A and B controlling for C."""
    n = dist_a.shape[0]
    idx = np.triu_indices(n, k=1)
    va = dist_a[idx]
    vb = dist_b[idx]
    vc = dist_c[idx]

    # Residualize A and B on C
    def residualize(y, x):
        slope, intercept, _, _, _ = stats.linregress(x, y)
        return y - (slope * x + intercept)

    ra = residualize(va, vc)
    rb = residualize(vb, vc)

    obs_r, _ = stats.pearsonr(ra, rb)

    count = 0
    rng = np.random.default_rng(42)
    for _ in range(n_perm):
        perm = rng.permutation(n)
        dist_b_perm = dist_b[np.ix_(perm, perm)]
        vb_perm = dist_b_perm[idx]
        rb_perm = residualize(vb_perm, vc)
        r_perm, _ = stats.pearsonr(ra, rb_perm)
        if r_perm >= obs_r:
            count += 1

    p_value = (count + 1) / (n_perm + 1)

    return {
        "test": "partial_mantel",
        "r_partial": float(obs_r),
        "p_value": float(p_value),
        "n_samples": n,
        "n_permutations": n_perm,
        "significant": p_value < 0.05,
    }


# ---------------------------------------------------------------------------
# Isolation by distance
# ---------------------------------------------------------------------------

def isolation_by_distance(
    dist_genetic: np.ndarray, dist_geographic: np.ndarray,
    labels: list = None, n_perm: int = 9999
) -> dict:
    """Test for isolation by distance: regression of genetic ~ geographic distance."""
    n = dist_genetic.shape[0]
    idx = np.triu_indices(n, k=1)
    gen = dist_genetic[idx]
    geo = dist_geographic[idx]

    # Log-transform geographic distance (common for IBD)
    geo_log = np.log1p(geo)

    slope, intercept, r_value, p_value_param, std_err = stats.linregress(geo_log, gen)

    # Permutation-based Mantel for p-value
    mantel_result = mantel_test(dist_genetic, dist_geographic, n_perm)

    return {
        "test": "ibd",
        "slope": float(slope),
        "intercept": float(intercept),
        "r_squared": float(r_value ** 2),
        "r_value": float(r_value),
        "p_value_regression": float(p_value_param),
        "p_value_mantel": mantel_result["p_value"],
        "mantel_r": mantel_result["r"],
        "n_pairs": len(gen),
        "n_samples": n,
        "significant": mantel_result["p_value"] < 0.05,
    }


def plot_ibd(dist_genetic, dist_geographic, result, output_path):
    """Plot isolation by distance scatter."""
    if not HAS_PLOT:
        return

    n = dist_genetic.shape[0]
    idx = np.triu_indices(n, k=1)
    gen = dist_genetic[idx]
    geo = dist_geographic[idx]
    geo_log = np.log1p(geo)

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(geo_log, gen, s=5, alpha=0.3, c="#2196F3")

    # Regression line
    x_line = np.linspace(geo_log.min(), geo_log.max(), 100)
    y_line = result["slope"] * x_line + result["intercept"]
    ax.plot(x_line, y_line, "r-", linewidth=2,
            label=f"R²={result['r_squared']:.4f}, p={result['p_value_mantel']:.4f}")

    ax.set_xlabel("ln(geographic distance + 1) [km]")
    ax.set_ylabel("Genetic distance (SNPs)")
    ax.set_title("Isolation by Distance")
    ax.legend()

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"IBD plot saved: {output_path}", file=sys.stderr)


# ---------------------------------------------------------------------------
# PACo — Procrustean Approach to Cophylogeny
# ---------------------------------------------------------------------------

def paco_test(
    host_dist: np.ndarray, parasite_dist: np.ndarray,
    hp_links: np.ndarray, n_perm: int = 9999
) -> dict:
    """PACo test for host-parasite co-phylogeny.

    Args:
        host_dist: square distance matrix between host populations
        parasite_dist: square distance matrix between parasite strains
        hp_links: binary matrix (n_parasites x n_hosts), 1 if associated
        n_perm: permutation count

    Returns dict with m² statistic and p-value.
    """
    # Principal coordinates
    def pcoa(dist_mat, n_axes=None):
        n = dist_mat.shape[0]
        if n_axes is None:
            n_axes = n - 1
        # Double centering
        H = np.eye(n) - np.ones((n, n)) / n
        B = -0.5 * H @ (dist_mat ** 2) @ H
        eigvals, eigvecs = np.linalg.eigh(B)
        # Sort descending
        order = np.argsort(eigvals)[::-1]
        eigvals = eigvals[order][:n_axes]
        eigvecs = eigvecs[:, order][:, :n_axes]
        # Keep positive eigenvalues
        pos = eigvals > 0
        return eigvecs[:, pos] * np.sqrt(eigvals[pos])

    host_pcoa = pcoa(host_dist)
    para_pcoa = pcoa(parasite_dist)

    # Project parasite onto host space via link matrix
    # Normalize link matrix rows
    hp_norm = hp_links / hp_links.sum(axis=1, keepdims=True).clip(min=1)
    projected = hp_norm @ host_pcoa

    # Procrustes: find best rotation
    def procrustes_m2(X, Y):
        """Sum of squared residuals after Procrustes alignment."""
        # Center
        X_c = X - X.mean(axis=0)
        Y_c = Y - Y.mean(axis=0)
        # Ensure same number of dimensions
        min_d = min(X_c.shape[1], Y_c.shape[1])
        X_c = X_c[:, :min_d]
        Y_c = Y_c[:, :min_d]
        # SVD for optimal rotation
        U, _, Vt = np.linalg.svd(Y_c.T @ X_c)
        R = Vt.T @ U.T
        Y_rot = Y_c @ R
        return float(np.sum((X_c - Y_rot) ** 2))

    # Observed m²
    min_dim = min(projected.shape[1], para_pcoa.shape[1])
    obs_m2 = procrustes_m2(projected[:, :min_dim], para_pcoa[:, :min_dim])

    # Permutation test
    count = 0
    rng = np.random.default_rng(42)
    for _ in range(n_perm):
        perm = rng.permutation(hp_links.shape[0])
        hp_perm = hp_links[perm, :]
        hp_perm_norm = hp_perm / hp_perm.sum(axis=1, keepdims=True).clip(min=1)
        proj_perm = hp_perm_norm @ host_pcoa
        m2_perm = procrustes_m2(proj_perm[:, :min_dim], para_pcoa[:, :min_dim])
        if m2_perm <= obs_m2:
            count += 1

    p_value = (count + 1) / (n_perm + 1)

    return {
        "test": "paco",
        "m_squared": float(obs_m2),
        "p_value": float(p_value),
        "n_parasites": int(hp_links.shape[0]),
        "n_hosts": int(hp_links.shape[1]),
        "n_permutations": n_perm,
        "significant": p_value < 0.05,
    }


# ---------------------------------------------------------------------------
# FST — Weir & Cockerham
# ---------------------------------------------------------------------------

def compute_fst(
    dist_matrix: np.ndarray, labels: list, populations: dict
) -> dict:
    """Compute pairwise FST between populations using distance-based approach.

    Args:
        dist_matrix: square genetic distance matrix
        labels: strain IDs matching matrix rows
        populations: {strain_id: population_name}
    """
    # Group indices by population
    pop_groups = defaultdict(list)
    for i, label in enumerate(labels):
        pop = populations.get(label)
        if pop:
            pop_groups[pop].append(i)

    pop_names = sorted(pop_groups.keys())
    n_pops = len(pop_names)

    if n_pops < 2:
        return {"test": "fst", "error": "Need >= 2 populations"}

    # Pairwise FST using distance-based estimator
    # FST ≈ 1 - (mean within-group distance) / (mean total distance)
    results = []
    for i, p1 in enumerate(pop_names):
        for j, p2 in enumerate(pop_names):
            if j <= i:
                continue
            idx1 = pop_groups[p1]
            idx2 = pop_groups[p2]

            # Within-group distances
            within_1 = []
            for a in range(len(idx1)):
                for b in range(a + 1, len(idx1)):
                    within_1.append(dist_matrix[idx1[a], idx1[b]])
            within_2 = []
            for a in range(len(idx2)):
                for b in range(a + 1, len(idx2)):
                    within_2.append(dist_matrix[idx2[a], idx2[b]])

            # Between-group distances
            between = []
            for a in idx1:
                for b in idx2:
                    between.append(dist_matrix[a, b])

            mean_within = np.mean(within_1 + within_2) if (within_1 or within_2) else 0
            mean_between = np.mean(between) if between else 0
            mean_total = np.mean(within_1 + within_2 + between) if between else 0

            fst = 1 - mean_within / mean_total if mean_total > 0 else 0

            results.append({
                "pop_1": p1,
                "pop_2": p2,
                "n_1": len(idx1),
                "n_2": len(idx2),
                "fst": round(float(fst), 4),
                "mean_within": round(float(mean_within), 2),
                "mean_between": round(float(mean_between), 2),
            })

    # Global FST
    all_within = []
    all_between = []
    for i, p1 in enumerate(pop_names):
        idx1 = pop_groups[p1]
        for a in range(len(idx1)):
            for b in range(a + 1, len(idx1)):
                all_within.append(dist_matrix[idx1[a], idx1[b]])
        for j, p2 in enumerate(pop_names):
            if j <= i:
                continue
            idx2 = pop_groups[p2]
            for a in idx1:
                for b in idx2:
                    all_between.append(dist_matrix[a, b])

    mean_w = np.mean(all_within) if all_within else 0
    mean_t = np.mean(all_within + all_between) if all_between else 0
    global_fst = 1 - mean_w / mean_t if mean_t > 0 else 0

    return {
        "test": "fst",
        "global_fst": round(float(global_fst), 4),
        "n_populations": n_pops,
        "pairwise": results,
    }


# ---------------------------------------------------------------------------
# AMOVA — Analysis of Molecular Variance
# ---------------------------------------------------------------------------

def amova(
    dist_matrix: np.ndarray, labels: list,
    populations: dict, regions: dict = None
) -> dict:
    """Hierarchical AMOVA: partition variance among regions, among populations
    within regions, and within populations.

    Args:
        dist_matrix: square genetic distance matrix
        labels: strain IDs
        populations: {strain_id: population}
        regions: {population: region} (optional, for 3-level hierarchy)
    """
    # Squared distances
    D2 = dist_matrix ** 2
    n = len(labels)

    # Group by population
    pop_groups = defaultdict(list)
    for i, label in enumerate(labels):
        pop = populations.get(label)
        if pop:
            pop_groups[pop].append(i)

    # Total SS
    ss_total = np.sum(D2) / (2 * n)

    # Within-population SS
    ss_within = 0
    n_within = 0
    for pop, indices in pop_groups.items():
        np_pop = len(indices)
        if np_pop > 1:
            for a in range(np_pop):
                for b in range(a + 1, np_pop):
                    ss_within += D2[indices[a], indices[b]]
            n_within += np_pop

    ss_within /= max(n_within, 1)

    # Among-populations SS
    ss_among_pops = ss_total - ss_within

    result = {
        "test": "amova",
        "n_samples": n,
        "n_populations": len(pop_groups),
        "ss_total": round(float(ss_total), 2),
        "ss_within_populations": round(float(ss_within), 2),
        "ss_among_populations": round(float(ss_among_pops), 2),
        "pct_within": round(100 * ss_within / ss_total, 1) if ss_total > 0 else 0,
        "pct_among_populations": round(100 * ss_among_pops / ss_total, 1) if ss_total > 0 else 0,
    }

    # 3-level hierarchy if regions provided
    if regions:
        region_groups = defaultdict(list)
        for pop, indices in pop_groups.items():
            reg = regions.get(pop, "Unknown")
            region_groups[reg].extend(indices)

        ss_among_regions = 0
        for reg, indices in region_groups.items():
            nr = len(indices)
            if nr > 0:
                reg_mean = np.sum(D2[np.ix_(indices, indices)]) / (2 * nr)
                ss_among_regions += reg_mean

        ss_among_pops_within = ss_among_pops - ss_among_regions
        result["n_regions"] = len(region_groups)
        result["ss_among_regions"] = round(float(ss_among_regions), 2)
        result["ss_among_pops_within_regions"] = round(float(max(ss_among_pops_within, 0)), 2)
        result["pct_among_regions"] = round(
            100 * ss_among_regions / ss_total, 1) if ss_total > 0 else 0
        result["pct_among_pops_within_regions"] = round(
            100 * max(ss_among_pops_within, 0) / ss_total, 1) if ss_total > 0 else 0

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Co-evolution statistical tests for MTBC-human co-divergence.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Mantel test
  python3 coevolution.py distances.csv geo_data.csv --test mantel -o results.csv

  # Isolation by distance
  python3 coevolution.py distances.csv geo_data.csv --test ibd -p ibd.png

  # FST between countries
  python3 coevolution.py distances.csv geo_data.csv --test fst --group-column country

  # PACo
  python3 coevolution.py distances.csv geo_data.csv --test paco \\
    --host-distances human_fst.csv --host-parasite-links hp_links.csv

  # AMOVA
  python3 coevolution.py distances.csv geo_data.csv --test amova \\
    --hierarchy hierarchy.csv
        """,
    )

    parser.add_argument("genetic_distances", help="Square genetic distance matrix CSV")
    parser.add_argument("geo_data", help="CSV with strain_id and coordinates/country")
    parser.add_argument(
        "--test", default="mantel",
        choices=["mantel", "partial_mantel", "ibd", "paco", "fst", "amova"],
    )
    parser.add_argument("--permutations", type=int, default=9999)
    parser.add_argument("--correlation", default="pearson", choices=["pearson", "spearman"])
    parser.add_argument("--covariate", help="Covariate distance matrix for partial Mantel")
    parser.add_argument("--host-distances", help="Host distance matrix for PACo")
    parser.add_argument("--host-parasite-links", help="Host-parasite link CSV for PACo")
    parser.add_argument("--group-column", default="country", help="Group column for FST/AMOVA")
    parser.add_argument("--hierarchy", help="Hierarchy CSV (population, region) for AMOVA")
    parser.add_argument("-o", "--output", help="Output CSV/JSON")
    parser.add_argument("-p", "--plot", help="Diagnostic plot output")
    parser.add_argument("--summary", action="store_true", help="Print JSON summary")

    args = parser.parse_args()

    # Load genetic distances
    gen_dist, gen_labels = load_distance_matrix(args.genetic_distances)
    print(f"Genetic distances: {len(gen_labels)} samples", file=sys.stderr)

    # Load geographic data
    geo = pd.read_csv(args.geo_data)
    # Normalize columns
    col_map = {}
    for col in geo.columns:
        cl = col.lower().strip()
        if cl in ("strain_id", "sra_id", "id", "name", "taxon"):
            col_map[col] = "strain_id"
        elif cl in ("lat", "latitude"):
            col_map[col] = "latitude"
        elif cl in ("lon", "lng", "longitude"):
            col_map[col] = "longitude"
        elif cl == args.group_column.lower():
            col_map[col] = "country"
    geo = geo.rename(columns=col_map)

    if "strain_id" not in geo.columns:
        print("Error: geo_data must have a strain_id column.", file=sys.stderr)
        sys.exit(1)

    # Align samples
    geo_ids = set(geo["strain_id"].astype(str))
    common = [l for l in gen_labels if l in geo_ids]
    if len(common) < 3:
        print(f"Error: only {len(common)} samples in common.", file=sys.stderr)
        sys.exit(1)

    # Reindex genetic matrix to common samples
    idx_map = {l: i for i, l in enumerate(gen_labels)}
    common_idx = [idx_map[c] for c in common]
    gen_dist_aligned = gen_dist[np.ix_(common_idx, common_idx)]

    # Reindex geo data
    geo_aligned = geo[geo["strain_id"].astype(str).isin(common)].copy()
    geo_aligned["strain_id"] = geo_aligned["strain_id"].astype(str)
    # Reorder to match common
    geo_aligned = geo_aligned.set_index("strain_id").loc[common].reset_index()

    print(f"Aligned: {len(common)} samples", file=sys.stderr)

    # Run test
    if args.test == "mantel":
        geo_dist, _ = geographic_distance_matrix(geo_aligned)
        result = mantel_test(gen_dist_aligned, geo_dist, args.permutations, args.correlation)

    elif args.test == "partial_mantel":
        geo_dist, _ = geographic_distance_matrix(geo_aligned)
        if not args.covariate:
            print("Error: --covariate required for partial Mantel.", file=sys.stderr)
            sys.exit(1)
        cov_dist, cov_labels = load_distance_matrix(args.covariate)
        cov_idx = [cov_labels.index(c) for c in common if c in cov_labels]
        cov_aligned = cov_dist[np.ix_(cov_idx, cov_idx)]
        result = partial_mantel(gen_dist_aligned, geo_dist, cov_aligned, args.permutations)

    elif args.test == "ibd":
        geo_dist, _ = geographic_distance_matrix(geo_aligned)
        result = isolation_by_distance(gen_dist_aligned, geo_dist, common, args.permutations)
        if args.plot:
            plot_ibd(gen_dist_aligned, geo_dist, result, args.plot)

    elif args.test == "paco":
        if not args.host_distances or not args.host_parasite_links:
            print("Error: --host-distances and --host-parasite-links required for PACo.",
                  file=sys.stderr)
            sys.exit(1)
        host_dist, host_labels = load_distance_matrix(args.host_distances)
        hp_df = pd.read_csv(args.host_parasite_links)

        # Build link matrix
        hp_map = dict(zip(hp_df.iloc[:, 0].astype(str), hp_df.iloc[:, 1].astype(str)))
        n_para = len(common)
        n_host = len(host_labels)
        links = np.zeros((n_para, n_host))
        host_idx = {h: i for i, h in enumerate(host_labels)}
        for i, strain in enumerate(common):
            host_pop = hp_map.get(strain)
            if host_pop and host_pop in host_idx:
                links[i, host_idx[host_pop]] = 1

        result = paco_test(host_dist, gen_dist_aligned, links, args.permutations)

    elif args.test == "fst":
        populations = dict(zip(
            geo_aligned["strain_id"].astype(str),
            geo_aligned["country"].astype(str)
        ))
        result = compute_fst(gen_dist_aligned, common, populations)

    elif args.test == "amova":
        populations = dict(zip(
            geo_aligned["strain_id"].astype(str),
            geo_aligned["country"].astype(str)
        ))
        regions = None
        if args.hierarchy:
            hier_df = pd.read_csv(args.hierarchy)
            regions = dict(zip(hier_df.iloc[:, 0].astype(str), hier_df.iloc[:, 1].astype(str)))
        result = amova(gen_dist_aligned, common, populations, regions)

    # Output
    if args.output:
        if "pairwise" in result:
            pd.DataFrame(result["pairwise"]).to_csv(args.output, index=False)
            print(f"Pairwise results saved: {args.output}", file=sys.stderr)
        else:
            with open(args.output, "w") as f:
                json.dump(result, f, indent=2, default=str)
            print(f"Results saved: {args.output}", file=sys.stderr)

    # Summary or default output
    if args.summary or not args.output:
        print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
