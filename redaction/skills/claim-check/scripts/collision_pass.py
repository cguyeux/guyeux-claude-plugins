#!/usr/bin/env python3
"""collision_pass.py — trouve les nombres qui, répétés avec des référents DIFFÉRENTS, trompent le lecteur.

POURQUOI CETTE PASSE EXISTE (2026-07-31, projet Rv2438A). Un claim-check vérifie les valeurs UNE À UNE
contre leurs sources. Il passe donc à côté, par construction, d'une classe entière de défauts : ceux où
chaque chiffre est EXACT, chaque phrase est CORRECTE, et c'est leur MISE EN VOISINAGE qui induit une
conclusion fausse. Deux cas rencontrés le même jour sur le même manuscrit :

  - « 3 sites polymorphes » (introduction) contre « 121 variants » (résultats) pour la même région :
    deux seuils de fréquence différents, aucun des deux explicité, les deux chiffres vérifiés exacts ;
  - deux « 34 % » à vingt-six lignes d'écart : taux de détection AU-DESSUS d'un seuil, et proportion de
    gènes essentiels EN DESSOUS du même seuil. Coïncidence numérique pure, les deux exacts.

Aucune relecture ne les attrape (chaque phrase se lit bien), aucune vérification numérique non plus
(chaque valeur est juste). Seule une passe qui cherche les DOUBLONS DE VALEUR À RÉFÉRENTS DIFFÉRENTS
les fait apparaître. Elle est mécanique et prend une seconde.

PIÈGE DE CONCEPTION, corrigé à la première utilisation : un motif naïf `(\\d{1,3})\\\\%` capture les
décimales des nombres à virgule, si bien que « 74.6\\% » remonte comme une occurrence de « 6 % » et
noie les vrais doublons sous du bruit. Le motif doit exiger un nombre COMPLET, non précédé d'un chiffre
ni d'un point. Sur le manuscrit de test, la version naïve rendait 10 valeurs répétées dont 6 fausses ;
la version corrigée en rend 5, dont 1 vraie collision — trouvée du premier coup.

CE QUE LA PASSE NE FAIT PAS. Elle ne juge pas : elle regroupe les occurrences d'une même valeur et
affiche leurs contextes, à charge pour le relecteur de dire si le référent est le même. Une valeur
répétée dix fois avec le même sens est normale et souhaitable (c'est la cohérence interne) ; c'est la
répétition à SENS DIFFÉRENT qui est le défaut.

USAGE
    python3 collision_pass.py main.tex              # pourcentages (défaut)
    python3 collision_pass.py main.tex --all        # + entiers et décimaux nus
    python3 collision_pass.py main.tex --window 80  # largeur de contexte
"""
from __future__ import annotations

import argparse
import collections
import pathlib
import re
import sys

# nombre complet suivi de \% : ni précédé d'un chiffre, ni d'un point décimal.
# Le séparateur avant \% n'est pas forcément un espace : la convention de groupe impose une
# espace fine LaTeX (\,) devant \%, ex. « 61\,\% » -- \s* seul ne matche ni le `\` ni la `,` de
# cette séquence, donc la version initiale ratait TOUT pourcentage écrit ainsi (faux négatif
# systématique, découvert le 2026-09-08 sur Rv2520c où c'est la convention unique du manuscrit :
# 0 collision annoncée alors que le script n'avait en réalité rien pu comparer). `~` (espace
# insécable) est le même besoin pour la même raison. Accepter aussi bien l'espace ordinaire que
# ces deux séparateurs LaTeX, dans n'importe quel ordre/répétition raisonnable.
MOTIF_PCT = re.compile(r"(?<![\d.])(\d+(?:[.,]\d+)?)\s*(?:\\,|~)?\s*\\%")
# nombres nus : au moins deux chiffres, pour éviter le bruit des « 1 », « 2 » de comptage.
# La première alternative capture les séparateurs de milliers (2,618 / 2\,618 / 2~618) AVANT
# que la seconde ne s'applique : sans elle « 2,618 » était tronqué en « 618 » (le lookbehind
# laisse passer le fragment qui suit la virgule), ce qui fabrique une fausse collision avec un
# vrai 618 ailleurs et masque le doublon réel. Corrigé le 2026-08-03, même famille de bug que
# celui de numeric_crosscheck.py, trouvé le même jour.
MOTIF_NUM = re.compile(
    r"(?<![\d.\\])(\d{1,3}(?:(?:,|\\,|~)\d{3})+|\d{2,}(?:[.,]\d+)?)(?![\d.])")

# valeurs dont la répétition n'apprend rien : années, seuils conventionnels, numéros de version
IGNORE = {"95", "99", "05", "100", "50", "20", "19", "18", "17", "16", "15", "10"}


def resolve_inputs(path: "pathlib.Path", seen: set | None = None, depth: int = 0) -> str:
    """Concatene le .tex et ses \\input/\\include -- sans ca, un manuscrit decoupe
    en squelette + sections fait manquer tout nombre cite hors du squelette."""
    seen = seen if seen is not None else set()
    path = path.resolve()
    if path in seen or depth > 6 or not path.exists():
        return ""
    seen.add(path)
    text = path.read_text(encoding="utf-8", errors="replace")

    def sub(m: re.Match) -> str:
        target = m.group(2).strip()
        cand = path.parent / target
        for c in (cand, cand.with_suffix(".tex"), pathlib.Path(str(cand) + ".tex")):
            if c.exists() and c.is_file():
                return "\n" + resolve_inputs(c, seen, depth + 1) + "\n"
        return ""

    return re.sub(r"\\(input|include)\{([^}]*)\}", sub, text)


def contextes(texte: str, positions: list[int], largeur: int) -> list[str]:
    out = []
    for p in positions:
        avant = texte[max(0, p - largeur):p]
        out.append(re.sub(r"\s+", " ", avant).strip()[-largeur:])
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("fichier")
    ap.add_argument("--all", action="store_true", help="inclure les nombres nus, pas que les %%")
    ap.add_argument("--window", type=int, default=60, help="largeur du contexte affiché")
    ap.add_argument("--min-occurrences", type=int, default=2)
    a = ap.parse_args()

    texte = resolve_inputs(pathlib.Path(a.fichier))
    motifs = [("pourcentage", MOTIF_PCT)] + ([("nombre", MOTIF_NUM)] if a.all else [])

    total_suspects = 0
    for nom, motif in motifs:
        occ: dict[str, list[int]] = collections.defaultdict(list)
        for m in motif.finditer(texte):
            occ[m.group(1)].append(m.start())
        repetes = {k: v for k, v in occ.items()
                   if len(v) >= a.min_occurrences and k not in IGNORE}
        print(f"\n=== {nom}s : {len(occ)} valeurs distinctes, {len(repetes)} répétées ===")
        if not repetes:
            print("  (aucune)")
            continue
        for val, pos in sorted(repetes.items(), key=lambda x: -len(x[1])):
            print(f"\n  {val} × {len(pos)}")
            for c in sorted(set(contextes(texte, pos, a.window))):
                print(f"      …{c}")
            total_suspects += 1

    print(f"\n{total_suspects} valeur(s) à examiner. Pour chacune, une seule question : "
          f"le RÉFÉRENT est-il le même partout ?")
    print("Si non, reformuler l'une des occurrences (effectifs bruts, « one in three »…) et ajouter "
          "une clause qui distingue les deux quantités.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
