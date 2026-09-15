---
name: cadrage-editorial
description: >-
  Dernière passe avant de déposer un manuscrit, une fois la revue choisie : relire la
  VITRINE (titre, résumé, mots-clés, clôture d'introduction, première phrase de discussion,
  conclusion, lettre d'accompagnement) contre ce que cette revue publie réellement, pour
  qu'un travail de qualité ne soit pas refusé sur un malentendu de formulation. Mesure la
  forme réelle du corpus de la revue, simule le rejet éditorial par une instance
  indépendante qui ne voit que ce que l'éditeur lit, propose des retouches justifiées par
  un fait éditorial vérifié, et rend UN verdict daté dans `cadrage_editorial.md` : ALIGNE,
  RETOUCHER, CHANGER-DE-CIBLE ou ROUVRIR. Ne touche jamais aux Résultats ni aux Méthodes,
  et ne sauve pas une revue mal choisie. Utiliser quand la revue est arrêtée et qu'il reste
  à vérifier que le cadrage colle, quand on craint un desk-reject de principe, quand on
  hésite sur le titre ou le résumé pour une cible donnée, quand on recadre après un rejet
  pour une nouvelle revue, ou taper /cadrage-editorial.
argument-hint: "<cle-revue> [chemin-projet] | read"
allowed-tools:
  - Bash
  - Read
  - Edit
  - Write
  - Grep
  - Glob
  - WebSearch
  - WebFetch
  - Agent
  - AskUserQuestion
---

# cadrage-editorial — Que l'éditeur comprenne, avant de juger, que ce papier est chez lui

Le pipeline qualité prouve qu'un manuscrit est bien fait. La porte 3bis prouve que le
résultat mérite d'être diffusé. Le choix de revue prouve que la cible est plausible.
Aucun des trois ne regarde le titre et le résumé comme un éditeur les regarde : seuls,
en trois minutes, pour décider s'il envoie le dossier en relecture ou s'il le renvoie.

C'est le dernier endroit où un travail solide se perd pour une raison qui n'a rien à
voir avec sa valeur. Un desk-reject de cadrage ne coûte pas seulement six semaines : il
brûle la revue pour douze mois (règle de variation, `/soumission` phase 2) et n'apprend
rien, puisque la lettre dira simplement que le sujet ne convient pas au lectorat.

> [!IMPORTANT]
> **Ce skill ne sauve pas une revue mal choisie, et il doit pouvoir le dire.** Les trois
> desk-rejects d'août 2026 (manuscrits purement in silico envoyés à des revues qui
> exigent de la paillasse) n'étaient pas des malentendus de formulation : aucune
> reformulation ne les aurait sauvés. Reformuler pour masquer une inadéquation de fond
> est un mensonge, et un mensonge qui se paie au premier relecteur. Quand l'écart est de
> cette nature, le verdict est CHANGER-DE-CIBLE.

> [!WARNING]
> **Le risque propre de ce skill est le survendu.** « Mettre en avant autrement » glisse
> très vite en « promettre davantage ». Toute retouche de la vitrine est donc soumise aux
> garde-fous de la section dédiée, et le périmètre est strictement borné : Résultats,
> Méthodes, figures et ordre de la démonstration ne sont **pas** touchés ici.

## Place dans le cycle

Entre le choix de la revue et la soumission, à l'intérieur de la phase 4 :

```
porte 3      manuscrit stabilisé (pipeline qualité)
porte 3bis   /verdict-diffusion → SOUMETTRE + niveau
phase 4      /soumission phase 2 : la revue est arrêtée par l'auteur
        →    CE SKILL : la vitrine colle-t-elle à cette revue ?          ← ici
phase 4      /soumission phase 3 : gabarit, longueur, cover letter, reviewers
             /soumission phases 4 et 5 : dépôts, portail
```

