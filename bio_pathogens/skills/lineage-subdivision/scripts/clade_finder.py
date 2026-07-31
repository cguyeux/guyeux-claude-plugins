#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "hdbscan",
#     "matplotlib",
#     "numpy",
#     "scikit-learn",
#     "scipy",
# ]
# ///
"""clade_finder.py — Recherche de sous-populations dans une lignée MTBC.

Construit une matrice de features binaires (pan-SPDI + IS + RD) par SRA
à partir des fichiers report.json/spdi.txt d'un répertoire de lignée,
applique t-SNE + HDBSCAN, et produit un PNG haute résolution.

Usage:
    uv run clade_finder.py /path/to/bdd/actuelle/L4.9/
    uv run clade_finder.py /path/to/bdd/actuelle/L4.9/ --min-cluster-size 10 --dpi 300
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import hdbscan
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.cluster.hierarchy import linkage, dendrogram, fcluster
from scipy.spatial.distance import pdist, squareform
from sklearn.manifold import TSNE
from sklearn.metrics import silhouette_score


# ---------------------------------------------------------------------------
# Étape 1 : lecture des features par SRA
# ---------------------------------------------------------------------------

def read_spdis_from_report(report_path: Path) -> set[str]:
    with open(report_path) as f:
        data = json.load(f)
    return {snp["spdi"] for snp in data.get("snp", []) if "spdi" in snp}


def read_spdis_from_txt(spdi_path: Path) -> set[str]:
    spdis = set()
    with open(spdi_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # Gère le format indexé (col1=index, col2=spdi) ou direct
            parts = line.split("\t")
            spdi = parts[-1] if len(parts) > 1 else parts[0]
            if spdi.startswith("NC_"):
                spdis.add(spdi)
    return spdis


def read_is_from_report(report_path: Path) -> set[str]:
    with open(report_path) as f:
        data = json.load(f)
    is_set = set()
    for entry in data.get("insertion_sequences", []):
        name = entry.get("name", "unknown")
        pos = entry.get("position", 0)
        is_set.add(f"{name}_{pos}")
    return is_set


def read_rd_from_report(report_path: Path) -> dict[str, bool]:
    """Retourne {rd_name: True si présent, False si absent}.

    Exclut les RD dynamiques (CUS_GS_*) qui sont spécifiques à chaque
    souche et ne servent qu'à détecter des délétions individuelles.
    """
    with open(report_path) as f:
        data = json.load(f)
    rd_status = {}
    for rd in data.get("large_rd", []):
        name = rd.get("name", "")
        if name.startswith("CUS_GS_"):
            continue
        pct_missing = rd.get("percent_missing", 0.0)
        rd_status[name] = pct_missing < 50.0
    for rd_name in data.get("missing_rd", []):
        if rd_name.startswith("CUS_GS_"):
            continue
        rd_status[rd_name] = False
    return rd_status


def scan_lineage_dir(lineage_dir: Path, ref: str) -> list[dict]:
    """Scanne le répertoire et lit les données de chaque SRA."""
    samples = []
    sra_dirs = sorted([d for d in lineage_dir.iterdir() if d.is_dir() and not d.name.startswith(".")])

    for sra_dir in sra_dirs:
        ref_dir = sra_dir / ref
        if not ref_dir.is_dir():
            continue
        report = ref_dir / "report.json"
        spdi_txt = ref_dir / "spdi.txt"

        sample = {"sra": sra_dir.name, "spdis": set(), "is": set(), "rd": {}}

        if report.exists():
            try:
                sample["spdis"] = read_spdis_from_report(report)
                sample["is"] = read_is_from_report(report)
                sample["rd"] = read_rd_from_report(report)
                sample["source"] = "report.json"
            except (json.JSONDecodeError, KeyError):
                sample["source"] = "report.json (error)"
        elif spdi_txt.exists():
            sample["spdis"] = read_spdis_from_txt(spdi_txt)
            sample["source"] = "spdi.txt"
        else:
            continue

        if sample["spdis"]:
            samples.append(sample)

    return samples


# ---------------------------------------------------------------------------
# Étape 2 : construction de la matrice de features
# ---------------------------------------------------------------------------

def build_feature_matrix(
    samples: list[dict],
    use_spdi: bool = True,
    use_is: bool = True,
    use_rd: bool = True,
    min_freq: float = 0.02,
    max_freq: float = 0.98,
) -> tuple[np.ndarray, list[str], dict[str, int]]:
    """Construit la matrice binaire n_samples × n_features."""
    n = len(samples)
    feature_names = []
    feature_counts = {"spdi": 0, "is": 0, "rd": 0}
    columns = []

    if use_spdi:
        # Pan-SPDI : compter les fréquences
        spdi_counter = Counter()
        for s in samples:
            spdi_counter.update(s["spdis"])
        # Filtrer par fréquence
        min_count = max(2, int(n * min_freq))
        max_count = int(n * max_freq)
        pan_spdi = sorted([
            sp for sp, c in spdi_counter.items()
            if min_count <= c <= max_count
        ])
        for sp in pan_spdi:
            col = np.array([1 if sp in s["spdis"] else 0 for s in samples], dtype=np.uint8)
            columns.append(col)
        feature_names.extend(pan_spdi)
        feature_counts["spdi"] = len(pan_spdi)

    if use_is:
        # Pan-IS
        is_counter = Counter()
        for s in samples:
            is_counter.update(s["is"])
        pan_is = sorted(is_counter.keys())
        for is_id in pan_is:
            col = np.array([1 if is_id in s["is"] else 0 for s in samples], dtype=np.uint8)
            columns.append(col)
        feature_names.extend([f"IS:{x}" for x in pan_is])
        feature_counts["is"] = len(pan_is)

    if use_rd:
        # Pan-RD
        all_rd_names = set()
        for s in samples:
            all_rd_names.update(s["rd"].keys())
        pan_rd = sorted(all_rd_names)
        for rd_name in pan_rd:
            col = np.array([1 if s["rd"].get(rd_name, True) else 0 for s in samples], dtype=np.uint8)
            columns.append(col)
        feature_names.extend([f"RD:{x}" for x in pan_rd])
        feature_counts["rd"] = len(pan_rd)

    if not columns:
        print("ERREUR: aucune feature construite.", file=sys.stderr)
        sys.exit(1)

    matrix = np.column_stack(columns)
    feature_counts["total"] = matrix.shape[1]
    return matrix, feature_names, feature_counts


# ---------------------------------------------------------------------------
# Étape 3 : t-SNE
# ---------------------------------------------------------------------------

def run_tsne(matrix: np.ndarray, perplexity: float | None, seed: int = 42) -> np.ndarray:
    n = matrix.shape[0]
    if perplexity is None:
        perplexity = min(50.0, max(5.0, (n - 1) / 3.0))

    # Distance Jaccard
    dist = squareform(pdist(matrix.astype(float), metric="jaccard"))

    # Compatibilité scikit-learn (n_iter vs max_iter)
    tsne_kwargs = {
        "n_components": 2,
        "perplexity": perplexity,
        "metric": "precomputed",
        "random_state": seed,
        "init": "random",
    }
    import inspect
    sig = inspect.signature(TSNE.__init__)
    if "max_iter" in sig.parameters:
        tsne_kwargs["max_iter"] = 1000
    else:
        tsne_kwargs["n_iter"] = 1000

    tsne = TSNE(**tsne_kwargs)
    embedding = tsne.fit_transform(dist)
    return embedding, perplexity


# ---------------------------------------------------------------------------
# Étape 4 : HDBSCAN
# ---------------------------------------------------------------------------

def run_hdbscan(
    embedding: np.ndarray, min_cluster_size: int | None
) -> tuple[np.ndarray, np.ndarray, float]:
    n = embedding.shape[0]
    if min_cluster_size is None:
        min_cluster_size = max(3, n // 15)
    min_cluster_size = max(2, min(min_cluster_size, n // 3))

    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=None,
        metric="euclidean",
    )
    labels = clusterer.fit_predict(embedding)
    probs = clusterer.probabilities_

    sil = -1.0
    n_clusters = len(set(labels) - {-1})
    if n_clusters >= 2:
        non_noise = labels != -1
        if non_noise.sum() >= 2:
            sil = float(silhouette_score(embedding[non_noise], labels[non_noise]))

    return labels, probs, sil, min_cluster_size


# ---------------------------------------------------------------------------
# Étape 5 : clustering hiérarchique
# ---------------------------------------------------------------------------

def run_hierarchical(matrix: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Clustering hiérarchique UPGMA sur distances Jaccard."""
    dist_condensed = pdist(matrix.astype(float), metric="jaccard")
    Z = linkage(dist_condensed, method="average")
    return Z, dist_condensed


