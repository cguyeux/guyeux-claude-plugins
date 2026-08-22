# Claude Plugins — Instructions

## Architecture des plugins

Onze plugins partageant des skills via des symlinks. L'ex-plugin `bio/` a été scindé
en deux. Comptages vérifiés le 2026-08-21 (`find <plugin>/skills -maxdepth 1 -mindepth 1 -type d -not -type l | wc -l`) :

| Plugin | Rôle | Skills (canoniques + symlinks) |
|--------|------|-------------------------------|
| `bio_pathogens/` | Étude de recherche scientifique du MTBC stricto sensu : chaîne TBannotator, lignages, variants, phylogénomique et littérature spécialisée | 57 + 29 |
| `bio_bacteria/` | **Bactéries hors MTBC stricto sensu** : mycobactéries non tuberculeuses (*M. abscessus*, *M. avium*), autres genres. Assemblage et caractérisation, clonalité cgMLST, mobilome ab initio | 9 + 15 |
| `bio_population_genetics/` | Génétique des populations humaines (anciennes et modernes), archéologie, paléoclimat, langues, voyages historiques, plus l'outillage générique bioinfo/stats/ML/littérature | 55 + 3 (redac/) |
| `redac/` | Rédaction pure (LaTeX, slides, manuscrits) | 29 + 4 vers bio_population_genetics/ (`sci-figure`, `create-viz` alias, `geo-map`, `read-scientific-pdf`) |
| `bio_redac/` | Phase hybride analyse + rédaction | 1 réel (`phylo-history` version narration) + 147 symlinks |
| `ia/` | Statistiques, apprentissage automatique, géospatial, calcul scientifique | 14 + 4 vers bio_population_genetics/ (`scikit-learn`, `statsmodels`, `scientific-problem-selection`, `remote-compute`) |
| `ops/` | Déploiement, incidents, documentation technique | 4 + 2 |
| `multimedia/` | Synthèse vocale, sous-titrage, cinéma | 5 |
| `web/` | Design frontend, test d'applications web | 2 |
| `maboss/` | **Projet distinct** (modélisation booléenne CoLoMoTo/MaBoSS), hors collection MTBC | 12 |
| `droit/` | **Domaine distinct**, droit français, notes et citations vérifiées à leurs sources officielles | 1 |

Le skill `cahier-de-labo` est désormais **uniquement** à `~/.claude/skills/cahier-de-labo/` (version générique, multi-projets). Plus de copie dans aucun plugin.

**`external/` n'est PAS un plugin.** Ce répertoire héberge des skills TIERS importés d'un catalogue
public, un sous-répertoire par fournisseur (`external/kdense/` pour K-Dense `scientific-agent-skills`,
4 skills importés le 2026-08-10). Ils sont figés à un commit amont, hors marketplace, et **ne doivent
jamais être édités** : une correction locale serait écrasée à la prochaine mise à jour et brouillerait
la frontière entre ce qui vient d'eux et ce qui vient de nous. Chaque fournisseur porte son
`PROVENANCE.md` (commit épinglé, licence par skill, pièges connus, procédure de mise à jour). La règle
d'adoption est le cherry-pick : jamais d'installation en masse, sous peine de dégrader le routage de
déclenchement de nos skills. Les outils d'audit ci-dessous ne couvrent pas `external/`, c'est voulu.

**Dépendances hors dépôt.** Quelques skills renvoient à `~/.claude/skills/`
(`cahier-de-labo`, `init-project`) : ces références fonctionnent dans
l'environnement de Christophe mais **pas** pour un collaborateur qui clone le
dépôt. Ne pas les convertir en `${CLAUDE_PLUGIN_ROOT}` (les skills concernés ne
sont pas dans le dépôt) ; les mentionner comme optionnelles dans le corps du
skill.

## Installation locale : marketplace, pas miroir de symlinks

Le dépôt **est** un marketplace (`.claude-plugin/marketplace.json`, nom `guyeux-claude-plugins`,
onze `plugin.json`). C'est la seule voie correcte pour rendre les skills visibles dans un projet :

```bash
claude plugin marketplace add ~/docs/codes/claude_plugins
claude plugin install bio_pathogens@guyeux-claude-plugins -s user -y     # 86 skills actifs
claude plugin install redac@guyeux-claude-plugins -s user -y             #  33 skills, ~7,1 k tok
claude plugin list ; claude plugin details bio_pathogens                 # inventaire + coût projeté
claude plugin disable bio_pathogens                                      # session popgen pure (AUP)
```

