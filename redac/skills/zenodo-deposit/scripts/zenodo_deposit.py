#!/usr/bin/env python3
"""Dépôt Zenodo automatique et réutilisable (API REST, urllib, zéro dépendance).

Le token est résolu UNE FOIS puis réutilisé pour tous les articles :
  1. variable d'env ZENODO_TOKEN (ou ZENODO_TOKEN_SANDBOX en --sandbox)
  2. fichier ~/.config/zenodo/token  (ou token.sandbox), mode 600
  3. sinon -> message expliquant comment en créer un (une seule fois).

`set-token` enregistre le token dans ~/.config/zenodo/ (chmod 600) : à faire une fois.
`create` crée un BROUILLON, upload l'archive, écrit les métadonnées et RÉSERVE le DOI.
Il NE PUBLIE PAS : `publish <id>` est une étape explicite et IRRÉVERSIBLE.

Exemples :
  python zenodo_deposit.py set-token            # lit le token sur stdin et l'enregistre
  python zenodo_deposit.py create --src paper/eval --metadata meta.json --patch-tex paper/main.tex
  python zenodo_deposit.py create --zip bundle.zip --metadata meta.json
  python zenodo_deposit.py status <id>
  python zenodo_deposit.py publish <id>
  # répétition à blanc :
  python zenodo_deposit.py --sandbox create --src paper/eval --metadata meta.json
"""
import argparse
import json
import os
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

CONFIG_DIR = Path(os.environ.get("ZENODO_CONFIG_DIR", Path.home() / ".config" / "zenodo"))
PLACEHOLDER = "[Zenodo DOI to be inserted]"


def base_and_tokenfile(sandbox: bool):
    if sandbox:
        return "https://sandbox.zenodo.org", CONFIG_DIR / "token.sandbox", "ZENODO_TOKEN_SANDBOX"
    return "https://zenodo.org", CONFIG_DIR / "token", "ZENODO_TOKEN"


def resolve_token(sandbox: bool) -> str:
    _, tokfile, envname = base_and_tokenfile(sandbox)
    tok = os.environ.get(envname) or os.environ.get("ZENODO_TOKEN")
    if tok:
        return tok.strip()
    if tokfile.exists():
        return tokfile.read_text().strip()
    where = "sandbox.zenodo.org" if sandbox else "zenodo.org"
    sys.exit(
        f"Aucun token Zenodo.\n"
        f"  Créez-en un (UNE SEULE FOIS) sur https://{where}/account/settings/applications/tokens/new/\n"
        f"  scopes: deposit:write + deposit:actions, puis :\n"
        f"  python {Path(sys.argv[0]).name} {'--sandbox ' if sandbox else ''}set-token\n"
        f"  (ou export {envname}=...)")


def save_token(sandbox: bool):
    _, tokfile, _ = base_and_tokenfile(sandbox)
    tok = (sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("-") else
           sys.stdin.read()).strip()
    if not tok:
        sys.exit("Token vide. Usage : echo 'TOKEN' | python zenodo_deposit.py set-token")
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    tokfile.write_text(tok + "\n")
    tokfile.chmod(0o600)
    print(f"Token enregistré dans {tokfile} (chmod 600). Réutilisé automatiquement désormais.")


class Z:
    def __init__(self, base, tok):
        self.base, self.tok = base, tok

    def req(self, url, method="GET", data=None, ctype="application/json") -> "tuple[int, dict]":
        sep = "&" if "?" in url else "?"
        r = urllib.request.Request(f"{url}{sep}access_token={self.tok}", data=data, method=method)
        if ctype:
            r.add_header("Content-Type", ctype)
        try:
            with urllib.request.urlopen(r, timeout=600) as resp:
                body = resp.read()
                return resp.status, (json.loads(body) if body else {})
        except urllib.error.HTTPError as e:
            raw = e.read().decode(errors="replace")
            try:
                return e.code, json.loads(raw)
            except Exception:  # noqa: BLE001
                return e.code, {"_error": raw}


def zip_dir(src: Path) -> Path:
    out = Path(tempfile.gettempdir()) / f"{src.name}_zenodo.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(src.rglob("*")):
            if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc" and ".git" not in p.parts:
                zf.write(p, p.relative_to(src.parent))
    return out


def build_metadata(args) -> dict:
    if args.metadata:
        return json.loads(Path(args.metadata).read_text())
    creators = []
    for c in (args.creator or []):
        name, *rest = c.split("|")
        d = {"name": name.strip()}
        if len(rest) >= 1 and rest[0].strip():
            d["affiliation"] = rest[0].strip()
        if len(rest) >= 2 and rest[1].strip():
            d["orcid"] = rest[1].strip()
        creators.append(d)
    if not (args.title and creators):
        sys.exit("Sans --metadata, il faut au moins --title et un --creator \"Nom|Affiliation|ORCID\".")
    return {"metadata": {
        "upload_type": args.upload_type, "title": args.title, "creators": creators,
        "description": (Path(args.description_file).read_text() if args.description_file
                        else (args.description or args.title)),
        "keywords": [k.strip() for k in (args.keywords or "").split(",") if k.strip()],
        "access_right": "open", "license": args.license, "language": "eng"}}


def patch_tex(texpath: Path, doi: str, placeholder: str):
    txt = texpath.read_text()
    if placeholder not in txt:
        print(f"  (placeholder {placeholder!r} absent de {texpath} — patch ignoré)")
        return
    url = f"\\url{{https://doi.org/{doi}}}"
    texpath.write_text(txt.replace(placeholder, url))
    print(f"  {texpath} : {placeholder!r} -> {url}")


