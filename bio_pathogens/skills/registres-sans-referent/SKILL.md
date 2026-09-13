---
name: registres-sans-referent
description: >-
  Auditer et reparer les ENONCES d'un depot dont la nomenclature a bouge : noms
  de clades qui ne designent plus rien, effectifs perimes, enonces refutes qui
  survivent ailleurs, et le cas qu'aucun test d'existence n'attrape, le label
  VIVANT mais FAUX d'une table de correspondance. Mesure d'abord (combien, ou,
  dans quel fichier), repare ensuite en posant un renvoi de peremption en tete
  de chaque entree concernee, sans jamais reecrire l'entree elle-meme.

  Utiliser quand : une lignee vient d'etre renommee, re-peignee ou re-decoupee ;
  un effectif cite ne correspond plus au disque ; un resultat s'appuie sur un
  clade dont le nom a change ; une base de connaissances partagee entre projets
  nomme des clades ; avant de reutiliser une calibration ou une mesure datee ;
  a chaque ouverture d'iteration sur un projet taxonomique.
---

# Registres sans referent

## Le probleme, et pourquoi il ne se voit pas

Un nom de clade n'est pas une donnee stable. Quand une taxonomie est re-peignee, les
affirmations deja ecrites continuent de nommer des clades avec les noms d'avant : elles
restent vraies comme faits et deviennent fausses comme adresses. Rien ne le signale, et
l'erreur se propage d'autant mieux que le fichier est lu au demarrage de chaque session.

Cas fondateur, depot `mtbc`, septembre 2026 : deux renommages successifs ont laisse 98 labels
sans referent dans 54 fichiers, dont 52 sans le moindre marqueur de peremption, et cinq
effectifs faux sur douze dans le fichier le plus lu du projet. En parallele, une calibration
refutee a survecu six jours dans ce meme fichier apres que sa refutation eut ete ecrite
ailleurs.

## Les cinq controles, du plus simple au moins evident

**1. Le label sans referent.** Chaque nom de clade cite dans la prose existe-t-il encore, sur
disque ou au registre autoritaire ? Trois verdicts : `EXISTE` (repertoire present),
`NOEUD_INTERNE` (absent du disque mais present au registre, ou prefixe strict d'un label
existant), `INCONNU` (sans referent). Un `INCONNU` n'est pas forcement une faute : il peut etre
cite comme perime avec sa correction a cote. **Ce qui compte est un `INCONNU` cite SANS marqueur
de peremption.**

**2. L'effectif perime.** Quand une ligne annonce un effectif a cote d'un label unique, le
comparer au cumul reel du sous-arbre. Ne jamais recopier un effectif : le mesurer, ou renvoyer
au registre.

**3. Le label VIVANT mais FAUX.** C'est le controle que personne n'ecrit, et le seul qui attrape
le cas dangereux. Une table de correspondance souche vers clade se controle par comparaison au
placement REEL sur disque, jamais par un test d'existence du label : un label qui existe encore
mais designe un autre groupe passe tous les tests d'existence, et une jointure rattachera
silencieusement la souche au mauvais clade. Mesure du cas fondateur : sur 13 414 lignes, 113
portaient le placement reel, 12 297 un label mort et **654 un label vivant et faux**.

**4. L'enonce refute qui survit ailleurs.** Rendre une source accessible ne corrige pas la
propagation. Ce controle-ci lit un registre DECLARATIF, `refutations.tsv`, ou l'on inscrit une
ligne au moment ou l'on refute quelque chose, et verifie que le jeton ne survit pas comme
affirmation dans un fichier qui pilote le travail. **Ne pas essayer de deviner les enonces
refutes par regex** : la version heuristique a signale 74 jetons sur 86, presque tous legitimes,
parce qu'une phrase de correction porte l'ancien ET le nouveau (« le taux passe de 0,2862 a
0,446 ») et qu'un meme nombre a des usages sans rapport (la souche « Pasteur 1908 » n'est pas la
calibration « 1908 »). Elle reste disponible en mode decouverte, hors indicateur.

**5. Le label encode dans un NOM DE FICHIER.** Les quatre controles ci-dessus lisent le CONTENU
de fichiers texte et ne voient donc pas un repertoire de donnees dont les NOMS portent des
labels : jeux de marqueurs par clade, alignements, figures, sorties par sous-lignee. C'est un
angle mort entier, et il est souvent le plus peuple. Le controle est le meme que le 1 applique
aux noms, PLUS le controle 3 applique au contenu des fichiers dont le nom survit — et c'est la
seconde moitie qui paie. Mesure du cas fondateur (`Bovis_full/data/markers_v2/`, 2026-09-12) :
**634 fichiers, 628 noms sans referent, et les 6 noms encore vivants decrivaient tous un AUTRE
clade**, intersection de marqueurs VIDE avec l'entite de leur propre nom et appariement parfait
(jaccard 1,000, cinq sur six) avec une autre. Le nombre de fichiers utilisables etait donc zero
et non six. Mecanisme a connaitre : un decalage de niveau LIBERE des noms, qui sont ensuite
REATTRIBUES a d'autres clades ; le fichier reste juste, c'est le nom qui change de proprietaire.

