#!/usr/bin/env python3
"""audit_connaissances_2026_09.py — auditer les ENONCES, pas la structure.

Objet     : la taxonomie Bovis a change trois fois (trichotomie du 2026-06-22, decalage de niveau
            du 2026-07-20, cycles de validation d'aout dans `lineage_navigator`), et chaque
            changement a laisse derriere lui des affirmations ECRITES qui nomment des clades. Le
            lot 1 du 2026-09-02 (`audit_taxonomie_2026_09.py`) a audite la STRUCTURE : registre
            autoritaire contre disque. Celui-ci audite les ARTEFACTS DE CONNAISSANCE : manuscrit,
            etat des decouvertes, pistes, cahier, CLAUDE.md, base de connaissances inter-projets,
            memoire native, skills, marqueurs. Question posee a chaque citation : le clade nomme
            ici existe-t-il encore, et l'effectif annonce a cote est-il encore le bon ?

            LECTURE SEULE INTEGRALE. N'ecrit que dans son propre repertoire de resultats.

            TROIS VERDICTS PAR LABEL CITE :
              EXISTE          repertoire present dans bdd/actuelle (le label designe quelque chose) ;
              NOEUD_INTERNE   absent du disque mais present au registre autoritaire, ou prefixe
                              strict d'un label existant : le noeud existe, il n'est pas materialise ;
              INCONNU         ni l'un ni l'autre : la citation est SANS REFERENT.
            Un INCONNU n'est pas forcement une erreur (il peut etre cite comme perime, avec sa
            correction a cote), d'ou la colonne `contexte_perime` qui detecte les marqueurs de
            peremption deja poses dans le texte. Ce qui doit alerter, c'est un INCONNU cite SANS
            marqueur de peremption, surtout dans le manuscrit et l'etat des decouvertes.

Entrées   : bdd/actuelle (labels materialises), lineage_navigator/résultats/bovis_validation/
            registre_noeuds.tsv (autorite), et la liste CIBLES ci-dessous.
Sorties   : résultats/audit_connaissances_2026-09/{CITATIONS.tsv, EFFECTIFS.tsv, CHIFFRES.tsv,
            MESURES.json, SYNTHESE.md}
Réutilisable : oui, et c'est le point — toute lignee dont la nomenclature a bouge a le meme
            probleme. Changer RACINE et CIBLES suffit. Candidat skill (`registres-sans-referent`).
Projet    : Bovis_full (audit demande par CG le 2026-09-12)
Date      : 2026-09-12
"""
from __future__ import annotations

import collections
import csv
import json
import os
import re
from pathlib import Path

# === A ADAPTER AU DEPOT (skill `registres-sans-referent`) ===
# Ces chemins sont derives de l'emplacement du script, ce qui est correct quand il vit dans le
# `analyses/` d'un projet et faux quand il est appele depuis le skill. Fixer le projet cible par
# la variable d'environnement RSR_PROJET, ou editer PROJ ci-dessous.
#   RSR_PROJET=/chemin/vers/le/projet python audit_enonces.py
HERE = Path(__file__).resolve().parent
PROJ = Path(os.environ["RSR_PROJET"]).resolve() if os.environ.get("RSR_PROJET") else HERE.parent
MTBC = PROJ.parent
BDD = MTBC / "bdd" / "actuelle"
REGISTRE = MTBC / "lineage_navigator" / "résultats" / "bovis_validation" / "registre_noeuds.tsv"
HOME = Path.home()
OUT = PROJ / "résultats" / "audit_connaissances_2026-09"

RACINE = "Bovis"
RX_LABEL = re.compile(r"\bBovis(?:[._][A-Za-z0-9]+)*\b")
RX_EFF = re.compile(r"(\d[\d   ]{0,9}\d|\d)\s*souches?\b")
# une notation generique (X, x, n, pairSRR, RDs, tree) n'est pas un label : la classer a part
RX_NOTATION = re.compile(r"[._](?:[Xxni]|\d*[Xx]\d*|pairSRR\w*|RDs?|tree|La\d)$|[._][Xx][._]|"
                         r"[._](?:crown|racine|BCG)\b")
