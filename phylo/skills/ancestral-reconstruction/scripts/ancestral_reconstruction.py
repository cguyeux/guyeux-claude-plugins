#!/usr/bin/env python3
"""
Ancestral Geographic State Reconstruction for MTBC Phylogenies

Reconstruct ancestral locations on phylogenetic trees using parsimony (Fitch),
maximum likelihood (MPPA-style marginal posteriors), or stochastic mapping.
Export iTOL annotations and BEAST DTA XML.

Usage:
    python3 ancestral_reconstruction.py tree.nwk metadata.csv --method ml -o results.csv
    python3 ancestral_reconstruction.py tree.nwk metadata.csv --method stochastic \
        --migration-counts migrations.csv
    python3 ancestral_reconstruction.py tree.nwk metadata.csv --itol itol_prefix
"""

import argparse
import json
import sys
from collections import defaultdict

import numpy as np
import pandas as pd
from scipy.linalg import expm

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    HAS_PLOT = True
except ImportError:
    HAS_PLOT = False

try:
    import dendropy
    HAS_DENDROPY = True
except ImportError:
    HAS_DENDROPY = False


# ---------------------------------------------------------------------------
# Tree I/O
# ---------------------------------------------------------------------------

class SimpleNode:
    """Minimal tree node for when dendropy is unavailable."""

    def __init__(self, name=None, branch_length=0.0):
        self.name = name
        self.branch_length = branch_length
        self.children = []
        self.parent = None
        self._id = id(self)

    @property
    def is_leaf(self):
        return len(self.children) == 0

    def iter_postorder(self):
        for child in self.children:
            yield from child.iter_postorder()
        yield self

    def iter_preorder(self):
        yield self
        for child in self.children:
            yield from child.iter_preorder()

    def iter_leaves(self):
        for node in self.iter_postorder():
            if node.is_leaf:
                yield node


def _parse_newick_simple(newick_str: str) -> SimpleNode:
    """Parse a Newick string into a SimpleNode tree (no dependencies)."""
    newick_str = newick_str.strip().rstrip(";").strip()
    pos = [0]

    def _read_node():
        node = SimpleNode()
        if newick_str[pos[0]] == "(":
            pos[0] += 1  # skip '('
            child = _read_node()
            child.parent = node
            node.children.append(child)
            while newick_str[pos[0]] == ",":
                pos[0] += 1  # skip ','
                child = _read_node()
                child.parent = node
                node.children.append(child)
            pos[0] += 1  # skip ')'

        # read name
        name_chars = []
        while pos[0] < len(newick_str) and newick_str[pos[0]] not in (",", ")", ":", ";"):
            name_chars.append(newick_str[pos[0]])
            pos[0] += 1
        node.name = "".join(name_chars).strip() or None

        # read branch length
        if pos[0] < len(newick_str) and newick_str[pos[0]] == ":":
            pos[0] += 1
            bl_chars = []
            while pos[0] < len(newick_str) and newick_str[pos[0]] not in (",", ")", ";"):
                bl_chars.append(newick_str[pos[0]])
                pos[0] += 1
            try:
                node.branch_length = float("".join(bl_chars))
            except ValueError:
                node.branch_length = 0.0

        return node

    return _read_node()


def load_tree(tree_path: str):
    """Load a Newick tree. Returns (tree_root, is_dendropy)."""
    if HAS_DENDROPY:
        tree = dendropy.Tree.get(path=tree_path, schema="newick")
        # Assign internal node labels if missing
        for i, node in enumerate(tree.preorder_node_iter()):
            if node.taxon is None and not node.is_leaf():
                node.label = node.label or f"N{i}"
        return tree, True

    with open(tree_path) as f:
        newick = f.read().strip()
    root = _parse_newick_simple(newick)
    # Assign internal node names
    counter = [0]
    for node in root.iter_preorder():
        if not node.is_leaf and not node.name:
            node.name = f"N{counter[0]}"
            counter[0] += 1
    return root, False


def get_leaves(tree, is_dendropy: bool) -> list:
    if is_dendropy:
        return [(leaf.taxon.label, leaf) for leaf in tree.leaf_node_iter()]
    return [(leaf.name, leaf) for leaf in tree.iter_leaves()]


def iter_postorder(tree, is_dendropy: bool):
    if is_dendropy:
        return tree.postorder_node_iter()
    return tree.iter_postorder()


