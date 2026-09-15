---
name: isfinder-offline
description: >-
  Academic research toolkit (Guyeux group, FEMTO-ST). Repli LOCAL/hors-ligne pour identifier ou
  classer une séquence d'insertion (IS) quand isfinder.biotoul.fr est injoignable — ce qui arrive
  souvent (échec SSL/connexion direct, pas seulement un blocage d'outil de fetch, vérifié à deux
  reprises en 2026-08). Mirroir GitHub statique (thanhleviet/Isfinder-sequences, ~6000 IS, snapshot
  figé ~2020-10) : recherche par nom (IS.csv) ou par séquence (blastn/blastp contre IS.fna/IS.faa).
  Utiliser quand : classer un élément mobile candidat trouvé dans un génome bactérien, vérifier la
  famille/groupe d'une IS déjà nommée dans la littérature, ou chercher des répétitions inversées
  terminales (IR) de référence. TOUJOURS essayer ISfinder EN DIRECT d'abord si le site répond ;
  ce skill est un repli, pas une source plus autorisée que le site lui-même.
argument-hint: "<nom IS ou fichier FASTA> [--method name|blastn|blastp]"
allowed-tools: Bash, Read, WebFetch
user-invocable: true
---

# /isfinder-offline — Identification d'IS hors ligne (repli ISfinder)

## Garde-fou n°1 — toujours tenter ISfinder EN DIRECT en premier

```bash
curl -s -o /dev/null -w "%{http_code}\n" -m 15 "https://isfinder.biotoul.fr/"
```

Si ça répond (200), utiliser le site directement (fiche officielle, à jour, faisant autorité) —
ce skill ne sert QUE quand cette requête échoue (connexion refusée, timeout, `HTTP_CODE:000`).
Vécu 2026-08-05 (projet `Rv3222c`, P9.2o) : le site est resté injoignable en curl direct des deux
côtés (`isfinder.biotoul.fr` et le miroir `www-is.biotoul.fr`), pas juste bloqué pour l'outil de
fetch — c'est la situation que ce skill couvre.

## Garde-fou n°2 — COUVERTURE INCOMPLÈTE, pas juste périmée

Le mirroir ne contient QUE les IS formellement curées par ISfinder au moment du snapshot (~2020-10).
**Cas vécu et vérifié** (P9.2o, `Rv3222c`) : **IS1607** (Mycobacterium tuberculosis, nommée par
Dziadek et al. 2000) est **ABSENTE** du jeu de données — recherche exhaustive dans `IS.csv`
confirmée à zéro résultat. Explication probable : Dziadek 2000 décrit IS1607 comme un élément
« insertion-sequence-*related* », un seul exemplaire déjà dégradé au moment de sa description —
jamais soumis pour curation formelle à ISfinder, contrairement aux IS actives multi-copies typiques
(IS6110 etc.). **Une absence dans ce mirroir ne prouve donc PAS l'inexistence ou l'absence de
classification officielle** — elle peut aussi signifier "jamais formellement curée par ISfinder",
un état différent de "site indisponible temporairement". Toujours le dire explicitement dans le
rapport, ne jamais présenter un résultat négatif de ce skill comme équivalent à un résultat négatif
d'ISfinder lui-même.

## Mise en place (une fois, ~13 Mo)

```bash
DIR=~/docs/codes/mtbc/isfinder_local
mkdir -p "$DIR" && cd "$DIR"
for f in IS.csv IS.fna IS.faa; do
  curl -sL "https://raw.githubusercontent.com/thanhleviet/Isfinder-sequences/bedbeb5c16618eca3e16ef74adf865d6b88cafb5/$f" -o "$f"
done
makeblastdb -in IS.fna -dbtype nucl -out IS_nucl
makeblastdb -in IS.faa -dbtype prot -out IS_prot
wc -l IS.csv   # ~6008 lignes (header + ~6007 IS)
```

Empreintes SHA-256 verifiees sur le commit miroir ci-dessus :

