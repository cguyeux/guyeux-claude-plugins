#!/usr/bin/env python3
"""
iTOL Pipeline — Upload, export, and manage phylogenetic trees via itolapi.

End-to-end workflow: upload tree + annotations → configure display → export
publication-quality figures (SVG/PDF/PNG) with programmatic legends.

Supports presets (article, supplement, presentation, poster), batch export,
and comparison mode (same tree, different visible datasets).

Replaces itol_api_legacy.py. Uses the itolapi library (v4.1+) when available,
falls back to direct HTTP requests otherwise.
"""

import argparse
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

# Import presets from companion module
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from presets import (
    COMPARISON_CONFIGS,
    EXPORT_PRESETS,
    FORMAT_EXTENSIONS,
    MTBC_LEGENDS,
)

# --- itolapi or fallback ---

try:
    from itolapi import Itol, ItolExport

    ITOLAPI_AVAILABLE = True
except ImportError:
    ITOLAPI_AVAILABLE = False

    try:
        import requests
    except ImportError:
        print(
            "Error: either 'itolapi' or 'requests' is required.\n"
            "  pip install itolapi   (recommended)\n"
            "  pip install requests  (fallback)",
            file=sys.stderr,
        )
        sys.exit(1)


# ─── Layer A: Config ────────────────────────────────────────────────────────────


def resolve_api_key(cli_key: str = None) -> str | None:
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


# ─── Layer B: Core operations ───────────────────────────────────────────────────


def _ensure_tree_extension(tree_file: Path, tmp_dir: Path) -> Path:
    """Ensure tree file has a recognized extension for iTOL."""
    recognized = {".tree", ".nwk", ".newick", ".nex", ".nexus", ".phyloxml"}
    if tree_file.suffix.lower() in recognized:
        return tree_file
    # Copy with .tree extension
    dest = tmp_dir / (tree_file.stem + ".tree")
    shutil.copy2(tree_file, dest)
    return dest


def upload_tree(
    tree_file: str,
    annotation_files: list[str],
    api_key: str,
    project: str,
    tree_name: str = None,
    tree_description: str = None,
) -> tuple[str, str, list[str]]:
    """Upload tree + annotations to iTOL.

    Returns:
        (tree_id, webpage_url, warnings)
    """
    if not api_key:
        raise RuntimeError(
            "iTOL API key required for upload. Provide via:\n"
            "  --api-key KEY\n"
            "  ITOL_API_KEY environment variable\n"
            "  ~/.config/itol/api_key file"
        )

    tree_path = Path(tree_file)
    if not tree_path.exists():
        raise RuntimeError(f"Tree file not found: {tree_file}")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        safe_tree = _ensure_tree_extension(tree_path, tmp)

        if ITOLAPI_AVAILABLE:
            itol = Itol()
            itol.add_file(safe_tree)
            for annot in annotation_files:
                annot_path = Path(annot)
                if not annot_path.exists():
                    print(f"  Warning: annotation file not found: {annot}", file=sys.stderr)
                    continue
                itol.add_file(annot_path)

            itol.params["projectName"] = project
            if api_key:
                itol.params["APIkey"] = api_key
            if tree_name:
                itol.params["treeName"] = tree_name
            if tree_description:
                itol.params["treeDescription"] = tree_description

            print(f"Uploading tree to iTOL project '{project}'...", file=sys.stderr)
            success = itol.upload()

            if not success:
                raise RuntimeError(f"iTOL upload failed: {itol.comm.upload_output}")

            tree_id = itol.comm.tree_id
            webpage = itol.get_webpage()
            warnings = itol.comm.warnings if hasattr(itol.comm, "warnings") else []

            return tree_id, webpage, warnings

        else:
            # Fallback: direct HTTP with requests
            return _upload_fallback(
                safe_tree, annotation_files, api_key, project, tree_name, tree_description
            )


