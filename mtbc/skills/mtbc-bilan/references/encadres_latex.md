# Encadres pedagogiques : types, syntaxe LaTeX et exemples -- version integrale

Reference de `mtbc-bilan` : texte integral de la section 9.1bis. Contient les
cinq types d'encadres, la distinction originalite / remarquable, la syntaxe des
blocs raw LaTeX pour pandoc, cinq exemples longs prets a transposer, les regles
d'insertion et la syntaxe Beamer equivalente.

### 9.1bis Insertion des encadres pedagogiques

Le template PDF (`templates/bilan.latex`) definit trois environnements
`tcolorbox` dedies, et le template Beamer (`templates/bilan_slides.tex`)
definit trois commandes equivalentes. Ces encadres permettent
d'expliquer, sans rompre la narration, les notions opaques pour un
lecteur de formation math pure / info de base.

#### Cinq types d'encadres

| Type | Usage | Couleur |
|------|-------|---------|
| `notion` | Concept de domaine (ethno-linguistique, biologie, geographie, MTBC...) | Bleu |
| `methode` | Technique statistique, algorithmique, ou methodologique (test de Mantel, ABC, datation moleculaire...) | Vert |
| `originalite` | En quoi un resultat est nouveau / original / novateur **par rapport a la litterature existante** | Violet |
| `remarquable` | Pourquoi un resultat est frappant / impressionnant / non trivial **dans l'absolu**, en quoi un non-specialiste devrait y preter attention | Ambre |
| `fragilite` | Pourquoi un fait `volatile` ou `fragile` (Phase 1bis) ne peut pas etre cite tel quel : amplitude de variation, hypotheses critiques, voies de consolidation. **Obligatoire** pour tout fait central non-`etabli`. | Rouge / orange |

**Distinction `originalite` vs `remarquable`** : ce sont deux dimensions
distinctes, qui peuvent coexister sur un meme resultat.
- `originalite` repond a : *qu'apporte ce resultat que la litterature ne
  contient pas deja ?* C'est une comparaison externe, ancree dans
  references publiees.
- `remarquable` repond a : *pourquoi ce chiffre, ce pattern, cette
  observation est frappant en soi, qu'est-ce qui devrait surprendre ou
  interpeller un lecteur non specialiste ?* C'est une mise en relief
  pedagogique de l'amplitude, de la precision, de la rarete, ou des
  consequences du resultat.

Exemples illustrant la difference :
- *"57 SNP retro-mutes detectes dans L4.9"* → un encadre `remarquable`
  explique pourquoi 57 est un grand nombre (les SNP MTBC sont reputes
  irreversibles a l'echelle d'une lignee, on s'attend a 0-2 retro-mutations
  par hasard sur ce volume de donnees ; 57 est 30 fois plus eleve que la
  borne attendue) ; et un encadre `originalite` explique que la
  reversibilite n'avait jamais ete quantifiee a cette echelle dans la
  litterature MTBC.
- *"Datation MRCA de proto-L4.2 a 1240 CE [IC95 : 980-1430]"* →
  `remarquable` peut souligner la precision de l'intervalle et le fait
  que cela situe l'emergence avant les premiers contacts coloniaux,
  contrairement a l'intuition ; `originalite` peut souligner que c'est la
  premiere datation publiee de cette sous-lignee.

Un resultat peut etre `remarquable` sans etre tres `original` (confirmation
d'un pattern attendu, mais avec une amplitude saisissante) et inversement
(premiere mesure publiee, mais sans surprise particuliere). Quand le
resultat est a la fois remarquable ET original, mettre **les deux
encadres** -- ils ne se substituent pas l'un a l'autre.

#### Syntaxe Markdown (rendu PDF)

Inserer les encadres via des **blocs raw LaTeX** pandoc. La syntaxe
` ```{=latex} ` indique a pandoc de passer le contenu tel quel au moteur
LaTeX (sans tenter de l'interpreter comme du Markdown).

````markdown
```{=latex}
\begin{notion}[Bantu et Kwa : familles linguistiques d'Afrique de l'Ouest]
Les langues bantoues (Niger-Congo, branche bantoue) sont parlees par
environ 350 millions de personnes en Afrique sub-saharienne, depuis le
Cameroun jusqu'a l'Afrique du Sud. Les langues kwa (Niger-Congo, branche
kwa) sont parlees plus au nord, principalement en Cote d'Ivoire, au Ghana,
au Togo et au Benin (Akan, Ewe, Yoruba...).

L'expansion bantoue (debutee il y a ~3000-5000 ans depuis la frontiere
Cameroun-Nigeria) est l'un des evenements demographiques majeurs de
l'histoire humaine recente : elle a remodele en profondeur la structure
genetique des populations subsahariennes. Les groupes humains coevoluant
avec les ecotypes MTBC L5 et L6 (West-African 1 et 2) sont
majoritairement de langue kwa et bantoue, ce qui rend la correlation
genetique humaine / lignee MTBC particulierement informative dans cette
region. La distinction Bantu/Kwa structure ainsi les analyses
phylogeographiques de L5/L6 a un niveau plus fin que la simple
geographie.

