# Exploitation de la litterature -- texte integral (Phase 4)

Reference de `mtbc-bilan` : texte integral des sous-phases 4.1 a 4.5. Le
SKILL.md en porte la version operationnelle condensee ; on lit ici le detail
des questions a se poser pour chaque fiche thematique, la construction du
mapping decouvertes / litterature, et la conduite a tenir quand aucune
litterature_review n'existe. La sous-phase 4.6 (notions pedagogiques) est dans
`references/notions_pedagogiques.md`.

## Phase 4 -- Exploitation approfondie de la litterature

La litterature n'est pas une annexe du bilan — c'est le **cadre
interpretatif** qui donne du sens aux decouvertes du projet. Cette phase
doit produire une comprehension fine de ce que la communaute sait (et ne
sait pas) sur le sujet, pour pouvoir ensuite situer les resultats du
projet dans ce paysage.

**Cette phase alimente deux sections du bilan** :
- La section "Etat des connaissances avant ce projet" (background)
- La section "Paysage de la litterature" (mise en perspective des
  resultats du projet)

### 4.1 Inventaire des sources disponibles

1. `Glob <projet>/litterature_review/*.md` → fiches thematiques presentes.
2. `Read <projet>/litterature_review/index.md` → sujets explores, derniere
   MAJ, directions futures suggerees.
3. Compter les references :
   `Grep -c ^@ <projet>/litterature_review/references.bib`
4. Si `article/references.bib` ou `article/*.bib` existe aussi : le lire,
   car il contient souvent des refs supplementaires citees dans le manuscrit
   mais pas dans la litterature_review.
5. Pour toute recherche bibliographique lancee pendant le bilan : interroger
   en priorite `tbmonitor-papers` (corpus PubMed TB pre-indexe, ~190k papiers,
   reponse sub-seconde) avant les sources externes.

### 4.2 Lecture des syntheses thematiques

**Pour chaque fiche thematique** dans `litterature_review/` :

1. `Read` la fiche integralement (pas juste les lacunes).
2. Extraire :
   - La synthese narrative (section `## Synthese`)
   - Les articles cles et leur contribution
   - Les lacunes identifiees
   - Les directions suggerees non explorees
3. **Construire un mapping decouvertes ↔ litterature** : pour chaque
   decouverte majeure du projet (Phase 1), identifier :
   - Quels articles de la litterature_review confirment, contredisent,
     ou sont coherents avec ce resultat ?
   - Est-ce que cette decouverte comble une lacune identifiee ?
   - Est-ce que cette decouverte est completement nouvelle (rien dans
     la litterature ne la mentionne ou l'anticipe) ?

### 4.3 Mise en perspective des decouvertes

C'est le coeur de cette phase. Pour chaque decouverte majeure du projet :

1. **Situer dans la litterature** : cette observation a-t-elle ete faite
   ailleurs ? Sur d'autres lignees ? Avec d'autres methodes ? Si oui,
   les resultats convergent-ils ?

2. **Evaluer l'originalite** : est-ce une confirmation de resultats
   connus, une extension a une nouvelle lignee, ou une observation
   genuinement nouvelle ?

3. **Identifier les mecanismes** : la litterature propose-t-elle des
   mecanismes biologiques qui expliqueraient cette observation ? Si oui,
   lesquels ? Si non, c'est une lacune a mentionner.

4. **Detecter les contradictions** : cette decouverte contredit-elle des
   resultats publies ? Si oui, c'est potentiellement l'element le plus
   interessant du bilan.

### 4.4 Identification des angles morts

Comparer ce que la litterature couvre avec ce que le projet a explore :

1. Y a-t-il des sujets bien couverts dans la litterature mais que le
   projet n'a pas abordes ? (opportunites manquees)
2. Y a-t-il des resultats du projet qui ne correspondent a aucune fiche
   thematique ? (lacune dans la lit-review, pas dans le projet)
3. Les lacunes identifiees dans les fiches : lesquelles le projet
   pourrait-il combler avec ses donnees actuelles ?

### 4.5 Si litterature_review/ n'existe pas

Ne pas se contenter de noter "pas de litterature". A la place :

1. Lire les references du manuscrit (`article/*.bib`) si elles existent.
2. Identifier les articles les plus cites dans le cahier de labo.
3. Mentionner cette absence comme une **lacune majeure** du projet et
   la proposer comme piste haute priorite (`/lit-review <sujet> --wide`).

