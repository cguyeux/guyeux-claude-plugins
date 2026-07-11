#!/usr/bin/env python3
"""OCR d'un PDF/image via Mistral OCR 4 (`mistral-ocr-latest`), API REST pure.

Dernier recours du skill read-scientific-pdf, pour les documents SANS couche
texte (archives numerisees, manuscrits) quand la lecture multimodale ne suffit
pas : corpus trop volumineux, ou besoin d'une couche texte greppable.

Depend uniquement de la stdlib (pas de SDK mistralai a installer).
Cle attendue dans $MISTRAL_API_KEY (definie dans ~/.bashrc).

Usage :
    python3 mistral_ocr.py <fichier.pdf> [-o sortie.md] [--pages 1-5] [--json]
    python3 mistral_ocr.py --batch <dossier_ou_glob> -o resultats/   # 50% moins cher

Tarif (juillet 2026) : 4 $ / 1000 pages en synchrone, 2 $ / 1000 pages en batch.
"""

import argparse
import glob
import json
import mimetypes
import os
import re
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

BASE = "https://api.mistral.ai/v1"
MODEL = "mistral-ocr-latest"


def key():
    k = os.environ.get("MISTRAL_API_KEY")
    if not k:
        sys.exit("MISTRAL_API_KEY absente. Elle est definie dans ~/.bashrc : "
                 "lancer via `bash -lc` ou exporter la variable.")
    return k


def _req(url, data=None, headers=None, method=None, retries=0):
    """Appel API. `retries` : nb de reessais sur 404/429/5xx, avec backoff.

    Le 404 apres upload n'est pas une erreur logique : sur un gros fichier, le
    fichier n'est pas encore indexe cote Mistral quand on reclame son URL signee.
    Constate sur un PDF de 52 Mo / 125 pages. D'ou le reessai.
    """
    for essai in range(retries + 1):
        r = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
        try:
            with urllib.request.urlopen(r, timeout=300) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            transitoire = e.code in (404, 408, 429) or e.code >= 500
            if transitoire and essai < retries:
                delai = 2 ** essai
                print(f"  HTTP {e.code}, reessai dans {delai}s "
                      f"({essai + 1}/{retries})", file=sys.stderr)
                time.sleep(delai)
                continue
            sys.exit(f"Erreur API Mistral {e.code} sur {url}\n{e.read().decode()[:800]}")
        except urllib.error.URLError as e:
            if essai < retries:
                time.sleep(2 ** essai)
                continue
            sys.exit(f"Erreur reseau sur {url} : {e}")
    sys.exit(f"Echec apres {retries} reessais sur {url}")  # inatteignable


def upload(path):
    """Televerse un fichier local et renvoie une URL signee."""
    boundary = uuid.uuid4().hex
    ctype = mimetypes.guess_type(path)[0] or "application/octet-stream"
    body = (
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"purpose\"\r\n\r\nocr\r\n"
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
        f"filename=\"{Path(path).name}\"\r\nContent-Type: {ctype}\r\n\r\n"
    ).encode() + Path(path).read_bytes() + f"\r\n--{boundary}--\r\n".encode()

    up = _req(f"{BASE}/files", data=body, headers={
        "Authorization": f"Bearer {key()}",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    }, retries=3)
    # retries=5 : l'indexation du fichier cote Mistral n'est pas immediate sur les
    # gros PDF, et l'URL signee repond alors 404. Backoff jusqu'a ~31 s.
    signed = _req(f"{BASE}/files/{up['id']}/url?expiry=24",
                  headers={"Authorization": f"Bearer {key()}"}, retries=5)
    return signed["url"]


def ocr(path, pages=None, tables="markdown", confidence=False):
    """OCR synchrone d'un document. Renvoie la reponse brute de l'API."""
    doc_url = upload(path)
    kind = "image_url" if Path(path).suffix.lower() in {".png", ".jpg", ".jpeg"} else "document_url"
    payload = {
        "model": MODEL,
        "document": {"type": kind, kind: doc_url},
        "table_format": tables,          # null | markdown | html
        "include_image_base64": False,   # eviter de gonfler la reponse
    }
    if confidence:
        payload["confidence_scores_granularity"] = "word"
    if pages:
        payload["pages"] = pages         # liste d'index 0-based
    return _req(f"{BASE}/ocr", data=json.dumps(payload).encode(), headers={
        "Authorization": f"Bearer {key()}",
        "Content-Type": "application/json",
    })