RX_TAUX = re.compile(r"([01][.,]\d{2,4})\s*(?:SNP|snp)?[ /]*(?:SNP/génome/an|SNP par génome|snp/génome/an)?")
# marqueurs indiquant que l'auteur SAIT que le nom est perime
# CORRIGE le 2026-09-12 (P16.8, defaut mesure en P16.4) : ce motif etait sensible a la CASSE et
# ne voyait donc pas les bandeaux ecrits a la main, qui crient en majuscules (« TOUT ce qui suit
# est HISTORIQUE », « N'EXISTE PLUS »). Le skill `mtbc-lineages` et `pistes/P4.md`, correctement
# marques, etaient comptes comme nus : le chiffre rendu etait une borne HAUTE de la dette.
RX_PERIME = re.compile(r"périmé|perime|obsolèt|obsolet|supersed|ex-|ancien|"
                       r"historique|dérivé le|a dérivé|n'existe plus|absent|sans référent|"
                       r"avant la trichotomie|avant le décalage|renommé|renomme|"
                       r"caduque|réfuté|refute|ne désigne plus|ne designe plus", re.IGNORECASE)

# CORRIGE le 2026-09-12 (P16.8, defaut mesure en P16.4) : RX_LABEL capte des NON-labels, et le
# critere MORPHOLOGIQUE qui vient a l'esprit est faux — « deux chiffres finaux = exemple » jetait
# `Bovis.12`, vrai label de l'ancienne racine, qui allait jusqu'a `Bovis.53`. Le critere qui
# marche est CONTEXTUEL : n'ecarter un tel label que si la phrase parle d'un piege de nommage.
RX_CONTEXTE_EXEMPLE = re.compile(r"fnmatch|glob|capterait|piège de nommage|startswith|"
                                 r"ne matche pas|NE capture PAS", re.IGNORECASE)
# Composites d'un AUTRE systeme de nommage (suffixe Loiseau Af1/Af2, La4, proto, crown) : ils
# n'ont jamais designe un repertoire, les compter en dette est un faux positif.
RX_COMPOSITE = re.compile(r"_(?:Af\d|proto|La\d|crown)\b")

CIBLES = [
    ("manuscrit", PROJ / "article" / "main.tex"),
    ("etat", PROJ / "etat_des_decouvertes.md"),
    ("claude_projet", PROJ / "CLAUDE.md"),
    ("cahier", PROJ / "cahier_de_labo.md"),
    ("claude_depot", MTBC / "CLAUDE.md"),
    ("readme_depot", MTBC / "README.md"),
    ("pistes_depot", MTBC / "pistes.md"),
    ("kb_tuberculosis", HOME / ".agents" / "knowledge" / "tuberculosis.md"),
    ("sources_of_truth", MTBC / "global_supplementary" / "barcoding_v2" / "SOURCES_OF_TRUTH.md"),
]


def cibles_completes() -> list[tuple[str, Path]]:
    c = list(CIBLES)
    for p in sorted((PROJ / "pistes").glob("P*.md")):
        if p.suffix == ".md" and ".bak" not in p.name:
            c.append((f"piste_{p.stem}", p))
    mem = HOME / ".claude" / "projects" / "-home-christophe-docs-codes" / "memory"
    for p in sorted(mem.glob("*.md")):
        c.append((f"memoire_{p.stem}", p))
    for base in (HOME / "docs" / "codes" / "claude_plugins",):
        for p in sorted(base.glob("*/skills/mtbc-lineages/**/*.md")):
            c.append((f"skill_{p.parent.name}_{p.stem}", p))
    for p in sorted((PROJ / "article").glob("*.tex")):
        if p.name != "main.tex":
            c.append((f"manuscrit_{p.stem}", p))
    return [(n, p) for n, p in c if p.is_file()]


