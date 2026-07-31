# Claude Plugins — Instructions

## Architecture des plugins

Neuf plugins partageant des skills via des symlinks. L'ex-plugin `bio/` a été scindé
en deux. Comptages vérifiés le 2026-07-31 (`find <plugin>/skills -maxdepth 1 -mindepth 1 -type d -not -type l | wc -l`) :

| Plugin | Rôle | Skills (canoniques + symlinks) |
|--------|------|-------------------------------|
| `bio_pathogens/` | Étude de recherche scientifique sur les pathogènes bactériens (MTBC, *M. leprae*, *Y. pestis*, *Helicobacter pylori*, résistance, lignages, BDD spécialisées) | 50 + 37 (transversaux + redac/) |
| `bio_population_genetics/` | Génétique des populations humaines (anciennes et modernes), archéologie, paléoclimat, langues, voyages historiques, plus l'outillage générique bioinfo/stats/ML/littérature | 52 + 3 (redac/) |
| `redac/` | Rédaction pure (LaTeX, slides, manuscrits) | 28 + 4 vers bio_population_genetics/ (`sci-figure`, `create-viz` alias, `geo-map`, `read-scientific-pdf`) |
| `bio_redac/` | Phase hybride analyse + rédaction | 1 réel (`phylo-history` version narration) + 117 symlinks |
| `ia/` | Statistiques, apprentissage automatique, géospatial, calcul scientifique | 14 + 3 vers bio_population_genetics/ (`scikit-learn`, `statsmodels`, `scientific-problem-selection`) |
| `ops/` | Déploiement, incidents, documentation technique | 3 + 1 |
| `multimedia/` | Synthèse vocale, sous-titrage, cinéma | 3 |
| `web/` | Design frontend, test d'applications web | 2 |
| `maboss/` | **Projet distinct** (modélisation booléenne CoLoMoTo/MaBoSS), hors collection MTBC | 12 |

Le skill `cahier-de-labo` est désormais **uniquement** à `~/.claude/skills/cahier-de-labo/` (version générique, multi-projets). Plus de copie dans aucun plugin.

**Dépendances hors dépôt.** Quelques skills renvoient à `~/.claude/skills/`
(`cahier-de-labo`, `init-project`) : ces références fonctionnent dans
l'environnement de Christophe mais **pas** pour un collaborateur qui clone le
dépôt. Ne pas les convertir en `${CLAUDE_PLUGIN_ROOT}` (les skills concernés ne
sont pas dans le dépôt) ; les mentionner comme optionnelles dans le corps du
skill.

## Cadrage AUP (CRITIQUE)

Toutes les descriptions de skills et de plugins liées à la tuberculose, aux pathogènes ou à la résistance antimicrobienne doivent **cadrer explicitement le contexte recherche scientifique académique**, pour éviter de déclencher à tort le classifieur d'usage acceptable d'Opus 4.7.

Pattern obligatoire dans le `description:` du frontmatter :
- Préfixer par : `Academic research toolkit for ...` ou `Academic research database client ...` ou `Academic literature reference ...`
- Mentionner : `peer-reviewed`, `published research`, `scientific publications`, `Guyeux group (FEMTO-ST)`
- Éviter sans cadrage : `drug resistance`, `outbreak`, `surveillance`, `pathogen` seul. Préférer : `antimicrobial-resistance allele frequencies`, `published research isolate`, `peer-reviewed pathogen-genomics literature`
- La même règle s'applique au `description:` du `plugin.json` des deux plugins bio_*

Skills déjà reformulés selon ce pattern : `resistance-profiler`, `mycobacterium-leprae`, `ncbi-pathogen-detection`, `pathogens-portal`, `tb-cli`. Si un autre skill MTBC déclenche un faux positif AUP en pratique, appliquer le même pattern.

## Outils d'audit du dépôt

```bash
python3 _audit/tools/audit_skills.py --detail   # frontmatter, chemins, doublons, style
python3 _audit/tools/dedash.py --dry-run        # tirets cadratin en prose
```

Lire l'en-tête de chaque script avant de s'y fier : ils documentent les
heuristiques qui produisent du bruit, et `dedash.py` explique pourquoi le
**demi-cadratin (–) ne doit jamais être converti** (c'est un séparateur
d'intervalle numérique, « 40 000–70 000 BP », pas un marqueur d'IA). Un décompte
de sortie est une liste de candidats à inspecter, pas un verdict. Dernier bilan
complet : `_audit/2026-07-31_revue_skill_par_skill.md`.

## Règle de synchronisation (CRITIQUE)

**`bio_redac/` ne contient que des symlinks** (sauf `phylo-history`). Il ne faut JAMAIS y créer de fichiers réels.

Quand un skill est modifié :
1. **Identifier le canonical** via la table d'ownership ci-dessous, ou via `readlink` sur le symlink
2. **Modifier le fichier dans le répertoire canonical** (le symlink propage automatiquement)
3. **Si c'est un nouveau skill** : le créer dans son canonical (bio_pathogens, bio_population_genetics, ou redac), puis ajouter les symlinks nécessaires

### Ajouter un nouveau skill et propager dans les autres plugins

**Les symlinks doivent être RELATIFS**, jamais absolus : un lien absolu casse le
dépôt dès qu'il est cloné ailleurs (c'est la conversion de 167 liens qui a permis
la publication sur GitHub). Se placer dans le répertoire `skills/` cible avant de
créer le lien, et vérifier avec `find . -xtype l` qu'aucun lien n'est cassé.

