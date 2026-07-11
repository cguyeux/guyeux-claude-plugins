# Audit de coherence numerique interne -- recettes detaillees

Ce document complete la Phase 1bis du skill `/claim-check`. Il fournit les
regex, les exemples de divergences typiques, et les recettes d'extraction
et de verification automatisable.

## 1. Pourquoi un audit numerique separe ?

Un manuscrit scientifique typique repete les memes chiffres entre :
- l'abstract,
- le corps des Methods, Results, Discussion,
- les captions de figures et tableaux,
- les tableaux principaux et supplementaires,
- la conclusion.

Une seule de ces occurrences peut deriver lors d'une revision (re-run d'analyse,
typo, copier-coller errone) sans que le reste du manuscrit ne soit mis a jour.
Le resultat : un meme fait quantitatif rapporte avec des valeurs differentes
selon la section. Le lecteur ne peut pas distinguer une vraie nuance d'une
incoherence accidentelle.

Une revue manuelle de quelques centaines de nombres ne detecte pas ces
divergences en pratique. Un audit systematique par regex le fait
trivialement.

## 2. Classes de chiffres a auditer

### 2.1 Tailles d'echantillon

Souvent repetees 5-10 fois dans le manuscrit (abstract, dataset, methods,
results, discussion, captions, tableaux). Une derive d'un seul chiffre
casse la coherence.

Exemples :
- `n=1556 L6 strains` (abstract)
- `L6 contributes 1556 strains` (dataset)
- `1556 L6 genomes carrying all three disruptions` (discussion)
- `L6 & 1556 & 340 & 0 & 1` (table 1)

Test :
```bash
for pat in "1556" "1\\\\,556" "1~556"; do
  rg -c -F "$pat" main.tex
done
```

### 2.2 Sous-decompositions et sommes

Un total annonce doit egaler la somme de ses parts. Exemples typiques :

```python
# Sous-lignages L6
936 + 232 + 8 + 16 + 364 == 1556  # ✓

# Decomposition signature 49 SPDIs
3_HIGH + 28_missense + 12_synonymous + 6_upstream == 49  # ✓

# Tip-dating panel 99 taxa
50_L6 + 21_L9 + 2_L10 + 10_CladeA + 10_Animal1 + 5_L5 + 1_H37Rv == 99  # ✓

# Decomposition par branche du clade re-humanise
23_TRI + 71_L6L9 + 1_L6L10 + 0_L9L10 + 117_L6 + 217_L9 + 431_L10 + 2730_non_excl
```

A chaque rencontre d'une decomposition, *additionner* mentalement et verifier
que ca tombe juste.

### 2.3 Dates et TMRCA

