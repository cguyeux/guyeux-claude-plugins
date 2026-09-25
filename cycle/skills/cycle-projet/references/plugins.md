# Le profil de plugins d'un projet, et sa bascule aux portes

Née d'une question de CG sur l'économie de contexte (session `SpacerEgalVirus`,
2026-08-20, `mtbc/pistes.md` P36), puis refondue par la piste P5.5 du projet
`environnement` (2026-09-15) : ce qui était une bascule manuelle de deux plugins
est devenu un **profil écrit dans le `.claude/settings.json` du projet**, que la
porte réécrit.

## Ce qu'est un profil

`profil = socle + blocs de la FAMILLE du projet + blocs de sa PHASE`, plus
l'exception éventuelle de ce projet précis. La table est dans
`~/docs/environnement/profils/profils.json`, l'outil dans
`~/docs/environnement/outils/profil_plugins.py`. Le profil écrit est **complet et
explicite** : chacun des dix-sept plugins du marketplace y porte `true` ou `false`,
donc un projet déplacé garde son profil et la lecture du fichier suffit à savoir ce
qui sera chargé.

Au niveau utilisateur (`~/.claude/settings.json`), tous les plugins du marketplace
sont à `false` : sans cela, un plugin installé et non nommé par le projet serait
**actif par défaut** (doc officielle, « Default Enablement »), et le profil ne
retrancherait rien.

## Ce que la phase ajoute

| Phase | Ce que la phase ajoute au domaine | Pourquoi |
|---|---|---|
| 1 — analyse primaire | rien | aucune compétence de rédaction n'est utile avant qu'il y ait un état à valoriser |
| 2 — valorisation et squelette | `redaction` | le squelette commence, et le pipeline qualité de la phase 3 en dépendra |
| 3 — itération draft | `redaction` | la phase alterne rédaction et analyse en son sein : les deux couches restent |
| 4 — finalisation et soumission | `redaction` + `diffusion` | soumission, dépôts, slides ; le pipeline qualité peut rouvrir le manuscrit à tout moment |
| 5 — clôture | rien | la clôture est `/recadrage` + `/reflect` + archivage, pas de la rédaction |
| hors rail (voie réponse ou réoutillage) | rien | pas de phase, donc pas de bloc de phase : le domaine seul |

Deux bascules utiles dans toute la vie d'un projet, donc : l'entrée en phase 2 et
l'entrée en phase 5. Ne jamais basculer à l'intérieur d'une phase.

## Ce que le skill fait aux portes

À chaque `gate` qui fait franchir une porte, et donc changer la phase déclarée
dans `etat_des_decouvertes.md` :

```bash
python3 ~/docs/environnement/outils/profil_plugins.py --apply <projet> --write
```

puis **dire à CG de redémarrer la session** : la bascule n'est pas prise en compte
dans une session déjà ouverte. `cycle_status.py` affiche de lui-même une ligne
`Plugins : profil À RÉÉCRIRE` quand le settings du projet a pris du retard sur la
phase — c'est le cas le plus fréquent, une phase avancée à la main.

## Pourquoi un redémarrage, et pas `/reload-plugins`

Mesuré le 2026-09-13 (KB `claude-plugins-aup.md`) : `/reload-plugins` recharge le
CONTENU des plugins déjà chargés au démarrage du process, mais **ne redécouvre pas
un plugin nouvellement activé**. Et il invalide le cache de prompt, donc une
bascule fréquente coûterait plus qu'elle ne fait gagner.

Deuxième piège de la même KB : `settings.json` n'est pas la seule source de vérité.
Un état runtime séparé, visible par `claude plugin list` seul, peut diverger après
une manipulation du cache. Si `claude plugin list` dit `disabled` ce que le fichier
dit `true`, aucun redémarrage n'y changera rien : il faut
`claude plugin enable <plugin>@<votre-marketplace>`, puis redémarrer.

## Ce que le profil n'est PAS

Ce n'est pas une économie de budget de catalogue. Le modèle en caractères qui
justifiait cette économie (`skillListingBudgetFraction × 200 000`) a été réfuté par
la mesure le 2026-09-15 (P5.3) : les profils réels occupent 1,5 à 2,8 % de la
fenêtre, sans éviction. Ce que le profil sert vraiment, c'est la PERTINENCE de ce
que le modèle voit — un projet de droit ne doit pas se voir proposer des skills de
phylogénomique — et la mitigation du classifieur AUP, qui s'active sur
l'accumulation de vocabulaire pathogène injectée par des descriptions de skills
dont la session n'a que faire (même KB, entrées du 2026-05-17).
