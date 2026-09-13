---
name: supp-tables
description: >-
  Cherche un gène, un locus tag, une accession ou tout motif dans les TABLES SUPPLÉMENTAIRES
  d'articles scientifiques — les .xlsx, .csv et .docx qu'aucun moteur plein texte n'indexe.
  Comble le troisième angle mort du rappel bibliographique, après l'écart résumé/plein texte et le
  gène rebaptisé : un gène peut être ABSENT du corps de tous les articles pertinents et PRÉSENT
  dans les tables de plusieurs d'entre eux. Récupère par Europe PMC, avec repli obligatoire par le
  préprint bioRxiv quand l'article n'est pas en accès ouvert, et rend chaque occurrence avec ses
  EN-TÊTES de colonnes. Porte son propre garde-fou : `rank` situe une valeur trouvée dans la
  distribution de sa propre table, parce qu'une ligne trouvée n'est pas un résultat.
  Use when: un gène ressort « sans littérature » alors que des jeux protéomiques, des cribles
  CRISPRi, des tables d'essentialité ou des sorties de GWAS le contiennent ; vérifier qu'un terme
  est réellement absent ; instruire un gène dark ; préparer un claim-check sur une donnée publiée.
---

# supp-tables — fouiller ce que la recherche plein texte ne voit pas

## Le problème que ce skill résout

La chaîne de rappel bibliographique a trois angles morts documentés, et deux seulement sont
couverts ailleurs. `tbmonitor` ne voit que les résumés. `europepmc_fulltext.py search` voit le
corps du texte, et c'est déjà un facteur 6,5 de rappel supplémentaire. **Ce skill couvre le
troisième : les tables supplémentaires, qu'aucun des deux n'indexe.**

L'angle mort n'est pas marginal, il est structurel. Les identifications protéomiques, les listes
de hits de GWAS, les tables d'essentialité, les sorties de cribles CRISPRi et les matrices
d'abondance vivent dans des classeurs Excel joints à l'article. Le corps du texte, lui, ne nomme
que les quelques gènes que les auteurs ont choisi de discuter. **Un gène peut donc être absent du
corps de TOUS les articles pertinents et présent dans les tables de plusieurs d'entre eux.**

Cas mesuré, à l'origine du skill (2026-09-07, projet `Rv2520c`) : la chaîne « Rv2520c » n'apparaît
dans le texte d'aucun des trois articles protéomiques qui portent les seules données empiriques
existantes sur la topologie de cette protéine, et se trouve dans les tables des trois. Une
recherche plein texte rendait zéro, proprement et faussement.

## Usage

```bash
S=~/docs/codes/claude_plugins/redac/skills/supp-tables/scripts/supp_tables.py

# le geste principal : un motif, des articles, les lignes qui le contiennent
python3 $S hunt "Rv2520c,I6XEI0" --dois 10.1128/spectrum.02277-24,10.1016/j.mcpro.2026.101555

# beaucoup d'articles : un identifiant par ligne (DOI, PMID ou PMCID indifféremment)
python3 $S hunt Rv1908c --dois-file dois.txt --out /tmp/supp

# séparer les deux temps quand on veut relancer plusieurs motifs sans retélécharger
python3 $S fetch --dois-file dois.txt --out /tmp/supp
python3 $S grep /tmp/supp "katG,P9WIE5"

# LE GARDE-FOU, à passer après tout hit numérique
python3 $S rank /tmp/supp/PMC11792546/table.xlsx --sheet Proteins --col 17 --needle I6XEI0
```

## Le garde-fou, et pourquoi il est dans le skill plutôt que dans la tête

**Une ligne trouvée dans une table n'est pas un résultat.** C'est la seule règle de ce skill, et
elle a été payée deux fois en septembre 2026 :

- un score de co-purification de `0,06 ± 0,06`, présenté par un article comme une identification,
  s'est révélé être **la médiane des protéines non caractérisées de sa propre table** (rang 78 sur
  94 par score, 84 sur 94 par nombre de spectres) ;
