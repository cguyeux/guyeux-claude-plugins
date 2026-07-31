#!/usr/bin/env python3
"""Consensus multi-moteurs : le DESACCORD entre lecteurs designe ce qu'il faut arbitrer.

POURQUOI CET OUTIL EXISTE
=========================
Nous avons DEMONTRE (13/07/2026) que le score de confiance d'un OCR est **aveugle au faux
vraisemblable** : sur le parchemin le plus faux d'un fonds d'Ancien Regime (« Louis par la
grace de Dieu … de Navarre » rendu « Conia par la grace de Jean … de Manasse »), la confiance
MEDIANE de Mistral etait de **0,72**. Le moteur mesure la NETTETE DU TRACE, pas la JUSTESSE
DE LA LECTURE : sur une chancellerie calligraphiee, il voit des traits nets, se declare sur,
et assemble des mots faux.

Il fallait donc un signal de remplacement. La FRANCITE (cf. `mistral_ocr.py`) en est un, mais
elle est **globale** : elle dit « cette page est fausse », pas « ce mot-ci est faux ».

**Le desaccord entre deux lecteurs INDEPENDANTS est le signal fin qui manquait.** Il opere au
niveau du MOT, il est orthogonal a la confiance du moteur, et il ne coute que la lecture.

PRINCIPE (emprunte au consensus ROVER de la reconnaissance de parole)
---------------------------------------------------------------------
  - la ou tous les lecteurs s'accordent  -> probablement juste, ne pas arbitrer ;
  - la ou ils divergent                  -> ZONE A ARBITRER SUR L'ENCRE.

CE QUE CET OUTIL NE FAIT PAS, ET IL FAUT LE SAVOIR
--------------------------------------------------
1. **Il ne VOTE PAS.** Avec deux lecteurs, une divergence ne designe pas un gagnant ; avec
   trois, la majorite peut avoir tort de facon CORRELEE (voir 2). L'outil **signale**, il ne
   tranche pas. **Seule la lecture de l'encre tranche** (doctrine des trois signaux).
2. **Il ne detecte QUE les erreurs NON CORRELEES.** Deux modeles multimodaux entraines sur du
   texte moderne partagent un biais massif : ils **normalisent la langue du scripteur**. Tous
   deux « corrigeront » silencieusement `carressais` en `caressais`. Le consensus est ALORS
   UNANIME ET FAUX. C'est le piege le plus grave, et il est structurel.
3. **Il ne franchit pas le mur du HTR.** Benchmark (arXiv 2503.15195) : sur manuscrit
   historique non anglais, les VLM plafonnent a ~41 % de CER contre ~14 % pour un HTR
   specialise. **Additionner deux VLM ne fait pas un HTR.** Sur un fonds ancien, la voie est
   Kraken/Transkribus (cf. [[htr-ecritures-anciennes]]) ; le consensus sert a savoir OU
   REGARDER, pas a transcrire.

USAGE
-----
    # 1. produire les lectures (une par moteur)
    python3 mistral_ocr.py page.jpg -o /tmp/a.txt --force   # moteur A (OCR)
    python3 consensus.py --openai page.jpg -o /tmp/b.txt    # moteur B (GPT multimodal)
    #    moteur C = MOI (Claude) : je lis l'image avec `Read` et j'ecris /tmp/c.txt

    # 2. confronter
    python3 consensus.py --diff /tmp/a.txt /tmp/b.txt /tmp/c.txt -o /tmp/arbitrage.md

La sortie marque chaque divergence  ⟪A:mot_a │ B:mot_b │ C:mot_c⟫  et liste les zones a
arbitrer, dans l'ordre de gravite (nombre de lecteurs en desaccord).
"""
import argparse
import base64
import difflib
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

MODELE_DEFAUT = "gpt-5.5"

