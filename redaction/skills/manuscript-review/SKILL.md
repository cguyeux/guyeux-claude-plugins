---
name: manuscript-review
description: >-
  Peer review of a scientific manuscript as for a high-impact journal. Reads the full paper
  (LaTeX or text), evaluates structure, methodology, statistics, terminology, figures and
  references, and produces a structured review in French with severity-ranked
  recommendations. Measures mechanically what linear reading cannot see: total length against
  the target journal's limit, near-verbatim redundancy between sections, dead-end failure
  narrative versus informative negatives, under-use of supplementary materials, and citation
  traceability of the data provenance (plus the self-citation rate, in both directions). For
  TB / MTBC manuscripts, validates the state of the art and citation completeness against
  tbmonitor-papers (~190k PubMed TB abstracts). Use when the user asks for a critical read of
  a manuscript, wants to know what a reviewer would object to, asks whether a paper is too
  long for a journal, asks to review a paper before submission, or wants a second opinion on
  a draft.
argument-hint: "<path to main.tex or manuscript file>"
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, WebSearch, WebFetch, mcp__tbmonitor__execute_sql, mcp__tbmonitor__show_schema
---

# /manuscript-review : Review de manuscrit scientifique

Produit une review structuree, serieuse et complete d'un article scientifique,
comme le ferait un reviewer exigeant pour un journal a haut facteur d'impact.



## Prealable -- Consultation memoire projet

**Avant toute action**, verifier si le projet possede :
1. Un `JOURNAL.md` dans le repertoire du projet → le lire pour connaitre l'historique
2. Un `CLAUDE.md` local → le lire pour les instructions specifiques
3. Un `claim_check.md`, `review/INDEX.md`, ou `response.md` → connaitre l'etat courant

Afficher un bref resume de l'etat connu du projet avant de commencer :

```
Etat projet : [titre article]
  Journal     : [derniere entree ou "absent"]
  Claim-check : [N claims, M infirmes ou "jamais execute"]
  Reviews     : [N reviews, M en cours ou "aucune"]
  Derniere action : [date et description]
```

## Declenchement

```
/manuscript-review path/to/main.tex
```

Si aucun argument, chercher un fichier `main.tex` dans le repertoire courant.

## Processus

### Phase 1 : Lecture integrale du manuscrit

Lire le manuscrit **en entier**, section par section. Ne pas commencer la review
avant d'avoir lu la derniere ligne (bibliographie incluse).

Pour un fichier LaTeX :
1. Identifier la structure : `\section`, `\subsection`, `\begin{table}`, `\begin{figure}`
2. Lire par blocs de 300 lignes max (limite du Read tool)
3. Prendre des notes mentales sur chaque section au fur et a mesure
4. Lire aussi les fichiers inclus (`\input{}`, `\include{}`)
5. Identifier les figures referencees et verifier qu'elles existent
6. **Lire aussi le supplementaire COMPILE SEPAREMENT.** Un
   `supplementary_materials/supplementary.tex` qui porte son propre `\documentclass`
   n'est inclus par aucun `\input{}` : les points 1-5 ne l'atteignent jamais, et la grille
   D10/C2 ne pose sur lui que des questions de QUANTITE (combien d'items, sont-ils cites,
   le corps est-il autonome), jamais de CONTENU. Le lire en entier comme le corps, et poser
   la seule question qui compte : **dit-il encore la meme chose que le corps ?**

   > **Reflexe des horodatages, a faire AVANT de lire.** `ls -l --time-style=+%F_%R` sur
   > `main.tex`, le `.tex` du supplementaire et `supp_check.md`. Un supplementaire (ou un
   > registre `supp_check.md`) **plus ancien que `main.tex` est perime par construction** des
   > que le corps a change d'analyse depuis. Vecu (mixed_infections_multimarker, 6e tour,
   > 2026-09-18) : `supplementary.tex` a 10h53, `supp_check.md` a 10h56, `main.tex` a 16h38.
   > Entre les deux, le manuscrit avait REMPLACE son design geographique primaire ; le
   > supplementaire publiait donc encore, comme tables officielles de l'article, le design que
   > le corps venait de retracter — dont un pays a 5,06x et q=0,031 dont le corps dit
   > desormais qu'il vaut 0,85x, un dénominateur annonce comme « used throughout the main
   > text » qui ne l'etait plus, et une analyse de sensibilite que les Methodes declaraient
   > inapplicable. Aucune verification du corps seul ne peut attraper cela : chaque document,
   > pris isolement, est coherent. **Severite : BLOQUANT pour la soumission**, un relecteur
   > qui ouvre le supplementaire y lit le contraire du texte.

### Phase 1bis : RECROISEMENT MECANIQUE des chiffres avec les donnees sources (OBLIGATOIRE)

**Ne jamais se fier a la relecture pour verifier un chiffre.** La relecture ne rattrape
PAS une valeur attribuee au mauvais modele/echantillon/condition : elle lit une phrase
plausible et passe. Seul le recroisement mecanique l'attrape. Cette phase est donc
obligatoire des que le manuscrit rapporte des nombres issus de calculs.

1. **Localiser les donnees sources** : fichiers de resultats (`.json`, `.csv`, logs de
   run, tableaux) produits par les scripts d'analyse. Les demander a l'utilisateur si
   leur emplacement n'est pas evident.
2. **Extraire tous les nombres du manuscrit** (abstract, texte, legendes, tables) avec
   leur contexte : a quelle condition, quel modele, quel echantillon chacun est attribue.
3. **Verifier chaque nombre contre la source**, et surtout **verifier l'ATTRIBUTION** :
   le chiffre existe-t-il bien dans les donnees, et provient-il bien de la condition
   annoncee dans la phrase ? Signaler en priorite les valeurs qui **existent dans les
   donnees mais sous une autre condition** (c'est le mode d'erreur le plus dangereux :
   le chiffre est « vrai », mais il ne dit pas ce que la phrase lui fait dire).