- un rapport d'enrichissement de **6,10** avec p ajustée de 0,098, qui franchissait le critère
  publié par ses auteurs, plaçait le gène **entre RpoC et RecA**, deux protéines strictement
  cytoplasmiques — et les auteurs eux-mêmes avaient montré, par étiquetage et cytométrie, que 5 de
  leurs 8 meilleurs candidats n'étaient pas en surface.

Dans les deux cas la valeur était réelle et la conclusion fausse. D'où `rank`, qui rend la médiane,
les quartiles et le rang de la ligne trouvée dans sa propre colonne. Et d'où la consigne que le
script affiche après chaque `hunt` fructueux : **chercher le SEUIL que les auteurs ont appliqué
dans le corps de leur article, et vérifier s'ils retiennent cette ligne.** Un critère publié franchi
n'est pas non plus une preuve : c'est ce que la validation orthogonale des auteurs, quand elle
existe, sert à mesurer.

## Les deux routes de récupération, et pourquoi la seconde est indispensable

**Voie 1, Europe PMC** : `/<PMCID>/supplementaryFiles` rend une archive de tous les fichiers
joints. C'est la voie propre — mais elle rend une archive **vide** pour un article non OA.

**Voie 2, le préprint** : la page `<doi>v1.supplementary-material` de bioRxiv ou medRxiv porte des
liens `.../DC<n>/embed/media-<n>.xlsx?download=true` librement téléchargeables. PMC, lui, sert
désormais ses fichiers derrière une porte de type proof-of-work (page « Preparing to download »,
cookie et JavaScript) qu'un client en ligne de commande ne franchit pas ; changer d'User-Agent n'y
fait rien.

**Retrouver le préprint est le point difficile, et aucune route évidente ne marche.** Mesuré le
2026-09-08 : la relation `has-preprint` de CrossRef est vide, `api.biorxiv.org/pubs/` ne connaît
pas le DOI publié, et Europe PMC ne relie pas les deux enregistrements. Surtout, **le titre change
souvent entre le préprint et la version publiée** — « Cell wall proteomics in live *M.
tuberculosis*... » est devenu « Proteomics from compartment-specific APEX2 labeling... » — donc une
recherche par titre rend zéro et paraît concluante. La route qui marche, et que le script
implémente : chercher les préprints du **premier auteur** sur une fenêtre de quatre ans, puis
confirmer par **recouvrement des listes d'auteurs**. Un titre bouge, une liste d'auteurs beaucoup
moins.

## Trois pièges de transfert, tous mesurés

**`curl` rend des fichiers tronqués avec un code de sortie 0** quand le système de fichiers de
destination est plein : 1,4 Mo au lieu de 10,5 ; 16 Ko au lieu de 7 Mo. Le script vérifie la taille
obtenue et refuse une archive qui ne s'ouvre pas. Ne jamais se fier au seul code de retour.

**bioRxiv limite le débit** et rend un HTTP 429 dès deux fichiers demandés coup sur coup. Sans
reprise, on perd silencieusement la moitié des tables d'un article. Le script réessaie quatre fois
avec attente croissante.

**Une ligne de table sans ses en-têtes n'est pas interprétable.** C'est le moment exact où l'on
invente un sens aux colonnes. Le script rend systématiquement la ligne AVEC la ligne d'en-têtes de
sa feuille.

## Ce que le skill ne fait pas

Il ne contourne aucun paywall : il utilise Europe PMC et les dépôts de préprints, tous deux
publics. Pour un article fermé sans préprint, il le dit et s'arrête — la suite relève de la cascade
d'accès légale de `literature-access` (TDM institutionnel, bibliothèque sous licence, contact
auteur).

Il ne remplace pas `europepmc_fulltext.py search`, il le complète : le corps du texte et les tables
sont deux corpus disjoints, et une revue à haut rappel a besoin des deux.

## Enchaînement

`tbmonitor-papers` (recensement par résumés) → `literature-access` / `europepmc_fulltext.py search`
(rappel par le corps) → **`supp-tables`** (rappel par les tables) → `claim-check` (vérification de
ce qu'on écrira).
