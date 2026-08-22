#!/usr/bin/env python3
"""
BibTeX Verification Script - Check bibliography integrity and citation consistency.

Usage:
    uv run python -B verify_bib.py references.bib
    uv run python -B verify_bib.py references.bib --tex main.tex
    uv run python -B verify_bib.py references.bib --standard gb7714
    uv run python -B verify_bib.py references.bib --online-check --output verification_needed.json
"""

import argparse
import json
import re
import sys
from pathlib import Path

try:
    from parsers import extract_latex_citation_keys
except ImportError:
    sys.path.append(str(Path(__file__).parent))
    from parsers import extract_latex_citation_keys


class BibTeXVerifier:
    """Verify BibTeX file integrity and citation consistency."""

    REQUIRED_FIELDS = {
        "article": ["author", "title", "journal", "year"],
        "inproceedings": ["author", "title", "booktitle", "year"],
        "book": ["author", "title", "publisher", "year"],
    }

    GB7714_RECOMMENDED = ["doi", "url", "urldate"]

    def __init__(
        self,
        bib_file: str,
        standard: str = "default",
        tex_file: str | None = None,
        online: bool = False,
        email: str | None = None,
        online_timeout: float = 10.0,
    ):
        self.bib_file = Path(bib_file).resolve()
        self.standard = standard
        self.tex_file = Path(tex_file).resolve() if tex_file else None
        self.entries: list[dict] = []
        self.parse_issues: list[dict] = []
        self.online = online
        self.email = email
        self.online_timeout = online_timeout

    def parse(self) -> list[dict]:
        """Parse BibTeX file into entries."""
        try:
            content = self.bib_file.read_text(encoding="utf-8", errors="ignore")
        except Exception as exc:
            self.parse_issues.append(
                {
                    "severity": "error",
                    "type": "file_error",
                    "message": f"Failed to read BibTeX file: {exc}",
                }
            )
            return []

        entries = []
        seen_keys: dict[str, str] = {}

        # Entry-level extraction (best-effort for common BibTeX files)
        entry_pattern = r"@(\w+)\s*{\s*([^,]+)\s*,([^@]*?)(?=\n\s*@|\Z)"
        for match in re.finditer(entry_pattern, content, re.DOTALL):
            entry_type = match.group(1).lower().strip()
            key = match.group(2).strip()
            fields = self._parse_fields(match.group(3))
            entries.append(
                {"type": entry_type, "key": key, "fields": fields, "raw": match.group(0)}
            )
            self.parse_issues.extend(self._check_missing_commas(match.group(3), key))

            key_lower = key.lower()
            if key_lower in seen_keys:
                self.parse_issues.append(
                    {
                        "severity": "error",
                        "type": "duplicate_key",
                        "key": key,
                        "message": f"Duplicate key detected: '{seen_keys[key_lower]}' and '{key}'",
                    }
                )
            else:
                seen_keys[key_lower] = key

        self.entries = entries
        return entries

    def _check_missing_commas(self, fields_str: str, entry_key: str) -> list[dict]:
        # A field not separated from the previous one by a comma is silently
        # tolerated by _parse_fields below (it just searches forward for the
        # next `word =` pattern), but real BibTeX/biber chokes on the entry:
        # it either drops the field or merges it into the previous one.
        # Found 2026-08-18 on bpal_resistance_emergence: 93/96 entries had
        # `verified = {date}` glued to the previous field with no comma
        # (typically added by a manual Edit rather than crossref_verify.py's
        # --mark-verified, which always inserts the comma) -- only 60/96
        # entries actually compiled, and this script reported no issue.
        issues: list[dict] = []
        pos, n = 0, len(fields_str)
        name_re = re.compile(r"(\w+)\s*=\s*")
        prev_end: int | None = None
        while pos < n:
            m = name_re.search(fields_str, pos)
            if not m:
                break
            if prev_end is not None and "," not in fields_str[prev_end:m.start()]:
                issues.append(
                    {
                        "key": entry_key,
                        "type": "missing_comma",
                        "field": m.group(1).lower(),
                        "severity": "error",
                        "message": (
                            f"Field '{m.group(1).lower()}' is not preceded by a comma "
                            "(BibTeX/biber will silently drop or mis-merge this field)"
                        ),
                    }
                )
            i = m.end()
            if i >= n:
                break
            if fields_str[i] == "{":
                depth, j = 1, i + 1
                while depth > 0 and j < n:
                    if fields_str[j] == "{":
                        depth += 1
                    elif fields_str[j] == "}":
                        depth -= 1
                    j += 1
                pos = j
            elif fields_str[i] == '"':
                j = fields_str.find('"', i + 1)
                if j == -1:
                    break
                pos = j + 1
            else:
                m2 = re.match(r"\d+", fields_str[i:])
                if not m2:
                    pos = i + 1
                    continue
                pos = i + len(m2.group(0))
            prev_end = pos
        return issues

    def _parse_fields(self, fields_str: str) -> dict[str, str]:
        # Depth-counting extraction, not a fixed-nesting regex: a single-level
        # pattern like r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}' truncates at the second
        # nested brace (e.g. an author field containing `{\v{Z}}{\'i}dek`, which
        # nests THREE levels deep) and silently drops the rest of the field.
        # Same class of bug already fixed in bib-check's crossref_verify.py /
        # doi_coherence.py / author_format.py -- ported here so it stops
        # recurring wherever a .bib field is parsed in this ecosystem.
        fields: dict[str, str] = {}
        pos, n = 0, len(fields_str)
        name_re = re.compile(r"(\w+)\s*=\s*")
        while pos < n:
            m = name_re.search(fields_str, pos)
            if not m:
                break
            name = m.group(1).lower()
            i = m.end()
            if i >= n:
                break
            if fields_str[i] == "{":
                depth, start, j = 1, i + 1, i + 1
                while depth > 0 and j < n:
                    if fields_str[j] == "{":
                        depth += 1
                    elif fields_str[j] == "}":
                        depth -= 1
                    j += 1
                val, pos = fields_str[start:j - 1], j
            elif fields_str[i] == '"':
                j = fields_str.find('"', i + 1)
                if j == -1:
                    break
                val, pos = fields_str[i + 1:j], j + 1
            else:
                m2 = re.match(r"\d+", fields_str[i:])
                if not m2:
                    pos = i + 1
                    continue
                val, pos = m2.group(0), i + len(m2.group(0))
            fields[name] = re.sub(r"\s+", " ", val).strip()
        return fields

    def verify(self) -> dict:
        """Run full verification and return structured results."""
        if not self.entries:
            self.parse()

        results: dict[str, object] = {
            "total_entries": len(self.entries),
            "valid_entries": 0,
            "issues": list(self.parse_issues),
            "status": "PASS",
            "needs_online_check": [],
            "missing_in_bib": [],
            "unused_in_tex": [],
        }

        for entry in self.entries:
            entry_issues = self._verify_entry(entry)
            if entry_issues:
                results["issues"].extend(entry_issues)
            else:
                results["valid_entries"] += 1

            # Check for missing identifiers (DOI/URL)
            if "doi" not in entry["fields"] and "url" not in entry["fields"]:
                results["needs_online_check"].append(
                    {
                        "key": entry["key"],
                        "title": entry["fields"].get("title", "Unknown Title"),
                        "author": entry["fields"].get("author", "Unknown Author"),
                    }
                )

            if self.standard == "gb7714":
                self._check_gb7714_recommended(entry, results["issues"])

        if self.tex_file:
            missing_in_bib, unused_in_tex, tex_issues = self._check_citation_consistency()
            results["missing_in_bib"] = sorted(missing_in_bib)
            results["unused_in_tex"] = sorted(unused_in_tex)
            results["issues"].extend(tex_issues)

        # Online verification (when --online and online_bib_verify is available)
        if self.online:
            try:
                from online_bib_verify import OnlineBibVerifier

                online_verifier = OnlineBibVerifier(
                    polite_email=self.email,
                    timeout=self.online_timeout,
                )
                for entry_info in results["needs_online_check"]:
                    entry_dict = {
                        "key": entry_info["key"],
                        "title": entry_info.get("title", ""),
                        "author": entry_info.get("author", ""),
                    }
                    # Find full entry fields
                    for entry in self.entries:
                        if entry["key"] == entry_info["key"]:
                            entry_dict.update(entry["fields"])
                            break
                    result = online_verifier.verify_entry(entry_dict)
                    if result.status == "mismatch":
                        for m in result.mismatches:
                            results["issues"].append(
                                {
                                    "key": result.bib_key,
                                    "type": "metadata_mismatch",
                                    "severity": "error",
                                    "message": f"Online verification mismatch: {m}",
                                }
                            )
                    elif result.status == "not_found":
                        results["issues"].append(
                            {
                                "key": result.bib_key,
                                "type": "not_found_online",
                                "severity": "warning",
                                "message": "Entry not found in online databases",
                            }
                        )
                    elif result.status == "verified" and result.suggested_doi:
                        results["issues"].append(
                            {
                                "key": result.bib_key,
                                "type": "doi_suggestion",
                                "severity": "warning",
                                "message": f"Consider adding DOI: {result.suggested_doi}",
                            }
                        )
            except ImportError:
                print("# Warning: online_bib_verify.py not found, skipping online verification")

        if results["issues"]:
            has_error = any(item["severity"] == "error" for item in results["issues"])
            results["status"] = "FAIL" if has_error else "WARNING"

        return results

    def _verify_entry(self, entry: dict) -> list[dict]:
        issues: list[dict] = []
        entry_type = entry["type"]
        entry_key = entry["key"]
        fields = entry["fields"]

        required = self.REQUIRED_FIELDS.get(entry_type, [])
        for field in required:
            if field not in fields or not fields[field]:
                if field == "author" and "editor" in fields:
                    continue
                issues.append(
                    {
                        "key": entry_key,
                        "type": "missing_field",
                        "field": field,
                        "severity": "error",
                        "message": f"Missing required field '{field}'",
                    }
                )

        # Title case check (simplified heuristic)
        title = fields.get("title", "")
        if title and re.search(r"\b[A-Z]{2,}\b", title) and "{" not in title:
            issues.append(
                {
                    "key": entry_key,
                    "type": "caps",
                    "severity": "warning",
                    "message": "Unprotected uppercase in title",
                }
            )

        return issues

    def _check_gb7714_recommended(self, entry: dict, issues: list[dict]) -> None:
        fields = entry["fields"]
        entry_key = entry["key"]
        for field in self.GB7714_RECOMMENDED:
            if field not in fields:
                issues.append(
                    {
                        "key": entry_key,
                        "type": "gb7714_recommended",
                        "field": field,
                        "severity": "warning",
                        "message": f"GB7714 recommends field '{field}'",
                    }
                )

    def _check_citation_consistency(self) -> tuple[set[str], set[str], list[dict]]:
        issues: list[dict] = []
        if not self.tex_file or not self.tex_file.exists():
            msg = (
                f"TeX file not found: {self.tex_file}" if self.tex_file else "TeX file not provided"
            )
            issues.append(
                {
                    "severity": "error",
                    "type": "tex_file_error",
                    "message": msg,
                }
            )
            return set(), set(), issues

        try:
            tex_content = self.tex_file.read_text(encoding="utf-8", errors="ignore")
        except Exception as exc:
            issues.append(
                {
                    "severity": "error",
                    "type": "tex_file_error",
                    "message": f"Failed to read TeX file: {exc}",
                }
            )
            return set(), set(), issues

        cited_keys = extract_latex_citation_keys(tex_content)
        bib_keys = {entry["key"] for entry in self.entries}

        missing_in_bib = cited_keys - bib_keys
        unused_in_tex = bib_keys - cited_keys

        if missing_in_bib:
            issues.append(
                {
                    "severity": "error",
                    "type": "missing_in_bib",
                    "message": f"Citations not found in BibTeX: {', '.join(sorted(missing_in_bib))}",
                }
            )
        if unused_in_tex:
            issues.append(
                {
                    "severity": "warning",
                    "type": "unused_in_tex",
                    "message": f"Unused BibTeX entries: {', '.join(sorted(unused_in_tex))}",
                }
            )

        return missing_in_bib, unused_in_tex, issues

    def generate_report(self, result: dict) -> str:
        lines = []
        lines.append(f"BibTeX Check: {self.bib_file}")
        lines.append(f"Status: {result['status']}")
        lines.append(f"Total entries: {result['total_entries']}")
        lines.append(f"Valid entries: {result['valid_entries']}")

        if self.tex_file:
            lines.append(f"TeX file: {self.tex_file}")
            lines.append(f"missing_in_bib: {len(result['missing_in_bib'])}")
            lines.append(f"unused_in_tex: {len(result['unused_in_tex'])}")

        if result["issues"]:
            lines.append("\nIssues:")
            for issue in result["issues"]:
                key_suffix = f" @{issue['key']}" if issue.get("key") else ""
                lines.append(f"  [{issue['severity'].upper()}]{key_suffix}: {issue['message']}")

        if result["needs_online_check"]:
            lines.append(
                f"\n[INFO] {len(result['needs_online_check'])} entries missing DOI/URL "
                "(Use --online-check to export list)"
            )
            lines.append(
                "[TIP] AI-generated citations have ~40% error rate. "
                "Verify entries without DOI/URL using Semantic Scholar API or CrossRef. "
                "See references/CITATION_VERIFICATION.md for verification workflow."
            )

        if result["missing_in_bib"]:
            lines.append(f"[INFO] missing_in_bib keys: {', '.join(result['missing_in_bib'])}")
        if result["unused_in_tex"]:
            lines.append(f"[INFO] unused_in_tex keys: {', '.join(result['unused_in_tex'])}")

        return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="BibTeX Verification")
    parser.add_argument("bib_file", help=".bib file")
    parser.add_argument("--tex", help="Main .tex file for citation consistency checks")
    parser.add_argument("--standard", choices=["default", "gb7714"], default="default")
    parser.add_argument(
        "--online-check", action="store_true", help="Generate list for online verification"
    )
    parser.add_argument(
        "--online",
        action="store_true",
        help="Enable online verification via CrossRef/Semantic Scholar",
    )
    parser.add_argument("--email", help="Email for CrossRef polite pool (faster rate limits)")
    parser.add_argument(
        "--online-timeout",
        type=float,
        default=10.0,
        help="Timeout per API request in seconds",
    )
    parser.add_argument("--output", help="Output JSON file path")
    parser.add_argument("--json", action="store_true", help="Print full JSON result")

    args = parser.parse_args()

    if not Path(args.bib_file).exists():
        print(f"[ERROR] File not found: {args.bib_file}", file=sys.stderr)
        return 1

    verifier = BibTeXVerifier(
        args.bib_file,
        args.standard,
        args.tex,
        online=getattr(args, "online", False),
        email=getattr(args, "email", None),
        online_timeout=getattr(args, "online_timeout", 10.0),
    )
    result = verifier.verify()

    if args.online_check:
        output_file = args.output or "verification_needed.json"
        with open(output_file, "w", encoding="utf-8") as handle:
            json.dump(result["needs_online_check"], handle, indent=2, ensure_ascii=False)
        print(f"Exported {len(result['needs_online_check'])} entries to {output_file}")
    elif args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2, ensure_ascii=False)
        print(f"Saved verification result to {args.output}")
    else:
        print(verifier.generate_report(result))

    # Exit policy: PASS/WARNING -> 0, FAIL/error -> 1
    return 1 if result["status"] == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