\textit{Reference de vulgarisation : Pakendorf et al., 2011, Trends in
Genetics ; Patin et al., 2017, Science.}
\end{notion}
```
````

Autre exemple, encadre methode :

````markdown
```{=latex}
\begin{methode}[Test de Mantel partiel]
Le test de Mantel (Mantel, 1967) compare deux matrices de distances
calculees sur les memes objets : par exemple, une matrice de distances
genetiques entre souches MTBC, et une matrice de distances geographiques
entre les lieux de prelevement. Il calcule la correlation entre les
elements correspondants des deux matrices, et evalue sa significativite
par permutations (typiquement 9999) -- les permutations etant necessaires
parce que les elements d'une matrice de distances ne sont pas
independants.

Le \textit{Mantel partiel} (Smouse et al., 1986) etend cela en
controlant pour une troisieme matrice. Question typique : la correlation
genetique-langue persiste-t-elle apres avoir controle pour la geographie ?
Si oui, c'est un argument pour une coevolution culture-pathogene
au-dela de la simple proximite spatiale.

\textbf{Limites} : le test de Mantel est puissant pour detecter des
patterns globaux mais peu sensible aux structures locales. Il a aussi
une puissance statistique reduite par rapport aux methodes plus modernes
(MMRR, dbRDA), et ses p-values peuvent etre instables sur petits
echantillons. Quand un effet est detecte par Mantel partiel, il est
generalement reel ; quand il ne l'est pas, ca ne prouve rien.
\end{methode}
```
````

Autre exemple, encadre remarquable :

````markdown
```{=latex}
\begin{remarquable}[57 SNP retro-mutes dans L4.9 : un signal 30 fois au-dessus du bruit]
Pour comprendre pourquoi ce chiffre est frappant : un SNP est une
mutation ponctuelle (un nucleotide change) qui, une fois fixee dans une
lignee, est consideree comme \textit{irreversible} a l'echelle de
quelques milliers d'annees -- c'est le postulat fondateur sur lequel
repose toute la phylogenie SNP de MTBC. Sur un corpus de 1200 souches
L4.9, en supposant un taux d'erreur de sequencage de l'ordre de
$10^{-6}$ par base et le postulat d'irreversibilite, on s'attend a
detecter \textbf{0 a 2 reversions par hasard}.