def autorite() -> tuple[dict[str, int], set[str]]:
    """(labels materialises -> effectif direct+cumule, labels du registre autoritaire)."""
    disque: dict[str, int] = {}
    if BDD.is_dir():
        for d in BDD.iterdir():
            if d.is_dir() and (d.name == RACINE or d.name.startswith(RACINE + ".")):
                disque[d.name] = sum(1 for s in d.iterdir() if s.is_dir())
    reg: set[str] = set()
    if REGISTRE.is_file():
        with REGISTRE.open() as f:
            for r in csv.DictReader(f, delimiter="\t"):
                reg.add(r["node"])
    return disque, reg


def cumul(disque: dict[str, int]) -> dict[str, int]:
    """label -> nombre de souches dans tout son sous-arbre materialise."""
    out: dict[str, int] = collections.defaultdict(int)
    for lab, n in disque.items():
        p = lab.split(".")
        for k in range(1, len(p) + 1):
            out[".".join(p[:k])] += n
    return dict(out)


# TABLES a colonne de lignee : (nom, chemin, colonne identifiant, colonne label). Un registre en
# PROSE se controle par l'existence du label ; une TABLE ne le peut pas, parce que son defaut le
# plus dangereux est le label VIVANT mais FAUX — il pointe un clade reel, donc aucun controle
# d'existence ne le voit, et une jointure rattache silencieusement la souche au mauvais clade.
# Mesure fondatrice, P16.6 du 2026-09-12 : sur 13 414 lignes de la table maitre par souche, 113
# portaient le placement reel, 12 471 un label mort et 480 un label vivant et faux.
TABLES_LIGNEE = [
    ("master_par_souche", MTBC / "Bovis_emergence" / "data" / "bovis_master_per_strain.tsv",
     "strain", "lineage_bdd"),
]


def placement_reel() -> dict[str, str]:
    """souche -> clade qui la contient REELLEMENT sous bdd/actuelle."""
    out: dict[str, str] = {}
    if not BDD.is_dir():
        return out
    for c in BDD.iterdir():
        if not c.is_dir() or not (c.name == RACINE or c.name.startswith(RACINE + ".")):
            continue
        for s in c.iterdir():
            if s.is_dir():
                out[s.name] = c.name
    return out


def audit_tables(disque: dict, reg: set, prefixes: set) -> dict:
    """Pour chaque table declaree : le label annonce est-il celui du disque ?"""
    place = placement_reel()
    res = {}
    for nom, chemin, col_id, col_lab in TABLES_LIGNEE:
        if not chemin.is_file():
            res[nom] = {"etat": "ABSENT", "chemin": str(chemin)}
            continue
        exact = mort = vivant_faux = hors_disque = total = 0
        exemples = []
        with chemin.open(encoding="utf-8") as f:
            for r in csv.DictReader(f, delimiter="\t"):
                lab = (r.get(col_lab) or "").strip()
                sid = (r.get(col_id) or "").strip()
                if not lab.startswith(RACINE):
                    continue
                total += 1
                vrai = place.get(sid)
                if vrai is None:
                    hors_disque += 1
                elif vrai == lab:
                    exact += 1
                elif lab in disque:
                    vivant_faux += 1
                    if len(exemples) < 5:
                        exemples.append({"souche": sid, "annonce": lab, "reel": vrai})
                else:
                    mort += 1
        res[nom] = {"etat": "MESURE", "chemin": str(chemin), "n_lignes": total,
                    "placement_exact": exact, "label_mort": mort,
                    "label_VIVANT_mais_FAUX": vivant_faux, "souche_hors_disque": hors_disque,
                    "pct_exact": round(100 * exact / total, 1) if total else None,
                    "exemples_vivant_faux": exemples}
    return res


# Marqueurs d'une REFUTATION FORTE : la ligne ne dit pas « attention », elle dit « c'est faux ».
RX_REFUTATION = re.compile(r"⛔|RÉFUTÉ|REFUTE|CADUQUE|NE TIENT PLUS|ne tient plus|"
                           r"est FAUX|sont FAUX|TOMBE|invalidée|invalide depuis", re.IGNORECASE)