def iter_preorder(tree, is_dendropy: bool):
    if is_dendropy:
        return tree.preorder_node_iter()
    return tree.iter_preorder()


def node_name(node, is_dendropy: bool) -> str:
    if is_dendropy:
        if node.taxon:
            return node.taxon.label
        return node.label or str(id(node))
    return node.name or str(node._id)


def node_is_leaf(node, is_dendropy: bool) -> bool:
    if is_dendropy:
        return node.is_leaf()
    return node.is_leaf


def node_children(node, is_dendropy: bool) -> list:
    if is_dendropy:
        return node.child_nodes()
    return node.children


def node_branch_length(node, is_dendropy: bool) -> float:
    if is_dendropy:
        return node.edge_length or 0.0
    return node.branch_length or 0.0


# ---------------------------------------------------------------------------
# Parsimony — Fitch algorithm
# ---------------------------------------------------------------------------

def fitch_parsimony(tree, is_dendropy: bool, leaf_states: dict, states: list) -> dict:
    """Fitch parsimony reconstruction. Returns {node_name: set_of_states}."""
    state_sets = {}

    # Bottom-up: assign state sets
    for node in iter_postorder(tree, is_dendropy):
        nname = node_name(node, is_dendropy)
        if node_is_leaf(node, is_dendropy):
            s = leaf_states.get(nname)
            state_sets[nname] = {s} if s else set(states)
        else:
            children = node_children(node, is_dendropy)
            child_sets = [state_sets[node_name(c, is_dendropy)] for c in children]
            intersection = child_sets[0]
            for cs in child_sets[1:]:
                intersection = intersection & cs
            if intersection:
                state_sets[nname] = intersection
            else:
                union = set()
                for cs in child_sets:
                    union = union | cs
                state_sets[nname] = union

    # Top-down: resolve ambiguities
    resolved = {}
    for node in iter_preorder(tree, is_dendropy):
        nname = node_name(node, is_dendropy)
        if node.parent is None if not is_dendropy else node.parent_node is None:
            # Root: pick most frequent state
            ss = state_sets[nname]
            resolved[nname] = _pick_most_frequent(ss, leaf_states)
        else:
            parent_node = node.parent if not is_dendropy else node.parent_node
            parent_state = resolved[node_name(parent_node, is_dendropy)]
            ss = state_sets[nname]
            if parent_state in ss:
                resolved[nname] = parent_state
            else:
                resolved[nname] = _pick_most_frequent(ss, leaf_states)

    return resolved


def _pick_most_frequent(state_set: set, leaf_states: dict) -> str:
    """Pick the most frequent state from a set based on leaf frequencies."""
    counts = defaultdict(int)
    for s in leaf_states.values():
        if s in state_set:
            counts[s] += 1
    if counts:
        return max(counts, key=counts.get)
    return next(iter(state_set))


# ---------------------------------------------------------------------------
# ML — Marginal posterior probabilities (MPPA-style)
# ---------------------------------------------------------------------------

def build_rate_matrix(states: list, model: str = "F81", freqs: np.ndarray = None) -> np.ndarray:
    """Build a rate matrix Q for the given model."""
    n = len(states)
    if model == "equal":
        Q = np.ones((n, n)) / (n - 1)
        np.fill_diagonal(Q, 0)
        np.fill_diagonal(Q, -Q.sum(axis=1))
        return Q

    # F81: off-diagonal proportional to stationary frequencies
    if freqs is None:
        freqs = np.ones(n) / n
    Q = np.outer(np.ones(n), freqs)
    np.fill_diagonal(Q, 0)
    np.fill_diagonal(Q, -Q.sum(axis=1))
    # Normalize so mean rate = 1
    mean_rate = -np.sum(freqs * np.diag(Q))
    if mean_rate > 0:
        Q /= mean_rate
    return Q


