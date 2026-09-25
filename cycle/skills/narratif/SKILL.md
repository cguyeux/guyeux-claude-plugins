---
name: narratif
description: Conception de l'article entre le message et le squelette. Ordonne l'acquis en vue de la démonstration, fixe la chaîne d'arguments et ses points de bascule, puis décide du temps et du lieu de chaque fait — développé dans le corps, porté par une figure, réduit à une phrase avec renvoi, versé au supplémentaire, ou reconnu comme sérendipité. Émet ensuite le squelette LaTeX depuis le plan, chaque section portant son allocation. Use on `/narratif`, `/narratif read`, `/narratif tri`, `/narratif drift`, `/narratif reprise`, or « comment structurer cet article », « quel est le fil de la démonstration », « dans quel ordre sortir les arguments », « qu'est-ce qui va en supplementary », « l'article est trop verbeux », « on perd le lecteur », « par quoi commencer », avant d'écrire le squelette d'un manuscrit.
argument-hint: "[read | tri | drift | reprise] [chemin-projet]"
---

# narratif — Décider du fond, puis de la forme, avant d'écrire

Entre « le message » et « le squelette », il manquait une étape. La porte 1bis dit
qu'il faut écrire ; le squelette dit où les sections tombent. Aucun des deux ne
demande **comment exploiter au mieux ce qu'on a appris pour délivrer ce qu'on a à
dire**. Ce skill occupe cette place, et il la tient avant qu'un seul paragraphe
soit rédigé.

## Le défaut qu'il corrige, mesuré

Un article écrit sans cette étape s'ordonne tout seul selon la chronologie du
chantier, et se remplit de tout ce qui a coûté du temps. Le parc le montre :

| Manuscrit | Mots | Fichiers supp. | Figures | Tables |
|---|---|---|---|---|
| `animal_vs_human` | 13 558 | 0 | 22 | 15 |
| `L4.11` | 10 843 | 1 | 10 | |
| `Rv2516c` | 10 679 | 1 | 3 | |
| `methodology` | 11 571 | 8 | 7 | |

`animal_vs_human` découpe ses Résultats nœud par nœud de l'arbre, dans l'ordre où
l'analyse l'a parcouru, puis referme sur une sous-section « Validation and general
analyses ». Ses « Supplementary Tables » et « Supplementary Results » sont des
sections **internes** au fichier principal : elles restent donc dans le chemin du
lecteur. `methodology`, à longueur comparable, compile un `supplementary.tex`
séparé et porte huit fichiers supplémentaires.

**Le défaut n'est pas la longueur, c'est l'absence de tri et un ordre calqué sur le
chantier.** La longueur en est le symptôme. C'est pourquoi couper en phase 3 ne le
répare pas : `/deai-latex` R16 raccourcit un texte, il ne le réordonne pas.

## Le principe qui commande tout le reste

> [!IMPORTANT]
> **La revue n'arbitre ni l'article, ni le message, ni la longueur** (règle posée
> par CG, 2026-09-09). On fait le travail de recherche proprement, on l'écrit
> proprement, et on regarde **ensuite** quelles revues sont compatibles. Un beau
> travail bien écrit déposé sur bioRxiv ou HAL vaut mieux qu'une compromission
> éditoriale payée en qualité scientifique.

Conséquence directe sur la nature du budget. La taille du corps est **celle que la
démonstration exige** : aucun mot qui ne serve un maillon, une bascule, ou la
capacité du lecteur à suivre. La contrainte est qualitative, son test est mécanique
— *quel maillon ce paragraphe sert-il ?* La compatibilité avec les revues se calcule
en **sortie**, comme information pour la phase 4, jamais comme contrainte ici. Si
aucune revue ne convient, la réponse est le préprint, pas l'amputation.

Deuxième conséquence, sur le supplémentaire. Il n'existe pas pour absorber un
dépassement de compteur, mais **pour le lecteur exigeant**. C'est ce qui autorise à
y être franchement généreux : un corps qu'on suit sans effort, et derrière lui une
rafale de vérifications pour qui veut contrôler. Générosité n'est pas déversement :
tout item supplémentaire répond à une question qu'un lecteur poserait vraiment.

## Localiser le contexte

