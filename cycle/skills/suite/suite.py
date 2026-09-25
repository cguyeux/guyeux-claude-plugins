#!/usr/bin/env python3
"""/suite — consigne la piste suivante à traiter avant un /clear.

Écrit dans ~/.claude/state/suite/<hash(root)>.md la piste ouverte la plus
prioritaire (en cours avant à faire, ordre du fichier), avec son étiquette
[Modèle:effort] si `/routage étiqueter` l'a déjà posée. Ne recalcule PAS la
logique de routage : réutilise les étiquettes existantes de pistes.md —
décision CG du 2026-09-16, piste S de environnement/pistes.md.

Parseur : `carrefour.py::parse_pistes_tree`, pas `status.py::lire_registre`.
`status.py` ne reconnaît que les identifiants `P<chiffre>` (RE_HEAD/RE_ITEM),
alors que ce projet (et `mtbc/`) numérote aussi des chantiers hors rail avec
une autre lettre (`N6`, `S2`...) ; `carrefour.py` a déjà reçu ce
correctif le 2026-09-16 (piste Q1) et a été régression-testé sur le corpus
réel. Réutiliser le parseur déjà reforgé plutôt que le parseur encore
déficient est le choix retenu ici — corriger `status.py` à son tour reste
une dette tracée séparément (piste S5, ouverte le 2026-09-16), plus lourde
qu'un correctif ponctuel : plusieurs regex à reprendre, à régression-tester
sur le corpus réel comme carrefour.py l'a été, hors du périmètre de /suite.

Le hook SessionStart (matcher "clear") relit ce fichier une fois puis le
supprime : la suggestion ne doit pas survivre à un /clear qu'elle ne visait
pas.
"""
import datetime
import hashlib
import re
import sys
from pathlib import Path

# `pistes` est un skill voisin du meme plugin ; chemin relatif d'abord (portable apres
# clonage/installation), repli sur le skill personnel pour qui n'a que celui-ci.
for _cand in (Path(__file__).resolve().parent.parent / "pistes",
              Path.home() / ".claude" / "skills" / "pistes"):
    if _cand.is_dir():
        sys.path.insert(0, str(_cand))
        break
from carrefour import OPEN_STATES, STATE_RE, parse_pistes_tree  # noqa: E402
from status import RE_TAG, detecter_prefixes  # noqa: E402


def racine_projet(depart: Path) -> Path | None:
    d = depart.resolve()
    for _ in range(6):
        if (d / "cahier_de_labo.md").is_file():
            return d
        if d.parent == d:
            break
        d = d.parent
    return None


def bloc_texte(item: dict) -> str:
    return item["text"] + " " + " ".join(item.get("tail", item.get("body", [])))


def priorite(item: dict) -> int:
    """0 = en cours, 1 = à faire, 2 = ouvert mais état textuel non retrouvé."""
    bloc = bloc_texte(item)
    tags = [strip.lower() for strip in
            (m.group(1).strip() for m in reversed(list(STATE_RE.finditer(bloc))))]
    for tag in tags:
        if tag.startswith("en cours"):
            return 0
        if tag.startswith(("à faire", "a faire")):
            return 1
        if any(tag.startswith(o) for o in OPEN_STATES):
            return 2
    return 2


def choisir_piste(items: list[dict]) -> dict | None:
    ouverts = [it for it in items if it.get("type") == "question"]
    if not ouverts:
        return None
    return min(ouverts, key=lambda it: (priorite(it), items.index(it)))


# Forme d'un identifiant de piste dans ce dépôt : 1-3 lettres majuscules, chiffre
# optionnel, puis suffixes `.`/`-` (P2.6, S7, AB3.a, AC1bis). Sert uniquement à
# décider si l'argument de la ligne de commande DÉSIGNE une piste existante plutôt
# qu'à valider la syntaxe en général — cf. piste S7 de environnement/pistes.md.
RE_ID_CANDIDAT = re.compile(r"^[A-Z]{1,3}[0-9]*(?:[.\-][0-9A-Za-z]+)*$")


