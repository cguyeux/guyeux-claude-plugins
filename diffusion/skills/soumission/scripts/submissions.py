#!/usr/bin/env python3
"""Registre central des soumissions d'articles : etat, suivi, regle de variation.

Donnees : $SOUMISSION_KB/submissions.tsv (defaut ~/.agents/knowledge/journals/).
Le registre est CENTRAL et non par projet : c'est la seule facon de voir qu'on
concentre trois manuscrits chez le meme editeur. Zero dependance externe.

Sous-commandes
    add       enregistre une soumission (ou une preparation)
    set       met a jour des champs, date le changement de statut
    list      affiche le registre
    show      detail d'une soumission
    variety   verdict de la regle de variation avant de viser une revue
    stale     soumissions dont le statut n'a pas bouge depuis trop longtemps
    review    point d'etat complet : ou en est chaque manuscrit, ce qui cloche
    reject    enregistre une decision negative et son enseignement
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
import textwrap
from datetime import date, datetime
from pathlib import Path

FIELDS = [
    "id", "project", "title_short", "domain", "journal_key", "journal_name",
    "publisher", "portal", "submitted_on", "manuscript_id", "status",
    "status_on", "decision", "decision_on", "editor", "preprint_server",
    "preprint_id", "github_repo", "zenodo_doi", "fr_version", "notes",
]

STATUSES = [
    "preparing", "submitted", "with-editor", "under-review", "revision",
    "accepted", "published", "rejected", "withdrawn", "transferred",
    # `abandoned` n'est pas `withdrawn` : un paquet peut etre entierement prepare
    # pour une revue puis la cible ecartee AVANT tout depot, quand la mesure du
    # scope reel arrive apres la preparation. Le 2026-08-25, deux paquets etaient
    # dans ce cas (Tuberculosis pour Rv0810c, IJAA pour bpal). Sans ce statut ils
    # restent `preparing`, donc comptes comme actifs par la regle de variation,
    # et ils bloquent l'editeur pour une vraie cible.
    "abandoned",
    # `returned-to-draft` n'est ni `preparing` ni `revision` : le dossier EXISTE chez
    # l'editeur, avec son numero de manuscrit, mais il a ete renvoye a l'auteur AVANT
    # toute evaluation, pour un manque de forme (declarations ethique / conflit
    # d'interets / copyright, sections a fusionner). Constate le 2026-09-02 sur
    # Molecular Microbiology 3557325, ou le registre disait `submitted` alors que le
    # manuscrit dormait en brouillon depuis trois jours, et ou aucun mail n'etait
    # arrive sur l'adresse gmail : seul le portail le montrait.
    "returned-to-draft",
]
# `returned-to-draft` n'est PAS actif : le dossier est revenu chez l'auteur, il
# n'occupe plus l'editeur et ne compte donc pas dans la regle de variation.
ACTIVE = {"submitted", "with-editor", "under-review", "revision"}

# Seuils de la regle de variation. Voir references/choix-revue.md pour le pourquoi.
MAX_ACTIVE_SAME_JOURNAL = 1      # au-dela : refus
MAX_ACTIVE_SAME_PUBLISHER = 2    # au-dela : alerte
# Cles de revue SYNTHETIQUES : elles ne designent aucun lieu de publication reel, mais
# un mode de diffusion (mode b/c du cycle : preprint seul, code seul). La regle de
# variation ne s'y applique pas -- concentrer trois manuscrits "sans revue" n'expose a
# aucun editeur, et un refus de criblage de preprint n'est pas le refus d'une revue.
# Sans cette exemption, un refus bioRxiv enregistre sous 'preprint-only' mettait la cle
# en cooldown 365 j et faisait repondre REFUS a toute future diffusion en preprint seul,
# tous projets confondus (faux blocage constate le 2026-09-05 sur Rv1125).
SYNTHETIC_JOURNAL_KEYS = {"preprint-only", "no-journal", "none", "n/a"}

REJECT_COOLDOWN_DAYS = 365       # ne pas retenter une revue qui a rejete depuis moins de


def kb_dir() -> Path:
    return Path(os.environ.get(
        "SOUMISSION_KB", Path.home() / ".agents" / "knowledge" / "journals"))


def db_path() -> Path:
    return kb_dir() / "submissions.tsv"


def load() -> list[dict]:
    global _LOADED_MTIME
    p = db_path()
    _LOADED_MTIME = _mtime_or_none(p)
    if not p.exists():
        return []
    with p.open(encoding="utf-8", newline="") as fh:
        return [dict(r) for r in csv.DictReader(fh, delimiter="\t")]


_LOADED_MTIME: float | None = None


def save(rows: list[dict]) -> None:
    def render(fh):
        w = csv.DictWriter(fh, fieldnames=FIELDS, delimiter="\t",
                           extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for r in sorted(rows, key=lambda x: (x.get("submitted_on") or "9999",
                                             x.get("id") or "")):
            w.writerow({f: (r.get(f) or "").replace("\t", " ").strip() for f in FIELDS})

    _atomic_write(db_path(), render, mtime_before=_LOADED_MTIME)


# --------------------------------------------------------------------------
# ecriture concurrente
# --------------------------------------------------------------------------

def _atomic_write(path: Path, render, *, mtime_before: float | None = None) -> None:
    """Ecrit sous verrou exclusif, en refusant d'ecraser une version plus recente.

    Ces fichiers sont partages entre plusieurs sessions Claude travaillant en
    parallele sur le meme depot. Sans verrou, deux sessions qui lisent puis
    reecrivent le fichier entier se marchent dessus : la derniere a ecrire gagne
    et efface silencieusement le travail de l'autre. Vecu le 2026-08-25 sur
    submissions.tsv et journals.tsv, ou plusieurs heures de mises a jour ont
    disparu d'un coup, sans aucun message.

    Le verrou serialise les ecritures ; la comparaison de mtime attrape le cas ou
    le fichier a change entre notre lecture et notre ecriture, et fait echouer
    bruyamment plutot que d'ecraser.
    """
    import fcntl
    import os
    import tempfile

    path.parent.mkdir(parents=True, exist_ok=True)
    lock = path.with_suffix(path.suffix + ".lock")
    with lock.open("w") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        if mtime_before is not None and path.exists():
            now = path.stat().st_mtime
            if now > mtime_before + 0.001:
                raise RuntimeError(
                    f"{path.name} a ete modifie par un autre processus pendant "
                    f"cette operation (lu a {mtime_before:.1f}, trouve a {now:.1f}). "
                    f"Rien n'a ete ecrit : relire et refaire la modification.")
        fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=path.name + ".")
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as fh:
                render(fh)
            os.replace(tmp, path)
        except BaseException:
            temporary = Path(tmp)
            if temporary.exists():
                temporary.replace(temporary.with_name(temporary.name + ".failed"))
            raise


def _mtime_or_none(path: Path) -> float | None:
    return path.stat().st_mtime if path.exists() else None


def days_since(iso: str) -> int | None:
    try:
        return (date.today() - datetime.strptime(iso.strip(), "%Y-%m-%d").date()).days
    except (ValueError, AttributeError):
        return None


def _jours(iso: str) -> str:
    """Rend le nombre de jours en texte, sans confondre 0 et inconnu.

    `days_since(...) or "?"` rend "?" pour une soumission du JOUR MEME, puisque 0
    est falsy : le cas le plus frequent au moment ou l'on consulte le registre est
    aussi celui que l'affichage rendait illisible.
    """
    d = days_since(iso)
    return "?" if d is None else str(d)


def make_id(project: str, journal_key: str, when: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", project.lower()).strip("-")[:24]
    jk = re.sub(r"[^a-z0-9]+", "-", journal_key.lower()).strip("-")[:16]
    return f"{slug}--{jk}--{when[:7]}"


def journals_index() -> dict[str, dict]:
    p = kb_dir() / "journals.tsv"
    if not p.exists():
        return {}
    with p.open(encoding="utf-8", newline="") as fh:
        return {r["key"]: r for r in csv.DictReader(fh, delimiter="\t") if r.get("key")}


# --------------------------------------------------------------------------

def cmd_add(args) -> int:
    rows = load()
    when = args.submitted_on or date.today().isoformat()
    jidx = journals_index()
    j = jidx.get(args.journal_key, {})
    if not j and not args.force:
        print(f"revue inconnue de la base : {args.journal_key}\n"
              f"l'ajouter d'abord (journals.py set {args.journal_key} ... --create) "
              f"ou passer --force", file=sys.stderr)
        return 1
    sid = args.id or make_id(args.project, args.journal_key, when)
    if any(r["id"] == sid for r in rows):
        print(f"identifiant deja pris : {sid}", file=sys.stderr)
        return 1
    row = {f: "" for f in FIELDS}
    row.update({
        "id": sid,
        "project": args.project,
        "title_short": args.title,
        "domain": args.domain or j.get("domain", ""),
        "journal_key": args.journal_key,
        "journal_name": args.journal_name or j.get("name", ""),
        "publisher": args.publisher or j.get("publisher", ""),
        "portal": args.portal or j.get("portal", ""),
        "submitted_on": when,
        "manuscript_id": args.manuscript_id or "",
        "status": args.status,
        "status_on": when,
        "preprint_server": args.preprint_server or "",
        "preprint_id": args.preprint_id or "",
        "github_repo": args.github_repo or "",
        "zenodo_doi": args.zenodo_doi or "",
        "fr_version": args.fr_version or "",
        "notes": args.notes or "",
    })
    # Le verdict se calcule sur les AUTRES dossiers : compter celui qu'on vient
    # d'ajouter ferait crier l'alerte a chaque enregistrement, et une alerte qui
    # se declenche toujours cesse d'etre lue.
    others = list(rows)
    rows.append(row)
    save(rows)
    print(f"enregistre : {sid}  [{row['status']}]  {row['journal_name']}")
    verdict, motifs = variety_verdict(others, args.journal_key, row["publisher"])
    if verdict != "OK":
        print(f"\nRappel variation : {verdict}")
        for m in motifs:
            print(f"  - {m}")
    return 0


def cmd_set(args) -> int:
    rows = load()
    idx = {r["id"]: i for i, r in enumerate(rows)}
    if args.id not in idx:
        near = [k for k in idx if args.id.lower() in k.lower()]
        print(f"identifiant inconnu : {args.id}"
              + (f"\nproche : {', '.join(near[:6])}" if near else ""), file=sys.stderr)
        return 1
    row = rows[idx[args.id]]
    for assign in args.assign:
        if "=" not in assign:
            print(f"attendu champ=valeur : {assign}", file=sys.stderr)
            return 1
        f, v = assign.split("=", 1)
        if f not in FIELDS:
            print(f"champ inconnu : {f}\nchamps : {', '.join(FIELDS)}", file=sys.stderr)
            return 1
        if f == "status" and v not in STATUSES:
            print(f"statut inconnu : {v}\nstatuts : {', '.join(STATUSES)}", file=sys.stderr)
            return 1
        if f == "status" and v != row.get("status"):
            row["status_on"] = args.on or date.today().isoformat()
        if f == "decision":
            row["decision_on"] = args.on or date.today().isoformat()
        row[f] = v.replace("\t", " ").strip()
    save(rows)
    print(f"{args.id} : " + ", ".join(args.assign)
          + (f"  (status_on={row['status_on']})" if any(a.startswith("status=")
                                                        for a in args.assign) else ""))
    return 0


def cmd_rename(args) -> int:
    """Un identifiant porte le nom de la revue visee au moment de sa creation. Quand la
    cible change, il ment : le 2026-08-25 deux lignes disaient `archives-microbi` alors
    qu'une seule y allait vraiment. C'est la meme confusion qui a failli faire deposer un
    manuscrit dans le brouillon d'un autre."""
    rows = load()
    idx = {r["id"]: i for i, r in enumerate(rows)}
    if args.old not in idx:
        near = [k for k in idx if args.old.lower() in k.lower()]
        print(f"identifiant inconnu : {args.old}"
              + (f"\nproche : {', '.join(near[:6])}" if near else ""), file=sys.stderr)
        return 1
    if args.new in idx:
        print(f"identifiant deja pris : {args.new}", file=sys.stderr)
        return 1
    rows[idx[args.old]]["id"] = args.new
    save(rows)
    print(f"{args.old} -> {args.new}")
    return 0


