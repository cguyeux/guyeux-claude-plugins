---
name: crispr-spacer-null
description: >-
  Academic research toolkit (Guyeux group, FEMTO-ST), peer-reviewed comparative
  genomics: evaluate whether a CRISPR spacer, primer, amplicon, or short marker
  sequence is truly absent from a published bacterial genome set, rather than an
  artefact of assembly, orientation, masking, read depth, database scope, or
  taxonomy. Use when: testing spacer or marker null claims, comparing CRISPR
  arrays, auditing negative PCR or BLAST results, or deciding whether a zero-hit
  sequence can support an evolutionary claim.
---

# crispr-spacer-null — un appariement court n'a de sens que comparatif

## Pourquoi ce skill existe

`../archeo_crispr/` porte ce garde-fou (n°9) : **« un test de protospacer n'a
de sens que comparatif »**. Sur 20-50 nt, une e-value de 1e-3 à 10 ne dit rien
seule — elle doit toujours être lue contre un modèle nul explicite. Le dossier
`SpacerEgalVirus` (2019-2022, repris 2026) a développé ce harnais pour
répondre à une question précise (les espaceurs du locus DR du MTBC
pointent-ils vers les mycobactériophages plus qu'une séquence de même
composition ?) et l'a durci sur plusieurs mois : nul dinucléotidique d'abord,
puis d'ordre supérieur face à l'objection qu'un rapporteur poserait
forcément, puis témoins génomiques réels quand la permutation seule s'est
révélée insuffisante (P2.12 : des témoins GC-appariés ressemblaient autant
que les espaceurs aux mycobactériophages en FORCE d'appariement — seule la
CIBLE les distinguait). Ce skill emballe ce harnais pour qu'un projet
frère n'ait pas à le redécouvrir pièce par pièce.

## Les quatre outils

```bash
CSN=~/docs/codes/claude_plugins/bio_pathogens/skills/crispr-spacer-null/scripts/crispr_spacer_null.py
```

### 1. `null` — permutation d'ordre k, AVEC diagnostic de dégénérescence

```bash
python3 $CSN null --fasta spacers.fa --k 2 --n-perm 100 --out perms_di.fasta
python3 $CSN null --fasta spacers.fa --k 4 --diagnostic-only
```

k=1 (composition), k=2 (dinucléotidique, Altschul & Erickson 1985 — le nul par
défaut : conserve le GC ET les biais dinucléotidiques, le confondant principal
entre deux génomes GC-riches), k=3, k=4 (marche eulérienne généralisée sur les
(k-1)-mers).

