#!/usr/bin/env python3
"""Cohérence INTERNE des entrées BibTeX : le DOI dit-il le même éditeur que le journal ?

Pourquoi cet outil existe. Le 2026-07-11, une passe /bib-check a marqué `verified` une
entrée CHIMÉRIQUE, fusion de deux articles distincts :

    @article{biswas2019_residence_time_psf,
      title   = {Stability and mean residence times for hybrid epithelial/mesenchymal ...},
      journal = {Physical Biology},                 <- IOP Publishing
      doi     = {10.1371/journal.pbio.3001113},     <- PLOS  (INCOMPATIBLE)
      pmid    = {33626035},                         <- pointe vers le papier PLOS
    }

Un article de *Physical Biology* NE PEUT PAS porter un DOI `10.1371/journal.pbio`. La
contradiction est décidable HORS LIGNE, en une ligne, et pourtant la passe de vérification
l'a manquée : elle interrogeait PubMed AVEC LE PMID, donc elle a récupéré le papier PLOS,
qui existe, et a validé. **Vérifier qu'un identifiant résout ne prouve rien sur la
COHÉRENCE de l'entrée qui le porte.** L'entrée portait une affirmation load-bearing du
manuscrit (ΔNp63α comme facteur de stabilité phénotypique).

Ce script attrape cette classe d'erreur sans réseau : le préfixe DOI encode l'éditeur.

Usage :
    python3 doi_coherence.py references.bib
    python3 doi_coherence.py references.bib --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# CONCEPTION — et pourquoi la première version était fausse.
#
# Premier réflexe : « préfixe DOI -> éditeur, puis vérifier que le journal est un journal de
# cet éditeur ». INUTILISABLE : Elsevier (10.1016) publie des MILLIERS de titres. La liste ne
# peut pas être complétée, donc tout journal absent de la liste devient un faux positif. Test
# réel : 15 alertes, **15 fausses** (Journal of Theoretical Biology, Biophysical Journal...
# sont bel et bien chez Elsevier). Un test qui crie à tort est un test qu'on apprend à
# ignorer : pire qu'absent.
#
# Conception correcte : partir d'une LISTE BLANCHE de journaux dont l'éditeur est CERTAIN, et
# n'alerter QUE sur ceux-là. Un journal inconnu de la table n'est pas vérifié — et c'est très
# bien : mieux vaut ne rien dire que dire faux. La table s'étend au fil des besoins, sans
# jamais générer de bruit.
JOURNAL_PREFIX = {
    # journal (normalise, minuscules)          : prefixe DOI attendu
    "plos biology":                              "10.1371",
    "plos one":                                  "10.1371",
    "plos computational biology":                "10.1371",
    "plos genetics":                             "10.1371",
    "plos pathogens":                            "10.1371",
    "physical biology":                          "10.1088",
    "science":                                   "10.1126",
    "science advances":                          "10.1126",
    "science translational medicine":            "10.1126",
    "science signaling":                         "10.1126",
    "nature":                                    "10.1038",
    "nature communications":                     "10.1038",
    "nature methods":                            "10.1038",
    "nature genetics":                           "10.1038",
    "nature biotechnology":                      "10.1038",
    "nature cell biology":                       "10.1038",
    "nature reviews cancer":                     "10.1038",
    "scientific reports":                        "10.1038",
    "oncogene":                                  "10.1038",
    "npj systems biology and applications":      "10.1038",
    "elife":                                     "10.7554",
    "proceedings of the national academy of sciences": "10.1073",
    "new england journal of medicine":           "10.1056",
    "cancer research":                           "10.1158",
    "cancer discovery":                          "10.1158",
    "clinical cancer research":                  "10.1158",
    "genome research":                           "10.1101",
    "genes & development":                       "10.1101",
    # bioRxiv/medRxiv ont MIGRE de 10.1101 vers 10.64898 (constate 2026-07-11 sur un
    # preprint d'avril 2026). Un journal peut changer de prefixe : la valeur est donc
    # une LISTE, jamais un scalaire. Sans cela, l'outil crie sur des entrees valides.
    "biorxiv":                                   ["10.1101", "10.64898"],
    "medrxiv":                                   ["10.1101", "10.64898"],
    "nucleic acids research":                    "10.1093",
    "bioinformatics":                            "10.1093",
    "molecular biology and evolution":           "10.1093",
    "journal of clinical oncology":              "10.1200",
    "the lancet":                                "10.1016",
    "cell":                                      "10.1016",
    "molecular systems biology":                 "10.15252",
    "the embo journal":                          "10.15252",
}

PUBLISHER_OF_PREFIX = {
    "10.1371": "PLOS", "10.1088": "IOP Publishing", "10.1126": "AAAS",
    "10.1038": "Nature Portfolio", "10.7554": "eLife", "10.1073": "PNAS",
    "10.1056": "NEJM", "10.1158": "AACR", "10.1101": "Cold Spring Harbor",
    "10.1093": "Oxford University Press", "10.1200": "ASCO", "10.1016": "Elsevier",
    "10.15252": "EMBO Press", "10.3390": "MDPI", "10.1002": "Wiley",
    "10.64898": "Cold Spring Harbor (bioRxiv/medRxiv, nouveau prefixe)",
    "10.1186": "BMC", "10.1128": "ASM", "10.3389": "Frontiers",
}


def _norm(j: str) -> str:
    j = re.sub(r"[{}\\]", "", j).lower().strip()
    j = re.sub(r"^the\s+", "", j)
    return re.sub(r"\s+", " ", j)


ENTRY = re.compile(r"@(\w+)\s*\{\s*([^,]+),(.*?)\n\}", re.S)


def field(body: str, name: str) -> str | None:
    m = re.search(rf"\b{name}\s*=\s*[{{\"]([^}}\"]*)", body, re.I)
    return m.group(1).strip() if m else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("bib")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    text = Path(a.bib).read_text(encoding="utf-8")
    findings, checked = [], 0

    for m in ENTRY.finditer(text):
        key, body = m.group(2).strip(), m.group(3)
        doi = field(body, "doi")
        journal = field(body, "journal") or field(body, "booktitle") or ""
        if not doi or not journal:
            continue
        expected = JOURNAL_PREFIX.get(_norm(journal))
        if not expected:
            continue          # journal hors liste blanche : on ne dit RIEN (pas de bruit)
        allowed = expected if isinstance(expected, list) else [expected]
        checked += 1
        prefix = doi.split("/")[0].strip()
        if prefix not in allowed:
            findings.append({
                "key": key, "doi": doi, "journal": journal,
                "expected_prefix": " ou ".join(allowed),
                "doi_publisher": PUBLISHER_OF_PREFIX.get(prefix, "editeur inconnu"),
                "expected_publisher": PUBLISHER_OF_PREFIX.get(allowed[0], "?"),
                "verified": field(body, "verified"),
                "issue": f"le journal « {journal} » est publie par "
                         f"{PUBLISHER_OF_PREFIX.get(allowed[0], '?')} (prefixe {' ou '.join(allowed)}), "
                         f"mais le DOI porte le prefixe {prefix} "
                         f"({PUBLISHER_OF_PREFIX.get(prefix, 'editeur inconnu')})",
            })

    if a.json:
        print(json.dumps({"checked": checked, "findings": findings}, indent=2, ensure_ascii=False))
        return 1 if findings else 0

    print(f"Coherence DOI <-> journal : {checked} entrees verifiables "
          f"(journal en liste blanche), {len(findings)} incoherence(s)\n")
    for f in findings:
        v = f" [marquee verified = {f['verified']} !]" if f["verified"] else ""
        print(f"  INCOHERENT  @{f['key']}{v}")
        print(f"     journal : {f['journal']}")
        print(f"     doi     : {f['doi']}  -> {f['doi_publisher']}")
        print(f"     attendu : prefixe {f['expected_prefix']} ({f['expected_publisher']})")
        print(f"     {f['issue']}")
        print("     => entree probablement CHIMERIQUE (deux articles fusionnes). "
              "Reconstruire depuis la source primaire.\n")
    if not findings:
        print("  Aucune incoherence editeur/journal detectee.")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