def ml_reconstruction(
    tree, is_dendropy: bool, leaf_states: dict, states: list, model: str = "F81"
) -> dict:
    """ML marginal posterior probabilities at each internal node.

    Returns {node_name: {state: probability}}.
    """
    n = len(states)
    state_idx = {s: i for i, s in enumerate(states)}

    # Estimate frequencies from tips
    freq_counts = defaultdict(int)
    for s in leaf_states.values():
        freq_counts[s] += 1
    total = sum(freq_counts.values())
    freqs = np.array([freq_counts.get(s, 0) / total for s in states])
    freqs = np.maximum(freqs, 1e-6)
    freqs /= freqs.sum()

    Q = build_rate_matrix(states, model, freqs)

    # Conditional likelihoods (bottom-up)
    cond_lik = {}  # node_name -> array of shape (n,)

    for node in iter_postorder(tree, is_dendropy):
        nname = node_name(node, is_dendropy)
        if node_is_leaf(node, is_dendropy):
            lik = np.zeros(n)
            s = leaf_states.get(nname)
            if s and s in state_idx:
                lik[state_idx[s]] = 1.0
            else:
                lik[:] = 1.0  # Unknown: all states equally likely
            cond_lik[nname] = lik
        else:
            lik = np.ones(n)
            for child in node_children(node, is_dendropy):
                bl = max(node_branch_length(child, is_dendropy), 1e-8)
                P = expm(Q * bl)
                child_lik = cond_lik[node_name(child, is_dendropy)]
                # Sum over child states weighted by transition probs
                lik *= P @ child_lik
            cond_lik[nname] = lik

    # Marginal posteriors (top-down)
    marginals = {}

    for node in iter_preorder(tree, is_dendropy):
        nname = node_name(node, is_dendropy)
        parent_node = node.parent if not is_dendropy else node.parent_node

        if parent_node is None:
            # Root: prior * conditional likelihood
            post = freqs * cond_lik[nname]
        else:
            parent_name = node_name(parent_node, is_dendropy)
            bl = max(node_branch_length(node, is_dendropy), 1e-8)
            P = expm(Q * bl)

            # Marginal at this node = sum_parent_state P(parent_state) * P(state|parent) * L(data_below|state)
            parent_post = marginals[parent_name]
            parent_arr = np.array([parent_post.get(s, 0) for s in states])

            post = np.zeros(n)
            for j in range(n):
                post[j] = cond_lik[nname][j] * np.sum(parent_arr * P[:, j])

        # Normalize
        total_p = post.sum()
        if total_p > 0:
            post /= total_p

        marginals[nname] = {states[i]: float(post[i]) for i in range(n)}

    return marginals


# ---------------------------------------------------------------------------
# Stochastic mapping
# ---------------------------------------------------------------------------

def stochastic_mapping(
    tree, is_dendropy: bool, leaf_states: dict, states: list,
    n_simulations: int = 100, model: str = "F81"
) -> tuple:
    """Stochastic mapping: sample histories, count transitions.

    Returns (transition_counts dict, per-simulation results).
    """
    marginals = ml_reconstruction(tree, is_dendropy, leaf_states, states, model)

    transition_counts = defaultdict(list)  # (from, to) -> [count per sim]

    for sim in range(n_simulations):
        # Sample ancestral states from marginals
        sampled = {}
        for node in iter_preorder(tree, is_dendropy):
            nname = node_name(node, is_dendropy)
            if node_is_leaf(node, is_dendropy):
                sampled[nname] = leaf_states.get(nname, states[0])
            else:
                probs = marginals[nname]
                prob_arr = np.array([probs.get(s, 0) for s in states])
                prob_arr = np.maximum(prob_arr, 0)
                total = prob_arr.sum()
                if total > 0:
                    prob_arr /= total
                else:
                    prob_arr = np.ones(len(states)) / len(states)
                sampled[nname] = np.random.choice(states, p=prob_arr)

        # Count transitions on branches
        counts = defaultdict(int)
        for node in iter_preorder(tree, is_dendropy):
            parent_node = node.parent if not is_dendropy else node.parent_node
            if parent_node is None:
                continue
            nname = node_name(node, is_dendropy)
            pname = node_name(parent_node, is_dendropy)
            s_parent = sampled[pname]
            s_child = sampled[nname]
            if s_parent != s_child:
                counts[(s_parent, s_child)] += 1

        for key in counts:
            transition_counts[key].append(counts[key])

    # Aggregate
    summary = {}
    all_pairs = set()
    for s1 in states:
        for s2 in states:
            if s1 != s2:
                all_pairs.add((s1, s2))

    for pair in all_pairs:
        vals = transition_counts.get(pair, [0] * n_simulations)
        # Pad with zeros for simulations with no transition
        while len(vals) < n_simulations:
            vals.append(0)
        summary[pair] = {
            "mean": float(np.mean(vals)),
            "std": float(np.std(vals)),
            "median": float(np.median(vals)),
            "ci95_lo": float(np.percentile(vals, 2.5)),
            "ci95_hi": float(np.percentile(vals, 97.5)),
        }

    return summary, marginals


