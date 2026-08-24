# `fig_plan.md` — le registre du plan de figures

Comme `claim_check.md`, `fig_check.md` et `review/INDEX.md`, ce registre est la **preuve
datée** que l'idéation a eu lieu. Son absence vaut preuve que le contrôle n'a pas eu lieu :
ne jamais conclure qu'une idéation antérieure a été faite parce que les figures « ont l'air
bien ».

Il vit à la racine du projet, à côté de `etat_des_decouvertes.md`. Il est **réécrit** à
chaque passage, pas empilé, mais les fiches déjà décidées sont conservées avec leur état.

## En-tête

```markdown
# Plan de figures — <projet>

**Passage :** 3    **Mis à jour le :** 2026-08-24    **Manuscrit :** article/main.tex
**Message de l'article :** <la phrase falsifiable du squelette, recopiée telle quelle>
**Cible :** <revue>, <n> figures maximum dans le corps
**Diagnostic mécanique :** <n> pendante(s), <n> orpheline(s), <n> muette(s),
part conceptuelle <x> % (corpus MTBC 16 %)
```

Le message est recopié depuis le squelette, jamais reformulé. Une figure se juge contre le
message ; si le message change, tout le plan est à rejuger.

## Fiche d'une figure retenue

Une fiche par figure. Les champs marqués obligatoire ne se laissent pas vides : un champ vide
signifie que la figure n'est pas prête à être produite.

```markdown
## F3 — Frise à double registre, MTBC et histoire humaine   [à produire]

- **Charge de preuve** (obligatoire, une phrase falsifiable) : la radiation des lignées
  modernes L2 et L4 est postérieure à la transition néolithique et antérieure aux grandes
  routes commerciales de l'âge du bronze.
- **Archétype** : T1
- **Emplacement** : corps, après la section de datation. Pleine largeur.
- **Panneaux** : registre haut, cinq événements humains sourcés ; registre bas, quatre
  événements MTBC avec HPD ; deux connecteurs testés.
- **Source des données** : `résultats/beast/l2l4_mcc.tree`, `résultats/dates_hpd.tsv`
- **Outil** : TikZ, patron `frise_double_registre.tex`
- **Effort** : moyen, deux à trois tours d'inspection
- **Modèle nul** : si aucune coïncidence n'existait, les HPD couvriraient uniformément
  l'intervalle et aucun connecteur ne serait justifié. La figure reste lisible et rend un
  résultat négatif publiable.
- **Test du noir et blanc** : passé, les deux registres sont séparés par la position, pas
  par la teinte.
- **Test des 86 mm** : échoue en colonne simple. Réservée à la pleine largeur, ou scindée.
- **Répond à** : remarque R04 de `review/2026-08-12_reviewer2.md`
- **État** : à produire | esquissée | produite | inspectée | intégrée | abandonnée
```

États et ce qu'ils signifient exactement :

| État | Signifie |
|---|---|
| `à produire` | fiche complète, rien n'existe |
| `esquissée` | une esquisse jetable a tranché la structure |
| `produite` | le fichier compile et le PDF existe |
| `inspectée` | le PNG a été relu, y compris ses recadrages, et les défauts sont corrigés |
| `intégrée` | incluse dans le manuscrit **et** citée dans le corps du texte |
| `abandonnée` | avec sa raison, en une ligne |

`produite` n'est pas `inspectée`, et `inspectée` n'est pas `intégrée`. Le dépôt compte
85 images produites et jamais incluses dans un seul projet : c'est le passage de `produite`
à `intégrée` qui casse le plus souvent.

## Candidates rejetées

Une ligne par candidate tuée, pour qu'elle ne revienne pas à chaque passage.

```markdown
## Candidates rejetées

- **Carte des pays d'origine** — rejetée au passage 2. Contre-argument : trois pays
  représentent 88 % de l'effectif, la carte est une table de trois lignes. Retenue comme
  supplementary S2 si un relecteur la demande.
- **Figure-thèse** — reportée au passage 4. Le message n'est pas encore stabilisé, et une
  figure-thèse dessinée trop tôt fige une thèse non prouvée.
- **Barplot des catégories fonctionnelles** — rejetée : redit la table 3 au chiffre près.
```

## Inventaire des orphelines

Section obligatoire dès que le diagnostic mécanique en signale. Chaque orpheline reçoit une
décision explicite, sinon elle sera re-signalée à chaque passage sans jamais être traitée.

```markdown
## Images produites et non intégrées

| Fichier | Décision | Raison |
|---|---|---|
| `article/figures/map_l416.png` | à intégrer comme F2 | répond à la section phylogéographique |
| `résultats/distance_histogram.png` | supplementary S1 | contrôle utile, hors argument principal |
| `résultats/pairwise_heatmap.png` | abandonner | remplacée par la matrice triée par l'arbre |
```

## Bilan du passage

```markdown
## Bilan du passage 3

- Retenues : F1 à F5, dont deux conceptuelles (F3 frise, F4 avant/après).
- Part conceptuelle du plan : 40 %, contre 0 % avant ce passage.
- Rejetées : 3, dont une reportée.
- Orphelines traitées : 9 sur 9.
- Prochaine porte : produire F3 et F4, puis `/fig-check main.tex --force`.
```

## Articulation avec les autres registres

- **`pistes.md`** : une sous-piste par figure à produire, rattachée à la piste majeure de
  l'article. C'est ce qui rend le travail reprenable après une pause.
- **`fig_check.md`** : prend le relais dès qu'une figure passe à `produite`. Les deux
  registres ne se recouvrent pas — `fig_plan.md` dit ce qui doit exister et pourquoi,
  `fig_check.md` dit si ce qui existe est lisible et exact.
- **`review/INDEX.md`** : quand une figure répond à une remarque, la remarque porte le
  numéro de figure et la fiche porte le numéro de remarque. `/reviewer-response` a alors de
  quoi rédiger la réponse.
- **`claim_check.md`** : une figure qui porte un claim structurant doit apparaître dans les
  deux registres, avec la même formulation de la charge de preuve.
- **`cahier_de_labo.md`** : une entrée par passage d'idéation, même sans figure produite.