# Consigne PALEOGRAPHIQUE, pas « lis ce texte ». La difference est mesurable : sans elle,
# un VLM normalise la graphie et invente pour combler les trous — exactement ce qu'on veut
# eviter quand la langue fautive du scripteur EST la donnee (cf. « carressais »).
PROMPT = (
    "Tu es paleographe. Transcris DIPLOMATIQUEMENT le texte manuscrit de cette image "
    "d'archive francaise ancienne.\n"
    "REGLES STRICTES :\n"
    "- Conserve la graphie d'origine (orthographe, abreviations, majuscules). Ne modernise RIEN.\n"
    "- Preserve les FAUTES du scripteur : elles sont la donnee, pas du bruit.\n"
    "- Mot incertain -> suffixe [?]. Mot illisible -> [...].\n"
    "- N'INVENTE JAMAIS un mot pour combler un trou. Une lacune signalee vaut mieux qu'une "
    "invention plausible : c'est la seule facon d'echouer VISIBLEMENT.\n"
    "- Ne rends QUE la transcription, sans commentaire ni preambule."
)


def openai_lire(path, modele=MODELE_DEFAUT):
    cle = os.environ.get("OPENAI_API_KEY")
    if not cle:
        sys.exit("OPENAI_API_KEY absente de l'environnement (voir ~/.bashrc).")
    b64 = base64.b64encode(Path(path).read_bytes()).decode()
    corps = json.dumps({
        "model": modele,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": PROMPT},
                {"type": "image_url",
                 "image_url": {"url": f"data:image/jpeg;base64,{b64}", "detail": "high"}},
            ],
        }],
        "max_completion_tokens": 4000,
    }).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions", data=corps,
        headers={"Authorization": f"Bearer {cle}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return json.load(r)["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:300]
        if e.code == 429:
            sys.exit(f"OpenAI 429 — quota epuise ou debit depasse.\n{detail}")
        sys.exit(f"OpenAI HTTP {e.code} : {detail}")


_MOT = re.compile(r"\S+")


def mots(txt):
    # On garde la ponctuation collee au mot : une divergence sur « Navarre. » vs « Manasse »
    # doit rester UNE divergence, pas deux.
    return _MOT.findall(re.sub(r"<!--.*?-->", " ", txt))


def confronter(lectures, noms):
    """Aligne N lectures sur la 1re et marque les divergences.

    Retourne (texte_marque, zones). Une « zone » = un point de desaccord, avec ce que
    chaque lecteur y a lu. Aucun vote n'est rendu : SEULE L'ENCRE TRANCHE.
    """
    base = mots(lectures[0])
    # Aligner chaque autre lecture sur la base, par blocs d'egalite (difflib).
    alignes = [base]
    for autre in lectures[1:]:
        m = mots(autre)
        sm = difflib.SequenceMatcher(None, base, m, autojunk=False)
        col: list = [None] * len(base)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                for k in range(i2 - i1):
                    col[i1 + k] = m[j1 + k]
            elif tag == "replace":
                # aligner au mieux, position a position
                for k in range(i2 - i1):
                    col[i1 + k] = m[j1 + k] if j1 + k < j2 else "∅"
            elif tag == "delete":
                for k in range(i1, i2):
                    col[k] = "∅"          # ce lecteur n'a rien lu ici
            # 'insert' : le lecteur a lu un mot en trop -> ignore pour l'alignement
        alignes.append(col)

    sortie, zones = [], []
    for i, mot in enumerate(base):
        lus = [a[i] if a[i] is not None else "∅" for a in alignes]
        if len(set(lus)) == 1:
            sortie.append(mot)
        else:
            marque = " │ ".join(f"{n}:{l}" for n, l in zip(noms, lus))
            sortie.append(f"⟪{marque}⟫")
            zones.append((i, lus, len(set(lus))))
    return " ".join(sortie), zones


