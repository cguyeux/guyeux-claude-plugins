#!/usr/bin/env python3
"""Apparier les QUESTIONS imprimees d'un formulaire a leurs REPONSES manuscrites.

LE PROBLEME. Sur un formulaire administratif a deux colonnes (questions imprimees
a gauche, reponses manuscrites a droite), l'OCR **decolonne** : il transcrit
toutes les questions en un bloc, puis toutes les reponses en un autre, SANS les
apparier. Pire, le decalage n'est pas constant : **une question sans reponse ne
produit aucune ligne**, si bien qu'un appariement positionnel derape. Aucun
ancrage textuel ne rattrape cela — ce n'est pas un probleme de segmentation, mais
d'ALIGNEMENT.

LA SOLUTION. Elle est GEOMETRIQUE. `include_blocks=True` renvoie les boites
englobantes, et la reponse manuscrite est tracee A LA MEME HAUTEUR que sa
question. On apparie donc par recouvrement vertical (y), pas par l'ordre du texte.

DEUX PIEGES, tous deux constates :
  1. Les questions se terminent par des POINTS DE CONDUITE (« Quelle est leur
     residence ? . . . »). Un test naif `endswith('?')` les rejette et casse tout.
  2. Les colonnes ne se separent pas toujours proprement en x (selon le scan).
     Ne PAS se fier a x pour distinguer question et reponse : se fier au TEXTE
     (une question imprimee finit par « ? » ou est une rubrique en capitales), et
     a y pour l'appariement.

Valide sur le formulaire de naturalisation (loi du 26 juin 1889) :
  ARMENGOL 1913 -> « Pour quel motif ? » / « pour acquerir la qualite de francais
                    et beneficier des retraites ouvrieres »
  AMIGO    1927 -> « Pour quel motif ? » / « Pour que toute sa famille fasse son
                    devoir de francais »
Les deux appariements sont conformes a la lecture de l'encre.

Usage :
    python3 pair_form.py <fichier.pdf> --pages 9        # 1-based
    python3 pair_form.py <fichier.pdf> --pages 6-10 --json
"""

import argparse
import json
import os
import re
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mistral_ocr as M  # noqa: E402

# Une rubrique imprimee : « OBSERVATIONS. », « SITUATION DE FORTUNE », ...
RUBRIQUE = re.compile(r"^[A-ZÉÈÀÇŒ\s.'’-]{6,}\.?$")
TOLERANCE = 28  # px de decalage vertical admis entre une question et sa reponse


def est_question(txt):
    """Vrai si le bloc est une question ou une rubrique IMPRIMEE du formulaire."""
    t = txt.strip()
    return t.rstrip(" .·…:-").endswith("?") or bool(RUBRIQUE.match(t))


def apparier(blocks, tolerance=TOLERANCE):
    """[(question, reponse|None)], apparies par proximite verticale."""
    qs = [b for b in blocks if est_question(b["content"])]
    reps = [b for b in blocks
            if not est_question(b["content"])
            and b["content"].strip()
            and not b["content"].lstrip().startswith("![")]
    pris, out = set(), []
    for q in sorted(qs, key=lambda b: b["top_left_y"]):
        qy = (q["top_left_y"] + q["bottom_right_y"]) / 2
        best, bd = None, float("inf")
        for i, r in enumerate(reps):
            if i in pris:
                continue
            ry = (r["top_left_y"] + r["bottom_right_y"]) / 2
            d = abs(ry - qy)
            if d < bd:
                best, bd = i, d
        if best is not None and bd <= tolerance:
            pris.add(best)
            out.append((q["content"].strip(), reps[best]["content"].strip()))
        else:
            out.append((q["content"].strip(), None))
    return out


def blocs(pdf, pages):
    """Blocs avec boites englobantes, pour une liste de pages 0-based."""
    url = M.upload(pdf)
    payload = {"model": M.MODEL,
               "document": {"type": "document_url", "document_url": url},
               "pages": pages, "include_blocks": True}
    req = urllib.request.Request(
        f"{M.BASE}/ocr", data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {M.key()}",
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as resp:
        r = json.load(resp)
    return {p["index"] + 1: (p.get("blocks") or []) for p in r["pages"]}


def main():
    ap = argparse.ArgumentParser(
        description="Apparier les questions imprimees d'un formulaire a leurs "
                    "reponses manuscrites, par geometrie (boites englobantes).")
    ap.add_argument("pdf")
    ap.add_argument("--pages", required=True, help="page ou plage 1-based, ex. 9 ou 6-10")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    lo, _, hi = a.pages.partition("-")
    pages0 = list(range(int(lo) - 1, int(hi or lo)))

    resultat = {}
    for page, bl in blocs(a.pdf, pages0).items():
        paires = [{"question": q, "reponse": r} for q, r in apparier(bl) if r]
        if paires:
            resultat[page] = paires

    if a.json:
        print(json.dumps(resultat, ensure_ascii=False, indent=2))
        return
    for page, paires in resultat.items():
        print(f"--- page {page} ---")
        for p in paires:
            print(f"  Q  {p['question']}")
            print(f"  R  {p['reponse']}\n")


if __name__ == "__main__":
    main()