def cmd_list(args) -> int:
    rows = load()
    if args.open:
        rows = [r for r in rows if r.get("status") in ACTIVE]
    if args.project:
        rows = [r for r in rows if args.project.lower() in (r.get("project") or "").lower()]
    if args.publisher:
        rows = [r for r in rows if args.publisher.lower() in (r.get("publisher") or "").lower()]
    if not rows:
        print("registre vide pour ce filtre")
        return 0
    print(f"{'ID':38s} {'STATUT':13s} {'DEPUIS':7s} {'REVUE':30s} {'EDITEUR':16s} PROJET")
    print("-" * 128)
    for r in rows:
        d = days_since(r.get("status_on", ""))
        print(f"{r['id'][:38]:38s} {(r.get('status') or '')[:13]:13s} "
              f"{(str(d) + ' j') if d is not None else '?':7s} "
              f"{(r.get('journal_name') or '')[:30]:30s} "
              f"{(r.get('publisher') or '')[:16]:16s} {r.get('project')}")
    n_active = sum(1 for r in rows if r.get("status") in ACTIVE)
    print(f"\n{len(rows)} soumissions ({n_active} en cours d'evaluation)")
    return 0


def cmd_show(args) -> int:
    rows = {r["id"]: r for r in load()}
    r = rows.get(args.id)
    if not r:
        near = [k for k in rows if args.id.lower() in k.lower()]
        print(f"inconnu : {args.id}" + (f"\nproche : {', '.join(near[:6])}" if near else ""),
              file=sys.stderr)
        return 1
    width = max(len(f) for f in FIELDS)
    for f in FIELDS:
        if r.get(f):
            print(f"{f:>{width}} : " + textwrap.fill(r[f], 100,
                  subsequent_indent=" " * (width + 3)))
    d = days_since(r.get("status_on", ""))
    if r.get("status") in ACTIVE and d is not None and d > 90:
        print(f"\nSans nouvelle depuis {d} jours : relancer l'editeur ou verifier le portail. "
              f"Le statut ne se lit PAS dans le depot local, seulement dans le systeme "
              f"de gestion ou les mails.")
    return 0


