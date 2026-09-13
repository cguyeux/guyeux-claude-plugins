# `plan_presentation.md` : le format littéral

Un fichier par exposé, dans `presentations/AAAA-MM-JJ_<slug>/`. L'en-tête est
machine-lisible, le corps est fait pour être relu par un humain.

````markdown
---
exposé: Le pathogène comme archive sociale
projet: L5L6-codivergence_ethnies_ouest_afrique
date: 2026-09-15
occasion: séminaire d'équipe
public: microbiologiste MTBC, non spécialiste de génétique des populations
durée: 20 min, questions en plus
langue_slides: fr
langue_oral: fr
intensité: academique
budget: 18 min de parole → 12 slides de corps, 2 ruptures, 3 sections, 6 annexes
état_source: etat_des_decouvertes.md du 2026-07-06
révisé: 2026-09-15
---

## Message

Les lignées de *M. africanum* épousent la carte ethnolinguistique ouest-africaine,
et racontent la même histoire que le chromosome Y humain, en plus fin et plus récent.

**Contre-message** : la distribution des lignées suit la géographie, pas la structure
sociale. C'est ce que la slide 4 doit tuer.

## Arc

énigme → résultat → tension → deux échelles → mécanisme et temps → convergence
avec le génome humain → chute → ouverture

## Chaîne d'arguments

- **M1** — *M. africanum* est cantonnée à l'Afrique de l'Ouest, ce qui demande une explication.
- **M2** — à l'échelle continentale, les lignées suivent la partition ethnolinguistique.
- **M3** — ce n'est pas la géographie : témoin négatif *M. ulcerans*, distance contrôlée.
- **M4** — deux échelles emboîtées résolvent la tension avec la littérature.

## Points de bascule

- **B1** (tue « c'est la géographie ») → slide 5, carte + témoin négatif. Figure due.
- **B2** (tue « c'est la génétique profonde de l'hôte ») → slide 8, F_ST inter-ethnies. Figure due.

## Inventaire

| Item | Rang | Slide | Motif si écarté |
|---|---|---|---|
| Batterie de tests concordants | NOYAU | 4 | |
| Témoin négatif *M. ulcerans* | NOYAU | 5 | |
| F_ST inter-ethnies 0,005-0,006 | NOYAU | 8 | |
| Réplication Nguidi 2024 | APPUI | 9 | |
| Datation des sous-lignées | MENTION | 11 | non bouclée, une phrase suffit |
| Détail des 12 tests | ANNEXE | A2 | |
| Pipeline d'annotation | ÉCARTÉ | | aucun maillon n'en dépend devant ce public |

## Figures

| Fichier | Verdict | Geste | Slide |
|---|---|---|---|
| `article/figures/map_l5l6_pie.pdf` | à reforger | polices ×1,6, légende annotée sur la carte | 5 |
| `article/figures/fst_y_mtdna.pdf` | à refaire | répond à une autre question que la slide | 8 |
| à produire | `sci-figure` | barres appariées Y contre mtDNA, 5 ethnies | 9 |

## Fiches par slide

### Slide 5 — La même partition dans le pathogène

- **Rôle** : point de bascule B1, tuer l'explication géographique.
- **Message, donc titre** : « Ce n'est pas la géographie : le témoin négatif le montre ».
- **Informations** : carte des lignées ; distribution disjointe de *M. ulcerans* ;
  effet de la distance contrôlé.
- **Durée** : 2 min 30.
- **Modalité** : carte via `geo-map`, deux panneaux appariés, une ligne de lecture.
- **Consomme** : NOYAU « témoin négatif », APPUI « isolement par la distance ».

### Slide 7 — Une liste, faute de mieux

- **Rôle** : appui, énumérer les quatre tests.
- **Message, donc titre** : « Quatre tests indépendants, tous concordants ».
- **Modalité** : liste à puces. **Justification** : quatre tests hétérogènes sans
  relation d'ordre ni de composition ; ni frise, ni schéma, ni graphique ne les
  relie. Une liste de quatre items courts est ici la forme honnête.
- **Durée** : 45 s.

## Dérive

- 2026-09-16 — la slide 9 est passée de 1 à 2 slides : la réplication Nguidi
  demandait sa propre lecture, l'empiler rendait les deux illisibles. Budget
  repris sur une annexe.
````

## Règles

L'en-tête est le contrat : tout le reste du skill le relit. Ne pas le laisser
diverger du deck.

Le champ **Modalité** d'une fiche doit porter une **justification** dès qu'il
vaut « liste à puces ». C'est la trace de la règle par défaut inversée, et c'est
ce que le contrôle relit.

La section **Dérive** se remplit pendant la production. Une dérive n'est pas
interdite, la fabrication découvre des choses ; ce qui est interdit, c'est que le
plan et le deck se contredisent en silence. Dater et motiver.
