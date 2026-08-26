# Remplir un formulaire de soumission

Se connecter est un problème réglé ailleurs (`acces.md`). Ce document traite de ce
qui vient après : les quarante champs, les fichiers, et ce qui coince.

## Une seule fenêtre, du début à la fin, puis fermée

Règle posée le 2026-08-25 après une plainte de l'auteur : une journée de soumissions
avait laissé **47 onglets** ouverts sur plusieurs espaces de travail, au point qu'il ne
retrouvait plus les siens.

- **Ouvrir une fois** : `agent-browser --session soumission open <url>` au début de la
  soumission crée UNE fenêtre avec son groupe. C'est la fenêtre de la soumission.
- **Réutiliser** : passer le `tabId` explicite à chaque `agent-browser open`. Une soumission
  traverse dix à quinze pages (connexion, tableau de bord, étapes du formulaire,
  guide aux auteurs, vérification d'un DOI) ; ces pages s'enchaînent dans le MÊME
  onglet. `agent-browser click <ref> --new-tab` ne sert qu'à préserver un état réellement parallèle, par
  exemple garder le formulaire à demi rempli pendant qu'on va relire une consigne, et
  le second onglet se ferme dès la vérification faite.
- **Fermer avant de rendre la main** : `agent-browser --session soumission close` sur chaque onglet en fin de
  soumission, y compris quand le dépôt est resté en attente d'un geste de l'auteur.
  Fermer le dernier onglet du groupe fait disparaître la fenêtre.

Ce dernier point n'est pas une question de propreté mais de possibilité : **un agent ne
peut fermer que les onglets de son propre groupe**. Une session terminée laisse un
groupe orphelin que plus aucune session, ni aucun script, ne peut fermer (Chrome tourne
sans `--remote-debugging-port`, et sous Wayland l'introspection des fenêtres est
refusée). Ce qui n'est pas fermé pendant la session reste ouvert jusqu'à ce que
l'auteur le ferme à la main.

Ne jamais garder un onglet « au cas où l'éditeur répondrait ». Le suivi d'une
soumission se fait par le registre (`submissions.py`), pas par un onglet laissé
ouvert.

## Préparer le paquet avant d'ouvrir le portail

La plupart du temps perdu vient d'un fichier qu'il faut fabriquer au milieu du
formulaire. Tout produire avant, dans `article/submission_<revue>/` :

- `main.pdf`, la version exacte qui sera déposée, compilée après le dernier
  ajustement ;
- les sources, si la revue les demande dès la soumission : `main.tex`, le `.bib`,
  le `.bbl`, les figures, dans une archive ;
- les figures en fichiers séparés, au format et à la résolution exigés, nommées
  comme la revue le demande (souvent `Figure1.pdf`) ;
- les supplementary, un fichier par élément, chacun avec un nom parlant et une
  légende courte, parce que le portail demande une légende par fichier ;
- la lettre d'accompagnement, en texte brut autant qu'en PDF, car certains portails
  la veulent collée dans un champ ;
- une page de titre séparée si l'évaluation est en double anonyme, et dans ce cas
  un manuscrit expurgé de toute mention d'auteur, d'affiliation et de remerciement ;
- la liste des relecteurs suggérés (`author_profile.py reviewers --n 5`), avec nom,
  affiliation, pays et courriel, en respectant l'exigence habituelle d'au moins deux
  pays différents de celui des auteurs et aucun co-auteur des dernières années ;
- le texte des déclarations (`author_profile.py show declarations`).

Le résumé doit exister en **texte brut avec macros résolues**. Un résumé collé
depuis le LaTeX avec des `\mtb{}`, des `4{,}370` et des `--` arrive déformé dans le
formulaire, et personne ne le relit avant l'éditeur.

## Ce que les portails demandent presque toujours

Titre, résumé, mots-clés, type d'article, section ou catégorie, auteurs avec
affiliation et ORCID, auteur correspondant, lettre d'accompagnement, relecteurs
suggérés et parfois opposés, déclarations (conflits d'intérêts, financement,
éthique, consentement, disponibilité des données et du code, contributions des
auteurs, usage d'IA générative), confirmation que le manuscrit n'est pas soumis
ailleurs, choix de la voie de publication.

Le choix de la voie est le point où une inattention coûte cher : sélectionner la
voie abonnement, jamais l'option Open Access payante, sauf décision explicite de
l'auteur pour ce manuscrit.

## Par portail

### Editorial Manager (Elsevier, et beaucoup d'autres)

URL de la forme `editorialmanager.com/<code>/`. Accepte ORCID. Interface en étapes
numérotées avec une barre de progression ; on peut revenir en arrière sans perdre
la saisie. Le PDF de contrôle est construit à la fin et doit être approuvé
explicitement, sans quoi la soumission reste en brouillon et l'éditeur ne la voit
jamais. C'est l'erreur la plus fréquente sur ce portail : croire avoir soumis parce
que tous les écrans sont verts.

### ScholarOne Manuscript Central (OUP, FEMS, Wiley, Taylor & Francis)

URL de la forme `mc.manuscriptcentral.com/<code>`. Accepte ORCID. Interface en sept
étapes, sauvegarde à chaque étape. Impose souvent une limite de caractères sur le
résumé, comptée caractères et non mots. Le double anonyme y est fréquent : préparer
la page de titre séparée. Le bouton de soumission finale se trouve à l'étape de
revue et demande une confirmation.

### Snapp (Springer Nature)

`submission.springernature.com/new-submission/<journal>/<n>`. C'est le portail des
titres purement Springer, à ne pas confondre avec Editorial Manager que Springer
utilise encore pour certains titres, ni avec ChronosHub. Accepte ORCID, Google et
mot de passe. Interface récente, à une seule page qui se déroule, avec un
enregistrement automatique dont le rendu textuel peut donner l'illusion d'un
formulaire vide : vérifier par capture d'écran avant de conclure à une perte de
saisie. Le gabarit `sn-jnl` n'est exigé qu'après acceptation, pas à la soumission.

### ChronosHub (ASM)

`asm.chronoshub.io`. Portail de soumission des titres ASM. Le brouillon porte un
numéro visible dans l'URL (`draft=<n>`), à noter dans le registre avant même la
soumission. Les titres ASM séparent le statut Open Access du dispositif Subscribe
to Open et les frais de page, qui restent dus et dont le montant n'est pas public
sans compte connecté : ne pas conclure « gratuit » d'un statut S2O.

### Frontiers, MDPI

Portails maison, très guidés, mais Gold OA à frais dans tous les cas. Hors périmètre
par défaut, sauf décision explicite de l'auteur.

## Reprendre un brouillon : lire avant d'ajouter

Un brouillon ouvert sur un portail ne dit pas quel manuscrit il porte. Ni son URL, ni
le nom de la revue, ni le mail « You started a submission » ne le précisent. **Le seul
indice fiable est le nom du fichier déjà téléversé**, et il faut donc lire la page
avant d'y déposer quoi que ce soit.

Vécu le 2026-08-25 : un brouillon Archives of Microbiology, atteint par le lien de son
mail de confirmation, portait `rv3222c_archives_source.zip` alors qu'on s'apprêtait à
y déposer un tout autre manuscrit. Un téléversement de plus et deux articles se
retrouvaient dans une même soumission.

Le risque est d'autant plus réel que plusieurs sessions peuvent préparer des dossiers
en parallèle sur le même compte éditeur. Avant toute reprise : lire la page, identifier
le manuscrit, et confronter au registre (`submissions.py list`). Un brouillon inconnu
du registre est un brouillon dont on ne sait rien.

Corollaire sur Snapp : `submission.springernature.com/your-submissions` affiche
« No records found » alors qu'un brouillon existe, parce que cette page ne liste que
les soumissions **achevées**. Un brouillon n'est atteignable que par son URL directe
ou par son mail, et reste donc invisible à toute vérification passant par le tableau
de bord.

## Pièges récurrents

**Le guide aux auteurs et le portail imposent deux jeux de contraintes distincts.**
Le portail peut exiger un fichier, un format ou une déclaration dont le guide ne
parle pas, et réciproquement. Lire les deux, et considérer l'intersection comme
insuffisante.

**Les champs d'auto-complétion d'affiliation tronquent.** Après validation,
relire ce que le portail a réellement retenu et corriger à la main. Vécu sur
bioRxiv, où le remplissage automatique réduit l'affiliation au seul nom de
l'université.

**Les boutons radio stylés ne réagissent pas au clic par coordonnées.** Viser
l'élément par son rôle ou son libellé via `agent-browser snapshot -i`.

**Une page qui semble vide après un enregistrement ne l'est pas.** `agent-browser get text body`
n'expose que le texte statique, pas les valeurs des champs. Vérifier par
`agent-browser snapshot -i` ou par capture avant de tout ressaisir.

**Les bannières de cookies apparaissent deux fois**, sur le domaine de l'éditeur et
sur celui du portail. Décliner les non-essentiels sur les deux.

**Le téléversement de nombreux fichiers demande une saisie par fichier** : type,
légende, ordre. Prévoir le temps, et vérifier la liste finale plutôt que de faire
confiance au compteur.

**La conversion PDF est asynchrone.** Après téléversement, le portail construit son
PDF ; l'état « en conversion » n'est pas un état soumis. Attendre, relire l'aperçu,
et seulement ensuite envisager le clic final.

## Après la soumission

Noter immédiatement l'identifiant rendu par le portail dans le registre
(`submissions.py add ... --manuscript-id`). Sans lui, retrouver le dossier six
semaines plus tard demande de reconstituer un compte et une navigation.

Écrire ce qui a coincé dans `~/.agents/knowledge/journals/portal_lessons.md` et
dans `author_profile.py portal-set <portail> quirks="..."`. Une difficulté non
consignée sera repayée intégralement à la soumission suivante ; c'est le seul
mécanisme qui rend la prochaine plus rapide que celle-ci.