def variety_verdict(rows: list[dict], journal_key: str, publisher: str,
                    editor: str = "") -> tuple[str, list[str]]:
    """Applique la regle de variation. Rend (verdict, motifs).

    Verdict : OK / ALERTE / REFUS. Un REFUS n'interdit rien mecaniquement, il
    impose d'expliquer a l'auteur pourquoi on passerait outre.
    """
    motifs = []
    if (journal_key or "").strip().lower() in SYNTHETIC_JOURNAL_KEYS:
        return "OK", [f"'{journal_key}' n'est pas une revue mais un mode de diffusion : "
                      f"la regle de variation ne s'y applique pas (ni concentration chez "
                      f"un editeur, ni cooldown apres refus)"]
    active = [r for r in rows if r.get("status") in ACTIVE]
    same_j = [r for r in active if r.get("journal_key") == journal_key]
    same_p = [r for r in active if publisher and r.get("publisher") == publisher]
    rejected = [r for r in rows
                if r.get("journal_key") == journal_key
                and (r.get("decision") or "").startswith("reject")]

    verdict = "OK"
    if len(same_j) > MAX_ACTIVE_SAME_JOURNAL:
        verdict = "REFUS"
        motifs.append(f"{len(same_j)} manuscrits deja en evaluation dans cette revue "
                      f"({', '.join(r['project'] for r in same_j)}) : le meme editeur "
                      f"associe verra arriver un troisieme dossier du meme auteur")
    elif len(same_j) == MAX_ACTIVE_SAME_JOURNAL:
        verdict = "ALERTE"
        motifs.append(f"1 manuscrit deja en evaluation ici ({same_j[0]['project']}, "
                      f"depuis {_jours(same_j[0].get('submitted_on',''))} j)")
    # La concentration chez un EDITEUR doit compter les preparations autant que les
    # evaluations : trois dossiers qui convergent vers trois revues du meme groupe
    # arrivent quand meme chez le meme groupe, et deux d'entre eux peuvent encore
    # etre a l'etat de brouillon quand on decide du troisieme.
    prep_p = [r for r in rows
              if r.get("status") == "preparing" and publisher
              and r.get("publisher") == publisher and r.get("journal_key") != journal_key]
    total_p = same_p + prep_p
    if len(total_p) >= MAX_ACTIVE_SAME_PUBLISHER:
        verdict = "REFUS" if verdict == "REFUS" else "ALERTE"
        detail = ", ".join(f"{r['project']} ({r.get('journal_name') or '?'}"
                           + (", en preparation)" if r.get("status") == "preparing"
                              else ")")
                           for r in total_p)
        motifs.append(f"{len(total_p)} manuscrits deja diriges vers {publisher} : "
                      f"{detail}. Trois revues distinctes du meme groupe restent le "
                      f"meme groupe")
    for r in rejected:
        d = days_since(r.get("decision_on", "") or r.get("status_on", ""))
        if d is not None and d < REJECT_COOLDOWN_DAYS:
            verdict = "REFUS"
            motifs.append(f"cette revue a rejete {r['project']} il y a {d} jours "
                          f"({r.get('decision')}) : resoumettre un dossier de meme nature "
                          f"expose au meme desk-reject")
    # Deux manuscrits EN PREPARATION vers la meme revue sont le cas le plus facile
    # a ne pas voir : ils ne sont dans aucune file d'evaluation, donc invisibles a
    # un compteur qui ne regarde que l'actif. Vecu le 2026-08-25 : un brouillon
    # Snapp portant un manuscrit allait en recevoir un second par-dessus.
    prep = [r for r in rows
            if r.get("status") == "preparing" and r.get("journal_key") == journal_key]
    if prep:
        verdict = "REFUS" if verdict == "REFUS" else "ALERTE"
        motifs.append(
            f"{len(prep)} manuscrit(s) DEJA EN PREPARATION vers cette revue "
            f"({', '.join(r['project'] for r in prep)}) : verifier a quel dossier "
            f"appartient le brouillon ouvert sur le portail avant d'y televerser "
            f"quoi que ce soit")

    # L'editeur associe est le niveau de concentration le plus fin, et le plus
    # sensible : c'est une personne qui voit arriver les dossiers, pas une marque.
    if editor:
        same_e = [r for r in active
                  if (r.get("editor") or "").lower() == editor.lower()]
        if same_e:
            verdict = "REFUS"
            motifs.append(f"l'editeur associe {editor} traite deja "
                          f"{', '.join(r['project'] for r in same_e)} : c'est la "
                          f"concentration qui se remarque le plus")
    known_editors = {(r.get("editor") or "").strip() for r in active if r.get("editor")}
    if not editor and known_editors:
        motifs.append(f"editeurs associes deja mobilises sur les dossiers en cours : "
                      f"{', '.join(sorted(known_editors))} — verifier a qui la revue "
                      f"visee confie ce domaine avant de conclure")

    for r in rejected:
        if r.get("notes"):
            motifs.append(f"enseignement du rejet {r['project']} : {r['notes'][:160]}")
    return verdict, motifs


