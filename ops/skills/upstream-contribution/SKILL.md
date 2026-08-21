---
name: upstream-contribution
description: Prépare (et, sur autorisation explicite, pousse) une contribution vers un dépôt open source amont à partir d'une réimplémentation ou d'un fork local qui l'a dépassé. Trigger sur "proposer ça en amont", "remonter ce correctif au dépôt d'origine", "contribuer à [dépôt GitHub]", "faire une PR/issue sur le repo de X", ou quand un outil local corrige ou étend un outil externe dont il dérive.
---

# Contribution à un dépôt amont

Un outil local (souvent une réimplémentation ou un skill) a divergé d'un dépôt open
source amont : il corrige des défauts, ajoute des capacités, ou les deux. Ce skill
structure le passage de « on a fait mieux localement » à « proposition écrite,
vérifiée, prête à transmettre », et s'arrête avant l'action publique, qui reste
décidée par l'utilisateur.

Née de la piste P10.5 du projet `SpacerEgalVirus` (MTBC) : `crisprbuilder2.py`,
réimplémentation locale de `cguyeux/CRISPRbuilder-TB` (Guyeux 2021), avait accumulé
des corrections et des ajouts jamais remontés. Le principe se généralise à tout outil
qui étend un dépôt externe qu'on ne maintient pas soi-même.

## Étape 1 : Lire l'amont AVANT d'écrire quoi que ce soit

Ne jamais rédiger une proposition depuis la seule mémoire de ce qu'on a corrigé
localement. Lire le code amont réellement :

- Dernier commit, branche par défaut, état du dépôt (`gh repo view`, ou
  `git ls-remote`), un dépôt qui n'a pas bougé depuis des années n'a pas forcément
  de mainteneur actif ; un dépôt très actif a peut-être déjà corrigé ce qu'on croit
  être un défaut.
- Le(s) fichier(s) source précis où portent les points envisagés, ligne par ligne,
  pas seulement le README.
- L'historique des issues/PR déjà ouvertes sur le même sujet (`gh issue list`,
  `gh pr list --state all`), pour ne pas dupliquer une demande déjà faite ou déjà
  refusée avec une raison qu'il faut connaître.

## Étape 2 : Classer chaque point envisagé en trois catégories

Ne pas mélanger ces trois catégories dans la rédaction : elles n'ont pas le même
niveau de preuve requis.

1. **Ajout** (une capacité qui n'existe pas en amont). Ne dépend d'aucune
   vérification du code amont au-delà de constater l'absence. Le plus facile à
   proposer.
2. **Défaut constaté chez nous, à VÉRIFIER en amont avant de le signaler.**
   Piège central de ce skill : un bug trouvé en portant/réimplémentant une méthode
   n'est PAS automatiquement un bug du code amont, c'est un défaut du code qu'on a
   soi-même écrit en s'en inspirant. Avant d'écrire « l'amont a ce défaut », lire la
   fonction correspondante côté amont et confirmer qu'elle a la même faille. Si la
   lecture n'a pas été faite, le dire explicitement dans la proposition plutôt que
   de laisser croire à une vérification qui n'a pas eu lieu.
3. **Choix de conception à ne pas toucher.** Noter aussi ce que l'amont fait bien
   et qu'il ne faut pas laisser croire qu'on veut changer, une proposition qui ne
   critique que du négatif se lit comme hostile ; une qui commence par ce qui est
   juste se lit comme collaborative.

## Étape 3 : Chiffrer chaque point

Un correctif sans mesure est un avis, pas une preuve. Chaque point de la
proposition doit s'appuyer sur un exemple reproductible ou un chiffre : un cas où
l'ancien comportement produit un résultat concrètement faux (pas seulement
« sous-optimal »), avec l'entrée qui le déclenche et la sortie observée avant/après.
Le modèle à suivre est celui de la piste d'origine : chaque défaut est illustré par
une entrée précise (un génome, un jeu de lectures simulées) et un chiffre avant/après,
jamais une affirmation générale du type « plus robuste ».

## Étape 4 : Rédiger le document de proposition

Structure qui a fait ses preuves (voir
`claude_plugins/bio_pathogens/skills/crisprbuilder/PROPOSITION_AMONT.md` comme
exemple complet) :

1. État du dépôt amont au moment de l'écriture (branche, dernier commit, référence
   de publication s'il y en a une).
2. Ce que l'amont fait bien, à ne pas toucher.
3. Ajouts proposés, un point par capacité, avec le chiffre qui justifie chacun.
4. Défauts constatés chez nous à vérifier en amont, avec le cas reproductible, et
   la mention explicite que la vérification côté amont reste à faire si elle ne
   l'a pas été.
5. Section finale « ce qui reste à faire avant de proposer quoi que ce soit »,
   ne pas la faire disparaître même quand le document semble complet : elle est le
   garde-fou contre l'envoi prématuré.

Écrire le document dans le dépôt/skill local (jamais directement comme issue ou PR
à ce stade), c'est un brouillon interne tant qu'il n'est pas transmis.

## Étape 5 : Arrêt avant l'action publique

Rédiger la proposition ne demande pas d'autorisation. **Ouvrir une issue, une PR,
ou envoyer un message au mainteneur en demande.** C'est une action publique,
visible par l'auteur amont et potentiellement toute une communauté, et difficile à
retirer proprement une fois lue. Présenter le document terminé, proposer le
support de transmission (issue, PR, discussion) le plus adapté au projet cible, et
attendre une décision explicite avant d'exécuter quoi que ce soit avec `gh issue
create`, `gh pr create`, ou équivalent.

Si l'utilisateur autorise l'envoi : vérifier une dernière fois que les points de
catégorie 2 (défauts à vérifier) ont bien été confirmés dans le code amont avant
de les inclure tels quels, sinon les reformuler en question ouverte plutôt qu'en
affirmation (« se pourrait-il que… » plutôt que « ceci est cassé »).

## Anti-patron à éviter

Ne pas transformer un travail de portage/amélioration locale en procès de l'amont.
La proposition la plus utile part du principe que l'amont a fait des choix
raisonnables avec les contraintes qu'il avait, et que la contribution apporte ce
que l'usage local a permis de découvrir depuis, pas ce que l'amont aurait dû
savoir faire dès le départ.

## Provenance

Ce skill est une procédure originale issue du retour d'expérience du projet
`SpacerEgalVirus`. Son origine locale, ses empreintes et sa frontière avec les
projets externes cités sont consignées dans `PROVENANCE.md`.
