---
name: panisa
description: >-
  Academic research toolkit (Guyeux group, FEMTO-ST) for ab initio detection of
  insertion sequences (IS) in bacterial genomes from short-read alignments, using
  panISa (Treepong, Guyeux, Meunier, Couchoud, Hocquet, Valot, Bioinformatics
  2018). Detects IS insertion sites WITHOUT any IS database, from clipped-read
  signatures, direct repeats and reconstructed inverted repeats, then optionally
  assigns families against ISfinder. Use when: looking for mobile elements in a
  published research isolate of any bacterium (non-tuberculous mycobacteria,
  Pseudomonas, Salmonella, Helicobacter...), hunting IS types ABSENT from a known
  IS panel, or documenting one insertion with publication-grade evidence (direct
  repeat plus both border sequences).
argument-hint: "<fichier BAM ou accession> [--min-clipped N] [--annotate]"
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
---

# panISa : détection ab initio de séquences d'insertion

## Provenance, et pourquoi la citer

panISa est un outil **du groupe** : Treepong P, **Guyeux C**, Meunier A, Couchoud C, Hocquet D,
Valot B. *panISa: ab initio detection of insertion sequences in bacterial genomes from short read
sequence data.* Bioinformatics 2018, 34(22):3795-3800, `10.1093/bioinformatics/bty479`. Dépôt :
`github.com/bvalot/panISa`. Toute utilisation dans un manuscrit se cite, y compris quand c'est nous
qui l'utilisons.

## Ce qu'il fait, et ce qu'aucun autre outil de la collection ne fait

Trois étapes : signature de **lectures clippées** aux bornes de l'insertion, détection de la
**répétition directe** que l'insertion engendre, puis reconstruction des **répétitions inversées**
(IRL/IRR) pour valider. Aucune base de données d'IS en entrée, d'où « ab initio ».

> [!IMPORTANT]
> **Ne pas l'utiliser pour une présence/absence d'IS connue chez une souche MTBC déjà en base.**
> La chaîne TBannotator le fait déjà, pour 136 822 souches, en mappant les séquences clippées contre
> un panel de **22 IS connues du MTBC** : voir `is_report.json`, `coverage_report_is.bed.tsv` et
> `is_mapping.bam` dans `mp:/data/current/run/results/<SRA>/`, et le skill `fetch-tbannotator`.
> Relancer panISa là-dessus serait plus lent et rendrait des sites bruts au lieu d'annotations.
>
> **Et surtout** : si le problème est de LIRE ces résultats, ce n'est pas un problème de calcul. Le
> champ `insertion_sequences` d'un `report.json` **tronque au premier IS non-référence** si on le
> parse naïvement (14 insertions comptées au lieu de 18 435 : utiliser `raw_decode`, cf.
> `~/.claude/knowledge/tuberculosis.md`). Ne pas répondre à un bug de parsing par une campagne de
> calcul.

Le complément réel de panISa tient en trois cas :

1. **Bactéries hors MTBC** (mycobactéries non tuberculeuses, autres genres) : aucune chaîne
   équivalente n'existe, panISa est agnostique de l'espèce. C'est son usage principal ici, et il y a
   déjà de la matière sur `mp` : `references_results/` porte **10 001 souches de *P. aeruginosa*** et
   **710 de *M. leprae*** déjà mappées, dont le `coverage_report_is.bed.tsv` **ne contient que
   l'en-tête** parce que le panel d'IS de la chaîne est celui du MTBC. Le fichier est vide, pas en
   erreur : rien ne signale que la détection n'a pas eu lieu.
2. **IS absentes du panel** : un panel de 22 IS est aveugle par construction à tout le reste. La
   question « quels *autres* éléments mobiles bougent dans ce clade ? » ne peut se poser qu'ab initio.
3. **Preuve détaillée d'une insertion** : panISa rend la répétition directe et les deux séquences de
   bordure, matériau publiable, là où un pipeline rend une présence/absence et un score.

## Environnement

Sur `mh`, environnement prêt et testé : **`/Work/Users/cguyeux/envs/bacto`** (micromamba, voir
`remote-compute`), qui porte `panISa.py` **2.3.2** (le paquet bioconda s'annonce en 0.1.6 mais embarque
2.3.2), `pymlst`, EMBOSS et `samtools`. Dépendances amont : `pysam` ≥ 0.9, `requests` ≥ 2.12, EMBOSS.

