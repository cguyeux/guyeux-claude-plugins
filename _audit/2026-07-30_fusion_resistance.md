# Famille `resistance-*` du plugin bio_pathogens : analyse de fusion

Répertoire analysé : `/home/christophe/docs/codes/claude_plugins/bio_pathogens/skills/`
Aucun fichier n'a été modifié.

## 1. Inventaire

| Skill | Rôle réel | Fichiers annexes | Chevauchement |
|---|---|---|---|
| `resistance-catalogue` | Interroge et régénère le catalogue consolidé mutation vers résistance (OMS 2023 + tb-profiler + CRyPTIC, ~62 000 assertions, 21 médicaments) et convertit HGVS vers SPDI 0-based | 3 scripts : `query_catalogue.py` (97 l.), `hgvs_to_spdi.py` (121 l.), `vocab.py` (45 l.) | `hgvs_to_spdi.py` identique octet pour octet (md5 `0bacbd6e`) à celui de `resistance-predict`. Son `--strain-spdi --drug` est une version dégradée de `resistance_profile.py` (SPDI brut, un seul médicament). Sa section propagation AA redit l'étape 0 de `discovery` |
| `resistance-discovery` | GWAS logistique à correction de structure (20 PC SVD + score de co-résistance) pour déterminants hors catalogue, plus filtres de convergence phylogénétique | 1 script : `variant_match.py` (71 l.) | `variant_match.py` identique (md5 `76483578`) à la copie de `predict` et à celle du projet. Étape 0 (trois angles morts) reprise dans `catalogue` et `predict`. Tout le code exécuté vit dans le projet (`phase4/6/7`) |
| `resistance-predict` | Prédiction par médicament, catalogue déterministe plus XGBoost résiduel, évaluation GroupKFold par lignée ; embarque le CLI de profilage déterministe autonome | 3 scripts : `resistance_profile.py` (321 l.), `variant_match.py` (71 l., doublon), `hgvs_to_spdi.py` (121 l., doublon) | 2 de ses 3 scripts sont des doublons exacts. Son baseline est par définition le `--strain-spdi` de `catalogue`, en mieux |
| `resistance-explain` | Dossier mécanistique d'une mutation : verdict catalogue, association empirique, littérature tbmonitor, LLR ESM-1v, structure 3D, avec hiérarchie de preuve explicite | 1 script : `explain_mutation.py` (125 l.), copie conforme du projet (md5 `64cd690a`) | Consomme le verdict de `catalogue` et les candidats de `discovery`. Valeur ajoutée = hiérarchie de preuve et orchestration, pas de code propre |
| `resistance-profiler` | Fréquences de résistance par lignée depuis TBannotator (Postgres via MCP), cross-tabulations, Fisher exact, odds ratio, IC95 binomial, pistes iTOL, tables supplémentaires | 1 script : `resistance_profiler.py` (286 l.), autonome, entrée CSV | Aucun code ni donnée partagés. Seul le champ lexical est commun. Collision de nommage trompeuse avec `resistance-predict/scripts/resistance_profile.py`, mais l'un opère au niveau population et l'autre au niveau souche |

Aucun des cinq n'a de `references/` ni d'`assets/`, uniquement `scripts/`.

## 2. Verdict

Fusion des quatre premiers en un seul skill, `resistance-profiler` reste autonome.

Groupe fusionné (`catalogue` + `discovery` + `predict` + `explain`) : même racine projet `RESISTANCE_PROJECT` (`~/docs/codes/mtbc/Resistance_antibio`), mêmes données (`catalogue/catalogue_consolide.tsv`, matrice pangénome, phénotypes), même concept central répété trois fois (réconciliation SNP / MNV / acide aminé), pipeline linéaire déclaré par leurs propres tables d'intégration (le catalogue fournit l'exclusion à `discovery` et le baseline à `predict` ; `discovery` fournit les candidats à `explain`), 2 scripts sur 9 en doublon exact, 0 invocation en cinq mois pour les quatre.

`resistance-profiler` autonome, pour quatre raisons cumulées : source de données disjointe (TBannotator via MCP, vues `mv_strain_metadata` et `mv_strain_classification`, contre des fichiers locaux du projet) ; granularité lignée et non souche ; sorties différentes (iTOL `DATASET_BINARY`, tables supplémentaires, tests de Fisher) ; seule invocation réelle du groupe (2026-06-04) et 8 références entrantes depuis d'autres skills et un agent.

