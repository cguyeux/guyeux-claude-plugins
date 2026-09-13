#!/usr/bin/env python3
"""Dérive entre un manuscrit écrit et son `plan_narratif.md`, pour /narratif drift.

Le plan décide, avant rédaction, du temps et du lieu de chaque fait, et le squelette
est émis depuis lui avec une ligne d'allocation par section :

    \\subsection{Exclusive markers of the clade}
    % narratif: maillon M2 | bascule B1 -> figure 2 | taille visee 600 mots
    % question du lecteur : comment savoir que ce n'est pas un artefact de mapping ?

Ce script relit le manuscrit contre ces lignes et rend trois choses :

  1. SECTION NON PLANIFIÉE — une section substantielle sans ligne `% narratif:`.
     Personne ne l'a décidée : c'est la section « et aussi », celle qui existe
     parce que le travail a été fait. C'est le générateur de verbosité, et c'est
     la mesure la plus utile du script.

  2. DÉPASSEMENT — une section très au-delà de la taille visée par son plan. Le
     seuil est lâche (+50 %) : on cherche la dérive structurelle, pas le mot près.

  3. SUPPLÉMENTAIRE DÉVELOPPÉ DANS LE CORPS — un acquis classé SUPPLÉMENTAIRE au
     plan dont le vocabulaire sature une section du corps. SIGNAL, jamais verdict :
     l'appariement est lexical, et un renvoi d'une phrase (rang MENTION) déclenche
     légitimement quelques occurrences. Le tri reste humain.

La dérive n'est pas interdite : la rédaction découvre des choses, et un rang peut se
révéler faux. Ce qui est interdit, c'est que le plan et le manuscrit se contredisent
en silence. Une dérive constatée se corrige au plan, datée, avec sa raison.

Usage :
    python3 plan_vs_manuscrit.py [projet]
    python3 plan_vs_manuscrit.py [projet] --tex article/main.tex --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent.parent / "deai-latex" / "scripts"))
sys.path.insert(0, str(_HERE))

try:                                    # réutilisé, jamais réécrit : cf. /deai-latex
    from latex_metrics import count_rendered_words      # type: ignore
    from content_economy import resolve_inputs, take_body, match_brace  # type: ignore
except ImportError as exc:              # pragma: no cover
    print(f"Scripts de /deai-latex introuvables ({exc}). "
          "Ce script les réutilise plutôt que de recompter les mots.",
          file=sys.stderr)
    raise SystemExit(3)

from plan_status import (resoudre, tri_du_plan, _read, mots_cle,  # type: ignore
                         apparie, rows)

SEUIL_DEPASSEMENT = 1.5      # au-delà de +50 % de la taille visée
MOTS_SECTION_UTILE = 80      # en-deçà, une section sans plan n'est pas un signal


def unites(body: str) -> list[dict]:
    """Découpe sur \\section ET \\subsection, en GARDANT les commentaires.

    `content_economy.split_sections` ne coupe qu'aux \\section et travaille sur un
    corps déjà décommenté : les deux ne conviennent pas ici, puisque l'allocation
    vit précisément dans un commentaire et descend au niveau sous-section.
    """
    marks = list(re.finditer(r"\\(sub)?section\*?\s*(?:\[[^\]]*\])?\{", body))
    out: list[dict] = []
    for i, m in enumerate(marks):
        end_t = match_brace(body, m.end() - 1)
        titre = body[m.end():end_t] if end_t > 0 else "?"
        start = (end_t + 1) if end_t > 0 else m.end()
        stop = marks[i + 1].start() if i + 1 < len(marks) else len(body)
        corps = body[start:stop]
        out.append({
            "niveau": "subsection" if m.group(1) else "section",
            "titre": re.sub(r"\s+", " ", titre).strip(),
            "corps": corps,
        })
    return out


def allocation(corps: str) -> dict | None:
    """Ligne `% narratif: ...` dans l'ouverture de la section."""
    tete = "\n".join(corps.splitlines()[:8])
    m = re.search(r"^\s*%\s*narratif\s*:\s*(.+)$", tete, re.M | re.I)
    if not m:
        return None
    txt = m.group(1)
    n = re.search(r"taille\s+vis[ée]{1,2}e?\s+(\d{2,5})", txt, re.I)
    q = re.search(r"^\s*%\s*question du lecteur\s*:\s*(.+)$", tete, re.M | re.I)
    return {
        "brut": txt.strip(),
        "maillons": re.findall(r"\bM\d+\b", txt),
        "bascules": re.findall(r"\bB\d+\b", txt),
        "cible": int(n.group(1)) if n else 0,
        "question": q.group(1).strip() if q else "",
    }