Remonter jusqu'à la racine du projet (premier répertoire portant
`cahier_de_labo.md`). Lire, dans cet ordre, et ne rien écrire avant d'avoir tout lu :

- `etat_des_decouvertes.md` — **l'unique intrant scientifique**. §1 la question, §2
  les acquis (avec leur `destination :`), §3 le réfuté, §4 l'incertain, §5 la
  position vs littérature, §7 les angles morts. Le cahier est l'historique, pas la
  matière : ne pas partir de lui, c'est ainsi qu'on écrit la chronologie du chantier.
- `verdict_diffusion.md` — le verdict amont doit être RÉDIGER (ou RECADRER déjà
  traité). Son axe **P, charge de preuve**, contraint le verbe du message.
- `pistes.md`, `claim_check.md` s'il existe, et l'inventaire de `résultats/` et
  `experiments/`.

**Refuser de travailler sans verdict amont.** Un projet qui n'a pas franchi la
porte 1bis n'a pas établi qu'il fallait écrire ; concevoir son narratif est
prématuré. Renvoyer vers `/verdict-diffusion amont`.

---

## Les neuf gestes

### 1. Le message, et le contre-message

Le **message** est la phrase que le lecteur doit retenir : falsifiable, avec un
verbe calibré sur le niveau de preuve réel (axe P du verdict amont). Le
**contre-message** est ce que ce même lecteur croyait avant d'ouvrir l'article.

Un article est une **transformation de la croyance du lecteur**. Tout ce qui ne
participe pas à cette transformation n'appartient pas au corps du texte. Cette
définition n'est pas une image : c'est le critère dont dérivent les gestes 3 et 6.

Deux sorties immédiates :

- si message et contre-message se ressemblent, il n'y a pas d'article — remonter à
  `/verdict-diffusion amont` ;
- si le message ne tient pas en une phrase, il y en a deux — passer la main à
  `/recadrage`, ne pas arbitrer seul.

Écrire enfin le **et alors ?** : ce qu'un lecteur fait différemment après. S'il n'y
a pas de réponse, le message est un constat, pas une thèse, et l'article sera plat
quelle que soit sa structure.

### 2. La chaîne porteuse

Les propositions que le lecteur doit accepter, **dans l'ordre**, pour aller du
contre-message au message. Typiquement trois à six ; au-delà de six, il y a deux
articles, ou des confirmations déguisées en maillons.

Chaque maillon `M<n>` porte quatre choses, et les quatre sont obligatoires :

| Champ | Ce qu'il dit |
|---|---|
| proposition | énoncée **comme le lecteur doit l'accepter**, pas comme le calcul l'a produite |
| acquis | quels items de `etat_des_decouvertes.md` §2 la soutiennent |
| alternative tuée | l'explication concurrente que ce maillon élimine |
| statut | établi, convergent, ou faible |

**Un maillon sans alternative tuée n'est pas un maillon.** C'est une description.
Le lecteur ne change pas d'avis parce qu'on lui décrit quelque chose, il change
d'avis parce qu'une autre explication devient intenable.

### 3. Le test de charge

Pour chaque maillon, mécaniquement : **le retirer, et regarder si le message tient
encore.** S'il tient, ce n'était pas un maillon mais une confirmation, et sa place
est au supplémentaire.

C'est ce test, et lui seul, qui décide le tri du geste 6. Pas le temps passé, pas
la difficulté technique, pas l'élégance du calcul.

Deux pièges. Un maillon peut sembler retirable parce qu'un autre le recouvre
partiellement : alors ce sont deux formulations d'un même maillon, à fusionner, pas
deux maillons. Et un maillon **faible** qui ne peut être retiré sans faire tomber le
message est le vrai point de fragilité de l'article : c'est là qu'il faut dépenser
des mots et, si possible, une analyse de plus — pas là où l'on a déjà dépensé du
temps.

### 4. Les points de bascule

Parmi les maillons, ceux où la croyance du lecteur **bascule effectivement** : le
moment précis où une explication alternative meurt. Deux à quatre par article.

> **Le nombre de figures du corps égale le nombre de points de bascule.** Pas le
> nombre d'analyses conduites, pas un format de revue.

