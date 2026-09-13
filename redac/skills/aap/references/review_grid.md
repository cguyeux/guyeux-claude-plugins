# Relire un dossier contre la grille de l'appel

Généralisation du skill local `smart-mi-review`, écrit pour un seul appel et invisible
depuis les autres. La méthode vaut pour tout dispositif dont le règlement énonce des
critères de sélection, et c'est le cas de tous.

## Procédure

**Étape 0.** Lire le règlement de l'appel, la fiche `calls/<key>.md`, le brouillon en
entier, et `rejections.md`. Ce dernier point n'est pas décoratif : les reproches déjà
reçus se vérifient en premier, parce qu'ils reviennent.

**Étape 1.** Reprendre les critères de sélection du règlement, un par un, dans leur ordre
et avec leur intitulé exact. Pour chacun : une note sur 5 (1 absent, 2 faible, 3 correct,
4 solide, 5 excellent), la justification en citant le passage du brouillon qui la porte,
les forces, les angles morts, et des recommandations commençant par un verbe d'action.

Le critère qu'un dossier scientifique traite mal est presque toujours le même : celui qui
n'est pas scientifique. Transition écologique, réplicabilité, valorisation, indicateurs
d'impact, questions de genre, parité, rôle des jeunes chercheurs. Ils sont notés comme les
autres.

**Étape 2.** Vérifier la matérialité, séparément du fond. C'est ce que reprochait
l'instructeur OPCO, et cinq de ses sept reproches portaient là : les intervenants sont-ils
nommés avec leur rôle et leur quotité ? Un prestataire externe est-il identifié ? Y a-t-il
des exemples concrets et des illustrations ? Le chiffrage est-il justifié ligne à ligne, et
adossé à des devis réels ? La valorisation après projet est-elle dite ? Les parties
prenantes sont-elles impliquées ou seulement citées ? Le projet est-il surdimensionné pour
le dispositif visé ?

**Étape 2 bis.** Passer la bibliographie du dossier au même crible qu'un manuscrit, avec
`/bib-check`. Ce n'est pas du zèle : le comité PEPR PREZODE a consacré une rubrique entière,
« Scientific Quality and Scholarship Issues », à reprocher une revue de littérature
incomplète et datée, des sources périphériques plutôt qu'autoritatives, des articles de revue
clés publiés dans des revues obscures, des citations incomplètes ne permettant pas
d'identifier la source, et cinq références figurant dans la bibliographie sans jamais être
citées dans le texte. Un dossier de financement se relit bibliographiquement comme un article.

**Étape 2 ter.** Vérifier que le dossier énonce lui-même en quoi il diffère des travaux
voisins. Sur TSIA 2025, le comité a opposé deux publications qui n'étaient pas exactement le
même objet que le projet : le reproche ne portait pas sur l'existence de ces travaux mais sur
l'absence, dans le dossier, d'une démarcation explicite. Écrire la démarcation, ne pas
attendre que le lecteur la déduise.

**Étape 3.** Conformité formelle. Limite de pages, police, marges, interligne, langue,
pièces obligatoires, signatures, acronyme utilisé partout de la même façon, cohérence entre
le plan de travail, le calendrier et le budget, cohérence entre personne-mois et montants.

**Étape 4.** Simuler l'évaluation. Écrire les trois objections qu'un évaluateur formulera,
et pour chacune dire si le dossier y répond déjà, s'il peut y répondre, ou s'il faut accepter
la faiblesse et la mentionner.

Partir des six motifs mesurés dans `rejections.md`, qui reviennent de 2019 à 2025 : la
méthodologie pas assez détaillée, la nouveauté pas démontrée face à la littérature, l'impact
et la valorisation sous-écrits, les risques et remédiations absents, le consortium trop
homogène avec une co-construction qui sonne creux, la bibliographie traitée à la légère.
S'y ajoute une question de dosage : sur un dispositif à visée opérationnelle, un budget qui
penche vers la modélisation ou le développement logiciel se lit comme un désalignement.

## Sortie

Un rapport daté dans `review/` à la racine du dossier, sur le modèle de
`~/docs/projects/AMI/Smart MI 2026/review/`. Les recommandations sont ordonnées par
gravité, pas par section.
