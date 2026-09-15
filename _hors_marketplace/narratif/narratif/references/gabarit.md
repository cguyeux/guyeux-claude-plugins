# Gabarit de `plan_narratif.md`

Un fichier par projet, à sa racine, à côté de `etat_des_decouvertes.md`. Pour un
projet à deux manuscrits, **une section `# Plan narratif — <manuscrit>` par
manuscrit** dans le même fichier, chacune avec son propre en-tête : ne jamais créer
`plan_narratif_article2.md`, la dispersion des registres se paie à la relecture.

Le format est lu par `scripts/plan_status.py`. Les trois tableaux (chaîne, bascules,
tri) et les clés de l'en-tête sont **stables** : les renommer casse la mesure.

---

```markdown
# Plan narratif — <projet>

**Passage :** 1    **Mis à jour le :** 2026-09-09    **Manuscrit :** article/main.tex

message : <une phrase, falsifiable, verbe calibré sur la preuve réelle>
contre-message : <ce que le lecteur croit avant d'ouvrir l'article>
et alors : <ce qu'il fait différemment après>
archetype : <une des six formes de references/archetypes.md, ou « hors bestiaire »>
verdict amont : RÉDIGER (2026-09-08)
maillons : 4    bascules : 2    supplémentaire : 6 items
taille visée du corps : 4200 mots (hors résumé, légendes et références)

## 1. La chaîne porteuse

| # | Proposition, telle que le lecteur doit l'accepter | Acquis mobilisés | Alternative tuée | Statut | Dépend de |
|---|---|---|---|---|---|
| M1 | ... | <titres d'acquis de l'état §2> | ... | établi | — |
| M2 | ... | ... | ... | convergent | M1 |
| M3 | ... | ... | ... | faible | M1, M2 |
| M4 | ... | ... | ... | établi | M3 |

**Test de charge.** Pour chaque maillon, ce qui se passe si on le retire :

- M1 retiré : le message tombe (M2 n'a plus de population de référence). MAILLON.
- M2 retiré : le message tombe. MAILLON.
- M3 retiré : le message tient mais devient « compatible avec » au lieu de
  « établit que ». MAILLON, et c'est le point de fragilité de l'article.
- M4 retiré : le message tient tel quel. CONFIRMATION → rang SUPPLÉMENTAIRE (S3).

## 2. Les points de bascule

| # | Maillon | Ce qui meurt là | Figure ou table | Emplacement |
|---|---|---|---|---|
| B1 | M2 | l'explication par un artefact de couverture | figure 2 | Résultats, §2 |
| B2 | M3 | l'explication par la structure de population | figure 3 | Résultats, §4 |

Figures du corps sans bascule, et leur justification écrite :

- figure 1 — orientation : sans le cladogramme, aucune section suivante n'est
  lisible. Conservée.
- *(toute autre figure sans justification ici part au supplémentaire.)*

## 3. Le narratif

État initial du lecteur : <ce qu'il croit, une phrase>

| Q | Question, dans les mots du lecteur | Y répond | Section |
|---|---|---|---|
| Q1 | « de quoi parle-t-on au juste, et pourquoi maintenant ? » | contexte | Introduction |
| Q2 | « comment savoir que ce n'est pas un artefact de mapping ? » | M1, M2 | Résultats §1-2 |
| Q3 | « d'accord, mais est-ce que ce n'est pas juste la lignée ? » | M3 | Résultats §3 |
| Q4 | « et cela change quoi ? » | M4 + discussion | Discussion |

Message accepté à la fin de Q4.

**Contrôle des dépendances** : ordre M1 < M2 < M3 < M4, aucune inversion.

## 4. Le tri des acquis

Un rang par acquis destiné à ce manuscrit (`**Destination : A**` dans l'état §2 — le format
réel du parc met la clé en gras et en fin de phrase, pas sur une ligne à part).

L'intitulé peut être **abrégé**, mais il doit garder les mots-clés de l'état : l'appariement
entre les deux fichiers se fait par recouvrement de vocabulaire, et une paraphrase casse le
croisement en produisant un faux « acquis sans rang ».

| Acquis (intitulé abrégé, avec le vocabulaire de l'état §2) | Rang | Lieu | Taille visée | Si MENTION, la phrase du corps |
|---|---|---|---|---|
| <titre> | BASCULE | Résultats §2, figure 2 | 700 mots | — |
| <titre> | PORTEUR | Résultats §3 | 500 mots | — |
| <titre> | MENTION | Résultats §3 | 1 phrase | « ... (p = 0,36, non significatif ; détail en S4). » |
| <titre> | SUPPLÉMENTAIRE | S3 | — | — |
| <titre> | SÉRENDIPITÉ | — | — | destination C, `/recadrage` du 2026-09-09 |

**Taxe de coût irrécupérable** — items déclassés à ce titre, et pourquoi :

- <titre> : trois semaines de mise au point, mais un lecteur qui l'ignore tire la
  même conclusion. PORTEUR → SUPPLÉMENTAIRE (S5).

## 5. Sommaire du supplémentaire

Chaque item porte la question du lecteur exigeant à laquelle il répond. Document
compilé à part (`article/supplementary.tex`), jamais une section de `main.tex`.

| # | Titre | Question à laquelle il répond | Contenu |
|---|---|---|---|
| S1 | Sélection des génomes | « qu'avez-vous exactement filtré ? » | flux CONSORT, seuils, effectifs |
| S2 | Contrôles de couverture | « et si c'était un défaut de profondeur ? » | tables par souche |
| S3 | ... | ... | ... |

## 6. Falsifications du plan

**Contre-narratif** — la meilleure histoire concurrente que les mêmes données
racontent : <énoncé sérieux>. Ce qui la tue : <maillon, ou "rien encore", et alors
c'est une limite déclarée>.

**Test du lecteur pressé** — titre, résumé, légendes et dernier paragraphe
d'introduction : le message passe / ne passe pas. Si non, ce qui manque : <...>

## 7. Journal des révisions

Empilé du plus récent au plus ancien, jamais réécrit.

- **2026-09-20** — M3 déclassé de BASCULE à PORTEUR : la figure 3 ne montrait pas la
  mort de l'alternative, seulement sa cohérence. Bascules : 2 → 1, figures du corps :
  3 → 2. Signalé par `plan_vs_manuscrit.py` (section 47 % au-delà de sa taille visée).
```

---

## Ce que `plan_status.py` lit exactement

| Élément | Motif attendu |
|---|---|
| en-tête | lignes `clé : valeur` avant le premier `##` |
| maillons | lignes de tableau commençant par `\| M<n> \|`, dépendances en dernière colonne |
| bascules | lignes de tableau commençant par `\| B<n> \|`, figure en 4e colonne |
| tri | tableau de la section `## 4`, rang en 2e colonne parmi les cinq valeurs |
| supplémentaire | lignes de tableau commençant par `\| S<n> \|` |

Les cinq rangs sont écrits **en capitales** : `PORTEUR`, `BASCULE`, `MENTION`,
`SUPPLÉMENTAIRE`, `SÉRENDIPITÉ`. La forme sans accent est acceptée en lecture, mais
la forme accentuée est celle qu'on écrit.
