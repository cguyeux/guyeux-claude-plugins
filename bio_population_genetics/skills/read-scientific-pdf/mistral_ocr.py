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


# --------------------------------------------------------------------------
# GARDE-FOU D'EFFONDREMENT (ecritures anciennes)
#
# Pourquoi : un OCR valide sur une ecriture NE SE GENERALISE PAS a une ecriture
# plus ancienne, et quand il echoue il ne produit PAS du charabia -- il produit
# du FAUX VRAISEMBLABLE. Mesure sur le fonds d'Ancien Regime des AN (13/07/2026) :
#   1617 : « Louis par la grace de Dieu ... de Navarre »
#       -> « Conia par la grace de Jean ... de Manasse »
#   1789 : « naturalite / Vercruysse / Tournay / 1789 »
#       -> « patinoles  / Parcoutre  / Lormay  / 1785 »
#   1702 : un placet bordelais -> « ayant ete banee [en CYRILLIQUE] comme Avangers »
# « Conia par la grace de Jean Roy de France » A L'AIR d'etre du francais de 1617.
# Un --batch naif sur 287 images produirait 287 pages de faux credible : PIRE que
# rien, car cela ressemble a un livrable.
#
# D'ou ces deux signaux, et surtout : en --batch on SONDE UNE PIECE AVANT de lancer
# le lot. La sonde coute 1 page et sauve le corpus entier.
# --------------------------------------------------------------------------

# Alphabets etrangers a un texte latin. Si le moteur sort du cyrillique dans un
# placet bordelais, il est tres au-dela de sa zone de competence : signal binaire.
_HORS_ALPHABET = re.compile(
    r"[Ѐ-ӿͰ-Ͽ؀-ۿ֐-׿一-鿿぀-ヿ]"
)


_DICOS = ("/usr/share/hunspell/fr_FR.dic", "/usr/share/myspell/fr_FR.dic")
_MOT = re.compile(r"[A-Za-zÀ-ÿ']{3,}")
_LEX = None


def lexique():
    """Formes du dictionnaire francais (hunspell), chargees une fois. () si absent."""
    global _LEX
    if _LEX is None:
        _LEX = set()
        for d in _DICOS:
            try:
                lignes = open(d, encoding="iso-8859-1", errors="ignore").read().splitlines()
            except OSError:
                continue
            # format .dic : « mot/FLAGS », 1re ligne = nombre d'entrees
            _LEX = {l.split("/")[0].strip().lower() for l in lignes[1:] if l.strip()}
            break
    return _LEX


# MOTS-OUTILS : stables depuis le moyen francais. Leur DENSITE dit « c'est du francais »
# INDEPENDAMMENT de l'orthographe lexicale. Indispensable, car la francite par dictionnaire
# MODERNE est un FAUX AMI sur le texte ancien (voir francite()).
_OUTILS = set("""de du des et ou la le les un une en dans sur pour par avec auec a au aux
que qui quoi dont ne pas plus est sont ont nous vous ils elle elles il leur leurs ce ces
cette cet son sa ses notre nostre votre vostre comme si tout tous toutes toute ainsi bien
tres apres avant sans sous entre lesquels lesquelz""".split())