# ---------------------------------------------------------------------------
# Migration counts output
# ---------------------------------------------------------------------------

def migration_counts_to_csv(summary: dict, output_path: str):
    """Write migration counts from stochastic mapping to CSV."""
    rows = []
    for (from_loc, to_loc), stats in sorted(summary.items(), key=lambda x: -x[1]["mean"]):
        if stats["mean"] > 0.01:
            rows.append({
                "from": from_loc,
                "to": to_loc,
                "n_transitions": round(stats["mean"], 2),
                "std": round(stats["std"], 2),
                "median": stats["median"],
                "ci95_lo": round(stats["ci95_lo"], 2),
                "ci95_hi": round(stats["ci95_hi"], 2),
            })
    pd.DataFrame(rows).to_csv(output_path, index=False)
    print(f"Migration counts saved: {output_path}", file=sys.stderr)


# ---------------------------------------------------------------------------
# iTOL export
# ---------------------------------------------------------------------------

# Location color palette
LOCATION_COLORS = {
    "Africa": "#F5A623", "West Africa": "#D4A017", "East Africa": "#E8A317",
    "Central Africa": "#C68E17", "Southern Africa": "#B8860B", "North Africa": "#DAA520",
    "Europe": "#4A90D9", "Western Europe": "#5B9BD5", "Eastern Europe": "#2F5496",
    "Asia": "#D0021B", "East Asia": "#E03D31", "South Asia": "#FF6347",
    "Southeast Asia": "#FF4500", "Central Asia": "#CD5C5C",
    "Americas": "#7B2D8E", "North America": "#9B59B6", "South America": "#8B008B",
    "Caribbean": "#BA55D3", "Central America": "#9370DB",
    "Oceania": "#1B9AAA", "Middle East": "#2D6A4F",
}


def export_itol_branch_colors(
    ancestral_states: dict, states: list, output_prefix: str, is_leaf: dict
):
    """Export iTOL branch color annotation."""
    path = f"{output_prefix}_branch_colors.txt"
    palette = {}
    default_colors = plt.cm.tab20(np.linspace(0, 1, max(len(states), 1))) if HAS_PLOT else None

    for i, s in enumerate(states):
        if s in LOCATION_COLORS:
            palette[s] = LOCATION_COLORS[s]
        elif default_colors is not None:
            c = default_colors[i % len(default_colors)]
            palette[s] = "#{:02x}{:02x}{:02x}".format(int(c[0]*255), int(c[1]*255), int(c[2]*255))
        else:
            palette[s] = "#999999"

    with open(path, "w") as f:
        f.write("TREE_COLORS\nSEPARATOR TAB\nDATA\n")
        for nname, state_info in ancestral_states.items():
            if isinstance(state_info, dict):
                # ML: use most probable state
                state = max(state_info, key=state_info.get)
            else:
                state = state_info
            color = palette.get(state, "#999999")
            style = "normal" if is_leaf.get(nname, False) else "normal"
            f.write(f"{nname}\tbranch\t{color}\t{style}\t2\n")

    print(f"iTOL branch colors: {path}", file=sys.stderr)


def export_itol_migration_arrows(
    tree, is_dendropy: bool, ancestral_states: dict, states: list, output_prefix: str
):
    """Export iTOL connection arrows for migration events."""
    path = f"{output_prefix}_arrows.txt"

    # Find branches where state changes
    transitions = []
    for node in iter_preorder(tree, is_dendropy):
        parent_node = node.parent if not is_dendropy else node.parent_node
        if parent_node is None:
            continue

        nname = node_name(node, is_dendropy)
        pname = node_name(parent_node, is_dendropy)

        state_n = _get_best_state(ancestral_states.get(nname))
        state_p = _get_best_state(ancestral_states.get(pname))

        if state_n and state_p and state_n != state_p:
            transitions.append((pname, nname, state_p, state_n))

    with open(path, "w") as f:
        f.write("DATASET_CONNECTION\nSEPARATOR TAB\n")
        f.write("DATASET_LABEL\tMigration events\n")
        f.write("COLOR\t#ff0000\nDRAW_ARROWS\t1\nARROW_SIZE\t20\n")
        f.write("MAXIMUM_LINE_WIDTH\t5\nDATA\n")
        for pname, nname, s_from, s_to in transitions:
            color = LOCATION_COLORS.get(s_to, "#ff0000")
            f.write(f"{pname}\t{nname}\t2\t{color}\tnormal\t{s_from}->{s_to}\n")

    print(f"iTOL migration arrows: {path} ({len(transitions)} events)", file=sys.stderr)