> [!WARNING]
> **Ne JAMAIS revenir à un miroir `.claude/skills` de symlinks vers ce dépôt.** C'était le montage
> des projets de `~/docs/codes/mtbc/` jusqu'au 2026-08-17 : 78 liens créés à la main, pour 173 skills
> canoniques, donc **95 skills muets** sans le moindre message d'erreur. Un skill absent ne se
> déclenche pas, ce qui est indiscernable d'un skill qui a jugé la tâche hors de son périmètre : la
> dérive ne se voit qu'en cherchant un skill précis et en ne le trouvant pas. Deuxième défaut du
> miroir : `${CLAUDE_PLUGIN_ROOT}` n'est défini que pour un skill chargé **comme plugin**, alors
> qu'une vingtaine de SKILL.md l'utilisent pour leurs chemins de scripts. Le miroir a été retiré
> (74 liens), à l'exception des quatre skills `external/kdense`, qui n'appartiennent à aucun plugin
> et n'ont donc pas d'autre voie d'accès. `_audit/tools/sync_project_skills.py` reste disponible pour
> un projet qui voudrait délibérément un sous-ensemble choisi.

**Choix des plugins à activer.** `bio_pathogens` porte déjà les transversaux et une partie de
`redac/` par symlinks : `bio_pathogens` + `redac` couvre 112 noms de skills, dont 7 comptés deux fois
(`claim-check`, `create-viz`, `geo-map`, `lit-review`, `read-scientific-pdf`, `reviewer-response`,
`sci-figure`). `bio_redac` couvre désormais ces 112 noms et 36 autres, mais ses 147 symlinks en font
le plugin le plus large. Ne l'activer que lorsqu'une session a réellement besoin de la phase hybride
analyse et rédaction, pas comme sélection globale par défaut.

### Frontière `bio_pathogens` / `bio_bacteria` (créée le 2026-08-17)

`bio_pathogens` reste le plugin du **MTBC stricto sensu** : sa chaîne TBannotator, ses lignées, ses
barcodes SNP, ses ~136 800 souches annotées. `bio_bacteria` prend tout le reste du monde bactérien,
là où les méthodes diffèrent réellement et non par simple changement d'organisme :

- le **cgMLST** (`pymlst`) est la référence de clonalité hors MTBC, alors que le MTBC quasi clonal se
  lit par barcodes de lignée : y appliquer MLST donnerait un résultat interprétable de travers ;
- l'**assemblage** (`bactrline`) est nécessaire quand aucune chaîne pré-analysée n'existe, ce qui est
  le cas général hors MTBC ;
- le **mobilome ab initio** (`panisa`) trouve les IS que le panel de 22 IS du MTBC ne peut pas voir.
  Constat qui a motivé la scission : `mp:/data/current/run/references_results/` porte déjà **10 001
  souches de *P. aeruginosa*** (NC_002516.2) et **710 de *M. leprae*** (NC_002677.1) passées dans la
  chaîne, avec leurs `mapped.cram`, et leur `coverage_report_is.bed.tsv` **ne contient que l'en-tête**,
  le panel d'IS étant spécifique du MTBC. Gisement mesuré, pas supposé : sur un échantillon de 195
  souches de *P. aeruginosa*, **154 dépassent 20× de profondeur**, donc exploitables par panISa au
  seuil par défaut ; *M. leprae* est hétérogène (0,2× à 57×) et demande un filtrage. Premier geste
  d'une campagne : trier sur `meandepth` de `coverage_stats.tsv`.

`panisa` est le seul des trois symlinké dans `bio_pathogens`, parce que le cas « IS du MTBC absente du
panel des 22 » existe bel et bien. `pymlst` et `bactrline` n'y sont pas, volontairement.
`enterobase`, `helicobacter-pylori-phylogeography`, `mycobacterium-leprae`,
`ncbi-pathogen-detection` et `yersinia-resources` sont également canoniques dans `bio_bacteria` ;
`bio_redac` les consomme par symlinks relatifs. `mbovis` et `triangulate-route` restent désactivés
sous `bio_pathogens/skills_disabled` et ne doivent avoir aucun lien dans un plugin actif.

### Export pérenne vers Codex

