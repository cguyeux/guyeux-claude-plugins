#!/usr/bin/env python3
"""remat_from_tree.py — (re)matérialise un clade depuis un ARBRE ML/parcimonie (CHARACTER-BASED), au lieu du
dendrogramme average-linkage de lineage-mdl `tree`/`materialize` (qui ne voit que les CROWNS et rate les
clades LARGES/NICHÉS : les souches basales partageant une synapomorphie PROFONDE sont éparpillées par le
average-linkage). À utiliser quand une subdivision dendrogramme s'avère fausse (CG repère un clade large
manqué, ou un grade polyphylétique). L'arbre ML groupe correctement les basaux par synapo profonde.

Méthode : subdivision RÉCURSIVE pilotée par l'arbre ML. À chaque niveau, sous-clades = nœuds ML maximaux
DISJOINTS à >=MINSZ souches ET >=MINSYN synapomorphies PER-POOL (in>=t_in dans le sous-clade, out<=t_out dans
le RESTE DU POOL COURANT, positions masquées). grade = souches du pool sans sous-clade. Profondeur bornée
(évite de pectiner un comb clonal à N niveaux non demandés). Post-traitement : CONTRACTION des nœuds unaires
(degré-2) -> pas de cascade binaire ni de nom profond `direct=0` (un grade basal à enfant unique = même clade
que l'enfant, fusionné). SORTIE : chaque unité affiche ses SYNAPO PROPRES per-pool (strict 100/0, relax 90/2) =
le critère de définition (jamais juger un découpage sur la seule géo) ; un clade terminal à 0 synapo STRICTE est
flaggé `WEAK` (candidat faible : sous-structure clonale/échantillonnage acceptée au seuil relax, souvent à NE PAS
nommer -> scruter géo/hôte+SNP). Réversible (log), `gio trash` jamais `rm`.

LIMITE IMPORTANTE : remat ne classe QUE les souches PRÉSENTES dans l'arbre (`ml_tip`) ; les souches du clade
ROOT absentes de l'arbre tombent toutes AU GRADE (direct). Donc l'arbre doit être un FULL-COHORT (toutes les
souches de ROOT). Sur un arbre REPRÉSENTATIF (~N reps/dir), la couverture est faible -> grade explosif +
clades fragmentés -> garde-fou : avertissement si couverture <70%, et 'apply' REFUSÉ (sauf 'force-low-coverage').
Pour un full-cohort rapide sur clonal : UShER (placement parcimonie en secondes) ou RAxML complet. Pour
seulement HIÉRARCHISER des dirs DÉJÀ matérialisés (sans re-classer les souches), préférer un outil au niveau
dir testant chaque regroupement vs son FRÈRE sur pools entiers (cf. Bovis_full/analyses/phase_uk_dir_hierarchy.py).

Usage : remat_from_tree.py <CLADE> <ARBRE_ML.nwk> <MAX_DEPTH> [MINSZ=5] [MINSYN=2] [apply]
  <CLADE>      préfixe bdd, ex. Bovis.2.2.2.2.1.1 (les souches = sous-arbre de ce dir dans bdd/actuelle)
  <ARBRE_ML>   newick contenant (au moins) les souches du clade comme tips (labels SRA|... tolérés)
"""
import os, sys, random, subprocess
from collections import Counter
from pathlib import Path
from Bio import Phylo
random.seed(1)
MTBC=Path('/home/christophe/docs/codes/mtbc'); BDD=MTBC/'bdd/actuelle'; TM=MTBC/'global_supplementary/traces_mask'
ROOT=sys.argv[1]; MLT=sys.argv[2]; MAX_DEPTH=int(sys.argv[3])
rest_args=sys.argv[4:]
APPLY='apply' in rest_args
nums=[a for a in rest_args if a.isdigit()]
MINSZ=int(nums[0]) if len(nums)>0 else 5
MINSYN=int(nums[1]) if len(nums)>1 else 2
T_IN,T_OUT=0.9,0.02
LOG=MTBC/f'Bovis_full/résultats/lineage_mdl/{ROOT.split(".")[0]}/remat_{ROOT}_log.tsv'
def has(d,s): return (BDD/d/s/'NC_000962.3/spdi.txt').is_file()
mask=set()
for f in ['traces_mask_positions.txt','resistance_positions.txt']:
    for ln in open(TM/f):
        ln=ln.strip()
        if ln.isdigit(): mask.add(int(ln))
def posm(m):
    try: return int(m.split(':')[1])
    except: return -1
