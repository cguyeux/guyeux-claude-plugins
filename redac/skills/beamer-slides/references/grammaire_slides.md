# La grammaire des slides

Un deck qui répète le même gabarit vingt fois est un deck que l'œil cesse de
lire au bout de dix minutes. Le remède n'est pas la décoration, c'est d'avoir
plusieurs **types** de slide et de les employer à bon escient. Chaque type est
une macro du thème : la composition ne se refait pas à la main, donc elle ne
dérive pas.

Le contrôle `M1` signale un deck dont plus de 60 % des slides partagent la même
signature structurelle, `M2` plus de trois slides consécutives du même type.

## Les types

### Titre
`\begin{frame}[plain]\titlepage\end{frame}`. Gabarit maison, pas celui de
metropolis. Une fois, au début.

### Page de section
Émise par `\section{...}`. Elle coûte cinq secondes et donne à l'auditoire le
seul repère de progression qu'il aura. Trois à cinq par exposé ; au-delà, l'arc
est trop découpé.

### Rupture
```latex
\begin{sliderupture}
Le pathogène est une patriline sociale.
\end{sliderupture}
```
Une phrase, pleine couleur, rien d'autre. C'est le moment où l'auditoire lève
les yeux. Réservée aux deux ou trois assertions qui portent l'exposé : employée
cinq fois, elle ne rompt plus rien. La couleur se change en argument optionnel,
`\begin{sliderupture}[gxaccent]`.

### Grand chiffre
```latex
\bigchiffre{$\times$15}{Le chromosome Y est quinze fois plus structuré que l'ADN mitochondrial.}
```
Quand un seul nombre porte le message. Le chiffre se lit du fond de la salle, la
phrase l'explique. Ne pas y mettre deux chiffres : c'est alors une comparaison.

### Figure dominante
```latex
\slidefigure{carte.pdf}{Le Y sépare le nord du sud ; le mtDNA est plat partout.}
```
Le type le plus fréquent dans un bon deck. La hauteur de l'image est **calculée**
en retranchant la hauteur réelle de la clé de lecture, donc elle ne peut pas
déborder quelle que soit la longueur de la clé.

La **clé de lecture** n'est pas une légende. Une légende dit ce qu'est la figure,
une clé dit ce qu'il faut y voir. Sans elle, l'auditoire cherche pendant qu'on
parle, donc n'écoute pas.

### Figure et commentaire
```latex
\slidefiguretexte{arbre.pdf}{\begin{itemize}\item ...\end{itemize}}
```
À n'employer que si le commentaire doit être lu **en même temps** que la figure.
Sinon préférer la figure dominante, qui laisse respirer. C'est le gabarit dont
le parc abuse : il donne l'illusion de la densité utile.

### Comparaison appariée
```latex
\slidecompare{Avant}{...}{Après}{...}
```
Deux états, la même grille des deux côtés. Très lisible à condition que la grille
soit vraiment la même : deux colonnes qui ne se répondent pas sont deux slides.

### Tableau minimal
`booktabs`, trois colonnes au plus, pas de filets verticaux, alignement décimal
par `siunitx`. Au-delà de six lignes, c'est une figure ou une annexe. Un tableau
sur une slide se lit ligne par ligne à voix haute, ou ne sert à rien.

### Schéma, frise, pipeline
TikZ, mais avec des **labels**, pas des phrases. Un nœud qui porte plus de six
mots déclenche le contrôle `V1`. Patrons prêts à copier dans
`ideation_visuelle.md`.

### Liste à puces
Le dernier recours, et il doit se justifier dans la fiche de la slide. Quatre
items au plus, dix mots par item. Le thème lui donne volontairement des puces
discrètes et aucun ornement : elle ne mérite pas d'être embellie, elle mérite
d'être remplacée.

### Encadré pédagogique
`\notion`, `\methode`, `\nouveau`, `\remarquable`, `\fragilite`. Trois à cinq
lignes maximum sur une slide. **Le détail va dans `notes_techniques.md`**, pas à
l'écran : un encadré long est un paragraphe que personne ne lira pendant que
l'orateur parle.

### Take-away
```latex
\kb{On étend Asante-Poku et Gagneux, on ne les contredit pas.}
```
Une phrase à retenir, sur les slides qui portent un maillon. Pas sur toutes :
mis partout, il devient du mobilier. Au-delà de 25 mots, le contrôle `D3` le
signale, parce que ce n'est plus une phrase à retenir.

### Annexe
Après `\appendix`, donc hors du compte des slides du corps et hors des ratios de
l'audit. Elles sont gratuites : en préparer généreusement, surtout pour une
audition. Une annexe bien placée est ce qui distingue un orateur préparé.

## Comment on répartit

Un ordre de grandeur pour un exposé de vingt minutes en registre académique,
autour de douze à quatorze slides de corps : quatre à six figures dominantes,
deux ou trois comparaisons ou tableaux, un ou deux grands chiffres, une ou deux
ruptures, une ou deux listes au plus, trois à quatre pages de section.

Si la répartition obtenue tient en deux types, le deck sera monotone quel que
soit son contenu.