Pieges classiques : un re-run d'analyse genere des valeurs sub-annuelles
differentes du run precedent ; les anciennes valeurs survivent dans le
texte tandis que la table est mise a jour (ou l'inverse).

Exemples observes :
- Texte : `crown 990 BCE / stem 1498 BCE / gap 508 yrs`
- Table de sensibilite (ligne ref.) : `crown 992 BCE / stem 1501 BCE / gap 510 yrs`

Test :
```bash
rg -n "990 BCE|992 BCE|1498 BCE|1501 BCE|508|510" main.tex
```

### 2.4 Ratios et statistiques

Le ratio rapporte (`30/12`) doit etre coherent avec la decomposition annoncee
(`28 missense + 2 HIGH = 30 N` vs `28 missense + 3 HIGH = 31 N`). Une
divergence d'une unite dans la decomposition fait deriver le ratio mais
ne change typiquement pas la p-value au-dela de la 2e decimale -- pourtant
le lecteur attentif ne peut pas reconcilier les deux.

### 2.5 Formatage des milliers et decimales

Trois conventions LaTeX cohabitent souvent :
- `1\,556` (thin space, convention LaTeX standard)
- `1~556` (espace insecable, fonctionne mais non standard pour les milliers)
- `1556` (sans separateur, justifie en tableau compact)

Recommandation : `\,` partout sauf dans les cellules de tableau.

Pour la version FR, le separateur decimal est `,` (`11{,}6\%`) tandis que
EN utilise `.` (`11.6\%`). Verifier que la version FR n'a pas de chiffres
au format anglais oublie (et reciproquement).

### 2.6 p-values, q-values, intervalles de confiance

Doivent etre identiques entre abstract, results, captions de tableaux, et
texte de discussion qui les commente.

Exemples a tester :
- `p = 0.42`, `p = 0.71`, `q = 0.146`
- `p_emp = 0.26`, `p_emp = 0.83`
- `dN/dS = 0.89`
- `7.0 \times 10^{-4}` (Bonferroni THD)
- `[2010\text{:}2022]` (calibration TreeTime)

### 2.7 Partitions et funnels -- categories MECE

Cas particulier des sous-decompositions (§2.2), mais avec un piege distinct : une
somme qui ne tombe pas juste n'est PAS forcement une typo -- ce peut etre une
**partition mal construite** (categories qui se chevauchent). Une partition doit
etre **MECE** : mutuellement exclusive et collectivement exhaustive.

Exemple observe (`gene_decay_census`, funnel de tri des 311 candidats) :
- Ecrit : `311 = 43 mobile + 31 widespread + 112 convergent + 139 Dollo` -> **325 != 311**.
- Chaque chiffre etait exact isolement (Phase 4). L'erreur etait de DESIGN de la partition :
  - `mobile` (43) est un **flag orthogonal** (transposase / PE-PPE / phage par nom+Pfam) qui
    recoupe widespread/convergent/clonal -- pas une part du tout.
  - `widespread` / `convergent` (verdicts d'etape grossiers) **chevauchent** le set Dollo final
    (58 des 139 Dollo etaient verdict-convergent/widespread avant le test strict).
- Partition disjointe correcte, sur la determination FINALE (`dollo_stratum`) :
  `18 widespread + 67 convergent + 87 near-clonal + 139 Dollo = 311`, + note orthogonale
  « 43/311 portent le flag mobile/repeat, 0 dans les 139 ».

Test : pour tout ensemble de comptes presente comme couvrant un tout,
1. verifier que la somme == total ;
2. si non, AVANT de chercher une typo, verifier que les categories sont disjointes
   (aucun flag transversal additionne, aucun verdict intermediaire mele au final) ;
3. reconstruire la partition sur la determination finale, mettre les flags orthogonaux hors somme.

## 3. Regex utiles

### 3.1 Extraction de tous les nombres

```bash
# Nombres bruts (incluant separateurs LaTeX et decimaux)
rg -n -o "[0-9][0-9~,. \\\\]*[0-9]|[0-9]+" main.tex
```

### 3.2 Detection de conventions heterogenes

```bash
# Tildes entre chiffres (mauvaise convention pour milliers)
rg -n "[0-9]~[0-9]" main.tex

# Thin spaces (bonne convention)
rg -n "[0-9]\\\\,[0-9]" main.tex

# Nombres a 4+ chiffres sans separateur
rg -n "\\b[0-9]{4,}\\b" main.tex
```

### 3.3 Comparaison EN vs FR

```bash
# Liste triee unique des entiers de chaque version
diff <(rg -o "[0-9]+" main.tex | sort -u) \
     <(rg -o "[0-9]+" main_fr.tex | sort -u)
```

Les chiffres absents d'une version mais presents dans l'autre meritent une
verification : soit un chiffre a ete oublie lors de la traduction, soit un
chiffre a derive lors d'une revision dans une seule des deux langues.

### 3.4 Recherche de toutes les occurrences d'une valeur cle

```bash
# Avec contexte (pour comprendre lequel des chiffres est "le bon")
rg -n -F "1556" main.tex
rg -n -F "1\\,556" main.tex
rg -n -F "1~556" main.tex
```

## 4. Procedure d'audit complet

```python
# Pseudocode
chiffres_cles = {
    "L6_sample": [1556, "1\\,556", "1~556"],
    "L9_sample": [21],
    "L10_sample": [2],
    "L5_sample": [183],
    "grand_clade": [3122, "3\\,122", "3~122"],
    "stratified_sample": [1849, "1\\,849", "1~849"],
    "signature_size": [49],
    "tip_dating_taxa": [99],
    "snp_alignment": [17385, "17\\,385", "17~385"],
    "crown_TMRCA_bce": [990, 992],
    "stem_TMRCA_bce": [1498, 1501],
    "stem_to_crown": [508, 510],
    "L6_crown_ce": [176, 174],
    "L9_crown_ce": [187, 185],
    "L10_crown_ce": [783, 782],
    # ...
}

# Pour chaque cle, trouver toutes les occurrences et detecter les divergences
for key, valeurs in chiffres_cles.items():
    occurrences_par_valeur = {}
    for v in valeurs:
        occurrences_par_valeur[v] = grep_count(v, "main.tex")
    if len(set(occurrences_par_valeur.values())) > 1:
        signaler_divergence(key, occurrences_par_valeur)
```

## 5. Sommes attendues a tester

Liste typique pour un manuscrit MTBC :

| Total | Decomposition | Test |
|-------|---------------|------|
| Sample L6 | sublignages 936+232+8+16+364 | == 1556 |
| Signature 49 | 3 HIGH + 28 missense + 12 syn + 6 upstream | == 49 |
| Tip-dating 99 | 50 L6 + 21 L9 + 2 L10 + 10 CladeA + 10 Animal_1 + 5 L5 + 1 H37Rv | == 99 |
| Reversion 48 | tested vs verified per lineage | sums match |
| Branch decomposition | TRI + L6L9 + L6L10 + L9L10 + L6 + L9 + L10 + non-excl | == total polymorphic |

## 6. Cas typiques de divergences observees

| # | Pattern | Cause probable | Solution |
|---|---------|----------------|----------|
| 1 | `n=2` vs `n=3` pour L10 | Faute de frappe dans un caveat | Aligner sur valeur principale |
| 2 | `990 BCE` vs `992 BCE` | Re-run TreeTime avec seed different | Aligner texte sur table (ou inverse) |
| 3 | `30/12` vs `31/12` | Decomposition snpEff differente entre Methods et Results | Clarifier dans le texte |
| 4 | `1\,556`, `1~556`, `1556` | Conventions accumulees au fil des revisions | sed global vers `\,` |
| 5 | EN `0.89`, FR `0.89` (devrait etre `0{,}89`) | Traduction litterale sans conversion | sed `\.` -> `{,}` cible |
| 6 | Abstract `~500-year` vs body `508-year` | Arrondi rhetorique vs valeur exacte | OK si explicit, sinon harmoniser |
| 7 | Caption figure et texte different | Caption ecrite separement, pas mise a jour | Re-lecture systematique |
| 8 | `43+31+112+139=325` annonce `=311` | Fausse partition : flag orthogonal + verdict intermediaire meles au final (non-MECE) | Repartitionner sur la determination finale, flag orthogonal hors somme (cf. §2.7) |

## 7. Que faire d'une divergence detectee ?

1. **Identifier la valeur "vraie"** : chercher dans le cahier de labo, le code
   source, ou les fichiers de resultats bruts (`.csv`, `.json`, `.log`) la
   valeur authoritative.
2. **Choisir une politique d'harmonisation** :
   - Aligner toutes les occurrences sur la valeur authoritative.
   - Si deux runs differents donnent des valeurs proches mais distinctes,
     choisir le run le plus complet/recent et noter dans le cahier que
     l'ancien run est superseded.
3. **Appliquer les corrections** par sed/Edit en EN puis en FR (miroir).
4. **Recompiler** et verifier que rien d'autre n'a casse.
5. **Documenter** dans le cahier de labo : ce qui a ete corrige, pourquoi,
   et a partir de quelle source authoritative.

## 8. Quand cet audit est-il dispensable ?

- Tres premier draft, avant que les chiffres se stabilisent (mais alors
  ne pas oublier de relancer apres stabilisation).
- Manuscrit purement methodologique sans chiffres recurrents.
- Texte de moins de ~10 nombres distincts.

Dans tous les autres cas, l'audit numerique doit etre lance au moins une
fois avant chaque jalon majeur (soumission, resoumission, depot final).
