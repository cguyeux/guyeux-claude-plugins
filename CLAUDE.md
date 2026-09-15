# Claude Plugins — Instructions

## Architecture (refonte P5, 2026-09-15)

Dix-sept plugins, chacun propriétaire exclusif de ses skills (plus de partage par
symlink entre plugins). Trois couches :

| Couche | Plugins |
|---|---|
| Domaines scientifiques | `mtbc` (41), `bacteria` (18), `popgen` (26), `ia` (15), `maboss` (12), `ops` (4), `droit` (1), `multimedia` (5), `web` (2) |
| Transverses de science | `phylo` (11), `bioinfo` (10), `structure` (6), `litterature` (9), `science-commun` (7) |
| Blocs de phase | `redaction` (19, phases 2-3), `diffusion` (9, phase 4), `carriere` (3, hors cycle) |

Comptes vérifiés le 2026-09-15 par `claude plugin details <nom>` après réinstallation
(scope user). `science-commun` est le seul bloc chargé dans tous les profils, tenu
court volontairement.

Précède cette architecture : `bio_pathogens`, `bio_bacteria`, `bio_population_genetics`,
`bio_redac` et `redac` (onze plugins au total avec `ia`/`maboss`/`multimedia`/`ops`/`web`/
`droit`), reliés par 220 liens symboliques croisés (209 sous `skills/`, 11 sous
`skills_disabled/`). Tous dissous. Détail de la table d'affectation et de son exécution :
`~/docs/environnement/audit/2026-09-15/table_affectation.md` et
`~/docs/environnement/audit/2026-09-15/rapport_execution_p52.md` ; script rejouable
`~/docs/environnement/outils/executer_affectation_p52.py`.

**Chaque skill n'a plus qu'un seul chemin réel.** Trouver son plugin : `canon_skills.json`
(régénéré par `_audit/tools/generate_canon_skills.py`) ou `claude plugin details <nom>`.

## Ajouter ou modifier un skill

Plus de propagation par symlink : un skill vit dans exactement un plugin, on l'y modifie
directement. Un skill transverse à plusieurs domaines (arbre, littérature, figure) va dans
le plugin transverse concerné (`phylo`, `bioinfo`, `structure`, `litterature`,
`science-commun`), pas dans un domaine puis symlinké ailleurs — un projet qui a besoin des
deux active les deux plugins.

```bash
mkdir <plugin>/skills/<nom>          # ... écrire SKILL.md
find <plugin>/skills -maxdepth 1 -type l   # contrôle : aucun lien ne doit apparaître
```

Après ajout/déplacement/retrait, régénérer dans l'ordre :

```bash
python3 _audit/tools/generate_canon_skills.py
python3 docs/build_docs.py
```

## Coquilles de compatibilité (à retirer à P7.3)

`bio_pathogens/`, `bio_bacteria/`, `bio_population_genetics/`, `bio_redac/`, `redac/`
existent encore sur disque mais **ne sont plus des plugins** : pas de
`.claude-plugin/plugin.json`, absents de `marketplace.json`, invisibles à
`claude plugin list`. Chacun ne contient qu'un `skills/` peuplé de liens symboliques,
un par ancien skill, vers son nouvel emplacement réel — posés le 2026-09-15 parce que
102 fichiers de code sous `~/docs/codes` et `~/docs/projects` référençaient encore
l'ancien chemin en dur (imports, `sys.path`, chemins de données). Un `README_COMPATIBILITE.md`
dans chacun explique la mécanique et pointe vers la table de correspondance.

