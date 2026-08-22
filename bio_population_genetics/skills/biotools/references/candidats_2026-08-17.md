# Triage du premier balayage bio.tools — 2026-08-17

Balayage de 16 termes (MTBC, mycobactéries, *Yersinia*, spoligotypage, MIRU-VNTR, mobilome,
prédiction de résistance, cgMLST) : **169 outils distincts**, dont 27 déjà mentionnés dans nos skills
ou notre base de connaissances, et **50 inconnus trouvés par un terme ciblant nos organismes**.

Ce fichier est le tri à la main de ces 50. Il n'est pas exhaustif du registre, et il périme : relancer
`biotools_scan.py --preset mtbc` pour la suite. Aucun de ces outils n'a été installé ni testé ; ce
sont des candidats, pas des recommandations validées.

## 1. À adopter en priorité (répondent à un besoin déjà identifié chez nous)

**RDscan** `rdscan`, pipeline Snakemake de détection de délétions et de régions de différence (RD)
dans les génomes MTBC. Intérêt réel : c'est une **implémentation indépendante d'un calcul que fait
déjà la chaîne TBannotator** (méthode profondeur + signaux de clipping, cf. `~/.claude/knowledge/
tuberculosis.md`). Un second avis sur les RD est le contrôle le moins cher pour une méthode maison
dont les seuils ont été fixés en interne.

**QuantTB** `quanttb` : identifie et quantifie les **infections mixtes** par SNP dans du WGS. La KB
note explicitement le besoin du signal sous-clonal (infections mixtes, hétérorésistance), que le
`bdd/` local ne conserve pas. Candidat direct.

**binoSHP / binoSNP** `binosnp` : workflow R de détection de **SNP de résistance à basse fréquence**
par modèle binomial dans du NGS MTBC. Même famille que QuantTB, angle hétérorésistance.

**pathotypr** `pathotypr` : classification de lignée et génotypage **piloté par vos propres marqueurs**
(« bring your own SNP marker »), hors ligne, agnostique du pathogène. C'est exactement la forme dont
nous avons besoin : la banque de marqueurs maison (`guyeux`) existe, et l'outil est transposable à
*M. leprae* ou *Yersinia* sans réécriture. À évaluer sérieusement.

**PANPASCO** `PANPASCO` : distances SNP **pan-génome** par paires pour les clusters de transmission
MTBC. Complète `snp-distance`, qui compare sur une référence unique et rate donc ce qui est absent de
H37Rv.

## 2. Bases de données et ressources à connaître (référence, pas outil de calcul)

| ressource | ID | intérêt |
|---|---|---|
| **NTM-DB** | `ntm-db` | base dédiée aux mycobactéries **non tuberculeuses** : nourrit directement le plugin `bio_bacteria` |
| **Mabellini** | `Mabellini` | protéome structural de ***M. abscessus***, cibles antimicrobiennes prospectives |
| **Leproma** | `leproma` | base génomique de ***M. leprae*** ; à croiser avec le skill `mycobacterium-leprae`, qui ne la mentionne pas |
| **SITVITBovis** | `sitvitbovis` | base et cartographie des cas ***M. bovis*** animaux et humains ; complète `sitvitweb` et `mbovis` |
| **Yersiniomics** | (voir fiche) | base multi-omique interactive du genre *Yersinia* |
| **Yersinia cgMLST genre entier** | (Ridom) | identification d'espèce et typage cgMLST sur tout le genre |
| **Y. enterocolitica cgMLST** | `iyersinia` | base et logiciel de surveillance génomique en France |
| **mycoprint** | `mycoprint` | interactome de H37Rv prédit par Domain Interaction Mapping ; à confronter à `mtbc-gene-network`, qui s'appuie sur STRING |
| **BacFITBase** | `BacFITBase` | pertinence des gènes bactériens **pendant l'infection** ; complète les jeux TnSeq d'essentialité déjà documentés |
| **TuberQ** | `tuberq` | druggabilité des protéines de *M. tuberculosis* |
| **TB Portals** | `TB_Portals` | consortium international, données cliniques et radiologiques appariées au génotype |

## 3. Génotypage complémentaire (surtout lectures longues)

**MIRUReader** `MIRUReader` (MIRU-VNTR 24 loci depuis des lectures longues) et **Galru** `galru`
(spoligotypage rapide depuis des lectures longues non corrigées) couvrent un angle que nos skills
`miru-vntr` et `crisprbuilder` n'ont pas : le Nanopore. **TGS-TB** `tgs-tb` fait spoligotypage plus
détection de phylogénie en une interface web. **lorikeet** `lorikeet`, **Nomenclature WS**
`nomenclature_ws`, **MSDB** `MSDB` (bases MLVA) et **MAC-INMV-SSR** `MAC-INMV-SSR` (génotypage du
complexe *M. avium*, dont *paratuberculosis*) complètent le tableau, ce dernier pour `bio_bacteria`.

## 4. Prédiction de résistance : à comparer, pas à adopter en aveugle

Huit outils indépendants de prédiction de résistance MTBC : **DrPRG** (graphes de référence),
**MTB++** (classifieur sur matrice de 31-mers), **GenTB**, **TB-ML** (cadre de comparaison de
méthodes), **Treesist-TB** (arbre de décision modifié), **Resistance Sniffer**, **PointFinder**
(meilleur traitement des indels et codons stop prématurés), **GenoMycAnalyzer** (espèce plus
résistance, tout le genre *Mycobacterium*).

Leur intérêt n'est pas de remplacer `resistance-profiler` mais de servir d'**étalons** : `TB-ML` est
explicitement un cadre de comparaison, donc le bon point d'entrée si l'on veut chiffrer notre propre
performance plutôt que l'affirmer.

## 5. Ce qu'il faut écarter, et pourquoi le dire

**Radiologie et dépistage clinique** : DecXpert, Qure.ai, ScreenTB, mtTB, COTS, ATBdiscrimination.
Vrais outils, hors de notre objet. Ils occupent une part notable des résultats sur « tuberculosis »,
d'où l'utilité de le noter une fois pour toutes.

**Faux amis « lineage barcode »** : BARtab, CellDestiny, TedSim font du **code-barres cellulaire** en
transcriptomique, aucun rapport avec un barcode de lignée bactérienne. Illustration du piège `q=`.

**Chimie et vaccins** : ChemTB, gdoq, mtbveb, Secret-AAR, ShinyOmics. Périmètre différent, à ne
rouvrir que si un projet le demande.

**Deux cas limites qui méritent mieux que « bruit »** : **nosoi** (simulateur stochastique de chaînes
de transmission, agent par agent) est un outil de **modèle nul** crédible pour tester une hypothèse de
transmission, et **iMarmot** (génomique comparative des marmottes) touche au **réservoir sauvage de
*Y. pestis*** en Asie centrale. Ni l'un ni l'autre n'est un outil MTBC, mais tous deux sont
défendables dans un projet précis.
