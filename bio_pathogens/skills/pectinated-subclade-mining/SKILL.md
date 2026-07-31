---
name: pectinated-subclade-mining
description: >-
  Extraction iterative des sous-lignees pectinees d'une lignee MTBC (ou autre
  bacterie clonale) via les SPDI core exclusifs du sous-clade. Lit les spdi.txt
  sur disque, filtre PER-POOL (jamais global), produit un repertoire par
  sous-clade avec ses markers.

  Utiliser quand : topologie pectinee dans un arbre RAxML focalise, clade trop
  heterogene, classifier SPDI pour reclasser des souches en attente (a_ranger).

argument-hint: "<clade_parent> <sous_clade_name> <list.txt>"
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# pectinated-subclade-mining : Extraction iterative de sous-lignees MTBC

## Quand l'utiliser

Apres avoir construit un arbre RAxML focalise sur une lignee, on observe
visuellement des sous-clades emergents. Cas typiques : raffiner la taxonomie
d'une lignee pectinee, trancher si un clade trop heterogene contient plusieurs
sous-lignees distinctes, produire un classifier SPDI-based pour reclasser les
souches en attente (`a_ranger`).

Le test de synapomorphismes lit les `spdi.txt` **directement sur disque**
(filesystem-based, pas de SQL) ; TBannotator n'intervient que pour les metadata.

Pour chaque candidat, ce skill :
1. Verifie les **synapomorphismes SPDI** (presence >=95% dans le candidat,
   absence <=5% partout ailleurs avec **filtre per-pool strict**)
2. Recupere les **metadata** geo-hote depuis TBannotator
3. Extrait physiquement les souches vers un nouveau repertoire dans `bdd/actuelle/`
4. Sauvegarde les markers dans `<projet>/data/markers_v2/`

## Principe : filtre PER-POOL (essentiel)

**Bug a eviter** : un seuil global "<5% des autres souches" peut conserver
un marker present dans 100% d'un petit sous-clade voisin si ce sous-clade
est noye dans un pool externe plus grand. **Toujours** filtrer pool par pool :

```python
def find_synapo_per_pool(target_sets, exclude_pools_dict, t_in=0.95, t_out=0.05):
    cnt=Counter()
    for sp in target_sets.values(): cnt.update(sp)
    core={sp for sp,n in cnt.items() if n>=t_in*len(target_sets)}
    final=set()
    for sp in core:
        valid=True
        for pname, pool in exclude_pools_dict.items():
            if not pool: continue
            present=sum(1 for ref in pool if sp in ref)
            if present > t_out*len(pool):
                valid=False; break  # echec sur ce pool
        if valid: final.add(sp)
    return final
```

Chaque sous-clade voisin doit etre dans son propre pool (pas merge). Sinon
un sister-pair de 15+15 voit ses markers s'echanger.

## Pipeline standard

### Etape 1 : preparer les listes candidates

L'utilisateur identifie visuellement dans l'arbre RAxML :
- Une **topologie pectinee** : (A, (B, (C, (D, E))))
- Pour chaque sous-clade candidat, donner une liste de SRA

Stocker chaque liste dans `/tmp/cand_<name>.txt` (un SRA par ligne).

### Etape 2 : test synapomorphismes

Script reference : `scripts/find_synapomorphisms.py`

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/pectinated-subclade-mining/scripts/find_synapomorphisms.py \
  --candidates /tmp/cand_X.txt \
  --candidate-current-dir <Bovis1.2.2> \
  --bdd /home/christophe/docs/codes/mtbc/bdd/actuelle \
  --exclude-clades Bovis1.1,Bovis1.2.1.BCG,Bovis2.s2.1,Caprae1_La2 \
  --out /tmp/synapo_X.txt
