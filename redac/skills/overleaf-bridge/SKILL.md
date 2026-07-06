---
name: overleaf-bridge
description: Synchronise a local article/ repository with an Overleaf project through Overleaf's official Git integration (git-bridge, git.overleaf.com). Deposit a new manuscript, pull the latest co-author edits, view the diff, and collect co-author comments left in the .tex for processing. Standard git on the official remote — no MCP server, no unofficial API, no scraping.
user_invocable: true
invocation: /overleaf-bridge
---

# /overleaf-bridge -- Déposer / synchroniser un article sur Overleaf (Git officiel)

Gère le va-et-vient entre un dépôt `article/` local et un projet Overleaf, via
**l'intégration Git officielle d'Overleaf** (git-bridge, `git.overleaf.com`).
Pas de serveur MCP, pas d'API non officielle, pas de scraping : du `git` standard
sur le remote officiel d'Overleaf. Déposer un nouvel article, récupérer la dernière
version éditée par les co-auteurs, voir le diff, et **collecter leurs commentaires
laissés dans le `.tex`** pour les traiter avec `/reviewer-response`.

Déclencheurs : « dépose l'article sur Overleaf », « récupère la dernière version
Overleaf », « qu'ont changé mes collègues », « relève les commentaires des
co-auteurs ».

---

## Préalable -- mémoire projet + prérequis

1. Lire `CLAUDE.md` et `cahier_de_labo.md` du projet courant (état de l'article).
2. Vérifier les prérequis :
   - `article/` est un dépôt git (créé par `/init-project`). Sinon : `git init`.
   - **Overleaf Premium ou licence institutionnelle** avec « Git integration »
     activée (sinon le git-bridge n'existe pas pour les projets ; voir Annexe).
   - Un **token d'authentification Overleaf** (Account Settings → Git Integration
     → « Generate token », forme `olp_...`).

Afficher l'état :
```
Overleaf-bridge : <titre article>
  Dépôt local   : article/ (branche <main>, dernier commit <…>)
  Remote overleaf : <configuré <url> | non configuré>
  Token Overleaf  : <présent dans le credential helper | à fournir>
```

---

## Faits techniques importants (à respecter)

- **URL git Overleaf** : `https://git.overleaf.com/<PROJECT_ID>`, où `PROJECT_ID`
  est l'identifiant de l'URL du projet `https://www.overleaf.com/project/<PROJECT_ID>`.
- **Authentification** : nom d'utilisateur `git`, mot de passe = le **token** Overleaf.
  Le token est SENSIBLE : ne JAMAIS le mettre dans l'URL du remote (il finirait
  dans `.git/config`, donc potentiellement poussé sur GitHub), ni l'écrire dans un
  fichier suivi, ni l'afficher en clair. Le stocker dans le credential helper git
  (cf. ci-dessous) ou le trousseau de l'OS.
- **Branche** : le git-bridge Overleaf utilise la branche **`master`**. Les dépôts
  `/init-project` sont sur **`main`**. Donc pousser/tirer en mappant explicitement :
  `git push overleaf main:master` et `git pull overleaf master`.
- **Ce qui NE transite PAS par git** : les commentaires natifs et le suivi de
  modifications d'Overleaf ne sont PAS exportés (git ne voit que le `.tex`). C'est
  pourquoi les co-auteurs commentent via la convention `\rev{...}` dans le `.tex`
  (voir « Commentaires des co-auteurs »). Ne pas tenter de lire les commentaires
  natifs Overleaf : aucune voie supportée, fragile et hors CGU.