4. **Verifier l'HOMOGENEITE des bras de comparaison** : quand plusieurs valeurs sont
   comparees (dans une phrase, une figure, un tableau), proviennent-elles de conditions
   qui ne different QUE par le facteur dont on tire la conclusion ? Tout facteur
   supplementaire qui varie en meme temps est un facteur de confusion → BLOQUANT.
5. **Verifier la coherence interne** : abstract vs resultats vs discussion vs legendes
   vs tables. Un meme resultat doit porter le meme chiffre partout.
6. **RECALCULER les nombres DERIVES, ne pas se contenter de les retrouver.** Un nombre
   du manuscrit qui n'existe PAS tel quel dans les donnees (une difference, une somme,
   un pourcentage, un « ajoute N elements », un « sur N cas ») est **derive** : il ne
   peut pas etre valide par simple recherche dans les sources. Il doit etre **recalcule
   depuis les donnees brutes**. Les points 1-5 sont aveugles a cette classe d'erreur,
   parce que le nombre n'a aucune source a laquelle le confronter.
   **PIEGE CANONIQUE : une difference de CARDINAUX n'est pas un nombre d'ELEMENTS
   NOUVEAUX.** $|A| - |B| \neq |A \setminus B|$ des que la correspondance entre $A$ et
   $B$ n'est pas injective. Vecu (mabossDemo) : un modele etendu passait de 25 a 49
   etats stables, et le manuscrit en concluait « adds 24 states ». Le calcul de la
   difference ENSEMBLISTE reelle donnait **12** nouveaux etats seulement, les 12 autres
   etant des **dedoublements** d'etats existants (meme configuration, deux variantes
   d'une boucle bistable). Le decompte etait faux, et sa correction (49 = 25 + 12 + 12)
   s'est revelee bien plus informative que l'affirmation initiale.
   **REFLEXE : pour tout « ajoute / gagne / perd N elements », exiger le calcul de la
   difference ensembliste (ou de l'appariement explicite), jamais la soustraction des
   totaux.** Verifier de meme les pourcentages (recalculer numerateur et denominateur)
   et les « N sur M » (verifier M).

**Risque specifique aux etudes multi-variantes / multi-modeles / multi-jeux de donnees**
(frameworks de variantes, ablations, grilles d'hyperparametres, cohortes multiples) :
le recit veut une serie homogene, les donnees viennent de variantes heterogenes, et la
substitution d'un chiffre par celui d'une variante voisine est **invisible a la
relecture**. C'est le premier endroit ou chercher.

7. **Les affirmations de RANG exigent un TRI, pas une recherche.** « Les plus frequents
   sont A, B et C », « le plus conserve », « le meilleur modele », « les trois premiers » :
   ces enonces ne se verifient PAS en confirmant que A, B et C existent avec les bonnes
   valeurs, ce que fait naturellement une verification nombre par nombre. Il faut **trier
   la source entiere sur le critere annonce** et comparer le classement obtenu a celui du
   texte. Vecu (dark_enzymes) : « the most frequent are H222N n=101, Y224C n=33, and D178G
   n=23 » — les trois valeurs etaient exactes et correctement attribuees, mais le tri
   complet de la table supplementaire donnait **R175Q n=30 en troisieme position**, saute
   par le texte. Erreur contredite par la propre supplementaire du manuscrit, donc visible
   par tout relecteur qui l'ouvre. Une verification nombre par nombre ne peut pas
   l'attraper : chaque nombre pris isolement est juste.

8. **Les FOURCHETTES exigent de recalculer les deux extremes.** « ranged from X to Y »,
   « entre X et Y », « au plus X » : recalculer min et max sur l'ensemble reel des valeurs,
   jamais se contenter de verifier que X et Y apparaissent quelque part. Vecu : « mean
   pLDDT ranged from 0.85 to 0.92 » alors que les six valeurs reelles montaient a **0,97**,
   deux cibles sur six sortant de l'intervalle publie. Meme angle mort que le point 7 : la
   borne haute annoncee EXISTE bien dans les donnees, elle n'est simplement pas le maximum.

9. **La FRAICHEUR des instantanes : deux chiffres justes peuvent faire une phrase fausse.**
   Quand la source est une base VIVANTE (collection qui grossit, corpus reindexe, jeu
   nettoye), un nombre calcule le jour J et un nombre calcule le jour J+n **ne se
   juxtaposent pas**, meme si chacun est exact dans son contexte. Verifier la DATE de
   production de chaque chiffre, pas seulement sa valeur. Vecu : « les 1 387 genomes L6 de
   la collection (145 209 genomes, toutes lignees) » — le 1 387 venait d'un balayage du
   jour, le 145 209 d'une couche calculee sept semaines plus tot, et la collection en
   comptait **143 110** au moment de la redaction. Aucune verification de coherence interne
   ne peut attraper cela, puisque les deux nombres sont vrais. **Reflexe : dater les
   sources ; si deux chiffres d'une meme phrase viennent de deux instantanes, recalculer le
   plus ancien ou retirer celui qui n'est pas necessaire a l'enonce.**

10. **Les affirmations de CONTRASTE exigent de recalculer LES DEUX COTES, et de verifier
    qu'on compare bien la meme grandeur.** « X est plus conserve que Y », « les cas traites
    repondent mieux que les temoins », « A varie d'un ordre de grandeur plus que B » : ces
    enonces ont **deux** membres, et le second est presque toujours celui que personne n'a
    recalcule. Deux facons de se tromper, souvent combinees : (i) le contraste **n'existe
    pas** dans la direction annoncee ; (ii) les deux membres ne sont pas la **meme
    grandeur**, si bien que l'ecart mesure un changement de definition et non un effet.
    Vecu (dark_enzymes) : « les residus catalytiques portent des variants dans au plus
    0,04 % des genomes, alors que les codons voisins en portent un ordre de grandeur plus
    frequents ». Le membre gauche etait exact et verifie ; le membre droit n'avait jamais
    ete recalcule. En le recalculant : le maximum non-synonyme des codons voisins est
    **0,0335 %**, donc **INFERIEUR** au maximum catalytique de 0,0403 %. Le contraste
    n'existait pas. Il paraissait exister parce que le membre droit avait ete lu sur les
    variants **synonymes** (jusqu'a 0,197 %) et le membre gauche sur les **non-synonymes** :
    deux grandeurs differentes presentees comme comparables. L'enonce avait survecu a
    plusieurs relectures et a un premier claim-check parce qu'il est **plausible pour un
    specialiste du domaine**, ce qui est precisement ce qui le rendait invisible.
    **REFLEXE : pour tout comparatif, ecrire les deux nombres cote a cote avec leur
    definition exacte (meme population, meme classe d'evenement, meme denominateur) avant
    de juger l'enonce. Un contraste dont un seul membre a ete calcule n'est pas verifie.**
    Bonus frequent : le recalcul honnete livre souvent un contraste VALIDE mais different
    (ici, non-synonyme au site contre synonyme dans son propre voisinage, qui tient fixes
    le taux de mutation local et la profondeur d'echantillonnage), scientifiquement plus
    solide que l'affirmation d'origine. Corriger renforce le papier au lieu de l'affaiblir.

11. **Papier « systeme deploye » avec un depot de code associe accessible : chercher le
    chiffre-cle sur TOUT l'historique git, pas seulement la branche courante.** Si un
    depot de code correspondant au systeme decrit est accessible en local, ne pas se
    contenter de lire le `HEAD` de la branche de travail avant de conclure qu'un chiffre
    (benchmark, cout, latence) est/n'est pas retrouvable :
    ```bash
    git branch -a --format='%(refname:short)' | sed 's#^remotes/##' | sort -u > /tmp/branches.txt
    while read -r b; do git grep -qn "MON_CHIFFRE_CLE" "$b" -- '*.md' '*.tex' '*.py' '*.json' 2>/dev/null && echo "MATCH: $b"; done < /tmp/branches.txt
    ```
    Chercher aussi la mention **narrative** du processus (pas seulement le chiffre exact)
    dans les fichiers de suivi (`JOURNAL.md`, `cahier_de_labo.md`, `pistes.md`) : un
    mecanisme peut etre reellement implemente en code (verifiable, donc le recit n'est pas
    fabrique) sans que la mesure chiffree qui en decoule soit retrouvable nulle part
    (le resultat n'a jamais ete logge/sauvegarde). **Distinguer ces deux verdicts dans la
    review** : « mecanisme verifie en code, chiffre non reproductible » est une
    preoccupation MAJEURE nuancee, pas une accusation de fabrication. Si le meme depot
    contient un AUTRE papier du meme projet qui, lui, publie un harnais complet et
    versionne (scripts + sorties brutes), le signaler explicitement : cela prouve que
    l'equipe sait le faire et le fait deja ailleurs, ce qui rend l'omission plus difficile
    a excuser et la recommandation plus concrete (« faites comme dans votre autre papier »).
12. **Distinguer une propriete MESUREE d'une propriete simplement CONCUE** (« model-agnostic »,
    « extensible », « scalable »...). Chercher si le texte rapporte une EXECUTION EFFECTIVE
    qui exerce la propriete revendiquee (ex. un second fournisseur LLM reellement invoque
    de bout en bout sur le meme benchmark), pas seulement une architecture qui le
    permettrait en theorie. Si le code source est accessible, verifier que le mecanisme
    existe reellement avant de trancher : classer en MODERE (pas MAJEUR) quand la capacite
    est verifiee dans le code mais jamais exercee dans le papier — c'est une omission de
    mesure, pas une invention.

13. **Un compte annonce pour une ENUMERATION EN PROSE est un chiffre a recroiser, pas une
    tournure de style.** « the five measures... », « the four criteria... », « the three
    corrections... » : compter litteralement les items de la liste qui suit, ET chercher si
    une autre section du meme manuscrit enumere deja le meme ensemble sous une autre forme
    (une sous-liste, un total partiel donne ailleurs). Vecu (Rv2569c, 2026-09-18) : Methodes
    annoncait « the five measures... converge on one hypothesis », enumerant « two distances
    to a pocket, cryptic-pocket propensity by two predictors, the ESM-1v log-likelihood
    ratio, and conservation » (2+2+1+1 = 6, pas 5) ; les Resultats, deux paragraphes plus
    loin, disaient explicitement « two of the **four** pocket measures... », confirmant que
    le total reel est 4 (poche) + 1 (LLR) + 1 (conservation) = 6. Un `claim-check` classique
    avait explicitement ecarte cette phrase (« ne porte aucun chiffre nouveau a recroiser »)
    parce qu'elle ne contient aucune statistique calculee — exactement l'angle mort que ce
    point corrige : une prose qui annonce un compte est verifiable par simple denombrement,
    sans donnee source, et merite le meme reflexe que les points 7-10.

Consigner les ecarts trouves : ils alimentent les preoccupations MAJEURES de la review.

> **Garde-fou de methode (vecu 2026-07-31, dark_enzymes).** Les points 1-6 se font en lisant
> le texte et en cherchant ses nombres dans les sources ; les points 7-10 exigent de
> **retourner a la donnee brute et de la manipuler** (trier, calculer un extremum, lire une
> date de fichier, recalculer le membre droit d'un comparatif). Une passe qui ne fait que
> les points 1-6 conclut « aucune incoherence numerique » sur un manuscrit qui en contient
> quatre — c'est arrive le 2026-07-31 : trois erreurs de valeur trouvees par un audit
> exhaustif lance en parallele, plus un contraste entierement faux trouve seulement en
> rejouant le script source. Ne jamais rendre un verdict de Phase 1bis sans avoir
> explicitement traite les affirmations de rang, les fourchettes, les dates de calcul et
> les comparatifs.
>
> **Corollaire sur la plausibilite.** Les quatre classes partagent un trait : l'enonce faux
> est *plausible pour un expert du domaine*. La relecture par un specialiste ne les attrape
> donc pas mieux qu'une relecture naive, elle les attrape moins bien, parce que l'expertise
> fournit la justification qui manque. Le seul remede est le recalcul.

### Phase 1ter : MESURE MECANIQUE de l'economie du texte et de la tracabilite (OBLIGATOIRE)

Meme raison d'etre que la Phase 1bis, transposee de l'exactitude a l'**economie** : trois
defauts que la relecture lineaire ne peut pas voir, parce qu'ils ne se manifestent qu'en
comparant des passages DISTANTS, chacun **correct isolement**. Un relecteur qui lit de la
premiere a la derniere ligne ne les rencontre jamais ; il termine avec l'impression d'un
texte dense, et ne saura pas dire que le meme chiffre a ete redonne trois fois, ni que le
manuscrit depasse de 3000 mots la limite de la revue visee, ni qu'aucune de ses donnees
n'est tracable a sa source. Les mesurer avant la grille, pas apres.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/deai-latex/scripts/content_economy.py main.tex --limit <limite revue>
python3 ${CLAUDE_PLUGIN_ROOT}/skills/bib-check/scripts/self_citation.py main.tex --author <nom du 1er auteur>
python3 ~/.claude/skills/narratif/scripts/plan_vs_manuscrit.py [projet]
```

`narratif` est un skill personnel (source primaire `~/.claude/skills`), pas un skill du
plugin `redaction` : ne PAS utiliser `${CLAUDE_PLUGIN_ROOT}/skills/narratif/...`, ce chemin
n'existe pas (mesure le 2026-09-18, `/manuscript-review` sur Rv2892c) et fait echouer la
Phase 1ter en silence si l'echec n'est pas remarque. Verifier avant tout appel que le script
est bien present a `~/.claude/skills/narratif/scripts/plan_vs_manuscrit.py` ; a defaut, signaler
l'absence plutot que de sauter la mesure sans le dire.

Le troisieme script ne mesure rien du texte : il mesure l'ecart entre le manuscrit et le
**plan** qui l'a decide (`plan_narratif.md`, skill `/narratif`). C'est le seul instrument du
pipeline qui reponde a « cette section aurait-elle du exister ? », question qu'aucune lecture
du texte seul ne permet de poser. S'il n'y a pas de plan, le dire : le manuscrit a ete
structure sans etape de conception, et c'est en soi une remarque de relecteur.

**C1 -- Le manuscrit raconte-t-il ce qui n'a pas marche ?** Le script remonte les passages a
marqueur (tentative anterieure, bascule de methode, resultat negatif, peripetie d'acces a une
ressource). Le tri est un **jugement de relecteur**, jamais automatique, et il n'a que deux
issues :

| Ce que le passage fait | Verdict |
|---|---|
| Refute un claim que le lecteur porterait sinon ; sert de controle a un positif voisin ; borne l'espace de recherche ; previent un piege qu'un tiers reproduirait a ses frais | **Garder** — et exiger sa PUISSANCE (voir ci-dessous) |
| Raconte la chronologie du chantier, un outil ecarte sans lecon, une peripetie d'acces (403, quota, route de repli, telechargement manuel), un negatif sur une hypothese que personne n'avait | **Signaler comme a supprimer** (MINEUR, MODERE si recurrent) |

> **Exigence de puissance, a formuler comme une demande de reviewer.** Tout negatif conserve
> doit declarer **ce qui a ete cherche, avec quel outil, a quel seuil, dans quelle version de
> quelle base**. Un « no homolog was found » nu n'est pas un resultat : il est ininterpretable,
> et le reviewer suivant demandera exactement cela. Absence de puissance sur un negatif qui
> PORTE une conclusion du manuscrit → **MAJEUR**. Sur un negatif accessoire → MODERE.
>
> Le reflexe symetrique compte autant : **ne jamais demander la suppression d'un negatif
> informatif** au motif qu'il alourdit. Un resultat negatif citable est un actif rare ; c'est
> le RECIT des impasses qui est du remplissage.

**C2 -- Longueur, redites, supplementaire.** Lire les trois sorties ensemble, elles decrivent
un seul defaut structurel :

| Signal mesure | Severite indicative |
|---|---|
| Longueur > limite de la revue cible declaree | **BLOQUANT pour cette cible** (rejet mecanique au desk), a dire tel quel — mais la revue n'arbitre pas le message : si la demonstration exige cette taille, la reponse peut etre une autre cible ou le preprint, jamais l'amputation |
| n-grammes partages entre Resultats et Discussion (redite quasi verbatim) | MODERE ; MAJEUR si la Discussion refait la demonstration au lieu d'interpreter |
| Meme jeton numerique dans >= 3 sections du corps | MINEUR a MODERE — verifier d'abord : un effectif ou une longueur de proteine se repete legitimement |
| Resultats > 50 % du corps ET zero fichier supplementaire | MODERE, structurel : du materiel de reproductibilite est reste dans le corps |
| Item supplementaire jamais cite dans le corps, ou renvoi vers un chemin local (`supplementary_materials/table_S1.csv`) | MINEUR |
| Section substantielle sans ligne `% narratif:` (aucun maillon, aucune bascule) | MODERE a MAJEUR — personne ne l'a decidee ; demander ce qu'elle demontre, et si la reponse est « rien », la couper avant tout autre levier |
| Item classe SUPPLEMENTAIRE au plan mais developpe dans le corps | MODERE — signal lexical, a trancher a l'oeil ; une derive assumee se corrige au plan, pas en silence |

La recommandation de relecteur suit l'ordre des leviers, et **cet ordre fait partie de la
recommandation** : epuiser les redites d'abord, migrer verbatim vers le supplementaire
ensuite, polir en dernier. Recommander de « raccourcir » sans dire par ou revient a inviter
l'auteur a sacrifier du contenu qui n'avait pas besoin de l'etre.

**C3 -- Tracabilite de la provenance, et auto-citations.** Deux controles distincts, que la
grille D9 confondait :

1. **Tracabilite (vaut pour TOUT manuscrit, quel qu'en soit l'auteur).** La base de donnees,
   la plateforme, le pipeline, la classification ou la nomenclature dont le manuscrit tire sa
   matiere sont-ils **cites** ? Un lecteur peut-il remonter a la provenance de chaque jeu de
   donnees ? Une provenance non citee est un defaut de reproductibilite → **MAJEUR**, au meme
   titre qu'une version d'outil absente (D3). Ce controle ne depend pas de savoir qui a ecrit
   quoi : il se lit dans les Methodes.
2. **Volume d'auto-citations.** `self_citation.py --author <nom>` rend le taux. Bandes de
   lecture (heuristique de travail, a presenter comme telle, pas comme une regle editoriale
   publiee) : <= 15 % usage courant ; 15-25 % eleve, chaque entree doit soutenir un point
   distinct ; > 25 % MODERE a signaler, un editeur le remarquera. Signaler nommement les
   tapis de citations (`\citep{a,b,c}` d'un meme auteur sur un seul point) et toute
   auto-citation dont le sujet ne recoupe pas la phrase qu'elle soutient.

> **Cas particulier, a ne pas rater sur les manuscrits du groupe.** Le corpus local
> `~/docs/cv/references/{journals,conferences}.bib` permet de detecter la **SOUS-citation** :
> travaux anterieurs de l'equipe portant sur le point traite et absents de la `.bib`. Mesure
> sur le parc en 2026-08 : plusieurs manuscrits a **0 auto-citation sur 20-40 references**
> alors que leurs donnees venaient d'une plateforme publiee par les memes auteurs. Ce n'est
> pas de la modestie, c'est une rupture de chaine de provenance, et c'est le premier point a
> signaler. Sur un manuscrit EXTERNE, ce corpus n'existe pas : le controle se limite alors
> legitimement au point 1 (tracabilite) et au point 2 (volume).

Consigner les mesures dans la review avec leurs chiffres (« 14 282 mots, dont 65 % de
Resultats, 0 fichier supplementaire, 0 auto-citation sur 41 references ») : un relecteur qui
chiffre est un relecteur qu'on ne discute pas.

### Phase 2 : Grille d'evaluation (11 dimensions)

Evaluer le manuscrit sur chaque dimension. Pour chaque probleme identifie,
attribuer un niveau de severite :

| Niveau | Signification |
|--------|---------------|
| **BLOQUANT** | Empeche la publication en l'etat |
| **MAJEUR** | Affaiblit significativement la credibilite |
| **MODERE** | Amelioration necessaire mais non bloquante |
| **MINEUR** | Polish, coherence, presentation |

#### D1. Titre et Abstract
- Le titre reflète-t-il fidelement le contenu ?
- L'abstract est-il autonome (comprehensible sans lire l'article) ?
- Les claims de l'abstract sont-elles toutes soutenues dans le texte ?
- Les chiffres cles sont-ils qualifies (biais, limites) ?
- Longueur appropriee pour le journal cible ?

#### D2. Introduction
- Contexte suffisant pour un lecteur du domaine large ?
- Etat de l'art complet et equilibre ?
- Gap clairement identifie ?
- Objectifs explicites, numerotes si multiples ?
- Progression logique : contexte → gap → objectifs ?

#### D3. Methodes : Reproductibilite
- Un chercheur independant pourrait-il reproduire l'analyse ?
- Versions logicielles et parametres documentes ?
- Criteres d'inclusion/exclusion formalises et objectifs ?
- Pipeline dependant d'un outil unique non valide ? → RED FLAG
- Donnees d'entree accessibles ?
- **Papier qui mesure/compare un systeme LLM : le(s) nom(s) de modele(s) sont-ils cites
  explicitement (grep `gpt-|claude-|mistral|gemini|llama|temperature` sur tout le texte) ?
  Aucune occurrence → RED FLAG BLOQUANT/MAJEUR** : un cout ou une latence en dollars/secondes
  n'est ni interpretable ni reproductible sans savoir quel modele (version, temperature) les
  a produits, et un changement de modele non declare entre deux configurations comparees
  suffirait a expliquer l'ecart mesure.

#### D4. Methodes : Rigueur statistique
- Tests statistiques adaptes aux types de donnees ?
- Correction pour tests multiples decrite et appliquee ?
- Tailles d'echantillon suffisantes ?
- Biais d'echantillonnage identifies et traites ?
- Intervalles de confiance rapportes ?
- **Taux de succes/reussite sur petit n (< 50, frequent dans les papiers « systeme LLM
  deploye ») : calculer soi-meme l'IC de Wilson si absent du manuscrit** (ex. 10/10 →
  IC95% ≈ [69%, 100%] : un « 100% » sans reserve sur n=10 est un red flag a signaler meme
  si le manuscrit ne rapporte aucune erreur).
- Distinction correlation/causalite respectee ?

#### D5. Resultats : Coherence et completude
- Tous les objectifs annonces sont-ils traites ?
- Les resultats soutiennent-ils les claims ?
- Statistiques de genetique des populations presentes si pertinentes ?
  (pi, FST, Tajima's D, Ne, structure AMOVA...)
- Chiffres coherents entre abstract, resultats, discussion, tables ?
- Resultats negatifs rapportes honnetement ?
- **Les negatifs conserves declarent-ils leur PUISSANCE** (quoi cherche, avec quel outil, a
  quel seuil, dans quelle base et quelle version) ? Un negatif nu n'est pas interpretable (C1)
- **Le texte raconte-t-il le chantier plutot que l'etat de connaissance ?** Chronologie des
  tentatives, outils ecartes sans lecon, peripeties d'acces a une ressource : a signaler comme
  a supprimer, en distinguant soigneusement du negatif informatif, qui lui doit RESTER (C1)

#### D6. Discussion : Interpretation
- Les interpretations depassent-elles les donnees ?
- Les limites sont-elles discutees honnetement et completement ?
- Comparaison adequate avec la litterature existante ?
- Distinction entre convergence vraie et contraintes universelles ?
- Hypotheses clairement etiquetees comme telles ?
- Les resultats refutes sont-ils traites avec la meme rigueur que les confirmes ?

#### D7. Terminologie et nomenclature
- Terminologie conforme aux standards du domaine ?
- Definitions fournies pour termes non standard ?
- Coherence interne (meme terme = meme concept tout au long) ?
- Noms de genes en italique, proteines en romain ?
- Unites SI, abbreviations definies a la premiere occurrence ?

#### D8. Figures et tables
- Figures referencees dans le texte ?
- Legendes autonomes (comprehensibles sans lire le texte) ?
- Qualite suffisante (resolution, lisibilite) ?
- Tables non redondantes avec le texte ?
- Coherence des chiffres entre texte et tables ?

#### D9. Bibliographie
- References appropriees et a jour ?
- Format homogene ?
- **Provenance tracable** : la base, la plateforme, le pipeline, la nomenclature dont vient la
  matiere du manuscrit sont-ils cites ? Une provenance non citee est un defaut de
  reproductibilite → MAJEUR (C3, point 1), independamment de qui l'a publiee
- Auto-citations dans les normes (<= 15 % ; 15-25 % eleve ; > 25 % a signaler) ?
- **Sous-citation** : des travaux anterieurs manifestement pertinents (des auteurs ou non)
  manquent-ils aux postes ou le manuscrit s'appuie sur eux — donnees, methode reutilisee,
  article precedent de la serie ? Un taux d'auto-citation de 0 % sur un manuscrit qui exploite
  une ressource des auteurs est un signal, pas une vertu (C3, encadre)
- Tapis de citations d'un meme auteur sur un point unique ? → FLAG
- References manquantes pour les claims fortes ?
- Preprints ou « in preparation » pour des outils critiques ? → FLAG

> **Manuscrits TB / MTBC, validation de l'etat de l'art.** Valider la
> completude de l'etat de l'art et des citations contre `tbmonitor-papers`
> (~190k abstracts PubMed TB pre-indexes, acces SQL sub-seconde via
> `mcp__tbmonitor__execute_sql`). Objectif : faire remonter **toute
> publication recente majeure oubliee par les auteurs** sur le sujet du
> manuscrit, et la signaler explicitement dans la review.

#### D10. Structure et equilibre
- Proportions section par section equilibrees ? **Resultats > 50 % du corps = signal** (C2)
- Discussion structuree en sous-sections thematiques ?
- **La Discussion interprete-t-elle, ou refait-elle la demonstration des Resultats ?** Un
  paragraphe de Discussion supprimable sans perdre une interpretation est un doublon (C2)
- Materiaux supplementaires listes et decrits ? **Chaque item S cite au moins une fois dans le
  corps ? Zero fichier supplementaire au-dela de ~8000 mots = signal structurel** (C2)
- **Le corps reste-t-il autonome pour ses conclusions ?** Un chiffre qui soutient une
  conclusion ne doit pas vivre uniquement en supplementaire
- Longueur globale appropriee pour le journal cible ? **Mesuree (C2), sur le perimetre exact
  qu'annonce le guide auteurs** — depassement = BLOQUANT pour la soumission
- Redondances entre sections ? **Mesurees, pas estimees** : n-grammes partages et jetons
  numeriques multi-sections (C2). Recommander l'ordre des leviers, pas un « raccourcir »
  general : redites d'abord, migration verbatim ensuite, polish en dernier

#### D11. Impact et originalite
- Quelle est la contribution principale ?
- Le manuscrit change-t-il la pratique ou la comprehension ?
- Les donnees/methodes sont-elles reutilisables par d'autres ?
- Le manuscrit repond-il a un besoin reel du domaine ?

### Phase 3 : Redaction de la review

Produire la review en **francais**, en suivant strictement ce format :

```markdown
# REVIEW DE MANUSCRIT

**Titre :** [titre complet du manuscrit]
**Reviewer :** Expertise en [domaines pertinents]

---

## EVALUATION GENERALE

[Paragraphe de synthese : forces, faiblesses, positionnement.
 Doit etre lisible independamment du reste.]

**Recommandation :** [Accepte / Revisions mineures / Revisions majeures / Rejet]

---

## I. PREOCCUPATIONS MAJEURES

### 1. [Titre du point]
[Description du probleme, impact, et recommandation concrete]
**Recommandation :** [action specifique]

[Repeter pour chaque point BLOQUANT ou MAJEUR]

---

## II. PREOCCUPATIONS MODEREES

### N. [Titre]
[Plus court, mais toujours avec recommandation]

---

## III. PREOCCUPATIONS MINEURES

### N. [Titre]
[Concis, format liste acceptable]

---

## IV. POINTS DE FORCE

[5-8 points positifs specifiques et argumentes.
 NE PAS OUBLIER cette section — une review equilibree est plus credible.]

---

## V. RECOMMANDATIONS FINALES

### Obligatoires (bloquantes)
1. [...]

### Fortement souhaitables
N. [...]

### Souhaitables
N. [...]

---

**DECISION :** [Revisions majeures / mineures / etc.]
**Score :** [X/10] (potentiel Y/10 apres revisions)
```

## Consignes

### Ce que la review DOIT faire
- Lire TOUT le manuscrit avant de commencer a rediger
- Etre **specifique** : citer les numeros de ligne, les phrases problematiques
- Proposer des **solutions concretes**, pas juste signaler des problemes
- Evaluer la **coherence interne** (abstract vs resultats vs discussion vs tables)
- Verifier les **chiffres** : totaux, pourcentages, effectifs coherents ?
- Identifier les **claims non soutenues** par les donnees presentees
- Distinguer ce qui est **demontré** vs **suggere** vs **speculé**
- **Chiffrer l'economie du texte** (Phase 1ter) : longueur vs limite de la revue, redites
  mesurees, part des Resultats, inventaire du supplementaire, tracabilite de la provenance et
  taux d'auto-citation. Une remarque chiffree ne se discute pas

### Ce que la review NE DOIT PAS faire
- Survoler des sections, chaque paragraphe compte
- Etre complaisante : une review molle n'aide personne
- Etre destructrice : critiquer sans proposer
- Ignorer les points positifs : l'equilibre renforce la credibilite
- Proposer des analyses irréalisables (ex. : wet lab quand l'equipe est bioinformatique)
- Repeter les memes points sous des formulations differentes
- **Demander la suppression d'un resultat negatif informatif** : ce qui se coupe est le RECIT
  des impasses, pas le negatif qui borne une conclusion ou sert de controle
- **Recommander « de raccourcir » sans dire par ou** : donner l'ordre des leviers (redites,
  puis migration verbatim vers le supplementaire, puis polish), sinon l'auteur sacrifie du
  contenu qui n'avait pas besoin de l'etre
- **Presenter les bandes d'auto-citation comme une regle editoriale publiee** : ce sont des
  heuristiques de travail, a annoncer comme telles

### Calibration du score
| Score | Signification |
|-------|---------------|
| 9-10  | Publiable en l'etat dans Nature/Science (exceptionnel) |
| 8-8.5 | Revisions mineures, journal top-10 du domaine |
| 7-7.5 | Revisions majeures, bon potentiel apres corrections |
| 6-6.5 | Revisions majeures substantielles, potentiel incertain |
| 5-5.5 | Faiblesses structurelles, resoumission necessaire |
| <5    | Rejet recommande, problemes fondamentaux |

### Adaptation au domaine
- **Genomique/bioinformatique** : verifier reproductibilite pipeline, validation independante, standards FAIR
- **Epidemiologie** : verifier biais d'echantillonnage, correction, generalisation
- **Phylogenetique** : verifier modeles d'evolution, support branches, sensibilite parametres
- **Resistance medicamenteuse** : verifier genotypique vs phenotypique, catalogues de reference
- **NLP / evaluation de LLM / ML** : verifier variance run-a-run et significativite (sorties LLM stochastiques → un run unique ne suffit pas), IC de Wilson/bootstrap sur petits jeux de test, macro-F1 vs accuracy sur classes desequilibrees (le « best model » se renverse selon la metrique), reproductibilite du prompt (texte integral, temperature, version/date d'API, exclusion des sorties invalides), asymetrie par classe masquee par la macro-moyenne, comparaison equitable supervise fine-tune vs LLM zero/few-shot (dispositif souvent apples-to-oranges), recall=1.0 exact = comportement degenere. **Grille detaillee : `~/.claude/knowledge/manuscript-review-llm-eval.md` (a lire avant de reviewer un papier qui mesure/compare un systeme LLM).**
- **Statistique** : verifier assumptions, puissance, corrections multiples

> Note : la dimension **D5** liste des statistiques de genetique des populations (pi, FST, Tajima's D, AMOVA...), pertinentes UNIQUEMENT pour les papiers de genomique evolutive. Pour un papier hors de ce domaine (NLP, ML, ingenierie logicielle...), ignorer ces items et appliquer les criteres du domaine ci-dessus a la place.

### Sauvegarde automatique de la review

A la fin de la Phase 3, **sauvegarder systematiquement** la review dans un fichier
Markdown horodate :

1. Creer le repertoire `review/` a cote du fichier `.tex` s'il n'existe pas
2. Nommer le fichier avec la date et l'heure : `review/YYYY-MM-DD_HHhMM.md`
   (ex. `review/2026-04-05_14h32.md`)
3. Y ecrire la review complete telle qu'affichee a l'utilisateur
4. Confirmer le chemin du fichier sauvegarde dans la sortie

Cela permet de conserver un historique des reviews successives et de comparer
l'evolution du manuscrit entre deux passages.

### Si argument fourni
L'argument `$ARGUMENTS` est le chemin vers le manuscrit. Commencer la lecture immediatement.
Si pas d'argument, chercher `main.tex` dans le repertoire courant, sinon demander.


---

## Epilogue -- Resume et suggestion de suite

A la **fin de chaque invocation** (apres le rapport, le registre, ou la derniere
action du skill), ajouter systematiquement un bloc de cloture pour l'humain.

### Resume de session

Rappeler en 3-5 lignes :
- Ce qui vient d'etre fait dans cette invocation
- L'etat actuel du manuscrit (claims verifies, review en cours, references OK...)
- Les fichiers produits ou modifies

### Ecart manuscrit <-> savoir du projet (si le projet est structure)

Une review regarde le manuscrit tel qu'il est. Elle est aussi, mecaniquement, le
meilleur moment pour voir ce qu'il ne contient PAS : une review qui dit "cette
section est hors sujet" ou "ce resultat n'est pas exploite" enonce en realite une
decision de perimetre, pas un defaut de redaction.

Si la racine du projet porte un `etat_des_decouvertes.md`, verifier deux ecarts
et les rapporter en quelques lignes (sans les corriger ici) :

- **Acquis non exploites** : des enonces de §2 qui n'apparaissent nulle part dans
  le manuscrit. Chacun est soit un manque du manuscrit (a integrer), soit un
  acquis hors perimetre (destination B ou C, cf. `/recadrage`) -- jamais rien.
- **Sections en trop** : une section du manuscrit qui ne sert pas la these
  annoncee par l'abstract. C'est le symptome d'un projet qui a deborde son
  cadre ; le remede n'est pas de couper, mais de decider ou va ce qui est coupe.

Signaler le compte des deux, et proposer `/recadrage` si l'un des deux est non
vide. Ne jamais supprimer du contenu d'un manuscrit au motif qu'il est hors
sujet sans qu'une destination ait ete decidee pour lui.

### Enseignements transferables (KB de domaine, outillage)

Une review, meme auto-produite, est aussi le meilleur moment pour voir ce qu'un
manuscrit ISOLE ne revele pas : un defaut qui depasse CE manuscrit. Avant de
conclure l'epilogue, relire les preoccupations MAJEURES et MODEREES rediges en
Phase 3 et se demander, pour chacune :

1. **Fait de domaine transferable ?** Le probleme souleve etablit-il quelque
   chose qui depasse ce manuscrit — un biais methodo, un resultat de
   litterature, une regle de robustesse — et qui merite d'etre verse dans la
   base de connaissances transversale du domaine (`~/.agents/knowledge/
   <domaine>.md`, ex. `tuberculosis.md` pour un projet MTBC) ?
2. **Defaut d'outil reutilisable ?** Le probleme revele-t-il qu'un skill/outil
   canonique (`claim-check`, `bib-check`, ce skill lui-meme) rate un cas, ou
   qu'un contournement manuel a ete necessaire pour l'instruire ?

Si l'une des deux reponses est OUI : **agir tout de suite** (editer le fichier
KB ou le skill concerne), pas seulement le signaler. Si l'action est trop
lourde pour cette session, ouvrir une piste explicite dans le `pistes.md` du
projet qui trace le report et sa raison. Rapporter en une ligne dans le bloc
de cloture : « Enseignements transferables : N verses, M reportes (pistes
ouvertes), ou aucun (avec la raison) ». Ne jamais passer cette question sous
silence — c'est precisement l'angle mort que cette etape corrige.

### Suggestion de prochaine etape

Evaluer l'etat global du manuscrit et proposer **la ou les commandes prioritaires**
parmi le pipeline de qualite :

| Commande | Quand la suggerer |
|----------|-------------------|
| `/claim-check` | Claims non verifies, article modifie depuis dernier run, ou jamais execute |
| `/bib-check` | References non verifiees, nouvelles refs ajoutees, ou jamais execute |
| `/deai-latex` | Article jamais nettoye IA, ou modifie substantiellement depuis |
| `/manuscript-review` | Article pret pour une evaluation globale, ou modifications majeures appliquees |
| `/lit-review [sujet]` | Un sujet necessite un approfondissement bibliographique |
| `/reviewer-response` | Une review existe non encore traitee, ou traitement en cours |
| `/reviewer-response next` | Remarques en attente dans la review active |
| `/recadrage` | Des acquis du projet n'apparaissent pas dans le manuscrit, une section ne sert pas la these, ou le manuscrit deborde (>= 9 sections / >= 8 figures) |
| `/cadrage-editorial <cle>` | Une revue cible est deja arretee : le titre et le resume n'ont pas encore ete relus contre ce que CETTE revue publie. Cette review-ci juge le texte dans l'absolu et ne le fait pas |

**Format de la suggestion** :

```
━━━━ Prochaine etape suggeree ━━━━

Le manuscrit a ete modifie par cette session. Je recommande :

  1. /claim-check --force    ← re-verifier les claims apres les modifications
  2. /bib-check              ← verifier les nouvelles references ajoutees

(ou /reviewer-response next s'il reste des remarques en attente)
```

## Apres la review : passer les objections au filtre de la figure

Avant de conclure, enchainer **`/fig-ideation review`**. Une part des objections de
relecture ne demande pas une analyse de plus mais une **figure** de plus, et le relecteur
ne dit presque jamais « faites une figure » : il dit qu'il ne comprend pas, qu'il n'est pas
convaincu, ou que la methode n'est pas reproductible.

| Ce que le relecteur ecrit | Ce qu'il demande souvent |
|---|---|
| « la methode est difficile a suivre », « je n'ai pas pu reproduire » | un diagramme de flux des donnees, exclusions chiffrees |
| « en quoi cela differe de [travail anterieur] ? », « la nouveaute n'est pas claire » | une figure avant/apres |
| « le mecanisme propose n'est pas etaye » | un schema de mecanisme, avec ce que la donnee ne tranche pas |
| « la datation n'est pas convaincante » | une frise avec les intervalles de credibilite traces |
| « pourquoi ces seuils ? » | un arbre de decision, valeurs sur les aretes |

Le piege a ne pas manquer : **une figure ne repond qu'aux objections portant sur la
LISIBILITE de l'argument, jamais sur sa validite.** Un relecteur qui doute d'un resultat
veut une analyse ; dessiner un argument faux le rend seulement plus visible. Quand le doute
est de fond, ouvrir une piste d'analyse, et la figure vient apres.

Ce skill ne detecte pas non plus les figures **manquantes** : sa dimension D8 ne pose que
cinq questions sur les figures presentes. C'est `/fig-ideation` qui couvre cet angle mort,
ainsi que les figures deja produites mais jamais integrees au manuscrit.

Si a ton sens le travail est **termine** (toutes les reviews traitees, claims
verifies, bib OK, texte nettoye), le dire clairement :

```
━━━━ Etat du manuscrit ━━━━

Le manuscrit semble pret pour soumission/resoumission :
  ✅ Claims verifies (claim_check.md : 0 infirme)
  ✅ References verifiees (34/34, 0 suspecte)
  ✅ Review traitee (14/14 remarques resolues)
  ✅ Texte nettoye (deai-latex applique)

Aucune action supplementaire identifiee.
Porte suivante : /verdict-diffusion (le manuscrit est bien fait ; reste a
juger si le resultat merite d'etre publie, et ou).
```

**Ne jamais conclure de ce bloc que le manuscrit est a soumettre.** Tout ce que ce
skill mesure, comme `/claim-check` et `/bib-check`, c'est que le manuscrit est bien
FAIT : que ses affirmations correspondent a leurs sources, que ses references
existent, que son texte est propre. Aucune de ces dimensions ne demande si le
RESULTAT meritait d'etre ecrit. Un manuscrit bien fabrique autour d'un resultat faux
passe ici sans encombre — c'est exactement ce qui s'est produit sur
`Mycobacterium_sp_novel` (27 pages, trois relectures internes, tous les registres au
vert, decouverte centrale artefactuelle). Cette question-la est celle de la porte
3bis : passer la main a **`/verdict-diffusion`**, qui tranche entre SOUMETTRE,
DIFFUSER-SANS-COMITE, NE-PAS-DIFFUSER et ROUVRIR.
