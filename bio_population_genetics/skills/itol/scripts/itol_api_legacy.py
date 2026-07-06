#!/usr/bin/env python3
"""
DEPRECATED — Use itol_pipeline.py instead.

This script is kept as a fallback reference. The new itol_pipeline.py
uses the itolapi library and provides additional features: presets,
batch export, comparison mode, and programmatic legends.

Original description:
  iTOL Batch API Client — upload, export, and delete phylogenetic trees.
"""

import argparse
import io
import os
import sys
import zipfile
from pathlib import Path

try:
    import requests
except ImportError:
    print(
        "Error: 'requests' is required. Install with: pip install requests",
        file=sys.stderr,
    )
    sys.exit(1)

ITOL_UPLOAD_URL = "https://itol.embl.de/batch_uploader.cgi"
ITOL_EXPORT_URL = "https://itol.embl.de/batch_downloader.cgi"
ITOL_DELETE_URL = "https://itol.embl.de/batch_delete.cgi"
ITOL_TREE_URL = "https://itol.embl.de/tree/{}"


def resolve_api_key(cli_key: str = None) -> str:
    """Resolve iTOL API key from CLI arg, env var, or config file."""
    if cli_key:
        return cli_key

    env_key = os.environ.get("ITOL_API_KEY")
    if env_key:
        return env_key

    config_path = Path.home() / ".config" / "itol" / "api_key"
    if config_path.exists():
        return config_path.read_text().strip()

    return None


def create_zip(tree_file: str, annotation_files: list) -> bytes:
    """Create a ZIP archive containing the tree and annotation files.

    The tree file is renamed to have a .tree extension as required by iTOL.
    Annotation files are included with their original names.
    """
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        tree_path = Path(tree_file)
        tree_name = tree_path.stem + ".tree"
        zf.write(tree_file, tree_name)

        for annot in annotation_files:
            annot_path = Path(annot)
            zf.write(annot, annot_path.name)

    return buf.getvalue()


def upload_tree(
    tree_file: str,
    annotation_files: list,
    api_key: str,
    project: str,
    tree_name: str = None,
    tree_description: str = None,
) -> str:
    """Upload a tree with annotations to iTOL.

    Args:
        tree_file: Path to Newick tree file.
        annotation_files: List of paths to annotation .txt files.
        api_key: iTOL API key.
        project: Project name on iTOL.
        tree_name: Display name for the tree.
        tree_description: Description text.

    Returns:
        Tree ID string.

    Raises:
        RuntimeError: If upload fails.
    """
    if not api_key:
        raise RuntimeError(
            "iTOL API key required for upload. Provide via:\n"
            "  --api-key KEY\n"
            "  ITOL_API_KEY environment variable\n"
            "  ~/.config/itol/api_key file"
        )

    zip_data = create_zip(tree_file, annotation_files)

    data = {
        "APIkey": api_key,
        "projectName": project,
    }
    if tree_name:
        data["treeName"] = tree_name
    if tree_description:
        data["treeDescription"] = tree_description

    files = {
        "zipFile": ("upload.zip", zip_data, "application/zip"),
    }

    print(f"Uploading tree to iTOL project '{project}'...", file=sys.stderr)
    resp = requests.post(ITOL_UPLOAD_URL, data=data, files=files, timeout=120)

    if resp.status_code != 200:
        raise RuntimeError(f"HTTP {resp.status_code}: {resp.text}")

    lines = resp.text.strip().split("\n")
    last_line = lines[-1]

    if last_line.startswith("ERR"):
        raise RuntimeError(f"iTOL upload error: {last_line}")

    if last_line.startswith("SUCCESS:"):
        tree_id = last_line.split(":", 1)[1].strip()
        if len(lines) > 1:
            warnings = [l for l in lines[:-1] if l.strip()]
            for w in warnings:
                print(f"  Warning: {w}", file=sys.stderr)
        return tree_id

    raise RuntimeError(f"Unexpected response: {resp.text}")