- Limite « nouveau projet » : le git-bridge **ne crée pas** de projet Overleaf à
  distance. Un projet doit exister (créé dans l'UI) pour avoir une URL git.

---

## Configurer l'authentification (une fois par machine)

Demander le token à l'utilisateur (ne pas le déduire, ne pas le logger). Puis,
dans `article/` :
```
git config --local credential.helper store
```
Au premier `git push/pull`, git demande identifiant/mot de passe → `git` / `<token>`.
Le helper `store` le met en cache (dans `~/.git-credentials`, en clair sur le disque
local ; acceptable pour un poste personnel ; sinon utiliser `osxkeychain` /
`libsecret`). Alternative non persistante : `credential.helper 'cache --timeout=3600'`.
**Ne jamais écrire le token dans le dépôt.**

---

## Mode `deposit` -- déposer un article pas encore sur Overleaf

Le projet doit d'abord exister dans Overleaf. Deux variantes :

**A. Upload du zip (recommandé pour un article complet déjà compilable)**
1. (Utilisateur, UI Overleaf) New Project → Upload Project → déposer le zip de
   l'article (ex. produit par packaging : `main.tex` + `references.bib` + `figures/`).
2. Ouvrir le projet, copier l'URL → récupérer `PROJECT_ID`.
3. (Skill)
   ```
   cd article
   git remote add overleaf https://git.overleaf.com/<PROJECT_ID>
   git fetch overleaf
   git pull overleaf master --allow-unrelated-histories   # fusionne les fichiers Overleaf
   ```
   Résoudre les éventuels conflits (Overleaf a un `main.tex` minimal si projet créé
   autrement ; ici l'upload contient déjà les bons fichiers, conflits rares), puis
   `git push overleaf main:master`.

**B. Projet vide puis push (si l'on veut partir du dépôt local comme source de vérité)**
1. (Utilisateur) New Project → Blank Project. Copier l'URL → `PROJECT_ID`.
2. (Skill)
   ```
   cd article
   git remote add overleaf https://git.overleaf.com/<PROJECT_ID>
   git push overleaf main:master --force   # remplace le main.tex vierge par l'article
   ```
   Le `--force` est ici légitime (projet fraîchement créé, vide). Ne jamais
   force-push sur un projet déjà édité par des co-auteurs.

Confirmer ensuite la compilation dans Overleaf (menu Recompile) et donner à
l'utilisateur l'URL de partage pour les co-auteurs.

---

## Mode `pull` -- récupérer la dernière version (après édition des co-auteurs)

```
cd article
git fetch overleaf
git diff --stat main overleaf/master      # aperçu de ce qui a changé
git pull overleaf master                   # fusionne dans main
```
En cas de conflit, les résoudre fichier par fichier (montrer les zones à l'utilisateur).
Après pull, recompiler localement (`make`) pour vérifier.

## Mode `push` -- envoyer des modifications locales vers Overleaf

```
cd article
git add -A && git commit -m "<message>"
git push overleaf main:master
```

## Mode `diff` -- ce qui diffère entre local et Overleaf

```
git fetch overleaf
git diff main overleaf/master              # diff complet
git log --oneline main..overleaf/master    # commits côté Overleaf non encore tirés
```

---

## Mode `comments` -- relever et traiter les commentaires des co-auteurs

Les co-auteurs commentent dans le `.tex` (voir « Commentaires des co-auteurs »
ci-dessous). Après un `pull`, collecter ces commentaires :
```
grep -nE '\\rev\{' main.tex                       # notes rendues  \rev{Auteur}{texte}
grep -nE '^[[:space:]]*% [A-Z][A-Za-z]+[[:space:]]*:' main.tex   # lignes % AUTEUR : ...
```
Présenter la liste (fichier:ligne, auteur, texte). Proposer de la traiter avec
**`/reviewer-response`** : chaque `\rev` devient une remarque (verdict + plan +
édition + réponse), exactement comme une review. Une fois une remarque traitée,
retirer la note `\rev{...}` correspondante (ou la convertir en `% résolu : …`).
Quand tout est traité, rappeler de mettre `\reviewfalse` pour le PDF de soumission.

---

## Commentaires des co-auteurs -- la convention dans le `.tex`

Pour que ce soit possible, le préambule du `.tex` doit contenir (ajouté par ce
skill si absent ; déjà présent dans les articles `/init-project` récents) :
```latex
\setlength{\marginparwidth}{2cm}
\usepackage[textsize=footnotesize]{todonotes}
\newif\ifreview
\reviewtrue   % \reviewfalse pour la soumission
\newcommand{\rev}[2]{\ifreview\todo[inline,color=yellow!55,size=\footnotesize]%
  {\textbf{#1:} #2}\fi}
```
Les co-auteurs écrivent alors, n'importe où dans le texte :
```latex
\rev{Sola}{cette affirmation a besoin d'une référence}
```
→ encadré jaune inline « **Sola:** … » dans le PDF, greppable et toggleable.
Vérifier la présence de ce bloc avant de proposer le mode `comments` ; sinon
l'injecter (et `git commit` + `git push overleaf` pour le pousser aux co-auteurs).
Garde-fou : `\reviewtrue` sans aucun `\rev` ne change pas le PDF (todonotes ne
produit rien sans note). Pour la soumission, `\reviewfalse` masque tout.

---

## Consignes

- Ne jamais afficher, logger, ni committer le token Overleaf.
- Ne jamais force-push sur un projet Overleaf déjà édité par des co-auteurs.
- Toujours `git fetch` + montrer le diff AVANT un merge ; recompiler après.
- Rappeler que les commentaires NATIFS Overleaf ne remontent pas : seule la
  convention `\rev` est traitable.
- Le remote s'appelle `overleaf` ; le mapping de branche est `main:master`.

---

## Annexe -- vérifier que l'intégration Git est disponible

Si le token n'apparaît pas dans Account Settings, l'intégration Git n'est pas
activée sur le plan. Voies : (1) plan Overleaf Premium individuel ; (2) licence
institutionnelle (souvent fournie par l'université) ; (3) à défaut, basculer sur
la synchro GitHub (Menu → GitHub) qui, elle, nécessite des clics manuels de
synchro côté Overleaf et un repo GitHub intermédiaire.

---

## Épilogue -- résumé + suite

Rappeler en 3-5 lignes : l'action faite (deposit/pull/push/comments), l'état du
remote Overleaf et du dépôt local, et la suite suggérée :
- après `pull` avec des `\rev` → `/reviewer-response` pour les traiter ;
- avant soumission → `\reviewfalse` + `/manuscript-review` + `/claim-check` ;
- après `deposit` → donner l'URL de partage aux co-auteurs.