Ce n'est pas une phase, c'est une passe d'une heure. Mais elle a deux propriétés d'une
porte : elle rend un verdict tracé, et elle peut renvoyer en arrière, au choix de revue
(CHANGER-DE-CIBLE) voire à la porte 3bis (ROUVRIR).

Elle se rejoue à chaque nouvelle cible. Un cadrage établi pour une revue ne vaut rien
pour une autre, et c'est précisément ce qu'il faut relire avant de resoumettre ailleurs
après un rejet : ce qu'on avait mis en avant la fois précédente, et pourquoi.

## Ce que les skills voisins ne font pas

| Skill | Ce qu'il juge | Pourquoi il ne couvre pas ce geste |
|---|---|---|
| `/manuscript-review` | le texte, dans l'absolu | ne connaît de la revue que sa limite de longueur ; ne lit pas la vitrine comme un éditeur |
| `/soumission` phase 2 | la revue, contre le manuscrit | sert à écarter une cible, jamais à ajuster ce qu'on met en avant ; jette le corpus récolté |
| `/soumission` phase 3 | la conformité | gabarit, longueur, lettre, relecteurs : du secrétariat, pas du cadrage |
| `/verdict-diffusion` | la valeur du résultat | se prononce avant que la revue soit connue |
| `/deai-latex` | le style | ne sait rien de la cible |
| `/narratif` | l'ordre de la démonstration | tranche le plan, en amont, et ce skill n'y touche pas |

## Entrées requises

1. `verdict_diffusion.md` porte un SOUMETTRE daté avec son `niveau` (sinon, rien à cadrer :
   lancer `/verdict-diffusion`).
2. Une clé de revue arrêtée, présente dans `~/.agents/knowledge/journals/journals.tsv`.
3. `article/main.tex` compilant, avec titre et résumé dans leur état candidat.
4. La fiche de la revue à jour : `python3 ${CLAUDE_PLUGIN_ROOT}/skills/soumission/scripts/journals.py lint`
   propre pour cette clé. Un champ `unknown` n'est pas une donnée, et un `computational_only`
   resté `unknown` a déjà coûté un desk-reject (Computers in Biology and Medicine, 2026-08-30).
5. Une cible **réellement viable**, pas seulement plausible. Le coût s'arbitre en phase 2 et ne
   se rejoue pas ici, mais cadrer pour une revue où l'on ne soumettra pas est du travail perdu :
   relire le champ `apc` et `free_route` de la fiche avant de lancer la passe. Cas rencontré au
   rodage : Microbial Genomics est le meilleur fit de scope du dépôt pour la génomique de
   population, et se trouve écartée pour cet auteur par un APC gold de 2 203 GBP sans dispense.

Une clause du guide aux auteurs qui n'a pas pu être relevée reste **non vérifiée** et se déclare
comme telle dans le matériel de la simulation : la page d'instructions de Microbial Genomics
renvoie un 403 aux outils de récupération, et une limite de résumé inventée serait pire que la
limite inconnue.

## Les quatre temps

### Temps 1 — Mesurer la revue, au lieu de l'imaginer

Le corpus des douze derniers mois a déjà été récolté au critère 2 du choix de revue, puis
jeté. On le récolte (ou le relit) et on le garde :

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/cadrage-editorial/scripts/corpus_fit.py fetch <cle> --months 12
python3 ${CLAUDE_PLUGIN_ROOT}/skills/cadrage-editorial/scripts/corpus_fit.py situate <cle> \
    --tex article/main.tex --terms "<2 à 4 termes qui nomment l'objet central>"