def collecte(root: Path, tex_rel: str) -> dict:
    tex = root / tex_rel
    d: dict = {"racine": str(root), "tex": str(tex), "alertes": [], "info": [],
               "sections": [], "non_planifiees": [], "depassements": [],
               "supp_dans_corps": []}
    if not tex.exists():
        d["alertes"].append(f"manuscrit introuvable : {tex}")
        return d

    body = take_body(resolve_inputs(tex))
    us = unites(body)
    total = 0
    for u in us:
        n = count_rendered_words(u["corps"])
        total += n if u["niveau"] == "section" else 0
        a = allocation(u["corps"])
        # `corps` est requis plus bas (detection d'un item SUPPLEMENTAIRE reste dans le
        # corps) : son absence faisait planter collecte() par KeyError. Corrige 2026-09-12.
        d["sections"].append({"titre": u["titre"], "niveau": u["niveau"],
                              "mots": n, "alloc": a, "corps": u["corps"]})
        if a is None:
            if n >= MOTS_SECTION_UTILE:
                d["non_planifiees"].append((u["titre"], n))
        elif a["cible"] and n > a["cible"] * SEUIL_DEPASSEMENT:
            d["depassements"].append(
                (u["titre"], n, a["cible"], round(100 * (n / a["cible"] - 1))))

    d["mots_corps"] = count_rendered_words(body)
    d["info"].append(f"{len(us)} unité(s), corps à {d['mots_corps']} mots rendus")

    plan_p = root / "plan_narratif.md"
    if not plan_p.exists():
        d["alertes"].append(
            "aucun `plan_narratif.md` : rien à comparer. Lancer `/narratif`, ou "
            "`/narratif reprise` pour reconstruire le plan depuis ce manuscrit.")
        if d["non_planifiees"]:
            d["info"].append("les sections listées le sont donc TOUTES, faute de plan")
        return d

    ptxt = _read(plan_p)
    tri = tri_du_plan(ptxt)
    d["tri"] = len(tri)
    supp = [t["acquis"] for t in tri if t["rang"] in ("SUPPLEMENTAIRE",)]

    for titre in supp:                       # signal lexical, jamais un verdict
        cle = mots_cle(titre)
        if len(cle) < 3:
            continue
        for s in d["sections"]:
            if s["niveau"] != "subsection" or s["mots"] < 150:
                continue
            vus = mots_cle(s["corps"]) & cle
            if len(vus) / len(cle) >= 0.6:
                d["supp_dans_corps"].append((titre[:70], s["titre"][:50]))
                break

    # sections planifiées portant un maillon inconnu du plan
    connus = {m[0] for m in rows(ptxt, "M")}
    for s in d["sections"]:
        if s["alloc"]:
            inc = [m for m in s["alloc"]["maillons"] if m not in connus]
            if inc:
                d["alertes"].append(
                    f"« {s['titre'][:44]} » invoque {', '.join(inc)}, absent du plan")

    if d["non_planifiees"]:
        d["alertes"].append(
            f"{len(d['non_planifiees'])} section(s) sans ligne `% narratif:` "
            "(sections « et aussi »)")
    if d["depassements"]:
        d["alertes"].append(f"{len(d['depassements'])} section(s) au-delà de +50 %")
    if d["supp_dans_corps"]:
        d["alertes"].append(
            f"{len(d['supp_dans_corps'])} item(s) classé(s) SUPPLÉMENTAIRE dont le "
            "vocabulaire sature une section du corps (signal lexical, à trancher à l'œil)")
    return d


def rendre(d: dict) -> str:
    L = [f"Dérive plan ↔ manuscrit — {d['tex']}"]
    for i in d["info"]:
        L.append(f"  · {i}")
    if d["non_planifiees"]:
        L.append("  SECTIONS SANS ALLOCATION (personne ne les a planifiées)")
        for t, n in sorted(d["non_planifiees"], key=lambda x: -x[1])[:20]:
            L.append(f"    {n:6d} mots  {t[:66]}")
    if d["depassements"]:
        L.append("  DÉPASSEMENTS")
        for t, n, c, pct in sorted(d["depassements"], key=lambda x: -x[3]):
            L.append(f"    {n:6d} mots pour {c} visés (+{pct} %)  {t[:52]}")
    if d["supp_dans_corps"]:
        L.append("  SUPPLÉMENTAIRE DÉVELOPPÉ DANS LE CORPS (signal, pas verdict)")
        for a, s in d["supp_dans_corps"]:
            L.append(f"    « {a} »  →  {s}")
    if d["alertes"]:
        L.append("  ALERTES")
        for a in d["alertes"]:
            L.append(f"    - {a}")
    else:
        L.append("  aucune dérive mesurée.")
    L.append("  (une dérive se corrige AU PLAN, datée et motivée ; le silence est le défaut)")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("projet", nargs="?")
    ap.add_argument("--tex", default="article/main.tex")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    root = resoudre(a.projet)
    if root is None:
        print("Aucune racine de projet trouvée (pas de cahier_de_labo.md).",
              file=sys.stderr)
        return 2
    d = collecte(root, a.tex)
    print(json.dumps(d, ensure_ascii=False, indent=2, default=str)
          if a.json else rendre(d))
    return 1 if d["alertes"] else 0


if __name__ == "__main__":
    sys.exit(main())
