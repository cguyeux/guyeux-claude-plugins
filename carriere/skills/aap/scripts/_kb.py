#!/usr/bin/env python3
"""Socle commun aux scripts du skill /aap : localisation de la base, lecture et
ecriture atomique de TSV. Zero dependance externe."""

from __future__ import annotations

import csv
import os
import sys
import tempfile
from pathlib import Path

DEFAULT_KB = Path.home() / ".agents" / "knowledge" / "funding"


def kb_dir() -> Path:
    return Path(os.environ.get("AAP_KB", DEFAULT_KB)).expanduser()


def load(name: str) -> tuple[list[str], list[dict]]:
    p = kb_dir() / name
    if not p.exists():
        sys.exit(f"introuvable : {p}\nVerifier AAP_KB ou creer la base (voir README).")
    with p.open(newline="", encoding="utf-8") as fh:
        r = csv.DictReader(fh, delimiter="\t")
        return list(r.fieldnames or []), list(r)


def save(name: str, cols: list[str], rows: list[dict]) -> None:
    p = kb_dir() / name
    fd, tmp = tempfile.mkstemp(dir=str(p.parent), prefix=p.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=cols, delimiter="\t",
                               extrasaction="ignore", lineterminator="\n")
            w.writeheader()
            for row in rows:
                w.writerow({c: str(row.get(c, "unknown")).replace("\t", " ").replace("\n", " ")
                            for c in cols})
        os.replace(tmp, p)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def wrap(text: str, width: int = 88, indent: str = "    ") -> str:
    import textwrap
    out = []
    for chunk in str(text).split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        out.append(textwrap.fill(chunk, width, initial_indent=indent,
                                 subsequent_indent=indent + "  "))
    return "\n".join(out)