```

Le cache vit dans `~/.agents/knowledge/journals/corpus/<cle>.json` et sert aussi aux
soumissions suivantes. Ce que la sortie donne : longueur médiane et intervalle p10-p90 des
titres et des résumés, part de titres interrogatifs, part avec deux-points, part avec un nom
d'espèce en tête, part affichant la méthode, part affirmant un résultat plutôt que nommant
un sujet, part de résumés structurés, et fréquence des termes de l'objet dans le corpus.

Exemple réel (FEMS Microbiology Letters, 101 articles sur douze mois) : titres de 15 mots
médians, **0 %** d'interrogatifs, 47 % avec un nom d'espèce en tête, **2 %** affichant la
méthode, résumés de 190 mots médians et **5 %** structurés. Un titre interrogatif de 26 mots
annonçant « a computational reanalysis » y détonne sur quatre points mesurables, ce qui
n'était pas devinable et se voit en une commande.

Les termes de l'objet sont la mesure la plus décisive du lot. Quand aucun des cent articles
ne nomme l'objet central du manuscrit, deux lectures seulement : la revue ne publie pas sur
cet objet, ou elle le nomme autrement. La seconde se vérifie (chercher les variantes dans le
corpus) avant de rien changer ; la première est un signal de mauvaise cible, pas de mauvaise
formulation.

**Toujours instruire les variantes avant de conclure quoi que ce soit d'un zéro.** Mesuré au
rodage du 2026-09-09 sur les 283 articles de Microbial Genomics : `homoplasy` zéro occurrence,
mais `recurrent` cinq et `convergent` deux ; `reference strain` zéro, mais `reference genome`
vingt-huit. Deux zéros qui ne disent pas la même chose : la revue ne publie pas sous ce mot-là,
elle publie sous l'autre, et elle avait même publié dans l'année deux articles sur le biais de
référence chez *M. tuberculosis*. Un zéro brut aurait conclu à la mauvaise cible ; les variantes
concluent à un vocabulaire à aligner, ce qui est une retouche légitime et bornée.

Les articles les plus proches trouvés dans le corpus servent deux fois : ils fournissent les
trois exemples de la simulation, et ils prouvent (ou non) que la revue publie réellement ce
genre de travail, ce qui est une vérification du critère 2 du choix de revue par une autre voie.

Ces heuristiques de forme sont grossières par construction. Elles repèrent un écart franc,
elles ne tranchent rien : un écart mesuré est un point à instruire, et un écart délibéré et
justifié se garde.

### Temps 2 — Simuler le rejet éditorial, par une instance indépendante

Le test que rien d'autre ne fait : donner à lire ce que l'éditeur lit vraiment, à quelqu'un
qui n'a pas rédigé le manuscrit et ne connaît pas ses résultats.

Déléguer par `Agent` (sous-agent neutre, pas la session qui a écrit), avec pour seul
matériel le titre, le résumé, les mots-clés, la lettre d'accompagnement, les clauses
d'exclusion de la revue relevées mot pour mot, et trois titres-résumés qu'elle a publiés
dans les douze mois. Consigne, format de retour et pièges d'indépendance :
`references/simulation-desk-reject.md`.

Le retour attendu est binaire et motivé : envoi en relecture, ou desk-reject avec la phrase
exacte qui le déclenche et la clause qu'elle heurte. Un « ça pourrait passer » n'est pas un
retour ; le redemander.

Deux simulations valent mieux qu'une quand le verdict revient positif du premier coup et que
l'écart mesuré au temps 1 était non nul : c'est le cas où l'instance a probablement complété
le dossier avec ce qu'elle savait du domaine plutôt que de s'en tenir à ce qu'elle voyait.

### Temps 3 — Retoucher, dans le périmètre et sous garde-fous

Périmètre autorisé, et rien d'autre :

- le titre ;
- le résumé ;
- les mots-clés ;
- le dernier paragraphe de l'introduction (ce que le papier annonce faire) ;
- la première phrase de la discussion (ce que le papier revendique avoir montré) ;
- la conclusion ;
- la lettre d'accompagnement.

Hors périmètre, sans exception dans cette passe : Résultats, Méthodes, figures, tableaux,
ordre de la démonstration, contenu des supplementary. Si le cadrage semble exiger d'y
toucher, ce n'est pas un cadrage : c'est un CHANGER-DE-CIBLE, ou un retour à `/narratif`
sur décision de l'auteur.

Garde-fous, à appliquer à chaque retouche :

1. **Chaque retouche est justifiée par un fait éditorial vérifié**, cité : une clause du guide
   aux auteurs, une mesure du temps 1, la formulation type des titres de la revue, un motif
   rendu par la simulation. Une retouche justifiée par « ça sonne mieux » est refusée.
2. **Aucune affirmation nouvelle, aucun chiffre nouveau.** Toute phrase retouchée qui porte un
   chiffre ou une affirmation repasse par `/claim-check` sur la vitrine seule. Un résumé
   reformulé est un endroit classique d'apparition de claims que le corps ne soutient pas.
3. **Le titre ne promet pas plus que le niveau du verdict 3bis.** Un `niveau : MINEUR` interdit
   un titre de rupture ; l'écart entre les deux se mesure en relisant l'axe de charge de preuve
   du verdict, pas à l'estime.
4. **Rien ne disparaît sans destination.** Si le cadrage conduit à retirer une revendication du
   résumé, elle reste dans le corps, ou part vers un autre article ; le retrait pur est tracé
   dans le registre avec son motif.
5. **`main_fr.tex` suit**, à la lettre et dans la même passe. Le pré-vol mesure cet écart, et
   une vitrine anglaise retouchée sans son pendant français bloque la soumission.
6. **Un préprint déjà en ligne ne se réécrit pas.** Si le titre change après dépôt, la
   divergence entre la version publique et la version soumise est consignée : le DOI reste
   attaché à ce qui a été déposé.
7. **Diff lisible en une minute** : avant / après, une ligne de justification par retouche.
   L'auteur doit pouvoir refuser chaque retouche séparément.

Puis rejouer les temps 1 et 2 sur la vitrine retouchée. Le point fixe est atteint quand la
simulation passe et que les écarts restants sont assumés par écrit. C'est ce tour à vide qui
autorise le verdict ALIGNE, exactement comme une porte du cycle.

### Temps 4 — Rendre UN verdict, daté, dans le registre

| Verdict | Sens | Suite |
|---|---|---|
| **ALIGNE** | la vitrine dit à cette revue ce qu'elle publie, sans rien promettre de plus | `/soumission` phase 3 |
| **RETOUCHER** | les retouches sont identifiées mais pas encore intégrées et revérifiées | appliquer, rejouer, empiler une entrée ALIGNE |
| **CHANGER-DE-CIBLE** | l'écart ne se comble pas sans mentir | retour `/soumission` phase 2, la clé rejetée est notée avec son motif |
| **ROUVRIR** | aucune vitrine honnête n'existe pour ce niveau de revue, quel que soit le titre | retour porte 3bis, `/verdict-diffusion` rejoué |

Un verdict, pas un menu. L'auteur arbitre l'action, jamais à partir d'un « à toi de voir ».

Le quatrième cas est rare et important. Découvrir qu'aucune formulation honnête ne rend le
travail publiable à ce niveau n'est pas un problème de communication : c'est la 3bis qui
n'avait pas vu quelque chose, et il vaut infiniment mieux le découvrir ici qu'après trois
relectures.

## Le registre `cadrage_editorial.md`

À la racine du projet, à côté de `verdict_diffusion.md` et `claim_check.md`. Entrées
**empilées de la plus récente à la plus ancienne**, jamais supprimées : la trace de ce qu'on
avait mis en avant pour une revue qui a rejeté est exactement ce qu'on veut relire avant de
recadrer pour la suivante.

En-tête normalisé, machine-lisible, cinq clés dans cet ordre exact :

```markdown
# Cadrage éditorial — <nom du projet>