def cmd_variety(args) -> int:
    rows = load()
    jidx = journals_index()
    publisher = args.publisher or jidx.get(args.journal, {}).get("publisher", "")
    verdict, motifs = variety_verdict(rows, args.journal, publisher, args.editor or "")
    print(f"Cible : {args.journal} ({publisher or 'editeur inconnu'})")
    print(f"Verdict de variation : {verdict}")
    if motifs:
        for m in motifs:
            print(f"  - {m}")
    else:
        print("  - aucune concentration detectee")
    active = [r for r in rows if r.get("status") in ACTIVE]
    if active:
        print(f"\nEn cours d'evaluation ({len(active)}) :")
        for r in active:
            print(f"  {r.get('journal_name','?'):34s} {r.get('publisher',''):16s} "
                  f"{r.get('project')}  (depuis {_jours(r.get('submitted_on',''))} j)")
    return 0 if verdict != "REFUS" else 2


def cmd_stale(args) -> int:
    rows = [r for r in load() if r.get("status") in ACTIVE]
    out = []
    for r in rows:
        d = days_since(r.get("status_on", ""))
        if d is not None and d >= args.days:
            out.append((d, r))
    if not out:
        print(f"aucune soumission sans nouvelle depuis {args.days} jours")
        return 0
    out.sort(key=lambda x: -x[0])
    print(f"{len(out)} soumissions a verifier (statut fige depuis >= {args.days} j) :\n")
    for d, r in out:
        print(f"  {d:4d} j  {r['id']}")
        print(f"          {r.get('journal_name')} ({r.get('portal')}) "
              f"manuscrit {r.get('manuscript_id') or '?'}")
    print("\nVerifier chaque statut dans le systeme de gestion (portail ou mails), "
          "jamais dans le depot local.")
    return 0


# ---------------------------------------------------------------------------
# Point d'etat du portefeuille. Les seuils ci-dessous ne mesurent pas la vitesse
# d'un editeur, mais le temps pendant lequel PERSONNE n'a regarde. Le cas qui les
# justifie : un paquet reste `preparing` apres une session de soumission, l'auteur
# croit l'article depose, et personne ne s'en apercoit avant des semaines.
REVIEW_PREPARING_DAYS = 7        # prepare, jamais depose
REVIEW_PREPARING_URGENT = 21
REVIEW_REVISION_DAYS = 30        # revision demandee : l'horloge de l'editeur tourne
REVIEW_RETURNED_DAYS = 2         # renvoye en brouillon : rien ne se passe tant qu'on n'agit pas
REVIEW_DORMANT_DAYS = 14         # rejet ou abandon sans cible suivante
REVIEW_ACCEPTED_DAYS = 30        # accepte, jamais passe a `published`
_TERMINAL_NEGATIF = {"rejected", "abandoned", "withdrawn", "transferred"}
_VIVANT = ACTIVE | {"preparing", "accepted", "returned-to-draft"}


def _last_move(r: dict) -> str:
    """Date du dernier mouvement connu : changement de statut, sinon depot."""
    return (r.get("status_on") or r.get("submitted_on") or "").strip()


def _age(r: dict) -> int | None:
    return days_since(_last_move(r))


def _fmt_age(r: dict) -> str:
    d = _age(r)
    return "?" if d is None else f"{d} j"


def _finding(sev: str, code: str, rid: str, constat: str, action: str) -> dict:
    return {"sev": sev, "code": code, "id": rid, "constat": constat, "action": action}


