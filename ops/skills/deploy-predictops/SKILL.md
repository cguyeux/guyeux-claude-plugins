---
name: deploy-predictops
description: >-
  Déploiement complet de PredictOps sur les 4 départements en production.
  Enchaîne : tests locaux → commit → push → git pull sur chaque serveur →
  restart des services fast → vérification des logs.
argument-hint: "[message-commit]"
---

# Deploy PredictOps — Pipeline complet

Déploiement de `scripts/global/predictops_test_bon_ancien.py` (et tout fichier
modifié localement) vers les 4 départements en production :
- **ovh1** → depts 25, 06, 31 (répertoires `Predictops_25`, `Predictops_06`, `Predictops_31`)
- **ovh2** → dept 01 (répertoire `Predictops_01`)

## Répertoire de travail attendu

`/home/christophe/Documents/docs/codes/predictops`

Si l'utilisateur est dans un autre répertoire, adapter les chemins.

---

## Étape 0 — Vérification préalable (TOUJOURS faire en premier)

### 0a. Vérifier les divergences serveur

Avant tout commit local, vérifier si des modifications existent **directement sur les serveurs** (qui seraient écrasées par un git pull) :

```bash
ssh ovh1 "for d in Predictops_25 Predictops_06 Predictops_31; do
  echo \"=== \$d ===\"
  git -C /home/ubuntu/\$d status --short
done"

ssh ovh2 "echo '=== Predictops_01 ===' && git -C /home/ubuntu/Predictops_01 status --short"
```

**Si des modifications existent sur les serveurs :** les rapatrier localement avant de continuer :
```bash
# Exemple : récupérer le pipeline modifié sur ovh1
scp ovh1:/home/ubuntu/Predictops_25/scripts/global/predictops_test_bon_ancien.py \
    scripts/global/predictops_test_bon_ancien.py
```
Puis vérifier le diff local et inclure ces changements dans le commit.

### 0b. Voir les fichiers modifiés localement

```bash
git status
```

---

## Étape 1 — Tests locaux

### 1a. Vérification syntaxe Python (toujours)

```bash
python -m py_compile scripts/global/predictops_test_bon_ancien.py && echo "Syntaxe OK"
```

Si le fichier `launch-predictops.py` existe :
```bash
python -m py_compile scripts/global/launch-predictops.py && echo "Syntaxe OK"
```

**Si une erreur de syntaxe est détectée → STOPPER. Corriger avant de continuer.**

### 1b. Tests unitaires (optionnel, si l'utilisateur le demande)

```bash
make ci-agent
```
ou plus rapide :
```bash
python -m pytest tests/ -x -q --tb=short 2>&1 | tail -20
```

---

## Étape 2 — Commit

Construire le message de commit depuis l'argument du skill ou inférer depuis les fichiers modifiés.

```bash
# Voir précisément ce qui change
git diff --stat HEAD
```

Committer **uniquement les fichiers pertinents** (ne jamais `git add .` qui inclurait logs, expériences, etc.) :

```bash
# Exemple pour le script principal
git add scripts/global/predictops_test_bon_ancien.py

# Ou pour tout le répertoire experiments/ si nécessaire
git add experiments/train_deploy.py

# Commit
git commit -m "$(cat <<'EOF'
<message de commit>

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

Vérifier :
```bash
git log --oneline -3
```

---

## Étape 3 — Push

```bash
git push origin main
```

Vérifier que le push a réussi. En cas d'échec (remote divergé) :
```bash
git pull --rebase origin main && git push origin main
```

---

## Étape 4 — Pull sur les 4 départements

Faire les 4 pulls en parallèle :

```bash
# ovh1 : 3 départements
ssh ovh1 "
  for d in Predictops_25 Predictops_06 Predictops_31; do
    echo \"=== Pull \$d ===\"
    git -C /home/ubuntu/\$d pull origin main 2>&1 | tail -3
  done
"

# ovh2 : 1 département
ssh ovh2 "
  echo '=== Pull Predictops_01 ==='
  git -C /home/ubuntu/Predictops_01 pull origin main 2>&1 | tail -3
