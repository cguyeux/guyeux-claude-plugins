---
name: parity-check
description: >-
  Verification de parite entre la version anglaise et la version francaise
  d'un meme manuscrit : apparie les sections, signale tout nombre, toute
  citation, tout renvoi interne et toute mention de supplementary present
  dans une version et absent de l'autre. Use when: le manuscrit existe en
  deux langues, apres toute correction appliquee a une seule des deux
  versions, avant soumission ou resoumission.
argument-hint: "<main.tex> <main_fr.tex> [--fix]"
allowed-tools: Bash, Read, Grep
---

# /parity-check -- Parite entre les versions EN et FR d'un manuscrit

Un manuscrit bilingue est verifie deux fois, jamais une fois deux. Les
contre-expertises (`/manuscript-review`, `/claim-check`, `/fig-check`,
`/supp-check`) lisent chacune le fond d'UNE version : rien dans le pipeline
ne verifie que les deux versions PORTENT le meme fond. Ce trou a laisse
passer, le 2026-09-19 sur `lineage_subdivision_methods`, un correctif
applique a `main_fr.tex` seul : la version anglaise -- celle que liront les
relecteurs -- citait en Results un chiffre (96,91 %) qu'aucune section ni
aucun tableau anglais ne definissait.

**Principe cardinal** : les deux versions doivent porter EXACTEMENT le meme
fond chiffre, bibliographique et referentiel. Une divergence de FORMULATION
est legitime (traduction), une divergence de CHIFFRE, de CITATION ou de
RENVOI ne l'est jamais -- elle signale qu'une correction a ete appliquee d'un
seul cote.

---

## Quand lancer ce skill

- Le manuscrit existe en deux versions linguistiques (`main.tex` /
  `main_fr.tex`, ou toute paire de fichiers `.tex` couvrant le meme contenu).
- **Apres toute correction appliquee a UNE SEULE des deux versions** -- c'est
  precisement le defaut vecu, et le moment ou il se produit.
- Avant une **soumission** ou une **resoumission** dans une revue qui exige
  les deux langues, ou avant l'envoi d'une version francaise a un
  co-auteur/financeur qui ne lira que celle-ci.
- En complement systematique d'un `/claim-check` ou d'un `/manuscript-review`
  qui ne porte que sur une seule des deux versions.

---

## Prealable -- Consultation memoire projet

1. Lire `CLAUDE.md` local et `cahier_de_labo.md` si presents : une
   correction recente notee au cahier mais appliquee d'un seul cote est le
   signal le plus direct d'une divergence a venir.
2. Charger `parity_check.md` existant dans le repertoire de l'article s'il
   est present (registre persistant, format Phase 3).
3. Charger `claim_check.md` et `supp_check.md` s'ils existent : une
   divergence EN/FR sur un chiffre est souvent la meme cause qu'un claim
   `non verifie` ou qu'un supplementary `MAJOR`/`CRITICAL` -- correler plutot
   que retraiter.

---

## Declenchement

```
/parity-check article/main.tex article/main_fr.tex
/parity-check article/main.tex article/main_fr.tex --fix
```

- Le premier argument est traite comme la version de reference, le second
  comme la version a comparer -- l'ordre n'affecte que la presentation, pas
  la detection (les deux sens sont symetriques).
- `--fix` : apres correction manuelle d'une divergence, relancer sans cet
  argument pour verifier qu'elle est resorbee (`--fix` ne modifie ici aucun
  fichier automatiquement, cf. Phase 4 -- present pour homogeneite avec
  `/supp-check`).

---

## Phase 1 -- Passe mecanique

Lancer le script deterministe, qui fait tout le travail reproductible :

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/parity-check/scripts/parity_check.py \
  article/main.tex article/main_fr.tex --json
