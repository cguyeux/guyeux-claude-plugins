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
]
ACTIVE = {"submitted", "with-editor", "under-review", "revision"}

# Seuils de la regle de variation. Voir references/choix-revue.md pour le pourquoi.
MAX_ACTIVE_SAME_JOURNAL = 1      # au-dela : refus
MAX_ACTIVE_SAME_PUBLISHER = 2    # au-dela : alerte
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
