#!/usr/bin/env python3
"""
Objet     : à la clôture d'une piste (`/pistes done Px`), chercher parmi les
            pistes ENCORE OUVERTES du MÊME `pistes.md` celles que la clôture
            de `Px` répond, ferme ou rend caduques — le miroir de
            `/pistes match`, qui cherche un destinataire à une découverte
            NEUVE à travers tout le dépôt multi-projets, jamais un contrôle
            rétroactif à l'intérieur d'un seul projet.
Entrées   : racine du PROJET (auto-détectée : premier parent avec
            `cahier_de_labo.md`, ou --root), et la référence `Px` qui vient
            d'être close (déjà taguée `[réalisé]`/`[abandonné]` dans le
            fichier au moment de l'appel).
Sorties   : jusqu'à `-k` candidats classés, jamais un verdict — même
            garde-fou que `/pistes match` : un score élevé ne prouve rien,
            c'est à l'agent de lire et de décider.
Réutilisable : oui — générique à tout projet à cahier ; réutilise tel quel
            le moteur BM25 et le parseur de `carrefour.py` (import, pas de
            duplication) plutôt que d'en réécrire une variante.
Projet    : pistes (skill canonique) — exposé par `/pistes done`
Date      : 2026-09-16
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from carrefour import bm25, expand, parse_pistes_tree, tokenize  # noqa: E402
from status import detecter_prefixes  # noqa: E402


def find_project_root(start: Path) -> Path:
    """Premier ancêtre strict (départ inclus) portant `cahier_de_labo.md`."""
    cur = start.resolve()
    for _ in range(8):
        if (cur / "cahier_de_labo.md").is_file():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    return start.resolve()


def load_items(root: Path) -> list[dict]:
    """Items de `pistes.md` ET de `pistes/<RACINE>.md` (architecture index + détail).

    Les racines de fichiers détail ne sont PAS toutes `P` (piste AD, 2026-09-21) : un
    projet hors rail (`N`, `Q`...) ou à racines multi-lettres (`AA`, `AC`, `AD`...) porte
    des fichiers `pistes/N.md`, `pistes/AC.md`, etc. — même défaut de NAMESPACE que celui
    réglé par `AC1` pour `status.py`, ici dans le glob figé `P*.md`. On réutilise
    `status.detecter_prefixes()` (mêmes deux sources : noms de fichiers `pistes/X[0-9]*.md`,
    puis titres `## X<chiffre>` de l'index) plutôt que de dupliquer sa logique de détection.

    Un item porte : ref, text, body, state (ouvert/clos/indéterminé), tokens.
    """
    items: list[dict] = []
    principal = root / "pistes.md"
    if principal.is_file():
        items.extend(parse_pistes_tree(principal))
    detail_dir = root / "pistes"
    if detail_dir.is_dir():
        prefixes = detecter_prefixes(root)
        fichier_re = re.compile(r"^(?:" + "|".join(sorted(prefixes, key=len, reverse=True))
                                 + r")(?:[0-9]+)?\.md$")
        for p in sorted(detail_dir.iterdir()):
            if fichier_re.match(p.name):
                items.extend(parse_pistes_tree(p))
    for it in items:
        full = it["text"] + " " + " ".join(it.get("body", []))
        it["tokens"] = tokenize(full)
        it["_full"] = full
    return items


def cmd_impact(root: Path, ref: str, k: int, min_score: float) -> int:
    items = load_items(root)
    closed = [it for it in items if it["ref"] == ref or it["ref"].startswith(ref + ".")]
    if not closed:
        print(f"référence « {ref} » introuvable dans {root / 'pistes.md'} "
              f"(ni dans pistes/{ref.split('.')[0]}.md)", file=sys.stderr)
        return 1
    query_tokens: list[str] = []
    for it in closed:
        query_tokens.extend(expand(tokenize(it["_full"])))
    closed_refs = {it["ref"] for it in closed}

    open_items = [it for it in items
                  if it["type"] == "question" and it["ref"] not in closed_refs]
    if not open_items:
        print("aucune autre piste ouverte dans ce projet — rien à vérifier.")
        return 0

    scored = bm25(query_tokens, open_items)
    if not scored:
        print("aucun rapprochement lexical avec une piste encore ouverte.")
        return 0

    top = scored[0][0] or 1.0
    shown = 0
    for s, r, why in scored:
        if s / top < min_score:
            break
        print(f"{s / top:4.2f} {r['ref']:8s} {r['text'][:90]:90s} | {','.join(why)}")
        shown += 1
        if shown >= k:
            break
    if shown == 0:
        print("aucun rapprochement au-dessus du seuil — rien à vérifier.")
    else:
        print(f"\n{shown} candidat(s) à vérifier manuellement : un match n'est pas "
              f"une décision, ni une clôture ni une réouverture automatique.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ref", help="référence de la piste qui vient d'être close (ex. P7, N7.a)")
    ap.add_argument("--root", type=Path, default=None,
                     help="racine du projet (défaut : auto-détectée depuis le cwd)")
    ap.add_argument("-k", type=int, default=8)
    ap.add_argument("--min-score", type=float, default=0.35,
                     help="fraction du meilleur score en deçà de laquelle un candidat "
                          "n'est plus affiché (défaut 0.35)")
    a = ap.parse_args()
    root = a.root.resolve() if a.root else find_project_root(Path.cwd())
    return cmd_impact(root, a.ref, a.k, a.min_score)


if __name__ == "__main__":
    raise SystemExit(main())