# Jetons qu'une refutation emporte avec elle et qu'on peut rechercher ailleurs sans bruit : une
# ANNEE HISTORIQUE (1500-1999 : ni une date de seance, ni un effectif) et un TAUX decimal. Un
# effectif brut serait ingerable, trop de nombres se ressemblent.
RX_JETON_ANNEE = re.compile(r"\b(1[5-9]\d{2})\b")
RX_JETON_TAUX = re.compile(r"\b([01][.,]\d{3,4})\b")
# Au-dela de ce nombre de fichiers, un jeton est un mot commun du projet et non la trace d'un
# enonce : le signaler noierait le vrai signal.
MAX_FICHIERS_PAR_JETON = 12
# Une phrase de correction porte DEUX jetons, l'ancien et le nouveau : « le taux passe de 0,2862 a
# 0,446 », « ~~0,2862~~ -> 0,2448 ». Prendre les deux pour refutes fait signaler le REMPLACANT, ce
# qui est le contraire du but. Le jeton qui suit un marqueur de remplacement est donc retire.
RX_REMPLACANT = re.compile(r"(?:\ba\b|à|->|→|vers|devient|remplac\w*|passe a|passe à)[^\d]{0,12}$")
# Fichiers qui PILOTENT le travail : une survivance y est grave, ailleurs c'est du recit.
FICHIERS_PILOTES = {"claude_projet", "claude_depot", "etat", "manuscrit"}
# Une ligne qui porte la CORRECTION cite forcement la valeur tombee (« 699 et non 722 ») : c'est
# le contraire d'une survivance, et la compter ferait signaler le correctif lui-meme.
RX_CORRECTION = re.compile(r"et non\b|au lieu de\b|plutôt que\b|contre\b|remplac|corrigé[e]? à|"
                           r"~~|imposerait|exigerait|hors d'atteinte|incompatible", re.IGNORECASE)
# Un separateur de milliers fabrique de faux jetons : « 70 722 » contient « 722 » comme mot
# entier. Le jeton ne compte que s'il n'est pas precede d'un chiffre et d'une espace.
RX_MILLIERS = re.compile(r"\d[\u202f\u00a0 ]$")


REGISTRE_REFUTATIONS = PROJ / "refutations.tsv"


def audit_refutations_declarees(cibles: list[tuple[str, Path]]) -> dict:
    """Les enonces DECLARES refutes survivent-ils dans un fichier qui pilote le travail ?

    Le mode heuristique ci-dessous (`audit_refutations`) cherchait a DEVINER quels chiffres une
    ligne de refutation emporte avec elle. Mesure du 2026-09-12 : 74 jetons signales sur 86, dont
    la quasi-totalite legitimes, parce qu'une phrase de correction porte l'ancien ET le nouveau
    (« le taux passe de 0,2862 a 0,446 ») et qu'un meme nombre a des usages sans rapport (la
    souche « Pasteur 1908 » n'est pas la calibration « 1908 »). Deviner un enonce refute dans de
    la prose est un probleme mal pose ; le DECLARER coute une ligne au moment ou on le refute et
    rend le controle exact. D'ou `refutations.tsv`, tenu a la main, et ce controle-ci, qui est
    celui qui compte. Le mode heuristique reste disponible en DECOUVERTE, hors indicateur.
    """
    if not REGISTRE_REFUTATIONS.is_file():
        return {"etat": "REGISTRE_ABSENT", "chemin": str(REGISTRE_REFUTATIONS)}
    textes = {}
    for nom, p in cibles:
        try:
            textes[nom] = p.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
    survivances, n = [], 0
    with REGISTRE_REFUTATIONS.open(encoding="utf-8") as f:
        for d in csv.DictReader(f, delimiter="\t"):
            n += 1
            jeton = d["jeton"].strip()
            legit = [x.strip() for x in (d.get("usages_legitimes") or "").split(";")
                     if x.strip() and x.strip() != "NA"]
            rx = re.compile(r"\b" + re.escape(jeton).replace(r"\.", "[.,]") + r"\b")
            occ = []
            for nom, lignes in textes.items():
                for i, ligne in enumerate(lignes, 1):
                    m = rx.search(ligne)
                    if not m:
                        continue
                    if RX_MILLIERS.search(ligne[:m.start()]):
                        continue
                    if (RX_REFUTATION.search(ligne) or RX_PERIME.search(ligne)
                            or RX_CORRECTION.search(ligne)):
                        continue
                    if any(l.lower() in ligne.lower() for l in legit):
                        continue
                    occ.append({"fichier": nom, "ligne": i, "extrait": ligne.strip()[:170]})
            pilotes = sorted({o["fichier"] for o in occ} & FICHIERS_PILOTES)
            if occ:
                survivances.append({"jeton": jeton, "enonce": d["enonce"],
                                    "refute_le": d["date_refutation"], "source": d["source"],
                                    "n_survivances": len(occ),
                                    "survit_dans_un_fichier_qui_pilote": pilotes,
                                    "occurrences": occ[:10]})
    survivances.sort(key=lambda x: (not x["survit_dans_un_fichier_qui_pilote"],
                                    -x["n_survivances"]))
    graves = [d for d in survivances if d["survit_dans_un_fichier_qui_pilote"]]
    return {"etat": "MESURE", "n_declarees": n, "n_qui_survivent": len(survivances),
            "n_dans_un_fichier_qui_pilote": len(graves), "survivances": survivances}


