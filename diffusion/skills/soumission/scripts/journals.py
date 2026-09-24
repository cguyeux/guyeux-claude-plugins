#!/usr/bin/env python3
"""Base de revues cibles : interrogation, filtrage et appariement manuscrit -> revue.

Donnees : $SOUMISSION_KB/journals.tsv (defaut ~/.agents/knowledge/journals/).
Schema : voir SCHEMA.md dans le meme repertoire. Zero dependance externe.

Sous-commandes
    merge    fusionne parts/*.tsv dans journals.tsv (dedoublonnage par key)
    list     filtre et affiche la base
    show     detail d'une revue
    match    classe les revues candidates pour un manuscrit donne
    set      met a jour un champ d'une revue
    lint     controle d'integrite du fichier
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
    "key", "name", "publisher", "domain", "scope_short", "article_types",
    "computational_only",
    "length_limit", "abstract_limit", "oa_model", "apc", "free_route",
    "hidden_fees", "impact_factor", "tier", "first_decision_days",
    "desk_reject_speed", "portal", "preprint_policy", "url_journal",
    "url_guide", "notes", "verified_on", "source",
]

# Valeurs de `computational_only`. Cette colonne existe parce qu'un scope
# thematique juste peut recouvrir une exclusion METHODOLOGIQUE invisible dans le
# resume de scope : c'est ce qui a produit les desk-rejects d'aout 2026 et fait
# preparer deux paquets pour des revues qui n'auraient jamais pris le manuscrit.
# Un depot qui produit surtout de la genomique sur donnees publiques sans
# validation experimentale doit pouvoir interroger cette dimension, sinon chaque
# manuscrit repaie le test exhaustif que le precedent a deja paye.
COMP_ACCEPTED = "accepted"        # precedents purement in silico verifies
COMP_CONDITIONAL = "conditional"  # clause avec porte de sortie, ou pratique divergente
COMP_EXCLUDED = "excluded"        # clause d'exclusion sans aucun contre-exemple
COMP_VALUES = {COMP_ACCEPTED, COMP_CONDITIONAL, COMP_EXCLUDED, "unknown"}

TIER_RANK = {"low-barrier": 1, "modest": 2, "solid": 3, "high": 4, "top": 5}
OA_FREE = {"diamond", "subscription", "s2o"}


def kb_dir() -> Path:
    return Path(os.environ.get(
        "SOUMISSION_KB", Path.home() / ".agents" / "knowledge" / "journals"))


def db_path() -> Path:
    return kb_dir() / "journals.tsv"


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


def read_tsv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as fh:
        return [dict(r) for r in csv.DictReader(fh, delimiter="\t")]


_LOADED_MTIME: float | None = None


def write_tsv(path: Path, rows: list[dict]) -> None:
    def render(fh):
        w = csv.DictWriter(fh, fieldnames=FIELDS, delimiter="\t",
                           extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for r in sorted(rows, key=lambda x: x.get("key", "")):
            w.writerow({f: (r.get(f) or "unknown").strip() for f in FIELDS})

    expected = _LOADED_MTIME if path == db_path() else None
    _atomic_write(path, render, mtime_before=expected)


def load() -> list[dict]:
    global _LOADED_MTIME
    _LOADED_MTIME = _mtime_or_none(db_path())
    return read_tsv(db_path())


# --------------------------------------------------------------------------
# parsing tolerant des champs libres
# --------------------------------------------------------------------------

NO_LIMIT = ("sans limite", "no limit", "unlimited", "not limited", "aucune limite",
            "no word limit", "no length limit", "no strict")


def parse_words(limit: str, kind: str | None = None) -> int | None:
    """Extrait une limite en mots depuis un champ libre. None si non exprimable.

    Un champ `length_limit` decrit souvent PLUSIEURS types d'article separes par
    des points-virgules ("Original Papers sans limite de longueur ; Short
    Communications 3-4 pages imprimees"). Chercher la premiere valeur numerique
    dans toute la chaine lit alors la limite du format COURT comme celle du format
    long, et fait annoncer un depassement de 2 000 mots la ou il n'y en a aucune.
    On ne lit donc qu'UN segment : celui qui correspond a `kind`, ou le premier a
    defaut, par convention le format principal.
    """
    if not limit or limit.lower() in {"unknown", "none", ""}:
        return None
    segments = [seg.strip() for seg in re.split(r"[;|]", limit) if seg.strip()]
    seg = segments[0] if segments else limit
    if kind:
        for candidate in segments:
            if kind.lower() in candidate.lower():
                seg = candidate
                break
    if any(tok in seg.lower() for tok in NO_LIMIT):
        return None
    s = seg.lower().replace(",", "").replace("\u00a0", " ")
    m = re.search(r"(\d{3,6})\s*(?:-|to|–)?\s*(\d{3,6})?\s*words?", s)
    if m:
        return int(m.group(2) or m.group(1))
    # "35000 characters" : les revues qui comptent en caracteres ne comptent pas
    # toutes les espaces ; 6 caracteres par mot est la conversion usuelle.
    m = re.search(r"(\d{4,7})\s*(?:characters?|caracteres?|signes?)", s)
    if m:
        return int(m.group(1)) // 6
    # "8 printed pages" / "10 pages" : ~750 mots par page imprimee de revue
    m = re.search(r"(\d{1,3})\s*(?:printed\s+)?pages?", s)
    if m:
        return int(m.group(1)) * 750
    return None


def parse_days(field: str) -> tuple[int | None, str]:
    """Rend (jours, semantique) depuis `first_decision_days`.

    La semantique n'est pas un detail : un « submission to first decision » de deux
    jours ne dit PAS que la revue relit vite, il dit qu'elle desk-reject beaucoup et
    tot. Confondre les deux revient a recompenser les revues qui refusent le plus,
    ce qui est exactement l'inverse du conseil utile.
    """
    if not field or field.lower() == "unknown":
        return None, "unknown"
    low = field.lower()
    sem = ("review" if "review" in low else
           "acceptance" if "accept" in low else
           "editorial" if "editorial" in low else
           "unqualified")
    m = re.search(r"(\d{1,4})", field)
    return (int(m.group(1)) if m else None), sem


def parse_if(field: str) -> float | None:
    if not field or field.lower() == "unknown":
        return None
    m = re.search(r"(\d+(?:[.,]\d+)?)", field)
    return float(m.group(1).replace(",", ".")) if m else None


def declares_no_limit(limit: str, kind: str | None = None) -> bool:
    """« Pas de limite de longueur » est un AVANTAGE, pas une donnee manquante.

    `parse_words` rend None dans les deux cas, ce qui reviendrait a traiter une
    revue qui n'impose rien comme une revue dont on ignore les contraintes.
    """
    if not limit or limit.lower() in {"unknown", "none", ""}:
        return False
    segments = [s.strip() for s in re.split(r"[;|]", limit) if s.strip()]
    seg = segments[0] if segments else limit
    if kind:
        for candidate in segments:
            if kind.lower() in candidate.lower():
                seg = candidate
                break
    return any(tok in seg.lower() for tok in NO_LIMIT)


def domains(row: dict) -> set[str]:
    return {d.strip() for d in (row.get("domain") or "").split(";") if d.strip()}


def types(row: dict) -> set[str]:
    return {d.strip() for d in (row.get("article_types") or "").split(";") if d.strip()}


def is_free(row: dict) -> bool:
    fr = (row.get("free_route") or "").lower()
    if fr in {"yes", "y", "true"}:
        return True
    if fr in {"no", "n", "false"}:
        return False
    return (row.get("oa_model") or "").lower() in OA_FREE


def staleness_days(row: dict) -> int | None:
    v = (row.get("verified_on") or "").strip()
    try:
        return (date.today() - datetime.strptime(v, "%Y-%m-%d").date()).days
    except ValueError:
        return None


# --------------------------------------------------------------------------
# commandes
# --------------------------------------------------------------------------

def cmd_merge(args) -> int:
    parts = sorted((kb_dir() / "parts").glob("*.tsv"))
    if not parts:
        print(f"aucun fichier dans {kb_dir() / 'parts'}", file=sys.stderr)
        return 1
    merged: dict[str, dict] = {r["key"]: r for r in load() if r.get("key")}
    conflicts, added, updated = [], 0, 0
    for p in parts:
        for row in read_tsv(p):
            key = (row.get("key") or "").strip()
            if not key:
                continue
            row.setdefault("source", p.stem)
            if key in merged:
                old, new = merged[key], row
                if (new.get("verified_on") or "") >= (old.get("verified_on") or ""):
                    diff = [f for f in FIELDS
                            if (old.get(f) or "") != (new.get(f) or "")
                            and (old.get(f) or "unknown") != "unknown"
                            and (new.get(f) or "unknown") != "unknown"]
                    if diff:
                        conflicts.append((key, p.stem, diff))
                    merged[key] = {**old, **{k: v for k, v in new.items()
                                             if v and v != "unknown"}}
                    updated += 1
            else:
                merged[key] = row
                added += 1
    write_tsv(db_path(), list(merged.values()))
    print(f"{db_path()} : {len(merged)} revues ({added} ajoutees, {updated} fusionnees)")
    if conflicts:
        print(f"\n{len(conflicts)} conflits de valeur entre sources "
              f"(la plus recemment verifiee gagne) :")
        for key, src, diff in conflicts[:25]:
            print(f"  {key:32s} <- {src:14s} {', '.join(diff)}")
    return 0


def _filter(rows: list[dict], args) -> list[dict]:
    out = rows
    if getattr(args, "domain", None):
        want = {d.strip() for d in args.domain.split(",")}
        out = [r for r in out if domains(r) & want]
    if getattr(args, "publisher", None):
        pat = args.publisher.lower()
        out = [r for r in out if pat in (r.get("publisher") or "").lower()]
    if getattr(args, "free", False):
        out = [r for r in out if is_free(r)]
    if getattr(args, "portal", None):
        out = [r for r in out if args.portal in (r.get("portal") or "")]
    if getattr(args, "tier", None):
        want = {t.strip() for t in args.tier.split(",")}
        out = [r for r in out if (r.get("tier") or "") in want]
    if getattr(args, "min_if", None) is not None:
        out = [r for r in out if (parse_if(r.get("impact_factor", "")) or 0) >= args.min_if]
    if getattr(args, "max_days", None) is not None:
        out = [r for r in out
               if (parse_days(r.get("first_decision_days", ""))[0] or 10**6) <= args.max_days]
    return out


def cmd_list(args) -> int:
    rows = _filter(load(), args)
    if not rows:
        print("aucune revue ne correspond")
        return 0
    rows.sort(key=lambda r: (-(parse_if(r.get("impact_factor", "")) or 0), r["key"]))
    print(f"{'KEY':30s} {'EDITEUR':16s} {'$':4s} {'IF':6s} {'NIV':10s} "
          f"{'1RE DEC':10s} {'PORTAIL':17s} NOM")
    print("-" * 130)
    for r in rows:
        print(f"{r['key'][:30]:30s} {(r.get('publisher') or '')[:16]:16s} "
              f"{'free' if is_free(r) else 'APC':4s} "
              f"{(parse_if(r.get('impact_factor','')) or 0) or '-':<6} "
              f"{(r.get('tier') or '')[:10]:10s} "
              f"{(r.get('first_decision_days') or '')[:10]:10s} "
              f"{(r.get('portal') or '')[:17]:17s} {(r.get('name') or '')[:44]}")
    print(f"\n{len(rows)} revues")
    return 0


def cmd_show(args) -> int:
    rows = {r["key"]: r for r in load()}
    r = rows.get(args.key)
    if not r:
        near = [k for k in rows if args.key.lower() in k.lower()]
        print(f"cle inconnue : {args.key}" + (f"\nproche : {', '.join(near[:8])}" if near else ""),
              file=sys.stderr)
        return 1
    width = max(len(f) for f in FIELDS)
    for f in FIELDS:
        val = r.get(f) or "unknown"
        print(f"{f:>{width}} : " + textwrap.fill(val, 100,
              subsequent_indent=" " * (width + 3)))
    st = staleness_days(r)
    if st is not None and st > 365:
        print(f"\nATTENTION : verifiee il y a {st} jours. Recontroler frais et scope "
              f"sur {r.get('url_guide') or r.get('url_journal')} avant de proposer.")
    return 0


def _submissions() -> list[dict]:
    return read_tsv(kb_dir() / "submissions.tsv")


def cmd_match(args) -> int:
    """Classe les revues pour un manuscrit. Le score est une AIDE AU TRI, jamais
    une decision : le choix final revient a l'auteur (cf. references/choix-revue.md)."""
    rows = load()
    if not rows:
        print("base vide : lancer `journals.py merge`", file=sys.stderr)
        return 1
    subs = _submissions()
    want_dom = {d.strip() for d in args.domain.split(",")}
    manu_tier = TIER_RANK.get(args.tier, 3)

    # charge editoriale en cours, pour la regle de variation. `preparing` compte
    # comme actif au meme titre que dans submissions.py (ACTIVE + `or status ==
    # "preparing"`, cf. son commentaire du 2026-08-25) : un paquet deja coupe au
    # gabarit et pret au depot pour une revue precise est une charge editoriale
    # reelle, pas une hypothese. Sans ce cas, `match` peut recommander une revue
    # que `preflight.py --journal` signale ensuite en ALERTE de variation (trouve
    # sur Rv0007 le 2026-09-01 : bpal_resistance_emergence "preparing" pour JAC,
    # invisible du classement `match` qui l'a pourtant remontee premiere).
    active = [s for s in subs if (s.get("status") or "") in
              {"submitted", "under-review", "revision", "with-editor", "preparing"}]
    per_journal, per_pub = {}, {}
    for s in active:
        per_journal[s.get("journal_key", "")] = per_journal.get(s.get("journal_key", ""), 0) + 1
        per_pub[s.get("publisher", "")] = per_pub.get(s.get("publisher", ""), 0) + 1
    rejected_recent = {s.get("journal_key", "") for s in subs
                       if (s.get("decision") or "").startswith("reject")}

    scored = []
    for r in rows:
        if not (domains(r) & want_dom):
            continue
        if args.free and not is_free(r):
            continue
        score, why = 0.0, []

        overlap = len(domains(r) & want_dom)
        score += 3 * overlap
        why.append(f"domaine x{overlap}")

        lim = parse_words(r.get("length_limit", ""))
        if declares_no_limit(r.get("length_limit", "")):
            score += 4
            fit = "aucune limite de longueur, rien a comprimer"
        elif lim is None:
            score -= 0.5
            fit = "limite inconnue, a verifier avant de proposer"
        elif args.words <= lim:
            score += 3
            fit = f"tient ({args.words} <= {lim} mots)"
        elif args.words <= lim * 1.35:
            score += 1
            fit = f"adaptable (-{args.words - lim} mots vers le supplement)"
        else:
            score -= 4
            fit = f"trop long ({args.words} vs {lim} mots)"
        why.append(fit)

        rt = TIER_RANK.get(r.get("tier", ""), 3)
        gap = rt - manu_tier
        score += {0: 3, 1: 1, -1: 1}.get(gap, -2 * abs(gap))
        why.append(f"niveau {'aligne' if gap == 0 else f'ecart {gap:+d}'}")

        if is_free(r):
            score += 2
            why.append("gratuit auteur")
        else:
            score -= 3
            why.append(f"APC {r.get('apc')}")

        # Le delai ne compte comme un avantage que si c'est une decision APRES
        # relecture. Un « submission to first decision » de quelques jours mesure
        # la propension a desk-rejeter, pas la rapidite : le bonifier reviendrait a
        # recommander en priorite les revues qui refusent le plus vite.
        d, sem = parse_days(r.get("first_decision_days", ""))
        if d is None:
            score -= 0.5
            why.append("delai inconnu")
        elif sem == "review":
            if d <= 45:
                score += 2
                why.append(f"decision apres relecture {d} j")
            elif d <= 90:
                score += 1
                why.append(f"decision apres relecture {d} j")
            else:
                score -= 2
                why.append(f"relecture lente ({d} j)")
        elif sem == "acceptance":
            why.append(f"soumission a acceptation {d} j, delai de relecture non publie")
        elif sem == "editorial":
            if d <= 7:
                why.append(f"tri editorial en {d} j : la revue desk-rejette vite et "
                           "souvent, echec peu couteux mais fit a verifier serieusement")
            else:
                why.append(f"tri editorial {d} j")
        else:
            why.append(f"delai {d} j de semantique non etablie, a revalider")

        if args.types:
            want_t = {t.strip() for t in args.types.split(",")}
            if types(r) and not (types(r) & want_t):
                score -= 3
                why.append(f"type non accepte ({args.types})")

        # Manuscrit sans validation experimentale des auteurs : une exclusion
        # methodologique est plus fatale qu'un mauvais fit thematique, parce
        # qu'aucune reecriture ne la leve.
        if args.computational:
            comp = (r.get("computational_only") or "unknown").strip().lower()
            if comp == COMP_EXCLUDED:
                score -= 8
                why.append("EXCLUSION : refuse le purement computationnel")
            elif comp == COMP_CONDITIONAL:
                score -= 1
                why.append("computationnel accepte SOUS CONDITION, lire la clause")
            elif comp == COMP_ACCEPTED:
                score += 3
                why.append("precedent purement computationnel verifie")
            else:
                score -= 1.5
                why.append("acceptation du purement computationnel NON MESUREE")

        n_j = per_journal.get(r["key"], 0)
        if n_j:
            score -= 3 * n_j
            why.append(f"VARIATION : {n_j} manuscrit(s) deja en cours ici")
        n_p = per_pub.get(r.get("publisher", ""), 0)
        if n_p >= 2:
            score -= 1.5 * (n_p - 1)
            why.append(f"VARIATION : {n_p} en cours chez {r.get('publisher')}")
        if r["key"] in rejected_recent:
            score -= 5
            why.append("REJET ANTERIEUR sur cette revue")

        st = staleness_days(r)
        if st is not None and st > 365:
            why.append(f"fiche vieille de {st} j, a revalider")

        scored.append((score, r, why))

    scored.sort(key=lambda x: -x[0])
    top = scored[: args.top]
    if not top:
        print("aucune revue candidate : elargir --domain ou lever --free")
        return 0
    print(f"Manuscrit : domaine={args.domain} longueur={args.words} mots "
          f"niveau={args.tier}\n")
    for i, (score, r, why) in enumerate(top, 1):
        print(f"{i}. {r['name']}  [{r['key']}]   score {score:.1f}")
        print(f"   {r.get('publisher')} | {r.get('oa_model')} | "
              f"IF {r.get('impact_factor')} | 1re decision {r.get('first_decision_days')} "
              f"| portail {r.get('portal')}")
        print(f"   scope : {(r.get('scope_short') or '')[:160]}")
        print(f"   longueur : {r.get('length_limit')} | resume : {r.get('abstract_limit')}")
        print(f"   pour/contre : {' ; '.join(why)}")
        if (r.get("notes") or "unknown") != "unknown":
            print(f"   notes : {(r.get('notes') or '')[:200]}")
        print(f"   guide : {r.get('url_guide')}")
        print()
    print("Ce classement est une aide au tri. Le choix revient a l'auteur : "
          "lui presenter au moins trois options avec pour, contre, delai et chances.")
    return 0


def cmd_set(args) -> int:
    rows = load()
    idx = {r["key"]: i for i, r in enumerate(rows)}
    if args.key not in idx:
        if not args.create:
            print(f"cle inconnue : {args.key} (utiliser --create)", file=sys.stderr)
            return 1
        rows.append({f: "unknown" for f in FIELDS} | {"key": args.key})
        idx[args.key] = len(rows) - 1
    row = rows[idx[args.key]]
    for assign in args.assign:
        if "=" not in assign:
            print(f"attendu champ=valeur : {assign}", file=sys.stderr)
            return 1
        f, v = assign.split("=", 1)
        if f not in FIELDS:
            print(f"champ inconnu : {f}\nchamps : {', '.join(FIELDS)}", file=sys.stderr)
            return 1
        if f == "computational_only" and v.strip().lower() not in COMP_VALUES:
            print(f"valeur invalide : {v}\nattendu : {', '.join(sorted(COMP_VALUES))}",
                  file=sys.stderr)
            return 1
        row[f] = v.replace("\t", " ").strip()
    row["verified_on"] = args.verified_on or date.today().isoformat()
    write_tsv(db_path(), rows)
    print(f"{args.key} mis a jour ({len(args.assign)} champs), "
          f"verified_on={row['verified_on']}")
    return 0


def cmd_lint(args) -> int:
    path = db_path()
    if not path.exists():
        print(f"absent : {path}", file=sys.stderr)
        return 1
    problems = []
    with path.open(encoding="utf-8", newline="") as fh:
        header = fh.readline().rstrip("\r\n").split("\t")
        if header != FIELDS:
            problems.append(f"en-tete non conforme : {set(FIELDS) ^ set(header)}")
        for n, line in enumerate(fh, start=2):
            cells = line.rstrip("\r\n").split("\t")
            if len(cells) != len(FIELDS):
                problems.append(f"ligne {n} : {len(cells)} colonnes au lieu de {len(FIELDS)}")
    rows = load()
    seen = {}
    for r in rows:
        seen.setdefault(r.get("key"), []).append(r.get("name"))
    for k, names in seen.items():
        if len(names) > 1:
            problems.append(f"cle dupliquee : {k} ({names})")
    # Deux cles pour une meme revue : la regle de variation compte alors deux
    # revues distinctes la ou il n'y en a qu'une, et cesse de voir la concentration.
    by_name = {}
    for r in rows:
        by_name.setdefault((r.get("name") or "").strip().lower(), []).append(r["key"])
    for name, ks in by_name.items():
        if name and len(ks) > 1:
            problems.append(f"revue en double sous {len(ks)} cles : {name} "
                            f"({', '.join(ks)}) — resorber par `drop`")
    # Une gratuite CONDITIONNELLE annoncee comme inconditionnelle est le piege le
    # plus couteux de la base : elle fait remonter dans les classements des revues
    # ou l'auteur ne peut pas publier. Vecu le 2026-08-25 avec Open Research Europe
    # et Wellcome Open Research (reservees aux beneficiaires d'un financement) et
    # avec les titres Microbiology Society (accord d'etablissement).
    # Cibler les formulations qui RESTREIGNENT vraiment, pas les mots polysemiques.
    # Un premier jet declenchait sur « accord », et sortait trois faux positifs sur
    # quatre : « aucun accord transformatif » est une NEGATION, « accord prealable du
    # bureau editorial » ne parle pas de frais, et « un accord Couperin couvre » est
    # un avantage. Un controle qui crie faux cesse d'etre lu.
    CONDITIONNEL = ("reserve aux", "reservee aux", "uniquement si", "seulement si",
                    "conditionnee a", "conditionne a", "only if", "only for",
                    "beneficiaires", "beneficiaries", "publish and read",
                    "subscribe to open", "sous reserve d'un accord",
                    "depend de l'affiliation", "si l'etablissement")
    # `computational_only` reste `unknown` alors que `notes` porte deja la clause
    # d'exclusion qui aurait du la trancher : c'est l'ecart trouve sur
    # computers-in-biology-and-medicine le 2026-08-30 (desk-reject d'un manuscrit
    # entierement in silico) — la note capturait deja « sont refuses les travaux
    # reposant sur des outils in silico elementaires ... ou par des validations
    # experimentales detaillees », mais la colonne structuree, seule lue par
    # `match --computational`, etait restee `unknown` et n'a donc jamais penalise
    # la revue dans un classement. Meme mecanisme que le piege free_route
    # ci-dessus : un signal capture en prose ne protege personne s'il ne migre pas
    # dans le champ que les filtres lisent reellement.
    EXCLUSION_SIGNAL = (
        "in silico elementaire", "in silico elementaires", "sont refuses les travaux",
        "sans implication experimentale", "sans travail experimental",
        "validations experimentales detaillees", "validation experimentale detaillee",
        "meta-analyse fondee sur des bases publiques", "reanalyse de donnees publiees",
        "experimental validation is a mandatory", "experimental validation is required",
        "does not publish purely", "purely bioinformatic", "purely in silico",
        "purely computational approaches", "outside the scope of this journal",
        "requires experimental", "wet-lab validation",
    )
    for r in rows:
        if is_free(r) and (r.get("free_route") or "").lower() == "unknown":
            problems.append(f"{r['key']} : free_route deduit de oa_model, non verifie")
        if (r.get("free_route") or "").lower() == "yes":
            blob = ((r.get("notes") or "") + " " + (r.get("hidden_fees") or "")).lower()
            mots = [m for m in CONDITIONNEL if m in blob]
            if mots:
                problems.append(
                    f"{r['key']} : free_route=yes mais les notes evoquent une CONDITION "
                    f"({', '.join(mots)}). Une gratuite conditionnelle doit etre "
                    f"free_route=no tant que la condition n'est pas verifiee pour cet "
                    f"auteur, sinon la revue remonte a tort dans les classements")
        if (r.get("computational_only") or "unknown").strip().lower() == "unknown":
            blob = (r.get("notes") or "").lower()
            mots = [m for m in EXCLUSION_SIGNAL if m in blob]
            if mots:
                problems.append(
                    f"{r['key']} : computational_only=unknown mais les notes portent deja "
                    f"un signal d'exclusion methodologique ({', '.join(mots)}). Trancher le "
                    f"champ (accepted/conditional/excluded) avant de laisser cette revue "
                    f"remonter dans `match --computational`, ou elle echappe a la penalite "
                    f"que la colonne existe pour appliquer")
        st = staleness_days(r)
        if st is None:
            problems.append(f"{r['key']} : verified_on absent ou mal forme")
    # Une cle de revue citee par le registre mais absente de la base rend la regle
    # de variation aveugle sur cette revue : c'est une erreur silencieuse.
    keys = {r.get("key") for r in rows}
    orphans = {}
    for s in _submissions():
        k = s.get("journal_key", "")
        if k and k not in keys:
            orphans.setdefault(k, []).append(s.get("project", "?"))
    for k, projets in orphans.items():
        near = [c for c in keys if c and (c.startswith(k[:12]) or k.startswith(c[:12]))]
        problems.append(f"cle citee par le registre mais absente de la base : {k} "
                        f"({', '.join(projets)})"
                        + (f" — proche : {', '.join(near)} ; corriger par `rename`"
                           if near else ""))

    unknown_rate = {
        f: sum(1 for r in rows if (r.get(f) or "unknown") == "unknown") for f in FIELDS
    }
    print(f"{len(rows)} revues dans {path}")
    print("\nTaux d'inconnu par champ (les plus lacunaires) :")
    for f, n in sorted(unknown_rate.items(), key=lambda x: -x[1])[:10]:
        if n:
            print(f"  {f:20s} {n:4d}/{len(rows)}")
    if problems:
        print(f"\n{len(problems)} problemes :")
        for p in problems[:40]:
            print(f"  {p}")
        return 1
    print("\naucun probleme structurel")
    return 0


def cmd_rename(args) -> int:
    """Renomme une cle dans la base, dans le registre ET dans les fragments sources.

    Oublier les fragments est une erreur qui se repare toute seule dans le mauvais
    sens : le merge suivant relit `parts/` et reintroduit l'ancienne cle a cote de
    la nouvelle, donc la meme revue figure deux fois et la regle de variation cesse
    de voir la concentration.
    """
    rows = load()
    keys = {r["key"] for r in rows}
    if args.new in keys and args.old in keys:
        print("les deux cles existent deja : utiliser `drop` sur celle a abandonner "
              "apres avoir verifie qu'elle ne porte rien d'unique", file=sys.stderr)
        return 1
    n = 0
    for r in rows:
        if r.get("key") == args.old:
            r["key"] = args.new
            n += 1
    if n:
        write_tsv(db_path(), rows)

    p = 0
    for part in sorted((kb_dir() / "parts").glob("*.tsv")):
        prows = read_tsv(part)
        hit = [r for r in prows if r.get("key") == args.old]
        if not hit:
            continue
        for r in hit:
            r["key"] = args.new
        fields = list(prows[0].keys())
        with part.open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=fields, delimiter="\t",
                               lineterminator="\n")
            w.writeheader()
            w.writerows(prows)
        p += len(hit)

    sub_path = kb_dir() / "submissions.tsv"
    m = 0
    if sub_path.exists():
        subs = read_tsv(sub_path)
        for s in subs:
            if s.get("journal_key") == args.old:
                s["journal_key"] = args.new
                m += 1
        if m:
            fields = list(subs[0].keys())
            with sub_path.open("w", encoding="utf-8", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=fields, delimiter="\t",
                                   lineterminator="\n")
                w.writeheader()
                w.writerows(subs)
    if not n and not m and not p:
        print(f"cle absente partout : {args.old}", file=sys.stderr)
        return 1
    print(f"{args.old} -> {args.new} : {n} revue(s), {m} soumission(s), "
          f"{p} ligne(s) de fragment")
    return 0


