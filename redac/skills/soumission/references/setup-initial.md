# Configuration initiale, à faire une seule fois

Objectif : que la connexion aux portails cesse d'être un sujet. Vingt minutes de
l'auteur, une fois, en échange de la suppression du frottement à chaque soumission
suivante.

L'assistant fait le diagnostic et prépare chaque page ; l'auteur ne fait que les
gestes que lui seul peut faire.

## Étape 1 : ORCID, la clé de voûte

C'est l'étape qui rapporte le plus, parce qu'elle déverrouille tous les portails qui
acceptent ORCID comme fournisseur d'identité.

1. Aller sur `orcid.org/signin`, se connecter, en cochant l'option de session
   persistante si elle est proposée.
2. Laisser Chrome enregistrer le mot de passe quand il le propose. S'il ne le propose
   pas, l'ajouter à la main dans les paramètres de Chrome, section gestionnaire de
   mots de passe.
3. Vérifier dans `orcid.org` → « Trusted parties » quelles organisations éditrices
   sont déjà autorisées. Chacune correspond à un portail où la connexion ORCID
   fonctionnera sans rien redemander.

Si un code de double authentification est activé sur ORCID, le noter : il faudra une
intervention de dix secondes de l'auteur à chaque expiration de session, et c'est le
seul point que l'automatisation ne peut pas absorber.

## Étape 2 : recenser les comptes qui existent déjà

L'assistant ouvre chaque portail et constate l'état, sans rien saisir. Le résultat
va dans `portals.tsv`. Trois cas :

- **session vivante** : rien à faire, la fiche est complétée et datée ;
- **compte existant mais session expirée** : l'auteur se connecte une fois, en
  laissant Chrome enregistrer, puis rattache son ORCID depuis le profil du portail
  quand l'option existe ;
- **aucun compte** : ne rien créer par anticipation. Un compte se crée au moment où
  une soumission le demande, et pas avant.

Le point à ne jamais manquer, à cette étape : sous quelle adresse mail chaque compte
existe. L'adresse institutionnelle et l'adresse personnelle créent deux comptes
distincts sur le même portail, et le doublon casse le rattachement des manuscrits
déjà déposés. C'est le champ `account_login` de `portals.tsv`.

## Étape 3 : rattacher ORCID à chaque portail

Sur chaque portail où un compte existe, dans les paramètres de profil, chercher
« Link ORCID » ou « Connect your ORCID iD » et accepter l'autorisation. Ce geste ne
se fait qu'une fois par portail ; ensuite, le bouton « Sign in with ORCID » suffit.

L'assistant amène sur la bonne page ; l'auteur accepte l'écran d'autorisation OAuth,
que l'assistant ne franchit pas.

## Étape 4 : compléter le dossier auteur

```bash
python3 scripts/author_profile.py show
```

Sort la liste des champs encore vides. Les remplir une fois évite de les retaper à
chaque formulaire. Les plus souvent demandés et souvent absents : le numéro de
téléphone professionnel, l'identifiant Scopus, et la liste des relecteurs suggérés.

Pour les relecteurs, la méthode qui coûte le moins : partir des auteurs les plus
cités dans le `.bib` du manuscrit, retirer les co-auteurs des cinq dernières années,
retenir ceux dont un article récent traite du même objet, vérifier leur affiliation
et leur courriel sur la page de leur laboratoire. Cinq noms couvrant au moins deux
pays hors France couvrent la quasi-totalité des exigences de portail.

## Étape 5 : vérifier que ça marche

Rouvrir un portail au hasard et constater que la connexion se fait sans saisie. Puis
dater la fiche :

```bash
python3 scripts/author_profile.py portal-set <portail> access_method=orcid-sso --success
```

## Ce que cette configuration ne couvre pas

Les codes de double authentification envoyés sur téléphone, les CAPTCHA et les défis
Cloudflare restent des interruptions. Elles se réduisent en gardant les sessions
vivantes, mais ne disparaissent pas. L'assistant les signale avec l'onglet déjà
ouvert au bon endroit, pour que l'interruption dure quelques secondes plutôt qu'une
reconstitution de compte.