def to_markdown(resp):
    return "\n\n".join(
        f"<!-- page {p['index'] + 1} -->\n{p['markdown']}" for p in resp["pages"]
    )


# Syntaxe markdown pure : ce sont des artefacts de STRUCTURE produits par l'OCR,
# pas des mots du document. Leur « confiance » n'a aucun sens, et les encapsuler
# CASSE le markdown en aval : `⟦#|0.59⟧ AVIS MOTIVE` n'est plus un titre, et toute
# regex `^#+\s*AVIS` le rate SILENCIEUSEMENT. Constate sur ce corpus : 14 % des
# titres etaient ainsi corrompus, soit la moitie des avis motives introuvables.
_MARKDOWN_PUR = re.compile(r"^[#*_~`>|\-+=\[\]().:]+$")


def audit(resp, fort=0.50, faible=0.80):
    """Marque les mots peu surs et liste les candidats a arbitrage multimodal.

    Sortie destinee a etre RELUE PAR LE MODELE, qui applique ensuite le
    controle semantique puis l'arbitrage multimodal (cf. SKILL.md).

    Ne marque JAMAIS la syntaxe markdown (voir _MARKDOWN_PUR).
    """
    out, cands = [], []
    for p in resp["pages"]:
        page = p["index"] + 1
        md = p["markdown"]
        scores = (p.get("confidence_scores") or {}).get("word_confidence_scores")
        if not scores:
            out.append(f"<!-- page {page} (pas de score) -->\n{md}")
            continue
        # reconstruire le texte en marquant les mots douteux, a rebours pour
        # ne pas invalider les start_index
        marked = md
        for w in sorted(scores, key=lambda x: x["start_index"], reverse=True):
            c, txt = w["confidence"], w["text"]
            if c >= faible or not txt.strip():
                continue
            if _MARKDOWN_PUR.match(txt.strip()):
                continue  # `#`, `##`, `|`, `-`… : structure, pas un mot
            i, j = w["start_index"], w["start_index"] + len(txt)
            niveau = "FORT" if c < fort else "faible"
            lead = txt[: len(txt) - len(txt.lstrip())]  # garder l'espace initial
            marked = f"{marked[:i]}{lead}⟦{txt.strip()}|{c:.2f}⟧{marked[j:]}"
            cands.append((page, txt.strip(), c, niveau))
        out.append(f"<!-- page {page} -->\n{marked}")

    txt = "\n\n".join(out)
    if cands:
        txt += "\n\n---\n## Candidats a verification (⟦mot|confiance⟧)\n\n"
        txt += "| page | mot | conf. | suspicion |\n|---|---|---|---|\n"
        for page, w, c, n in sorted(cands, key=lambda x: x[2]):
            txt += f"| {page} | `{w}` | {c:.2f} | {n} |\n"
        pages = sorted({p for p, _, _, n in cands if n == "FORT"})
        txt += (
            f"\n**{len(cands)} candidats.** Pages a arbitrer en multimodal "
            f"(suspicion FORTE) : {pages or 'aucune'}.\n\n"
            "RAPPEL : un mot peu sur peut etre (a) une ERREUR D'OCR a corriger, "
            "ou (b) une FAUTE DU SCRIPTEUR, fidelement transcrite, qu'il faut "
            "PRESERVER. Seule la lecture multimodale de la page tranche. "
            "Ne jamais normaliser la langue du redacteur.\n"
        )
    return txt