def rapport(texte, zones, noms, n_mots):
    out = [texte, "", "---", "", "## Zones à arbitrer SUR L'ENCRE", ""]
    if not zones:
        out.append("Aucune divergence. **Cela ne prouve pas que la lecture est juste** : "
                   "deux modèles peuvent se tromper de la même façon (biais partagé de "
                   "normalisation de la graphie).")
        return "\n".join(out)

    out.append(f"| # | mot n° | " + " | ".join(noms) + " | lecteurs en désaccord |")
    out.append("|---|---|" + "---|" * (len(noms) + 1))
    for r, (i, lus, n) in enumerate(sorted(zones, key=lambda z: -z[2])[:80], 1):
        out.append(f"| {r} | {i} | " + " | ".join(f"`{l}`" for l in lus) + f" | {n} |")

    taux = len(zones) / n_mots if n_mots else 0
    out += [
        "",
        f"**{len(zones)} divergences sur {n_mots} mots ({taux:.0%}).**",
        "",
        "**CE QUE CELA VEUT DIRE, ET CE QUE CELA NE VEUT PAS DIRE.**",
        "- Une divergence = un endroit où **au moins un lecteur s'est trompé**. "
        "Elle dit *où regarder*, jamais *qui a raison*.",
        "- **Ne PAS voter à la majorité** : deux modèles multimodaux partagent un biais "
        "massif (ils **normalisent la graphie du scripteur**) et peuvent être unanimes ET "
        "faux. Mesuré sur ce corpus : « carressais » (deux R, faute de la requérante) "
        "« corrigé » en « caressais ».",
        "- **L'accord n'est pas une preuve.** Le silence du consensus ne vaut rien contre "
        "une erreur corrélée.",
        "- Verdict : **ouvrir l'image aux zones listées** (`Read`, page recadrée, haute "
        "résolution). Seule l'encre tranche.",
        "",
        "**NE PAS INTERPRÉTER LE TAUX GLOBAL COMME UNE MESURE DE QUALITÉ.**",
        "Mesuré (13/07/2026) : **66 %** sur un parchemin de 1617 (effondrement réel) mais aussi "
        "**44 %** sur une page manuscrite de 1914 **bien lue**. Le taux brut mélange deux choses "
        "incomparables :",
        "  1. les **vraies divergences de lecture** (ce qu'on cherche) ;",
        "  2. le **bruit de convention** entre lecteurs — abréviations, `[?]`, `[...]`, ordre de "
        "lecture des colonnes, en-têtes imprimés inclus ou non. Ce bruit est ÉNORME et il "
        "n'indique aucune erreur.",
        "**C'est la LISTE des divergences qui vaut, pas le pourcentage.** Un seuil global "
        "serait un faux ami — exactement le défaut que cet outil existe pour corriger.",
    ]
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(
        description="Consensus multi-moteurs : le désaccord désigne ce qu'il faut arbitrer.")
    ap.add_argument("--openai", metavar="IMAGE",
                    help="lire une image avec un VLM OpenAI et sortir la transcription")
    ap.add_argument("--modele", default=MODELE_DEFAUT, help=f"défaut : {MODELE_DEFAUT}")
    ap.add_argument("--diff", nargs="+", metavar="FICHIER",
                    help="confronter 2 lectures ou plus (fichiers texte)")
    ap.add_argument("--noms", help="noms des lecteurs, séparés par des virgules "
                                   "(défaut : A,B,C…)")
    ap.add_argument("-o", "--out")
    a = ap.parse_args()

    if a.openai:
        txt = openai_lire(a.openai, a.modele)
    elif a.diff:
        if len(a.diff) < 2:
            sys.exit("--diff exige AU MOINS DEUX lectures : le consensus n'a pas de sens seul.")
        lectures = [Path(f).read_text() for f in a.diff]
        noms = (a.noms.split(",") if a.noms
                else [Path(f).stem[:8] for f in a.diff])
        marque, zones = confronter(lectures, noms)
        txt = rapport(marque, zones, noms, len(mots(lectures[0])))
    else:
        ap.error("choisir --openai <image> ou --diff <fichiers>")

    if a.out:
        Path(a.out).write_text(txt)
        print(f"-> {a.out}", file=sys.stderr)
    else:
        print(txt)


if __name__ == "__main__":
    main()
