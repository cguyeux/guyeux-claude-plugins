#!/usr/bin/env python3
"""Restructure pistes.md en index + un fichier de détail par piste MAJEURE.

Analogue au fonctionnement des skills Claude Code (description toujours chargée,
corps lu à la demande) : `pistes.md` ne garde plus que l'index (en-tête `## Px.`,
ligne `origine/maj/MIU`, et une ligne de justification éventuelle) + un pointeur
`-> détail : pistes/Px.md`. Le CORPS COMPLET de chaque piste majeure (tout, y
compris ses sous-pistes) part verbatim dans `pistes/Px.md`, un fichier par piste
majeure -- lu seulement quand cette piste précise est travaillée.

Remplace, à terme, `archive_closed_pistes.py` : avec ce mécanisme, TOUTE piste
(ouverte ou close) a son fichier de détail, donc plus besoin d'un geste
d'archivage séparé au moment de la clôture. `pistes_archive.md` (s'il existe)
est traité comme une SOURCE supplémentaire de corps de pistes (les pistes qui
y ont déjà été déplacées par l'ancien mécanisme) et n'est plus jamais réécrit
par ce script -- son contenu est simplement COPIÉ vers `pistes/Px.md`, jamais
modifié ni supprimé.

Usage :
    python3 split_pistes_files.py <chemin/vers/pistes.md> [--apply] [--date-tag AAAAMMJJ]

Sans --apply : dry-run, affiche ce qui serait fait sans rien écrire.
Avec --apply : écrit pistes.md (compacté), pistes/Px.md pour chaque piste
majeure, une sauvegarde <pistes.md>.bak_<date> avant toute écriture, et une
note figée en tête de pistes_archive.md (jamais son contenu, juste un avis).

Sûreté : après écriture, revérifie que chaque pistes/Px.md est byte-identique
au corps d'origine (pistes.md ou pistes_archive.md, selon la source), que
l'union des IDs Px trouvés dans le nouvel index correspond exactement à
l'ensemble d'origine, et que chaque ligne d'index est un préfixe exact du
fichier de détail correspondant. Échoue bruyamment sinon.

Idempotent : si pistes.md est déjà au format index (toute piste majeure porte
déjà un pointeur `-> détail : pistes/Px.md`), le script ne fait rien.
"""
import argparse
import re
import shutil
import sys
from pathlib import Path

# Une piste MAJEURE est `## <Lettre><chiffres éventuels>.` suivi d'un NON-chiffre :
# `## P61.1 ...` est une sous-piste écrite en titre de niveau 2 (cas réel rencontré
# dans predictops) et doit rester DANS le corps de P61. Sans le lookahead négatif,
# les deux en-têtes partagent l'id capturé "P61", le corps de P61.1 écrase
# pistes/P61.md et la vérification post-écriture échoue (constaté le 2026-08-31).
# Le rail article numérote en `P<chiffre>`, mais des chantiers hors-rail existent
# aussi en majeures à lettre seule (`## N.`, `## O.`, `## Q.`...) : les exclure du
# motif fait absorber silencieusement leur corps ENTIER dans le dernier bloc `P\d+`
# reconnu avant eux (`split_blocks` ferme un bloc à la prochaine occurrence
# reconnue, pas à la prochaine ligne `## `), constaté le 2026-09-16 sur
# `environnement/pistes.md` : six pistes lettrées (N,O,Q,R,S,T) et deux sections
# sans identifiant court (« Hors plan de refonte — ... ») se sont retrouvées
# fusionnées dans `pistes/P8.md`, disparues de l'index sans message d'erreur.
#
# Second séparateur légitime, le TIRET CADRATIN (piste V, 2026-09-21) : `## P1 —
# titre [état]` au lieu du point canonique `## P1. titre [état]`. Convention
# minoritaire mais RÉELLE et stable sur ce dépôt -- mesurée sur trois projets
# vivants (`admin/gis`, `mtbc/en_cours/Bovis_emergence`, `pompiers/optimops`),
# jamais un simple tiret bas `-` (qui, lui, sert de puce de sous-piste ou
# d'ordinal dans la numérotation `P16.2a-sexies-bis.4`). L'ID capturé doit être
# immédiatement suivi d'espace(s) PUIS du tiret cadratin -- jamais d'un tiret
# cadratin ailleurs dans le titre, qui ne rentre pas dans cette position -- donc
# aucune ambiguïté avec un titre canonique qui contiendrait par ailleurs un tiret
# cadratin en prose (ex. « Hors plan de refonte — ... », qui n'a pas d'ID court
# et reste hors de ce motif comme avant). Pas de sous-piste écrite en titre
# `## P61.1 — ...` observée sous cette convention à ce jour ; si un tel cas
# apparaît, il collisionnera comme documenté ci-dessus pour le point et devra
# recevoir le même lookahead négatif sur cette branche.
HEADER_RE = re.compile(r"^## ([A-Z]\d*)(?:\.(?!\d)|\s+—)", re.M)
# Titres majeurs sans identifiant court du type `## <ID>.` (ex. « Hors plan de
# refonte — ... ») : le garde-fou ci-dessous (voir `_verifier_aucun_titre_orphelin`)
# les détecte et échoue bruyamment plutôt que de les laisser fusionner dans le
# bloc précédent -- la CONVENTION reste `## <ID>. <titre>`, ce script ne les
# scinde jamais lui-même, il refuse seulement de les perdre en silence.
ANY_TOPLEVEL_HEADER_RE = re.compile(r"^## .+$", re.M)
DETAIL_MARKER = "-> détail : pistes/"
ARCHIVE_MARKER = "-> archivé, détail :"


