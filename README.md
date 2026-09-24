# Claude Plugins : groupe Guyeux (FEMTO-ST)

Collection de plugins [Claude Code](https://docs.claude.com/en/docs/claude-code) développés par Christophe Guyeux (Institut FEMTO-ST, CNRS UMR 6174, Université Marie et Louis Pasteur, Besançon) pour la recherche scientifique académique : phylogénomique évolutive des pathogènes bactériens clonaux, génétique des populations humaines, rédaction scientifique, et outillage transverse (bioinformatique, structure des protéines, statistiques, visualisation, revue de littérature).

Le périmètre est multi-genres. La collection a été bâtie sur le complexe *Mycobacterium tuberculosis*, qui en reste l'exemple le plus outillé, mais les projets de recherche du groupe couvrent aussi *Yersinia* et *Leptospira*. Ce qui change d'un genre à l'autre n'est pas la méthode, c'est le génome de référence, la nomenclature de branches et la base de souches.

Documentation complète, skill par skill (raison d'être et compétences) : **[dossier `docs/`](docs/README.md)**. Chaque plugin ci-dessous est aussi lié directement à sa page.

## Plugins

Dix-sept plugins organisés en trois couches depuis la refonte du 2026-09-15. Chaque skill vit dans exactement un plugin.

### Domaines scientifiques

| Plugin | Rôle |
|--------|------|
| [mtbc](docs/mtbc.md) | Pile de données du complexe *Mycobacterium tuberculosis* : chaîne TBannotator, base de souches, autorité de lignées et barcode, catalogue de résistance de l'OMS, SITVIT, Atlas de gènes. |
| [bacteria](docs/bacteria.md) | Génomique comparative des pathogènes bactériens, tous genres : identification d'espèce et de clade, cgMLST, mobilome ab initio, contenu CRISPR, métadonnées d'isolement, ressources propres à un genre. |
| [popgen](docs/popgen.md) | Génétique des populations humaines anciennes et modernes, archéologie, paléoclimat, corpus de migrations, co-évolution hôte-pathogène. |
| [ia](docs/ia.md) | Apprentissage automatique, statistiques et science des données appliqués aux données de recherche. |
| [ops](docs/ops.md) | Projets PrédictOps, OptimOps, DoctrinOps. |
| [multimedia](docs/multimedia.md) | Sous-titrage de films muets, audio et vidéo, synthèse vocale, métadonnées de films. |
| [web](docs/web.md) | Développement et test d'applications web. |

### Transverses de science

| Plugin | Rôle |
|--------|------|
| [phylo](docs/phylo.md) | Inférence phylogénétique et phylodynamique, transverse à tous les taxons : arbres, datation moléculaire, reconstruction ancestrale, annotation iTOL. |
| [bioinfo](docs/bioinfo.md) | Briques bioinformatiques génériques : séquences, formats d'alignement et de variants, réseaux de protéines, ontologies, pipelines. |
| [structure](docs/structure.md) | Couche structurale des protéines : recherche par structure, prédiction de complexes, impact d'une substitution, site actif, poches de liaison. |
| [litterature](docs/litterature.md) | Accès et fouille de la littérature scientifique, revue incrémentale, plein texte et tables supplémentaires. |
| [science-commun](docs/science-commun.md) | Socle commun de tout projet, seul bloc chargé dans tous les profils : figures aux normes des revues, cartes, lecture de PDF, calcul distant, statistiques. |

### Blocs de phase

| Plugin | Rôle |
|--------|------|
| [redaction](docs/redaction.md) | Phases 2 et 3 du cycle : plan narratif, squelette et rédaction LaTeX, vérification des affirmations, des références et des figures, review interne. |
| [diffusion](docs/diffusion.md) | Phase 4 : choix de la revue, dépôt du préprint et du code, portail éditorial, réponse aux relecteurs. |
| [carriere](docs/carriere.md) | Hors cycle de projet : CV, dossiers de financement, suivi de carrière. |

### Domaines séparés

| Plugin | Rôle |
|--------|------|
| [maboss](docs/maboss.md) | MaBoSS et CoLoMoTo : modèles booléens `.bnd` et `.cfg` (grammaire refcard), API pyMaBoSS, évaluateur CCT (Oscar Dufossez), carte de l'écosystème (WebMaBoSS de Vincent Noël, dépôts de modèles, positionnement vis-à-vis d'INDRA). Modélisation de la signalisation cancer, projet mabossDemo. |
| [droit](docs/droit.md) | Recherche juridique en droit français : conventions de notes et citations, vérification des décisions et textes normatifs aux sources officielles. |

Le répertoire `mes_skills/` conserve des ressources personnelles historiques pour iTOL et Rasigade. Il ne contient actuellement aucun `SKILL.md` actif et n'est pas empaqueté en plugin.

## Cartographie des skills

La collection se lit comme la chaîne de production d'un article de phylogénomique bactérienne, du choix du problème au dépôt final. Vue d'ensemble par étape :

| Étape | Plugins mobilisés |
|-------|-------------------|
| 1. Cadrage et revue de littérature | `science-commun`, `litterature` |
| 2. Acquisition des génomes et isolats publiés | `bacteria`, `mtbc`, `bioinfo` |
| 3. Contrôle qualité et identification d'espèce | `bacteria`, `mtbc` |
| 4. Variants, typage, résistance | `mtbc`, `bacteria` |
| 5. Phylogénie et datation moléculaire | `phylo` |
| 6. Phylogéographie et contexte hôte | `phylo`, `mtbc`, `popgen` |
| 7. Fonction et structure des protéines | `structure`, `bioinfo` |
| 8. Modélisation, statistiques, apprentissage | `science-commun`, `ia` |
| 9. Visualisation (figures, arbres, cartes) | `science-commun`, `phylo` |
| 10. Conception et rédaction du manuscrit | `redaction` |
| 11. Vérification et réponse aux relecteurs | `redaction`, `diffusion` |
| 12. Diffusion et dépôt | `diffusion` |

Le catalogue complet est dans le [dossier `docs/`](docs/README.md) : une page par plugin, plus un index alphabétique des 199 skills. Les plugins `maboss` et `droit` relèvent de domaines séparés et y sont documentés à part.

Le partage entre `mtbc` et `bacteria` suit une règle simple, documentée dans `CLAUDE.md` : ce qui est soudé à la pile de données de la tuberculose (TBannotator, `bdd/actuelle`, `barcoding_v2`, catalogue de l'OMS, SITVIT) reste dans `mtbc` ; ce qui est méthode agnostique de l'espèce doit rester trouvable depuis un projet de n'importe quel genre, et sa description l'annonce explicitement.

## Installation

Ajouter ce dépôt comme marketplace, puis installer les plugins voulus :

```
/plugin marketplace add cguyeux/claude_plugins
/plugin install mtbc@guyeux-claude-plugins
/plugin install bacteria@guyeux-claude-plugins
/plugin install phylo@guyeux-claude-plugins
/plugin install redaction@guyeux-claude-plugins
```

Pour Codex, le dépôt reste également la source canonique. Le fichier
`codex_skills.json` sélectionne les skills exposés dans les sessions et le
synchroniseur crée des liens vers leurs répertoires réels :

```
python3 _audit/tools/sync_codex_skills.py --apply
python3 _audit/tools/sync_codex_skills.py
python3 _audit/tools/sync_codex_skills.py --inventory --detail
python3 _audit/tools/sync_agent_skills.py
python3 _audit/tools/report_agent_skill_divergences.py --check
python3 _audit/tools/audit_codex_skill_farm.py --profile-root ~/.codex
python3 _audit/tools/skills_farm.py audit --profile-root ~/.codex
python3 _audit/tools/skills_farm.py sync --farm ~/docs/.claude/skills --plugin redaction --all-missing --dry-run
python3 _audit/tools/audit_execpolicy.py --check
python3 _audit/tools/sync_execpolicy.py
python3 _audit/tools/audit_claude_memories.py --check
python3 _audit/tools/import_claude_memories.py --check
python3 _audit/tools/audit_auxiliary_surfaces.py --check
python3 _audit/tools/validate_parity.py --check
python3 _audit/tools/maintain_environment.py validate
python3 _audit/tools/maintain_environment.py audit
python3 _audit/tools/check_all.py --profile-root ~/.codex
python3 _audit/tools/check_all.py --source git-index --profile-root ~/.codex
```

La seconde commande doit indiquer zéro skill manquant et zéro conflit. Le
troisième produit l'écart entre le registre canonique et la sélection Codex,
groupé par plugin source, sans modifier le profil.
Le synchroniseur ne remplace jamais un fichier, un répertoire ou un lien divergent
déjà présent dans `~/.codex/skills`.

`skills_farm.py audit` est l'audit unifié CCX-11 : registre canonique, exports
directs, paquets Codex, profil réel, fermes personnelles Claude et Agents,
fermes projet Claude, liens morts, collisions, sources divergentes et poids des
métadonnées. Il distingue le masquage hiérarchique Claude de la découverte
Codex par ferme personnelle, exports directs et plugins.

`skills_farm.py sync` est un dry-run par défaut. La ferme cible et les skills
doivent être sélectionnés explicitement. `--apply` crée uniquement des liens
symboliques absents depuis `canon_skills.json`, sans remplacement ni suppression.
Un traitement global d'une ferme mixte exige en plus `--allow-mixed`.

La politique de commandes hors sandbox vit dans `codex_rules/default.rules`.
Elle remplace l'accumulation automatique des approbations historiques par des
règles `forbidden`, `prompt` et `allow` documentées avec leurs exemples
`match` et `not_match`. `sync_execpolicy.py` vérifie que le profil utilisateur
pointe vers cette source Git; toute ancienne politique est déplacée dans une
sauvegarde récupérable avant installation.

Le dry-run `sync_agent_skills.py` contrôle la ferme personnelle `~/.agents/skills`
depuis `~/.claude/skills` sans écrire. Il ne crée, avec `--apply`, que des liens
manquants non whitelistés et ne remplace jamais un skill divergent. Les écarts
intentionnels vivent dans `_audit/agent_farm_expected_delta.json`.

`audit_claude_memories.py` inventorie les mémoires projet Claude sans recopier
leur contenu dans ses rapports. Il conserve seulement provenance, hash, type,
destination et indicateurs de risque. `import_claude_memories.py` pilote
l'interface officielle Codex avec une sélection explicite au niveau projet,
un dry-run par défaut, une sauvegarde récupérable avant écriture et une
vérification des scopes et hashes. Un projet sensible, incomplet ou non proposé
par le détecteur officiel est refusé sans option de contournement.

`audit_auxiliary_surfaces.py` porte le contrôle CCX-14 sur les plugins
auxiliaires, agents, commandes, MCP et réglages d'interface. Il vérifie le
statusline TUI natif, les quatre MCP déjà présents, le runtime Pyright et
l'installation Graphify adaptée sous `~/.agents/skills`, sans sérialiser les
valeurs secrètes de configuration.

`validate_parity.py` porte le harnais CCX-15. Sa matrice couvre instructions,
mémoire projet, KB, mémoire native, skills, plugins, hooks, règles, MCP,
interface et contrôles négatifs. Les sondes runtime s'exécutent séparément avec
`--run-runtime claude|codex --location global|root|nested|skill`. Seuls les
résultats structurés, événements de hooks et coûts agrégés sont conservés ; les
transcripts, identifiants de session et valeurs de configuration ne le sont pas.

`maintain_environment.py` porte CCX-16. Il crée des snapshots locaux filtrés,
reconstruit les surfaces dérivées avec rollback récupérable, réinstalle les
plugins Codex depuis le marketplace versionné et fournit l'audit hebdomadaire.
La procédure complète et ses limites privées sont documentées dans
`maintenance/README.md`.

`check_all.py` regroupe les contrôles de non-dérive : registres générés,
documentation, audit des skills, fermes Codex et Agents, profil Codex réel et
tests unitaires. Sur un worktree contenant des brouillons locaux hors index,
utiliser `--source git-index` pour valider exactement le candidat staged dans
une projection temporaire mise à la corbeille en fin d'exécution.

Le rapport CCX-06 `_audit/agent_farm_divergence_report.md` détaille les
divergences de contenu entre skills communs Claude et Agents. Il est régénéré
par `report_agent_skill_divergences.py` et contrôlé par `check_all.py`.

## Un skill, un plugin

La mutualisation par liens symboliques entre plugins a été dissoute lors de la refonte du 2026-09-15. Chaque skill possède désormais un unique chemin réel, dans exactement un plugin, et s'y modifie directement. Un skill transverse à plusieurs domaines va dans le plugin transverse concerné (`phylo`, `bioinfo`, `structure`, `litterature`, `science-commun`) plutôt que dans un domaine puis lié ailleurs : un projet qui a besoin des deux active les deux plugins.

Le contrôle est immédiat, et `docs/build_docs.py` signale désormais comme anomalie tout lien ou tout nom de skill dupliqué entre plugins :

```
find */skills -maxdepth 1 -type l   # aucun lien ne doit apparaître
```

Pour retrouver le plugin d'un skill : `canon_skills.json` (régénéré par `_audit/tools/generate_canon_skills.py`) ou `claude plugin details <nom>`. La table d'affectation et les règles de placement sont documentées dans `CLAUDE.md`.

## Cadrage

L'ensemble de cet outillage est destiné à un usage de recherche scientifique académique. Les composants touchant aux pathogènes bactériens et à la résistance antimicrobienne relèvent exclusivement de la biologie évolutive, de la phylogénomique et de la littérature évaluée par des pairs.

## Auteur

Christophe Guyeux, Institut FEMTO-ST (CNRS UMR 6174), Université Marie et Louis Pasteur.
