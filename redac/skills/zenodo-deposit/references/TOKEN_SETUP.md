# Token Zenodo — configuration unique (réutilisé pour tous les articles)

Un Personal Access Token Zenodo est **valable indéfiniment** : on le crée **une
seule fois**, on l'enregistre, et tous les dépôts suivants le réutilisent. Plus
jamais de manip par article.

## 1. Créer le token (une fois)

1. Se connecter sur https://zenodo.org (ou créer un compte ; ORCID ou e-mail).
2. Aller sur https://zenodo.org/account/settings/applications/tokens/new/
3. Nom : par ex. `redac-zenodo-deposit`.
4. Cocher les scopes :
   - **`deposit:write`** (créer/éditer/téléverser)
   - **`deposit:actions`** (publier)
5. Créer, puis **copier la valeur** (affichée une seule fois).

## 2. L'enregistrer (une fois)

```bash
printf '%s' 'COLLER_LE_TOKEN_ICI' | python3 scripts/zenodo_deposit.py set-token
```
→ écrit `~/.config/zenodo/token` (chmod 600). Désormais résolu automatiquement.

Ordre de résolution du token par le script :
1. `$ZENODO_TOKEN` (ou `$ZENODO_TOKEN_SANDBOX` en `--sandbox`) ;
2. `~/.config/zenodo/token` (ou `token.sandbox`) ;
3. sinon, message expliquant ces étapes.

## 3. (Optionnel) Bac à sable pour répéter à blanc

Le sandbox est un Zenodo de test (DOIs non réels). Token séparé créé sur
https://sandbox.zenodo.org/account/settings/applications/tokens/new/ :
```bash
printf '%s' 'TOKEN_SANDBOX' | python3 scripts/zenodo_deposit.py --sandbox set-token
python3 scripts/zenodo_deposit.py --sandbox create --src paper/eval --metadata meta.json
```

## Sécurité

- Le token donne accès en écriture/publication au compte Zenodo : **ne jamais le
  committer** (le fichier est hors repo, dans `~/.config/zenodo/`), ne jamais
  l'afficher en clair.
- Le révoquer/recréer en cas de fuite : page « Applications » de Zenodo.