def _get_best_state(state_info):
    if state_info is None:
        return None
    if isinstance(state_info, dict):
        return max(state_info, key=state_info.get)
    return state_info


# ---------------------------------------------------------------------------
# BEAST DTA XML generation
# ---------------------------------------------------------------------------

def generate_beast_dta_xml(
    tree_path: str, leaf_states: dict, dates: dict, states: list, output_path: str
):
    """Generate BEAST2 XML for discrete trait analysis (DTA)."""
    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append('<beast beautitemplate="Standard" beautistatus="" '
                 'namespace="beast.core:beast.evolution.alignment:'
                 'beast.evolution.tree.coalescent:'
                 'beast.core.util:beast.evolution.nuc:'
                 'beast.evolution.operators:'
                 'beast.evolution.sitemodel:'
                 'beast.evolution.substitutionmodel:'
                 'beast.evolution.likelihood" '
                 'required="BEAST.base v2.7.0" version="2.7">')
    lines.append("")

    # Trait alignment
    lines.append('  <!-- Discrete trait alignment -->')
    lines.append('  <data id="traitData" spec="Alignment" dataType="integer">')
    state_map = {s: i for i, s in enumerate(states)}
    for strain, state in sorted(leaf_states.items()):
        idx = state_map.get(state, 0)
        date = dates.get(strain, 0)
        lines.append(f'    <sequence id="seq_{strain}" spec="Sequence" '
                     f'taxon="{strain}" totalcount="{len(states)}" value="{idx}"/>')
    lines.append('  </data>')
    lines.append("")

    # Date trait
    date_str = ",".join(f"{s}={dates.get(s, 0)}" for s in sorted(leaf_states.keys()))
    lines.append(f'  <!-- Tip dates -->')
    lines.append(f'  <trait id="dateTrait" spec="beast.evolution.tree.TraitSet" '
                 f'traitname="date" value="{date_str}">')
    lines.append(f'    <!-- Reference tree taxa here -->')
    lines.append(f'  </trait>')
    lines.append("")

    # Location trait
    loc_str = ",".join(f"{s}={leaf_states[s]}" for s in sorted(leaf_states.keys()))
    lines.append(f'  <!-- Location trait -->')
    lines.append(f'  <trait id="locationTrait" spec="beast.evolution.tree.TraitSet" '
                 f'traitname="location" value="{loc_str}">')
    lines.append(f'    <!-- Reference tree taxa here -->')
    lines.append(f'  </trait>')
    lines.append("")

    lines.append('  <!-- NOTE: This is a template. Complete with tree model, clock model, -->')
    lines.append('  <!-- substitution model for the location trait (CTMC), operators, and loggers. -->')
    lines.append('  <!-- Recommended: symmetric substitution model with BSSVS for location. -->')
    lines.append('  <!-- Use UCLD relaxed clock for branch rates. -->')
    lines.append("")

    # State list
    lines.append(f'  <!-- States: {", ".join(states)} -->')
    lines.append(f'  <!-- N states: {len(states)} -->')
    lines.append(f'  <!-- N taxa: {len(leaf_states)} -->')

    lines.append("")
    lines.append("</beast>")

    with open(output_path, "w") as f:
        f.write("\n".join(lines))
    print(f"BEAST DTA XML template: {output_path}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------------

def plot_ancestral_tree(
    tree, is_dendropy: bool, ancestral_states: dict, states: list, output_path: str
):
    """Simple visualization of ancestral states on tree."""
    if not HAS_PLOT:
        print("Warning: matplotlib not available for plotting.", file=sys.stderr)
        return

    # Collect state assignments
    state_counts = defaultdict(int)
    for nname, info in ancestral_states.items():
        state = _get_best_state(info)
        if state:
            state_counts[state] += 1

    # Transition count summary
    transitions = defaultdict(int)
    for node in iter_preorder(tree, is_dendropy):
        parent_node = node.parent if not is_dendropy else node.parent_node
        if parent_node is None:
            continue
        nname = node_name(node, is_dendropy)
        pname = node_name(parent_node, is_dendropy)
        s_n = _get_best_state(ancestral_states.get(nname))
        s_p = _get_best_state(ancestral_states.get(pname))
        if s_n and s_p and s_n != s_p:
            transitions[(s_p, s_n)] += 1

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Left: state distribution
    ax = axes[0]
    sorted_states = sorted(state_counts.items(), key=lambda x: -x[1])
    labels = [s[0] for s in sorted_states]
    values = [s[1] for s in sorted_states]
    colors = [LOCATION_COLORS.get(l, "#999999") for l in labels]
    ax.barh(labels, values, color=colors)
    ax.set_xlabel("Number of nodes")
    ax.set_title("Ancestral state distribution")
    ax.invert_yaxis()

    # Right: top transitions
    ax2 = axes[1]
    if transitions:
        sorted_trans = sorted(transitions.items(), key=lambda x: -x[1])[:15]
        trans_labels = [f"{t[0][0]} -> {t[0][1]}" for t in sorted_trans]
        trans_values = [t[1] for t in sorted_trans]
        ax2.barh(trans_labels, trans_values, color="#E03D31")
        ax2.set_xlabel("Number of transitions")
        ax2.set_title("Migration events (top 15)")
        ax2.invert_yaxis()
    else:
        ax2.text(0.5, 0.5, "No transitions detected", ha="center", va="center",
                 transform=ax2.transAxes)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Plot saved: {output_path}", file=sys.stderr)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Ancestral geographic state reconstruction for MTBC phylogenies.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Parsimony (Fitch)
  python3 ancestral_reconstruction.py tree.nwk metadata.csv --method parsimony -o states.csv

  # ML marginal posteriors
  python3 ancestral_reconstruction.py tree.nwk metadata.csv --method ml -o states.csv -p tree.png

  # Stochastic mapping with migration counts
  python3 ancestral_reconstruction.py tree.nwk metadata.csv --method stochastic \\
    --n-simulations 100 --migration-counts migrations.csv

  # iTOL export
  python3 ancestral_reconstruction.py tree.nwk metadata.csv --method ml --itol itol_prefix

  # BEAST DTA XML template
  python3 ancestral_reconstruction.py tree.nwk metadata.csv \\
    --beast-xml beast_dta.xml --dates dates.csv
        """,
    )

    parser.add_argument("tree", help="Newick tree file")
    parser.add_argument("metadata", help="CSV with strain_id and location columns")
    parser.add_argument(
        "--method", default="ml", choices=["parsimony", "ml", "stochastic"],
        help="Reconstruction method (default: ml)",
    )
    parser.add_argument("--location-column", default="country", help="Location column name")
    parser.add_argument("--n-simulations", type=int, default=100, help="Stochastic mapping simulations")
    parser.add_argument("-o", "--output", help="Output CSV (ancestral states)")
    parser.add_argument("-p", "--plot", help="Output plot (PNG/PDF)")
    parser.add_argument("--itol", help="Prefix for iTOL annotation files")
    parser.add_argument("--beast-xml", help="Generate BEAST DTA XML template")
    parser.add_argument("--dates", help="CSV with strain_id and date for BEAST")
    parser.add_argument("--migration-counts", help="Output CSV for migration transition counts")
    parser.add_argument("--model", default="F81", choices=["F81", "equal"], help="Transition model")
    parser.add_argument("--summary", action="store_true", help="Print JSON summary")

    args = parser.parse_args()

    # Load tree
    tree, is_dendropy = load_tree(args.tree)
    print(f"Tree loaded (dendropy={is_dendropy})", file=sys.stderr)

    # Load metadata
    meta = pd.read_csv(args.metadata)
    # Normalize column names
    col_map = {}
    for col in meta.columns:
        cl = col.lower().strip()
        if cl in ("strain_id", "sra_id", "id", "name", "taxon"):
            col_map[col] = "strain_id"
        elif cl == args.location_column.lower():
            col_map[col] = "location"
    meta = meta.rename(columns=col_map)

    if "strain_id" not in meta.columns or "location" not in meta.columns:
        print(f"Error: CSV must have 'strain_id' and '{args.location_column}' columns.",
              file=sys.stderr)
        sys.exit(1)

    # Empty/NaN cells must stay "unknown" (falsy), never become the literal
    # string "nan": pandas reads a blank CSV field as float NaN, and
    # .astype(str) on that turns it into "nan", which is truthy and was
    # being fed to fitch_parsimony/ml_reconstruction as a real geographic
    # state instead of triggering their "unknown: all states equally
    # likely" branch (both check `if s` / `if s and s in state_idx`).
    meta["location"] = meta["location"].fillna("")
    leaf_states = dict(zip(meta["strain_id"].astype(str), meta["location"].astype(str)))
    states = sorted(s for s in set(leaf_states.values()) if s)

    # Match leaves
    tree_leaves = {name for name, _ in get_leaves(tree, is_dendropy)}
    matched = tree_leaves & set(leaf_states.keys())
    print(f"Leaves: {len(tree_leaves)} in tree, {len(leaf_states)} in metadata, "
          f"{len(matched)} matched", file=sys.stderr)
    print(f"States ({len(states)}): {', '.join(states[:10])}"
          f"{'...' if len(states) > 10 else ''}", file=sys.stderr)

    if len(matched) < 3:
        print("Error: need at least 3 matched leaves.", file=sys.stderr)
        sys.exit(1)

    # Build leaf lookup for is_leaf
    is_leaf_map = {name: True for name, _ in get_leaves(tree, is_dendropy)}

    # Run reconstruction
    if args.method == "parsimony":
        result = fitch_parsimony(tree, is_dendropy, leaf_states, states)
        ancestral_states = result
    elif args.method == "ml":
        ancestral_states = ml_reconstruction(tree, is_dendropy, leaf_states, states, args.model)
    elif args.method == "stochastic":
        transition_summary, ancestral_states = stochastic_mapping(
            tree, is_dendropy, leaf_states, states, args.n_simulations, args.model
        )
        if args.migration_counts:
            migration_counts_to_csv(transition_summary, args.migration_counts)

    print(f"Reconstruction complete ({args.method})", file=sys.stderr)

    # Output CSV
    if args.output:
        rows = []
        for nname, info in ancestral_states.items():
            row = {"node": nname, "is_leaf": is_leaf_map.get(nname, False)}
            if isinstance(info, dict):
                best = max(info, key=info.get)
                row["best_state"] = best
                row["probability"] = round(info[best], 4)
                for s in states:
                    row[f"p_{s}"] = round(info.get(s, 0), 4)
            else:
                row["best_state"] = info
                row["probability"] = 1.0
            rows.append(row)
        pd.DataFrame(rows).to_csv(args.output, index=False)
        print(f"Ancestral states saved: {args.output}", file=sys.stderr)

    # Plot
    if args.plot:
        plot_ancestral_tree(tree, is_dendropy, ancestral_states, states, args.plot)

    # iTOL export
    if args.itol:
        export_itol_branch_colors(ancestral_states, states, args.itol, is_leaf_map)
        export_itol_migration_arrows(tree, is_dendropy, ancestral_states, states, args.itol)

    # BEAST DTA XML
    if args.beast_xml:
        dates = {}
        if args.dates:
            date_df = pd.read_csv(args.dates)
            for col in date_df.columns:
                cl = col.lower().strip()
                if cl in ("strain_id", "sra_id", "id", "name"):
                    date_df = date_df.rename(columns={col: "strain_id"})
                elif cl in ("date", "year", "decimal_date"):
                    date_df = date_df.rename(columns={col: "date"})
            if "strain_id" in date_df.columns and "date" in date_df.columns:
                dates = dict(zip(date_df["strain_id"].astype(str), date_df["date"]))
        generate_beast_dta_xml(args.tree, leaf_states, dates, states, args.beast_xml)

    # Summary
    if args.summary:
        summary_data = {
            "method": args.method,
            "n_leaves": len(tree_leaves),
            "n_matched": len(matched),
            "n_states": len(states),
            "states": states,
        }

        # Count transitions from best states
        trans_counts = defaultdict(int)
        for node in iter_preorder(tree, is_dendropy):
            parent_node = node.parent if not is_dendropy else node.parent_node
            if parent_node is None:
                continue
            nname = node_name(node, is_dendropy)
            pname = node_name(parent_node, is_dendropy)
            s_n = _get_best_state(ancestral_states.get(nname))
            s_p = _get_best_state(ancestral_states.get(pname))
            if s_n and s_p and s_n != s_p:
                trans_counts[f"{s_p}->{s_n}"] += 1

        summary_data["n_transitions"] = sum(trans_counts.values())
        summary_data["top_transitions"] = dict(
            sorted(trans_counts.items(), key=lambda x: -x[1])[:10]
        )
        print(json.dumps(summary_data, indent=2))


if __name__ == "__main__":
    main()