def trouver_piste(items: list[dict], ref: str) -> dict | None:
    for it in items:
        if it.get("ref") == ref:
            return it
    return None


def main() -> int:
    root = racine_projet(Path.cwd())
    if root is None:
        print("Aucun projet structuré trouvé (pas de cahier_de_labo.md en remontant "
              "depuis le répertoire courant). /suite est sans objet ici.")
        return 0

    pistes_md = root / "pistes.md"
    if not pistes_md.is_file():
        print(f"{root} n'a pas de pistes.md : rien à suggérer. /clear reste un geste "
              "simple ici.")
        return 0

    items = parse_pistes_tree(pistes_md)
    detail_dir = root / "pistes"
    if detail_dir.is_dir():
        # Namespace : ne pas coder en dur "P*.md", cf. piste S8 de environnement/pistes.md
        # (même défaut réglé par AD1 dans impact_done.py) — réutiliser
        # status.detecter_prefixes() plutôt que dupliquer sa logique de détection.
        prefixes = detecter_prefixes(str(root))
        fichier_re = re.compile(r"^(?:" + "|".join(sorted(prefixes, key=len, reverse=True))
                                 + r")(?:[0-9]+)?\.md$")
        for p in sorted(detail_dir.iterdir()):
            if fichier_re.match(p.name):
                items.extend(parse_pistes_tree(p))

    etat_dir = Path.home() / ".claude/state/suite"
    etat_dir.mkdir(parents=True, exist_ok=True)
    cle = hashlib.md5(str(root).encode("utf-8")).hexdigest()[:16]
    fichier = etat_dir / f"{cle}.md"

    # Argument optionnel (piste S7) : soit un identifiant de piste connu du projet
    # (`/suite P2.6`), qui va chercher titre et étiquette dans pistes.md comme le
    # choix automatique ; soit, si l'argument n'est pas un identifiant reconnu, un
    # texte libre repris tel quel comme amorce (diagnostic déjà rédigé, contraintes
    # déjà posées). Sans argument, comportement historique inchangé.
    arg = " ".join(sys.argv[1:]).strip()
    choix = None
    amorce_libre = None
    if arg:
        if RE_ID_CANDIDAT.match(arg):
            choix = trouver_piste(items, arg)
        if choix is None:
            amorce_libre = arg

    if amorce_libre is not None:
        contenu = (
            f"[SUITE — amorce fournie avant ce /clear]\n"
            f"Projet : {root.name} ({root})\n"
            f"{amorce_libre}\n"
            f"(posée par /suite le {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')})"
        )
        fichier.write_text(contenu + "\n", encoding="utf-8")
        print(f"Amorce consignée telle quelle pour la suite : {amorce_libre}")
        print("Tapez /clear : la suggestion réapparaîtra automatiquement juste après.")
        return 0

    if choix is None:
        choix = choisir_piste(items)
    if choix is None:
        fichier.unlink(missing_ok=True)
        print(f"Aucune piste ouverte dans {root}/pistes.md. Rien à consigner avant le "
              "/clear.")
        return 0

    pid = choix["ref"]
    titre = choix["text"][:110]
    tag_m = RE_TAG.search(bloc_texte(choix))
    tag_txt = tag_m.group(0) if tag_m else "non étiqueté — lancer /routage étiqueter avant de router"
    etat_txt = "en cours" if priorite(choix) == 0 else "à faire"

    contenu = (
        f"[SUITE — piste suggérée avant ce /clear]\n"
        f"Projet : {root.name} ({root})\n"
        f"Piste {pid} [{etat_txt}] {tag_txt} — {titre}\n"
        f"(posée par /suite le {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')})"
    )
    fichier.write_text(contenu + "\n", encoding="utf-8")

    print(f"Piste suggérée pour la suite : {pid} [{etat_txt}] {tag_txt} — {titre}")
    print("Tapez /clear : la suggestion réapparaîtra automatiquement juste après.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