Une figure candidate qui ne sert aucune bascule se justifie en **une ligne écrite au
registre** (les cas légitimes : une figure d'orientation sans laquelle la suite est
illisible, un schéma de mécanisme, un flux de sélection des données), ou elle part
au supplémentaire. La justification est écrite, jamais implicite : c'est elle qui
sera relue quand on se demandera pourquoi il y a onze figures.

Les bascules deviennent les emplacements de figures que `/fig-ideation` doit remplir.
Il conçoit la figure ; ce skill dit **combien** il en faut et **où** elles sont dues.

### 5. L'ordre, c'est-à-dire le narratif

Trois ordres sont possibles et un seul est bon.

L'ordre **chronologique** (celui du chantier) est le défaut par gravité : c'est celui
qu'on obtient sans rien décider, et c'est le producteur de verbosité. L'ordre
**logique** (celui de la preuve) est meilleur mais froid, et il charge le lecteur de
méthode avant de lui avoir donné une raison de s'y intéresser. L'ordre **par les
questions** est celui qui fait que la démonstration coule de source.

Écrire donc la chaîne explicitement :

```
état initial du lecteur  ->  Q1  ->  M1 y répond  ->  Q2 que M1 fait naître
                         ->  M2 y répond  ->  ...  ->  message accepté
```

**La question se rédige dans les mots du lecteur, pas dans les nôtres.** « Comment
savoir que ce n'est pas un artefact de mapping ? » est une question de lecteur ;
« validation de la robustesse du pipeline » est un titre de section. Si l'on
n'arrive pas à écrire la question, la section n'est pas gagnée : soit elle est mal
placée, soit elle est du supplémentaire.

Deux contrôles mécaniques :

- **ordre des dépendances** : aucun maillon ne peut dépendre d'un maillon énoncé
  après lui. Le plan est un graphe orienté sans cycle ; s'il en a un, l'ordre est
  faux, pas la science.
- **la section « et aussi »** : toute section qui ne répond à aucune question est
  là parce que le travail a été fait, non parce qu'il fallait le dire. C'est le
  générateur de verbosité, et il se reconnaît à ce titre-là.

### 6. Le tri — le temps et le lieu de chaque fait

Chaque acquis destiné à cet article reçoit **exactement un rang**.

| Rang | Lieu | Développement |
|---|---|---|
| **PORTEUR** | corps | développé, avec ses chiffres et son dénominateur |
| **BASCULE** | corps + figure ou table | le plus cher, et le plus rare |
| **MENTION** | corps | **une seule phrase**, qui garde le chiffre exact et son statut, plus le renvoi |
| **SUPPLÉMENTAIRE** | `supplementary.tex` | migré **verbatim**, jamais réécrit |
| **SÉRENDIPITÉ** | aucun article | part à `/recadrage` avec sa destination |

**Ce qui vaut le rang PORTEUR**, et le test de charge seul ne suffit pas à le dire : un acquis
est porteur s'il soutient un maillon **ou** s'il répond à une question de la chaîne du geste 5.
La distinction compte. Le volet fonctionnel d'un article de requalification, par exemple, ne
porte souvent aucun maillon — le message tient sans lui — mais il répond à la question que tout
lecteur pose une fois convaincu, et il porte le « et alors ». Il est donc PORTEUR et jamais
BASCULE : aucune figure ne lui est due au titre de la preuve, tout au plus un schéma
d'orientation justifié par écrit. Confondre les deux fait produire une figure par volet, ce qui
est exactement la façon dont on arrive à vingt-deux figures dans un corps.

Cinq règles qui font tenir le tri :

1. **Le corps reste autonome pour la conclusion, le supplémentaire n'ajoute que la
   reproductibilité.** Un MENTION garde dans le corps la valeur et le statut
   (« p = 0,36, non significatif »), et migre seulement le chemin qui y mène.
   Migrer la conclusion avec le détail la vide de sens pour qui ne consulte jamais
   le supplémentaire.
2. **Une phrase, c'est une phrase.** Le rang MENTION est la seule chose qui rende
   compatibles un corps léger et un supplémentaire généreux. S'il dérive en
   paragraphe, tout le dispositif retombe.
3. **Le supplémentaire se planifie, il ne se remplit pas par débordement.** Écrire
   son sommaire S1..Sn avant de rédiger, chaque item nommé par la question à
   laquelle il répond.