def review_findings(rows: list[dict], stale_days: int) -> list[dict]:
    """Anomalies deductibles du seul registre, sans rien consulter d'externe."""
    out: list[dict] = []

    for r in rows:
        rid, st, age = r["id"], (r.get("status") or "").strip(), _age(r)
        revue = r.get("journal_name") or r.get("journal_key") or "?"

        if st not in STATUSES:
            out.append(_finding(
                "bloquant", "statut-hors-vocabulaire", rid,
                f"statut '{st or 'vide'}' inconnu du registre",
                f"corriger vers un statut valide ({', '.join(STATUSES[:6])}...) : "
                f"submissions.py set {rid} status=<valide> ; tant qu'il est faux, "
                f"la ligne echappe aux compteurs d'actives et a la regle de variation"))
            continue

        if st == "preparing" and age is not None and age >= REVIEW_PREPARING_DAYS:
            out.append(_finding(
                "bloquant" if age >= REVIEW_PREPARING_URGENT else "a-traiter",
                "prepare-jamais-depose", rid,
                f"prepare pour {revue} il y a {age} j, jamais depose",
                "finir le depot, ou acter l'abandon de la cible : "
                f"submissions.py set {rid} status=abandoned"))

        if st in ACTIVE and not (r.get("manuscript_id") or "").strip():
            out.append(_finding(
                "a-traiter", "sans-identifiant", rid,
                f"donne pour {st} chez {revue} sans identifiant de manuscrit",
                "verifier sur le portail que le depot existe vraiment, puis "
                f"submissions.py set {rid} manuscript_id=<id>"))

        if st == "returned-to-draft" and age is not None and age >= REVIEW_RETURNED_DAYS:
            out.append(_finding(
                "bloquant", "renvoye-en-brouillon", rid,
                f"renvoye en brouillon par {revue} il y a {age} j",
                "le dossier n'est PAS en evaluation : corriger ce que le bureau "
                "editorial demande, puis resoumettre depuis le tableau de bord. "
                "Tant que ce n'est pas fait, le manuscrit n'existe pour personne")) 

        if st == "revision" and age is not None and age >= REVIEW_REVISION_DAYS:
            out.append(_finding(
                "bloquant", "revision-qui-traine", rid,
                f"revision demandee par {revue} il y a {age} j",
                "verifier la date limite de renvoi sur le portail (souvent 60 a 90 j) "
                "et reprendre la revision, ou demander un delai"))

        if st == "accepted":
            # L'acceptation est le seul moment ou l'affiliation deposee chez
            # l'editeur peut encore etre corrigee sans rien couter : les epreuves
            # passent sous les yeux de l'auteur, et la fiche auteur du portail
            # alimente l'indexation. Arbitrage CG du 2026-09-09 : on ne touche PAS
            # aux bases auteurs d'un manuscrit en cours d'evaluation, on le fait a
            # l'acceptation. D'ou ce rappel des l'entree en `accepted`, sans delai.
            retard = (f" (accepte il y a {age} j, toujours pas 'published')"
                      if age is not None and age >= REVIEW_ACCEPTED_DAYS else "")
            out.append(_finding(
                "a-verifier", "acceptation-a-solder", rid,
                f"accepte chez {revue}{retard}",
                "quatre gestes, dans cet ordre : (1) sur les EPREUVES, verifier la "
                "signature scientifique et les remerciements (mesocentre, financeurs) "
                "-- c'est la derniere fenetre ou ils se corrigent ; (2) mettre a jour "
                "l'affiliation dans la BASE AUTEURS du portail, ce que la direction de "
                "l'institut demande explicitement et qui commande l'indexation ; "
                "(3) DES L'ACCEPTATION, sans attendre la parution : ajouter la "
                "publication au CV (skill /cv, avec les seuls champs deja connus), la "
                "recompiler, et preparer le ticket Publiweb avec la VERSION FINALE "
                "AUTEUR (jamais la version editeur) -- soumission du ticket bornee par "
                "le perimetre d'autorisation ci-dessus ; (4) a la parution effective "
                "(DOI, pagination), completer l'entree, recompiler, passer le statut a "
                "published et verifier l'ingestion (cv_publiweb_sync.py)"))

        if st in ACTIVE and age is not None and age >= stale_days:
            out.append(_finding(
                "a-verifier", "statut-fige", rid,
                f"{st} chez {revue} sans changement depuis {age} j",
                "lire l'etat dans le systeme de gestion ou les mails de l'editeur, "
                "jamais dans le depot local ; au-dela de trois mois, relancer"))

    # Projet dormant : la derniere ligne du projet est une decision negative et
    # rien d'autre n'est vivant. C'est un manuscrit fini que plus rien ne porte.
    by_project: dict[str, list[dict]] = {}
    for r in rows:
        by_project.setdefault((r.get("project") or "?"), []).append(r)
    for proj, rs in sorted(by_project.items()):
        if any((x.get("status") or "") in _VIVANT for x in rs):
            continue
        derniere = sorted(rs, key=lambda x: (_last_move(x), x["id"]))[-1]
        st = (derniere.get("status") or "")
        age = _age(derniere)
        if st in _TERMINAL_NEGATIF and age is not None and age >= REVIEW_DORMANT_DAYS:
            out.append(_finding(
                "a-traiter", "projet-dormant", derniere["id"],
                f"projet '{proj}' : {st} il y a {age} j, aucune cible suivante",
                "choisir la revue suivante (submissions.py variety <cle>) et "
                "resoumettre, ou acter que le manuscrit s'arrete la"))

    # Concentration editeur : la regle de variation, mais lue sur l'existant.
    actives = [r for r in rows if (r.get("status") or "") in ACTIVE]
    for champ, seuil, code in (("journal_key", MAX_ACTIVE_SAME_JOURNAL, "concentration-revue"),
                               ("publisher", MAX_ACTIVE_SAME_PUBLISHER, "concentration-editeur")):
        groupes: dict[str, list[str]] = {}
        for r in actives:
            v = (r.get(champ) or "").strip().lower()
            if v and v not in SYNTHETIC_JOURNAL_KEYS:
                groupes.setdefault(v, []).append(r["id"])
        for v, ids in sorted(groupes.items()):
            if len(ids) > seuil:
                out.append(_finding(
                    "a-verifier", code, ", ".join(ids),
                    f"{len(ids)} soumissions actives sur {champ}={v} (seuil {seuil})",
                    "ne pas viser cette cible pour le prochain manuscrit avant "
                    "qu'une des lignes soit tranchee"))

    ordre = {"bloquant": 0, "a-traiter": 1, "a-verifier": 2}
    out.sort(key=lambda f: (ordre.get(f["sev"], 9), f["code"], f["id"]))
    return out


