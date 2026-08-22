# Skills tiers : K-Dense `scientific-agent-skills`

Skills importés depuis un catalogue public tiers, isolés du canonique du dépôt.
Aucun de ces skills n'est de nous, aucun n'est évalué par les pairs.

## Source

- Dépôt : `https://github.com/k-dense-ai/scientific-agent-skills` (K-Dense Inc.)
- Commit épinglé : `7eb9c23c32ecf7f8c19cb45ded3150534ccefe6a` (2026-08-10T09:48:06Z)
- Arbre Git : `abd82b55f654ddfae003316007db2149d64a9463`
- Importé le : 2026-08-10
- Audit d'origine : cahier `mtbc/cahier_de_labo.md`, entrée 2026-08-10 ; pistes P9.1 à P9.7 ;
  méthode d'audit dans `~/.claude/knowledge/claude-plugins-aup.md` (section « Adoption de skills TIERS »).
- Contrôle Codex du 2026-08-22 : les 37 fichiers sous `skills/` ont le même `git blob sha`
  que les chemins `skills/<name>/...` du commit épinglé. Aucun fichier de skill n'a été édité.

Sur les 161 skills du catalogue, 4 sont importés. La règle est le cherry-pick : importer les 161
descriptions dégraderait le routage de déclenchement de nos 68 skills MTBC, dont les descriptions
sont finement calibrées. Ne rien ajouter ici sans un trou identifié.

## Skills importés

| Skill | Licence amont | Trou comblé | Piste |
|-------|---------------|-------------|-------|
| `etetoolkit` | GPL-3.0-or-later | Comparaison et édition de topologies (`raxml` infère, `itol` rend, `pastml` reconstruit des états, rien ne compare) | P9.1 |
| `genomic-coordinates` | MIT | Conventions 0-based/1-based, left-alignment d'indels, mismatch REF et nommage de contigs | P9.2 |
| `pymoo` | Apache-2.0 | Optimisation multi-objectif (fronts de Pareto), absente de nos skills | P9.3 |
| `statistical-power` | MIT | Puissance a priori et effet minimal détectable, en amont de `lineage-comparison` | P9.4 |

Les licences sont hétérogènes PAR SKILL malgré le MIT annoncé du dépôt. Sans effet pour un usage
interne. Bloquant si le plugin MTBC est un jour redistribué : `etetoolkit` est en GPL-3.0.

Textes de licence conservés localement :

- `LICENSE.upstream` : MIT du dépôt K-Dense au commit épinglé.
- `LICENSES/Apache-2.0.txt` : texte standard Apache-2.0, pour `pymoo`.
- `LICENSES/GPL-3.0.txt` : texte standard GPL-3.0, pour `etetoolkit` déclaré
  `GPL-3.0-or-later`.

## Non importés, volontairement

- `paperclip` : décision budgétaire en attente (aucun tarif public, cf. piste P9.5).
- `cobrapy` : retourné en direction de recherche, pas en outil (piste P10, close le 2026-08-10).
- Tier 2, sur besoin constaté seulement : `ontology-term-resolution`, `polars`, `networkx`,
  `latex-posters` (P9.6).
- Écartés avec raison écrite : cf. P9.7. Ne pas les réexaminer sans raison neuve.

## Pièges connus

`statistical-power` renvoie dans son corps vers deux skills K-Dense que nous n'avons pas importés,
`experimental-design` et `statistical-analysis`. Ces renvois sont des impasses : traiter ces demandes
avec nos skills (`lineage-comparison`, `challenge`) ou importer la cible si le besoin se confirme.

`genomic-coordinates` est écrit pour la génomique humaine (GRCh37, hg19, GRCh38, T2T, liftover).
Sa valeur pour nous est dans les conventions de format et la normalisation de variants, pas dans les
assemblages qu'il nomme. Le cas d'usage visé est P5.3, le système de coordonnées CO92 de
*Yersinia pestis* avec ses trois plasmides.

`etetoolkit` cible ETE4, qui n'est pas ETE3. Nos scripts MTBC existants utilisent ETE3
(`get_common_ancestor`, `set_outgroup`, `prune`), installé pour le Python système. ETE4 vit dans un
venv séparé, `~/venvs/ete4`, et ne remplace rien : voir la note de migration fournie par le skill,
`skills/etetoolkit/references/migration-ete3-to-ete4.md`. Ne pas convertir les scripts existants.

Installation d'ETE4 (faite le 2026-08-10, interpréteur `~/venvs/ete4/bin/python`) : PyPI ne publie
qu'une sdist pour 4.4.0, donc compilation Cython obligatoire, environ 20 minutes sous Python 3.14
avec les CFLAGS d'Arch (`-O3 -flto`). La lancer en tâche de fond. Deux différences d'API vérifiées
sur données réelles : `robinson_foulds` renvoie 7 valeurs (5 en ETE3), et un arbre `.raxml.bestTree`
étant non enraciné il faut `unrooted_trees=True`. Le CLI `ete4 compare` livré avec 4.4.0 est cassé
(il passe un argument `format=` supprimé du constructeur) : passer par l'API Python ou par
`skills/etetoolkit/scripts/tree_operations.py`, ce que le skill documente lui-même.

## Mise à jour

Le contenu est figé au commit ci-dessus, sans dépôt git local. Pour actualiser, re-télécharger les
mêmes chemins depuis un nouveau commit et mettre à jour le SHA de cette page :

gh api "repos/k-dense-ai/scientific-agent-skills/git/trees/<SHA>?recursive=1" --jq '.tree[] | select(.type=="blob") | select(.path|test("^skills/(etetoolkit|genomic-coordinates|statistical-power|pymoo)/")) | .path'

Puis un `curl` par chemin sur `https://raw.githubusercontent.com/k-dense-ai/scientific-agent-skills/<SHA>/<path>`.

## Règles

Ces fichiers sont du tiers : ne pas les éditer. Une correction locale serait écrasée à la première
mise à jour et rendrait indistinguable ce qui vient d'eux de ce qui vient de nous. Si un skill doit
être adapté, en faire un skill à nous dans le plugin adéquat et écarter celui-ci.

Comme pour tout skill, ne jamais éditer via un symlink : le canonique est ici.
