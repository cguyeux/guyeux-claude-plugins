# Validation CCX-15 : parité Claude et Codex

Date : 2026-08-26

## Verdict

La matrice est complète. Dix-huit scénarios couvrent les instructions, la
mémoire projet, la KB, la mémoire native, les skills, les plugins, les hooks,
les règles, les MCP, l'interface et les contrôles négatifs. Dix-sept passent et
un reste partiel avec une différence expliquée et un propriétaire. Aucun
scénario n'est bloqué, en échec ou non exécuté.

La parité signifie ici égalité des invariants utiles, pas identité des fichiers,
des formulations ou des mécanismes internes.

## Crible adversarial

Le risque principal était un test circulaire sur deux profils déjà configurés.
Le harnais sépare donc quatre couches de preuve : source commune synchronisée,
état local déterministe, contrôles négatifs falsifiants et sessions neuves. Une
simple présence dans un cache ne suffit pas à conclure qu'un skill est visible,
et une configuration MCP ne suffit pas à conclure que son authentification ou
son transport fonctionne.

## Sondes neuves

Huit sondes non persistantes ont réussi, quatre par plateforme :

| emplacement | invariant principal |
|---|---|
| `global` | cinq artefacts, cinq phases, trois contrôles pré-calcul, `mh` et `mp` |
| `root` | instruction propre à la plateforme dans un chemin avec espaces |
| `nested` | héritage de la même instruction depuis un sous-répertoire |
| `skill` | invocation réelle de `/challenge` avec verdict `Reformuler` |

Les quatre sondes Codex étaient éphémères et en lecture seule. Les quatre
sondes Claude utilisaient Haiku, aucun outil, aucune persistance et un plafond
de 0,50 USD par appel. Les appels Claude réussis totalisent 0,523 USD dans le
registre agrégé. Une première capture du résultat `/challenge` a terminé avec
code 0 mais n'a pas été comprise par le parseur ; après ajout du support des
blocs `assistant`, l'unique relance a réussi.

Le registre `_audit/parity_runtime_observations.json` ne conserve que la
plateforme, l'emplacement symbolique, le statut, la réponse structurée, les
événements de hooks, le coût et une catégorie d'erreur. Il ne contient aucun
transcript, identifiant de session, stdout, stderr ou valeur de configuration.

## Contrôles négatifs

- `rm parity-probe` est transmis directement aux garde-fous mais n'est jamais
  exécuté. Claude et Codex répondent tous deux avec le code de blocage 2 et la
  substitution `gio trash`.
- Le témoin ne contient aucun cahier, état, pistes ou journal. Les sessions ne
  prétendent pas que ces registres existent.
- Le chemin témoin contient des espaces et son instruction est retrouvée depuis
  deux profondeurs.
- `mbovis` est absent de la liste visible dans les quatre sondes projet. Un
  ancien cache Claude 1.0.0 le contient encore physiquement ; ce reliquat non
  actif est attribué à CCX-16.
- Les rapports d'audit sont scannés contre plusieurs formats usuels de clés et
  clés privées. Aucun motif n'est sérialisé.

## Différences conservées

1. Le mode Claude `--print --include-hook-events` montre `SessionStart` mais pas
   d'événement `Stop` exploitable. Le hook `Stop` est présent dans les réglages
   et le processus termine sans boucle. Cette différence est attribuée à la CLI
   Claude et reste le seul scénario partiel.
2. Les quatre noms MCP sont configurés des deux côtés, mais le transport et
   l'authentification ne sont pas promus en preuve de parité. Superhuman attend
   encore une autorisation OAuth et l'URL Codex de `tbannotator` reste
   intentionnellement distincte.
3. Graphify est visible dans Codex et absent de Claude. C'est un gain de la
   cible de migration, pas une régression, car la migration demandée va de
   Claude vers Codex.

## Clôture de CCX-02

Le dernier contrôle CCX-02 est maintenant satisfait. Une session Claude neuve
restitue les cinq artefacts projet, les cinq phases, les trois vérifications
avant calcul, `mh`, `mp`, `gio trash` et `~/.agents/knowledge`. Le rendu était
déjà synchronisé statiquement ; la restitution sémantique est désormais prouvée
avec un budget accepté.

## Artefacts

- `_audit/parity_scenarios.json` : matrice déclarative.
- `_audit/tools/validate_parity.py` : collecteur local et lanceur de sondes.
- `_audit/parity_runtime_observations.json` : observations agrégées.
- `_audit/parity_report.json` et `.md` : couverture et différences.
- `_audit/fixtures/parity/project with spaces/` : témoin racine et imbriqué.
- `_audit/tests/test_parity_validation.py` : contrat de matrice, parsing,
  minimisation des sorties et clôture.

## Commandes de contrôle

```text
python3 _audit/tools/validate_parity.py --check
python3 -m unittest _audit.tests.test_parity_validation _audit.tests.test_check_all
python3 _audit/tools/check_all.py --source git-index --profile-root ~/.codex
```

La projection exacte de l'index passe les 112 tests, les registres canoniques,
les fermes, hooks, règles, mémoires, surfaces auxiliaires et le contrôle de
parité. Le harnais global s'arrête ensuite sur
`sync_knowledge_base.py --check`, car les rapports KB du worktree sont déjà
modifiés hors de ce lot et ne correspondent plus à la KB vivante. CCX-15 ne
les écrase ni ne les committe.