Codex ne consomme pas le marketplace Claude. Les skills retenus pour les sessions
Codex sont déclarés dans `codex_skills.json`, puis exposés par liens symboliques
dans `~/.codex/skills` avec `_audit/tools/sync_codex_skills.py --apply`.
`canon_skills.json` résout chaque nom vers son unique répertoire réel : aucune
copie de `SKILL.md` n'est entretenue en parallèle. Après un ajout ou un déplacement,
relancer dans l'ordre `generate_canon_skills.py`, puis `sync_codex_skills.py`.
Le synchroniseur n'écrase jamais un chemin divergent et n'effectue aucun élagage.

## Cadrage AUP (CRITIQUE)

Toutes les descriptions de skills et de plugins liées à la tuberculose, aux pathogènes ou à la résistance antimicrobienne doivent **cadrer explicitement le contexte recherche scientifique académique**, pour éviter de déclencher à tort le classifieur d'usage acceptable d'Opus 4.7.

Pattern obligatoire dans le `description:` du frontmatter :
- Préfixer par : `Academic research toolkit for ...` ou `Academic research database client ...` ou `Academic literature reference ...`
- Mentionner : `peer-reviewed`, `published research`, `scientific publications`, `Guyeux group (FEMTO-ST)`
- Éviter sans cadrage : `drug resistance`, `outbreak`, `surveillance`, `pathogen` seul. Préférer : `antimicrobial-resistance allele frequencies`, `published research isolate`, `peer-reviewed pathogen-genomics literature`
- La même règle s'applique au `description:` du `plugin.json` des deux plugins bio_*

Skills déjà reformulés selon ce pattern : `resistance-profiler`, `mycobacterium-leprae`, `ncbi-pathogen-detection`, `pathogens-portal`, `tb-cli`. Si un autre skill MTBC déclenche un faux positif AUP en pratique, appliquer le même pattern.

### Veille outillage : ce que bio.tools a apporté (2026-08-17)

Premier balayage du registre ELIXIR par le skill `biotools` : 169 outils, 27 déjà chez nous,
**50 inconnus** pertinents. Le triage complet est dans
`bio_population_genetics/skills/biotools/references/candidats_2026-08-17.md`. Ce qui en a été tiré :