def build_cluster_dendrogram(
    matrix: np.ndarray, labels: np.ndarray,
) -> tuple[np.ndarray, list[str], list[int]]:
    """Construit un dendrogramme des clusters (centroïdes Jaccard).

    Retourne le linkage, les noms de cluster, et les tailles.
    """
    unique_labels = sorted(set(labels) - {-1})
    if len(unique_labels) < 2:
        return None, [], []

    # Calcul des centroïdes (profil moyen de chaque cluster)
    centroids = []
    cluster_names = []
    cluster_sizes = []
    for cl in unique_labels:
        mask = labels == cl
        centroid = matrix[mask].astype(float).mean(axis=0)
        centroids.append(centroid)
        cluster_names.append(f"C{cl} (n={mask.sum()})")
        cluster_sizes.append(int(mask.sum()))

    centroids = np.array(centroids)
    dist_c = pdist(centroids, metric="jaccard")
    Z_c = linkage(dist_c, method="average")
    return Z_c, cluster_names, cluster_sizes


# ---------------------------------------------------------------------------
# Étape 6 : visualisation PNG
# ---------------------------------------------------------------------------

def _build_cluster_colors(labels: np.ndarray) -> tuple[dict, object]:
    """Construit un mapping cluster → couleur."""
    unique_labels = sorted(set(labels) - {-1})
    n_cl = max(1, len(unique_labels))
    cmap = matplotlib.colormaps.get_cmap("tab20").resampled(n_cl)
    color_map = {}
    for i, cl in enumerate(unique_labels):
        rgba = cmap(i)
        color_map[cl] = rgba
    color_map[-1] = (0.8, 0.8, 0.8, 1.0)  # gris pour le bruit
    return color_map, cmap


def _get_leaf_cluster_map(Z: np.ndarray, labels: np.ndarray) -> dict[int, int | None]:
    """Pour chaque noeud interne du dendrogramme, détermine le cluster
    si toutes les feuilles en dessous appartiennent au même cluster.
    Retourne {node_id: cluster_label ou None si mélangé}."""
    n = len(labels)
    node_clusters = {}

    # Feuilles
    for i in range(n):
        node_clusters[i] = labels[i]

    # Noeuds internes
    for i, row in enumerate(Z):
        left, right = int(row[0]), int(row[1])
        cl_left = node_clusters.get(left)
        cl_right = node_clusters.get(right)
        if cl_left is not None and cl_left == cl_right and cl_left != -1:
            node_clusters[n + i] = cl_left
        else:
            node_clusters[n + i] = None

    return node_clusters