def export_tree(
    tree_id: str,
    fmt: str,
    output_path: str,
    display_mode: int = None,
    line_width: int = None,
    font_size: int = None,
    font_name: str = None,
    arc: int = None,
    rotation: int = None,
    label_display: int = None,
    align_labels: int = None,
    dashed_lines: int = None,
    bootstrap_display: int = None,
    bootstrap_type: int = None,
    bootstrap_min: float = None,
    internal_scale: int = None,
    ignore_branch_length: int = None,
    datasets_visible: str = None,
    range_mode: int = None,
    include_ranges_legend: int = None,
    default_branch_color: str = None,
    default_label_color: str = None,
) -> Path:
    """Export a rendered tree image from iTOL.

    Args:
        tree_id: iTOL tree ID (from upload or URL).
        fmt: Output format (svg, pdf, png, eps).
        output_path: Path to save the output file.
        ... display options (see iTOL batch export docs)

    Returns:
        Path to the saved output file.
    """
    data = {
        "tree": tree_id,
        "format": fmt,
    }

    option_map = {
        "display_mode": display_mode,
        "line_width": line_width,
        "current_font_size": font_size,
        "current_font_name": font_name,
        "arc": arc,
        "rotation": rotation,
        "label_display": label_display,
        "align_labels": align_labels,
        "dashed_lines": dashed_lines,
        "bootstrap_display": bootstrap_display,
        "bootstrap_type": bootstrap_type,
        "bootstrap_slider_min": bootstrap_min,
        "internal_scale": internal_scale,
        "ignore_branch_length": ignore_branch_length,
        "datasets_visible": datasets_visible,
        "range_mode": range_mode,
        "include_ranges_legend": include_ranges_legend,
        "default_branch_color": default_branch_color,
        "default_label_color": default_label_color,
    }

    for key, val in option_map.items():
        if val is not None:
            data[key] = val

    print(f"Exporting tree {tree_id} as {fmt}...", file=sys.stderr)
    resp = requests.post(ITOL_EXPORT_URL, data=data, timeout=120)

    if resp.status_code != 200:
        raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:200]}")

    content_type = resp.headers.get("Content-Type", "")
    if "text/html" in content_type and b"<html" in resp.content[:100].lower():
        raise RuntimeError(f"iTOL export error (HTML response): {resp.text[:300]}")

    out = Path(output_path)
    out.write_bytes(resp.content)
    return out


def delete_tree(tree_id: str, api_key: str) -> bool:
    """Delete a tree from iTOL.

    Returns True on success.
    """
    if not api_key:
        raise RuntimeError("API key required for delete operation.")

    data = {
        "APIkey": api_key,
        "tree": tree_id,
    }

    print(f"Deleting tree {tree_id}...", file=sys.stderr)
    resp = requests.post(ITOL_DELETE_URL, data=data, timeout=30)

    if "SUCCESS" in resp.text:
        return True

    raise RuntimeError(f"Delete failed: {resp.text}")


