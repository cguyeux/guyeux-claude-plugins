#!/usr/bin/env python3
"""DÉPRÉCIÉ (2026-08-20) : remplacé par split_pistes_files.py (architecture index +
détail, un fichier pistes/Px.md par piste majeure, ouverte ou close -- ce script-ci
n'archive que les closes vers pistes_archive.md, ce qui ne résout pas le coût des
pistes majeures OUVERTES volumineuses, cf. P16/P18 du projet annotation_mtbc). Gardé
pour compatibilité/rollback, ne plus l'invoquer sur un nouveau projet -- appeler
split_pistes_files.py directement, qui absorbe aussi tout pistes_archive.md existant.

Archive les pistes MAJEURES (## Px.) closes d'un pistes.md vers pistes_archive.md.

Conservateur par construction : n'agit qu'au niveau ## (pistes majeures), jamais sur les
sous-pistes -- la prose des sous-pistes est trop irrégulière (indentation manuelle, brackets
cités entre backticks, etc.) pour un découpage automatique fiable. Fusionner ou redécouper des
sous-pistes reste un geste manuel (skill /pistes, section "Restructuration").

Usage :
    python3 archive_closed_pistes.py <chemin/vers/pistes.md> [--apply]

Sans --apply : dry-run, affiche ce qui serait fait sans rien écrire.
Avec --apply : écrit pistes.md (compacté) et pistes_archive.md (ou l'étend s'il existe déjà),
et fait une copie de sauvegarde <pistes.md>.bak_<AAAAMMJJ> à côté avant toute écriture.

Sûreté : après écriture, revérifie que l'union des identifiants Px dans le nouveau pistes.md
et pistes_archive.md correspond exactement à l'ensemble d'origine (pas de perte, pas de doublon),
et que chaque bloc archivé est byte-identique à sa version d'origine. Échoue bruyamment sinon.
"""
import argparse
import re
import shutil
import sys
from pathlib import Path

HEADER_RE = re.compile(r"^## (P\d+)\.", re.M)
CLOSED_TOKENS = ("réalisé", "realise", "abandonné", "abandonne", "clos")
OPEN_TOKENS = ("en cours", "à faire", "a faire")


ARCHIVE_MARKER = "-> archivé, détail :"


def classify(header_line: str) -> str:
    # Idempotence : une ligne déjà compactée par un passage précédent ne doit jamais être
    # re-classée "closed" (son crochet d'état est toujours là) ni ré-archivée en double.
    if ARCHIVE_MARKER in header_line:
        return "already-archived"
    # Ignorer les crochets cités entre backticks (ex. "portait `[à faire]`" en référence à un
    # ancien tag) : ce ne sont pas l'annotation d'état réelle de CETTE piste.
    scrubbed = re.sub(r"`[^`]*`", "", header_line)
    # rfind (pas find) : le titre peut porter un tag de catégorie entre crochets AVANT
    # l'annotation d'état ([VALORISATION], [OUTILLAGE], [PRODUIT]...) -- l'état réel est
    # toujours le DERNIER crochet ouvert sur la ligne d'en-tête.
    i = scrubbed.rfind("[")
    if i == -1:
        return "unknown"
    snippet = scrubbed[i + 1 : i + 40].lstrip("*").strip().lower()
    for tok in CLOSED_TOKENS:
        if snippet.startswith(tok):
            return "closed"
    for tok in OPEN_TOKENS:
        if snippet.startswith(tok):
            return "open"
    return "unknown"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pistes_md", type=Path)
    ap.add_argument("--apply", action="store_true", help="écrit les fichiers (sinon dry-run)")
    ap.add_argument("--date-tag", default=None, help="AAAAMMJJ pour le nom du backup (par défaut : lu depuis l'horloge système -- passer explicitement en contexte scripté)")
    args = ap.parse_args()

    src = args.pistes_md
    archive = src.with_name("pistes_archive.md")

    text = src.read_text(encoding="utf-8")
    matches = list(HEADER_RE.finditer(text))
    if not matches:
        print("Aucun en-tête '## Px.' trouvé -- rien à faire.")
        return

    starts = [m.start() for m in matches]
    ends = starts[1:] + [len(text)]
    blocks = [(m.group(1), text[s:e]) for m, s, e in zip(matches, starts, ends)]
    preamble = text[: starts[0]]

    closed, kept = [], []
    for pid, block in blocks:
        header_line = block.splitlines()[0]
        state = classify(header_line)
        (closed if state == "closed" else kept).append((pid, block, state))

    already = [x for x in kept if x[2] == "already-archived"]
    active = [x for x in kept if x[2] != "already-archived"]
    print(f"{len(blocks)} pistes majeures trouvées : {len(closed)} closes (à archiver), "
          f"{len(active)} actives (gardées), {len(already)} déjà archivées (inchangées).")
    for pid, block, state in active:
        title = block.splitlines()[0][:90]
        print(f"  garde ({state}) {pid}: {title}")

    if not args.apply:
        print("\n(dry-run -- relancer avec --apply pour écrire)")
        return

    if not args.date_tag:
        sys.exit("--date-tag AAAAMMJJ requis avec --apply (pas d'horloge système fiable en contexte scripté).")

    backup = src.with_name(f"{src.name}.bak_{args.date_tag}")
    shutil.copy2(src, backup)
    print(f"Backup : {backup}")

    out_parts = [preamble]
    for pid, block in blocks:
        header_line = block.splitlines()[0]
        state = classify(header_line)
        if state == "closed":
            out_parts.append(header_line + "  -> archivé, détail : pistes_archive.md (`rg \"^## " + pid + r"\." + "\" pistes_archive.md`)\n\n")
        else:
            out_parts.append(block)
    new_text = "".join(out_parts)
    new_text = re.sub(r"\n{3,}", "\n\n", new_text)

    archive_prefix = ""
    if not archive.exists():
        archive_prefix = (
            "# Pistes archivées\n\n"
            "Détail complet des pistes majeures closes (`[réalisé]`/`[abandonné]`/`[clos...]`), "
            "déplacées hors de `pistes.md` pour alléger la lecture obligatoire de l'arbre actif "
            "à chaque `/pistes`. Contenu inchangé, jamais réécrit.\n"
            "Recherche : `rg \"^## P7\\.\" pistes_archive.md` (remplacer par le numéro voulu) "
            "ou `rg -i \"<mot-clé>\" pistes_archive.md`.\n\n---\n\n"
        )
    archive_addition = "".join(block + "\n" for _pid, block, _state in closed) if closed else ""

    src.write_text(new_text, encoding="utf-8")
    if archive_addition:
        with archive.open("a", encoding="utf-8") as f:
            if archive_prefix:
                f.write(archive_prefix)
            f.write(archive_addition)

    # Vérification post-écriture
    verify_text = src.read_text(encoding="utf-8")
    verify_arch = archive.read_text(encoding="utf-8") if archive.exists() else ""
    new_ids = set(HEADER_RE.findall(verify_text))
    orig_ids = set(pid for pid, _ in blocks)
    if new_ids != orig_ids:
        sys.exit(f"ÉCHEC VÉRIFICATION : ids attendus {orig_ids} != ids trouvés {new_ids}. Restaurer depuis {backup}.")
    for pid, block, _state in closed:
        if block.rstrip() not in verify_arch:
            sys.exit(f"ÉCHEC VÉRIFICATION : bloc {pid} absent ou altéré dans l'archive. Restaurer depuis {backup}.")
    print(f"OK -- {len(closed)} pistes archivées, {len(kept)} gardées actives. Vérification passée.")


if __name__ == "__main__":
    main()