## Cadrage du 2026-09-09 — archives-microbiology

verdict : ALIGNE
revue : archives-microbiology
rendu le : 2026-09-09
vitrine : titre+résumé de main.tex, empreinte 3f9a1c2d
simulation : desk-reject non (2 passes, instance indépendante)

### Ce que la revue publie réellement
101 articles sur 12 mois : titres 15 mots médians, 0 % interrogatifs, 47 % espèce en
tête, 2 % méthode affichée ; résumés 190 mots médians, 5 % structurés.

### Retouches appliquées
| Élément | Avant | Après | Fait éditorial qui la justifie |
|---|---|---|---|
| Titre | ... | ... | 0 % de titres interrogatifs sur 101 articles |

### Écarts assumés
...

### Ce que ce cadrage n'a pas touché
Résultats, Méthodes, figures, ordre de la démonstration.
```

L'empreinte de vitrine est ce qui rend la dérive détectable : c'est la somme de contrôle du
titre et du résumé au moment du verdict, que le pré-vol recalcule. La commande qui la donne :

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/soumission/scripts/preflight.py --vitrine-empreinte article/main.tex
```

## Contrôle mécanique en aval

`preflight.py` lit ce registre comme il lit déjà `verdict_diffusion.md`. Avec `--journal <cle>` :