Deux consequences pratiques. **Compter les fichiers avant de citer un chiffre** : le registre
annoncait « ~73 fichiers », il en portait 634, l'enonce datant d'avant les iterations qui ont
produit l'essentiel du repertoire. **Ne pas regenerer par reflexe** : si un registre autoritaire
couvre deja le besoin sous la nomenclature courante, regenerer localement recree la source de
verite concurrente que la gouvernance interdit ; et ne pas supprimer non plus, car des scripts
lisent ces chemins et ces fichiers tracent la construction des clades. Le geste est le bandeau,
plus un arbitrage separe sur les seuls faux amis, qui sont les seuls a pouvoir tromper un script
en silence.

## Les pieges mesures, a ne pas refaire

- **La casse.** Un motif de peremption sensible a la casse ne voit pas les bandeaux ecrits a la
  main, qui crient en majuscules (« TOUT ce qui suit est HISTORIQUE », « N'EXISTE PLUS »). Deux
  fichiers correctement marques etaient comptes comme nus : le chiffre rendu etait une borne
  haute de la dette.
- **Le critere morphologique.** Distinguer un vrai label perime d'un label d'exemple ne se fait
  PAS sur la forme : « deux chiffres finaux = exemple » jette `Bovis.12`, vrai label de
  l'ancienne racine, qui allait jusqu'a `Bovis.53`. Le critere qui marche est CONTEXTUEL,
  n'ecarter que si la phrase parle d'un piege de nommage.
- **Le contexte deborde la ligne.** En markdown a retours durs, « un piege de glob » et les
  labels qu'il cite tombent sur deux lignes voisines : un critere contextuel evalue ligne par
  ligne rate son propre cas. Fenetre de plus ou moins une ligne, reservee au contexte d'exemple.
  Ne PAS l'elargir au marqueur de peremption : cela ferait tomber la dette pour de mauvaises
  raisons, ce qui est le mauvais sens d'erreur.
- **Le separateur de milliers.** « 70 722 » contient « 722 » comme mot entier.
- **Le nom de fichier cite dans la prose.** Ecrire `Bovis.2.2.1.1.txt` dans un texte fait capter
  `Bovis.2.2.1.1.txt` comme label, verdict INCONNU, alors que le label sous-jacent existe : c'est
  l'extension qui cree le faux positif. Mesure sans gravite mais qui pollue un compteur cense
  rester a zero. Contourner en redigeant (« le nom perime `X.txt` designe en fait Y ») plutot qu'en
  elargissant le regex, car retirer les extensions ferait disparaitre le controle 5.
- **Un zero ne vaut rien sans temoin positif.** Un compteur a zero dit aussi bien « plus de
  dette » que « le filtre a tout mange ». Le script embarque trois lignes synthetiques dont le
  verdict est connu et rend `INSTRUMENT_VOIT` ou `INSTRUMENT_AVEUGLE`.

## Reparer sans reecrire

La reparation n'est PAS de corriger les entrees : elles consignent des faits dates, le plus
souvent encore vrais. C'est de poser en tete de chaque entree concernee un renvoi qui dit que
les noms employes sont morts, plus un bandeau global en tete de fichier qui porte l'histoire des
renommages et l'adresse de la verite du jour.

Regles de pose, toutes issues d'un echec mesure :

- **Un registre de pistes ne recoit qu'UN bandeau, en tete.** Ses sous-pistes sont des items de
  liste lus par un parseur ; un bloc insere entre deux items est rattache au corps du precedent.
  Verifier apres pose que le registre se relit a l'identique, hors numeros de ligne.
- **Un cahier append-only ne se retouche pas**, meme pour l'avertir. Signaler dans l'entree du
  jour a la place.
- **Une entree deja marquee a la main ne recoit rien** : son bandeau est souvent meilleur.
- **Un ajout horodate empile sous une entree sans rapport est une entree a part entiere** et
  recoit son propre bandeau, sinon le renvoi annonce des clades absents du debut de l'entree.
- **L'idempotence se verifie**, et elle se gagne en bornant la fenetre de detection au prochain
  point d'ancrage : trop large, deux entrees voisines se masquent ; trop courte, elles se
  dedoublent.

## Usage

```
python scripts/audit_enonces.py            # mesure : controles 1 a 4 (le 5, noms de fichiers, reste manuel)
python scripts/poser_bandeaux.py           # simulation de la reparation
python scripts/poser_bandeaux.py --apply   # pose, avec sauvegarde par fichier
```

Adapter en tete de script : `RACINE` (prefixe des labels), `BDD` (repertoire de verite),
`REGISTRE` (registre autoritaire), `CIBLES` (fichiers a auditer), `TABLES_LIGNEE` (tables a
colonne de clade), et le texte du bandeau, qui doit nommer les renommages reels du depot.

## Critere de succes

Le nombre de labels `INCONNU` cites sans marqueur de peremption, affiche au demarrage de
session, doit decroitre d'iteration en iteration. Dans le cas fondateur : 52, puis 4 apres la
pose des bandeaux, puis 0 apres correction des deux defauts de l'instrument, temoin positif au
vert. Pour le controle 4, le chiffre attendu n'est PAS zero : un projet qui documente ses
refutations cite forcement les chiffres refutes, et la liste rendue est a trier, pas a annuler.
