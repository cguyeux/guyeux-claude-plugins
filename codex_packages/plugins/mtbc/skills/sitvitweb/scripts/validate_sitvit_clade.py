#!/usr/bin/env python3
"""Valider un label `Clade` de SITVIT contre une VÉRITÉ SNP — validation NON CIRCULAIRE.

================================================================================================
LE PROBLÈME
================================================================================================
Le champ `Clade` de SITVIT (AFRI, CAM, LAM, T, H…) est déduit du **SPOLIGOTYPE SEUL**. Or les
familles définies par des **absences de spacers** sont des **attracteurs de convergence** :
toute souche qui perd les bons spacers y tombe. Mesuré : **~12 % des isolats étiquetés `AFRI`
ne sont PAS du *M. africanum*** (faux positif documenté : SIT 1476, le prétendu « foyer péruvien
autochtone » de Lima).

⛔ **On ne peut donc PAS valider SITVIT avec SITVIT** : ce serait circulaire.

================================================================================================
★ LA SOURCE DE VÉRITÉ NON CIRCULAIRE
================================================================================================
    `~/Documents/codes/MTBC/Spolgraph/SITVIT23882_PHELAN_SNPBASEDLIN_SORTED.xlsx`

**97 389 souches SÉQUENCÉES**, dont **34 111 portent une `SNP-based lineage`** — c'est-à-dire une
lignée déduite des **SNP**, donc **INDÉPENDANTE du spoligotype**.
=> On peut demander : « les souches portant tel SIT, à quelle lignée SNP appartiennent-elles
   RÉELLEMENT ? » C'est la validation croisée qui manquait.

Résultat de référence (2026-07-13) :
    SIT   61  (Clade « Cameroon ») n=174 -> **lineage4.6.2.2 à 98,9 %**   ✅ le label est BON
    SIT  181  (Clade « AFRI_1 »)   n= 42 -> **lineage6 à 100 %**          ✅
    SIT  331  (Clade « AFRI_2 »)   n= 44 -> **lineage5 à 100 %**          ✅
    SIT  101 / 326                        -> lineage5 / lineage6 à 100 %  ✅
    SIT 1476  (Clade « AFRI_2 »)   n=  2 -> **lineage4.3.2 à 100 %**      ⛔ **FAUX** — c'est du L4
              (= le « foyer péruvien autochtone de M. africanum » : il n'existe pas)

================================================================================================
⚠⚠ DEUX PIÈGES DE LECTURE, TOUS DEUX RENCONTRÉS
================================================================================================
1. **La colonne `SIT` est en TYPES MIXTES** : `'939'` (chaîne) et `53` (entier) cohabitent dans la
   même colonne (dtype `object`). Un `d[d.SIT == 61]` renvoie **0 ligne** sans erreur.
   ⇒ **NORMALISER en chaîne d'entier** avant tout filtrage.
2. **La colonne `SpoligotypeOctal` est en `float64`** ⇒ **les zéros de tête sont PERDUS**
   (`060000777777671` → `6.0000777777671e+13`). ⇒ `zfill(15)` obligatoire des DEUX côtés.
   (Même piège que dans `SIT.xls` — cf. SKILL.md.)

USAGE
    python3 validate_sitvit_clade.py                 # valide les SIT de référence
    python3 validate_sitvit_clade.py 61 181 1476     # valide des SIT précis
    python3 validate_sitvit_clade.py --clade AFRI    # valide TOUS les SIT d'un clade SITVIT
"""
import os
import sys

PHELAN = os.path.expanduser(
    "~/Documents/codes/MTBC/Spolgraph/SITVIT23882_PHELAN_SNPBASEDLIN_SORTED.xlsx")
SITVIT = os.path.expanduser("~/Documents/codes/MTBC/TB-tools/data/SIT.xls")

SIT_REFERENCE = {
    "61": "Clade SITVIT « Cameroon » -> attendu L4.6.2",
    "181": "Clade SITVIT « AFRI_1 »  -> attendu L6",
    "331": "Clade SITVIT « AFRI_2 »  -> attendu L5",
    "101": "Clade SITVIT « AFRI_2 »  -> attendu L5",
    "326": "Clade SITVIT « AFRI_1 »  -> attendu L6",
    "1476": "Clade SITVIT « AFRI_2 » -> FAUX POSITIF connu (attendu : L4)",
}


def norm_sit(x):
    """⚠ colonne SIT en TYPES MIXTES ('939' et 53) -> normaliser en chaîne d'entier."""
    import pandas as pd
    if pd.isna(x):
        return None
    t = str(x).strip()
    try:
        return str(int(float(t)))
    except ValueError:
        return None


def load_truth():
    import pandas as pd
    d = pd.read_excel(PHELAN)
    d["SIT"] = d["SIT"].apply(norm_sit)
    # ⚠ octal en float64 -> zéros de tête perdus
    d["oct"] = d["SpoligotypeOctal"].apply(
        lambda x: str(int(x)).zfill(15) if pd.notna(x) else None)
    d = d[d["SNP-based lineage"].notna()]
    return d


def report(truth, sits, labels=None):
    print("%-7s %7s  %-24s %8s   %s" % ("SIT", "n séq.", "lignée SNP majoritaire", "part", "contexte"))
    print("-" * 96)
    for sit in sits:
        ss = truth[truth["SIT"] == sit]
        ctx = (labels or {}).get(sit, "")
        if not len(ss):
            print("%-7s %7s  %-24s %8s   %s" % (sit, "0", "(aucune souche séquencée)", "-", ctx))
            continue
        vc = ss["SNP-based lineage"].value_counts()
        top, pct = vc.index[0], 100 * vc.iloc[0] / len(ss)
        flag = "" if pct >= 90 else "  ⚠ HÉTÉROGÈNE"
        print("%-7s %7d  %-24s %7.1f%%%s   %s" % (sit, len(ss), top, pct, flag, ctx))


def main():
    args = sys.argv[1:]
    truth = load_truth()
    print("Vérité SNP (Phelan) : %d souches séquencées avec une `SNP-based lineage`" % len(truth))
    print("=> INDÉPENDANTE du spoligotype : c'est ce qui rend la validation NON CIRCULAIRE.\n")

    if args and args[0] == "--clade":
        import pandas as pd
        clade = args[1]
        sv = pd.read_excel(SITVIT)
        sv["SIT"] = sv["SIT"].apply(norm_sit)
        sub = sv[sv["Clade"].astype(str).str.contains(clade, case=False, na=False)]
        sits = [s for s in sub["SIT"].dropna().value_counts().index[:25]]
        print("Clade SITVIT « %s » : %d isolats, %d SIT distincts. Les 25 plus fréquents :\n"
              % (clade, len(sub), sub["SIT"].nunique()))
        report(truth, sits)
        return

    sits = args if args else list(SIT_REFERENCE)
    report(truth, sits, SIT_REFERENCE)
    print("\n>>> LECTURE : si la lignée SNP majoritaire ne correspond PAS au clade annoncé par SITVIT,")
    print("    le label est FAUX (convergence de spoligotype). Ne JAMAIS publier sur le seul label.")
    print("    Une part < 90 % signale un SIT hétérogène : à écarter ou à traiter avec prudence.")


if __name__ == "__main__":
    main()