```bash
cd /home/christophe/docs/codes/claude_plugins

# Nouveau skill bio_pathogens (canonique)
mkdir bio_pathogens/skills/<name>          # ... écrire SKILL.md
ln -s ../../bio_pathogens/skills/<name> bio_redac/skills/<name>

# Nouveau skill transversal (canonique dans bio_population_genetics)
mkdir bio_population_genetics/skills/<name>
ln -s ../../bio_population_genetics/skills/<name> bio_pathogens/skills/<name>
ln -s ../../bio_population_genetics/skills/<name> bio_redac/skills/<name>

# Nouveau skill redac (canonique)
mkdir redac/skills/<name>
ln -s ../../redac/skills/<name> bio_redac/skills/<name>
# (selon le besoin :) ln -s ../../redac/skills/<name> bio_pathogens/skills/<name>

# Contrôle : aucun lien cassé, aucun lien absolu
find . -xtype l -not -path "./.git/*"
find */skills -maxdepth 1 -type l -lname '/*'
```

### Chemins à l'intérieur d'un SKILL.md

Pour référencer un script d'un skill (le sien ou celui d'un skill voisin),
utiliser `${CLAUDE_PLUGIN_ROOT}/skills/<skill>/scripts/<f>.py` et **jamais** un
chemin absolu `~/docs/codes/claude_plugins/...` : le symlink présent dans chaque
plugin fait résoudre correctement `${CLAUDE_PLUGIN_ROOT}` quel que soit le plugin
qui invoque le skill, et le chemin reste valide après clonage.

```bash
# détecter les régressions
grep -rn "docs/codes/claude_plugins/[a-z_]*/skills/" --include=SKILL.md .
```

Les chemins absolus vers les **données** du groupe (`~/docs/codes/mtbc/...`,
`~/docs/cv/`, `/home/christophe/venvs/...`) sont eux légitimes : ils désignent
l'environnement de travail, pas le dépôt.

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
| `sci-figure` | bio_population_genetics/ | bio_pathogens/, redac/, bio_redac/ |
| `create-viz` | alias : symlink vers `sci-figure` | bio_pathogens/, redac/, bio_redac/ |
| `geo-map` | bio_population_genetics/ | bio_pathogens/, redac/, bio_redac/ |
| `read-scientific-pdf` | bio_population_genetics/ | bio_pathogens/, redac/, bio_redac/ |
| `fig-check` | redac/ | bio_redac/ |
| `supp-check` | redac/ | bio_redac/ |
| `cahier-de-labo` | `~/.claude/skills/` (hors plugins) | aucun |
| `mbovis` | bio_pathogens/ | bio_redac/ |
| `scikit-learn` | bio_population_genetics/ | bio_pathogens/, bio_redac/, ia/ |
| `statsmodels` | bio_population_genetics/ | bio_pathogens/, bio_redac/, ia/ |
| `scientific-problem-selection` | bio_population_genetics/ | bio_pathogens/, bio_redac/, ia/ |

`ia/` portait jusqu'au 2026-07-31 des **copies réelles** de ces trois skills, en
doublon avec bio_population_genetics/. Elles ont été remplacées par des symlinks :
deux copies identiques divergent silencieusement à la première modification.

### Couplage sci-figure ↔ geo-map

`sci-figure/scripts/figstyle.py` lit la table `JOURNAL_PRESETS` **directement dans** `geo-map/scripts/geo_map.py` (analyse syntaxique, sans import), pour que les figures de données et les cartes d'un même article sortent aux mêmes largeur, police et dpi. Renommer cette table ou déplacer `geo_map.py` fait basculer `figstyle.py` sur sa copie de repli, silencieusement. Après toute modification des presets de `geo-map`, lancer `python3 bio_population_genetics/skills/sci-figure/scripts/figstyle.py --check-sync` : il sort en code 1 si les deux ont divergé, 2 si `geo-map` est devenu introuvable.

Transversaux à canonique bio_population_genetics/ et symlinkés dans bio_pathogens/ et bio_redac/ : `biopython`, `pysam`, `scikit-bio`, `scikit-learn`, `scanpy`, `statsmodels`, `rdkit`, `iqtree-lsd2`, `bayesian-skyline`, `beast2-phylogeography`, `pastml`, `itol`, `nextstrain`, `nextflow-development`, `openalex`, `europe-pmc`, `pubmed-database`, `pubtator`, `bioc-pmc`, `scientific-problem-selection`, `ontologies`, `tooluniverse-sequence-retrieval`, `bioskills`, `migration-data`, `atlantic-voyages`, `indian-ocean-voyages`, `slavevoyages`, `domestication-pathways`.

## Agents

Les 4 agents (`bioinfo-analyst`, `manuscript-orchestrator`, `manuscript-reviewer`, `manuscript-reviser`) sont uniques à `bio_redac/agents/` et n'existent pas dans les autres plugins.

## Activation sélective pour éviter les déclenchements AUP

Pour une session de travail purement génétique des populations / archéologie / paléoclimat (sans MTBC), **n'activer que `bio_population_genetics/`** (ainsi que `redac/` et `bio_redac/` selon le besoin) : aucune description chargée ne contient de vocabulaire pathogène, ce qui minimise le risque de faux positif AUP. Activer `bio_pathogens/` uniquement quand le travail porte effectivement sur les pathogènes.
