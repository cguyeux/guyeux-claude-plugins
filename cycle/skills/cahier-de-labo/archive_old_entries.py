#!/usr/bin/env python3
"""Archive les entrées anciennes d'un cahier_de_labo.md, ne garde en clair que les N dernières.

Le mode `read` du skill /cahier-de-labo n'exploite jamais que les 3-4 dernières entrées : le
reste n'a besoin d'être présent que pour une recherche ponctuelle (rg), pas pour la lecture
courante. Ce script maintient donc cahier_de_labo.md borné en déplaçant les entrées les plus
anciennes, verbatim, vers cahier_de_labo_archive.md (append -- jamais réécrit).

Usage :
    python3 archive_old_entries.py <chemin/vers/cahier_de_labo.md> [--keep N] [--apply] --date-tag AAAAMMJJ

Sans --apply : dry-run. Avec --apply : écrit, après une copie de sauvegarde
<cahier_de_labo.md>.bak_<AAAAMMJJ>, et revérifie que chaque entrée est byte-identique
à l'original (dans cahier_de_labo.md pour les gardées, dans l'archive pour les déplacées)
avant de conclure.
"""
import argparse
import re
import shutil
import sys
from pathlib import Path

HEADER_RE = re.compile(r"^## \[?\d{4}-\d{2}-\d{2}\]?.*$", re.M)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cahier_md", type=Path)
    ap.add_argument("--keep", type=int, default=4, help="nombre d'entrées les plus récentes à garder en clair (défaut 4)")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--date-tag", default=None, help="AAAAMMJJ pour le backup, requis avec --apply")
    args = ap.parse_args()

    src = args.cahier_md
    archive = src.with_name("cahier_de_labo_archive.md")

    text = src.read_text(encoding="utf-8")
    matches = list(HEADER_RE.finditer(text))
    if len(matches) <= args.keep:
        print(f"{len(matches)} entrée(s), <= --keep {args.keep} : rien à archiver.")
        return

    starts = [m.start() for m in matches]
    ends = starts[1:] + [len(text)]
    entries = [text[s:e] for s, e in zip(starts, ends)]
    preamble = text[: starts[0]]

    # Un run precedent peut avoir laisse sa propre banniere "Archive :" dans le
    # preambule (tout ce qui precede la premiere entree gardee) : la retirer
    # avant d'en ecrire une nouvelle, sous peine d'accumuler des bannieres
    # dupliquees a chaque archivage successif (bug constate, cf. reflect).
    ARCHIVE_BANNER_RE = re.compile(
        r"\*\*Archive :\*\* entrées jusqu'au \d{4}-\d{2}-\d{2} .*?\n"
        r"Ne conserver ici que les dernières entrées.*?\n\n---\n\n",
        re.S,
    )
    preamble = ARCHIVE_BANNER_RE.sub("", preamble)

    to_archive = entries[: -args.keep]
    to_keep = entries[-args.keep:]
    print(f"{len(entries)} entrées trouvées : {len(to_archive)} à archiver, {len(to_keep)} gardées en clair.")
    print(f"  plage archivée : {to_archive[0].splitlines()[0][:60]} ... {to_archive[-1].splitlines()[0][:60]}")

    if not args.apply:
        print("\n(dry-run -- relancer avec --apply pour écrire)")
        return
    if not args.date_tag:
        sys.exit("--date-tag AAAAMMJJ requis avec --apply.")

    backup = src.with_name(f"{src.name}.bak_{args.date_tag}")
    shutil.copy2(src, backup)
    print(f"Backup : {backup}")

    archive_prefix = ""
    if not archive.exists():
        archive_prefix = (
            "# Cahier de laboratoire -- ARCHIVE\n\n"
            "Entrées anciennes déplacées ici pour n'alléger que la lecture courante de "
            "`cahier_de_labo.md`. Contenu verbatim, jamais réécrit ni condensé.\n"
            "Recherche : `rg \"Pxx\" cahier_de_labo_archive.md` (numéro de piste), "
            "`rg -i \"<mot-clé>\"`, ou `rg \"^## AAAA-MM\"` pour une plage de dates.\n\n---\n\n"
        )

    with archive.open("a", encoding="utf-8") as f:
        if archive_prefix:
            f.write(archive_prefix)
        f.write("".join(to_archive))

    last_date_m = re.search(r"\d{4}-\d{2}-\d{2}", to_archive[-1].splitlines()[0])
    last_date = last_date_m.group(0) if last_date_m else "?"
    archived_range = (
        f"**Archive :** entrées jusqu'au {last_date} "
        "déplacées dans `cahier_de_labo_archive.md`, verbatim, consultable via `rg`.\n"
        "Ne conserver ici que les dernières entrées ; le skill /cahier-de-labo archive au fil de l'eau.\n\n---\n\n"
    )
    src.write_text(preamble + archived_range + "".join(to_keep), encoding="utf-8")

    verify_new = src.read_text(encoding="utf-8")
    verify_arch = archive.read_text(encoding="utf-8")
    new_entries = HEADER_RE.findall(verify_new)
    arch_entries = HEADER_RE.findall(verify_arch)
    if len(new_entries) != len(to_keep) or len(arch_entries) < len(to_archive):
        sys.exit(f"ÉCHEC VÉRIFICATION : comptes incohérents. Restaurer depuis {backup}.")
    for e in to_archive:
        if e.rstrip() not in verify_arch:
            sys.exit(f"ÉCHEC VÉRIFICATION : entrée '{e.splitlines()[0][:60]}' absente de l'archive. Restaurer depuis {backup}.")
    for e in to_keep:
        if e.rstrip() not in verify_new:
            sys.exit(f"ÉCHEC VÉRIFICATION : entrée gardée '{e.splitlines()[0][:60]}' altérée. Restaurer depuis {backup}.")
    print(f"OK -- {len(to_archive)} entrées archivées, {len(to_keep)} gardées en clair. Vérification passée.")


if __name__ == "__main__":
    main()