def dernier_crochet(ligne: str):
    """(préfixe, état) à partir du DERNIER groupe `[...]` de premier niveau de
    `ligne`, en respectant l'imbrication -- même logique que recadrage_signals.py
    (une simple recherche du dernier `[` se fait piéger par un crochet cité en
    imbrication, ex. `[**CLOS** ... portait `[à faire]` ...]`)."""
    spans = []
    profondeur = 0
    debut = None
    for i, ch in enumerate(ligne):
        if ch == "[":
            if profondeur == 0:
                debut = i
            profondeur += 1
        elif ch == "]":
            if profondeur > 0:
                profondeur -= 1
                if profondeur == 0 and debut is not None:
                    spans.append((debut, i))
    if not spans:
        return None
    s, e = spans[-1]
    return ligne[:s], ligne[s + 1 : e]


# Cas légitime documenté (predictops, 2026-08-31) : une sous-piste numérotée
# écrite en titre de niveau 2 plutôt qu'en puce, ex. `## P61.1 ...`. Elle est
# volontairement exclue de HEADER_RE (lookahead négatif) et doit rester DANS le
# corps de sa majeure -- ce n'est PAS un titre orphelin.
SOUS_PISTE_TITRE_RE = re.compile(r"^## [A-Z]\d+\.\d", re.M)


def _verifier_aucun_titre_orphelin(text: str) -> None:
    """Échoue bruyamment si un titre `## ...` du texte n'est ni une piste
    MAJEURE reconnue par HEADER_RE, ni une sous-piste numérotée légitime
    (`SOUS_PISTE_TITRE_RE`). Sans ce garde-fou, un tel titre est absorbé en
    silence dans le corps de la piste précédente par `split_blocks` (le corps
    d'un bloc va jusqu'au PROCHAIN match reconnu, pas jusqu'à la prochaine
    ligne `## `) -- constaté le 2026-09-16 : six pistes lettrées et deux
    sections sans identifiant court, fusionnées dans `pistes/P8.md`, disparues
    de l'index sans aucun message d'erreur."""
    reconnus = {m.start() for m in HEADER_RE.finditer(text)}
    any_matches = list(ANY_TOPLEVEL_HEADER_RE.finditer(text))
    for i, m in enumerate(any_matches):
        if m.start() in reconnus or SOUS_PISTE_TITRE_RE.match(text, m.start()):
            continue
        # Déjà au format index (titre sans ID court mais MIGRÉ, ex. les sections
        # « Hors plan de refonte — ... » : pointeur -> détail/-> archivé juste
        # après, aucun corps réel à ce niveau) : rien à absorber, pas dangereux.
        segment_end = any_matches[i + 1].start() if i + 1 < len(any_matches) else len(text)
        segment = text[m.start():segment_end]
        if DETAIL_MARKER in segment or ARCHIVE_MARKER in segment:
            continue
        ligne = text.count("\n", 0, m.start()) + 1
        sys.exit(
            f"ÉCHEC : titre de niveau 2 non reconnu à la ligne {ligne} : {m.group(0)!r} "
            "-- ni piste majeure ('## <ID>. titre', ID = lettre + chiffres éventuels), "
            "ni sous-piste numérotée en titre ('## P61.1 ...'), ni section déjà migrée "
            "sans ID (pointeur -> détail/-> archivé absent de son corps). Laissé tel "
            "quel, il serait absorbé en silence dans le corps de la piste précédente. "
            "Renommer ce titre selon la convention, ou étendre HEADER_RE si c'est une "
            "nouvelle forme d'identifiant légitime -- rien n'a été écrit."
        )