loc={}
for d in os.listdir(BDD):
    if (BDD/d).is_dir() and (d==ROOT or d.startswith(ROOT+'.')):
        for s in os.listdir(BDD/d):
            if has(d,s): loc[s]=d
PROF={s:set(x for x in (l.strip() for l in open(BDD/loc[s]/s/'NC_000962.3/spdi.txt')) if x and posm(x) not in mask) for s in loc}
ALL=set(loc)
t=Phylo.read(MLT,'newick')
def sra(x): return (x.name.split('|')[0] if x.name else None)
ml_tip={sra(x):x for x in t.get_terminals() if sra(x) in ALL}
print(f"{ROOT} : {len(ALL)} souches bdd ; {len(ml_tip)} retrouvées dans l'arbre ML")
# GARDE-FOU couverture : remat ne classe QUE les souches présentes dans l'arbre ; les autres tombent
# au grade (direct). Sur un arbre REPRÉSENTATIF (~N reps/dir), la couverture est faible -> grade explosif
# + fragmentation des clades, et un 'apply' déplacerait à tort la quasi-totalité au grade ROOT.
_cover = len(ml_tip)/max(1,len(ALL))
if _cover < 0.70:
    print(f"  /!\\ COUVERTURE FAIBLE : {len(ml_tip)}/{len(ALL)} ({_cover:.0%}) des souches sont dans l'arbre.")
    print(f"      Les {len(ALL)-len(ml_tip)} hors-arbre tomberont AU GRADE (remat ne classe que les tips) ->")
    print(f"      grade artificiellement gonflé + clades fragmentés. Fournir un arbre FULL-COHORT (toutes")
    print(f"      les souches : UShER parcimonie en secondes, ou RAxML complet). Sur un arbre REPRÉSENTATIF,")
    print(f"      n'utiliser remat que pour LIRE la topologie, pas pour 'apply'.")
    if APPLY and 'force-low-coverage' not in rest_args:
        print(f"  /!\\ APPLY REFUSÉ sous couverture {_cover:.0%} (<70%) : risque de grade explosif et de")
        print(f"      déplacement massif erroné. Relance avec un arbre full-cohort, ou ajoute 'force-low-coverage'.")
        sys.exit(2)