- **quatre skills forgés là où il n'existait AUCUNE couverture** : `rd-detection` (régions de
  différence, cœur de TBannotator jamais recoupé jusqu'ici), `mixed-infection` (QuantTB + binoSNP),
  `yersinia-resources` (le genre n'apparaissait que de biais dans 13 skills), `ntm-resources`
  (mycobactéries non tuberculeuses, plugin `bio_bacteria`) ;
- **neuf greffes dans des skills existants** plutôt que neuf skills de plus : PANPASCO dans
  `snp-distance`, MIRUReader dans `miru-vntr`, Galru/TGS-TB/lorikeet dans `crisprbuilder`, Leproma dans
  `mycobacterium-leprae`, SITVITBovis dans `mbovis`, MycoPrint dans `mtbc-gene-network`,
  BacFITBase/TuberQ dans `mtbc-gene`, pathotypr dans `mtbc-lineages`, les huit prédicteurs de
  résistance dans `resistance-profiler`.

Règle qui en découle : **un outil trouvé se greffe dans le skill du domaine ; un skill neuf ne se crée
que si le domaine n'est couvert par aucun**. Chaque skill ajoute sa description au budget toujours
chargé de la session, un plugin qui double de taille se paie à chaque prompt.

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
| `mbovis` | désactivé sous bio_pathogens/skills_disabled/ | aucun |
| `panisa` | bio_bacteria/ | bio_pathogens/, bio_redac/ |
| `pymlst`, `bactrline` | bio_bacteria/ | bio_redac/ |
| `scikit-learn` | bio_population_genetics/ | bio_pathogens/, bio_redac/, ia/ |
| `statsmodels` | bio_population_genetics/ | bio_pathogens/, bio_redac/, ia/ |
| `scientific-problem-selection` | bio_population_genetics/ | bio_pathogens/, bio_redac/, ia/ |

`ia/` portait jusqu'au 2026-07-31 des **copies réelles** de ces trois skills, en
doublon avec bio_population_genetics/. Elles ont été remplacées par des symlinks :
deux copies identiques divergent silencieusement à la première modification.

### Couplage sci-figure ↔ geo-map

`sci-figure/scripts/figstyle.py` lit la table `JOURNAL_PRESETS` **directement dans** `geo-map/scripts/geo_map.py` (analyse syntaxique, sans import), pour que les figures de données et les cartes d'un même article sortent aux mêmes largeur, police et dpi. Renommer cette table ou déplacer `geo_map.py` fait basculer `figstyle.py` sur sa copie de repli, silencieusement. Après toute modification des presets de `geo-map`, lancer `python3 bio_population_genetics/skills/sci-figure/scripts/figstyle.py --check-sync` : il sort en code 1 si les deux ont divergé, 2 si `geo-map` est devenu introuvable.

Transversaux à canonique bio_population_genetics/ et actuellement symlinkés dans `bio_pathogens/` : `bayesian-skyline`, `beast2-phylogeography`, `bioc-pmc`, `bioskills`, `biotools`, `boltz`, `create-viz`, `esm-atlas-cli`, `europe-pmc`, `geo-map`, `iqtree-lsd2`, `itol`, `nextflow-development`, `nextstrain`, `ontologies`, `openalex`, `pastml`, `pubmed-database`, `pubtator`, `pysam`, `read-scientific-pdf`, `remote-compute`, `sci-figure`, `scientific-problem-selection` et `tooluniverse-sequence-retrieval`.

Onze autres transversaux restent explicitement désactivés dans `bio_pathogens/skills_disabled` :
`atlantic-voyages`, `biopython`, `domestication-pathways`, `indian-ocean-voyages`, `migration-data`,
`rdkit`, `scanpy`, `scikit-bio`, `scikit-learn`, `slavevoyages` et `statsmodels`. Leur présence dans
`bio_population_genetics` ou `bio_redac` ne les réactive pas dans `bio_pathogens`.

## Agents

Les 4 agents (`bioinfo-analyst`, `manuscript-orchestrator`, `manuscript-reviewer`, `manuscript-reviser`) sont uniques à `bio_redac/agents/` et n'existent pas dans les autres plugins.

## Activation sélective pour éviter les déclenchements AUP

Pour une session de travail purement génétique des populations / archéologie / paléoclimat (sans MTBC), **n'activer que `bio_population_genetics/`** (ainsi que `redac/` et `bio_redac/` selon le besoin) : aucune description chargée ne contient de vocabulaire pathogène, ce qui minimise le risque de faux positif AUP. Activer `bio_pathogens/` uniquement quand le travail porte effectivement sur les pathogènes.

## Plugin `droit/` (créé le 2026-08-17)

Domaine : **droit français** (public, constitutionnel, pénal, nationalité et citoyenneté).
**Référente du domaine : Camille Aynès** (MCF droit public, Paris Nanterre). Les conventions du
plugin sont établies par relevé sur sa thèse (Dalloz, 2022) et ses articles récents, jamais
reconstruites de mémoire ; toute évolution se décide avec elle.

| Skill | Rôle |
|---|---|
| `notes-et-citations` | Conventions de l'appareil de notes d'un écrit juridique, **à exécuter AVANT toute production de livrable**, et vérification de chaque décision ou texte normatif à la source officielle. Norme détaillée dans `references/norme-aynes.md`. |

Deux principes qui expliquent la forme du plugin :

- **Le skill est un préalable, pas une relecture.** Une convention de citation adoptée en cours de
  rédaction oblige à reprendre tout ce qui précède, et une référence vérifiée après coup ne l'est
  presque jamais. D'où le déclenchement en amont, écrit dans la description et rappelé dans le
  `CLAUDE.md` des projets de droit.
- **La norme vit dans `references/`, pas dans le `SKILL.md`.** Le SKILL.md porte la procédure et les
  modes d'échec ; le relevé détaillé (formes exactes par type de source, abréviations, variantes
  attestées) est chargé à la demande. Cela permet de faire évoluer la norme sans toucher au skill,
  et de tracer d'où vient chaque règle.

**Activation par PROJET, jamais globale.** `init_project.py` classe le domaine et écrit
`<projet>/.claude/settings.json` avec `droit@guyeux-claude-plugins`. Raison : la KB
`claude-plugins-aup` a établi que les descriptions de skills s'injectent dans le prompt système de
**toutes** les sessions ; un plugin de droit chargé pendant une session de phylogénomique n'apporte
rien et alourdit le contexte.