def cmd_review(args) -> int:
    rows = load()
    if args.project:
        rows = [r for r in rows
                if args.project.lower() in (r.get("project") or "").lower()]
    if not rows:
        print("registre vide pour ce filtre")
        return 0

    par_statut: dict[str, list[dict]] = {}
    for r in rows:
        par_statut.setdefault((r.get("status") or "vide"), []).append(r)

    print(f"POINT D'ETAT DES SOUMISSIONS -- {date.today().isoformat()}")
    print(f"{len(rows)} lignes au registre "
          f"({sum(1 for r in rows if (r.get('status') or '') in ACTIVE)} en evaluation, "
          f"{len(par_statut.get('preparing', []))} en preparation)\n")

    for st in STATUSES + sorted(k for k in par_statut if k not in STATUSES):
        lot = par_statut.get(st)
        if not lot:
            continue
        print(f"{st.upper()} ({len(lot)})")
        for r in sorted(lot, key=lambda x: _last_move(x), reverse=True):
            print(f"  {_fmt_age(r):>6}  {r['id'][:44]:44s} "
                  f"{(r.get('journal_name') or r.get('journal_key') or '')[:28]:28s} "
                  f"{(r.get('manuscript_id') or '-')[:22]}")
        print()

    findings = review_findings(rows, args.days)
    if not findings:
        print("A REPRENDRE : rien. Aucun ecart deductible du registre.")
    else:
        bloc = sum(1 for f in findings if f["sev"] == "bloquant")
        print(f"A REPRENDRE ({len(findings)}, dont {bloc} bloquant(s))\n")
        for f in findings:
            print(f"  [{f['sev']}] {f['code']} -- {f['id']}")
            print(f"      constat : {f['constat']}")
            print(f"      action  : {textwrap.fill(f['action'], 92, subsequent_indent=' ' * 16)}")
            print()

    externes = [f for f in findings
                if f["code"] in ("statut-fige", "sans-identifiant", "renvoye-en-brouillon",
                                 "acceptation-a-solder", "revision-qui-traine")]
    if externes:
        print("VERIFICATION EXTERNE DUE (le registre ne peut pas la faire seul)")
        idx = {r["id"]: r for r in rows}
        for f in externes:
            r = idx.get(f["id"])
            if r:
                print(f"  {r['id']}  portail={r.get('portal') or '?'}  "
                      f"manuscrit={r.get('manuscript_id') or '?'}")
        print()

    print("Le registre ne connait que ce qu'on lui a dit : une decision arrivee par "
          "mail et non enregistree reste invisible ici. Confronter aux mails de "
          "l'editeur avant de conclure que tout va bien.")
    return 0


def cmd_reject(args) -> int:
    rows = load()
    idx = {r["id"]: i for i, r in enumerate(rows)}
    if args.id not in idx:
        print(f"identifiant inconnu : {args.id}", file=sys.stderr)
        return 1
    row = rows[idx[args.id]]
    when = args.on or date.today().isoformat()
    row["status"], row["status_on"] = "rejected", when
    row["decision"], row["decision_on"] = args.kind, when
    if args.editor:
        row["editor"] = args.editor
    row["notes"] = (row.get("notes", "") + " | " if row.get("notes") else "") + args.lesson
    save(rows)

    path = kb_dir() / "rejections.md"
    if not path.exists():
        path.write_text(
            "# Enseignements des decisions negatives\n\n"
            "Une entree par decision, ecrite seulement si elle apprend quelque chose\n"
            "de reutilisable pour une soumission future. Un rejet sans enseignement\n"
            "n'a pas sa place ici : il vit dans `submissions.tsv` et rien de plus.\n",
            encoding="utf-8")
    with path.open("a", encoding="utf-8") as fh:
        fh.write(f"\n## {when} — {row.get('journal_name')} — {row.get('project')}\n\n")
        fh.write(f"Decision : {args.kind}")
        if args.editor:
            fh.write(f", editeur {args.editor}")
        fh.write(f". Manuscrit `{row.get('manuscript_id') or row['id']}`, "
                 f"soumis le {row.get('submitted_on')}.\n\n")
        fh.write(f"Enseignement : {args.lesson}\n")
        if args.next_target:
            fh.write(f"\nReport vers : {args.next_target}\n")
    print(f"{args.id} : {args.kind} le {when}")
    print(f"enseignement ajoute a {path}")
    verdict, _ = variety_verdict(load(), row["journal_key"], row.get("publisher", ""))
    print(f"\nCette revue passe en cooldown {REJECT_COOLDOWN_DAYS} j "
          f"(verdict de variation : {verdict}).")
    return 0


# ── audit : ce que le registre ne sait pas de lui-meme ───────────────────────
# P46. Le 2026-08-30, trois ecarts ont ete trouves A LA MAIN sur douze lignes :
# une decision (desk-reject mSystems du 2026-08-09) consignee dans le cahier du
# projet et jamais reportee ici, ce qui laissait le registre afficher une double
# soumission active du meme manuscrit pendant 21 jours ; un quatrieme rejet absent
# de rejections.md ; et un champ `fr_version` perdu lors d'une resoumission, parce
# qu'`add` cree une ligne neuve sans heriter des acquis du manuscrit. Aucun de ces
# trois defauts n'est detectable par `list` ou par `stale` : ils ne portent pas sur
# l'age d'un statut mais sur sa VERITE, et la verite vit dans le cahier du projet.
#
# Ce que cette commande n'est PAS : un verdict. Elle apparie du texte libre, donc
# elle signale des entrees A LIRE, jamais une decision a enregistrer. Le registre
# ne se corrige que par `set` ou `reject`, apres lecture de l'entree signalee.

PROJECT_ROOTS_ENV = "SOUMISSION_PROJECTS"
_DEFAULT_PROJECT_ROOT = Path.home() / "docs" / "codes" / "mtbc"
# Un projet vit sous l'un des cinq repertoires de statut du depot (regle gravee
# le 2026-09-16), ou encore a plat a la racine tant que la migration vers
# `en_cours/` n'est pas faite : tous comptent pour l'audit, une soumission
# continuant de vivre apres la cloture du projet qui l'a produite. `clos_accepte`
# compte au meme titre : un manuscrit accepte garde son dossier de soumission.
_PROJECT_SUBDIRS = ("", "en_cours", "clos_soumis", "clos_accepte", "clos",
                    "clos_abandonne")

# Largeur de la fenetre de co-occurrence, en caracteres de part et d'autre du nom
# de la revue. 200 tient une phrase et sa voisine ; au-dela, on retrouve le bruit
# d'une entree entiere, en deca on manque « X. La revue a refuse le manuscrit ».
_FENETRE = 90