**Le piège que ce skill refuse de cacher** : plus k monte, moins il reste de
séquences admissibles pour une requête courte, jusqu'à ce qu'il n'en reste
qu'une poignée — auquel cas un ratio observé/nul proche de 1 est
**indécidable**, pas un verdict d'absence de signal. `--diagnostic-only` rend
le nombre EXACT de séquences admissibles par requête (théorème BEST : de
Bruijn-van Aardenne-Ehrenfest-Smith-Tutte, déterminant de Bareiss), avant tout
calcul. Sur des espaceurs CRISPR de 35-41 nt (SpacerEgalVirus, P2.11) :
médiane de 698 000 séquences admissibles à k=3 (le nul reste informatif), mais
**médiane de 16 à k=4** (nul quasi dégénéré : 13,7 % des tirages reproduisent
alors l'original). Toujours lancer `--diagnostic-only` avant de citer un
résultat à k>=3, et rapporter le nombre de requêtes sous 100 séquences
admissibles.

### 2. `controls` — témoins génomiques GC-appariés, hors locus

```bash
python3 $CSN controls --genome ref.fasta --fasta spacers.fa \
    --exclude-start 3113658 --exclude-end 3132714 --flank 5000 \
    --n 300 --out controls.fasta
```

Tire `--n` fenêtres du génome de référence, de même longueur et de GC apparié
(±`--gc-tol`, 0,02 par défaut) aux requêtes, en excluant `[start-flank,
end+flank[`. **Pourquoi c'est nécessaire en plus de la permutation** : une
permutation ne peut détecter qu'un effet de COMPOSITION. Un effet de génome
entier (homologie de fond, prophages, biais d'ordre au-delà du dinucléotide)
lui échappe complètement. SpacerEgalVirus (P2.8) a découvert que des témoins
GC-appariés hors locus DR ressemblent aux mycobactériophages **autant que les
espaceurs en force d'appariement** — le nul seul aurait donc produit un faux
positif de généralité. P2.12 a ensuite montré que la CIBLE (test de
spécificité, pas la force) sépare bien les deux : c'est le test qui a sauvé
le projet.

### 3. `blast-test` — force (test A) et spécificité (test B)

```bash
python3 $CSN blast-test --observe spacers.fa --null perms_di.fasta \
    --db data/blast_db/ma_base --target-keyword Mycobacterium \
    --evalues 10 1 0.1 0.01 --out-dir résultats/mon_test
```

BLAST observé + nul contre la même base, puis pour chaque seuil d'e-value
balayé *a posteriori* (un seul BLAST permissif, filtré ensuite — observé et
nul subissent toujours rigoureusement le même filtre) :

- **test A (force)** : la meilleure e-value réelle d'une requête bat-elle
  celle de ses N permutations ? Répond à *« cette séquence ressemble-t-elle à
  une cible plus qu'une séquence de même composition ? »*
- **test B (spécificité)** : la PROPORTION de hits tombant sur un sous-ensemble
  cible (`--target-keyword`, un ou plusieurs mots cherchés dans le nom du
  sujet, ex. `Mycobacterium` ou `Massilia Martelella Ralstonia`) est-elle plus
  élevée pour l'observé que pour le nul ? C'est le test central dans le
  dossier d'origine — il neutralise d'un coup la composition ET la taille de
  la base, et répond à *« le signal pointe-t-il vers UNE cible précise, ou
  n'importe où ? »*

`--null` est optionnel : sans lui, `blast-test` rend juste le compte de hits
observés par seuil (utile pour explorer avant de lancer le nul).

### 4. `kmer-partial` — correspondances partielles (Shmakov 2017/2020)

```bash
python3 $CSN kmer-partial --observe spacers.fa --null perms_di.fasta \
    --target actinophages.fasta --control non_actino.fasta --k 16 18 20
```

Pour le matériel **trop divergé pour aligner** (BLASTN ne rend aucune e-value
exploitable) : ce qui survit à des millions d'années de divergence n'est pas
l'alignement d'ensemble mais des **segments exacts courts**. Compte les
k-mers (16-20 nt typiquement) de chaque requête retrouvés exactement dans le
corpus cible, observé contre nul. `--control` fournit un second corpus
(composition similaire, cible différente) : **c'est le juge** — un ratio
élevé sur les DEUX corpus signale un artefact de composition, un ratio élevé
sur la seule cible est le signal cherché. SpacerEgalVirus (P2.7) a ainsi
récupéré du signal réel (15,1x, p=0,0099) dans une « zone grise » de 27
espaceurs que BLASTN et SpacePHARER (recherche protéique) ne savaient pas
exploiter.

## Composer les quatre outils : le protocole complet du dossier d'origine

```bash
# 1. Diagnostic AVANT tout calcul : le nul choisi est-il informatif ?
python3 $CSN null --fasta spacers.fa --k 2 --diagnostic-only

# 2. Nul dinucléotidique (et, si le diagnostic le permet, tri/tétra en renfort)
python3 $CSN null --fasta spacers.fa --k 2 --n-perm 100 --out perms_di.fasta

# 3. Témoins génomiques réels, pour le contrôle biologique
python3 $CSN controls --genome H37Rv.fasta --fasta spacers.fa \
    --exclude-start LOCUS_START --exclude-end LOCUS_END --n 300 --out controls.fasta

# 4. Force + spécificité, observé vs nul, sur la base cible
python3 $CSN blast-test --observe spacers.fa --null perms_di.fasta \
    --db ma_base --target-keyword Mycobacterium --out-dir résultats/test1
# ... rejouer blast-test avec --observe controls.fasta (sans --null, ou avec
# un nul des controles) pour comparer force ET cible des témoins

# 5. Pour les requêtes sans hit BLAST exploitable : k-mers partiels
python3 $CSN kmer-partial --observe spacers.fa --null perms_di.fasta \
    --target ma_cible.fasta --control mon_temoin_composition.fasta
```

## Garde-fous (hérités du dossier d'origine, valables partout)

1. **Ne jamais lire une e-value seule sur du matériel court.** À 20-50 nt,
   1e-3 à 10 est le régime normal, pas un signal en soi.
2. **Le nul mononucléotidique/dinucléotidique ne détecte QUE la composition.**
   Un effet de génome entier (P2.8, P2.12) exige un témoin réel (`controls`),
   pas seulement une permutation.
3. **Un nul d'ordre k>=3 peut être dégénéré sur du matériel court.** Toujours
   vérifier avec `null --diagnostic-only` avant de citer un résultat.
4. **Le test de spécificité (test B) est plus informatif que le test de force
   (test A).** Deux séquences peuvent avoir la même force d'appariement
   moyenne et une spécificité de cible radicalement différente (SpacerEgalVirus
   P2.9 : la spécificité se jouait au niveau de l'ORDRE taxonomique, pas du
   GENRE — le test B l'a révélé, pas le test A).
5. **Le corpus témoin de `kmer-partial` doit avoir une composition proche du
   corpus cible**, sans quoi un ratio élevé peut n'être qu'un effet de GC.

## Validation

Les quatre sous-commandes ont été retestées le 2026-08-11 contre les données
et résultats déjà publiés de `SpacerEgalVirus` : `null --diagnostic-only`
reproduit l'ordre de grandeur de la dégénérescence à k=4 rapporté par P2.11
(médiane à deux chiffres, contre médiane de plusieurs milliers à k=3) ;
`controls` reproduit le tirage GC-apparié de P2.12/P2.17 sur le génome H37Rv ;
`blast-test` reproduit qualitativement (sur un sous-échantillon de 15
espaceurs) le sens et l'ordre de grandeur du ratio de spécificité de P2.1
contre ViruSITE.

## Voisinage

`crisprbuilder` (ce même groupe de skills) pour l'EXTRACTION du locus en
amont (DR, arrays, spacers) ; ce skill-ci pour l'INTERPRÉTATION statistique
des correspondances trouvées. `SpacerEgalVirus` (projet) pour l'usage complet
d'origine et son historique de durcissement méthodologique ; `archeo_crispr`
(projet) pour le garde-fou n°9 qui a motivé ce skill.

## Dépendances

Python >= 3.9, stdlib seule pour `null`/`controls`/`kmer-partial`. `blastn`
(NCBI BLAST+) requis pour `blast-test` uniquement.