def generate_plot(
    embedding: np.ndarray,
    labels: np.ndarray,
    Z: np.ndarray,
    Z_clusters: np.ndarray | None,
    cluster_names: list[str],
    cluster_sizes: list[int],
    sra_names: list[str],
    lineage_name: str,
    n_samples: int,
    sil: float,
    feature_counts: dict,
    output_path: Path,
    dpi: int = 300,
):
    n_clusters = len(set(labels) - {-1})
    noise_count = int((labels == -1).sum())

    has_cluster_tree = Z_clusters is not None and len(cluster_names) >= 2

    subtitle_parts = [f"{feature_counts.get('spdi',0)} SPDIs"]
    if feature_counts.get("is", 0) > 0:
        subtitle_parts.append(f"{feature_counts['is']} IS")
    if feature_counts.get("rd", 0) > 0:
        subtitle_parts.append(f"{feature_counts['rd']} RD")
    features_str = " + ".join(subtitle_parts) + f" = {feature_counts.get('total',0)} features"

    title = f"{lineage_name}  —  {n_samples} SRAs"
    if n_clusters >= 2:
        title += f",  {n_clusters} clusters (silhouette={sil:.2f})"

    color_map, cmap = _build_cluster_colors(labels)
    node_cluster_map = _get_leaf_cluster_map(Z, labels)

    if has_cluster_tree:
        fig = plt.figure(figsize=(24, max(10, n_samples * 0.12)))
        gs = fig.add_gridspec(1, 3, width_ratios=[1.2, 1.5, 0.8], wspace=0.3)
        ax_tsne = fig.add_subplot(gs[0])
        ax_dendro = fig.add_subplot(gs[1])
        ax_mini = fig.add_subplot(gs[2])
    else:
        fig, (ax_tsne, ax_dendro) = plt.subplots(
            1, 2, figsize=(20, max(10, n_samples * 0.12)),
            gridspec_kw={"width_ratios": [1, 1.5]},
        )
        ax_mini = None

    fig.suptitle(title + "\n" + features_str, fontsize=13, fontweight="bold")

    # --- Panel 1 : t-SNE ---
    if n_clusters >= 2:
        unique_labels = sorted(set(labels) - {-1})
        for i, cl in enumerate(unique_labels):
            mask = labels == cl
            ax_tsne.scatter(
                embedding[mask, 0], embedding[mask, 1],
                c=[color_map[cl]], label=f"C{cl} (n={mask.sum()})",
                s=22, alpha=0.7, edgecolors="white", linewidths=0.3,
            )
        noise_mask = labels == -1
        if noise_mask.any():
            ax_tsne.scatter(
                embedding[noise_mask, 0], embedding[noise_mask, 1],
                c=[color_map[-1]], label=f"bruit (n={noise_count})",
                s=12, alpha=0.4, edgecolors="none",
            )
        ax_tsne.legend(fontsize=9, loc="best", markerscale=2, framealpha=0.8)
    else:
        ax_tsne.scatter(
            embedding[:, 0], embedding[:, 1],
            c="steelblue", s=22, alpha=0.7, edgecolors="white", linewidths=0.3,
        )

    if n_samples <= 200:
        for j, name in enumerate(sra_names):
            ax_tsne.annotate(
                name, (embedding[j, 0], embedding[j, 1]),
                fontsize=max(3, min(6, 400 // n_samples)),
                alpha=0.5, textcoords="offset points", xytext=(3, 3),
            )

    ax_tsne.set_xlabel("t-SNE 1", fontsize=11)
    ax_tsne.set_ylabel("t-SNE 2", fontsize=11)
    ax_tsne.set_title("t-SNE (Jaccard)", fontsize=11)
    ax_tsne.grid(True, alpha=0.15)

    # --- Panel 2 : dendrogramme complet, branches colorées par cluster ---
    n_leaves = len(labels)

    def link_color_func(k):
        """Colorie un lien si toutes les feuilles en dessous sont du même cluster."""
        cl = node_cluster_map.get(k)
        if cl is not None and cl != -1 and cl in color_map:
            r, g, b, a = color_map[cl]
            return matplotlib.colors.rgb2hex((r, g, b))
        return "#888888"

    leaf_font = max(4, min(8, 600 // n_samples))

    dendro_result = dendrogram(
        Z,
        ax=ax_dendro,
        orientation="right",
        labels=sra_names,
        leaf_font_size=leaf_font,
        link_color_func=link_color_func,
        leaf_rotation=0,
        above_threshold_color="#888888",
    )

    # Colorier les labels des feuilles par cluster
    leaf_colors = {}
    for idx, cl in enumerate(labels):
        r, g, b, a = color_map[cl]
        leaf_colors[sra_names[idx]] = matplotlib.colors.rgb2hex((r, g, b))

    for lbl in ax_dendro.get_ymajorticklabels():
        name = lbl.get_text()
        if name in leaf_colors:
            lbl.set_color(leaf_colors[name])
            lbl.set_fontweight("bold")
            lbl.set_fontsize(leaf_font)

    ax_dendro.set_title("Dendrogramme UPGMA (Jaccard)", fontsize=11)
    ax_dendro.set_xlabel("Distance Jaccard", fontsize=10)
    ax_dendro.spines["top"].set_visible(False)
    ax_dendro.spines["right"].set_visible(False)

    # --- Panel 3 : mini-dendrogramme des clusters ---
    if ax_mini is not None and has_cluster_tree:
        unique_labels = sorted(set(labels) - {-1})
        cluster_colors = [
            matplotlib.colors.rgb2hex(color_map[cl][:3])
            for cl in unique_labels
        ]

        def cluster_link_color(k):
            return "#444444"

        dendrogram(
            Z_clusters,
            ax=ax_mini,
            orientation="right",
            labels=cluster_names,
            leaf_font_size=11,
            link_color_func=cluster_link_color,
            leaf_rotation=0,
        )

        # Colorier les labels du mini-dendrogramme
        for i, lbl in enumerate(ax_mini.get_ymajorticklabels()):
            if i < len(cluster_colors):
                lbl.set_color(cluster_colors[i])
                lbl.set_fontweight("bold")
                lbl.set_fontsize(12)

        ax_mini.set_title("Relations entre clusters", fontsize=11)
        ax_mini.set_xlabel("Distance Jaccard", fontsize=10)
        ax_mini.spines["top"].set_visible(False)
        ax_mini.spines["right"].set_visible(False)

    plt.tight_layout()
    fig.savefig(str(output_path), dpi=dpi, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Étape 7 : dendrogramme HTML interactif (D3.js)
# ---------------------------------------------------------------------------

def _compute_node_variants(Z: np.ndarray, matrix: np.ndarray, n_spdi: int):
    """Pour chaque noeud (feuille + interne), calcule :
    - leaf_indices : set des indices de feuilles descendantes
    - core_count : nb de variants SPDI présents dans TOUS les descendants
    - exclusive_count : nb de variants core absents de tous les non-descendants

    Ne travaille que sur les n_spdi premières colonnes (SPDIs, pas IS/RD).
    """
    n = matrix.shape[0]
    spdi_matrix = matrix[:, :n_spdi]  # sous-matrice SPDI seulement
    all_indices = set(range(n))

    # leaf_indices et core_mask pour chaque noeud
    leaf_sets = {}  # node_id -> set of leaf indices
    core_masks = {}  # node_id -> boolean array (True = variant present in all descendants)

    # Feuilles
    for i in range(n):
        leaf_sets[i] = {i}
        core_masks[i] = spdi_matrix[i].astype(bool)

    # Noeuds internes (bottom-up)
    for i, row in enumerate(Z):
        left, right = int(row[0]), int(row[1])
        node_id = n + i
        leaf_sets[node_id] = leaf_sets[left] | leaf_sets[right]
        # Core = intersection : variant présent dans TOUS les descendants
        core_masks[node_id] = core_masks[left] & core_masks[right]

    # Calculer exclusive pour chaque noeud
    node_stats = {}
    for node_id in range(n + len(Z)):
        leaves = leaf_sets[node_id]
        core_mask = core_masks[node_id]
        core_count = int(core_mask.sum())

        # Exclusif = core ET absent de tous les non-descendants
        non_descendant = all_indices - leaves
        if non_descendant:
            nd_indices = sorted(non_descendant)
            # Un variant est exclusif s'il est core ET aucun non-descendant ne l'a
            non_desc_any = spdi_matrix[nd_indices].any(axis=0)
            exclusive_mask = core_mask & ~non_desc_any
            exclusive_count = int(exclusive_mask.sum())
        else:
            # Racine : tous les core sont "exclusifs" (trivial)
            exclusive_count = core_count

        node_stats[node_id] = {
            "core": core_count,
            "exclusive": exclusive_count,
            "leaves": len(leaves),
        }

    return node_stats


def _linkage_to_tree(Z: np.ndarray, sra_names: list[str], labels: np.ndarray,
                     color_map: dict, node_stats: dict) -> dict:
    """Convertit la matrice de linkage scipy en arbre JSON pour D3.js."""
    n = len(sra_names)
    nodes = {}

    # Feuilles
    for i in range(n):
        cl = int(labels[i])
        r, g, b, a = color_map.get(cl, (0.5, 0.5, 0.5, 1.0))
        stats = node_stats.get(i, {})
        nodes[i] = {
            "name": sra_names[i],
            "cluster": cl,
            "color": matplotlib.colors.rgb2hex((r, g, b)),
            "dist": 0.0,
            "size": 1,
            "core": stats.get("core", 0),
            "exclusive": stats.get("exclusive", 0),
        }

    # Noeuds internes
    for i, row in enumerate(Z):
        left, right, dist, count = int(row[0]), int(row[1]), float(row[2]), int(row[3])
        left_node = nodes[left]
        right_node = nodes[right]
        node_id = n + i

        cl_left = left_node.get("cluster")
        cl_right = right_node.get("cluster")
        if cl_left == cl_right and cl_left != -1:
            cl = cl_left
        else:
            cl = -1

        r, g, b, a = color_map.get(cl, (0.5, 0.5, 0.5, 1.0))
        stats = node_stats.get(node_id, {})
        nodes[node_id] = {
            "name": f"n{node_id}",
            "cluster": cl,
            "color": matplotlib.colors.rgb2hex((r, g, b)) if cl != -1 else "#888888",
            "dist": round(dist, 4),
            "size": count,
            "core": stats.get("core", 0),
            "exclusive": stats.get("exclusive", 0),
            "children": [left_node, right_node],
        }

    root = nodes[n + len(Z) - 1]
    return root


def _compute_initial_depth(root: dict, n_clusters: int) -> int:
    """Calcule la profondeur à laquelle ouvrir pour voir les clusters séparés."""
    # On déplie jusqu'à ce qu'on ait au moins n_clusters branches visibles
    # Heuristique : profondeur = 2 (montre les grands clades)
    return 2


def generate_html(
    Z: np.ndarray,
    labels: np.ndarray,
    embedding: np.ndarray,
    matrix: np.ndarray,
    sra_names: list[str],
    lineage_name: str,
    feature_counts: dict,
    sil: float,
    output_path: Path,
):
    """Génère un fichier HTML avec dendrogramme interactif D3.js + t-SNE."""
    color_map, _ = _build_cluster_colors(labels)
    n_spdi = feature_counts.get("spdi", 0)
    node_stats = _compute_node_variants(Z, matrix, n_spdi)
    tree = _linkage_to_tree(Z, sra_names, labels, color_map, node_stats)

    # Données SPDI sparse par SRA (indices des colonnes SPDI à 1)
    spdi_matrix = matrix[:, :n_spdi]
    spdi_sets = {}
    for i, name in enumerate(sra_names):
        spdi_sets[name] = [int(j) for j in np.where(spdi_matrix[i] == 1)[0]]
    n_clusters = len(set(labels) - {-1})
    n_samples = len(sra_names)
    initial_depth = _compute_initial_depth(tree, n_clusters)

    # Préparer les données t-SNE pour le scatter plot
    tsne_data = []
    for i in range(n_samples):
        cl = int(labels[i])
        r, g, b, a = color_map.get(cl, (0.5, 0.5, 0.5, 1.0))
        tsne_data.append({
            "x": round(float(embedding[i, 0]), 3),
            "y": round(float(embedding[i, 1]), 3),
            "name": sra_names[i],
            "cluster": cl,
            "color": matplotlib.colors.rgb2hex((r, g, b)),
        })

    tree_json = json.dumps(tree)
    tsne_json = json.dumps(tsne_data)
    spdi_json = json.dumps(spdi_sets)

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>Clade Finder — {lineage_name}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
         background: #fafafa; color: #333; }}
  h1 {{ text-align: center; padding: 10px 0 2px; font-size: 17px; }}
  .subtitle {{ text-align: center; color: #888; font-size: 12px; margin-bottom: 4px; }}
  .status {{ text-align: center; font-size: 12px; color: #666; padding: 2px 0; }}
  .status strong {{ color: #c00; }}
  .container {{ display: flex; width: 100%; height: calc(100vh - 80px); }}
  .panel {{ flex: 1; overflow: auto; border-right: 1px solid #ddd; position: relative; }}
  .panel:last-child {{ border-right: none; }}
  .panel-title {{ text-align: center; font-size: 12px; font-weight: 600; color: #555;
                  padding: 4px 0; border-bottom: 1px solid #eee; background: #f5f5f5; }}
  #tsne-panel {{ flex: 0 0 32%; }}
  #tsne-svg {{ width: 100%; height: calc(100% - 28px); }}
  .dot {{ cursor: pointer; transition: r 0.15s; }}
  .dot.highlighted {{ stroke: #000; stroke-width: 2.5px; }}
  .dot.excluded {{ opacity: 0.12; }}
  .tooltip {{ position: absolute; background: rgba(0,0,0,0.85); color: #fff; padding: 4px 8px;
              border-radius: 4px; font-size: 11px; pointer-events: none; display: none; z-index: 10; }}
  #dendro-panel {{ flex: 0 0 68%; }}
  .node circle {{ cursor: pointer; stroke: #fff; stroke-width: 1.5px; }}
  .node text {{ font-size: 11px; }}
  .node .sra-label {{ cursor: default; }}
  .node .sra-label.excluded {{ text-decoration: line-through; opacity: 0.35; }}
  .node .remove-btn {{ cursor: pointer; fill: #c00; font-size: 13px; font-weight: bold; opacity: 0.4; }}
  .node .remove-btn:hover {{ opacity: 1; }}
  .link {{ fill: none; stroke: #ccc; stroke-width: 1.5px; }}
  .controls {{ text-align: center; padding: 4px; background: #f5f5f5; border-bottom: 1px solid #eee;
               display: flex; justify-content: center; gap: 3px; flex-wrap: wrap; }}
  .controls button {{ padding: 3px 10px; font-size: 11px; cursor: pointer;
                      border: 1px solid #bbb; border-radius: 3px; background: #fff; }}
  .controls button:hover {{ background: #e8e8e8; }}
  .controls button:disabled {{ opacity: 0.35; cursor: default; }}
  .controls .sep {{ width: 1px; background: #ccc; margin: 0 4px; }}
</style>
</head>
<body>
<h1>{lineage_name} — <span id="active-count">{n_samples}</span>/{n_samples} SRAs, {n_clusters} clusters (silhouette={sil:.2f})</h1>
<div class="subtitle">{feature_counts.get('spdi',0)} SPDIs + {feature_counts.get('is',0)} IS + {feature_counts.get('rd',0)} RD = {feature_counts.get('total',0)} features</div>
<div class="status" id="status-bar"></div>

<div class="container">
  <div class="panel" id="tsne-panel">
    <div class="panel-title">t-SNE (Jaccard)</div>
    <svg id="tsne-svg"></svg>
    <div class="tooltip" id="tsne-tooltip"></div>
  </div>
  <div class="panel" id="dendro-panel">
    <div class="controls">
      <button onclick="expandAll()">+ Tout</button>
      <button onclick="collapseAll()">- Tout</button>
      <button onclick="expandLevel()">+ 1 niv</button>
      <button onclick="collapseLevel()">- 1 niv</button>
      <div class="sep"></div>
      <button onclick="undo()" id="btn-undo" disabled>Undo</button>
      <button onclick="redo()" id="btn-redo" disabled>Redo</button>
      <button onclick="resetAll()" id="btn-reset" disabled>Reset</button>
    </div>
    <div class="panel-title">Dendrogramme — clic noeud = deplier, <span style="color:#c00">x</span> = exclure SRA</div>
    <svg id="dendro-svg"></svg>
  </div>
</div>

<script src="https://d3js.org/d3.v7.min.js"></script>
<script>
const treeData = {tree_json};
const tsneData = {tsne_json};
const spdiSets = {spdi_json};
const nSpdi = {n_spdi};
const totalSamples = {n_samples};

// ---- STATE ----
const excludedSet = new Set();
const undoStack = [];
const redoStack = [];

// ---- t-SNE ----
const tPanel = document.getElementById('tsne-panel');
const tSvg = d3.select('#tsne-svg');
const tooltip = d3.select('#tsne-tooltip');
const tW = tPanel.clientWidth, tH = tPanel.clientHeight - 28;
tSvg.attr('viewBox', `0 0 ${{tW}} ${{tH}}`);
const pad = 30;
const xSc = d3.scaleLinear().domain(d3.extent(tsneData, d=>d.x)).range([pad+20, tW-pad]);
const ySc = d3.scaleLinear().domain(d3.extent(tsneData, d=>d.y)).range([tH-pad, pad+10]);

const dots = tSvg.selectAll('.dot').data(tsneData).enter().append('circle')
  .attr('class','dot').attr('cx',d=>xSc(d.x)).attr('cy',d=>ySc(d.y))
  .attr('r',4.5).attr('fill',d=>d.color).attr('opacity',0.8)
  .attr('data-name',d=>d.name)
  .on('mouseover',function(ev,d){{
    tooltip.style('display','block').html(`${{d.name}}<br>C${{d.cluster}}`)
      .style('left',(ev.offsetX+10)+'px').style('top',(ev.offsetY-10)+'px');
    d3.select(this).attr('r',8);
  }}).on('mouseout',function(){{
    tooltip.style('display','none'); d3.select(this).attr('r',4.5);
  }});
tSvg.append('g').attr('transform',`translate(0,${{tH-pad}})`).call(d3.axisBottom(xSc).ticks(5))
  .selectAll('text').style('font-size','9px');
tSvg.append('g').attr('transform',`translate(${{pad+20}},0)`).call(d3.axisLeft(ySc).ticks(5))
  .selectAll('text').style('font-size','9px');

function highlightDots(names, on) {{
  tSvg.selectAll('.dot').classed('highlighted', false).attr('r',4.5);
  if (on && names && names.length) {{
    const s = new Set(names);
    tSvg.selectAll('.dot').filter(d => s.has(d.name))
      .classed('highlighted',true).attr('r',9).raise();
  }}
}}

// Collecte toutes les feuilles (noms SRA) sous un noeud D3
function getLeafNames(d) {{
  if (isLeaf(d)) return [d.data.name];
  const ch = d.children || d._children || [];
  return ch.flatMap(c => getLeafNames(c));
}}
function updateDots() {{
  tSvg.selectAll('.dot').classed('excluded', d => excludedSet.has(d.name));
}}

// ---- STATS RECOMPUTATION ----
function recomputeStats() {{
  // Global freq
  const gFreq = new Uint16Array(nSpdi);
  let gCount = 0;
  for (const [name, idxs] of Object.entries(spdiSets)) {{
    if (excludedSet.has(name)) continue;
    gCount++;
    for (const j of idxs) gFreq[j]++;
  }}

  function calc(node) {{
    const ch = node.children || node._children;
    if (!ch) {{
      // Leaf
      const nm = node.data.name;
      if (excludedSet.has(nm)) {{
        node.data.activeSize = 0; node.data.core = 0; node.data.exclusive = 0;
        return new Uint16Array(nSpdi);
      }}
      const f = new Uint16Array(nSpdi);
      const s = spdiSets[nm] || [];
      for (const j of s) f[j] = 1;
      node.data.activeSize = 1;
      node.data.core = s.length;
      let e = 0; for (const j of s) {{ if (gFreq[j] === 1) e++; }}
      node.data.exclusive = e;
      return f;
    }}
    const fs = ch.map(c => calc(c));
    const tot = ch.reduce((s,c) => s + (c.data.activeSize||0), 0);
    const m = new Uint16Array(nSpdi);
    for (const f of fs) {{ for (let j=0;j<nSpdi;j++) m[j]+=f[j]; }}
    let core=0, excl=0;
    if (tot > 0) {{
      for (let j=0;j<nSpdi;j++) {{
        if (m[j]===tot) {{ core++; if (gFreq[j]===tot) excl++; }}
      }}
    }}
    node.data.activeSize = tot; node.data.core = core; node.data.exclusive = excl;
    return m;
  }}
  calc(root);
  document.getElementById('active-count').textContent = gCount;
}}

// ---- EXCLUDE / UNDO / REDO ----
// names peut être un string ou un array
function excludeSRAs(names) {{
  const arr = Array.isArray(names) ? names : [names];
  const added = arr.filter(n => !excludedSet.has(n));
  if (!added.length) return;
  added.forEach(n => excludedSet.add(n));
  undoStack.push(added);  // un undo = un groupe
  redoStack.length = 0;
  refresh();
}}
function undo() {{
  if (!undoStack.length) return;
  const group = undoStack.pop();
  group.forEach(n => excludedSet.delete(n));
  redoStack.push(group);
  refresh();
}}
function redo() {{
  if (!redoStack.length) return;
  const group = redoStack.pop();
  group.forEach(n => excludedSet.add(n));
  undoStack.push(group);
  refresh();
}}
function resetAll() {{
  excludedSet.clear();
  undoStack.length = 0;
  redoStack.length = 0;
  refresh();
}}
function refresh() {{
  recomputeStats();
  updateDots();
  update(root);
  document.getElementById('btn-undo').disabled = !undoStack.length;
  document.getElementById('btn-redo').disabled = !redoStack.length;
  document.getElementById('btn-reset').disabled = !excludedSet.size;
  const st = document.getElementById('status-bar');
  st.innerHTML = excludedSet.size
    ? `<strong>${{excludedSet.size}} SRA(s) exclus</strong> : ${{[...excludedSet].join(', ')}}`
    : '';
}}

// ---- DENDROGRAM ----
const dPanel = document.getElementById('dendro-panel');
const margin = {{top:10, right:200, bottom:10, left:40}};
let dW = dPanel.clientWidth - margin.left - margin.right;
const dSvg = d3.select('#dendro-svg').attr('width', dPanel.clientWidth);
const g = dSvg.append('g').attr('transform',`translate(${{margin.left}},${{margin.top}})`);

const root = d3.hierarchy(treeData, d => d.children);
root.x0 = 0; root.y0 = 0;

function collapseAtDepth(n, mx, d) {{
  if (n.children) {{
    if (d>=mx) {{ n._children=n.children; n.children=null; }}
    else n.children.forEach(c=>collapseAtDepth(c,mx,d+1));
  }}
}}
collapseAtDepth(root, 2, 0);

let nodeId = 0;
const duration = 350;

function countLeaves(n) {{
  if(!n.children && !n._children) return 1;
  return (n.children||n._children||[]).reduce((s,c)=>s+countLeaves(c),0);
}}
function visibleLeaves(n) {{
  if(!n.children) return 1;
  return n.children.reduce((s,c)=>s+visibleLeaves(c),0);
}}

function isLeaf(d) {{ return !d.children && !d._children; }}

function nodeLabel(d) {{
  if (isLeaf(d)) return '';  // handled by sra-label
  const sz = d.data.activeSize ?? d.data.size;
  const core = d.data.core || 0;
  const excl = d.data.exclusive || 0;
  return `${{sz}} SRAs | core: ${{core}} | excl: ${{excl}}`;
}}

function update(source) {{
  const nVis = visibleLeaves(root);
  const rh = Math.max(16, Math.min(22, 500/nVis));
  const treeH = nVis * rh;
  dSvg.attr('height', treeH + margin.top + margin.bottom + 40);
  dW = dPanel.clientWidth - margin.left - margin.right;

  const layout = d3.tree().size([treeH, dW]);
  layout(root);
  const nodes = root.descendants();
  const links = root.links();

  // --- NODES ---
  const nd = g.selectAll('g.node').data(nodes, d => d.id||(d.id=++nodeId));

  const enter = nd.enter().append('g').attr('class','node')
    .attr('transform', `translate(${{source.y0||0}},${{source.x0||0}})`);

  // Circle
  enter.append('circle').attr('r',1e-6)
    .style('fill', d => d._children ? d.data.color||'#888' : '#fff')
    .style('stroke', d => d.data.color||'#888')
    .on('click', (ev, d) => {{
      ev.stopPropagation();
      if (d.children) {{ d._children=d.children; d.children=null; }}
      else if (d._children) {{ d.children=d._children; d._children=null; }}
      update(d);
    }})
    .on('mouseover', (ev, d) => highlightDots(getLeafNames(d), true))
    .on('mouseout', () => highlightDots([], false));

  // Label noeud interne
  const intEnter = enter.filter(d => !isLeaf(d));

  intEnter.append('text')
    .attr('class','node-label').attr('dy','.35em').attr('x',-10).attr('text-anchor','end')
    .style('fill', d => d.data.color||'#333').style('font-size','10px')
    .style('cursor','default')
    .on('mouseover', (ev,d) => highlightDots(getLeafNames(d), true))
    .on('mouseout', () => highlightDots([], false));

  // Bouton X sur noeud interne (exclure tout le sous-arbre)
  intEnter.append('text').attr('class','remove-btn').attr('dy','.35em')
    .attr('x', -10).attr('text-anchor','end')
    .text('x  ')
    .on('click', (ev,d) => {{
      ev.stopPropagation();
      const leaves = getLeafNames(d).filter(n => !excludedSet.has(n));
      if (leaves.length) excludeSRAs(leaves);
    }});

  // Clic droit sur noeud interne : copier les SRA descendants
  intEnter.on('contextmenu', (ev,d) => {{
    ev.preventDefault();
    const leaves = getLeafNames(d).filter(n => !excludedSet.has(n));
    const txt = leaves.join('\\n');
    navigator.clipboard.writeText(txt).then(() => {{
      const st = document.getElementById('status-bar');
      st.innerHTML = `<span style="color:green">${{leaves.length}} SRA(s) copies dans le presse-papier</span>`;
      setTimeout(() => refresh(), 2000);  // restore status bar
    }});
  }});

  // Label feuille (SRA)
  const leafEnter = enter.filter(d => isLeaf(d));

  leafEnter.append('text').attr('class','sra-label').attr('dy','.35em').attr('x',10)
    .attr('text-anchor','start')
    .text(d => d.data.name)
    .style('fill', d => d.data.color||'#333')
    .style('font-size','11px').style('font-weight','bold')
    .on('mouseover', (ev,d) => highlightDots([d.data.name], true))
    .on('mouseout', () => highlightDots([], false));

  // Bouton X feuille
  leafEnter.append('text').attr('class','remove-btn').attr('dy','.35em')
    .attr('text-anchor','start')
    .text('x')
    .on('click', (ev,d) => {{ ev.stopPropagation(); excludeSRAs(d.data.name); }});

  // --- UPDATE ---
  const merged = enter.merge(nd);
  merged.transition().duration(duration)
    .attr('transform', d => `translate(${{d.y}},${{d.x}})`);

  merged.select('circle')
    .attr('r', d => isLeaf(d) ? 3 : 5)
    .style('fill', d => d._children ? d.data.color||'#888' : '#fff')
    .style('stroke', d => d.data.color||'#888');

  merged.select('.node-label').text(nodeLabel);

  // Update leaf labels
  merged.select('.sra-label')
    .classed('excluded', d => excludedSet.has(d.data.name))
    .text(d => d.data.name);

  // Position du bouton X après le label SRA (feuilles seulement)
  merged.filter(d => isLeaf(d)).select('.remove-btn')
    .each(function(d) {{
      const lbl = d3.select(this.parentNode).select('.sra-label').node();
      const w = lbl ? lbl.getComputedTextLength() : 60;
      d3.select(this).attr('x', 10 + w + 6);
    }});

  // --- EXIT ---
  const exit = nd.exit().transition().duration(duration)
    .attr('transform', `translate(${{source.y||0}},${{source.x||0}})`).remove();
  exit.select('circle').attr('r',1e-6);
  exit.selectAll('text').style('fill-opacity',1e-6);

  // --- LINKS ---
  const lk = g.selectAll('path.link').data(links, d => d.target.id);
  const lkEnter = lk.enter().insert('path','g').attr('class','link')
    .attr('d', d => {{ const o={{x:source.x0||0,y:source.y0||0}}; return diag(o,o); }})
    .style('stroke', d => d.target.data.color||'#ccc');
  lkEnter.merge(lk).transition().duration(duration)
    .attr('d', d => diag(d.source, d.target))
    .style('stroke', d => d.target.data.color||'#ccc');
  lk.exit().transition().duration(duration)
    .attr('d', d => {{ const o={{x:source.x||0,y:source.y||0}}; return diag(o,o); }}).remove();

  nodes.forEach(d => {{ d.x0=d.x; d.y0=d.y; }});
}}

function diag(s,d) {{
  return `M ${{s.y}} ${{s.x}} C ${{(s.y+d.y)/2}} ${{s.x}}, ${{(s.y+d.y)/2}} ${{d.x}}, ${{d.y}} ${{d.x}}`;
}}

update(root);

// ---- TREE CONTROLS ----
function expandAll() {{
  (function ex(n){{ if(n._children){{n.children=n._children;n._children=null;}} if(n.children)n.children.forEach(ex); }})(root);
  update(root);
}}
function collapseAll() {{
  function cl(n){{ if(n.children){{n._children=n.children;n._children.forEach(cl);n.children=null;}} }}
  if(root.children) root.children.forEach(cl);
  update(root);
}}
function expandLevel() {{
  function find(n,d) {{
    if(n._children) return [{{node:n,depth:d}}];
    if(n.children) return n.children.flatMap(c=>find(c,d+1));
    return [];
  }}
  const cs = find(root,0);
  if(!cs.length) return;
  const mn = Math.min(...cs.map(c=>c.depth));
  cs.filter(c=>c.depth===mn).forEach(c => {{
    c.node.children = c.node._children; c.node._children = null;
    c.node.children.forEach(ch => {{ if(ch.children){{ch._children=ch.children;ch.children=null;}} }});
  }});
  update(root);
}}
function collapseLevel() {{
  function find(n,d) {{
    if(!n.children) return [];
    let sub = n.children.flatMap(c=>find(c,d+1));
    if(!sub.length && d>0) return [{{node:n,depth:d}}];
    return sub;
  }}
  const es = find(root,0);
  if(!es.length) return;
  const mx = Math.max(...es.map(c=>c.depth));
  es.filter(c=>c.depth===mx).forEach(c => {{ c.node._children=c.node.children; c.node.children=null; }});
  update(root);
}}
</script>
</body>
</html>"""

    with open(output_path, "w") as f:
        f.write(html)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Clade finder: t-SNE + HDBSCAN sur lignée MTBC")
    parser.add_argument("lineage_dir", type=Path, help="Répertoire de lignée (bdd/actuelle/L4.x/)")
    parser.add_argument("--min-cluster-size", type=int, default=None)
    parser.add_argument("--perplexity", type=float, default=None)
    parser.add_argument("--dpi", type=int, default=300)
    parser.add_argument("--no-spdi", action="store_true", help="Exclure les SPDIs")
    parser.add_argument("--no-is", action="store_true", help="Exclure les IS")
    parser.add_argument("--no-rd", action="store_true", help="Exclure les RD")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--ref", default="NC_000962.3", help="ID référence génome")
    parser.add_argument("--min-freq", type=float, default=0.02, help="Fréq min SPDI (défaut 0.02)")
    parser.add_argument("--max-freq", type=float, default=0.98, help="Fréq max SPDI (défaut 0.98)")
    args = parser.parse_args()

    lineage_dir = args.lineage_dir.resolve()
    if not lineage_dir.is_dir():
        print(f"ERREUR: {lineage_dir} n'est pas un répertoire.", file=sys.stderr)
        sys.exit(1)

    lineage_name = lineage_dir.name
    output_path = args.output or (lineage_dir / "clade_finder.png")

    # Phase 0 : scan
    print(f"Scan de {lineage_dir}...", file=sys.stderr)
    samples = scan_lineage_dir(lineage_dir, args.ref)
    if len(samples) < 5:
        print(f"ERREUR: seulement {len(samples)} SRAs avec données. Minimum 5.", file=sys.stderr)
        sys.exit(1)

    source_counts = Counter(s["source"] for s in samples)
    print(f"SRAs chargés: {len(samples)} ({dict(source_counts)})", file=sys.stderr)

    # Phase 1 : matrice de features
    print("Construction de la matrice de features...", file=sys.stderr)
    matrix, feature_names, feature_counts = build_feature_matrix(
        samples,
        use_spdi=not args.no_spdi,
        use_is=not args.no_is,
        use_rd=not args.no_rd,
        min_freq=args.min_freq,
        max_freq=args.max_freq,
    )
    print(
        f"Matrice: {matrix.shape[0]} SRAs × {matrix.shape[1]} features "
        f"(SPDI:{feature_counts['spdi']} IS:{feature_counts['is']} RD:{feature_counts['rd']})",
        file=sys.stderr,
    )

    # Phase 2 : t-SNE
    print("t-SNE...", file=sys.stderr)
    embedding, perplexity_used = run_tsne(matrix, args.perplexity)

    # Phase 3 : HDBSCAN
    print("HDBSCAN...", file=sys.stderr)
    labels, probs, sil, mcs_used = run_hdbscan(embedding, args.min_cluster_size)
    n_clusters = len(set(labels) - {-1})
    noise_count = int((labels == -1).sum())
    print(f"Clusters: {n_clusters}, bruit: {noise_count}, silhouette: {sil:.3f}", file=sys.stderr)

    # Phase 4 : clustering hiérarchique
    print("Clustering hierarchique...", file=sys.stderr)
    Z, _ = run_hierarchical(matrix)
    Z_clusters, cluster_names, cluster_sizes = build_cluster_dendrogram(matrix, labels)

    # Phase 5 : PNG
    sra_names = [s["sra"] for s in samples]
    generate_plot(
        embedding, labels, Z, Z_clusters, cluster_names, cluster_sizes,
        sra_names, lineage_name,
        len(samples), sil, feature_counts, output_path, args.dpi,
    )
    print(f"PNG sauvegardé: {output_path}", file=sys.stderr)

    # Phase 6 : HTML interactif
    html_path = output_path.with_suffix(".html")
    generate_html(Z, labels, embedding, matrix, sra_names, lineage_name,
                  feature_counts, sil, html_path)
    print(f"HTML interactif: {html_path}", file=sys.stderr)

    # Phase 7 : JSON résumé sur stdout
    cluster_sizes = {}
    for cl in sorted(set(labels) - {-1}):
        cluster_sizes[str(cl)] = int((labels == cl).sum())

    summary = {
        "lineage": lineage_name,
        "n_samples": len(samples),
        "features": feature_counts,
        "tsne": {"perplexity": round(perplexity_used, 1)},
        "hdbscan": {
            "min_cluster_size": mcs_used,
            "n_clusters": n_clusters,
            "noise_count": noise_count,
            "noise_ratio": round(noise_count / len(samples), 3),
            "silhouette_score": round(sil, 3),
            "cluster_sizes": cluster_sizes,
        },
        "output_png": str(output_path),
        "output_html": str(html_path),
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