_DECISION_WORDS = (
    # Motifs FORTS : des formes ou une revue PRONONCE une decision, pas des mots
    # isoles. Mesure du 2026-08-30 : la liste large ("reject", "refus", "accept"…)
    # rendait 4 faux positifs sur 5 signalements, un cahier de soumission parlant de
    # rejets a longueur de page, y compris de ceux des projets voisins.
    "desk-reject", "desk reject", "reject-desk", "rejet sans revue",
    "a ete rejete", "a ete rejetee", "a ete refuse", "a ete refusee",
    "a ete accepte", "a ete acceptee", "hors perimetre",
    "decision editoriale", "notification de rejet", "revisions majeures",
    "major revision", "minor revision", "accepte pour publication",
)

_JOURNAL_STOPWORDS = {"the", "of", "and", "for", "journal", "international",
                      "review", "reviews", "research", "letters", "annals",
                      "archives", "advances", "current", "open", "access"}


def _deaccent(t: str) -> str:
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", t)
                   if unicodedata.category(c) != "Mn").lower()


def project_dir(project: str) -> Path | None:
    """Ou vit le projet qui a produit cette soumission, archive ou non."""
    roots = [Path(x) for x in os.environ.get(PROJECT_ROOTS_ENV, "").split(":") if x]
    roots.append(_DEFAULT_PROJECT_ROOT)
    for root in roots:
        for sub in _PROJECT_SUBDIRS:
            cand = (root / sub / project) if sub else (root / project)
            if (cand / "cahier_de_labo.md").exists():
                return cand
    return None


def _cahier_entries(d: Path) -> list[tuple[str, str, str]]:
    """(date, titre, corps) par entree de cahier, archive comprise."""
    out: list[tuple[str, str, str]] = []
    for name in ("cahier_de_labo.md", "cahier_de_labo_archive.md"):
        f = d / name
        if not f.exists():
            continue
        cur_date, cur_title, buf = "", "", []
        for line in f.read_text(errors="ignore").splitlines():
            m = re.match(r"^##\s+(\d{4}-\d{2}-\d{2})\s*(.*)$", line)
            if m:
                if cur_date:
                    out.append((cur_date, cur_title, "\n".join(buf)))
                cur_date, cur_title, buf = m.group(1), m.group(2)[:90], []
            elif cur_date:
                buf.append(line)
        if cur_date:
            out.append((cur_date, cur_title, "\n".join(buf)))
    return out


def _journal_tokens(row: dict) -> list[str]:
    toks = [t for t in re.split(r"[^a-z0-9]+", _deaccent(row.get("journal_name", "")))
            if len(t) >= 4 and t not in _JOURNAL_STOPWORDS]
    key = _deaccent(row.get("journal_key", "")).replace("-", " ")
    toks += [t for t in key.split() if len(t) >= 4 and t not in _JOURNAL_STOPWORDS]
    return sorted(set(toks))


def _self_test() -> int:
    """Temoin positif : le cas qui a motive cette commande doit etre retrouve.

    Le 2026-08-09, mSystems a rejete Rv2438A hors perimetre ; le cahier du projet le
    dit, le registre l'a ignore 21 jours. Un detecteur qui ne retrouve pas CE cas ne
    prouve rien quand il ne signale rien ailleurs. Le test rejoue donc l'appariement
    sur ce couple connu, sans toucher au registre.
    """
    d = project_dir("Rv2438A")
    if d is None:
        print("self-test IMPOSSIBLE : projet Rv2438A introuvable sur disque")
        return 1
    faux = {"journal_name": "mSystems", "journal_key": "msystems"}
    toks = _journal_tokens(faux)
    trouve = []
    for date, titre, corps in _cahier_entries(d):
        if date < "2026-08-04":
            continue
        texte = _deaccent(titre + "\n" + corps)
        for t in toks:
            for m in re.finditer(re.escape(t), texte):
                fen = texte[max(0, m.start() - _FENETRE):m.end() + _FENETRE]
                mot = next((w for w in _DECISION_WORDS if w in fen), None)
                if mot:
                    trouve.append((date, mot))
                    break
            if trouve and trouve[-1][0] == date:
                break
    if trouve:
        print(f"self-test OK : le desk-reject mSystems de Rv2438A est retrouve "
              f"({trouve[0][0]}, motif « {trouve[0][1]} »)")
        return 0
    print("self-test ECHOUE : le temoin positif connu n'est PAS retrouve.")
    print("  -> tout resultat vide de `audit` est donc ininterpretable ; elargir")
    print("     _DECISION_WORDS ou _FENETRE avant de conclure quoi que ce soit.")
    return 1


