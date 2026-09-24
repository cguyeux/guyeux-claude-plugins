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
- la longueur du corps depend du workflow. Elle reste disponible dans
  `audit.json`, mais ne constitue pas un echec mecanique : une extraction vers
  `references/` doit etre decidee apres lecture de la structure du skill.

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


def marketplace_plugins(root: Path = ROOT) -> list[tuple[str, Path]]:
    """Lire les plugins depuis le manifeste canonique du marketplace."""
    marketplace = root / ".claude-plugin" / "marketplace.json"
    data = json.loads(marketplace.read_text(encoding="utf-8"))
    plugins = data.get("plugins")
    if not isinstance(plugins, list):
        raise ValueError(f"liste `plugins` absente de {marketplace}")

    resolved_root = root.resolve()
    result: list[tuple[str, Path]] = []
    seen: set[str] = set()
    for record in plugins:
        if not isinstance(record, dict):
            raise ValueError(f"entree plugin invalide dans {marketplace}")
        name, source = record.get("name"), record.get("source")
        if not isinstance(name, str) or not isinstance(source, str):
            raise ValueError(f"plugin sans nom/source valide dans {marketplace}")
        if name in seen:
            raise ValueError(f"plugin duplique dans {marketplace}: {name}")
        path = (root / source).resolve()
        try:
            path.relative_to(resolved_root)
        except ValueError as exc:
            raise ValueError(f"source plugin hors depot: {source}") from exc
        if not path.is_dir():
            raise ValueError(f"source plugin absente: {source}")
        seen.add(name)
        result.append((name, path))
    return result

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
    r"(use when|use this|use for|use to|use here|use proactively when|"
    r"used when|when the user|trigger|"
    r"utiliser quand|a utiliser|pour toute|pour tout |toute demande|"
    r"déclencher|declencher|load when|invoke)", re.I)

# Emojis reels uniquement. Les caracteres de dessin de boite (U+2500-257F), les
# fleches (U+2190-21FF) et les operateurs mathematiques (U+2200-22FF) N'EN SONT
# PAS, et les marqueurs de section DO/DON'T sont fonctionnels : ne pas les
# retirer, ce sont eux qui structurent les regles dans le format Anthropic.
EMOJI = re.compile(r"[\U0001F300-\U0001F9FF]")

REF_FICHIER = re.compile(r"\b(?:scripts?|references?|assets?|src|templates?)/[\w./-]+")
REF_EXTERNE = re.compile(
    r"(https?://|~/|mp:/|<projet>|<skills>|cahier/|resultats/|résultats/|"
    r"\bfigure?s?/|supplementary/|paper/|bdd/|investigate_phylo/|"
    r"\$\{CLAUDE_PLUGIN_ROOT\}/skills/|PredictOps|Predictops|clone|"
    r"pipeline TBannotator|RDscan|File S|quanttb/|QuantTB|ete4\[|etetoolkit)"
)

DESC_MAX = 1024   # au-dela, la description risque d'etre tronquee dans le catalogue
CORPS_MIN = 60

# Deux implementations reelles, complementaires et volontairement distinctes :
# le diagnostic vit dans bio_pathogens, la narration de manuscrit dans bio_redac.
DOUBLONS_INTENTIONNELS = {
    "phylo-history": {
        "bio_pathogens/skills/phylo-history",
        "bio_redac/skills/phylo-history",
    },
}


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
    for plug, plugin_root in marketplace_plugins():
        sd = plugin_root / "skills"
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
    existing_skill_refs = {
        str(path.relative_to(skill_root))
        for _, plugin_root in marketplace_plugins()
        for skill_root in (plugin_root / "skills").iterdir()
        if skill_root.is_dir()
        for path in skill_root.rglob("*")
        if path.is_file()
    }
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
        # references de fichiers : seuls les chemins plausiblement portes par le
        # skill courant sont signalés. Les URLs, racines personnelles et
        # références explicites à d'autres skills canoniques sont contrôlées par
        # leur propre skill plutôt que dupliquées ici.
        manquants: list[str] = []
        fence = False
        for line in corps.splitlines():
            if line.lstrip().startswith(("```", "~~~")):
                fence = not fence
                continue
            if fence:
                continue
            for match in REF_FICHIER.finditer(line):
                f = match.group(0).rstrip(".,);:`\"'")
                if "<" in f or "*" in f:
                    continue
                if REF_EXTERNE.search(line):
                    continue
                if (p / f).exists() or (p / f.split("/", 1)[-1]).exists():
                    continue
                if f in existing_skill_refs:
                    continue
                manquants.append(f)
        manquants = sorted(set(manquants))
        if manquants:
            r["issues"].append("REF_FICHIER_A_VERIFIER:" + ",".join(manquants[:5]))

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

    # Deux copies reelles d'un meme nom divergent en silence, sauf exception
    # documentee dont les deux chemins attendus sont presents.
    par_nom = defaultdict(list)
    for r in rows:
        par_nom[r["dir"]].append(r)
    dbl = {n: v for n, v in par_nom.items() if len(v) > 1}
    if dbl:
        print("\nNoms portes par plusieurs skills reels :")
        for n, v in sorted(dbl.items()):
            paths = {str(Path(x["path"]).relative_to(ROOT)) for x in v}
            if paths == DOUBLONS_INTENTIONNELS.get(n):
                etat = "EXCEPTION_INTENTIONNELLE (diagnostic + narration)"
            else:
                etat = "IDENTIQUES" if len({x["sha"] for x in v}) == 1 else "divergents"
            print(f"  {n:32s} {[x['home'] for x in v]}  {etat}")
        print("  (IDENTIQUES = a symlinker sur le canonique avant divergence)")

    return 1 if signales else 0


if __name__ == "__main__":
    raise SystemExit(main())
