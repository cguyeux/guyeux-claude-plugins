# Claude Plugins — Instructions

## Architecture des plugins

Quatre plugins partageant des skills via des symlinks. L'ex-plugin `bio/` a été scindé en deux :

| Plugin | Rôle | Skills (canonique + symlinks) |
|--------|------|-------------------------------|
| `bio_pathogens/` | Étude de recherche scientifique sur les pathogènes bactériens (MTBC, *M. leprae*, *Y. pestis*, *Helicobacter pylori*, résistance, lignages, BDD spécialisées) | 37 canoniques + ~35 symlinks (transversaux + redac/) |
| `bio_population_genetics/` | Génétique des populations humaines (anciennes et modernes), archéologie, paléoclimat, langues, voyages historiques, plus l'outillage générique bioinfo/stats/ML/littérature | 49 canoniques + 3 symlinks (redac/) |
| `redac/` | Rédaction pure (LaTeX, slides, manuscrits) | 28 canoniques + symlinks vers bio_population_genetics/ pour `create-viz`, `seaborn`, `geo-map`, `read-scientific-pdf` |
| `bio_redac/` | Phase hybride analyse + rédaction | ~104 symlinks + 1 réel (`phylo-history` version narration) |

Le skill `cahier-de-labo` est désormais **uniquement** à `~/.claude/skills/cahier-de-labo/` (version générique, multi-projets). Plus de copie dans aucun plugin.

## Cadrage AUP (CRITIQUE)

Toutes les descriptions de skills et de plugins liées à la tuberculose, aux pathogènes ou à la résistance antimicrobienne doivent **cadrer explicitement le contexte recherche scientifique académique**, pour éviter de déclencher à tort le classifieur d'usage acceptable d'Opus 4.7.

Pattern obligatoire dans le `description:` du frontmatter :
- Préfixer par : `Academic research toolkit for ...` ou `Academic research database client ...` ou `Academic literature reference ...`
- Mentionner : `peer-reviewed`, `published research`, `scientific publications`, `Guyeux group (FEMTO-ST)`
- Éviter sans cadrage : `drug resistance`, `outbreak`, `surveillance`, `pathogen` seul. Préférer : `antimicrobial-resistance allele frequencies`, `published research isolate`, `peer-reviewed pathogen-genomics literature`
- La même règle s'applique au `description:` du `plugin.json` des deux plugins bio_*

Skills déjà reformulés selon ce pattern : `resistance-profiler`, `mycobacterium-leprae`, `ncbi-pathogen-detection`, `pathogens-portal`, `tb-cli`. Si un autre skill MTBC déclenche un faux positif AUP en pratique, appliquer le même pattern.

## Règle de synchronisation (CRITIQUE)

**`bio_redac/` ne contient que des symlinks** (sauf `phylo-history`). Il ne faut JAMAIS y créer de fichiers réels.

Quand un skill est modifié :
1. **Identifier le canonical** via la table d'ownership ci-dessous, ou via `readlink` sur le symlink
2. **Modifier le fichier dans le répertoire canonical** (le symlink propage automatiquement)
3. **Si c'est un nouveau skill** : le créer dans son canonical (bio_pathogens, bio_population_genetics, ou redac), puis ajouter les symlinks nécessaires

### Ajouter un nouveau skill et propager dans les autres plugins

```bash
PLUGINS=/home/christophe/docs/codes/claude_plugins
# Nouveau skill bio_pathogens (canonique)
mkdir $PLUGINS/bio_pathogens/skills/<name> && # ... écrire SKILL.md
ln -s $PLUGINS/bio_pathogens/skills/<name> $PLUGINS/bio_redac/skills/<name>

# Nouveau skill transversal (canonique dans bio_population_genetics, symlink vers bio_pathogens et bio_redac)
mkdir $PLUGINS/bio_population_genetics/skills/<name>
ln -s $PLUGINS/bio_population_genetics/skills/<name> $PLUGINS/bio_pathogens/skills/<name>
ln -s $PLUGINS/bio_population_genetics/skills/<name> $PLUGINS/bio_redac/skills/<name>

# Nouveau skill redac (canonique)
mkdir $PLUGINS/redac/skills/<name>
ln -s $PLUGINS/redac/skills/<name> $PLUGINS/bio_redac/skills/<name>
# (selon le besoin :) ln -s ... $PLUGINS/bio_pathogens/skills/<name>
# (selon le besoin :) ln -s ... $PLUGINS/bio_population_genetics/skills/<name>
```

### Exception : phylo-history

Deux versions intentionnellement différentes :
- `bio_pathogens/skills/phylo-history` — version diagnostic (analyse de placement phylogénétique)
- `bio_redac/skills/phylo-history` — version narration (paragraphe pour manuscrit)

Ce sont les seuls skills à maintenir manuellement en parallèle.

## Ownership canonique des skills partagés

| Skill | Canonical dans | Symlinks dans |
|-------|---------------|---------------|
| `reviewer-response` | redac/ | bio_pathogens/, bio_population_genetics/, bio_redac/ |
| `claim-check` | redac/ | bio_pathogens/, bio_population_genetics/, bio_redac/ |
| `lit-review` | redac/ | bio_pathogens/, bio_population_genetics/, bio_redac/ |
| `create-viz` | bio_population_genetics/ | bio_pathogens/, redac/, bio_redac/ |
| `seaborn` | bio_population_genetics/ | bio_pathogens/, redac/, bio_redac/ |
| `geo-map` | bio_population_genetics/ | bio_pathogens/, redac/, bio_redac/ |
| `read-scientific-pdf` | bio_population_genetics/ | bio_pathogens/, redac/, bio_redac/ |
| `fig-check` | redac/ | bio_redac/ |
| `supp-check` | redac/ | bio_redac/ |
| `cahier-de-labo` | `~/.claude/skills/` (hors plugins) | aucun |
| `mbovis` | bio_pathogens/ | bio_redac/ |

Transversaux à canonique bio_population_genetics/ et symlinkés dans bio_pathogens/ et bio_redac/ : `biopython`, `pysam`, `scikit-bio`, `scikit-learn`, `scanpy`, `statsmodels`, `rdkit`, `iqtree-lsd2`, `bayesian-skyline`, `beast2-phylogeography`, `pastml`, `itol`, `nextstrain`, `nextflow-development`, `openalex`, `europe-pmc`, `pubmed-database`, `pubtator`, `bioc-pmc`, `scientific-problem-selection`, `ontologies`, `tooluniverse-sequence-retrieval`, `bioskills`, `migration-data`, `atlantic-voyages`, `indian-ocean-voyages`, `slavevoyages`, `domestication-pathways`.

## Agents

Les 4 agents (`bioinfo-analyst`, `manuscript-orchestrator`, `manuscript-reviewer`, `manuscript-reviser`) sont uniques à `bio_redac/agents/` et n'existent pas dans les autres plugins.

## Activation sélective pour éviter les déclenchements AUP

Pour une session de travail purement génétique des populations / archéologie / paléoclimat (sans MTBC), **n'activer que `bio_population_genetics/`** (ainsi que `redac/` et `bio_redac/` selon le besoin) : aucune description chargée ne contient de vocabulaire pathogène, ce qui minimise le risque de faux positif AUP. Activer `bio_pathogens/` uniquement quand le travail porte effectivement sur les pathogènes.