def cmd_audit(args) -> int:
    if getattr(args, "self_test", False):
        return _self_test()
    rows = load()
    active = [r for r in rows if r.get("status") in ACTIVE or r.get("status") == "preparing"]
    print(f"=== Audit du registre ({len(rows)} lignes, {len(active)} actives) ===\n")
    ecarts = 0

    # 1. deux lignes actives pour le meme manuscrit
    par_projet: dict[str, list[dict]] = {}
    for r in active:
        par_projet.setdefault(r.get("project", ""), []).append(r)
    for proj, rs in sorted(par_projet.items()):
        if len(rs) > 1:
            ecarts += 1
            print(f"[DOUBLE SOUMISSION ACTIVE] {proj} : {len(rs)} lignes actives")
            for r in rs:
                print(f"    {r['status']:10s} {r.get('journal_name','?')[:40]:42s} depuis {r.get('submitted_on','?')}")
            print("    -> un manuscrit ne peut etre en evaluation que dans UNE revue a la fois ;")
            print("       soit une decision n'a pas ete consignee, soit c'est une faute a corriger.\n")

    # 2. champs acquis perdus a la resoumission
    HERITABLES = ("preprint_server", "preprint_id", "github_repo", "zenodo_doi", "fr_version")
    for proj, rs in sorted(par_projet.items()):
        anciennes = [r for r in rows if r.get("project") == proj and r not in rs]
        for r in rs:
            for champ in HERITABLES:
                if r.get(champ):
                    continue
                source = next((a for a in anciennes if a.get(champ)), None)
                if source:
                    ecarts += 1
                    print(f"[CHAMP PERDU] {r['id']} : `{champ}` vide, mais renseigne sur {source['id']}")
                    print(f"    valeur disponible : {source[champ][:70]}")
                    print(f"    -> `add` cree une ligne neuve sans heriter ; reporter avec `set`.\n")

    # 3. decision visible dans le cahier du projet, absente du registre
    for r in active:
        proj = r.get("project", "")
        d = project_dir(proj)
        if d is None:
            print(f"[PROJET INTROUVABLE] {r['id']} : aucun cahier pour `{proj}`")
            print(f"    -> ligne non auditable ; definir {PROJECT_ROOTS_ENV} si le depot a bouge.\n")
            continue
        toks = _journal_tokens(r)
        if not toks:
            continue
        depuis = r.get("submitted_on") or r.get("status_on") or ""
        suspects = []
        for date, titre, corps in _cahier_entries(d):
            if depuis and date < depuis:
                continue
            texte = _deaccent(titre + "\n" + corps)
            # Co-occurrence RAPPROCHEE, pas presence dans la meme entree : un cahier
            # de soumission parle de rejets a longueur de page, et exiger seulement
            # que la revue et un mot de decision figurent dans la meme entree rendait
            # 4 faux positifs sur 5 signalements au premier essai (mesure 2026-08-30).
            # La fenetre ramene le test a « ce mot de decision parle-t-il de CETTE
            # revue », qui est la question posee.
            hit = None
            for t in toks:
                for m in re.finditer(re.escape(t), texte):
                    fen = texte[max(0, m.start() - _FENETRE):m.end() + _FENETRE]
                    mot = next((w for w in _DECISION_WORDS if w in fen), None)
                    if mot:
                        hit = mot
                        break
                if hit:
                    break
            if hit:
                suspects.append((date, titre, hit))
        if suspects:
            ecarts += 1
            print(f"[DECISION POSSIBLE NON CONSIGNEE] {r['id']} ({r['status']} depuis {depuis})")
            for date, titre, mot in suspects[-3:]:
                print(f"    cahier {date} [{mot}] : {titre}")
            print(f"    -> LIRE ces entrees. Si une decision y figure, l'enregistrer avec")
            print(f"       `submissions.py reject {r['id']} --lesson \"...\"` ou `set`.\n")

    if not ecarts:
        print("aucun ecart : chaque ligne active est coherente avec le cahier de son projet,")
        print("aucun manuscrit n'a deux lignes actives, aucun champ acquis n'a ete perdu.")
        return 0
    print(f"{ecarts} ecart(s) a verifier. Un signalement n'est pas un verdict :")
    print("lire l'entree de cahier avant de toucher au registre.")
    return 1


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("add", help="enregistre une soumission")
    sp.add_argument("--project", required=True)
    sp.add_argument("--title", required=True, help="titre court, lisible")
    sp.add_argument("--journal-key", required=True)
    sp.add_argument("--journal-name")
    sp.add_argument("--publisher")
    sp.add_argument("--portal")
    sp.add_argument("--domain")
    sp.add_argument("--status", default="submitted", choices=STATUSES)
    sp.add_argument("--submitted-on")
    sp.add_argument("--manuscript-id", help="identifiant rendu par le portail")
    sp.add_argument("--preprint-server")
    sp.add_argument("--preprint-id")
    sp.add_argument("--github-repo")
    sp.add_argument("--zenodo-doi")
    sp.add_argument("--fr-version", help="chemin du main_fr.tex, ou 'absent'")
    sp.add_argument("--notes")
    sp.add_argument("--id")
    sp.add_argument("--force", action="store_true", help="accepte une revue hors base")
    sp.set_defaults(func=cmd_add)

    sp = sub.add_parser("set", help="met a jour des champs")
    sp.add_argument("id")
    sp.add_argument("assign", nargs="+", metavar="champ=valeur")
    sp.add_argument("--on", help="date du changement (defaut aujourd'hui)")
    sp.set_defaults(func=cmd_set)

    sp = sub.add_parser("rename", help="corrige un identifiant devenu trompeur")
    sp.add_argument("old")
    sp.add_argument("new")
    sp.set_defaults(func=cmd_rename)

    sp = sub.add_parser("list", help="affiche le registre")
    sp.add_argument("--open", action="store_true", help="seulement les evaluations en cours")
    sp.add_argument("--project")
    sp.add_argument("--publisher")
    sp.set_defaults(func=cmd_list)

    sp = sub.add_parser("show", help="detail d'une soumission")
    sp.add_argument("id")
    sp.set_defaults(func=cmd_show)

    sp = sub.add_parser("variety", help="regle de variation avant de viser une revue")
    sp.add_argument("journal", help="cle de la revue visee")
    sp.add_argument("--publisher")
    sp.add_argument("--editor", help="editeur associe pressenti, si on le connait")
    sp.set_defaults(func=cmd_variety)

    sp = sub.add_parser("stale", help="soumissions sans nouvelle")
    sp.add_argument("--days", type=int, default=60)
    sp.set_defaults(func=cmd_stale)

    sp = sub.add_parser("review", help="point d'etat complet et anomalies a reprendre")
    sp.add_argument("--project", help="restreindre a un projet")
    sp.add_argument("--days", type=int, default=60,
                    help="au-dela de combien de jours un statut actif fige est signale")
    sp.set_defaults(func=cmd_review)

    sp = sub.add_parser("audit", help="ecarts entre le registre et les cahiers de projet")
    sp.add_argument("--self-test", action="store_true",
                    help="rejoue le temoin positif connu (desk-reject mSystems de Rv2438A)")
    sp.set_defaults(func=cmd_audit)

    sp = sub.add_parser("reject", help="enregistre une decision negative")
    sp.add_argument("id")
    sp.add_argument("--kind", default="reject-desk",
                    choices=["reject-desk", "reject-review", "reject-transfer",
                             "withdrawn"])
    sp.add_argument("--lesson", required=True,
                    help="ce que cette decision apprend pour la prochaine fois")
    sp.add_argument("--editor")
    sp.add_argument("--next-target")
    sp.add_argument("--on")
    sp.set_defaults(func=cmd_reject)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