def _upload_fallback(tree_file, annotation_files, api_key, project, tree_name, tree_description):
    """Fallback upload using direct HTTP requests."""
    import io
    import zipfile

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        tree_path = Path(tree_file)
        zf.write(tree_file, tree_path.name)
        for annot in annotation_files:
            annot_path = Path(annot)
            if annot_path.exists():
                zf.write(annot, annot_path.name)

    data = {"APIkey": api_key, "projectName": project}
    if tree_name:
        data["treeName"] = tree_name
    if tree_description:
        data["treeDescription"] = tree_description

    print(f"Uploading tree to iTOL project '{project}' (fallback mode)...", file=sys.stderr)
    resp = requests.post(
        "https://itol.embl.de/batch_uploader.cgi",
        data=data,
        files={"zipFile": ("upload.zip", buf.getvalue(), "application/zip")},
        timeout=120,
    )

    if resp.status_code != 200:
        raise RuntimeError(f"HTTP {resp.status_code}: {resp.text}")

    lines = resp.text.strip().split("\n")
    last_line = lines[-1]
    if last_line.startswith("ERR"):
        raise RuntimeError(f"iTOL upload error: {last_line}")
    if last_line.startswith("SUCCESS:"):
        tree_id = last_line.split(":", 1)[1].strip()
        warnings = [l for l in lines[:-1] if l.strip()]
        url = f"https://itol.embl.de/tree/{tree_id}"
        return tree_id, url, warnings

    raise RuntimeError(f"Unexpected response: {resp.text}")


def export_tree(tree_id: str, output_path: str, params: dict = None) -> Path:
    """Export a rendered tree image from iTOL.

    Args:
        tree_id: iTOL tree ID (from upload).
        output_path: Path to save the output file.
        params: Dict of iTOL batch export parameters.

    Returns:
        Path to the saved output file.
    """
    params = params or {}
    params.setdefault("format", "svg")

    if ITOLAPI_AVAILABLE:
        exporter = ItolExport()
        exporter.set_export_param_value("tree", tree_id)
        for key, val in params.items():
            exporter.set_export_param_value(key, str(val))

        out = Path(output_path)
        print(f"Exporting tree {tree_id} as {params['format']}...", file=sys.stderr)
        exporter.export(out)
        return out

    else:
        # Fallback: direct HTTP
        data = {"tree": tree_id}
        data.update(params)
        print(f"Exporting tree {tree_id} as {params['format']} (fallback)...", file=sys.stderr)
        resp = requests.post(
            "https://itol.embl.de/batch_downloader.cgi", data=data, timeout=120
        )
        if resp.status_code != 200:
            raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:200]}")
        content_type = resp.headers.get("Content-Type", "")
        if "text/html" in content_type and b"<html" in resp.content[:100].lower():
            raise RuntimeError(f"iTOL export error: {resp.text[:300]}")
        out = Path(output_path)
        out.write_bytes(resp.content)
        return out


def delete_tree(tree_id: str, api_key: str) -> bool:
    """Delete a tree from iTOL. Always uses direct HTTP (itolapi has no delete)."""
    if not api_key:
        raise RuntimeError("API key required for delete operation.")

    if ITOLAPI_AVAILABLE:
        import requests as req
    else:
        req = requests

    data = {"APIkey": api_key, "tree": tree_id}
    print(f"Deleting tree {tree_id}...", file=sys.stderr)
    resp = req.post("https://itol.embl.de/batch_delete.cgi", data=data, timeout=30)

    if "SUCCESS" in resp.text:
        return True
    raise RuntimeError(f"Delete failed: {resp.text}")


# ─── Layer C: High-level features ──────────────────────────────────────────────


def inject_legend(params: dict, legend_name: str) -> dict:
    """Inject MTBC legend parameters into export params.

    Legends defined in annotation files appear in the web UI but are not always
    included in batch exports. This ensures they are present.
    """
    if legend_name not in MTBC_LEGENDS:
        available = ", ".join(MTBC_LEGENDS.keys())
        raise ValueError(f"Unknown legend '{legend_name}'. Available: {available}")

    result = dict(params)
    result.update(MTBC_LEGENDS[legend_name])
    return result


def build_export_params(preset_name: str, overrides: dict = None) -> dict:
    """Build export parameters from a preset with optional overrides."""
    if preset_name not in EXPORT_PRESETS:
        available = ", ".join(EXPORT_PRESETS.keys())
        raise ValueError(f"Unknown preset '{preset_name}'. Available: {available}")

    params = dict(EXPORT_PRESETS[preset_name])
    if overrides:
        params.update(overrides)
    return params


