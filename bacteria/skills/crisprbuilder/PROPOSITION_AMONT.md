# Propositions pour `cguyeux/CRISPRbuilder-TB`

Note préparatoire à la piste P10.5 du projet `SpacerEgalVirus`.

**Mise à jour 2026-08-11 (arbitrage CG) : PR #1 (découverte de novo) ouverte.**
https://github.com/cguyeux/CRISPRbuilder-TB/pull/2 — voir « Suite donnée » en fin de
document pour ce qui a été réellement envoyé, ce qui reste en attente, et une correction
importante à la lecture du point 2 ci-dessous.

État du dépôt amont au 2026-08-10 : branche `master`, dernière mise à jour 2024-03-13.
Référence de l'outil : Guyeux et al. 2021, *PLOS Comput Biol* 17(3):e1008500.

## Ce que l'amont fait bien, et qu'il ne faut pas toucher

Reconstruire le locus depuis les **lectures** et jamais depuis l'assemblage. Ce choix est
le bon, et il est maintenant chiffré : sur 21 assemblages SPAdes de *M. canettii*, cinq
ne contiennent aucune copie du DR, l'assembleur ayant effacé une région faite d'une
trentaine de répétitions quasi identiques. L'échec est silencieux, rien dans les contigs
ne le signale. Tout pipeline qui blaste un DR sur des contigs hérite donc d'un biais
d'échantillonnage invisible.

## 1. Découverte de novo du DR, en plus du catalogue

L'amont blaste un fichier de 221 motifs connus du MTBC (`data/fastas/crispr_patterns.fasta`)
et ne peut donc rien trouver là où le DR diffère. Or *M. canettii*, le plus proche parent
du MTBC, porte au moins quatre systèmes distincts (III-A avec le DR du MTBC, I-G, I-E,
I-C) dont les DR n'ont aucun rapport entre eux. Sur 151 souches de `bdd/actuelle/Canettii/`
traitées depuis les lectures : 101 III-A, 16 I-G, 15 I-E, 2 I-C, et 15 portant un DR ne
correspondant à aucun des cinq catalogués. Un tiers des souches est donc hors de portée du
catalogue.

La découverte proposée n'a besoin d'aucune dépendance : un DR est un k-mer sur-représenté
(sur lectures) ou périodique (sur génome), que l'on étend ensuite par consensus. Le
classement final se fait par validation — on extrait réellement l'array de chaque candidat.

Garde-fou à reprendre tel quel : **ne pas confondre « pas de DR du MTBC » et « pas de
CRISPR »**. C'est l'erreur que la découverte de novo corrige, et elle se commet facilement.

## 2. Trois défauts trouvés en portant la méthode, à vérifier dans l'amont

Ils ne sont pas propres à notre réimplémentation ; qui écrit ce genre de code les rencontre.

**a. Alignement des contextes lors de l'extension par consensus.** Si les fenêtres
extraites autour de chaque occurrence sont découpées sans remplissage, une occurrence
située à moins d'une demi-fenêtre du bord d'une lecture décale toutes ses colonnes. Sur un
chromosome complet cela concerne une poignée de positions ; sur des lectures de 75 à 150 nt,
presque toutes. Mesure sur des lectures simulées depuis le locus de H37Rv, couverture 50x :
consensus rendu `GTCGGCTCGGGGGGGGTGGGG` à 75 nt, qui n'est pas même un fragment du DR, et
la graine non étendue à 100 et 150 nt. Après correction, le DR exact aux trois longueurs.

**b. Le seuil de conservation d'une colonne doit dépendre de l'effectif.** Un seuil fixe
(80 %, par exemple) est trop permissif sur un petit array : avec 10 copies dans un génome
à 65 % de GC, une colonne de spacer atteint 8/10 par hasard environ trois fois sur mille.
Un critère binomial lu contre la composition du génome exige 9/10 à dix occurrences et
26/30 à trente, ce qui est le comportement voulu.

**c. Rien ne distingue un CRISPR d'une répétition en tandem.** Les deux produisent un motif
court, très conservé, revenant à intervalles réguliers ; la périodicité ne les sépare pas
et la conservation du DR non plus (100 % dans les deux cas). Cas mesuré sur *M. canettii*
CIPT 140070008 : un VNTR de 11 copies d'un motif de 23 nt, à 69 nt d'écart onze fois de
suite, battait le vrai locus I-G sur tous les critères. Ce qui les sépare est ce qu'il y a
**entre** les copies : un array CRISPR intercale des spacers tous différents, un VNTR
répète une unité. La mesure utile est une identité moyenne entre spacers, et non un test
d'unicité — le VNTR en question rend 7 spacers « distincts » sur 10, qui sont des variantes
à un nucléotide du même motif.

## 3. Sortie JSON structurée

Un objet par analyse : `dr`, `dr_conservation`, `n_arrays`, `n_spacers_total`, et par array
`sequence / strand / start / end / span / n_dr / n_spacers / spacers[]`. Permet de chaîner
l'outil dans un pipeline sans reparser une sortie texte, et de journaliser un lot.