> [!WARNING]
> **Deux variables d'environnement, sans quoi l'outil échoue en silence ou refuse de démarrer.**
> ```bash
> P=/Work/Users/cguyeux/envs/bacto
> export LD_LIBRARY_PATH=$P/lib PATH=$P/bin:$PATH
> ```
> `LD_LIBRARY_PATH` parce que le `libstdc++` de Rocky 8 est trop ancien pour les binaires conda (voir
> `remote-compute`). **`PATH` parce que panISa appelle `einverted` (EMBOSS) en sous-processus** : sans
> lui, `/bin/sh: einverted: command not found` passe dans le flux d'erreur, la colonne
> « Inverted repeats » se remplit de `No IR`, et **le résultat reste plausible tout en ayant perdu
> l'étape de validation**. Vérifié le 2026-08-17. Toujours lancer un site témoin et regarder cette
> colonne avant une campagne.

Coût mesuré : **2,3 s** pour un BAM de 41 Mo (génome de 6,3 Mb, 313 509 lectures). Le calcul n'est donc
jamais le facteur limitant, c'est le **déplacement des données** qui décide (voir ci-dessous).

> [!TIP]
> **Localité des données avant tout.** Les alignements vivent sur `mp` (`mapped.cram`, ~20 à 46 Mo par
> souche). Il n'y a **pas d'index `.crai`**, donc pas d'extraction par région sans indexer une copie
> au préalable. Pour quelques souches, le flux direct qui a fonctionné :
> ```bash
> R=/data/current/run/resources/NC_002516.2.fasta   # ou NC_000962.3.fasta, NC_002677.1.fasta
> C=/data/current/run/references_results/NC_002516.2/<souche>/mapped.cram
> ssh mp "samtools view -b -T $R $C" | ssh mh 'cat > /Work/Users/cguyeux/smoke/<souche>.bam'
> ```
> (un seul passage, mp et mh ne se parlant pas directement). Pour une campagne de centaines de
> souches, installer panISa **sur `mp`** et calculer sur place : à 2,3 s par souche, tout le coût est
> dans le transfert. Voir `remote-compute` pour l'arbitrage et le VPN.

## Invocation

```bash
P=/Work/Users/cguyeux/envs/bacto
# BAM direct
$P/bin/panISa.py -o resultat.txt alignement.bam

# depuis un CRAM TBannotator : convertir d'abord (la référence est OBLIGATOIRE pour décoder un CRAM)
samtools view -b -T NC_000962.3.fasta mapped.cram > mapped.bam && $P/bin/panISa.py -o resultat.txt mapped.bam
```

Quatre options qui changent le résultat, avec leur défaut :

| option | défaut | effet |
|---|---|---|
| `-m` | 10 | lectures clippées minimum par borne. Le baisser augmente la sensibilité **et** les artefacts |
| `-s` | 20 | taille maximale de la répétition directe recherchée |
| `-q` | 20 | qualité d'alignement minimale |
| `-p` | 0.8 | proportion de consensus pour appeler une base de la bordure |

Les alignements sont documentés comme optimaux avec **bwa**, ce qui est justement le mappeur de la
chaîne TBannotator : les CRAM existants sont donc directement exploitables.

## Annotation des familles

`ISFinder_search.py` interroge **ISfinder en ligne**, et ce site est souvent injoignable (échec SSL
ou connexion, constaté deux fois en août 2026). En repli, passer par le skill `isfinder-offline`
(miroir GitHub statique, ~6000 IS, recherche par nom ou par blastn/blastp). `annotateISresult.py`
complète l'annotation à partir d'un génome de référence annoté.

## Choisir les souches : la profondeur commande

Le seuil `-m 10` (défaut) exige dix lectures clippées à une borne, ce qui est hors d'atteinte sur un
alignement peu profond. Mesures du 2026-08-17 sur `mp` :

| cohorte | profondeur observée | verdict |
|---|---|---|
| MTBC (`results/`) | **36× à 538×** | pleinement exploitable au défaut |
| *P. aeruginosa* (`references_results/NC_002516.2/`, 10 001 souches) | **154 / 195 à ≥ 20×** | exploitable après tri |
| *M. leprae* (`references_results/NC_002677.1/`, 710 souches) | **0,2× à 57×**, très hétérogène | tri indispensable |

Premier geste d'une campagne : trier sur `meandepth`, colonne 7 de `coverage_stats.tsv`, présent dans
chaque répertoire de souche. Sur un test à 7,8× de profondeur, `-m 10` a rendu **zéro site** et `-m 5`
un seul candidat, sans répétition inversée : c'est le comportement attendu, pas une panne.

