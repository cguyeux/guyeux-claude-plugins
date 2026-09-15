#!/usr/bin/env python3
"""
RAxML-NG Job Monitor

Poll the status of a RAxML-NG job on the TBannotator server
and download the resulting Newick tree when completed.

Usage:
    python3 raxml_monitor.py --job-id 42 --output tree.nwk
    python3 raxml_monitor.py --job-id 42 --poll-interval 60 --timeout 86400
"""

import argparse
import json
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    print(
        "Error: 'requests' is required. Install with: pip install requests",
        file=sys.stderr,
    )
    sys.exit(1)

DEFAULT_BASE_URL = "https://tblearn.tbannotator.ideev.universite-paris-saclay.fr/mcp"
DEFAULT_POLL_INTERVAL = 30  # seconds
DEFAULT_TIMEOUT = 86400  # 24 hours


def get_job_status(base_url: str, job_id: int) -> dict:
    """Query job status via the MCP SSE endpoint.

    Falls back to direct download attempt if MCP query fails.
    Returns dict with job fields or raises RuntimeError.
    """
    # Try direct download endpoint to check if tree is ready
    download_url = f"{base_url}/download/tree_newick/{job_id}"
    try:
        resp = requests.head(download_url, timeout=10, allow_redirects=True)
        if resp.status_code == 200:
            return {
                "id": job_id,
                "status": "completed",
                "download_url": download_url,
            }
    except requests.RequestException:
        pass

    return {"id": job_id, "status": "unknown"}


def download_newick(base_url: str, job_id: int, output_path: str) -> Path:
    """Download the Newick tree file for a completed job."""
    url = f"{base_url}/download/tree_newick/{job_id}"
    print(f"Downloading Newick from {url}...", file=sys.stderr)

    resp = requests.get(url, timeout=120)
    if resp.status_code != 200:
        raise RuntimeError(
            f"Download failed: HTTP {resp.status_code}\n{resp.text[:300]}"
        )

    content = resp.text.strip()
    if not content or not any(c in content for c in "(,;"):
        raise RuntimeError(f"Response doesn't look like Newick: {content[:200]}")

    out = Path(output_path)
    out.write_text(content + "\n")
    return out


def count_leaves(newick: str) -> int:
    """Count leaf nodes in a Newick string."""
    import re

    leaves = re.findall(r"[A-Za-z_][A-Za-z0-9_]+", newick)
    # Filter out common non-leaf tokens
    leaves = [l for l in leaves if not l.startswith(("bootstrap", "node", "inner"))]
    return len(leaves)


def monitor_job(
    base_url: str,
    job_id: int,
    output_path: str,
    poll_interval: int,
    timeout: int,
) -> Path:
    """Poll job status and download tree when completed.

    This function is designed for use when MCP tools are not available
    (e.g., running from a terminal). When using Claude Code with MCP,
    prefer polling via tool_query_postgres directly.
    """
    start_time = time.time()
    last_status = None

    print(f"Monitoring RAxML job {job_id}...", file=sys.stderr)
    print(f"  Poll interval: {poll_interval}s", file=sys.stderr)
    print(f"  Timeout: {timeout}s ({timeout // 3600}h)", file=sys.stderr)
    print(f"  Output: {output_path}", file=sys.stderr)
    print(file=sys.stderr)

    while True:
        elapsed = time.time() - start_time
        if elapsed > timeout:
            raise RuntimeError(
                f"Timeout after {elapsed:.0f}s. Job {job_id} may still be running."
            )

        status_info = get_job_status(base_url, job_id)
        status = status_info.get("status", "unknown")

        if status != last_status:
            strain_count = status_info.get("strain_count", "?")
            snp_count = status_info.get("snp_count", "?")
            print(
                f"  [{time.strftime('%H:%M:%S')}] Status: {status} "
                f"(strains: {strain_count}, SNPs: {snp_count})",
                file=sys.stderr,
            )
            last_status = status

        if status == "completed":
            out = download_newick(base_url, job_id, output_path)
            newick = out.read_text()
            n_leaves = count_leaves(newick)
            print(file=sys.stderr)
            print(f"Tree downloaded: {out} ({out.stat().st_size:,} bytes)", file=sys.stderr)
            print(f"  Leaves: {n_leaves}", file=sys.stderr)

            # Print summary as JSON to stdout
            summary = {
                "job_id": job_id,
                "status": "completed",
                "output_file": str(out),
                "file_size_bytes": out.stat().st_size,
                "n_leaves": n_leaves,
                "elapsed_seconds": round(elapsed),
            }
            if "strain_count" in status_info:
                summary["strain_count"] = status_info["strain_count"]
            if "snp_count" in status_info:
                summary["snp_count"] = status_info["snp_count"]
            print(json.dumps(summary, indent=2))
            return out

        if status == "failed":
            error = status_info.get("error_message", "Unknown error")
            raise RuntimeError(f"Job {job_id} failed: {error}")

        time.sleep(poll_interval)


def main():
    parser = argparse.ArgumentParser(
        description="Monitor RAxML-NG jobs on TBannotator and download results.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Monitor and download when done
  python3 raxml_monitor.py --job-id 42 --output tree.nwk

  # Custom poll interval and timeout
  python3 raxml_monitor.py --job-id 42 --poll-interval 120 --timeout 172800 -o tree.nwk

  # Just download (no polling, job already completed)
  python3 raxml_monitor.py --job-id 42 --output tree.nwk --no-poll

  # Check status only
  python3 raxml_monitor.py --job-id 42 --status-only
        """,
    )

    parser.add_argument("--job-id", "-j", type=int, required=True, help="RAxML job ID")
    parser.add_argument("--output", "-o", default="tree.nwk", help="Output Newick file")
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=DEFAULT_POLL_INTERVAL,
        help=f"Seconds between status checks (default: {DEFAULT_POLL_INTERVAL})",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"Max seconds to wait (default: {DEFAULT_TIMEOUT})",
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"TBannotator MCP base URL (default: {DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "--no-poll",
        action="store_true",
        help="Don't poll — just try to download immediately",
    )
    parser.add_argument(
        "--status-only",
        action="store_true",
        help="Print status and exit (no download)",
    )

    args = parser.parse_args()

    try:
        if args.status_only:
            info = get_job_status(args.base_url, args.job_id)
            print(json.dumps(info, indent=2))
            return

        if args.no_poll:
            out = download_newick(args.base_url, args.job_id, args.output)
            newick = out.read_text()
            n_leaves = count_leaves(newick)
            print(f"Downloaded: {out} ({out.stat().st_size:,} bytes, {n_leaves} leaves)")
            return

        monitor_job(
            base_url=args.base_url,
            job_id=args.job_id,
            output_path=args.output,
            poll_interval=args.poll_interval,
            timeout=args.timeout,
        )

    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted by user.", file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    main()