def synapo(grp, pool):
    grp=[s for s in grp if s in PROF]; rest=[s for s in pool if s not in set(grp)]
    if len(grp)<MINSZ or len(rest)<3: return 0
    cg=Counter()
    for s in grp:
        for x in PROF[s]: cg[x]+=1
    # DÉTERMINISTE (corrige l'instabilité run-à-run des clades WEAK) : tout le reste si <=500, sinon
    # sous-échantillon SORTÉ à stride fixe (reproductible, indépendant de l'ordre du pool ; plus de random.sample)
    samp = rest if len(rest)<=500 else sorted(rest)[::max(1,len(rest)//500)]
    co=Counter()
    for s in samp:
        for x in PROF[s]: co[x]+=1
    return sum(1 for x,k in cg.items() if k>=T_IN*len(grp) and co.get(x,0)<=T_OUT*len(samp))
def max_subclades(pool):
    poolset=set(pool); tips=[ml_tip[s] for s in pool if s in ml_tip]
    if len(tips)<MINSZ: return []
    mrca=t.common_ancestor(tips); cands=[]
    for cl in mrca.find_clades():
        if cl.is_terminal() or cl is mrca: continue
        mem=frozenset(s for x in cl.get_terminals() if (s:=sra(x)) in poolset)
        if MINSZ<=len(mem)<len(poolset) and synapo(mem,pool)>=MINSYN: cands.append(mem)
    cands.sort(key=lambda m:-len(m)); picked=[]; used=set()
    for m in cands:
        if m&used: continue
        picked.append(m); used|=m
    return picked
def build(pool, depth):
    pool=list(pool)
    subs = max_subclades(pool) if (len(pool)>=2*MINSZ and depth<MAX_DEPTH) else []
    if not subs:
        return {'direct':pool,'children':[]}
    covered=set().union(*[set(s) for s in subs]); grade=[s for s in pool if s not in covered]
    children=[build(sub, depth+1) for sub in subs]
    return {'direct':grade,'children':children}
def stsize(node): return len(node['direct'])+sum(stsize(c) for c in node['children'])
def contract(node):
    # contracte récursivement, puis ABSORBE les nœuds unaires (degré-2 : un seul enfant + pas de branchement) :
    # le grade basal d'un nœud à enfant unique est le MÊME clade que son enfant -> fusion (évite cascades binaires
    # et noms profonds direct=0). Ne touche pas aux nœuds à >=2 enfants (vraies bifurcations synapo-soutenues).
    node['children']=[contract(c) for c in node['children']]
    while len(node['children'])==1:
        c=node['children'][0]
        node['direct']=list(node['direct'])+list(c['direct'])
        node['children']=c['children']
    return node
root=contract(build(ALL,0))
struct=[]
def assign(node,name):
    kind='clade' if not node['children'] else 'node'
    struct.append((name,kind,node['direct']))
    for i,c in enumerate(sorted(node['children'],key=lambda x:-stsize(x)),1):
        assign(c,f"{name}.{i}")
assign(root,ROOT)
# synapomorphies PROPRES par unité (sous-arbre COMPLET vs reste du pool ROOT) -> AFFICHÉES : c'est LE critère de
# définition d'un clade (un gros clade à peu de synapo = tronc ancestral ; un petit à beaucoup = offshoot divergent).
fullmem={name:[d for n2,_,d2 in struct if (n2==name or n2.startswith(name+'.')) for d in d2] for name,_,_ in struct}
co_all=Counter()
for s in ALL:
    for x in PROF[s]: co_all[x]+=1
def disp_syn(mem):
    grp=[s for s in mem if s in PROF]
    if not grp or len(grp)>=len(ALL): return (0,0)
    nrest=len(ALL)-len(grp); cg=Counter()
    for s in grp:
        for x in PROF[s]: cg[x]+=1
    st=rx=0
    for x,k in cg.items():
        out=co_all[x]-k
        if k==len(grp) and out==0: st+=1
        if k>=0.9*len(grp) and out<=0.02*nrest: rx+=1
    return (st,rx)
print(f"=== {ROOT} re-subdivisé depuis l'arbre ML (depth<={MAX_DEPTH}, MINSZ={MINSZ}, MINSYN={MINSYN}) ===")
print(f"  synapo = PROPRES per-pool (sous-arbre vs reste de {ROOT}) ; strict=100%in/0%out · relax>=90%/<=2%")
print(f"  WEAK = clade terminal sans synapo STRICTE (st=0) : candidat FAIBLE (souvent sous-structure clonale/")
print(f"         d'échantillonnage, PAS une vraie lignée) -> valider géo/hôte+SNP avant apply, souvent à NE PAS nommer")
nweak=0
for name,kind,direct in sorted(struct,key=lambda r:r[0]):
    ind='  '*(name.count('.')-ROOT.count('.'))
    cc=Counter(loc[s][len(ROOT):] or 'grade' for s in direct)
    st,rx=disp_syn(fullmem[name])
    flag=' <-- WEAK(0-strict)' if (kind=='clade' and st==0) else ''
    if flag: nweak+=1
    print(f"  {ind}{name:<28} {kind:<6} n={len(fullmem[name]):<4} synapo={st}/{rx:<3} direct={len(direct):<4} ex={dict(cc)}{flag}")
if nweak: print(f"  /!\\ {nweak} clade(s) terminal(aux) FAIBLE(s) (0 synapo stricte) : à scruter, souvent clonal pas lignée")
ncov=sum(len(d) for _,_,d in struct)
print(f"  total couvert={ncov}/{len(ALL)}")
if not APPLY:
    print("\nDRY-RUN. ajouter 'apply'."); sys.exit(0)
LOG.parent.mkdir(parents=True,exist_ok=True)
old=[d for d in os.listdir(BDD) if (BDD/d).is_dir() and (d==ROOT or d.startswith(ROOT+'.')) and d!=ROOT]
for d in old:
    for s in list(os.listdir(BDD/d)):
        if (BDD/d/s).is_dir() and not (BDD/ROOT/s).exists(): os.rename(BDD/d/s, BDD/ROOT/s)
empt=[str(BDD/d) for d in old if (BDD/d).is_dir() and not any(has(d,x) for x in os.listdir(BDD/d))]
if empt: subprocess.run(['gio','trash']+empt, check=False)
moved=0
with open(LOG,'w') as lf:
    lf.write("sra\tdest\n")
    for name,kind,direct in sorted(struct,key=lambda r:r[0]):
        if name==ROOT: continue
        (BDD/name).mkdir(parents=True,exist_ok=True)
        for s in direct:
            src=BDD/ROOT/s
            if src.is_dir() and not (BDD/name/s).exists(): os.rename(src,BDD/name/s); lf.write(f"{s}\t{name}\n"); moved+=1
rest=sum(1 for s in os.listdir(BDD/ROOT) if has(ROOT,s))
print(f"APPLY: {moved} déplacées ; restant grade {ROOT}={rest} ; log {LOG}")