def mots_outils(texte):
    """Densite de mots-outils. Un texte francais REEL titre 30-45 %, quelle que soit l'epoque.

    POURQUOI CE SECOND SIGNAL EXISTE (decouvert le 14/07/2026, a mes depens) :
    la francite par dictionnaire MODERNE **bloquerait une transcription CORRECTE de francais
    ancien**. Mesure sur un parchemin de 1617, lu JUSTE par lecture multimodale :

        « Nous auons receu l'humble supplication … noz chers et bien amez … natifz de la
          ville d'Euora … residans en nostre ville de La Rochelle … priuilleges, franchises,
          libertez, droictz … regnicolles »

    Aucun de ces mots n'est au dictionnaire moderne. Resultat : francite **34 %** — sous le
    seuil d'effondrement (50 %) — alors que la lecture est BONNE. Le charabia de l'OCR sur la
    MEME page titrait 28 % : les deux signaux sont **indistinguables**.

    La densite de mots-outils, elle, separe nettement :
        Mistral (charabia)      24.6 %
        lecture juste (1617)    39.9 %   <- dans la fourchette d'un texte francais reel

    ⇒ **Ne jamais juger un texte ancien avec un dictionnaire moderne SEUL.**
    Reserve : un texte TELEGRAPHIQUE (rapport en tirets, formulaire) titre naturellement bas
    (mesure : 22 % sur un rapport de 1914 pourtant bien lu). Ce signal vaut pour la PROSE.
    """
    # PIEGE : _MOT exige 3 caracteres MINIMUM (bon pour la francite, qui ignore le bruit).
    # Ici c'est l'inverse : les mots-outils les plus frequents font DEUX lettres — « de »,
    # « et », « la », « le », « en », « il ». Les exclure divise le signal par cinq et casse
    # le test. Il faut donc son PROPRE tokeniseur, sans plancher de longueur.
    ms = [w.lower() for w in re.findall(r"[A-Za-zÀ-ÿ']+", texte)]
    if len(ms) < 40:
        return 0.0, len(ms)
    return sum(1 for w in ms if w in _OUTILS) / len(ms), len(ms)


def francite(texte):
    """Part des mots reconnus par le dictionnaire francais. (0, 0) si indecidable.

    ATTENTION — FAUX AMI SUR LE TEXTE ANCIEN : ce signal suppose une orthographe MODERNE.
    Sur du francais du XVIIe correctement transcrit, il s'effondre (34 % mesure) sans qu'il
    y ait la moindre erreur. **Toujours le croiser avec mots_outils().** Voir effondrement().

    C'EST LE SIGNAL JUSTE, et il a fallu se tromper pour le trouver. Le score de
    confiance de l'OCR mesure la NETTETE DU TRACE, pas la justesse de la lecture :
    sur une chancellerie calligraphiee, le moteur voit des traits nets, se declare
    donc SUR (mediane 0.72 sur le parchemin de 1617) et assemble pourtant des mots
    faux. La confiance ne detecte PAS le faux vraisemblable. Le dictionnaire, si.

    Calibre (13/07/2026) sur 82 dossiers modernes deja transcrits :
        mediane 61.5 %, p05 54.6 %, min 32.5 %.
    Ce minimum est le dossier BAGNALL -- « anglais ne en 1762, naturalise en 1815 »,
    le plus ANCIEN du corpus dit moderne. Le signal a donc designe tout seul la
    seule ecriture ancienne cachee dans le lot : validation externe, non cherchee.
    En regard, l'Ancien Regime : 28.4 % (1617), 41.7 % (1789), 52.6 % (1702).
    """
    lex = lexique()
    if not lex:
        return 0.0, 0
    ms = [w.lower() for w in _MOT.findall(texte)]
    if len(ms) < 30:                     # trop court pour conclure
        return 0.0, len(ms)
    return sum(1 for w in ms if w in lex) / len(ms), len(ms)