## 4. Mode génome, en complément du mode lectures

Quand un assemblage fermé est disponible (génome de référence, chromosome complet), la
reconstruction depuis les lectures est un détour coûteux. Un mode génome donne le locus
avec ses coordonnées exactes, ce que le mode lectures ne peut pas fournir.

## 5. Lecture en flux depuis une URL

`--reads https://…/ERRxxxxxx_1.fastq.gz` analysé à la volée, sans rien écrire sur disque.
Sur un lot de 150 runs cela évite environ 39 Go de fichiers temporaires, et une limite de
lectures fait qu'on ne télécharge même pas le fichier entier. Utile en pratique : sur cette
machine, `/tmp` est un tmpfs, donc de la RAM, et un lot « télécharger, analyser, supprimer »
y saturait la mémoire.

## 6. Mode contrôle qualité

Le CRISPR est un marqueur taxonomique à haute résolution et quasi gratuit. Un DR appartenant
à un autre genre que celui attendu trahit une contamination qu'un mapping contre la
référence de l'espèce attendue ne verra jamais, les lectures du contaminant ne mappant pas
et disparaissant en silence. Cas fondateur : ERR266123, étiqueté *M. canettii*, porte le DR
du système I-F de *Pseudomonas aeruginosa* et un assemblage de 10,8 Mb, soit 2,45 fois un
génome de mycobactérie. Le contrôle croise deux signaux indépendants, le genre porteur du DR
et le rapport de taille.

## Ce qui reste à faire avant de proposer quoi que ce soit

Lire le code amont. Ce document est écrit depuis la réimplémentation et depuis l'article,
pas depuis une lecture ligne à ligne de `CRISPRbuilder-TB` : les points 2a, 2b et 2c sont
des défauts constatés chez nous, dont il faut vérifier s'ils existent là-bas avant de les
signaler. Les points 1, 3, 4, 5 et 6 sont des ajouts, et ne dépendent pas de cette
vérification.

## Suite donnée (2026-08-11)

Lecture du code amont faite (`crisprbuilder.py`, 402 lignes, `tools/tools.py`, 157 lignes).

⚠️ **Correction au point 2 : les défauts 2a/2b/2c n'ont PAS d'équivalent côté amont, et il
aurait été trompeur de les signaler comme des « bugs de l'amont ».** L'amont ne fait
JAMAIS de construction de consensus par alignement de contextes ni de découverte de novo :
il blaste le catalogue de 221 motifs connus, puis reconstruit un contig par extension
gloutonne read-par-read à la majorité simple (`_get_contigs`), un mécanisme entièrement
différent de celui de `crisprbuilder2.py`. Les trois défauts sont donc bien réels, mais
uniquement dans NOTRE réimplémentation — la réserve du paragraphe précédent a rempli
exactement son rôle : elle a empêché d'écrire une proposition basée sur une hypothèse
fausse.

**Ce qui a été fait à la place, plus utile : implémenter le point 1 (découverte de novo)
directement pour ce dépôt, plutôt que de le décrire.** `tools/de_novo.py` (nouveau,
autonome, aucune dépendance ajoutée) réutilise l'algorithme validé de `crisprbuilder2.py`
(sélection de graines par sur-représentation, tri par diversité de contexte plutôt que par
fréquence brute — la fréquence brute seule échoue : le vrai DR ne sortait qu'au rang ~4000
sur ERR5104570) et le branche dans `_sequences_of_interest` : si aucun des 221 motifs ne
matche, le DR découvert de novo est injecté dans `self._dicofind` et repasse par le MÊME
pipeline BLAST/contigs que l'amont utilise déjà pour un motif catalogué — aucune étape
avale n'est dupliquée ni modifiée. Validé contre des lectures réelles (ERR5104570, 200 000
lectures streamées depuis l'ENA) : le candidat classé en tête est exactement le DR III-A
connu. Non exécuté de bout en bout via la CLI complète (dépendances `xlrd`/sra-tools
absentes de l'environnement de préparation), signalé comme tel dans la PR.

**PR ouverte : https://github.com/cguyeux/CRISPRbuilder-TB/pull/2**, branche
`de-novo-dr-discovery`, diff purement additif (280 lignes, 3 fichiers, aucun comportement
existant modifié), option `-novo false` pour revenir au comportement d'avant.

**Non inclus dans cette PR, à reconsidérer séparément si utile** : sortie JSON structurée
(point 3), mode génome (point 4), lecture en flux depuis une URL (point 5), mode contrôle
qualité (point 6). Chacun toucherait une partie différente et déjà volumineuse du code
(`_cas_investigation`, `_find_IS_around`, l'aval `_get_contigs`) ; les mélanger à la
découverte de novo dans une seule PR l'aurait rendue plus difficile à relire. À proposer
un par un si l'auteur (CG) le juge utile après retour sur la première.