- registre absent → **bloquant** ;
- verdict courant pour une **autre** revue que la cible passée → **bloquant** ;
- verdict `RETOUCHER`, `CHANGER-DE-CIBLE` ou `ROUVRIR` → **bloquant** ;
- `ALIGNE` mais empreinte de vitrine différente de la vitrine actuelle → **réserve** : le titre
  ou le résumé ont bougé depuis le cadrage, le vérifier avant de déposer ;
- `ALIGNE` de plus de 90 jours → **réserve** (le corpus de la revue a vieilli).

Un blocage se lève en faisant le travail, pas en passant outre. Si l'auteur décide de déposer
malgré une réserve, la réserve est consignée dans le cahier de labo comme décision assumée.

## Modes

| Intention | Mode |
|---|---|
| « la vitrine colle-t-elle à cette revue ? » | passe complète, les quatre temps |
| « qu'est-ce que cette revue publie, au fond ? » | temps 1 seul (`corpus_fit.py profile`) |
| « on a été rejeté, on visait X, on vise Y » | lire l'entrée X du registre, puis passe complète sur Y |
| `read` | lire le registre et rendre l'état, sans rien mesurer |

## Erreurs à éviter

- **Ne pas confondre malentendu et inadéquation.** Le premier se répare par la formulation, le
  second par un changement de cible. Les confondre produit soit un desk-reject, soit un mensonge.
- **Ne pas prendre la sortie de `corpus_fit.py` pour un verdict.** Elle situe une forme dans une
  distribution ; elle ne sait rien du fond.
- **Ne pas faire simuler le rejet par la session qui a rédigé.** Elle sait ce que le manuscrit
  prouve, donc elle lit le résumé mieux qu'un éditeur, donc elle ne verra pas le malentendu.
- **Ne pas retoucher le résumé sans repasser les chiffres.** C'est là que naissent les claims
  orphelins.
- **Ne pas améliorer la vitrine « en général ».** Sans cible nommée, cette passe n'a pas d'objet :
  elle mesure un écart à une revue précise, ou elle ne mesure rien.
- **Ne pas toucher aux Résultats ni aux Méthodes**, même quand la tentation est raisonnable. Le
  périmètre est ce qui rend cette passe réversible et donc sûre.
- **Ne pas laisser un verdict RETOUCHER dormir dans le registre.** Il n'est pas un état stable :
  soit les retouches sont appliquées et une entrée ALIGNE l'empile, soit le verdict devient
  CHANGER-DE-CIBLE.

## Épilogue

Entrée au cahier de labo (`/cahier-de-labo update`) résumant le verdict et les retouches, mise à
jour de `pistes.md` si le verdict a rouvert quelque chose, puis reprise de `/soumission` là où
elle s'était arrêtée. Si la revue a révélé un fait durable (clause d'exclusion, forme imposée,
vocabulaire maison), l'écrire dans sa fiche avec `journals.py set` : c'est ce qui évite de
re-mesurer la même revue au manuscrit suivant.