```

Le script :

1. resout les `\input`/`\include` des deux fichiers ;
2. decoupe chacun en sections top-level (`\section{...}`) ;
3. aligne les sections EN et FR -- par `\label{}` partage d'abord (un label
   est en general recopie a l'identique entre les deux versions pour que les
   `\ref` internes fonctionnent), puis par ordre positionnel pour ce qui
   reste ;
4. pour chaque paire alignee, compare les **nombres**, les **citations**
   (`\cite`/`\citep`/`\citet`), les **renvois internes** (`\ref`/`\cref`/
   `\eqref`) et les **mentions de supplementary** (`Table Sx`, `Figure Sx`),
   et signale tout element present d'un seul cote ;
5. toute section sans contrepartie (label absent des deux cotes ET position
   non appariable) est une divergence STRUCTURELLE, rapportee a part.

Lire la sortie JSON : `status` global, `unmatched` (sections orphelines),
`pairs[]` avec pour chacune `numbers_only_en`/`numbers_only_fr`,
`citations_only_en`/`_fr`, `refs_only_en`/`_fr`, `supp_only_en`/`_fr`.

**Limite assumee** : le script ne juge pas le sens des phrases -- ce n'est
pas une verification de traduction. Il rattrape mecaniquement les
divergences CHIFFREES, BIBLIOGRAPHIQUES et STRUCTURELLES, qui sont celles
qui invalident une conclusion sans que personne ne le voie. Les divergences
purement redactionnelles (un paragraphe entier absent d'une traduction, une
nuance perdue) restent du ressort de la Phase 2.

---

## Phase 2 -- Passe de lecture pour les sections signalees

Pour chaque paire marquee `MISMATCH` ou `STRUCTURE` par la Phase 1 -- et
**seulement celles-la**, la lecture integrale des deux versions phrase a
phrase n'etant pas un usage raisonnable du contexte sur un manuscrit long :

1. `Read` le texte complet des deux sections appariees.
2. Determiner la cause : correction appliquee d'un seul cote (le cas le plus
   frequent), traduction fautive (le chiffre a change de sens en passant
   d'une langue a l'autre), ou faux positif du script (formatage : "96.9 %"
   vs "96,91 %" arrondis differemment -- **ceci n'est PAS un faux positif a
   ignorer**, c'est une divergence reelle de precision affichee, a trancher
   comme les autres).
3. Pour une section STRUCTURELLE (presente d'un seul cote) : verifier si
   c'est une section legitimement absente d'une version (ex. un "Data
   availability" different par convention de revue) ou un oubli de
   traduction pur et simple.

---

## Phase 3 -- Registre et rapport

### 3a. Ecrire `parity_check.md`

```markdown
# Registre de verification de parite EN/FR

**Article :** [titre extrait du \title{}]
**Derniere verification :** YYYY-MM-DD
**Sections :** N EN, M FR (K appariees par label, L par position)

## Etat global
- Parite : [bonne / partielle / compromise]
- Divergences structurelles : K
- Divergences numeriques : M
- Divergences bibliographiques : L
- Divergences de renvoi : R

## Divergences

| # | Section EN | Section FR | Type | Detail | Cause | Action |
|---|-----------|-----------|------|--------|-------|--------|
| 1 | Results (l.142) | Resultats (l.138) | nombre | 96,91 % en FR, absent en EN | correctif applique a main_fr.tex seul le 2026-09-18 | reporter le correctif dans main.tex |
| ... | ... | ... | ... | ... | ... | ... |
```

### 3b. Rapport ecran resume

```
━━━━ Rapport parity-check ━━━━

Article : [titre]
Date    : YYYY-MM-DD

Sections : N EN, M FR
Parite globale : [bonne / partielle / compromise]

Divergences
  structurelles : K  ⛔
  numeriques    : M  ⚠
  bibliographiques : L
  renvois       : R

Divergences les plus urgentes
  1. Results/Resultats -- 96,91 % present en FR seulement (correctif non reporte)
  2. Discussion -- \cite{doe2019} absent de la version FR
```

---

## Phase 4 -- Corrections

- **Ne jamais corriger automatiquement un fichier `.tex`**, meme en `--fix` :
  une correction de manuscrit reste sous controle humain (meme regle que
  `/supp-check` Phase 7, regle 1). Ce skill ne modifie rien ; il propose,
  section par section, la phrase exacte a reporter d'une version vers
  l'autre.
- Pour chaque divergence numerique ou bibliographique : citer la ligne et
  le texte exact du cote qui porte l'information manquante, et la ligne du
  cote qui doit la recevoir.
- Apres correction manuelle, relancer `/parity-check` sur les memes fichiers
  pour verifier que la divergence est resorbee.

---

## Integration avec l'ecosysteme

- **Complementaire a `/claim-check`** : `/claim-check` verifie qu'un chiffre
  d'UNE version remonte a une source primaire ; `/parity-check` verifie que
  ce meme chiffre existe aussi dans l'AUTRE version. Un chiffre `verified`
  par claim-check dans une seule version peut rester invisible dans l'autre
  -- les deux passes sont necessaires, ni l'une ni l'autre ne couvre le trou
  de l'autre.
- **Complementaire a `/supp-check`** : `/supp-check` aligne le main sur ses
  supplementary ; `/parity-check` aligne le main EN sur le main FR. Une
  mention de supplementary orpheline dans une seule langue est un signal
  pour les deux skills.
- **A lancer apres toute correction ponctuelle** d'un chiffre, d'une
  citation ou d'un renvoi appliquee a une seule version -- c'est le moment
  exact ou la divergence est introduite, pas seulement avant soumission.

---

## Epilogue -- Resume et suite

Scenario "parite bonne" :

```
━━━━ Etat de la parite EN/FR ━━━━

Les deux versions portent le meme fond (N sections appariees, 0 divergence) :
  ✅ Aucune section orpheline
  ✅ Tous les nombres concordent
  ✅ Toutes les citations concordent
  ✅ Tous les renvois internes concordent

Aucune action requise.
```

Scenario "divergences detectees" :

```
━━━━ Prochaine etape suggeree ━━━━

K divergences detectees. Je recommande :

  1. Corrections manuelles listees ci-dessus (une par ligne/version)
  2. make -C article/            ← recompiler les deux PDF
  3. /parity-check --force       ← re-verifier apres correction
  4. /claim-check --force        ← si un chiffre a change de valeur
```