def cmd_drop(args) -> int:
    """Supprime une cle de la base et des fragments. Pour resorber un doublon."""
    rows = load()
    victim = next((r for r in rows if r.get("key") == args.key), None)
    if not victim:
        print(f"cle absente : {args.key}", file=sys.stderr)
        return 1
    twins = [r for r in rows
             if r.get("name") == victim.get("name") and r.get("key") != args.key]
    if not twins and not args.force:
        print(f"{args.key} ({victim.get('name')}) n'a pas de jumeau portant le meme "
              f"nom : la supprimer perdrait la seule fiche de cette revue.\n"
              f"Utiliser --force si c'est bien voulu.", file=sys.stderr)
        return 1
    subs = read_tsv(kb_dir() / "submissions.tsv")
    used = [s.get("project") or "?" for s in subs if s.get("journal_key") == args.key]
    if used:
        print(f"{args.key} est cite par le registre ({', '.join(used)}) : "
              f"faire d'abord `rename {args.key} <cle_conservee>`", file=sys.stderr)
        return 1

    # Deux agents ayant verifie la meme revue separement, chaque fiche peut porter
    # des champs que l'autre a laisses en `unknown`. Supprimer sans reverser
    # perdrait du travail deja fait et deja source.
    kept_key = args.into or (twins[0]["key"] if twins else None)
    filled = []
    if kept_key:
        kept = next((r for r in rows if r.get("key") == kept_key), None)
        if kept is None:
            print(f"cle de destination inconnue : {kept_key}", file=sys.stderr)
            return 1
        for f in FIELDS:
            if f in ("key", "verified_on", "source"):
                continue
            v_keep, v_drop = kept.get(f) or "unknown", victim.get(f) or "unknown"
            if v_keep == "unknown" and v_drop != "unknown":
                kept[f] = v_drop
                filled.append(f)
            elif f == "notes" and v_drop != "unknown" and v_drop not in v_keep:
                kept[f] = f"{v_keep} | {v_drop}" if v_keep != "unknown" else v_drop
                filled.append(f)

    write_tsv(db_path(), [r for r in rows if r.get("key") != args.key])
    p = 0
    for part in sorted((kb_dir() / "parts").glob("*.tsv")):
        prows = read_tsv(part)
        kept = [r for r in prows if r.get("key") != args.key]
        if len(kept) == len(prows):
            continue
        p += len(prows) - len(kept)
        fields = list(prows[0].keys())
        with part.open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=fields, delimiter="\t",
                               lineterminator="\n")
            w.writeheader()
            w.writerows(kept)
    msg = f"{args.key} supprimee de la base et de {p} ligne(s) de fragment"
    if kept_key:
        msg += f" ; conservee sous {kept_key}"
        if filled:
            msg += f", enrichie de {len(filled)} champs ({', '.join(filled[:6])})"
    print(msg)
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("merge", help="fusionne parts/*.tsv").set_defaults(func=cmd_merge)

    def add_filters(sp):
        sp.add_argument("--domain", help="domaines separes par des virgules")
        sp.add_argument("--publisher")
        sp.add_argument("--free", action="store_true", help="voie sans frais auteur seulement")
        sp.add_argument("--portal")
        sp.add_argument("--tier")
        sp.add_argument("--min-if", type=float)
        sp.add_argument("--max-days", type=int, help="delai max de 1re decision")

    sp = sub.add_parser("list", help="filtre la base")
    add_filters(sp)
    sp.set_defaults(func=cmd_list)

    sp = sub.add_parser("show", help="detail d'une revue")
    sp.add_argument("key")
    sp.set_defaults(func=cmd_show)

    sp = sub.add_parser("match", help="classe les revues pour un manuscrit")
    sp.add_argument("--domain", required=True)
    sp.add_argument("--words", type=int, required=True, help="longueur du corps en mots")
    sp.add_argument("--tier", default="solid", choices=list(TIER_RANK),
                    help="niveau estime du manuscrit, honnetement")
    sp.add_argument("--types", help="type d'article vise : research, short, method...")
    sp.add_argument("--free", action="store_true")
    sp.add_argument("--computational", action="store_true",
                    help="manuscrit SANS validation experimentale des auteurs : penalise "
                         "lourdement les revues qui excluent le purement computationnel, "
                         "et signale celles dont la dimension n'a pas ete mesuree")
    sp.add_argument("--top", type=int, default=8)
    sp.set_defaults(func=cmd_match)

    sp = sub.add_parser("set", help="met a jour des champs")
    sp.add_argument("key")
    sp.add_argument("assign", nargs="+", metavar="champ=valeur")
    sp.add_argument("--create", action="store_true")
    sp.add_argument("--verified-on")
    sp.set_defaults(func=cmd_set)

    sp = sub.add_parser("rename", help="renomme une cle dans la base et le registre")
    sp.add_argument("old")
    sp.add_argument("new")
    sp.set_defaults(func=cmd_rename)

    sp = sub.add_parser("drop", help="supprime une cle en double")
    sp.add_argument("key")
    sp.add_argument("--into", help="cle conservee, qui recupere les champs renseignes "
                                   "de celle qu'on supprime (defaut : le jumeau de "
                                   "meme nom)")
    sp.add_argument("--force", action="store_true",
                    help="supprimer meme sans jumeau portant le meme nom")
    sp.set_defaults(func=cmd_drop)

    sub.add_parser("lint", help="controle d'integrite").set_defaults(func=cmd_lint)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