> [!CAUTION]
> **Ne pas échantillonner la tête d'un listing pour juger une cohorte.** Les accessions sont
> ordonnées par dépôt, donc les vingt premières appartiennent au même BioProject et partagent sa
> profondeur. Vécu ici : les 20 premières souches de *P. aeruginosa* plafonnaient à 4-8×, ce qui
> donnait la cohorte pour inexploitable, alors que 79 % d'un échantillon de 195 dépasse 20×. Tirer
> large, ou lire la distribution complète, jamais le premier bloc.

## Garde-fous d'interprétation

> [!WARNING]
> **panISa rapporte des insertions PAR RAPPORT À LA RÉFÉRENCE.** Une IS présente chez la référence
> et absente de la souche n'est pas une insertion détectable ici : c'est une délétion, qui relève de
> la logique RD (couverture et signaux de clipping appariés), pas de celle-ci. Confondre les deux
> inverse le sens biologique du résultat.
>
> **Son profil d'artefacts est l'inverse de celui du variant calling.** La chaîne masque PE/PPE, IS
> et régions répétitives avant d'appeler des variants ; panISa exploite délibérément les lectures
> clippées que ces régions produisent. Un site rapporté dans une région répétée n'est donc pas
> automatiquement faux, mais il demande la validation IRL/IRR, pas seulement le compte de lectures.

Avant d'annoncer une IS nouvelle : vérifier qu'elle n'est pas déjà dans le panel de 22 IS de la
chaîne, la classer via `isfinder-offline`, et regarder si la littérature de l'espèce la décrit
(`lit-review`, et `tbmonitor-papers` pour le MTBC).

## Campagne à l'échelle : script et contrôle obligatoire

`mp:/data/cguyeux/panisa_campaign.sh` (versionné aussi comme référence de ce skill) traite une liste
de souches déjà mappées par la chaîne : conversion CRAM → BAM, indexation, panISa, puis une ligne de
résumé par souche. Points de conception à ne pas défaire :

- **Sélection d'abord.** `awk -F'\t' 'FNR==2 && $7>=20 && $6>=90 {split(FILENAME,a,"/"); print a[7]"\t"$7"\t"$6}'
  sur les `coverage_stats.tsv` : un seul `awk` sur 9 839 fichiers prend quelques secondes, alors qu'une
  boucle shell avec un `awk` par fichier dépasse les deux minutes et se fait tuer. **9 110 souches sur
  9 839** passent ce filtre pour *P. aeruginosa*.
- **Empreinte disque bornée.** Chaque travailleur réutilise UN BAM temporaire qu'il écrase
  (`samtools view -o`), soit ~45 Mo par travailleur au lieu de 45 Mo par souche. Aucune suppression de
  fichier n'est nécessaire, ce qui respecte la règle « jamais `rm` ».
- **Idempotence.** Une souche dont le fichier de sortie existe déjà est sautée : la campagne se
  relance sans tout refaire.
- **Rien n'est écrit dans `/data/current`** (propriété de `gsenelle`) : la référence est recopiée et
  indexée dans `/data/cguyeux/ref/`, parce que `samtools view -T` réclame un `.fai`.
- Parallélisme par découpage de la liste, `nice -n 10`, car `mp` n'a pas d'ordonnanceur et la machine
  est partagée. Débit mesuré : ~13 souches par minute à 8 travailleurs.

> [!CAUTION]
> **Le contrôle falsifiant n'est pas optionnel.** PAO1 est une référence lointaine pour une partie de
> l'espèce (génome accessoire massif) : une souche divergente produit des lectures clippées partout, et
> panISa les lit comme des sites d'insertion. Le script relève donc `n_sites` **et** `n_snp` par souche.
> Si les deux corrèlent, la table est dominée par l'artefact de référence et ne s'interprète pas comme
> un inventaire d'IS ; si elles ne corrèlent pas, le signal est propre. La colonne `n_sites_avec_IR`
> (sites validés par une répétition inversée) est le second filtre : un vrai IS en a une, un artefact
> de divergence rarement.
>
> Corollaire de cadrage : lancer la campagne complète **après** avoir lu cette corrélation sur un
> pilote, pas avant.

## Composition

`bactrline` (assemblage et caractérisation en amont, si on part de lectures brutes) →
**`panisa`** (mobilome ab initio) → `isfinder-offline` (familles) → `sci-figure` (figure des sites).
Pour la clonalité du même jeu de souches, voir `pymlst`.