"
```

**Si un pull échoue** (conflit ou dirty state) :
```bash
# Sur le serveur concerné
ssh ovh1 "git -C /home/ubuntu/Predictops_25 stash && git -C /home/ubuntu/Predictops_25 pull origin main"
```

---

## Étape 5 — Restart des services fast

Les services fast tournent en continu et servent les prédictions courantes.

```bash
# ovh1 : 3 services fast
ssh ovh1 "
  for svc in predictops_25_fast predictops_06_fast predictops_31_fast; do
    echo \"=== Restart \$svc ===\"
    sudo systemctl restart \$svc
    sleep 1
    sudo systemctl is-active \$svc && echo 'OK' || echo 'ERREUR'
  done
"

# ovh2 : 1 service fast
ssh ovh2 "
  echo '=== Restart predictops_01_fast ==='
  sudo systemctl restart predictops_01_fast
  sleep 1
  sudo systemctl is-active predictops_01_fast && echo 'OK' || echo 'ERREUR'
"
```

> **Note :** Les services slow (`predictops_25`, `predictops_06`, etc.) ne sont PAS redémarrés
> automatiquement — ils reprennent le nouveau code à leur prochain cycle naturel.
> Si une modification urgente doit s'appliquer immédiatement en mode slow, redémarrer manuellement.

---

## Étape 6 — Vérification post-déploiement

### 6a. Statut des services

```bash
ssh ovh1 "
  for svc in predictops_25_fast predictops_06_fast predictops_31_fast; do
    status=\$(sudo systemctl is-active \$svc)
    echo \"\$svc : \$status\"
  done
"
ssh ovh2 "sudo systemctl is-active predictops_01_fast && echo 'predictops_01_fast: OK'"
```

### 6b. Vérification des logs (erreurs de démarrage)

Attendre 5-10 secondes puis lire les logs récents :

```bash
ssh ovh1 "
  for svc in predictops_25_fast predictops_06_fast predictops_31_fast; do
    echo \"=== Logs \$svc (20 dernières lignes) ===\"
    sudo journalctl -u \$svc -n 20 --no-pager 2>/dev/null | grep -E 'ERROR|CRITICAL|Traceback|Exception|Started|Démarrage' | tail -10
  done
"
ssh ovh2 "sudo journalctl -u predictops_01_fast -n 20 --no-pager 2>/dev/null | grep -E 'ERROR|CRITICAL|Traceback|Exception|Started'"
```

**Signaux d'alerte dans les logs :**
- `CRITICAL` ou `ERROR` immédiatement après démarrage → problème grave
- `Traceback` → exception Python non gérée
- `SyntaxError` → le script ne compile pas (ne devrait pas arriver si étape 1 faite)
- Absence de message de démarrage → service planté silencieusement

---

## Résumé des commandes (mode rapide)

Pour un déploiement sans complication, voici la séquence complète :

```bash
# 1. Syntaxe
python -m py_compile scripts/global/predictops_test_bon_ancien.py

# 2. Commit + push
git add scripts/global/predictops_test_bon_ancien.py
git commit -m "fix: description"
git push origin main

# 3. Pull sur les 4 serveurs
ssh ovh1 "for d in Predictops_25 Predictops_06 Predictops_31; do git -C /home/ubuntu/\$d pull; done"
ssh ovh2 "git -C /home/ubuntu/Predictops_01 pull"

# 4. Restart fast
ssh ovh1 "for s in predictops_25_fast predictops_06_fast predictops_31_fast; do sudo systemctl restart \$s; done"
ssh ovh2 "sudo systemctl restart predictops_01_fast"

# 5. Vérif
ssh ovh1 "for s in predictops_25_fast predictops_06_fast predictops_31_fast; do echo \$s: \$(sudo systemctl is-active \$s); done"
ssh ovh2 "echo predictops_01_fast: \$(sudo systemctl is-active predictops_01_fast)"
```

---

## Pièges à éviter

- **Ne jamais modifier le script directement sur le serveur** (les changements seraient écrasés au prochain pull). Toujours modifier localement puis déployer.
- **Ne jamais `git add .`** dans ce projet — `logs/`, `experiments/`, `data/` ne doivent pas être commités.
- **Ne pas redémarrer les services slow** sans raison — ils peuvent tourner jusqu'à 1h et une interruption perd leur progression.
- **Vérifier le statut après restart** — un service peut sembler démarré mais crasher dans les 10 premières secondes.
- **Ne pas déployer si ovh1 a des modifications non-committées** — git pull les écraserait.