def audit_refutations(cibles: list[tuple[str, Path]]) -> dict:
    """MODE DECOUVERTE, hors indicateur : un enonce REFUTE survit-il ailleurs ?

    Mode d'echec fondateur, P16.5 du 2026-09-12 : la calibration « 1908 » a ete refutee le
    2026-09-06 dans une memoire qui tracait elle-meme « 44 occurrences dans 25 fichiers et 4
    projets », et le `CLAUDE.md` du projet a continue six jours a la presenter comme valide. Rendre
    la memoire accessible ne corrige pas cela : ce qui manque est un controle de PROPAGATION.
    """
    textes = {}
    for nom, p in cibles:
        try:
            textes[nom] = p.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
    # 1. collecter les jetons portes par une ligne de refutation forte
    jetons: dict[str, set[str]] = collections.defaultdict(set)
    for nom, lignes in textes.items():
        for ligne in lignes:
            if not RX_REFUTATION.search(ligne):
                continue
            for rx in (RX_JETON_ANNEE, RX_JETON_TAUX):
                for m in rx.finditer(ligne):
                    if RX_REMPLACANT.search(ligne[:m.start()]):
                        continue    # c'est la valeur qui REMPLACE, pas celle qui tombe
                    jetons[m.group(1).replace(",", ".")].add(nom)
    # 2. chercher chaque jeton ailleurs, sur une ligne SANS marqueur de peremption ni refutation
    survivances = []
    for jeton, sources in sorted(jetons.items()):
        rx = re.compile(r"\b" + re.escape(jeton).replace(r"\.", "[.,]") + r"\b")
        occ = []
        for nom, lignes in textes.items():
            for i, ligne in enumerate(lignes, 1):
                if not rx.search(ligne):
                    continue
                if RX_REFUTATION.search(ligne) or RX_PERIME.search(ligne):
                    continue
                occ.append({"fichier": nom, "ligne": i, "extrait": ligne.strip()[:170]})
        if not occ:
            continue
        if len({o["fichier"] for o in occ}) > MAX_FICHIERS_PAR_JETON:
            continue    # mot commun du projet, pas la trace d'un enonce
        pilotes = sorted({o["fichier"] for o in occ} & FICHIERS_PILOTES)
        survivances.append({"jeton": jeton, "refute_dans": sorted(sources),
                            "n_survivances": len(occ),
                            "survit_dans_un_fichier_qui_pilote": pilotes,
                            "gravite": "A_TRIER_EN_PRIORITE" if pilotes else "RECIT",
                            "occurrences": occ[:12]})
    survivances.sort(key=lambda d: (not d["survit_dans_un_fichier_qui_pilote"],
                                    -d["n_survivances"]))
    graves = [d for d in survivances if d["survit_dans_un_fichier_qui_pilote"]]
    return {"n_jetons_refutes": len(jetons), "n_jetons_qui_survivent": len(survivances),
            "n_a_trier_en_priorite": len(graves),
            "avertissement": ("liste a TRIER, pas une dette : un meme jeton peut avoir un usage "
                              "legitime ailleurs (la souche « Pasteur 1908 » n'est pas la "
                              "calibration « 1908 »). Le controle signale, il ne tranche pas."),
            "survivances": survivances[:25]}