Or, ce projet en detecte \textbf{57}, soit un ordre de grandeur
au-dessus de toute attente. Ce n'est pas un effet marginal : c'est un
signal massif qui exige une explication biologique. Les hypotheses en
lice (selection convergente sur certains genes, hot-spots mutationnels,
biais d'alignement contre H37Rv) ont chacune des consequences
differentes pour l'usage du barcode SNP en epidemiologie moleculaire.

Concretement, si une fraction non negligeable des SNP utilises pour
typer les souches MTBC dans les hopitaux peut retromuter, alors
certaines souches classees comme appartenant a une lignee donnee
pourraient en realite avoir reverti depuis une autre. Les consequences
diagnostiques sont potentiellement importantes -- d'ou l'interet d'aller
au bout de cette analyse.
\end{remarquable}
```
````

Autre exemple, encadre originalite :

````markdown
```{=latex}
\begin{originalite}[Premiere caracterisation phylogeographique de proto-L4.2 a l'echelle mondiale]
Les sous-lignees L4.2 avaient ete decrites par Coll et al. (2014) sur
la base de 6 souches d'Europe occidentale. Aucune etude posterieure
n'avait elargi l'echantillonnage : la lignee restait definie par 91 SNP
sur un corpus de reference qui ne capturait pas sa diversite reelle.

Ce projet apporte la premiere caracterisation a l'echelle mondiale de
proto-L4.2, sur un corpus de 412 souches reparties sur 23 pays. Il
montre que (i) la lignee a une diversite phylogeographique bien plus
riche que ce qu'indiquait l'echantillonnage initial, (ii) 28 marqueurs
SNP supplementaires sont exclusifs a proto-L4.2 et permettent un
diagnostic moleculaire plus robuste, (iii) la distribution geographique
suggere une origine est-mediterraneenne et non ouest-europeenne comme
suppose initialement.

C'est typiquement le genre de resultat qui ne pouvait pas emerger sans
acces a une base de donnees genomique mondiale -- d'ou l'apport
specifique de ce projet, qui s'appuie sur l'agregation TBannotator.
\end{originalite}
```
````

Autre exemple, encadre fragilite (a inserer apres chaque fait central
classe `volatile` ou `fragile` en Phase 1bis) :

````markdown
```{=latex}
\begin{fragilite}[Datation du MRCA proto-L4.2 : un chiffre qui ne tient pas]
La valeur centrale de 1240 CE retenue dans le bilan provient de LSD2
sur un arbre RAxML-NG (GTR+G, calibration par dates de prelevement). Or
trois methodes alternatives appliquees aux memes donnees donnent des
valeurs sensiblement differentes :

\begin{itemize}
\item BEAST tip-dating, horloge stricte : 1110 CE [IC95 980-1240]
\item BEAST node-dating, calibration fossile : 1340 CE [IC95 1230-1450]
\item LSD2 (la valeur retenue) : 1240 CE
\end{itemize}

L'amplitude inter-methodes est de \textbf{260 ans}, soit beaucoup plus
que les IC95 individuels. Le \textit{pattern qualitatif} -- emergence
anterieure aux contacts coloniaux -- est stable, mais le chiffre exact
ne peut pas etre cite tel quel dans un manuscrit sans precaution.

\textbf{Hypotheses critiques} : (i) horloge moleculaire stricte
(LSD2 et BEAST tip-dating l'imposent), (ii) absence de structure de
population sous-jacente non modelisee, (iii) representativite de
l'echantillonnage temporel.

\textbf{Voies de consolidation} :
(1) BEAST avec horloge relaxee + calibration combinee
(\texttt{/molecular-clock}) ;
(2) tip-dating sur sous-echantillonnages stratifies (jackknife) pour
borner la sensibilite empirique ;
(3) comparaison croisee avec proto-L4.2 d'autres etudes si elles
existent (\texttt{/lit-review datation L4}).
\textit{Cf. section "A faire maintenant", item "Datation BEAST horloge relaxee".}
\end{fragilite}
```
````

**Note sur le template LaTeX** : tant que `templates/bilan.latex` ne
definit pas formellement l'environnement `fragilite`, recycler
provisoirement un environnement existant (par exemple `remarquable` avec
un titre commencant par "Fragilite :") ou definir un `tcolorbox` ad hoc
en preambule. La couleur cible est rouge-orange (`!RedOrange` ou
`colback=red!5!white,colframe=red!75!black`). L'ajout formel de
`\newtcolorbox{fragilite}` est une evolution future du template.

Syntaxe Beamer equivalente (a ajouter au template `bilan_slides.tex`) :

```latex
\fragilite{MRCA proto-L4.2 : volatile}{Valeur centrale 1240 CE (LSD2),
  mais 1110-1340 CE selon la methode. Pattern qualitatif stable
  (pre-colonial), chiffre exact non citable. A consolider par BEAST
  horloge relaxee.}
```

#### Regles d'insertion

1. **Au fil du texte, pas en annexe** : un encadre est insere a la
   premiere occurrence du concept dans le bilan, jamais regroupe en
   "glossaire" en fin de document. L'idee est qu'au moment ou le lecteur
   rencontre un terme inconnu, l'explication est a portee de regard.

2. **Une seule fois par concept** : ne pas redefinir Mantel partiel
   trois fois. La premiere occurrence dans le bilan recoit l'encadre.

3. **Heavy explanations** : 4-12 phrases par encadre est la cible
   normale. Mieux vaut un encadre dense et complet qu'un encadre
   superficiel qui n'apporte rien. Inclure systematiquement :
   - **Quoi** : definition simple mais precise
   - **Pourquoi c'est utilise ici** : lien explicite avec le projet
   - **Limites / nuances** : ce qu'il faut savoir pour ne pas
     surinterpreter
   - **Reference** : article ou ouvrage de vulgarisation

4. **Simple sans etre simpliste** : ne pas dire "Mantel mesure une
   correlation" et s'arreter la. Mais ne pas non plus rentrer dans la
   theorie complete des U-statistiques. Donner l'intuition + un niveau
   de detail suffisant pour que le lecteur puisse en parler.

5. **Encadres `originalite` : un par decouverte majeure** au minimum.
   Dans la section "Decouvertes majeures et leur signification", chaque
   sous-section doit avoir son encadre `originalite` qui dit en quoi
   ce resultat est nouveau / non trivial / important par rapport a
   l'existant. C'est ce que le specialiste considere evident et que
   le profil math/info ne peut pas evaluer seul.

5bis. **Encadres `remarquable` : pour chaque resultat frappant en soi**.
   Independamment de la litterature, certains resultats meritent qu'on
   explique pourquoi ils impressionnent : amplitude inattendue, precision
   exceptionnelle, rarete d'un phenomene, contre-intuition par rapport au
   sens commun, consequences pratiques importantes. L'encadre
   `remarquable` rend ces dimensions visibles a un lecteur non
   specialiste, qui ne peut pas evaluer seul si "57 retro-mutations" ou
   "datation a 1240 CE" est banal ou extraordinaire.

   Tous les resultats du projet n'ont pas vocation a etre `remarquable` :
   reserver cet encadre aux resultats genuinement saisissants. **Cible :
   3 a 6 encadres `remarquable` par bilan**, pas un par decouverte. Si
   tout est remarquable, rien ne l'est.

   Un meme resultat peut recevoir a la fois `originalite` et
   `remarquable` quand les deux dimensions s'appliquent (cf. distinction
   plus haut). Structure type d'un encadre `remarquable` :
   (i) rappel de ce a quoi on s'attend (ordre de grandeur, intuition,
   borne theorique) ;
   (ii) ce qui est observe ;
   (iii) le ratio ou le contraste qui rend la chose frappante ;
   (iv) la consequence pratique ou conceptuelle.

6. **Encadres `methode` : un par technique non triviale**. Pour chaque
   methode statistique ou phylogenetique mentionnee dans le bilan
   (Mantel, ABC, BEAST, dN/dS, IQ-TREE+LSD2, PastML...), un encadre
   `methode` la premiere fois qu'elle apparait.

7. **Encadres `notion` : couvrir A-F de la Phase 4.6**. Passer en revue
   les six categories et inserer un encadre pour chaque concept present
   dans le projet et non maitrise par un profil math/info pure.

#### Syntaxe pour les slides Beamer

Dans le fichier `bilan_slides.tex`, utiliser les commandes definies
dans le template :

```latex
\notion{Bantu et Kwa}{Familles linguistiques d'Afrique de l'Ouest.
  Les langues bantoues s'etendent du Cameroun a l'Afrique du Sud
  (~350 M locuteurs). L'expansion bantoue (-3000 ans) a remodele
  la genetique humaine subsaharienne et structure la coevolution
  avec MTBC L5/L6.}

\methode{Test de Mantel partiel}{Compare deux matrices de distances
  en controlant pour une troisieme. Permutations pour la
  significativite. Utile pour tester correlation genetique-langue
  apres controle de la geographie.}

\nouveau{Premiere caracterisation mondiale de proto-L4.2}{Coll 2014
  decrivait la lignee sur 6 souches europeennes. Ce projet l'etend
  a 412 souches sur 23 pays, decouvre 28 SNP marqueurs
  supplementaires, et reoriente l'origine geographique suppose.}
```

**Regle slides** : sur les slides, les encadres sont plus courts (3-5
lignes max). Privilegier 1-2 encadres par slide pertinent, jamais plus.
Les explications detaillees vont dans le PDF, pas dans les slides.