```text
IS.csv  1d7d4fa2d33488f2a21a6ca1ad908d4960267582b56addcfa5e098a5414cd5e2
IS.fna  47607f9e398d200f1954b18b9d91d6f5a612331ee137cb10d63897688f9d5507
IS.faa  7672fecd114c962c2d8640b70324e10b9a2f111c9ad6d40112800fdb65213b12
```

Le miroir ne declare pas de licence claire : garder ces fichiers comme cache local de travail, sans
les redistribuer dans un paquet public.

`IS.csv` colonnes : `N°,Name,Family,Group,Synomyns,Iso,Origin,Length,IR,DR,ORF,Accession Number,url`.
`IS.fna` en-têtes : `>(nom IS)_(groupe)_(famille)`. `IS.faa` : format Prokka,
`>(nom) ~~~(nom)_(groupe)_(famille)_ORF~~~(fonction)~~~`.

## Méthode 1 — recherche par nom (une IS déjà nommée dans la littérature)

```bash
DIR=~/docs/codes/mtbc/isfinder_local
grep -i "^[0-9]*,IS1607," "$DIR/IS.csv"          # recherche exacte sur le nom
grep -i "1607" "$DIR/IS.csv"                      # recherche large (attrape aussi la colonne synonymes)
```

Si présent : la ligne CSV donne famille, groupe, longueur, IR (répétitions inversées terminales),
DR (duplication du site cible), structure des ORF — exactement ce qu'une fiche ISfinder donnerait.
Si absent : voir garde-fou n°2, NE PAS conclure "IS non classifiée officiellement", conclure
"absente de ce mirroir, statut ISfinder réel inconnu tant que le site n'est pas réinterrogeable".

## Méthode 2 — classification par séquence (élément mobile candidat non nommé)

```bash
DIR=~/docs/codes/mtbc/isfinder_local
blastn -task blastn -query candidat.fna -db "$DIR/IS_nucl" \
    -outfmt "6 sseqid pident length evalue bitscore" -max_target_seqs 5 -evalue 1e-10
# ou, sur la traduction du meilleur cadre / transposase suspectée :
blastp -query candidat.faa -db "$DIR/IS_prot" \
    -outfmt "6 sseqid pident length evalue bitscore" -max_target_seqs 5 -evalue 1e-5
```

Lire le nom du meilleur hit (`>(nom)_(groupe)_(famille)`) puis croiser avec `IS.csv` pour la fiche
complète. Comme pour tout profil Pfam/HMM (cf. `pfam_scan.py` du même écosystème), lire la
**couverture** de l'alignement autant que l'identité — un hit à haute identité sur une petite
fraction de la longueur de l'IS de référence est un domaine partagé, pas une classification ferme.

## Citation obligatoire si le résultat entre dans un manuscrit

Le mirroir GitHub lui-même n'est pas une source à citer — citer la source primaire qu'il recopie :

> Siguier P, Perochon J, Lestrade L, Mahillon J, Chandler M. ISfinder: the reference centre for
> bacterial insertion sequences. *Nucleic Acids Res.* 2006;34(Database issue):D32-D36.
> doi: 10.1093/nar/gkj014

Si le résultat vient spécifiquement du mirroir (ISfinder injoignable au moment de la vérification),
le signaler dans les méthodes du manuscrit ou dans le cahier de labo : « classification vérifiée via
un mirroir statique d'ISfinder (snapshot ~2020-10, isfinder.biotoul.fr injoignable au moment de la
vérification) », pour que la limite de fraîcheur soit traçable.

## Intégration avec l'écosystème

- Complète `mtbc-lineages`/`species-id` (identification d'espèce) pour la caractérisation d'éléments
  mobiles trouvés en cours d'analyse de génome.
- Voisin naturel de `crisprcasdb_local` (autre « brique d'infrastructure » : copie locale d'une base
  externe peu fiable en accès direct, même position dans l'écosystème `mtbc/`).
- Origine : projet `Rv3222c`, piste P9.2o (2026-08-05) — IS1607, décrite par Dziadek et al. 2000 comme
  vestige dégradé inséré dans un paralogue de Rv3222c, a motivé cette recherche.