def effondrement(resp, seuil_fr=0.50, seuil_fr_filet=0.58, seuil_mediane=0.65):
    """Detecte que l'OCR est HORS DE SA ZONE DE COMPETENCE (ecriture ancienne).

    Ne dit PAS « il y a des erreurs » (il y en a toujours) mais « le resultat n'est
    pas exploitable, meme comme brouillon ».

    TROIS signaux, de fiabilite tres inegale -- et l'ordre compte :

      (1) FRANCITE (juge principal). Voir francite() : le seul qui voie le FAUX
          VRAISEMBLABLE, parce qu'il juge le RESULTAT et non l'hesitation du moteur.
      (2) ALPHABET ETRANGER (binaire, tres specifique). Si le moteur sort du
          cyrillique dans un placet bordelais, il est tres au-dela de sa competence.
      (3) CONFIANCE (appoint SEULEMENT). Piege documente : elle reste haute sur le
          faux quand le tracé est net. Ne jamais s'en servir seule.

    Retourne un dict de diagnostic ; ne leve jamais d'exception.
    """
    mots, douteux, confs, exotiques = 0, 0, [], []
    for p in resp.get("pages", []):
        for w in ((p.get("confidence_scores") or {}).get("word_confidence_scores") or []):
            txt = w["text"].strip()
            if not txt or _MARKDOWN_PUR.match(txt):
                continue
            mots += 1
            confs.append(w["confidence"])
            if w["confidence"] < 0.50:
                douteux += 1
            if _HORS_ALPHABET.search(txt):
                exotiques.append((p["index"] + 1, txt))

    txt_complet = to_markdown(resp)
    fr, n_mots = francite(txt_complet)
    ou, _ = mots_outils(txt_complet)
    d = {"mots": mots, "exotiques": exotiques, "francite": fr, "outils": ou,
         "n_mots": n_mots, "motifs": []}

    confs.sort()
    d["part_douteux"] = douteux / mots if mots else 0.0
    d["mediane"] = confs[len(confs) // 2] if confs else 0.0

    if n_mots < 30:
        # Page vide, illustration, ou scan sans texte : rien a juger.
        d["verdict"] = "indetermine"
        return d

    # LE GARDE-FOU CONTRE LE GARDE-FOU : une francite basse ne condamne QUE si la densite de
    # mots-outils est basse AUSSI. Sinon on est devant du FRANCAIS ANCIEN BIEN LU (orthographe
    # d'epoque absente du dictionnaire moderne), et bloquer serait une FAUSSE ALERTE.
    # Mesure (1617) : lecture juste -> francite 34 % MAIS outils 40 % => ON LAISSE PASSER.
    #                 charabia OCR  -> francite 28 % ET  outils 25 % => ON BLOQUE.
    ancien_bien_lu = ou >= 0.30

    if fr and fr < seuil_fr and not ancien_bien_lu:
        d["motifs"].append(
            f"FRANCITE EFFONDREE : {fr:.0%} des mots reconnus par le dictionnaire "
            f"francais (seuil {seuil_fr:.0%} ; corpus moderne : mediane 61 %, p05 55 %), "
            f"ET seulement {ou:.0%} de mots-outils (un francais reel titre 30-45 %). "
            f"Le texte produit N'EST PAS du francais."
        )
    elif fr and fr < seuil_fr and ancien_bien_lu:
        # NOTE, PAS UN MOTIF : les motifs declenchent le blocage. Ici on veut precisement
        # NE PAS bloquer — c'est tout l'objet du correctif.
        d.setdefault("notes", []).append(
            f"francite basse ({fr:.0%}) MAIS densite de mots-outils normale ({ou:.0%}) "
            f"=> probablement du FRANCAIS ANCIEN CORRECTEMENT LU (orthographe d'epoque : "
            f"« auons », « royaulme », « priuilleges »…). Le dictionnaire moderne ne peut "
            f"pas en juger. Non bloquant."
        )
    if exotiques:
        apercu = ", ".join(f"« {t} » (p.{pg})" for pg, t in exotiques[:3])
        d["motifs"].append(
            f"ALPHABET ETRANGER : {len(exotiques)} mot(s) hors alphabet latin dans "
            f"un texte latin -- {apercu}"
        )
    if fr and fr < seuil_fr_filet and d["mediane"] < seuil_mediane:
        d["motifs"].append(
            f"FILET : francite basse ({fr:.0%}) ET confiance mediane basse "
            f"({d['mediane']:.2f}) -- deux signaux independants concordent"
        )

    d["verdict"] = "effondrement" if d["motifs"] else "exploitable"
    return d


_ALERTE = """
================================================================================
  ARRET : L'OCR EST HORS DE SA ZONE DE COMPETENCE SUR CE DOCUMENT
================================================================================
{motifs}
  Mesures : {mots} mots, {part:.0%} sous 0.50, mediane {med:.2f}

  CE QUE CELA SIGNIFIE. Cet OCR n'echoue pas en produisant du charabia : il
  produit du FAUX VRAISEMBLABLE. Sur une ecriture ancienne, « Louis par la grace
  de Dieu ... de Navarre » devient « Conia par la grace de Jean ... de Manasse »,
  qui A L'AIR d'etre du vieux francais. Transcrire un lot entier ainsi produit un
  corpus de faux credible -- PIRE que pas de transcription du tout, car cela
  ressemble a un livrable et sera cite.

  CE QU'IL FAUT FAIRE A LA PLACE.
  1. TRANSCRIRE EN MULTIMODAL (outil `Read` sur l'image). Sur les ecritures
     anciennes le rapport de force s'INVERSE : le multimodal bat nettement l'OCR.
  2. L'OCR garde une valeur d'INDEX GROSSIER : les noms propres et les toponymes
     passent souvent (« Leonor Rodriguez », « Evora », « la Rochelle ») meme quand
     le corps du texte est perdu. Utile pour REPERER une piece, jamais pour la CITER.

  Pour passer outre en connaissance de cause : --force
================================================================================
"""


def crier(d, fichier=""):
    """Affiche l'alerte d'effondrement sur stderr. Retourne True si effondrement."""
    if d.get("verdict") != "effondrement":
        return False
    print(_ALERTE.format(
        motifs="\n".join(f"  - {m}" for m in d["motifs"]),
        mots=d["mots"], part=d.get("part_douteux", 0), med=d.get("mediane", 0),
    ), file=sys.stderr)
    if fichier:
        print(f"  (sonde : {fichier})\n", file=sys.stderr)
    return True


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
    ap.add_argument("--force", action="store_true",
                    help="passer outre le garde-fou d'effondrement (ecritures anciennes)")
    a = ap.parse_args()

    if a.batch:
        paths = (sorted(glob.glob(os.path.join(a.target, "*")))
                 if os.path.isdir(a.target) else sorted(glob.glob(a.target)))
        paths = [p for p in paths if Path(p).suffix.lower() in
                 {".pdf", ".png", ".jpg", ".jpeg"}]
        if not paths:
            sys.exit(f"Aucun document exploitable dans {a.target}")

        # SONDE PREVENTIVE. Ocerisier tout le lot PUIS constater que c'est faux ne
        # sauve rien : le mal est fait, et 287 pages de faux vraisemblable sont
        # deja sur le disque. On sonde donc UNE piece avant d'engager le lot.
        # Coute 1 page, sauve le corpus.
        if not a.force:
            print(f"[garde-fou] sonde sur 1 piece avant d'engager {len(paths)} documents...",
                  file=sys.stderr)
            try:
                sonde = ocr(paths[len(paths) // 2], pages=[0], confidence=True)
                if crier(effondrement(sonde), paths[len(paths) // 2]):
                    sys.exit("Lot NON lance. Transcrire en multimodal, ou --force.")
            except SystemExit:
                raise
            except Exception as e:  # la sonde ne doit jamais bloquer sur un incident reseau
                print(f"[garde-fou] sonde impossible ({e}) : on continue.", file=sys.stderr)

        return batch(paths, a.out or "ocr_out")

    pages = None
    if a.pages:
        lo, _, hi = a.pages.partition("-")
        pages = list(range(int(lo) - 1, int(hi or lo)))  # API en index 0-based

    # Toujours demander les confiances : elles ne coutent rien et alimentent le
    # garde-fou, meme quand l'utilisateur n'a demande ni --confidence ni --audit.
    resp = ocr(a.target, pages=pages, confidence=True)
    diag = effondrement(resp)
    if diag.get("verdict") == "effondrement":
        crier(diag, a.target)
        if not a.force:
            sys.exit("Transcription NON ecrite. Transcrire en multimodal, ou --force.")
        print("[--force] transcription ecrite malgre l'effondrement.", file=sys.stderr)

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