def main():
    parser = argparse.ArgumentParser(
        description="iTOL Batch API Client — upload, export, and delete phylogenetic trees.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Upload tree with annotations
  python itol_api.py upload tree.nwk colors.txt strip.txt \\
    --api-key YOUR_KEY --project MyProject --tree-name "L4.15"

  # Export as SVG (circular, with bootstrap)
  python itol_api.py export TREE_ID --format svg --display-mode 2 \\
    --bootstrap --align-labels --output figure.svg

  # Export as PNG
  python itol_api.py export TREE_ID --format png --output figure.png

  # Delete a tree
  python itol_api.py delete TREE_ID --api-key YOUR_KEY
        """,
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- Upload ---
    p_upload = subparsers.add_parser("upload", help="Upload tree + annotations to iTOL")
    p_upload.add_argument("tree_file", help="Newick tree file")
    p_upload.add_argument("annotations", nargs="*", help="Annotation .txt files")
    p_upload.add_argument("--api-key", "-k", default=None)
    p_upload.add_argument("--project", "-p", required=True, help="iTOL project name")
    p_upload.add_argument("--tree-name", "-n", default=None, help="Display name")
    p_upload.add_argument("--tree-description", "-d", default=None)

    # --- Export ---
    p_export = subparsers.add_parser("export", help="Export rendered tree image")
    p_export.add_argument("tree_id", help="iTOL tree ID")
    p_export.add_argument("--format", "-f", default="svg", choices=["svg", "pdf", "png", "eps"])
    p_export.add_argument("--output", "-o", required=True, help="Output file path")
    p_export.add_argument("--display-mode", type=int, choices=[1, 2, 3],
                          help="1=rectangular, 2=circular, 3=unrooted")
    p_export.add_argument("--line-width", type=int)
    p_export.add_argument("--font-size", type=int)
    p_export.add_argument("--font-name", default=None)
    p_export.add_argument("--arc", type=int, help="Arc angle for circular mode (0-360)")
    p_export.add_argument("--rotation", type=int)
    p_export.add_argument("--labels", action="store_true", help="Show leaf labels")
    p_export.add_argument("--no-labels", action="store_true", help="Hide leaf labels")
    p_export.add_argument("--align-labels", action="store_true")
    p_export.add_argument("--dashed-lines", action="store_true")
    p_export.add_argument("--bootstrap", action="store_true", help="Show bootstrap values")
    p_export.add_argument("--bootstrap-type", type=int, choices=[1, 2],
                          help="1=text, 2=symbol")
    p_export.add_argument("--bootstrap-min", type=float, help="Min bootstrap to display")
    p_export.add_argument("--scale-bar", action="store_true", help="Show internal scale")
    p_export.add_argument("--cladogram", action="store_true", help="Ignore branch lengths")
    p_export.add_argument("--datasets", default=None, help="Visible datasets (comma-separated indices)")
    p_export.add_argument("--ranges", action="store_true", help="Show colored ranges")
    p_export.add_argument("--ranges-legend", action="store_true")
    p_export.add_argument("--branch-color", default=None, help="Default branch color (hex)")
    p_export.add_argument("--label-color", default=None, help="Default label color (hex)")

    # --- Delete ---
    p_delete = subparsers.add_parser("delete", help="Delete a tree from iTOL")
    p_delete.add_argument("tree_id", help="iTOL tree ID")
    p_delete.add_argument("--api-key", "-k", default=None)

    args = parser.parse_args()

    if args.command == "upload":
        api_key = resolve_api_key(args.api_key)
        try:
            tree_id = upload_tree(
                tree_file=args.tree_file,
                annotation_files=args.annotations or [],
                api_key=api_key,
                project=args.project,
                tree_name=args.tree_name,
                tree_description=args.tree_description,
            )
            tree_url = ITOL_TREE_URL.format(tree_id)
            print(f"Upload successful!")
            print(f"  Tree ID: {tree_id}")
            print(f"  URL: {tree_url}")
        except RuntimeError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "export":
        try:
            out = export_tree(
                tree_id=args.tree_id,
                fmt=args.format,
                output_path=args.output,
                display_mode=args.display_mode,
                line_width=args.line_width,
                font_size=args.font_size,
                font_name=args.font_name,
                arc=args.arc,
                rotation=args.rotation,
                label_display=0 if args.no_labels else (1 if args.labels else None),
                align_labels=1 if args.align_labels else None,
                dashed_lines=1 if args.dashed_lines else None,
                bootstrap_display=1 if args.bootstrap else None,
                bootstrap_type=args.bootstrap_type,
                bootstrap_min=args.bootstrap_min,
                internal_scale=1 if args.scale_bar else None,
                ignore_branch_length=1 if args.cladogram else None,
                datasets_visible=args.datasets,
                range_mode=2 if args.ranges else None,
                include_ranges_legend=1 if args.ranges_legend else None,
                default_branch_color=args.branch_color,
                default_label_color=args.label_color,
            )
            print(f"Exported to {out} ({out.stat().st_size:,} bytes)")
        except RuntimeError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "delete":
        api_key = resolve_api_key(args.api_key)
        try:
            delete_tree(args.tree_id, api_key)
            print(f"Tree {args.tree_id} deleted successfully.")
        except RuntimeError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