def temoin_positif(disque: dict, reg: set, prefixes: set) -> dict:
    """L'instrument VOIT-IL encore une citation nue ? Un compteur a zero ne vaut rien sans ce
    controle : il peut dire « plus de dette » aussi bien que « le filtre a tout mange ». Trois
    lignes synthetiques, dont on connait le verdict attendu, sont passees dans exactement les
    memes regles que les fichiers reels. Discipline maison, cf. cahier 2026-09-12 (38)."""
    cas = [
        # (ligne, label attendu detecte comme INCONNU et NU ?)
        ("Le clade `Bovis.9.9.9` porte 42 souches et sert de reference.", True),
        ("Le clade `Bovis.9.9.9` est PÉRIMÉ depuis la trichotomie.", False),
        ("Piege fnmatch : `--prefix Bovis.2` ne doit pas capter `Bovis.2.99`.", False),
    ]
    res = {}
    for ligne, attendu in cas:
        perime = bool(RX_PERIME.search(ligne))
        nus = []
        for lab in set(RX_LABEL.findall(ligne)):
            if RX_COMPOSITE.search(lab):
                continue
            if re.search(r"[._]\d{2,}$", lab) and RX_CONTEXTE_EXEMPLE.search(ligne):
                continue
            if lab in disque or lab in reg or lab in prefixes:
                continue
            if RX_NOTATION.search(lab) or lab.startswith("Bovis_"):
                continue
            nus.append(lab)
        obtenu = bool(nus) and not perime
        res[ligne[:60]] = {"attendu": attendu, "obtenu": obtenu, "ok": obtenu == attendu}
    res["_verdict"] = "INSTRUMENT_VOIT" if all(v["ok"] for k, v in res.items()
                                               if k != "_verdict") else "INSTRUMENT_AVEUGLE"
    return res


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    disque, reg = autorite()
    cum = cumul(disque)
    prefixes_valides = set(cum)
    print(f"autorite : {len(disque)} labels materialises, {len(reg)} noeuds au registre "
          f"({REGISTRE.name}), {len(prefixes_valides)} prefixes valides")

    cites: dict[str, dict] = collections.defaultdict(
        lambda: {"n": 0, "fichiers": collections.Counter(), "lignes": [], "perime_ctx": 0})
    effectifs = []
    chiffres = []
    n_fichiers = 0

    for nom, p in cibles_completes():
        n_fichiers += 1
        try:
            txt = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        _lignes = txt.splitlines()
        for i, ligne in enumerate(_lignes, 1):
            # Le CONTEXTE d'une phrase deborde la ligne : en markdown a retours durs, « un piege
            # de glob » et les labels qu'il cite tombent sur deux lignes voisines. Un critere
            # contextuel evalue ligne par ligne rate donc son propre cas. Fenetre de +/-1 ligne,
            # reservee au contexte d'EXEMPLE : l'elargir au marqueur de PEREMPTION ferait tomber
            # la dette pour de mauvaises raisons, ce qui est le mauvais sens d'erreur.
            ctx = " ".join(_lignes[max(0, i - 2):i + 1])
            labs = set(RX_LABEL.findall(ligne))
            if not labs:
                continue
            perime = bool(RX_PERIME.search(ligne))
            for lab in labs:
                if lab in ("Bovis_full", "Bovis_emergence", "Bovis_proto",
                           "Bovis_slaughter_bottleneck"):
                    continue
                if RX_COMPOSITE.search(lab):
                    continue
                if re.search(r"[._]\d{2,}$", lab) and RX_CONTEXTE_EXEMPLE.search(ctx):
                    continue
                e = cites[lab]
                e["n"] += 1
                e["fichiers"][nom] += 1
                e["perime_ctx"] += int(perime)
                if len(e["lignes"]) < 6:
                    e["lignes"].append(f"{nom}:{i}")
            # effectif annonce sur la meme ligne qu'un unique label
            if len(labs) == 1:
                lab = next(iter(labs))
                for m in RX_EFF.finditer(ligne):
                    try:
                        n = int(re.sub(r"[   ]", "", m.group(1)))
                    except ValueError:
                        continue
                    if n < 3:
                        continue
                    reel = cum.get(lab)
                    effectifs.append((nom, i, lab, n, reel if reel is not None else "",
                                      "" if reel is None else ("OK" if n == reel else
                                                               f"ecart {n - reel:+d}"),
                                      ligne.strip()[:200]))
            if re.search(r"SNP/génome/an|SNP par génome|taux d'horloge|taux de référence", ligne):
                for m in RX_TAUX.finditer(ligne):
                    chiffres.append((nom, i, m.group(1).replace(",", "."), ligne.strip()[:220]))

    lignes = []
    for lab, e in sorted(cites.items()):
        if RX_NOTATION.search(lab) or lab.startswith("Bovis_"):
            v = "NOTATION"
        elif lab in disque:
            v = "EXISTE"
        elif lab in reg or lab in prefixes_valides:
            v = "NOEUD_INTERNE"
        else:
            v = "INCONNU"
        lignes.append((lab, v, e["n"], e["perime_ctx"],
                       ";".join(f"{k}={v2}" for k, v2 in e["fichiers"].most_common(6)),
                       ";".join(e["lignes"])))
    with (OUT / "CITATIONS.tsv").open("w", encoding="utf-8") as f:
        f.write("label\tverdict\tn_citations\tn_lignes_avec_marqueur_perime\tfichiers\texemples\n")
        for r in sorted(lignes, key=lambda r: (r[1] != "INCONNU", -r[2])):
            f.write("\t".join(str(x) for x in r) + "\n")
    with (OUT / "EFFECTIFS.tsv").open("w", encoding="utf-8") as f:
        f.write("fichier\tligne\tlabel\teffectif_annonce\teffectif_reel_cumule\tverdict\textrait\n")
        for r in effectifs:
            f.write("\t".join(str(x) for x in r) + "\n")
    with (OUT / "CHIFFRES.tsv").open("w", encoding="utf-8") as f:
        f.write("fichier\tligne\tvaleur\textrait\n")
        for r in chiffres:
            f.write("\t".join(str(x) for x in r) + "\n")

    par_verdict = collections.Counter(r[1] for r in lignes)
    inconnus = [r for r in lignes if r[1] == "INCONNU"]
    inconnus_nus = [r for r in inconnus if r[3] == 0]
    ecarts = [r for r in effectifs if isinstance(r[5], str) and r[5].startswith("ecart")]
    mes = {"date": "2026-09-12", "n_fichiers_audites": n_fichiers,
           "autorite": {"labels_materialises": len(disque), "noeuds_registre": len(reg),
                        "registre": str(REGISTRE)},
           "labels_distincts_cites": len(lignes), "par_verdict": dict(par_verdict),
           "inconnus_sans_marqueur_de_peremption": len(inconnus_nus),
           "citations_inconnues_total": sum(r[2] for r in inconnus),
           "effectifs_testes": len(effectifs), "effectifs_en_ecart": len(ecarts)}
    (OUT / "MESURES.json").write_text(json.dumps(mes, indent=2, ensure_ascii=False),
                                      encoding="utf-8")

    print(f"\n{n_fichiers} fichiers audites, {len(lignes)} labels distincts cites")
    for k, v in par_verdict.most_common():
        print(f"  {v:5d}  {k}")
    print(f"\nINCONNUS sans marqueur de peremption : {len(inconnus_nus)} labels, "
          f"{sum(r[2] for r in inconnus_nus)} citations")
    for r in sorted(inconnus_nus, key=lambda r: -r[2])[:25]:
        print(f"  {r[0]:45s} {r[2]:4d} cit.  {r[4][:90]}")
    print(f"\nEffectifs annonces testes : {len(effectifs)}, en ecart : {len(ecarts)}")
    for r in sorted(ecarts, key=lambda r: -abs(r[3] - (r[4] or 0)))[:20]:
        print(f"  {r[0]:16s}:{r[1]:<6d} {r[2]:42s} annonce {r[3]:>7d}  reel {r[4]:>7} {r[5]}")
    # ventilation des INCONNUS par fichier : c'est elle qui dit ou porter l'effort
    par_fichier = collections.Counter()
    for r in inconnus_nus:
        for part in r[4].split(";"):
            if "=" in part:
                k, v = part.rsplit("=", 1)
                par_fichier[k] += int(v)
    print("\nINCONNUS sans marqueur, par fichier :")
    for k, v in par_fichier.most_common(15):
        print(f"  {v:5d} citations  {k}")
    mes["inconnus_par_fichier"] = dict(par_fichier.most_common())
    cib = cibles_completes()
    mes["refutations_declarees"] = audit_refutations_declarees(cib)
    mes["refutations_decouverte"] = audit_refutations(cib)
    rd = mes["refutations_declarees"]
    if rd.get("etat") == "MESURE":
        print(f"\nÉNONCÉS DÉCLARÉS RÉFUTÉS (refutations.tsv) : {rd['n_declarees']} déclarés, "
              f"{rd['n_qui_survivent']} survivent, dont "
              f"{rd['n_dans_un_fichier_qui_pilote']} dans un fichier qui PILOTE")
        for d in rd["survivances"]:
            marque = "!!" if d["survit_dans_un_fichier_qui_pilote"] else "  "
            print(f" {marque} {d['jeton']:>8s} : {d['n_survivances']:3d} survivance(s)  "
                  f"({d['enonce'][:60]})")
            for o in d["occurrences"][:2]:
                print(f"              {o['fichier']}:{o['ligne']}  {o['extrait'][:95]}")
    else:
        print(f"\nRegistre de réfutations ABSENT : {rd.get('chemin')}")
    mes["tables_lignee"] = audit_tables(disque, reg, prefixes_valides)
    print("\nTABLES a colonne de lignee (le label VIVANT mais FAUX qu'aucun test d'existence ne voit) :")
    for nom, t in mes["tables_lignee"].items():
        if t["etat"] != "MESURE":
            print(f"  {nom}: {t['etat']}")
            continue
        print(f"  {nom}: {t['n_lignes']} lignes, {t['placement_exact']} exactes "
              f"({t['pct_exact']} %), {t['label_mort']} labels morts, "
              f"**{t['label_VIVANT_mais_FAUX']} VIVANTS MAIS FAUX**, "
              f"{t['souche_hors_disque']} souches hors disque")
    mes["temoin_positif"] = temoin_positif(disque, reg, prefixes_valides)
    print(f"\nTEMOIN POSITIF : {mes['temoin_positif']['_verdict']}")
    for k, v in mes["temoin_positif"].items():
        if k != "_verdict" and not v["ok"]:
            print(f"  ECHEC  attendu={v['attendu']} obtenu={v['obtenu']}  {k}")
    (OUT / "MESURES.json").write_text(json.dumps(mes, indent=2, ensure_ascii=False),
                                      encoding="utf-8")
    print(f"\necrit : {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