```

### Etape 3 : metadata

Via TBannotator MCP :
```sql
SELECT t.strain_name, t.ncbi_bioproject, b.geo_country, b.host, b.collection_date_parsed
FROM tb_ncbi_strain t LEFT JOIN tb_ncbi_biosample b ON b.ncbi_biosample=t.ncbi_biosample
WHERE t.strain_name IN (<liste>)
ORDER BY b.geo_country, b.host;
```

### Etape 4 : nommage hierarchique pectine

Convention :
- Clade racine : `<Lignee>.1`, `<Lignee>.2`
- Subdivision : `<Lignee>.2.1`, `<Lignee>.2.2`
- Et ainsi de suite : `<Lignee>.2.2.1`, `<Lignee>.2.2.2.1`, ...

A chaque profondeur, le `.1` est le clade basal qui emerge en premier,
le `.2` est le sister-clade (qui continue a se subdiviser).

### Etape 5 : extraction physique

```bash
cd <bdd/actuelle>
mkdir -p <NewCladeDir>
while read s; do
  [ -d "<CurrentDir>/$s" ] && mv "<CurrentDir>/$s" "<NewCladeDir>/$s"
done < /tmp/cand_X.txt
# Sauvegarder les markers
cp /tmp/synapo_X.txt <projet>/data/markers_v2/<NewCladeName>.txt
```

### Etape 6 : sanity check

Apres extraction, verifier qu'aucune souche n'est mieux classee ailleurs :

```python
# Pour chaque SRA, scoring per clade
# Si best != current AND score(best) > score(current) clairement, mismatch
```

## Seuils typiques

- **Strict (defaut)** : t_in=0.95, t_out=0.05, pour sous-lignees etablies
- **Relax** : t_in=0.85, t_out=0.10, pour sous-lignees recentes/clonales
- **Tres relax** : t_in=0.70, t_out=0.20, derniere chance, prudent

Si meme a t_in=0.70 t_out=0.20 on a 0 synapomorphismes, **ne pas extraire**
le sous-clade : il n'est pas synapomorphiquement distinct. Les sous-divisions
visuelles dans l'arbre ML sont probablement des artefacts (long-branch attraction,
homoplasie, ou expansion clonale ultra-recente non capturee par SPDI seuls).

## Tailles minimales

- `>=5` souches pour creer un sous-clade (en dessous : microvariation clonale,
  pas diversification phylogenetique). Cf. memoire utilisateur
  `feedback_minimum_sublineage_size`.
- Acceptable de creer un clade avec 4 souches si elles forment une lignee
  ancestrale (ex. proto-BCG francais ancestraux a Pasteur 1908).

## Cas particuliers

### Sister-pair sans markers exclusifs internes

Si B et C sont sister et B n'a aucun marker propre (tous chevauchent avec C),
cela signifie que **(B, C) forment ensemble un clade reel** mais que B n'est
pas un sous-clade synapomorphique. **Garder C** comme sous-clade extrait,
fusionner B dans (B,C) parent. Le repertoire B peut etre vide ou contenir
les outliers.

### Clade trop homogene (ex. France multi-hote clonal)

Apres avoir extrait un gros clade (>100 souches), les sous-divisions internes
peuvent ne pas avoir de support synapomorphique meme a t_in=0.70/t_out=0.30.
**Ne pas forcer** la subdivision : le clade reflete une expansion clonale
ultra-recente sans diversite SPDI suffisante. Marquer dans la memoire que
ce clade est "homogene non-subdivisable SPDI" et recommander des markers
complementaires (RD, indels, structural variants).

### Bloc visuel impur : chercher le sous-coeur par bimodalite (valide L1.2.1.2.1.2, 2026-06)

Un bloc pointe "a l'oeil" dans l'arbre est **presque toujours paraphyletique pris
entier** : 0 synapomorphisme exclusif, meme relache, meme sans filtre global. Ne PAS
conclure "pas de clade" pour autant. Calculer les **marqueurs candidats** (presents
>=40% du bloc ET ~0% partout ailleurs, globalement exclusifs) puis le **score de
portage par souche** : si bimodal (un groupe a ~tous les marqueurs, l'autre a ~0), le
vrai clade est le **sous-coeur porteur**, les non-porteurs sont des outliers a renvoyer
au "reste". Ex. : bloc 34 -> sous-coeur 25 (19 mk) + 9 outliers ; bloc 75 -> sous-coeur
30 (16 mk) + 45 outliers ; bloc 122 -> 0 sous-coeur (assemblage de plusieurs clades).
Toujours signaler les outliers nommement a l'utilisateur (ne pas rubber-stamper son bloc).

### Monophylie ML-single SANS synapomorphie = clade de topologie non soutenu

Un bloc peut etre monophyletique dans une recherche ML unique (non bootstrappee) ET
avoir 0 synapomorphisme exclusif (a tous seuils, avec/sans filtre global). C'est un
**clade de topologie**, pas un clade a marqueurs : ne pas le materialiser comme
sous-lignee. Le branchement fin d'un arbre non bootstrappe est peu fiable ; pour le
detail, refaire un arbre bootstrappe (IQ-TREE/UFBoot). Le **signal des marqueurs prime
sur la topologie** : >=3 synapomorphismes co-occurrents exclusifs = vrai clade meme si
l'arbre le dit "polyphyletique" (artefact de 1-2 souches intercalees).

### Exclusivite GLOBALE en plus du per-pool

Le per-pool teste vs les sister/parent fournis. Ajouter le test **global** via
`global_supplementary/traces_mask/clade_spdi_count.pkl` (compte de CLADES contenant le
SPDI dans leur union) : garder seulement les marqueurs a compte <=15 (= restreints a la
chaine lignee + ancetres). Ecarte les homoplasies que le per-pool local laisse passer.

### Clades-CONTENEURS legitimes (0 marqueur propre)

Un noeud parent peut avoir 0 synapomorphisme exclusif (toutes ses synapos chez les
enfants). Son dir ne tient que les basales directes, ou est **vide** si entierement
partitionne en enfants (entite `n=0`, noeud interne pur valide ; la classification passe
par les enfants porteurs). Ne pas forcer un marqueur sur un conteneur.

### Remanier une hierarchie deja materialisee : FLATTEN puis REBUILD

Si l'utilisateur rejette un decoupage et veut une autre hierarchie, NE PAS renommer
incrementalement (collisions, dirs fantomes). (1) FLATTEN : consolider tous les SRA des
sous-dirs dans le parent, `gio trash` les vides (jamais `rm`), purger leurs cles
`_marker_overrides.json`, `assert` la conservation. (2) REBUILD : recreer les dirs, `mv`
chaque souche au noeud le plus profond, ecrire les marqueurs. (3) `build_inventory.py` +
`build_barcodes.py` + `build_clade_unions.py`. **Ne pas utiliser `lineage_cycle --apply`**
pour une hierarchie SPECIFIEE (il relance sa propre detection qui diverge).

## Pieges classiques

1. **Filtre global au lieu de per-pool** : un marker present dans 100% d'un
   small sister-pair de 15 souches passe sous le seuil 5% si autres pools
   totalisent >300 souches. **Toujours per-pool**.
2. **Oublier d'inclure le reste du clade parent** dans les exclude_pools :
   un marker peut etre present dans les 6-10 basales restantes du parent
   et passer le filtre malgre tout.
3. **Mesurer la specificite uniquement vs lignees lointaines** : il faut
   exclure aussi les sister-clades proches phylogenetiquement.
4. **Conclure trop vite avec 0 synapomorphismes** : tester avec seuils
   relaches avant d'abandonner ; si toujours 0, c'est une vraie homogeneite.

## Fichiers produits

Pour chaque sous-clade extrait :
- `bdd/actuelle/<NewClade>/<SRA>/NC_000962.3/spdi.txt` (donnees)
- `<projet>/data/markers_v2/<NewClade>.txt` (synapomorphismes, 1 SPDI par ligne)
- `<projet>/data/markers_v2/<Parent>_parent.txt` (joint markers du parent commun)

Tous documentes dans `<projet>/cahier_de_labo.md` et `memory/project_*.md`.
