#!/usr/bin/env python3
r"""Bascule un deck monolithique en variantes partageant une source unique.

    deck.tex  ->  preambule.tex + corps.tex
                  deck.tex        (\gxlongtrue,  variante de reference)
                  deck_court.tex  (\gxlongfalse, la variante demandee)

Pourquoi ce script plutot qu'un copier-coller. Une variante fabriquee en
copiant le repertoire diverge des la premiere correction de chiffre, et rien
ne le signale ; une variante fabriquee par \\includeonlyframes perd ses pages
de section et affiche une numerotation calee sur le deck complet (mesure le
2026-09-10 : trois pages numerotees << 2/5 >> et << 4/5 >>). Le seul mecanisme
qui tienne est un maitre par variante au-dessus de fragments partages, et sa
mise en place est mecanique : autant ne pas la faire a la main.

La bascule est une REFACTORISATION : le PDF de la variante de reference doit
avoir exactement le meme nombre de pages qu'avant. Le script le verifie et
refuse de laisser le chantier en l'etat si ce n'est pas le cas.

Usage :
    deck_fork.py deck.tex --nom court            # cree deck_court.tex
    deck_fork.py deck.tex --nom en --booleen gxfr
    deck_fork.py deck.tex --nom court --sec      # a sec : dit ce qu'il ferait
"""
import argparse
import os
import re
import shutil
import subprocess
import sys


def pages_pdf(pdf: str) -> int:
    if not os.path.exists(pdf):
        return 0
    out = subprocess.run(['pdfinfo', pdf], capture_output=True, text=True).stdout
    m = re.search(r'^Pages:\s+(\d+)', out, re.M)
    return int(m.group(1)) if m else 0


def compile_deux_fois(tex: str) -> int:
    d, f = os.path.dirname(os.path.abspath(tex)) or '.', os.path.basename(tex)
    for _ in range(2):
        subprocess.run(['pdflatex', '-interaction=nonstopmode', f],
                       cwd=d, capture_output=True)
    return pages_pdf(os.path.splitext(os.path.abspath(tex))[0] + '.pdf')


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("deck", help="le deck monolithique a fragmenter")
    ap.add_argument("--nom", required=True,
                    help="suffixe de la variante : court, long, en, comite...")
    ap.add_argument("--booleen", default="gxlong",
                    help="nom du booleen LaTeX (defaut : gxlong)")
    ap.add_argument("--sec", action="store_true",
                    help="ne rien ecrire, dire ce qui serait fait")
    a = ap.parse_args()

    deck = os.path.abspath(a.deck)
    rep = os.path.dirname(deck)
    src = open(deck, encoding='utf-8', errors='replace').read()

    if re.search(r'\\input\s*\{\s*preambule\s*\}', src):
        print("Ce deck est deja fragmente. Pour ajouter une variante, copier "
              "son maitre et inverser le booleen ; ne pas relancer la bascule.")
        return 1
    m_deb = re.search(r'\\begin\{document\}', src)
    m_fin = re.search(r'\\end\{document\}', src)
    if not (m_deb and m_fin):
        print("FAIL : \\begin{document} ou \\end{document} introuvable.")
        return 1
    m_cls = re.search(r'\\documentclass[^\n]*\n', src)
    if not m_cls:
        print("FAIL : \\documentclass introuvable.")
        return 1

    classe = m_cls.group(0)
    preambule = src[m_cls.end():m_deb.start()].strip() + '\n'
    corps = src[m_deb.end():m_fin.start()].strip() + '\n'
    bo = a.booleen
    variante = os.path.join(rep, f"deck_{a.nom}.tex")

    entete = (f"% Fragment partage par toutes les variantes de cet expose.\n"
              f"% Un chiffre, une source : ce qui est mesure ou cite vit ICI,\n"
              f"% jamais recopie dans un maitre.\n")
    maitre = (f"{classe}\\newif\\if{bo} \\{bo}true"
              f"          % variante de reference\n"
              f"\\input{{preambule}}\n\n\\begin{{document}}\n\\input{{corps}}\n"
              f"\\end{{document}}\n")
    maitre_var = maitre.replace(f"\\{bo}true          % variante de reference",
                                f"\\{bo}false         % variante « {a.nom} »")

    print(f"Bascule de {os.path.basename(deck)} :")
    print(f"  preambule.tex   {len(preambule.splitlines()):>4} lignes")
    print(f"  corps.tex       {len(corps.splitlines()):>4} lignes")
    print(f"  {os.path.basename(deck):<15} maitre, \\{bo}true")
    print(f"  deck_{a.nom}.tex".ljust(17) + f" maitre, \\{bo}false")
    print(f"\nDans corps.tex, trois formes :")
    print(f"  (rien)                  la slide est dans toutes les variantes")
    print(f"  \\if{bo} … \\fi".ljust(24) + f"  reference seulement")
    print(f"  \\if{bo}\\else … \\fi".ljust(24) + f"  variante « {a.nom} » seulement")
    if a.sec:
        print("\nÀ sec : rien n'a été écrit.")
        return 0

    avant = pages_pdf(os.path.splitext(deck)[0] + '.pdf') or compile_deux_fois(deck)
    shutil.copy2(deck, deck + '.orig')
    for nom, contenu in (("preambule.tex", preambule),
                         ("corps.tex", entete + corps)):
        chemin = os.path.join(rep, nom)
        if os.path.exists(chemin):
            print(f"FAIL : {nom} existe deja, rien n'a ete ecrit.")
            return 1
        open(chemin, 'w', encoding='utf-8').write(contenu)
    open(deck, 'w', encoding='utf-8').write(maitre)
    open(variante, 'w', encoding='utf-8').write(maitre_var)

    apres = compile_deux_fois(deck)
    pages_var = compile_deux_fois(variante)
    print(f"\nContrôle de la refactorisation : {avant} page(s) avant, {apres} après.")
    if avant and apres != avant:
        print("FAIL : le PDF de référence a changé de longueur. La bascule a cassé "
              f"quelque chose. L'original est dans {os.path.basename(deck)}.orig ; "
              "le restaurer et regarder le log avant toute autre chose.")
        return 1
    print(f"La variante « {a.nom} » compile à {pages_var} page(s) : identique tant "
          f"qu'aucun \\if{bo} n'a été posé dans corps.tex. C'est le travail qui "
          f"reste, et il se fait en rejouant le budget, pas en supprimant des slides.")
    print(f"\nContrôler CHAQUE variante avec SA durée :")
    print(f"  slide_audit.py {os.path.basename(deck)} --duree <n> --pixels")
    print(f"  slide_audit.py deck_{a.nom}.tex --duree <m> --pixels")
    print(f"Puis inscrire la variante au tableau de plan_presentation.md.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