4. **Un acquis ne se désigne pas deux fois.** Au registre, l'intitulé d'un acquis peut être
   abrégé, mais avec **le vocabulaire de l'état**, pas une reformulation : le croisement entre
   `plan_narratif.md` et `etat_des_decouvertes.md` se fait par recouvrement de mots-clés, et
   une paraphrase élégante casse l'appariement sans rien signaler d'autre qu'un faux « sans
   rang ».
5. **Un négatif n'est pas une impasse.** Le récit des essais infructueux ne s'écrit
   pas ; le résultat négatif est un actif quand il réfute un claim que le lecteur
   porterait, sert de contrôle, borne l'espace cherché, ou évite à un tiers de
   refaire l'erreur. Doctrine complète en R14 de `/deai-latex`, à appliquer ici en
   amont plutôt qu'en aval.

### 7. La taille naturelle, et le sommaire du supplémentaire

Pour chaque section : ce qu'elle doit accomplir, les maillons qu'elle porte, et la
taille que cela demande — **estimée depuis le contenu**, jamais depuis un plafond
éditorial (cf. le principe directeur).

**La somme doit tenir.** Les tailles du tri s'additionnent, et le total annoncé doit les
couvrir **plus** l'introduction, les méthodes, la discussion et la conclusion, qui ne portent
aucun acquis. Un plan dont les items totalisent déjà le total annoncé promet une taille que son
propre tri dément — vu à la première application réelle, 5 200 mots d'items sous un total de
4 600. `plan_status.py` le mesure.

Puis le sommaire du supplémentaire, numéroté, chaque item portant la question d'un
lecteur exigeant : « comment savoir que ce n'est pas un artefact ? », « cela
tient-il sur l'autre lignée ? », « qu'avez-vous exactement filtré ? ». Un item qui
ne répond à aucune question de ce genre n'est pas de la générosité, c'est du
déversement, et il se supprime.

Le supplémentaire est un **document compilé à part** (`supplementary.tex`), jamais
une section de fin du fichier principal : une section de fin reste dans le chemin du
lecteur et dans tout compteur de mots.

### 8. La taxe de coût irrécupérable

Pour chaque item classé PORTEUR ou BASCULE, une question, posée à voix haute :

> **Si ce résultat avait coûté cinq minutes au lieu de trois semaines, garderait-il
> ce rang ?**

Si non, déclasser. `cycle-projet` interdit déjà de faire entrer le coût engagé dans
un verdict ; la même interdiction vaut pour l'occupation de l'espace. C'est le geste
le plus désagréable du skill et le plus rentable : il attrape exactement ce que
l'auteur ne voit pas, parce que ce qui a coûté cher paraît important.

### 9. Les deux falsifications du plan

**Le contre-narratif.** Quelle est la meilleure histoire concurrente que les
**mêmes données** racontent ? Si le plan ne la tue pas, le plan n'est pas prêt.
Discipline de `/challenge` : le contre-argument le plus fort, formulé sérieusement,
pas une objection de paille.

**Le test du lecteur pressé.** Un lecteur qui ne lit que le titre, le résumé, les
légendes de figures et le dernier paragraphe de l'introduction reçoit-il le message ?
C'est la majorité des lecteurs réels. Si non, le message n'est pas aux places
porteuses, et aucune quantité de corps de texte ne le rattrapera.

---

## Le registre, et l'émission du squelette

Le plan s'écrit dans **`plan_narratif.md`** à la racine du projet. Gabarit littéral,
en-tête machine-lisible compris : `references/gabarit.md`.

Le rang d'un acquis vit **dans ce registre, pas dans `etat_des_decouvertes.md`** :
l'état est la vérité scientifique et se réécrit en entier à chaque itération, et sa
ligne `destination :` appartient à `/recadrage`. Le croisement se fait par titre
d'acquis.

**Puis le squelette est émis depuis le registre**, et c'est ce qui empêche le plan de
n'être qu'une bonne intention. Chaque section porte son allocation en commentaire :

```latex
\section{Results}
% narratif: maillons M2,M3 | bascule B1 -> figure 2 | taille visee 2200 mots

\subsection{Exclusive markers of the clade}
% narratif: maillon M2 | taille visee 600 mots
% question du lecteur : comment savoir que ce n'est pas un artefact de mapping ?
```

