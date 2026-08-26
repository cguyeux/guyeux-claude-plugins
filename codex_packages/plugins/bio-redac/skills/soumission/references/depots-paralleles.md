# Les deux dépôts qui accompagnent toute soumission

Toute soumission à une revue s'accompagne d'un préprint et d'un dépôt de code. Ce
ne sont pas des options : ce sont les deux gestes qui rendent le travail citable
immédiatement et vérifiable par un relecteur, sans attendre douze mois de processus
éditorial.

Le détail vérifié des serveurs (formulaires, licences, catégories, délais, endorsement
arXiv) vit dans `~/.agents/knowledge/journals/preprints_et_delais.md`. Ce document-ci
donne le mode opératoire et l'ordre des gestes.

## Choisir le serveur

| Contenu du manuscrit | Serveur |
|---|---|
| biologie, génomique, phylogénomique, microbiologie | bioRxiv |
| santé humaine, clinique, épidémiologie de terrain | medRxiv |
| méthode, algorithme, apprentissage automatique, calcul | arXiv |

Un manuscrit de génomique bactérienne va sur bioRxiv même s'il parle d'un pathogène
humain : medRxiv est pour les travaux dont l'objet est le patient ou la population,
pas le génome. Un travail d'IA appliquée aux services de secours va sur arXiv.

**Vérifier avant de déposer que la revue cible accepte le préprint** (champ
`preprint_policy` de `journals.tsv`). La quasi-totalité l'accepte, mais quelques
titres contraignent la licence ou imposent un embargo, et un préprint déposé en
violation d'une politique éditoriale fait perdre la revue.

## Ordre des gestes, qui n'est pas négociable

1. Le manuscrit est figé et compilé, `preflight.py` est au vert.
2. Le préprint est déposé, et sa mise en ligne confirmée.
3. La soumission à la revue est faite, et son accusé de réception reçu.
4. **Seulement alors**, le PDF est poussé sur le dépôt GitHub centralisateur, avec
   son statut passé à « Submitted to <revue>, pending peer review ».

L'inversion des étapes 3 et 4 a déjà coûté six jours de dépôt public affichant une
version de 21 pages quand 22 avaient été soumises, sans qu'aucun signal ne le
révèle. Un PDF poussé à l'étape de préparation devient périmé au premier ajustement
imposé par le portail, et rien ne le rattrape ensuite.

Avant de considérer le point clos, comparer le fichier poussé au `article/main.pdf`
local par `pdfinfo` et `pdftotext`, pas seulement constater qu'un PDF existe.

## Déposer le préprint

Ce qu'il faut avoir sous la main : le PDF du manuscrit complet figures incluses, les
fichiers supplémentaires un par un, le résumé **en texte brut avec les macros LaTeX
résolues**, le titre, la catégorie, la licence.

Le résumé mérite une attention particulière. Un résumé copié depuis le `.tex` arrive
avec ses `\mtb{}`, ses `4{,}370` et ses doubles tirets. Résoudre à la main : noms
d'espèces en toutes lettres, séparateurs de milliers normaux, tirets simples. Puis
compter les mots du résultat, car les serveurs comme les portails ont une limite.

La licence par défaut est CC BY, cohérente avec le dépôt Zenodo et avec la politique
de la plupart des revues. Ne pas choisir une licence plus restrictive sans raison,
ni plus permissive sans vérifier la revue.

Le champ affiliation est piégeux : le remplissage automatique tronque souvent au
seul nom de l'université. Vérifier après validation que la ligne complète est bien
celle de `author_profile.py field affiliation.latex_line`.

Rattacher l'ORCID quand le serveur le propose : cela rend le préprint découvrable
depuis le profil et évite les homonymies.

Après téléversement, le serveur convertit les fichiers en PDF de manière asynchrone.
L'état « en conversion » n'est pas un état déposé. Attendre, relire l'aperçu, et
seulement ensuite envisager la publication, qui reste un geste de l'auteur.

Noter l'identifiant rendu par le serveur dans le registre
(`submissions.py set <id> preprint_id=...`), puis le DOI quand il arrive.

## Déposer le code

Deux dépôts centralisateurs, choisis selon le domaine :

- `cguyeux/deciphering-tuberculosis-with-ai` pour la tuberculose, le MTBC et la
  génomique bactérienne ;
- `cguyeux/ia-securite-civile` pour les travaux sur les services de secours, les
  appels d'urgence et l'IA opérationnelle.

Un dépôt propre au projet peut exister à côté et porter le détail du code. Le dépôt
centralisateur, lui, porte l'index : un sous-répertoire par article, le bundle de
reproductibilité, le PDF de la version soumise, et une ligne dans le tableau du
`README.md` avec le statut éditorial à jour.

Ce que contient un sous-répertoire d'article : les scripts d'analyse, les données
dérivées nécessaires pour reproduire les figures, un `README.md` local qui dit dans
quel ordre les exécuter, et le PDF de la version soumise.

Ce qu'il ne contient jamais : des données brutes lourdes qui vivent déjà dans une
base publique, des identifiants, des chemins absolus de la machine locale.

Le statut dans le tableau du `README.md` est une information vivante. « Draft,
pending peer review » laissé en place après une soumission effective est une erreur
silencieuse : le mettre à jour au moment du dépôt, et de nouveau à l'acceptation.

## Le DOI citable du code

`/zenodo-deposit` crée le dépôt, réserve un DOI et peut remplacer le placeholder
dans le `main.tex`. La réservation suffit pour citer dans le manuscrit soumis ; la
publication du dépôt, irréversible, est un geste confirmé par l'auteur, en général
au camera-ready.

## Enregistrer

Chaque dépôt se consigne dans le registre au moment où il est confirmé :

```bash
python3 scripts/submissions.py set <id> preprint_server=biorxiv preprint_id=<id>
python3 scripts/submissions.py set <id> github_repo=cguyeux/deciphering-tuberculosis-with-ai
python3 scripts/submissions.py set <id> zenodo_doi=10.5281/zenodo.<n>
```

Un dépôt non consigné est un dépôt qu'il faudra retrouver à la main dans six mois,
au moment où la revue demandera où sont les données.