## 3. Plan de fusion

Nom retenu : `resistance-catalogue`, inchangé. C'est le pivot que les trois autres citent déjà, le répertoire canonique existe, rien à modifier dans `canon_skills.json`. Alternative `mtbc-resistance` : coût supplémentaire = 1 entrée renommée dans `canon_skills.json`, 5 symlinks, docs régénérées.

Arborescence cible :

```
resistance-catalogue/
├── SKILL.md                  (~150 l. : cadrage, socle commun écrit une fois, routeur d'intention)
├── references/
│   ├── catalogue.md          (grades, table des sources, régénération, pont HGVS vers SPDI et limites)
│   ├── discovery.md          (étapes 1 à 5 GWAS, sanity fabG1/inhA OR 42, filtres de convergence)
│   ├── predict.md            (deux étages, GroupKFold, spécificité égale, CLI resistance_profile, SHAP)
│   └── explain.md            (hiérarchie de preuve, garde-fou SAE, orchestration en 5 étapes)
└── scripts/                  (6 fichiers au lieu de 9, répertoire plat)
    vocab.py · hgvs_to_spdi.py · variant_match.py · query_catalogue.py · resistance_profile.py
```

Socle écrit une seule fois dans le `SKILL.md` (aujourd'hui en triple) : les trois angles morts de représentation avec leurs gains chiffrés (codons synonymes, éthambutol +23 points ; déterminants rares élagués par le filtre de fréquence ; MNV contre SNP sur la QRDR gyrA, moxifloxacine +55 points et lévofloxacine +51), la règle « tout matching passe par `variant_match`, jamais par une égalité SPDI brute », la distinction catalogue déterministe contre apprentissage hors catalogue, et les garde-fous transverses (recherche et non diagnostic, sas QC `species-id` et `strain-qc`, causal contre co-résistance avec l'exemple rpoB Ser450Leu associé à 94 pour cent à l'isoniazide par co-résistance seule, garde-fou SAE du 30 mai 2026).

Préservation des scripts : un `scripts/` plat suffit et ne demande aucune réécriture d'imports, puisque `query_catalogue.py` fait `from vocab import canonical_drug` et `resistance_profile.py` fait `from variant_match import parse_spdi, decompose`, tous deux résolus par le répertoire du script. Garder impérativement les versions du skill, qui divergent déjà du projet : `hgvs_to_spdi.py` (`0bacbd6e` contre `e9d19545` côté projet, la version skill ajoute le téléchargement et le cache du fichier de coordonnées OMS plus `--report`), `resistance_profile.py` (`6c07a674` contre `bdd802dd`), `vocab.py` (`ae659cae` contre `cab671ab`). Les deux doublons exacts disparaissent sans perte.

Description proposée, 283 caractères :

```
Academic research toolkit for peer-reviewed MTBC antimicrobial-resistance genomics (Guyeux group, FEMTO-ST): query the WHO/tb-profiler catalogue, resolve HGVS to SPDI, profile or predict a strain, run lineage-aware GWAS for non-catalogued determinants, explain a variant's mechanism.
```

Elle couvre les six familles de déclencheurs des originaux (catalogue et grade OMS, conversion HGVS vers SPDI, profil de souche, prédiction, GWAS et déterminants hors catalogue, mécanisme d'un variant) et respecte le cadrage AUP obligatoire décrit au point 5.

`argument-hint` fusionné proposé :

```
<--variant katG_p.Ser315Thr | --drug isoniazid | --spdi NC_000962.3:2155167:C:G | --stats> · profil: <--spdi FILE | --vcf FILE | --strains ids.txt> · découverte: <--drug ethambutol [--sanity]>
```

## 4. Gain chiffré

Dans votre référentiel de comptage : les quatre skills fusionnés pèsent 5177 caractères (6198 moins les 1021 de `resistance-profiler`) et tombent à environ 360, soit un gain d'environ 4820 caractères, 78 pour cent du poids des cinq.

Mon comptage propre (nom plus bloc `description` tel qu'écrit dans le fichier) donne 5384 pour les cinq et un gain d'environ 4200 ; le pourcentage est identique, l'écart vient du comptage de `description: >-` et de l'indentation YAML.

| Skill | brut (nom + description) | normalisé |
|---|---|---|
| `resistance-discovery` | 1207 | 1158 |
| `resistance-catalogue` | 1151 | 1104 |
| `resistance-explain` | 1098 | 1053 |
| `resistance-predict` | 1068 | 1023 |
| `resistance-profiler` | 860 | 819 |
| Total | 5384 | 5157 |

Les cinq skills sont symlinkés dans `bio_redac/skills/`. Si les deux plugins sont chargés simultanément, le coût réel est doublé et le gain aussi, de l'ordre de 9600 caractères.

Gain optionnel sans fusion : la description de `resistance-profiler` fait 1021 caractères pour un périmètre étroit ; la réécrire à environ 350 en gardant le cadrage AUP libérerait 670 caractères de plus.

## 5. Risques de perte et dépendances croisées

Contrainte dure AUP. `claude_plugins/CLAUDE.md` lignes 16 à 26 impose le préfixe `Academic research toolkit for ...`, la mention de `peer-reviewed` et de `Guyeux group (FEMTO-ST)`, et l'évitement de `drug resistance` sans cadrage au profit de `antimicrobial-resistance`. Cette armature consomme environ 110 des 300 caractères. Ne pas la sacrifier au budget : c'est ce qui empêche les faux positifs du classifieur d'usage acceptable.

Déclencheurs perdus. Dix-sept clauses « Use when » réduites à six groupes nominaux. Les plus à risque de ne plus déclencher : « régénérer le catalogue après mise à jour d'une source », « auditer pourquoi la sensibilité baseline d'un médicament est basse », « produire la table sensibilité et spécificité par médicament pour un manuscrit », « rédiger le paragraphe mécanistique d'un manuscrit ». Coût pratique proche de zéro vu 0 invocation en cinq mois, et le routeur d'intention du `SKILL.md` rattrape ces cas une fois le skill ouvert.

Trois commandes slash disparaissent : `/resistance-discovery`, `/resistance-predict`, `/resistance-explain`, toutes déclarées `user-invocable: true`. Créer des skills alias est déconseillé : chaque alias recoûte une description et annule le bénéfice.

Références croisées trouvées par grep sur tout `claude_plugins/` :

- À corriger, une seule : `bio_population_genetics/skills/esm-atlas-cli/SKILL.md:173` cite `resistance-explain` parmi les appelants devant rattraper `EsmAtlasUnavailable`.
- Non touchées, car `resistance-profiler` survit : `bio_pathogens/skills/lineage-comparison/SKILL.md:182`, `molecular-clock/SKILL.md:642` et `:940`, `mtbc-bilan/SKILL.md:892`, `phylogeography/SKILL.md:190`, `bio_population_genetics/skills/geo-map/SKILL.md`, `itol/SKILL.md`, et l'agent `bio_redac/agents/bioinfo-analyst.md:49`.
- Artefacts régénérables à reconstruire : `docs/README.md`, `docs/bio_pathogens.md`, `docs/bio_redac.md`, `docs/skills_fr.json`, produits par `docs/build_docs.py`.
- Registres à mettre à jour : `canon_skills.json`, `skill_health.json`.
- Symlinks à supprimer : `bio_redac/skills/resistance-discovery`, `resistance-predict`, `resistance-explain`. Conserver ceux de `resistance-catalogue` et `resistance-profiler`.

Script orphelin préexistant à trancher pendant la fusion : `resistance-explain/scripts/explain_mutation.py` fait `import paths`, module qui vit dans `Resistance_antibio/paths.py` et n'existe ni dans le skill ni dans `analyses/`. Cette copie n'est donc pas exécutable depuis le répertoire du skill aujourd'hui, ce que le `SKILL.md` reconnaît implicitement en commandant la version projet. Recommandation : ne pas l'embarquer, pointer vers `${RESISTANCE_PROJECT}/analyses/explain_mutation.py`.

Dernier point de vigilance : `hgvs_to_spdi.py`, `resistance_profile.py` et `vocab.py` divergent déjà de leurs homologues dans `Resistance_antibio/analyses/`, alors que `variant_match.py` et `explain_mutation.py` en sont des copies conformes. La fusion n'aggrave rien, mais c'est le bon moment pour écrire dans le `SKILL.md` quelle copie fait foi pour chacun, sinon la prochaine mise à jour du projet créera un décalage silencieux.