def _finalize(z: Z, args, dep_id, bucket):
    zippath = Path(args.zip) if args.zip else zip_dir(Path(args.src))
    if not zippath.exists():
        sys.exit(f"Archive absente : {zippath}")
    print(f"  Upload {zippath.name} ({zippath.stat().st_size/1e6:.1f} Mo) (remplace si même nom) ...")
    st, _ = z.req(f"{bucket}/{zippath.name}", "PUT", zippath.read_bytes(), ctype="application/octet-stream")
    if st not in (200, 201):
        sys.exit(f"Échec upload (HTTP {st}).")
    print(f"  Métadonnées ...")
    st, body = z.req(f"{z.base}/api/deposit/depositions/{dep_id}", "PUT",
                     json.dumps(build_metadata(args)).encode())
    if st not in (200, 201):
        sys.exit(f"Échec métadonnées (HTTP {st}) : {body}")
    st, dep = z.req(f"{z.base}/api/deposit/depositions/{dep_id}")
    doi = dep.get("metadata", {}).get("prereserve_doi", {}).get("doi", "(non réservé)")
    print(f"  Brouillon prêt (NON publié). DOI réservé : {doi}")
    print(f"  Édition : {z.base}/uploads/{dep_id}")
    if args.patch_tex and doi and doi != "(non réservé)":
        patch_tex(Path(args.patch_tex), doi, args.placeholder)
    print(f"\nVérifiez le brouillon, puis publiez (IRRÉVERSIBLE) :")
    print(f"   python {Path(sys.argv[0]).name} {'--sandbox ' if args.sandbox else ''}publish {dep_id}")


def cmd_create(z: Z, args):
    print(f"[création] Brouillon sur {z.base} ...")
    st, dep = z.req(f"{z.base}/api/deposit/depositions", "POST", b"{}")
    if st not in (200, 201):
        sys.exit(f"Échec création (HTTP {st}) : {dep}")
    print(f"      id={dep['id']}")
    _finalize(z, args, dep["id"], dep["links"]["bucket"])


def cmd_update(z: Z, args):
    print(f"[mise à jour] Brouillon {args.id} sur {z.base} ...")
    st, dep = z.req(f"{z.base}/api/deposit/depositions/{args.id}")
    if st != 200:
        sys.exit(f"Brouillon introuvable (HTTP {st}) : {dep}")
    if dep.get("submitted"):
        sys.exit("Ce dépôt est déjà publié : impossible de le modifier (créer une nouvelle version).")
    _finalize(z, args, args.id, dep["links"]["bucket"])


def cmd_status(z: Z, dep_id):
    st, dep = z.req(f"{z.base}/api/deposit/depositions/{dep_id}")
    if st != 200:
        sys.exit(f"Introuvable (HTTP {st}) : {dep}")
    m = dep.get("metadata", {})
    print(json.dumps({"id": dep_id, "title": m.get("title"), "state": dep.get("state"),
                      "submitted": dep.get("submitted"),
                      "reserved_doi": m.get("prereserve_doi", {}).get("doi"),
                      "doi": dep.get("doi"), "files": [f["filename"] for f in dep.get("files", [])]},
                     indent=2, ensure_ascii=False))


def cmd_publish(z: Z, dep_id):
    st, body = z.req(f"{z.base}/api/deposit/depositions/{dep_id}/actions/publish", "POST", b"")
    if st in (200, 202):
        print("PUBLIÉ. DOI :", body.get("doi") if isinstance(body, dict) else body)
    else:
        sys.exit(f"Échec publication (HTTP {st}) : {body}")


def main():
    ap = argparse.ArgumentParser(description="Dépôt Zenodo réutilisable")
    ap.add_argument("--sandbox", action="store_true", help="utiliser sandbox.zenodo.org")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("set-token")

    def add_deposit_args(par):
        g = par.add_mutually_exclusive_group(required=True)
        g.add_argument("--src", help="répertoire à archiver (zippé automatiquement)")
        g.add_argument("--zip", help="archive .zip déjà prête")
        par.add_argument("--metadata", help="metadata.json (format Zenodo). Sinon --title/--creator/...")
        par.add_argument("--title")
        par.add_argument("--creator", action="append", help='"Nom, Prénom|Affiliation|ORCID" (répétable)')
        par.add_argument("--description")
        par.add_argument("--description-file")
        par.add_argument("--keywords", help="liste séparée par des virgules")
        par.add_argument("--license", default="cc-by-4.0")
        par.add_argument("--upload-type", default="software")
        par.add_argument("--patch-tex", help="remplace le placeholder DOI dans ce .tex")
        par.add_argument("--placeholder", default=PLACEHOLDER)

    add_deposit_args(sub.add_parser("create"))
    u = sub.add_parser("update"); u.add_argument("id"); add_deposit_args(u)
    s = sub.add_parser("status"); s.add_argument("id")
    p = sub.add_parser("publish"); p.add_argument("id")
    args = ap.parse_args()

    if args.cmd == "set-token":
        save_token(args.sandbox); return
    base, _, _ = base_and_tokenfile(args.sandbox)
    z = Z(base, resolve_token(args.sandbox))
    if args.cmd == "create":
        cmd_create(z, args)
    elif args.cmd == "update":
        cmd_update(z, args)
    elif args.cmd == "status":
        cmd_status(z, args.id)
    elif args.cmd == "publish":
        cmd_publish(z, args.id)


if __name__ == "__main__":
    main()
