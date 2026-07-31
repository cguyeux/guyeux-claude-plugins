#!/usr/bin/env python3
"""Audit mecanique des SKILL.md canoniques du depot claude_plugins.

Usage :
    python3 _audit/tools/audit_skills.py            # resume + audit.json
    python3 _audit/tools/audit_skills.py --detail   # une ligne par signalement

AVERTISSEMENT DE METHODE, appris a la revue du 2026-07-31 : un decompte produit
par ce script est une LISTE DE CANDIDATS A INSPECTER, jamais un verdict. Lors de
la premiere passe, trois metriques sur quatre etaient du bruit :

- la detection d'emojis attrapait les caracteres de dessin de boite, les fleches
  et les symboles mathematiques (regex corrigee ici, mais rester mefiant) ;
- la detection de declencheur ne cherchait que « use when » et manquait
  « use for », « a utiliser », « pour toute » (corrigee ici) ;
- les references de fichiers absentes etaient a 85 % des chemins inter-skills
  relatifs, des URL ou du contenu d'exemple (le script les signale toujours,
  c'est a l'humain de trancher).

Ne jamais rapporter un chiffre de sortie sans avoir inspecte les cas un par un.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PLUGINS = ["bio_pathogens", "bio_population_genetics", "redac", "bio_redac",
           "ia", "multimedia", "ops", "web", "maboss"]

# Vocabulaire qui declenche le classifieur AUP sans cadrage explicite.
# Volontairement etroit : « pathogen », « strain » ou « resistance » seuls dans
# une phrase manifestement academique produisaient 17 faux positifs sur 17.
AUP_RISQUE = re.compile(
    r"\b(drug.resistan\w*|outbreak|surveillance|epidemic|transmission chain|"
    r"contamination|virulen\w*)\b", re.I)
AUP_CADRE = re.compile(
    r"(academic|peer-reviewed|published research|scientific publication|"
    r"research toolkit|FEMTO|Guyeux|phylogenom|evolutionary)", re.I)

DECLENCHEUR = re.compile(
    r"(use when|use this|use for|use to|used when|when the user|trigger|"
    r"utiliser quand|a utiliser|pour toute|pour tout |load when|invoke)", re.I)

# Emojis reels uniquement. Les caracteres de dessin de boite (U+2500-257F), les
# fleches (U+2190-21FF) et les operateurs mathematiques (U+2200-22FF) N'EN SONT
# PAS, et les marqueurs de section DO/DON'T sont fonctionnels : ne pas les
# retirer, ce sont eux qui structurent les regles dans le format Anthropic.
EMOJI = re.compile(r"[\U0001F300-\U0001F9FF]")

REF_FICHIER = re.compile(r"(?:scripts?|references?|assets?|src|templates?)/[\w./-]+")

DESC_MAX = 1024   # au-dela, la description risque d'etre tronquee dans le catalogue
CORPS_MAX = 6000  # au-dela, le SKILL.md dilue l'attention a chaque chargement
CORPS_MIN = 60


def parse_frontmatter(text: str):
    """Renvoie (dict, corps). dict vaut None si le frontmatter est absent."""
    if not text.startswith("---"):
        return None, text
    end = text.find("\n---", 3)
    if end == -1:
        return None, text
    fm, key = {}, None
    for line in text[3:end].splitlines():
        if not line.strip():
            continue
        m = re.match(r"^([A-Za-z][\w-]*):\s*(.*)$", line)
        if m:
            key = m.group(1)
            fm[key] = m.group(2).strip()
        elif key and line[:1] in " \t":
            fm[key] = (fm[key] + " " + line.strip()).strip()
    return fm, text[end + 4:]


def skills_canoniques():
    """Un seul enregistrement par skill reel, quel que soit le nombre de symlinks."""
    vus = {}
    for plug in PLUGINS:
        sd = ROOT / plug / "skills"
        if not sd.is_dir():
            continue
        for entry in sorted(sd.iterdir()):
            if not entry.is_dir():
                continue
            cible = entry.resolve()
            rec = vus.setdefault(str(cible), {
                "path": cible, "dir": cible.name,
                "home": cible.relative_to(ROOT).parts[0],
                "plugins": [], "reel_dans": [],
            })
            rec["plugins"].append(plug)
            if not entry.is_symlink():
                rec["reel_dans"].append(plug)
    return sorted(vus.values(), key=lambda r: (r["home"], r["dir"]))


def audit():
    rows = []
    for rec in skills_canoniques():
        p: Path = rec["path"]
        r: dict[str, Any] = dict(rec, path=str(p), issues=[])
        sk = p / "SKILL.md"
        if not sk.exists():
            r["issues"].append("PAS_DE_SKILL_MD")
            rows.append(r)
            continue

        text = sk.read_text(encoding="utf-8", errors="replace")
        fm, corps = parse_frontmatter(text)
        r["mots"] = len(corps.split())
        r["sha"] = hashlib.sha1(text.encode()).hexdigest()[:10]
        if fm is None:
            r["issues"].append("FRONTMATTER_ABSENT")
            fm = {}

        nom, desc = fm.get("name", ""), fm.get("description", "")
        r["name"], r["desc"], r["desc_len"] = nom, desc, len(desc)

        if not nom:
            r["issues"].append("NAME_MANQUANT")
        elif nom != p.name:
            r["issues"].append(f"NAME_MISMATCH({nom}!={p.name})")

        if not desc:
            r["issues"].append("DESC_MANQUANTE")
        else:
            if len(desc) < 80:
                r["issues"].append(f"DESC_COURTE({len(desc)})")
            if len(desc) > DESC_MAX:
                r["issues"].append(f"DESC_TROP_LONGUE({len(desc)})")
            if not DECLENCHEUR.search(desc):
                r["issues"].append("DESC_SANS_DECLENCHEUR")
            if AUP_RISQUE.search(desc) and not AUP_CADRE.search(desc):
                r["issues"].append("AUP_NON_CADRE")

        if r["mots"] < CORPS_MIN:
            r["issues"].append(f"CORPS_MAIGRE({r['mots']}mots)")
        if r["mots"] > CORPS_MAX:
            r["issues"].append(f"CORPS_OBESE({r['mots']}mots)")

        # references de fichiers : bruyant par construction, a inspecter
        manquants = sorted({
            f for f in (m.group(0).rstrip(".,);:`\"'") for m in REF_FICHIER.finditer(corps))
            if "<" not in f and "*" not in f
            and not (p / f).exists() and not (p / f.split("/", 1)[-1]).exists()
        })
        if manquants:
            r["issues"].append("REF_FICHIER_A_VERIFIER:" + ",".join(manquants[:5]))

        # tirets cadratin : seule la PROSE compte, ceux des blocs de code sont
        # legitimes (arbres ASCII, sorties d'exemple). Voir tools/dedash.py.
        n_prose = 0
        fence = False
        for line in corps.splitlines():
            if line.lstrip().startswith(("```", "~~~")):
                fence = not fence
                continue
            if fence or "—" not in line:
                continue
            n_prose += re.sub(r"`[^`]*`", "", line).count("—")
        if n_prose:
            r["issues"].append(f"TIRET_CADRATIN_PROSE({n_prose})")

        if EMOJI.search(text):
            r["issues"].append("EMOJI")

        rows.append(r)
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--detail", action="store_true",
                    help="une ligne par skill signale")
    ap.add_argument("--json", type=Path, default=Path(__file__).with_name("audit.json"))
    args = ap.parse_args()

    rows = audit()
    args.json.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"{len(rows)} skills canoniques audites, rapport dans {args.json}")
    signales = [r for r in rows if r["issues"]]
    print(f"{len(signales)} avec au moins un signalement\n")

    c = Counter(i.split("(")[0].split(":")[0] for r in rows for i in r["issues"])
    for k, v in c.most_common():
        print(f"{v:4d}  {k}")

    if args.detail:
        print()
        for r in signales:
            print(f"{r['home']:24s} {r['dir']:34s} {'; '.join(r['issues'])}")

    # doublons : deux copies REELLES d'un meme nom divergent en silence
    par_nom = defaultdict(list)
    for r in rows:
        par_nom[r["dir"]].append(r)
    dbl = {n: v for n, v in par_nom.items() if len(v) > 1}
    if dbl:
        print("\nNoms portes par plusieurs skills reels :")
        for n, v in sorted(dbl.items()):
            etat = "IDENTIQUES" if len({x["sha"] for x in v}) == 1 else "divergents"
            print(f"  {n:32s} {[x['home'] for x in v]}  {etat}")
        print("  (IDENTIQUES = a symlinker sur le canonique avant divergence)")

    return 1 if signales else 0


if __name__ == "__main__":
    raise SystemExit(main())
