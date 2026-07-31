# Mode `--full` : bilan comparatif de tous les projets -- version integrale

Reference de `mtbc-bilan` : procedure complete du mode `--full`, template du
bilan global, generation du PDF global et resume console associe.

## Mode `--full` -- Bilan comparatif de tous les projets

1. `ls /home/christophe/docs/codes/mtbc/` -- lister les
   repertoires.
2. Filtrer :
   - **Inclure** : repertoires contenant `CLAUDE.md` ET (`article/` OU
     `analyses/` OU `cahier_de_labo.md` OU `JOURNAL.md`).
   - **Exclure explicitement** : `bdd/`, `investigate_phylo/`,
     `global_supplementary/`, `bilans_globaux/`, `.git/`, fichiers
     isoles (`init_project.py`, `*.png`, etc.).
3. Pour chaque projet retenu, executer une **version allegee** des
   Phases 1 a 5 :
   - Cahier : compter entrees, derniere date, pistes ouvertes (liste).
   - Manuscrit : presence + pourcentage de claims verifies si
     `claim_check.md` existe.
   - Verdict mini : appliquer les 7 criteres de cloture (dont le 7e,
     "consolidation", bloquant).
4. Agregation :

```markdown
# Bilan global MTBC -- YYYY-MM-DD

## Tableau comparatif
| Projet | Lignee | Derniere activite | Entrees cahier | Article | Claims OK | Pistes ouvertes | Verdict |
|--------|--------|-------------------|----------------|---------|-----------|-----------------|---------|
| L4.9 | L4.9 | 2026-04-07 (-2j) | 6 | en prep | n/a | 5 | poursuivre |
| L4.15 | L4.15 | 2026-04-06 (-3j) | 1 | soumis | 12/12 | 0 | **bouclee** |
| ... | ... | ... | ... | ... | ... | ... | ... |

## Priorites cross-projets
<Pistes apparaissant dans plusieurs projets -- ex : datation moleculaire
manquante dans L4.9, L4.14, L5 → lancer une campagne groupee.>

## Convergences possibles
<Projets qui pourraient partager donnees, outgroup, methodologie, ou
fusionner leur analyse.>

## Projets prets a clore
<Liste des projets passant le verdict "bouclee". Action suggeree :
archivage, soumission finale, passage a un nouveau projet.>

## Projets dormants (> 180 jours sans activite ET non boucles)
<Liste avec date de derniere activite. Signalement : risque de perte
de contexte, reouvrir ou clore explicitement.>

## Top 10 des pistes haute priorite (tous projets confondus)
1. **<projet>** -- <piste> (score X.X)
2. **<projet>** -- <piste> (score X.X)
...
```

5. Ecrire dans
   `/home/christophe/docs/codes/mtbc/bilans_globaux/YYYY-MM-DD_bilan_global.md`
   (creer le repertoire si absent, suffixer `_v2` si collision).

---

## Generation du PDF en mode `--full` (section 9.3 du SKILL.md)

### 9.3 Pour le mode `--full`

La meme procedure s'applique au bilan global :
- Markdown dans `mtbc/bilans_globaux/YYYY-MM-DD_bilan_global.md`
- PDF dans `mtbc/bilans_globaux/YYYY-MM-DD_bilan_global.pdf`
- Frontmatter adapte :

  ```yaml
  ---
  title: "Bilan global MTBC"
  subtitle: "État de tous les projets au YYYY-MM-DD"
  project: "MTBC (tous projets)"
  date: "YYYY-MM-DD"
  verdict: "<N projets actifs, M prêts à clore>"
  ---
  ```


---

## Resume console en mode `--full`

Si mode `--full` :

```
Bilan global produit : <chemin absolu>
  Projets scannes : N
  Prets a clore  : M
  Dormants       : P
  Top priorites cross-projets : <3 lignes>
```