Ces commentaires sont relus en phase 3 par `plan_vs_manuscrit.py`, qui rend les
sections très au-delà de leur taille visée, les sections **sans** ligne
`% narratif:` (personne ne les a planifiées : ce sont les sections « et aussi »), et
les items classés SUPPLÉMENTAIRE que le corps développe malgré tout.

> **La dérive n'est pas interdite, elle doit être consciente.** La rédaction
> découvre des choses, et un rang peut se révéler faux. Alors on corrige le plan, on
> date la correction, et on écrit pourquoi. Ce qui est interdit, c'est que le plan
> et le manuscrit se contredisent en silence.

## Modes d'invocation

- **`/narratif`** (défaut) — passe complète, les neuf gestes, écriture de
  `plan_narratif.md`, du sommaire supplémentaire et du squelette commenté.
- **`/narratif read`** — afficher le plan courant et sa fraîcheur, sans rien modifier.
- **`/narratif tri`** — seulement les gestes 3, 6 et 8 : reclasser les acquis quand
  de nouveaux résultats arrivent, le message et la chaîne restant inchangés.
- **`/narratif drift`** — comparer le manuscrit écrit à son plan (phase 3).
- **`/narratif reprise`** — partir d'un manuscrit **déjà écrit** au lieu de l'état :
  reconstruire la chaîne que le texte porte réellement, la confronter à celle qu'il
  devrait porter, et rendre le chantier de restructuration. C'est le mode des
  manuscrits longs du parc, à reprendre un à un.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/narratif/scripts/plan_status.py [projet]
python3 ${CLAUDE_PLUGIN_ROOT}/skills/narratif/scripts/plan_vs_manuscrit.py [projet]
```

Les deux scripts **ne tranchent rien** : ils mesurent. `plan_status.py` rend les
acquis destinés à l'article sans rang, les bascules sans figure, les dépendances
inversées, la taille projetée du corps et — en information seulement, pour la phase 4
— les revues de `~/.agents/knowledge/journals/journals.tsv` compatibles avec elle.

## Erreurs à éviter

- **Partir du cahier de labo.** Il porte la chronologie ; en partir produit
  mécaniquement le plan chronologique. L'intrant est l'état.
- **Confondre un maillon et une confirmation.** Le test de charge tranche, l'intuition
  non.
- **Laisser un MENTION devenir un paragraphe.** C'est la fuite par laquelle le corps
  regrossit sans que personne ne décide rien.
- **Réécrire au lieu de migrer.** Un item versé au supplémentaire s'y copie
  verbatim, avec un renvoi dans les deux sens ; le paraphraser fait diverger deux
  versions d'un même chiffre.
- **Mettre le supplémentaire en fin de fichier principal.** Il reste alors dans le
  chemin du lecteur, et le tri n'a servi à rien.
- **Dériver le nombre de figures d'un format de revue.** Il vient des bascules.
- **Compter les mots pour tenir dans une revue.** On écrit ce que la démonstration
  exige ; la revue se choisit après, et le préprint est une réponse légitime.
- **Faire entrer le coût engagé dans un rang.** Trois semaines de calcul ne
  gagnent pas une figure.
- **Écrire le plan et ne pas émettre le squelette.** Le plan qui ne produit pas la
  structure qu'on remplit ensuite est décoratif, et sera contredit dès le premier
  paragraphe.

## Frontière avec les skills voisins

`/verdict-diffusion amont` juge si le sujet mérite d'être écrit ; **`narratif`
décide comment l'écrire**. `/recadrage` attribue un acquis à un article ou à un
autre projet ; `narratif` lui donne sa place **à l'intérieur** d'un article, et lui
renvoie les SÉRENDIPITÉ. `/fig-ideation` conçoit les figures ; `narratif` dit
combien il en faut et où elles sont dues. `/deai-latex` coupe ce qui a été écrit en
trop ; `narratif` évite de l'écrire. `cycle-projet` séquence le tout.

## Références

- `references/gabarit.md` — le format littéral de `plan_narratif.md`.
- `references/archetypes.md` — six formes d'article récurrentes ici, chacune avec sa
  chaîne naturelle, ses bascules typiques et **son piège de verbosité propre**. À
  lire au geste 2 : reconnaître la forme fait gagner la moitié de la chaîne.