def batch_export(
    tree_id: str,
    preset_names: list[str],
    output_dir: str,
    base_name: str = "tree",
    legends: list[str] = None,
) -> list[Path]:
    """Export the same tree in multiple format/preset combinations.

    Args:
        tree_id: iTOL tree ID.
        preset_names: List of preset names (e.g., ["article", "presentation"]).
        output_dir: Directory for output files.
        base_name: Base filename (without extension).
        legends: Optional legend names to inject into all exports.

    Returns:
        List of output file paths.
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = []

    for i, preset_name in enumerate(preset_names):
        params = build_export_params(preset_name)
        if legends:
            for legend_name in legends:
                params = inject_legend(params, legend_name)

        fmt = params["format"]
        ext = FORMAT_EXTENSIONS.get(fmt, f".{fmt}")
        output_file = out_dir / f"{base_name}_{preset_name}{ext}"

        out = export_tree(tree_id, str(output_file), params)
        size = out.stat().st_size
        print(f"  {preset_name}: {output_file} ({size:,} bytes)", file=sys.stderr)
        outputs.append(out)

        # Rate limiting between requests
        if i < len(preset_names) - 1:
            time.sleep(1.5)

    return outputs


def comparison_export(
    tree_id: str,
    config_names: list[str],
    output_dir: str,
    base_name: str = "tree",
    preset_name: str = "article",
    legends: list[str] = None,
) -> list[Path]:
    """Export the same tree with different dataset visibility configurations.

    Args:
        tree_id: iTOL tree ID.
        config_names: List of comparison config names.
        output_dir: Directory for output files.
        base_name: Base filename (without extension).
        preset_name: Base preset to use for all exports.
        legends: Optional legend names to inject.

    Returns:
        List of output file paths.
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = []

    base_params = build_export_params(preset_name)
    if legends:
        for legend_name in legends:
            base_params = inject_legend(base_params, legend_name)

    for i, config_name in enumerate(config_names):
        if config_name not in COMPARISON_CONFIGS:
            available = ", ".join(COMPARISON_CONFIGS.keys())
            raise ValueError(f"Unknown config '{config_name}'. Available: {available}")

        config = COMPARISON_CONFIGS[config_name]
        params = dict(base_params)
        params["datasets_visible"] = config["datasets_visible"]

        fmt = params["format"]
        ext = FORMAT_EXTENSIONS.get(fmt, f".{fmt}")
        suffix = config["suffix"]
        output_file = out_dir / f"{base_name}_{suffix}{ext}"

        out = export_tree(tree_id, str(output_file), params)
        size = out.stat().st_size
        print(f"  {config['label']}: {output_file} ({size:,} bytes)", file=sys.stderr)
        outputs.append(out)

        if i < len(config_names) - 1:
            time.sleep(1.5)

    return outputs


def run_pipeline(
    tree_file: str,
    annotation_files: list[str],
    api_key: str,
    project: str,
    tree_name: str = None,
    tree_description: str = None,
    preset_name: str = "article",
    output_dir: str = ".",
    base_name: str = None,
    legends: list[str] = None,
    extra_params: dict = None,
) -> tuple[str, str, Path]:
    """Full pipeline: upload tree + annotations, then export.

    Returns:
        (tree_id, webpage_url, output_path)
    """
    # Upload
    tree_id, webpage, warnings = upload_tree(
        tree_file, annotation_files, api_key, project, tree_name, tree_description
    )
    print(f"Upload successful!", file=sys.stderr)
    print(f"  Tree ID: {tree_id}", file=sys.stderr)
    print(f"  URL: {webpage}", file=sys.stderr)
    for w in warnings:
        print(f"  Warning: {w}", file=sys.stderr)

    # Small delay for iTOL to process
    time.sleep(2)

    # Export
    params = build_export_params(preset_name, extra_params)
    if legends:
        for legend_name in legends:
            params = inject_legend(params, legend_name)

    if not base_name:
        base_name = Path(tree_file).stem

    fmt = params["format"]
    ext = FORMAT_EXTENSIONS.get(fmt, f".{fmt}")
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    output_file = out_dir / f"{base_name}_{preset_name}{ext}"

    out = export_tree(tree_id, str(output_file), params)
    size = out.stat().st_size
    print(f"Exported: {output_file} ({size:,} bytes)", file=sys.stderr)

    return tree_id, webpage, out