def split_blocks(text: str):
    """[(pid, block)] où block va de '## Px.' au prochain '## Py.' ou EOF."""
    matches = list(HEADER_RE.finditer(text))
    starts = [m.start() for m in matches]
    ends = starts[1:] + [len(text)]
    preamble = text[: starts[0]] if starts else text
    blocks = [(m.group(1), text[s:e]) for m, s, e in zip(matches, starts, ends)]
    return preamble, blocks


SOUS_PISTE_RE = re.compile(r"^\s*-\s+P\d+\.")


def index_prefix(block: str) -> str:
    """En-tête + ligne `origine/maj/MIU` SEULEMENT, jamais une 3e ligne
    arbitraire (une phrase de prose tronquée ou le début d'une sous-piste
    collerait mal au pointeur -> détail ajouté juste après). S'arrête au
    premier signe de corps réel : ligne vide, sous-piste, ou fin de bloc.
    recadrage_signals.py n'a plus besoin de cette fenêtre pour MIU/sous_pistes
    -- il rouvre pistes/Px.md quand le format index est détecté (cf. skill)."""
    lines = block.splitlines(keepends=True)
    kept = lines[:1]
    if len(lines) > 1:
        second = lines[1]
        if second.strip() and not SOUS_PISTE_RE.match(second):
            kept.append(second)
    return "".join(kept)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pistes_md", type=Path)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--date-tag", default=None)
    args = ap.parse_args()

    src = args.pistes_md
    archive = src.with_name("pistes_archive.md")
    detail_dir = src.with_name("pistes")

    text = src.read_text(encoding="utf-8")
    _verifier_aucun_titre_orphelin(text)
    preamble, blocks = split_blocks(text)
    if not blocks:
        print("Aucun en-tête '## Px.' trouvé -- rien à faire.")
        return

    # Garde anti-collision AVANT toute écriture : deux blocs de même id se
    # seraient écrasés silencieusement dans pistes/Px.md (le second gagnait),
    # avec échec de vérification seulement APRÈS mutation de pistes.md.
    seen, dups = set(), set()
    for pid, _block in blocks:
        if pid in seen:
            dups.add(pid)
        seen.add(pid)
    if dups:
        sys.exit(f"ÉCHEC : identifiants de piste dupliqués dans les en-têtes '## Px.' : "
                 f"{sorted(dups)} -- rien n'a été écrit, corriger pistes.md d'abord.")

    # Idempotence : déjà au format index si CHAQUE bloc porte le marqueur détail.
    if all(DETAIL_MARKER in block for _pid, block in blocks):
        print("pistes.md est déjà au format index (chaque piste pointe vers pistes/Px.md) -- rien à faire.")
        return

    archive_text = archive.read_text(encoding="utf-8") if archive.exists() else ""
    archive_blocks = split_blocks(archive_text)[1] if archive_text else []
    archive_by_id = {pid: block for pid, block in archive_blocks}

    # Détecte les doublons entre pistes.md (déjà-archivées incluses) et pistes_archive.md :
    # même pid des deux côtés = normal (c'est justement le pointeur -> corps).
    #
    # BUG CORRIGÉ (P29.8, 2026-08-29) : l'idempotence ci-dessus est TOUT-OU-RIEN -- si un
    # SEUL bloc de pistes.md porte encore un corps inline (résultat d'une mutation manuelle
    # hors script, ex. /pistes qui rouvre une sous-piste directement dans l'index), la
    # branche ci-dessous s'exécutait pour TOUS les blocs, y compris ceux DÉJÀ migrés (qui ne
    # portent que l'en-tête + le pointeur `-> détail :`, PAS le corps réel). Un bloc déjà
    # migré n'a ni ARCHIVE_MARKER ni de corps réel : il tombait dans la branche "inline" avec
    # pour "corps" son propre résumé de 2-3 lignes, écrasant silencieusement le vrai
    # `pistes/Px.md` (des centaines de lignes parfois) par ce stub. Un bloc qui porte déjà
    # DETAIL_MARKER doit être laissé intact : ni son detail_path réécrit, ni son body
    # recalculé -- seul son texte (déjà au format index) est recopié tel quel dans le
    # nouveau pistes.md.
    resolved = []  # (pid, full_body_or_None, source)
    for pid, block in blocks:
        header_line = block.splitlines()[0]
        if ARCHIVE_MARKER in header_line:
            if pid not in archive_by_id:
                sys.exit(f"ÉCHEC : {pid} pointe vers pistes_archive.md mais son corps y est introuvable.")
            resolved.append((pid, archive_by_id[pid], "archive"))
        elif DETAIL_MARKER in block:
            resolved.append((pid, block, "skip"))
        else:
            resolved.append((pid, block, "inline"))

    print(f"{len(resolved)} pistes majeures : "
          f"{sum(1 for *_, s in resolved if s == 'archive')} depuis pistes_archive.md, "
          f"{sum(1 for *_, s in resolved if s == 'inline')} inline dans pistes.md, "
          f"{sum(1 for *_, s in resolved if s == 'skip')} déjà migrées (laissées intactes).")

    if not args.apply:
        for pid, body, source in resolved[:5]:
            print(f"  {pid} ({source}) -> pistes/{pid}.md ({len(body.splitlines())} lignes)")
        if len(resolved) > 5:
            print(f"  ... et {len(resolved) - 5} de plus.")
        print("\n(dry-run -- relancer avec --apply pour écrire)")
        return

    if not args.date_tag:
        sys.exit("--date-tag AAAAMMJJ requis avec --apply.")

    backup = src.with_name(f"{src.name}.bak_split_{args.date_tag}")
    shutil.copy2(src, backup)
    print(f"Backup pistes.md : {backup}")

    detail_dir.mkdir(exist_ok=True)

    out_parts = [preamble]
    for pid, body, source in resolved:
        detail_path = detail_dir / f"{pid}.md"
        if source == "skip":
            # Déjà migré : ne pas toucher pistes/Px.md (son corps réel n'est pas `body`,
            # qui n'est que le résumé d'index déjà présent dans pistes.md) ; recopier le
            # bloc d'index tel quel.
            block_text = body if body.endswith("\n") else body + "\n"
            out_parts.append(block_text.rstrip("\n") + "\n\n")
            continue
        detail_path.write_text(body, encoding="utf-8")
        prefix = index_prefix(body)
        if not prefix.endswith("\n"):
            prefix += "\n"
        out_parts.append(prefix + f"  {DETAIL_MARKER}{pid}.md\n\n")
    new_text = "".join(out_parts)
    new_text = re.sub(r"\n{3,}", "\n\n", new_text)
    src.write_text(new_text, encoding="utf-8")

    if archive.exists():
        arch_text = archive.read_text(encoding="utf-8")
        note = (
            "> **FIGÉ le " + args.date_tag + "** : ce fichier n'est plus alimenté. Son contenu a été "
            "copié verbatim vers `pistes/Px.md` (un fichier par piste majeure, cf. section "
            "\"Architecture index + détail\" du skill `/pistes`). Conservé tel quel pour la "
            "traçabilité historique, jamais modifié ni supprimé.\n\n---\n\n"
        )
        if not arch_text.startswith("> **FIGÉ"):
            archive.write_text(note + arch_text, encoding="utf-8")

    # Vérification post-écriture. En cas d'échec, pistes.md est RESTAURÉ depuis la
    # sauvegarde plutôt que laissé en état demi-migré (défaut constaté 2026-08-31 :
    # l'index mutilé restait en place et seul le message invitait à restaurer).
    def _echec_verification(msg: str):
        shutil.copy2(backup, src)
        sys.exit(f"ÉCHEC VÉRIFICATION : {msg} -- pistes.md restauré automatiquement depuis {backup} "
                 f"(les pistes/Px.md déjà écrits restent sur disque et seront réécrits au prochain --apply).")

    for pid, body, source in resolved:
        if source == "skip":
            if not (detail_dir / f"{pid}.md").exists():
                _echec_verification(f"pistes/{pid}.md marqué 'skip' mais absent du disque")
            continue
        detail_path = detail_dir / f"{pid}.md"
        on_disk = detail_path.read_text(encoding="utf-8")
        if on_disk != body:
            _echec_verification(f"pistes/{pid}.md diffère du corps d'origine ({source})")
    new_index_text = src.read_text(encoding="utf-8")
    new_ids = set(HEADER_RE.findall(new_index_text))
    orig_ids = set(pid for pid, *_ in resolved)
    if new_ids != orig_ids:
        _echec_verification(f"ids attendus {orig_ids} != ids trouvés {new_ids}")
    for pid, body, source in resolved:
        if source == "skip":
            continue
        prefix = index_prefix(body).rstrip("\n")
        if prefix not in new_index_text:
            _echec_verification(f"préfixe d'index de {pid} absent du nouveau pistes.md")

    print(f"OK -- {len(resolved)} fichiers pistes/Px.md écrits, pistes.md compacté "
          f"({len(text.splitlines())} -> {len(new_index_text.splitlines())} lignes). Vérification passée.")


if __name__ == "__main__":
    main()
