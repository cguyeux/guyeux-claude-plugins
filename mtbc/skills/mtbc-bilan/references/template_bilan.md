# Template du bilan produit -- version integrale

Reference de `mtbc-bilan` : gabarit complet du document Markdown a ecrire en
Phase 9.1, section par section, avec les consignes de redaction et les exemples
narratifs attendus pour chaque niveau de consolidation.

## Template du bilan produit

```markdown
# Bilan projet -- <nom> -- YYYY-MM-DD

## Identite
- **Projet** : <titre depuis CLAUDE.md>
- **Responsable** : Christophe Guyeux (FEMTO-ST)
- **Lignee MTBC** : <...>
- **Cree le** : <date premiere entree cahier>
- **Derniere activite** : <date derniere entree, + delta jours>
- **Chemin** : <absolu>
- **Format cahier** : cahier_de_labo.md | JOURNAL.md | les deux (anomalie)

## Verdict synthetique
> **<bouclee | a poursuivre | actions prioritaires>**
> Criteres de cloture : X/7 (dont critere 7 "consolidation" bloquant ;
> detail en section "Limites et biais").
>
> <Paragraphe de 3-5 phrases justifiant le verdict. Pas un simple
> label mais une appreciation argumentee : pourquoi ce projet est/n'est
> pas termine, quels sont les enjeux restants, quel est le rapport
> effort/gain pour continuer.>

## Etat des connaissances avant ce projet

<Cette section pose le decor scientifique : qu'est-ce que la communaute
savait (et ne savait pas) sur le sujet AVANT que ce projet ne demarre ?
C'est le "Related Work" / "Background" du bilan — sans lui, le lecteur
ne peut pas apprecier la valeur des decouvertes du projet.>

<C'est aussi la section qui contient le plus d'encadres `notion` :
chaque concept de domaine apparaissant pour la premiere fois (lignee,
ecotype, groupe ethnique, methode de typage, etc.) declenche un
encadre. Voir Phase 4.6 et 9.1bis pour la syntaxe.>

<Rediger 3-8 paragraphes de prose continue, structures par sous-themes,
qui couvrent :>

### Ce que la litterature etablissait

<Synthese des connaissances pre-existantes sur la lignee, la methode,
ou le phenomene etudie. Pour chaque fait majeur, citer la reference
(auteur, annee) et expliquer brievement la contribution.>

<Exemples de questions a couvrir selon le type de projet :>
- **Projet sur une lignee** (L4.9, La4, L4.14...) : quand et par qui
  la lignee a-t-elle ete decrite ? Quelle etait sa definition initiale ?
  Combien de souches avaient ete etudiees ? Quelle distribution
  geographique etait connue ? Quels marqueurs definissaient la lignee ?
  Quelles hypotheses existaient sur son evolution ?
- **Projet methodologique** : quelle etait la methode standard avant
  ce projet ? Quelles limites avaient ete identifiees ? Qui avait
  propose des ameliorations ?
- **Projet transversal** (resistance, coevolution...) : quel etait
  l'etat du consensus ? Quelles controverses existaient ?

<Ne pas se contenter de lister les articles — raconter l'histoire de
la connaissance sur ce sujet, en montrant comment les idees se sont
construites les unes sur les autres.>

### Lacunes et questions ouvertes

<Quelles questions restaient sans reponse ? Quelles lacunes avaient
ete identifiees explicitement dans la litterature (ou implicitement
par l'absence de travaux) ? C'est ici que le projet trouve sa
justification scientifique.>

<Exemples : "Aucune etude n'avait analyse la distribution geographique
de L4.9 a l'echelle mondiale — les travaux de Coll et al. (2014) et
Napier et al. (2020) la mentionnent comme sous-lignee de L4 sans la
caracteriser davantage." Ou : "La question de la reversibilite des SNP
chez MTBC avait ete soulevee par [ref] mais jamais quantifiee
systematiquement.">

### References fondatrices

<Tableau des 5-15 articles les plus importants pour comprendre le
contexte du projet. Ce ne sont PAS tous les articles de la
litterature_review — ce sont les references incontournables que
quelqu'un devrait lire pour comprendre d'ou part ce projet.>

| Reference | Annee | Contribution cle pour ce projet |
|-----------|-------|-------------------------------|
| Coll et al. | 2014 | Barcode SNP definissant les lignees MTBC |
| ... | ... | ... |

### Sources pour cette section

Pour construire cette section, le skill doit :

1. **Lire `litterature_review/`** integralement (s'il existe) :
   syntheses, articles cles, lacunes identifiees.
2. **Lire les references de l'article** (`article/*.bib`) pour les
   refs deja citees dans le manuscrit.
3. **Lire le cahier** : les sections "Litterature" et "Connaissances
   acquises" mentionnent souvent des faits de la litterature.
4. **Consulter `~/.claude/knowledge/tuberculosis.md`** pour le
   contexte general MTBC.
5. Si les sources locales sont insuffisantes : le signaler comme
   lacune ("cette section meriterait un `/lit-review --wide` pour
   etre completee").

**Ne JAMAIS inventer de references.** Si une affirmation n'est pas
sourcee par une reference trouvee dans les fichiers du projet ou dans
la base de connaissances, ne pas la faire ou la marquer explicitement
comme "[ref a trouver]".

---

## Etat actuel des connaissances acquises

<C'est la section centrale du bilan. Elle presente, **organisee par
theme** (et non par ordre chronologique de decouverte), l'ensemble des
connaissances actuellement consolidees sur le projet, dans la version
post-consolidation issue de la Phase 1. C'est la **carte stabilisee** de
ce qui est su aujourd'hui.>

<Pour chaque grand theme (typiquement 4-8 selon le projet : structure
phylogenetique, marqueurs definissant la lignee, datation, distribution
geographique, mecanismes evolutifs, resistance, methodologie...), ecrire
une sous-section qui consolide TOUT ce que le projet a etabli sur ce
theme. Une connaissance qui a evolue n'apparait que dans sa version
actuelle ; mentionner l'evolution en une phrase seulement si elle est
instructive (ex : "Apres correction d'un biais d'alignement contre
H37Rv, 38 SNP retro-mutes sont confirmes -- la valeur initiale de 57
incluait des artefacts.").>

<Chaque connaissance acquise est presentee **en prose**, dans une phrase
ou un paragraphe court qui integre simultanement :>

- **L'enonce** : le fait lui-meme, formule de maniere precise et
  autonome (chiffre, identifiant de marqueur, gene, date, region...).
- **La maniere dont il a ete etabli** : la donnee source (nombre de
  souches, BDD), la methode (script, outil, algorithme, modele),
  eventuellement la reference de validation. Ces informations
  s'inserent **dans la phrase** ("identifie sur 412 souches via
  `phase3_subclade_marker.py`"), pas en bloc separe.
- **Le niveau de consolidation** parmi les sept de la Phase 1bis,
  enonce **textuellement dans la phrase** : "aujourd'hui `etabli`",
  "actuellement `volatile`", etc.
- **Pour tout fait non `etabli`** : enchainer dans le paragraphe avec
  l'amplitude de variation observee, ou l'hypothese qui pourrait
  casser, et la piste de consolidation. Pas de format "Fait /
  Volatilite / Consolidation" en sous-blocs : tout cela se dit en
  prose, dans le fil d'un paragraphe argumente.

**Interdiction absolue** dans cette section : les blocs structures
type "> **Fait :** ... > **Methode :** ... > **Consolidation :** ...".
Ce format etait utilise en interne en Phase 1 pour bookkeeper la
consolidation ; il **ne doit jamais apparaitre dans le bilan ecrit**.
Une connaissance se raconte ; elle ne se ficheote pas.

<Voici comment les memes connaissances doivent etre redigees en prose.>

**Exemple narratif -- fait bien consolide** :

> Le sous-clade proto-L4.2, identifie sur 412 souches reparties dans
> 23 pays via `phase3_subclade_marker.py` (BDD `bdd/actuelle/L4/`,
> TBannotator v3.6, critere d'exclusivite >= 95 %), repose sur 28
> marqueurs SNP exclusifs. Le resultat est aujourd'hui `etabli` :
> deux reproductions independantes a un mois d'intervalle, apres
> ajout de souches au corpus, ont restitue exactement les memes
> 28 marqueurs, et le claim-check confirme leur tracabilite jusqu'a
> la BDD source.

**Exemple narratif -- fait volatile** :

> La datation du MRCA de proto-L4.2 reste le point le plus instable
> de l'etude. La methode LSD2 (sur arbre RAxML-NG GTR+G, 1000
> bootstraps, calibration par dates de prelevement) place le MRCA
> aux alentours de 1240 CE, ce qui le situe avant les premiers
> contacts coloniaux europeens-americains : un resultat
> contre-intuitif pour une sous-lignee initialement decrite en
> Europe occidentale. Mais la valeur est `volatile` : BEAST en
> tip-dating donne 1110 CE [IC95 980-1240], et BEAST en node-dating
> avec calibration fossile remonte a 1340 CE [IC95 1230-1450].
> Soit une amplitude inter-methode de 330 ans pour la valeur centrale,
> bien superieure aux intervalles internes a chaque methode. Le
> pattern qualitatif (anteriorite aux contacts coloniaux) est
> robuste, mais le chiffre exact ne peut pas etre cite sans reserve.
> Deux pistes de consolidation existent : refaire BEAST avec une
> horloge relaxee et une calibration combinee (`/molecular-clock`),
> et lancer un tip-dating sur sous-echantillonnage stratifie pour
> evaluer la stabilite empirique (Cf. section "A faire maintenant").

**Exemple narratif -- fait fragile** :

> Le signal d'expansion demographique de L5 au XVIIIe siecle, obtenu
> par skyline BEAST (modele coalescent constant-then-growth,
> calibration par tip-dates), est qualifie de `fragile` parce qu'il
> repose sur trois hypotheses fortes : horloge moleculaire stricte,
> absence de structure de population non modelisee, echantillonnage
> representatif. Or aucune de ces hypotheses n'a ete testee sur les
> sous-populations connues de L5, et la violation de la deuxieme
> peut a elle seule generer un signal d'expansion fictif. Le
> resultat reste cite avec precaution ; sa consolidation passe par
> un refit avec multi-tree skyline et un sous-echantillonnage
> equilibre par region.

**Exemple narratif -- fait hypothetique** :

> L'hypothese actuelle pour expliquer les retro-mutations de L4.9
> est une selection convergente agissant specifiquement sur katG et
> inhA, deux genes cibles d'antibiotiques antituberculeux. Cette
> piste decoule de l'interpretation des resultats de
> `phase5_retromutation.py`, qui montrent une concentration des
> retro-mutations dans ces deux genes, mais elle n'a fait l'objet
> d'aucun test formel : ni dN/dS, ni McDonald-Kreitman. Le statut
> reste donc `hypothetique`, et une alternative reste plausible --
> des hot-spots mutationnels intrinseques aux regions concernees,
> independants de toute pression selective. Trancher entre les deux
> demande un appel au skill `/mk-ascertainment` sur katG et inhA,
> ou une comparaison avec les SNP non retro-mutes des memes genes.

### Themes (a adapter au projet)

#### Structure phylogenetique et clades
<Consolidation des connaissances sur l'arbre, les sous-clades, leur
support, leurs definitions.>

#### Marqueurs et signatures genetiques
<Consolidation des SNP, indels, signatures specifiques etablies par
le projet.>

#### Datation et evolution temporelle
<Si applicable : MRCA, age des clades, signaux de demographie.>

#### Distribution geographique et hote
<Si applicable : phylogeographie, associations ethniques, ecotypes.>

#### Mecanismes biologiques invoques
<Consolidation des hypotheses biologiques en cours : selection,
goulot, retro-mutation, hot-spots mutationnels... avec le statut de
chacune (test fait, en cours, hypothese non testee).>

#### Methodologie etablie par le projet
<Si le projet a developpe un workflow ou un outil reutilisable :
le decrire ici comme une connaissance methodologique acquise.>

<Inserer ici les encadres `notion`, `methode`, `originalite`,
`remarquable`, et `fragilite` selon les regles de la Phase 4.6,
9.1bis, et 1bis. L'etat actuel des connaissances est l'endroit le
plus dense en encadres pedagogiques. **Tout fait central marque
`volatile` ou `fragile` recoit obligatoirement un encadre
`fragilite`** qui explicite l'amplitude / l'hypothese critique et
renvoie a la piste de consolidation.>

## Apercu chronologique

<Section **courte** (4-8 phrases, pas plus) qui resume comment l'etat
de connaissance s'est construit, en ne retenant que les tournants
significatifs. NE PAS rentrer dans le detail des sessions ni de chaque
iteration ; donner les jalons : phase de demarrage, premier resultat
marquant, reorientation eventuelle, decouverte majeure, etat actuel.>

<Exemple de ton :>

> Le projet a demarre en septembre 2025 par un controle qualite des
> donnees TBannotator pour L4 (412 souches retenues). En decembre, la
> phase de typage a fait emerger un sous-clade non decrit dans la
> litterature, ce qui a reoriente l'etude vers la caracterisation de
> proto-L4.2. La datation moleculaire (mars 2026) a place le MRCA au
> XIIIe siecle, et la phylogeographie associee a fait l'objet d'un
> manuscrit soumis en avril 2026. L'etude est aujourd'hui en revision.

<Si une evolution d'une connaissance merite d'etre soulignee (ex :
correction d'un biais qui a divise par deux un effet), le mentionner
en une phrase. Tout le reste de la chronologie detaillee reste dans
le cahier de labo, pas dans le bilan.>

## Decouvertes majeures et leur signification

<Cette section met en relief, parmi l'etat actuel des connaissances
(section "Etat actuel des connaissances acquises"), les decouvertes les
plus significatives. C'est un **zoom commente** sur les 8-10 faits qui
font la valeur scientifique du projet, presentes dans leur **version
consolidee** (post-Phase 1).>

Pour chaque decouverte marquante (pas plus de 8-10, selectionner les
plus significatives si le projet est riche) :

### 4.N. <Titre descriptif de la decouverte>

<**Texte uniquement en prose**, pas de bloc "Etabli par / Niveau de
consolidation / Date" en en-tete. Le titre h3 suffit. Les informations
factuelles (methode d'etablissement, niveau de consolidation, date)
sont integrees dans les phrases qui suivent.>

<Rediger un **paragraphe argumentatif de 6 a 12 phrases** (et non
3-6 lignes en liste a puces) qui raconte la decouverte dans sa version
consolidee. Le paragraphe doit naturellement contenir, dans l'ordre
narratif qui convient le mieux :>

- le fait brut consolide, avec les chiffres exacts (sans les recopier en
  bullet : les inserer dans la phrase) ;
- la maniere dont il a ete etabli (donnees, script, outil) -- en une
  proposition incise, pas en ligne separee ;
- le **niveau de consolidation** enonce textuellement ("aujourd'hui
  `etabli`", "actuellement `volatile`", etc.) et, pour les faits non
  `etabli`, l'amplitude de variation ou l'hypothese critique tissee
  dans le paragraphe ;
- le mecanisme biologique sous-jacent (connu ou hypothetique) ;
- le lien argumente avec la litterature : ce que tel auteur (Coll,
  Stucki, Napier, Freschi...) disait jusqu'ici, et ce que ce projet
  confirme, contredit, etend ou nuance. Les citations sont integrees
  dans le texte, pas listees ;
- la **portee scientifique** : qu'est-ce que ce resultat change dans
  l'image globale de MTBC, du clade, ou de la methode ? Quelle est
  l'implication pour la suite du projet ou pour le terrain ?

<Si la valeur consolidee differe d'une valeur anterieure et que
l'evolution est instructive, une phrase de note dans le paragraphe
("Initialement estime a X, corrige a Y apres [methode/correction].").
Ne PAS detailler chaque iteration.>

<**Exemple de paragraphe attendu** (a transposer au contexte) :>

> La caracterisation phylogeographique mondiale de proto-L4.2 constitue
> le resultat le plus structurant de l'etude. A partir d'un corpus de
> 412 souches reparties dans 23 pays, extrait de TBannotator v3.6 puis
> filtre par `phase3_subclade_marker.py` (criteres d'exclusivite >= 95 %),
> 28 marqueurs SNP nouveaux et distincts de ceux de Coll *et al.* (2014)
> ont ete identifies, definissant la sous-lignee a une resolution
> jusque-la inedite. Le resultat est aujourd'hui `etabli` : deux
> reproductions independantes a un mois d'intervalle ont restitue le
> meme jeu de marqueurs, et le claim-check confirme la tracabilite
> jusqu'a la BDD source. La distribution geographique observee inverse
> le recit standard : alors que la lignee L4.2 avait ete decrite en
> Europe occidentale par Coll *et al.* sur six souches, la
> caracterisation mondiale fait apparaitre un noyau de diversite
> est-mediterraneen et levantin, suggerant que l'echantillonnage
> europeen initial capturait seulement la frange terminale de
> l'expansion. Cette geographie remaniee est compatible avec une
> emergence avant les contacts coloniaux, hypothese renforcee par la
> datation moleculaire (cf. section suivante), mais elle reste fragile
> sur la position exacte du foyer ancestral : les 23 pays
> d'echantillonnage ne couvrent pas l'Asie centrale, qui pourrait
> heberger les branches profondes manquantes. Pour la suite du projet,
> cela ouvre deux pistes precises : un appel a TBannotator restreint au
> Caucase et a l'Asie centrale, et une reconstruction d'etats ancestraux
> sur l'arbre phylogeographique enrichi.

<**Encadre `originalite` obligatoire** apres ce paragraphe : expliquer
en quoi ce resultat est nouveau / non trivial / important par rapport a
l'existant. Ce qu'un specialiste considere evident et qu'un profil
math/info pure ne peut pas evaluer seul. Voir Phase 9.1bis.>

<**Encadre `remarquable` si la decouverte est saisissante en soi** :
amplitude inattendue, precision exceptionnelle, contre-intuition,
consequence pratique majeure. Distinct de `originalite` (qui se compare
a la litterature) -- ici on rend pedagogique l'idee que "ce chiffre /
ce pattern devrait surprendre". Voir Phase 9.1bis pour la distinction
detaillee. Pas systematique : reserver aux resultats genuinement
frappants (3-6 par bilan max).>

<**Encadre `methode` si pertinent** : si la decouverte repose sur une
technique non triviale (Mantel partiel, ABC, dN/dS, ancestral state
reconstruction...), inserer un encadre `methode` la premiere fois que
la technique apparait dans le bilan.>

<Si le resultat est negatif (hypothese refutee, methode qui echoue),
expliquer en quoi cet echec est informatif et ce qu'il enseigne.>

## Donnees et analyses : etat des lieux

<Paragraphe introductif decrivant la masse de donnees accumulee et les
grandes etapes analytiques. Pas une liste seche — un survol qui donne
au lecteur une idee de l'ampleur du travail realise.>

<Exemple de ton : "Le projet repose sur un corpus de N souches
rassemblees dans la BDD centrale, dont les genomes ont ete annotes par
TBannotator v3.6. L'analyse s'est deployee en K phases, depuis le
controle qualite initial des variants jusqu'a la reconstruction
phylogenetique par maximum de vraisemblance. Les artefacts principaux
comprennent [arbre ML de N feuilles, matrice de distances SNP, K
figures de phylogeographie].">

### Vue schematique du pipeline

**IMPORTANT : le diagramme de pipeline est genere en TikZ**, insere
dans le Markdown via un bloc raw LaTeX. Ne JAMAIS tenter de dessiner
un pipeline en texte/ASCII/Unicode — c'est illisible en PDF.

Generer un bloc ```` ```{=latex} ```` contenant un `\begin{tikzpicture}`
qui represente le pipeline sous forme de boites reliees par des fleches.

**Modele de reference** (adapter au projet reel — phases, outils,
statuts) :

````markdown
```{=latex}
\begin{center}
\begin{tikzpicture}[
  phase/.style={
    rectangle, rounded corners=3pt, draw=accent, fill=accent!8,
    minimum width=13cm, minimum height=1.1cm, align=left,
    font=\small, text=darkgray, inner sep=8pt
  },
  arrow/.style={-{Stealth[length=5pt]}, thick, accent},
  done/.style={font=\small\bfseries, verdictgreen},
  partial/.style={font=\small\bfseries, verdictorange},
  node distance=0.5cm
]
\node[phase] (p1) {\textbf{Phase 1 — Contrôle qualité}\\
  bcftools, TBannotator v3.6 \hfill \textcolor{verdictgreen}{\textbf{OK}}\\
  \textit{→ N souches retenues sur M candidates, K variants filtrés}};

\node[phase, below=of p1] (p2) {\textbf{Phase 2 — Arbre ML}\\
  RAxML-NG (GTR+G, 1000 bootstraps) \hfill \textcolor{verdictgreen}{\textbf{OK}}\\
  \textit{→ Arbre de N feuilles, support moyen X\%}};

\node[phase, below=of p2] (p3) {\textbf{Phase 3 — Phylogéographie}\\
  geo\_map.py, choropleth \hfill \textcolor{verdictgreen}{\textbf{OK}}\\
  \textit{→ K figures, distribution dans P pays}};

\node[phase, below=of p3] (p4) {\textbf{Phase 4 — Datation moléculaire}\\
  IQ-TREE + LSD2 \hfill \textcolor{verdictorange}{\textbf{À faire}}\\
  \textit{→ Prérequis : fichier de dates des souches}};

\draw[arrow] (p1) -- (p2);
\draw[arrow] (p2) -- (p3);
\draw[arrow] (p3) -- (p4);
\end{tikzpicture}
\end{center}
```
````

**Regles pour le diagramme** :

1. **Une boite par phase reelle du projet** (pas de phases inventees).
   Lire les scripts `analyses/phase*_*.py` pour identifier les phases.
2. **Chaque boite contient** : titre de la phase, outil(s) utilise(s),
   statut (OK en vert, Partiel en orange, A faire en orange), et une
   ligne italique resumant le resultat concret.
3. **Fleches** entre les phases dans l'ordre sequentiel. Si deux phases
   sont independantes, les placer cote a cote (utiliser `right=of` au
   lieu de `below=of`).
4. **Largeur fixe** (`minimum width=13cm`) pour que toutes les boites
   soient alignees. Ajuster si le texte deborde.
5. **Couleurs** : utiliser les couleurs definies dans le template
   (`accent`, `verdictgreen`, `verdictorange`, `darkgray`). Ne pas
   definir de nouvelles couleurs.
6. **Ne pas surcharger** : max 8 phases. Si le projet en a plus,
   regrouper les phases proches.

### Donnees cles

| Ressource | Detail | Localisation |
|-----------|--------|-------------|
| BDD | N souches | `../../bdd/actuelle/<lignee>/` |
| Arbre ML | N feuilles, bootstrap X | `resultats/xxx.nwk` |
| ... | ... | ... |

## Etat du manuscrit

<Paragraphe decrivant l'avancement du manuscrit. Pas une liste de
sections — une evaluation qualitative : le manuscrit est-il coherent
avec les decouvertes ? Les resultats les plus importants y figurent-ils ?
La narration est-elle convaincante ?>

- **Structure** : <sections redigees, sections manquantes>
- **Verification factuelle** : <claims verifies/infirmes/a verifier>
- **Reviews** : <statut, points saillants des reviews recues>
- **Figures** : <adequation avec les resultats>
- **Statut** : en preparation | soumis | en revision | accepte | publie

<Si des claims ont ete infirmes par le claim-check, expliquer lesquels
et ce que ca implique pour le manuscrit.>

## Paysage de la litterature

<C'est la section ou la Phase 4 se materialise. Ecrire un ou plusieurs
paragraphes qui situent le projet dans le paysage de la recherche
publiee. Ce n'est PAS un inventaire de references — c'est une mise en
contexte qui aide a comprendre l'importance (ou non) du projet.>

<Questions auxquelles cette section doit repondre :>
- Que sait la communaute sur ce sujet ? Quels sont les travaux fondateurs ?
- En quoi ce projet apporte quelque chose de nouveau par rapport a l'existant ?
- Y a-t-il des resultats du projet qui contredisent la litterature ?
  (Si oui, c'est potentiellement le point le plus fort du bilan.)
- Quelles lacunes de la litterature ce projet pourrait-il combler ?
- Y a-t-il des travaux recents qui changent la donne ?

<Citer les references specifiques, pas juste "la litterature montre que".>

### Lacunes exploitables

<Pour chaque lacune identifiee dans la litterature ET adressable avec
les donnees du projet, expliquer en 2-3 phrases pourquoi c'est une
opportunite et comment le projet pourrait la combler.>

## A faire maintenant

<Cette section est **factuelle et tracee** : elle liste les choses
memorisees dans le cahier de labo qui n'ont pas ete faites. C'est la
valeur pratique du bilan -- ne laisser aucun fil pendant inapercu.>

<Paragraphe introductif : combien d'intentions non honorees ont ete
extraites, sur quelle periode du cahier elles s'etendent, et quelle est
la part de `a_faire` vs `partiellement_fait` (issue de la Phase 5.A).>

<Pour chaque intention non honoree, un bloc structure :>

### <Titre court de l'intention>

**Statut** : `a_faire` | `partiellement_fait`
**Origine** : entree du cahier du `YYYY-MM-DD`
**Citation** (si formulation marquante) : *"<copier la phrase exacte
du cahier>"*

<Paragraphe de 2-5 phrases qui explique :>
- **Ce qui etait prevu** (formulation precise du cahier).
- **Pourquoi ca avait ete prevu** (motivation memorisee : verifier une
  hypothese, repondre a un reviewer, completer une analyse, integrer
  une donnee externe...).
- **Ce qui manque concretement** pour l'executer (donnee, decision,
  temps, outil, prerequis methodologique).
- **Si partiel** : ou ca s'est arrete et quel etait le dernier etat.

**Commande suggeree** (si applicable) : `/<skill> <args>`
**Estimation effort** : faible | moyen | important

<Repeter pour chaque intention. Si plus de 10 intentions emergent,
regrouper celles qui sont semantiquement proches (ex : "Verifications
factuelles sur le manuscrit" qui regroupe 4 items).>

<Si la liste est vide -- toutes les intentions memorisees ont ete
realisees -- le dire explicitement et le considerer comme un critere
favorable pour le verdict "bouclee".>

## Pistes d'approfondissement

<Cette section est **prospective** : elle propose des nouvelles
directions qui ne sont pas dans le cahier, deduites de l'analyse
(inventaire des donnees, lacunes de la litterature, convergences
inter-projets). A distinguer nettement de "A faire maintenant" qui
trace les intentions deja memorisees.>

<Paragraphe introductif : combien de pistes emergent, d'ou elles
viennent (litterature, inventaire, convergence), et quelle est
la logique globale.>

### 8.N. <Titre de la piste>

**Priorite** : haute | moyenne | basse
**Score** : X.X (valeur Y/3, faisabilite Z/3, cout W/3)
**Origine** : <cahier YYYY-MM-DD | lacune litteraire | angle mort
methodologique | convergence inter-projets>

<Paragraphe de 4-8 phrases qui argumente scientifiquement pourquoi
cette piste vaut la peine. Inclure :>
- **La question** : que cherche-t-on a savoir ?
- **Le raisonnement** : pourquoi est-ce que cette question est
  interessante dans le contexte de ce projet ET de la litterature ?
  Quels articles suggerent que c'est un sujet porteur ? Quelle lacune
  ca comblerait ?
- **La methode** : comment proceder concretement ? Quel skill utiliser,
  avec quels parametres, sur quelles donnees ?
- **Le resultat attendu** : qu'est-ce qu'on espere trouver, et qu'est-ce
  que ca changerait pour les conclusions du projet ?
- **Les risques** : qu'est-ce qui pourrait ne pas marcher, et pourquoi
  ca vaut quand meme le coup ?

**Commande suggeree** : `/<skill> <args>`
**Prerequis** : <ce qu'il faut avant de lancer>

<Repeter pour chaque piste. Les pistes basses priorite peuvent etre
plus courtes (2-3 phrases) mais doivent quand meme etre argumentees,
pas juste listees.>

### Skills suggeres (si pertinent)

<Si une piste haute priorite ne peut etre couverte par aucun skill
existant, proposer la creation d'un nouveau skill avec nom, description,
et justification.>

## Convergences inter-projets

<Paragraphe (pas une liste) decrivant les projets MTBC voisins qui
partagent des questions, des donnees, ou des methodes avec ce projet.
Expliquer concretement ce que la mutualisation apporterait.>

## Limites et biais

<Paragraphe discutant honnetement les limites du projet. Pour chaque
limite, expliquer son impact sur les conclusions et si elle est
remediable ou inherente.>

<Points a toujours evaluer :>
- Biais de reference H37Rv (golden law MTBC)
- Taille et representativite de l'echantillon
- Couverture geographique et temporelle
- Biais d'echantillonnage (quelles souches sont disponibles et pourquoi)
- Limites des outils utilises

### Inventaire des faits fragiles ou volatils

<Cette sous-section recapitule explicitement les faits du projet dont
le niveau de consolidation (Phase 1bis) n'est pas `etabli` ni
`convergent`. Pour chacun :>

| Fait | Niveau | Amplitude / hypothese critique | Piste de consolidation |
|------|--------|-------------------------------|------------------------|
| <fait> | volatile | 1080-1410 CE (260 ans inter-methodes) | BEAST horloge relaxee (`/molecular-clock`) |
| <fait> | fragile | suppose horloge stricte, non teste | jackknife + multi-tree skyline |
| <fait> | hypothetique | mecanisme non teste | `/mk-ascertainment` sur katG/inhA |

<Le critere 7 de cloture (Phase 8) renvoie a ce tableau : tant qu'il
contient un fait central, le projet n'est pas boucle.>

## Anomalies detectees

<Vide ou paragraphe (pas une liste seche) : double format cahier, BDD
absente, phase sans script, claim non verifie depuis X jours, etc.
Pour chaque anomalie, suggerer une action corrective.>

## Plan d'action pour la prochaine session

<Pas une simple liste de commandes -- un paragraphe qui sequentialise
les actions en expliquant la logique, en **piochant en priorite dans
"A faire maintenant"** (intentions deja memorisees, donc d'effort faible
ou prevu) avant de proposer des elements de "Pistes d'approfondissement"
(nouvelles directions). La logique typique : "Commencer par finaliser
[intention non honoree X] car [raison], ce qui debloque ensuite la
piste prospective [Y]." Puis les commandes concretes :>

1. `/<skill> <args>` -- <justification, source : A faire / Piste>
2. `/<skill> <args>` -- <justification, source : A faire / Piste>
3. `/<skill> <args>` -- <justification, source : A faire / Piste>
```