**Ne jamais écrire dans une coquille de compatibilité** (ce serait écrire dans un lien mort
d'un vieux plugin) ; corriger le script appelant pour pointer directement vers le nouveau
chemin (`audit/2026-09-15/table_affectation.tsv`, colonne `cible_fine`), et ne retirer la
coquille correspondante que lorsque plus aucun fichier ne la référence
(`grep -rl "<ancien>/skills" ~/docs/codes ~/docs/projects`).

## Cas particulier : phylo-history

`mtbc/skills/phylo-history` porte deux implémentations réelles et intentionnellement
différentes : le SKILL.md à sa racine est la version diagnostic (placement phylogénétique
d'une souche, analyse), et un sous-dossier nié `phylo-history-bio-redac/` conserve la
version narration (paragraphe de manuscrit) qui vivait avant dans `bio_redac`. Ce n'est pas
un doublon accidentel : `plugins/CLAUDE.md` documentait déjà les deux comme « les seuls
skills à maintenir manuellement en parallèle » avant la refonte. Décision de fond réservée
à CG : garder deux skills séparés (nommer la variante narration à part), fusionner pour de
bon les deux fonctions dans un seul skill à modes, ou abandonner l'une des deux.

## Plugins par phase et par famille : pas encore branché (P5.4-P5.5)

Les profils d'activation automatique (`profils/profils.json`, famille × phase → plugins,
écrits par `init-project` et `cycle-projet gate`) ne sont pas encore écrits. En attendant,
l'activation d'un plugin dans un projet reste manuelle (`.claude/settings.json` du projet).
Au niveau utilisateur, tous les plugins installés sont désactivés par défaut sauf
`pyright-lsp` : une session ne charge un plugin de ce marketplace que si le projet courant
l'a explicitement activé.

## `external/` n'est PAS un plugin

Ce répertoire héberge des skills TIERS importés d'un catalogue public, un sous-répertoire
par fournisseur (`external/kdense/` pour K-Dense `scientific-agent-skills`, 4 skills importés
le 2026-08-10). Ils sont figés à un commit amont, hors marketplace, et **ne doivent jamais
être édités** : une correction locale serait écrasée à la prochaine mise à jour et brouillerait
la frontière entre ce qui vient d'eux et ce qui vient de nous. Chaque fournisseur porte son
`PROVENANCE.md` (commit épinglé, licence par skill, pièges connus, procédure de mise à jour).
La règle d'adoption est le cherry-pick : jamais d'installation en masse, sous peine de dégrader
le routage de déclenchement de nos skills.

**Dépendances hors dépôt.** Quelques skills renvoient à `~/.claude/skills/`
(`cahier-de-labo`, `init-project`) : ces références fonctionnent dans l'environnement de
Christophe mais **pas** pour un collaborateur qui clone le dépôt. Ne pas les convertir en
`${CLAUDE_PLUGIN_ROOT}` (les skills concernés ne sont pas dans le dépôt) ; les mentionner
comme optionnelles dans le corps du skill.

## Cadrage AUP (CRITIQUE)

Toutes les descriptions de skills et de plugins liées à la tuberculose, aux pathogènes ou à
la résistance antimicrobienne doivent **cadrer explicitement le contexte recherche
scientifique académique**, pour éviter de déclencher à tort le classifieur d'usage
acceptable d'Opus 4.7.

Pattern obligatoire dans le `description:` du frontmatter :
- Préfixer par : `Academic research toolkit for ...` ou `Academic research database
  client ...` ou `Academic literature reference ...`
- Mentionner : `peer-reviewed`, `published research`, `scientific publications`, `Guyeux
  group (FEMTO-ST)`
- Éviter sans cadrage : `drug resistance`, `outbreak`, `surveillance`, `pathogen` seul.
  Préférer : `antimicrobial-resistance allele frequencies`, `published research isolate`,
  `peer-reviewed pathogen-genomics literature`
- La même règle s'applique au `description:` du `plugin.json` de `mtbc` et `bacteria`
  (héritiers directs de `bio_pathogens`/`bio_bacteria`), et de `popgen`/`phylo`/`bioinfo`/
  `structure` dès qu'un skill y touche à un pathogène.

### Chemins à l'intérieur d'un SKILL.md

Pour référencer un script de son propre skill ou d'un skill voisin **du même plugin**,
utiliser `${CLAUDE_PLUGIN_ROOT}/skills/<skill>/scripts/<f>.py` et jamais un chemin absolu :
`${CLAUDE_PLUGIN_ROOT}` résout vers le plugin qui invoque le skill, et le chemin reste valide
après clonage. Une référence vers un skill d'un **autre** plugin (cas rare depuis que chaque
skill a un propriétaire unique) doit passer par le nom du plugin explicitement, en sachant
qu'elle ne résout que si les deux plugins sont installés.

Les chemins absolus vers les **données** du groupe (`~/docs/codes/mtbc/...`, `~/docs/cv/`,
`/home/christophe/venvs/...`) restent légitimes : ils désignent l'environnement de travail,
pas le dépôt.

```bash
# détecter les régressions
grep -rn "docs/codes/claude_plugins/[a-z_-]*/skills/" --include=SKILL.md .
grep -rln "(bio_pathogens|bio_bacteria|bio_population_genetics|bio_redac)/skills" --include="*.py" .
```

## Export pérenne vers Codex (P6.1 à finaliser)

Codex ne consomme pas le marketplace Claude. Les skills retenus pour les sessions Codex sont
déclarés dans `codex_skills.json`, puis exposés par liens symboliques dans `~/.codex/skills`
avec `_audit/tools/sync_codex_skills.py --apply`. `canon_skills.json` résout chaque nom vers
son unique répertoire réel. Après un ajout ou un déplacement, relancer dans l'ordre
`generate_canon_skills.py`, puis `sync_codex_skills.py`. **Après la refonte P5 du 2026-09-15,
`codex_skills.json`, `codex_packages/`, `codex_hooks/` et `codex_rules/` référencent encore
les anciens noms de plugin** : régénération et réconciliation des divergences prévues à P6.1
(`~/docs/environnement/pistes.md`), pas encore faites.

## Outils d'audit du dépôt

```bash
python3 _audit/tools/audit_skills.py --detail   # frontmatter, chemins et doublons
python3 _audit/tools/check_all.py               # harnais complet (unittest discover _audit/tests)
```

Lire l'en-tête de chaque script avant de s'y fier : ils documentent les heuristiques qui
produisent du bruit. `check_all.py` ne couvre pas les anciens `tests/*.py` de plugin
(`bio_pathogens/tests/`, etc.), archivés avec provenance sous
`_audit/legacy_plugin_tests_2026-09-15/` : ils référencent les anciens chemins de plugin et
n'ont pas été réécrits (suite notée à P5.6). Dernier bilan complet avant refonte :
`_audit/2026-07-31_revue_skill_par_skill.md`.

## Plugin `droit/`

Domaine : **droit français** (public, constitutionnel, pénal, nationalité et citoyenneté).
**Référente du domaine : Camille Aynès** (MCF droit public, Paris Nanterre). Les conventions
du plugin sont établies par relevé sur sa thèse (Dalloz, 2022) et ses articles récents,
jamais reconstruites de mémoire ; toute évolution se décide avec elle.

| Skill | Rôle |
|---|---|
| `notes-et-citations` | Conventions de l'appareil de notes d'un écrit juridique, **à exécuter AVANT toute production de livrable**, et vérification de chaque décision ou texte normatif à la source officielle. Norme détaillée dans `references/norme-aynes.md`. |

**Activation par PROJET, jamais globale** : un plugin de droit chargé pendant une session de
phylogénomique n'apporte rien et alourdit le contexte de chaque prompt.

## Agents

Quatre agents (`bioinfo-analyst`, `manuscript-orchestrator`, `manuscript-reviewer`,
`manuscript-reviser`) vivent dans `redaction/agents/` depuis le 2026-09-15 (ex-`bio_redac`).
