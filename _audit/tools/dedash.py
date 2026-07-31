#!/usr/bin/env python3
"""Retire les tirets CADRATIN (—) de la prose des SKILL.md.

Usage :
    python3 _audit/tools/dedash.py --dry-run     # diff sans rien ecrire
    python3 _audit/tools/dedash.py               # applique
    python3 _audit/tools/dedash.py fichier.md    # sur un fichier precis

=========================================================================
AVERTISSEMENT : LE DEMI-CADRATIN (–) NE DOIT JAMAIS ETRE TOUCHE
=========================================================================
Ce script existe sous cette forme parce qu'une premiere version, qui traitait
cadratin ET demi-cadratin, a CORROMPU DES FAITS SCIENTIFIQUES lors d'un test :

    « 40 000–70 000 BP »          ->  « 40 000, 70 000 BP »   (deux valeurs !)
    « mycocerosates C29–C32 »     ->  « C29, C32 »
    « host–pathogen co-dating »   ->  « host, pathogen co-dating »

Le demi-cadratin n'est PAS un marqueur de texte genere par IA : c'est la
typographie correcte d'un intervalle numerique et d'un compose. Seul le
cadratin (—) est vise, et meme lui est conserve entre deux chiffres.

Autres garde-fous, tous appris a l'usage :
  - blocs de code proteges (arbres ASCII et sorties d'exemple gardent leurs
    cadratins, ils y sont legitimes) ;
  - code inline `x` et cibles de liens ](...) proteges par jetons ;
  - dans un titre, le cadratin separe titre et sous-titre -> « : » ;
  - ailleurs -> « , », sauf devant une majuscule si la ligne n'a pas deja un
    « : » (sinon on empile « A : B : C ») ;
  - l'espace fine n'est retiree QUE devant la virgule : en francais « ; »,
    « : » et « ? » conservent leur espace insecable.

TOUJOURS lancer --dry-run et lire le diff avant d'appliquer. TOUJOURS
sauvegarder d'abord : tar czf /tmp/backup.tgz */skills/*/SKILL.md
"""
from __future__ import annotations

import argparse
import difflib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# Meme perimetre que _audit/tools/audit_skills.py, maboss compris : deux outils
# qui divergent sur leur perimetre produisent des bilans contradictoires.
PLUGINS = ["bio_pathogens", "bio_population_genetics", "redac", "bio_redac",
           "ia", "multimedia", "ops", "web", "maboss"]

EM = "—"
GARDE = "\x01"   # marque un cadratin d'intervalle numerique, a restaurer


def _proteger(line: str):
    """Remplace code inline et cibles de liens par des jetons."""
    toks: list[str] = []

    def sub(m):
        toks.append(m.group(0))
        return f"\x00{len(toks) - 1}\x00"

    line = re.sub(r"`[^`]*`", sub, line)
    line = re.sub(r"\]\([^)]*\)", sub, line)
    return line, toks


def _restaurer(line: str, toks: list[str]) -> str:
    return re.sub(r"\x00(\d+)\x00", lambda m: toks[int(m.group(1))], line)


def corriger_prose(s: str) -> str:
    # 1. intervalle numerique chiffre—chiffre : sanctuarise
    s = re.sub(rf"(?<=\d)\s?{EM}\s?(?=\d)", GARDE, s)
    # 2. titre : le cadratin introduit un sous-titre
    if s.lstrip().startswith("#"):
        s = re.sub(rf"\s+{EM}\s+", " : ", s, count=1)
    # 3. incise devant une majuscule, si la ligne n'a pas deja un deux-points
    elif " : " not in s.replace(GARDE, ""):
        s = re.sub(rf"\s+{EM}\s+(?=[A-ZÀÂÉÈÊÎÔÙÛÇ])", " : ", s, count=1)
    # 4. incise ordinaire
    s = re.sub(rf"\s+{EM}\s+", ", ", s)
    s = re.sub(rf"(?<=\w){EM}(?=\w)", ", ", s)
    s = re.sub(rf"^(\s*(?:[-*+]|\d+\.)\s+){EM}\s*", r"\1", s)
    s = s.replace(EM, ",")
    # 5. nettoyage, puis restauration des intervalles
    s = s.replace(GARDE, EM)
    s = re.sub(r",\s*,", ",", s)
    s = re.sub(r"[ \t]+,", ",", s)
    return s


def traiter(path: Path, dry_run: bool = False):
    """Renvoie (n_lignes_modifiees, diff_unifie)."""
    avant = path.read_text(encoding="utf-8")
    out, fence, n = [], False, 0
    for line in avant.splitlines(keepends=True):
        if line.lstrip().startswith(("```", "~~~")):
            fence = not fence
            out.append(line)
            continue
        if fence or EM not in line:
            out.append(line)
            continue
        body, nl = (line[:-1], "\n") if line.endswith("\n") else (line, "")
        prot, toks = _proteger(body)
        if EM not in prot:          # cadratin uniquement dans du code inline
            out.append(line)
            continue
        fixed = _restaurer(corriger_prose(prot), toks)
        if fixed != body:
            n += 1
        out.append(fixed + nl)

    apres = "".join(out)
    diff = ""
    if n:
        diff = "".join(difflib.unified_diff(
            avant.splitlines(keepends=True), apres.splitlines(keepends=True),
            fromfile=str(path), tofile=str(path) + " (corrige)", n=0))
        if not dry_run:
            path.write_text(apres, encoding="utf-8")
    return n, diff


def cibles():
    vus = set()
    for plug in PLUGINS:
        sd = ROOT / plug / "skills"
        if not sd.is_dir():
            continue
        for e in sorted(sd.iterdir()):
            if not e.is_dir():
                continue
            sk = e.resolve() / "SKILL.md"
            if sk.exists() and str(sk) not in vus:
                vus.add(str(sk))
                yield sk


def compter_prose(path: Path) -> int:
    fence, n = False, 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith(("```", "~~~")):
            fence = not fence
            continue
        if fence or EM not in line:
            continue
        n += re.sub(r"`[^`]*`", "", line).count(EM)
    return n


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("fichiers", nargs="*", type=Path,
                    help="fichiers a traiter (defaut : tous les SKILL.md canoniques)")
    ap.add_argument("--dry-run", action="store_true", help="affiche le diff sans ecrire")
    args = ap.parse_args()

    liste = args.fichiers or list(cibles())
    total = fichiers = 0
    for f in liste:
        n, diff = traiter(f, dry_run=args.dry_run)
        if n:
            fichiers += 1
            total += n
            if args.dry_run:
                print(diff)
    verbe = "seraient modifiees" if args.dry_run else "modifiees"
    print(f"{total} lignes {verbe} dans {fichiers} fichiers")

    if not args.dry_run:
        reste = sum(compter_prose(f) for f in liste)
        print(f"controle : {reste} cadratins restants en prose (doit valoir 0)")
        return 1 if reste else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