def batch(paths, outdir):
    """Batch API : 50% moins cher, asynchrone. Recommande au-dela de ~50 pages."""
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    jsonl = outdir / "batch_input.jsonl"

    with jsonl.open("w") as fh:
        for i, p in enumerate(paths):
            print(f"  upload {i + 1}/{len(paths)} : {Path(p).name}", file=sys.stderr)
            url = upload(p)
            kind = "image_url" if Path(p).suffix.lower() in {".png", ".jpg", ".jpeg"} else "document_url"
            fh.write(json.dumps({
                "custom_id": Path(p).name,
                "body": {"document": {"type": kind, kind: url}},
            }) + "\n")

    boundary = uuid.uuid4().hex
    body = (
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"purpose\"\r\n\r\nbatch\r\n"
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
        f"filename=\"{jsonl.name}\"\r\nContent-Type: application/jsonl\r\n\r\n"
    ).encode() + jsonl.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
    up = _req(f"{BASE}/files", data=body, headers={
        "Authorization": f"Bearer {key()}",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    })

    job = _req(f"{BASE}/batch/jobs", data=json.dumps({
        "input_files": [up["id"]], "model": MODEL, "endpoint": "/v1/ocr",
    }).encode(), headers={
        "Authorization": f"Bearer {key()}", "Content-Type": "application/json",
    })
    print(f"Job batch {job['id']} soumis ({len(paths)} documents).", file=sys.stderr)

    while True:
        j = _req(f"{BASE}/batch/jobs/{job['id']}",
                 headers={"Authorization": f"Bearer {key()}"})
        print(f"  statut={j['status']} reussis={j.get('succeeded_requests')}/"
              f"{j.get('total_requests')}", file=sys.stderr)
        if j["status"] in {"SUCCESS", "FAILED", "CANCELLED", "TIMEOUT_EXCEEDED"}:
            break
        time.sleep(20)

    if j["status"] != "SUCCESS":
        sys.exit(f"Batch termine en statut {j['status']}")

    req = urllib.request.Request(f"{BASE}/files/{j['output_file']}/content",
                                 headers={"Authorization": f"Bearer {key()}"})
    with urllib.request.urlopen(req, timeout=300) as resp:
        for line in resp.read().decode().splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            body = rec.get("response", {}).get("body", {})
            if "pages" not in body:
                print(f"  ECHEC : {rec.get('custom_id')}", file=sys.stderr)
                continue
            dest = outdir / (Path(rec["custom_id"]).stem + ".md")
            dest.write_text(to_markdown(body))
            print(f"  -> {dest}", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description="OCR via Mistral OCR 4")
    ap.add_argument("target", help="fichier PDF/image, ou dossier/glob avec --batch")
    ap.add_argument("-o", "--out", help="fichier .md (simple) ou dossier (--batch)")
    ap.add_argument("--pages", help="plage 1-based, ex. 1-5 (mode simple)")
    ap.add_argument("--batch", action="store_true", help="Batch API (50%% moins cher)")
    ap.add_argument("--json", action="store_true", help="sortir la reponse brute")
    ap.add_argument("--confidence", action="store_true",
                    help="scores de confiance par mot (a croiser avec le controle semantique)")
    ap.add_argument("--audit", action="store_true",
                    help="marque les mots peu surs et liste les pages a arbitrer en multimodal")
    a = ap.parse_args()

    if a.batch:
        paths = (sorted(glob.glob(os.path.join(a.target, "*")))
                 if os.path.isdir(a.target) else sorted(glob.glob(a.target)))
        paths = [p for p in paths if Path(p).suffix.lower() in
                 {".pdf", ".png", ".jpg", ".jpeg"}]
        if not paths:
            sys.exit(f"Aucun document exploitable dans {a.target}")
        return batch(paths, a.out or "ocr_out")

    pages = None
    if a.pages:
        lo, _, hi = a.pages.partition("-")
        pages = list(range(int(lo) - 1, int(hi or lo)))  # API en index 0-based

    resp = ocr(a.target, pages=pages, confidence=a.confidence or a.audit)
    if a.json:
        out = json.dumps(resp, ensure_ascii=False, indent=2)
    elif a.audit:
        out = audit(resp)
    else:
        out = to_markdown(resp)
    if a.out:
        Path(a.out).write_text(out)
        print(f"-> {a.out} ({len(resp['pages'])} pages)", file=sys.stderr)
    else:
        print(out)


if __name__ == "__main__":
    main()