# ─── CLI ────────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="iTOL Pipeline — upload, export, and manage phylogenetic trees.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full pipeline: upload + export in one step
  python itol_pipeline.py pipeline tree.nwk 00_colors.txt 01_strip.txt \\
    --project MyProject --preset article --output-dir ./figures/

  # Upload only
  python itol_pipeline.py upload tree.nwk annotations*.txt \\
    --project MyProject --tree-name "L4.15 v2"

  # Export with preset
  python itol_pipeline.py export TREE_ID -o figure.svg --preset article

  # Batch export (multiple formats)
  python itol_pipeline.py batch-export TREE_ID \\
    --presets article,presentation,supplement --output-dir ./figures/

  # Comparison (same tree, different datasets visible)
  python itol_pipeline.py compare TREE_ID \\
    --configs lineage_overview,dr_profile,phylogeography --output-dir ./comparison/

  # Delete
  python itol_pipeline.py delete TREE_ID
        """,
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Common arguments
    def add_api_key_arg(p):
        p.add_argument("--api-key", "-k", default=None, help="iTOL API key")

    # --- pipeline ---
    p_pipe = subparsers.add_parser("pipeline", help="Upload + export in one step")
    p_pipe.add_argument("tree_file", help="Newick tree file")
    p_pipe.add_argument("annotations", nargs="*", help="Annotation .txt files")
    add_api_key_arg(p_pipe)
    p_pipe.add_argument("--project", "-p", required=True, help="iTOL project name")
    p_pipe.add_argument("--tree-name", "-n", default=None)
    p_pipe.add_argument("--tree-description", "-d", default=None)
    p_pipe.add_argument("--preset", default="article", choices=list(EXPORT_PRESETS.keys()))
    p_pipe.add_argument("--output-dir", "-O", default=".", help="Output directory")
    p_pipe.add_argument("--base-name", default=None, help="Base filename (default: tree stem)")
    p_pipe.add_argument("--legend", action="append", dest="legends",
                        choices=list(MTBC_LEGENDS.keys()), help="Add legend (repeatable)")
    p_pipe.add_argument("--format", "-f", default=None, help="Override format from preset")
    p_pipe.add_argument("--datasets", default=None, help="Visible datasets (comma-separated)")

    # --- upload ---
    p_upload = subparsers.add_parser("upload", help="Upload tree + annotations")
    p_upload.add_argument("tree_file", help="Newick tree file")
    p_upload.add_argument("annotations", nargs="*", help="Annotation .txt files")
    add_api_key_arg(p_upload)
    p_upload.add_argument("--project", "-p", required=True, help="iTOL project name")
    p_upload.add_argument("--tree-name", "-n", default=None)
    p_upload.add_argument("--tree-description", "-d", default=None)

    # --- export ---
    p_export = subparsers.add_parser("export", help="Export rendered tree")
    p_export.add_argument("tree_id", help="iTOL tree ID")
    p_export.add_argument("--output", "-o", required=True, help="Output file path")
    p_export.add_argument("--preset", default=None, choices=list(EXPORT_PRESETS.keys()))
    p_export.add_argument("--format", "-f", default=None,
                          choices=["svg", "pdf", "png", "eps"])
    p_export.add_argument("--display-mode", type=int, choices=[1, 2, 3])
    p_export.add_argument("--line-width", type=int)
    p_export.add_argument("--font-size", type=int)
    p_export.add_argument("--align-labels", action="store_true")
    p_export.add_argument("--bootstrap", action="store_true")
    p_export.add_argument("--bootstrap-type", type=int, choices=[1, 2])
    p_export.add_argument("--bootstrap-min", type=float)
    p_export.add_argument("--datasets", default=None)
    p_export.add_argument("--legend", action="append", dest="legends",
                          choices=list(MTBC_LEGENDS.keys()))

    # --- batch-export ---
    p_batch = subparsers.add_parser("batch-export", help="Export in multiple presets")
    p_batch.add_argument("tree_id", help="iTOL tree ID")
    p_batch.add_argument("--presets", required=True,
                         help="Comma-separated preset names")
    p_batch.add_argument("--output-dir", "-O", default=".", help="Output directory")
    p_batch.add_argument("--base-name", default="tree", help="Base filename")
    p_batch.add_argument("--legend", action="append", dest="legends",
                         choices=list(MTBC_LEGENDS.keys()))

    # --- compare ---
    p_compare = subparsers.add_parser("compare", help="Export with different dataset subsets")
    p_compare.add_argument("tree_id", help="iTOL tree ID")
    p_compare.add_argument("--configs", required=True,
                           help="Comma-separated comparison config names")
    p_compare.add_argument("--preset", default="article", choices=list(EXPORT_PRESETS.keys()))
    p_compare.add_argument("--output-dir", "-O", default=".", help="Output directory")
    p_compare.add_argument("--base-name", default="tree", help="Base filename")
    p_compare.add_argument("--legend", action="append", dest="legends",
                           choices=list(MTBC_LEGENDS.keys()))

    # --- delete ---
    p_delete = subparsers.add_parser("delete", help="Delete a tree from iTOL")
    p_delete.add_argument("tree_id", help="iTOL tree ID")
    add_api_key_arg(p_delete)

    args = parser.parse_args()

    try:
        if args.command == "pipeline":
            api_key = resolve_api_key(args.api_key)
            extra = {}
            if args.format:
                extra["format"] = args.format
            if args.datasets:
                extra["datasets_visible"] = args.datasets
            tree_id, webpage, output = run_pipeline(
                tree_file=args.tree_file,
                annotation_files=args.annotations or [],
                api_key=api_key,
                project=args.project,
                tree_name=args.tree_name,
                tree_description=args.tree_description,
                preset_name=args.preset,
                output_dir=args.output_dir,
                base_name=args.base_name,
                legends=args.legends,
                extra_params=extra or None,
            )
            print(f"\nPipeline complete!")
            print(f"  Tree ID: {tree_id}")
            print(f"  URL: {webpage}")
            print(f"  Output: {output}")

        elif args.command == "upload":
            api_key = resolve_api_key(args.api_key)
            tree_id, webpage, warnings = upload_tree(
                tree_file=args.tree_file,
                annotation_files=args.annotations or [],
                api_key=api_key,
                project=args.project,
                tree_name=args.tree_name,
                tree_description=args.tree_description,
            )
            print(f"Upload successful!")
            print(f"  Tree ID: {tree_id}")
            print(f"  URL: {webpage}")
            for w in warnings:
                print(f"  Warning: {w}")

        elif args.command == "export":
            if args.preset:
                params = build_export_params(args.preset)
            else:
                params = {}

            # CLI overrides
            if args.format:
                params["format"] = args.format
            if args.display_mode:
                params["display_mode"] = str(args.display_mode)
            if args.line_width:
                params["line_width"] = str(args.line_width)
            if args.font_size:
                params["current_font_size"] = str(args.font_size)
            if args.align_labels:
                params["align_labels"] = "1"
            if args.bootstrap:
                params["bootstrap_display"] = "1"
            if args.bootstrap_type:
                params["bootstrap_type"] = str(args.bootstrap_type)
            if args.bootstrap_min:
                params["bootstrap_slider_min"] = str(args.bootstrap_min)
            if args.datasets:
                params["datasets_visible"] = args.datasets

            if not params.get("format"):
                params["format"] = "svg"

            if args.legends:
                for legend_name in args.legends:
                    params = inject_legend(params, legend_name)

            out = export_tree(args.tree_id, args.output, params)
            print(f"Exported to {out} ({out.stat().st_size:,} bytes)")

        elif args.command == "batch-export":
            preset_names = [p.strip() for p in args.presets.split(",")]
            outputs = batch_export(
                tree_id=args.tree_id,
                preset_names=preset_names,
                output_dir=args.output_dir,
                base_name=args.base_name,
                legends=args.legends,
            )
            print(f"\nBatch export complete: {len(outputs)} files")
            for f in outputs:
                print(f"  {f}")

        elif args.command == "compare":
            config_names = [c.strip() for c in args.configs.split(",")]
            outputs = comparison_export(
                tree_id=args.tree_id,
                config_names=config_names,
                output_dir=args.output_dir,
                base_name=args.base_name,
                preset_name=args.preset,
                legends=args.legends,
            )
            print(f"\nComparison export complete: {len(outputs)} files")
            for f in outputs:
                print(f"  {f}")

        elif args.command == "delete":
            api_key = resolve_api_key(args.api_key)
            delete_tree(args.tree_id, api_key)
            print(f"Tree {args.tree_id} deleted successfully.")

    except (RuntimeError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
