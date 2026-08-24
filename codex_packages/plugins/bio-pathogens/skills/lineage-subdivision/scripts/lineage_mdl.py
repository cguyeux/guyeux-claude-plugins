#!/usr/bin/env python3
"""lineage_mdl.py — definition de sous-lignees MTBC par optimisation MDL sous contraintes (multi-signal,
debruitee). Modes : denoise | rdis | tree | optimize | inspect | materialize. Parametre par ROOT (un
repertoire de bdd/actuelle). Sorties dans $LINEAGE_MDL_OUT/<ROOT>/ (defaut Bovis_full/résultats/lineage_mdl).
Voir SKILL.md. Lecture seule sauf 'materialize ... apply'. Garde-fou : gio trash, jamais rm."""
import os, sys, csv, json, math, re, pickle, subprocess
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
from scipy.spatial.distance import pdist
from scipy.cluster.hierarchy import linkage, to_tree, fcluster

MTBC=Path('/home/christophe/docs/codes/mtbc'); BDD=MTBC/'bdd/actuelle'
GS=MTBC/'global_supplementary'; TM=GS/'traces_mask'; BPG=GS/'bioproject_geo'
OUTBASE=Path(os.environ.get('LINEAGE_MDL_OUT', str(MTBC/'Bovis_full/résultats/lineage_mdl')))

def usage():
    print("usage: lineage_mdl.py <denoise|rdis|tree|optimize|inspect|materialize> <ROOT> [args]"); sys.exit(1)
if len(sys.argv)<3: usage()
MODE=sys.argv[1]; ROOT=sys.argv[2]
RES=OUTBASE/ROOT; RES.mkdir(parents=True, exist_ok=True)
def inroot(d): return d==ROOT or d.startswith(ROOT+'.')
def has(d,s): return (BDD/d/s/'NC_000962.3/spdi.txt').is_file()
def spf(d,s): return set(x.strip() for x in open(BDD/d/s/'NC_000962.3/spdi.txt') if x.strip())
def pos(m):
    try: return int(m.split(':')[1])
    except: return -1

def load_mask():
    mk=set()
    for f in ['traces_mask_positions.txt','resistance_positions.txt']:
        p=TM/f
        if p.exists():
            for ln in open(p):
                ln=ln.strip()
                if ln.isdigit(): mk.add(int(ln))
    return mk

def load_geo():
    geo={}
    for f in sorted(BPG.glob('consolidated_geo_*.tsv')):
        for r in csv.DictReader(open(f),delimiter='\t'):
            s=r.get('strain')
            if s and s not in geo:
                geo[s]={'c':r.get('country',''),'dmin':r.get('date_min',''),'dmax':r.get('date_max',''),'bp':r.get('bioproject','')}
    return geo

def load_profiles(mask=None, clean=False):
    """Rprof[strain]=set(SPDI dans cand) ; outC ; cand. clean=True -> marqueurs avec exclusivité globale
    (<=1% hors-ROOT) pour l'ARBRE-échafaud (topologie propre) ; clean=False -> tous les variables
    (DÉFINISSABILITÉ per-pool, cf. CG)."""
    Rprof={}; outC=Counter(); noutn=0
    for d in os.listdir(BDD):
        if not (BDD/d).is_dir(): continue
        if inroot(d):
            for s in os.listdir(BDD/d):
                if has(d,s): Rprof[s]=spf(d,s)
        elif clean:   # scan hors-ROOT (outC) SEULEMENT si exclusivité globale demandée (sinon coûteux: 54k souches)
            for s in os.listdir(BDD/d):
                if not has(d,s): continue
                noutn+=1
                for x in spf(d,s): outC[x]+=1
    nR=len(Rprof)
    rcnt=Counter()
    for p in Rprof.values():
        for x in p: rcnt[x]+=1
    # DEFINISSABILITE per-pool : marqueurs VARIABLES dans la lignee (pas d'exclusivite globale all-MTBC,
    # cf. CG : on definit dans le contexte de la lignee, pas sur tout le MTBC) ; masque homoplasie seul.
    cand=[x for x,k in rcnt.items() if 3<=k<=nR-3 and (mask is None or pos(x) not in mask)
          and (not clean or outC.get(x,0)<=0.01*max(noutn,1))]
    return Rprof,outC,nR,noutn,cand

def read_report(sd):
    f=sd/'NC_000962.3/report.json'
    if not f.is_file(): return None
    try: j=json.load(open(f))
    except Exception: return None
    mr=j.get('missing_rd') or []
    rd={str(x) for x in (mr.keys() if isinstance(mr,dict) else mr) if not str(x).startswith('CUS_GS')}
    iss=j.get('insertion_sequences') or []
    isp={int(x['position']) for x in iss if isinstance(x,dict) and 'IS6110' in str(x.get('name','')) and 'position' in x}
    return rd,isp

# ---------- DENOISE ----------
if MODE=='denoise':
    mask=load_mask(); Rprof,outC,nR,noutn,cand=load_profiles(mask)
    _,_,_,_,cand_nm=load_profiles(None)
    print(f"[{ROOT}] souches={nR} contexte hors-ROOT={noutn}")
    cnt={s:len(p) for s,p in Rprof.items()}; vals=sorted(cnt.values())
    import statistics as stx; med=stx.median(vals); mad=stx.median([abs(v-med) for v in vals]) or 1
    print(f"[QC compte SPDI] med={med:.0f} MAD={mad:.0f} ; haut(contam)={sum(1 for v in vals if v>med+5*mad)} bas(couv)={sum(1 for v in vals if v<med-5*mad)}")
    rdf=0
    if (TM/'bovis_rd4_qc.tsv').exists():
        rd={r['strain']:r for r in csv.DictReader(open(TM/'bovis_rd4_qc.tsv'),delimiter='\t')}
        rdf=sum(1 for s in Rprof if s in rd and rd[s].get('RD4_del') in ('0','0.0'))
        print(f"[RD4] dans QC={sum(1 for s in Rprof if s in rd)}/{nR} ; RD4 non-delete(suspect)={rdf}")
    print(f"[masque] cand sans masque={len(cand_nm)} -> apres masque={len(cand)} (retires={len(cand_nm)-len(cand)})")
    cset=set(cand); sig={s:frozenset(p&cset) for s,p in Rprof.items()}
    g=defaultdict(list)
    for s,k in sig.items(): g[k].append(s)
    print(f"[derep exacte] {nR} -> {len(g)} genotypes (signature masquee identique)")
    sys.exit(0)

# ---------- RDIS ----------
if MODE=='rdis':
    per={}; rdc=Counter(); isc=Counter()
    for d in os.listdir(BDD):
        if not (BDD/d).is_dir() or not inroot(d): continue
        for s in os.listdir(BDD/d):
            if not has(d,s): continue
            r=read_report(BDD/d/s)
            per[s]={'rd':r[0],'is':r[1]} if r else {'rd':set(),'is':set()}
            if r: rdc.update(r[0]); isc.update(r[1])
    nS=len(per)
    print(f"[{ROOT}] {nS} souches ; RD distinctes={len(rdc)} IS distinctes={len(isc)}")
    print(f"  RD variables(3..{nS-3})={sum(1 for c in rdc.values() if 3<=c<=nS-3)} IS variables={sum(1 for c in isc.values() if 3<=c<=nS-3)}")
    pickle.dump(per,open(RES/'rdis.pkl','wb')); print(f"-> {RES}/rdis.pkl")
    sys.exit(0)

# ---------- TREE ----------
if MODE=='tree':
    RADIUS=int(sys.argv[3]) if len(sys.argv)>3 else 2
    mask=load_mask(); Rprof,outC,nR,noutn,cand=load_profiles(mask, clean=True)   # arbre-échafaud propre
    idx={x:i for i,x in enumerate(cand)}; slist=list(Rprof); nc=len(cand)
    print(f"[{ROOT}] souches={nR} marqueurs masques={nc} ; matrice + derep rayon {RADIUS} SNP...",flush=True)
    M=np.zeros((nR,nc),np.uint8)
    for i,s in enumerate(slist):
        for x in Rprof[s]:
            if x in idx: M[i,idx[x]]=1
    cl=fcluster(linkage(pdist(M,'hamming'),'complete'),t=(RADIUS+0.5)/max(nc,1),criterion='distance')
    grp=defaultdict(list)
    for i,c in enumerate(cl): grp[c].append(slist[i])
    reps=sorted(grp); MR=np.zeros((len(reps),nc),np.uint8); rep_list=[]
    for j,c in enumerate(reps):
        mem=grp[c]; rep_list.append(mem); cnt=np.zeros(nc)
        for s in mem:
            for x in Rprof[s]:
                if x in idx: cnt[idx[x]]+=1
        MR[j]=(cnt>=len(mem)/2.0).astype(np.uint8)
    Zr=linkage(pdist(MR,'hamming'),'average')
    pickle.dump({'Z':Zr,'reps':rep_list,'cand':cand,'radius':RADIUS,'nR':nR},open(RES/'dendro.pkl','wb'))
    print(f"-> {RES}/dendro.pkl : {nR} souches -> {len(reps)} representants",flush=True)
    sys.exit(0)

# ---------- noyau commun optimize/inspect/materialize ----------
def build():
    dd=pickle.load(open(RES/'dendro.pkl','rb')); Z=dd['Z']; reps=dd['reps']
    geo=load_geo()
    # DÉCOUPLAGE : arbre = dendro (marqueurs PROPRES, topologie nette) ; synapo/définissabilité = TOUS
    # les marqueurs variables masqués (per-pool), indépendamment de l'arbre.
    RprofF,_,_,_,cand=load_profiles(load_mask(), clean=False)
    cand=set(cand); Rprof={s:(RprofF[s]&cand) for s in RprofF}
    nR=sum(len(m) for m in reps)
    gcount=pickle.load(open(TM/'clade_spdi_count.pkl','rb'))
    gexcl_extra={}; is_markers=set()
    if int(os.environ.get('RDIS','1')) and (RES/'rdis.pkl').exists():
        rdis=pickle.load(open(RES/'rdis.pkl','rb'))
        rd_cc=pickle.load(open(TM/'rd_cc.pkl','rb')); is_cc=pickle.load(open(TM/'is_cc.pkl','rb'))
        rdct=Counter()
        for s in Rprof:
            r=rdis.get(s,{'rd':set(),'is':set()})
            for x in r['rd']: rdct['RD:'+str(x)]+=1
            for p in r['is']: rdct['IS:'+str(p)]+=1
        rc=set()
        for m,c in rdct.items():
            if 3<=c<=nR-3:
                nm=m.split(':',1)[1]; gc=rd_cc.get(nm,0) if m.startswith('RD:') else is_cc.get(int(nm),0)
                if KGLOB<=0 or gc<=KGLOB: rc.add(m); gexcl_extra[m]=gc
        is_markers={m for m in rc if m.startswith('IS:')}
        for s in Rprof:
            r=rdis.get(s,{'rd':set(),'is':set()})
            Rprof[s]|={'RD:'+str(x) for x in r['rd'] if 'RD:'+str(x) in rc}
            Rprof[s]|={'IS:'+str(p) for p in r['is'] if 'IS:'+str(p) in rc}
    def gexcl(x): return gexcl_extra[x] if x in gexcl_extra else gcount.get(x,0)
    root=to_tree(Z)
    post=[]; st=[(root,False)]
    while st:
        n,done=st.pop()
        if n.is_leaf(): post.append(n); continue
        if done: post.append(n)
        else: st+=[(n,True),(n.left,False),(n.right,False)]
    STR={}; CT={}
    for n in post:
        if n.is_leaf():
            mem=reps[n.id]; STR[n.id]=mem; c=Counter()
            for s in mem:
                for x in Rprof.get(s,()): c[x]+=1
            CT[n.id]=c
        else:
            STR[n.id]=STR[n.left.id]+STR[n.right.id]; c=CT[n.left.id].copy(); c.update(CT[n.right.id]); CT[n.id]=c
    W={k:len(STR[k]) for k in STR}; rcnt=CT[root.id]
    def synapo(nid):
        # DEFINISSABILITE per-pool : marqueur CONCENTRE dans le noeud (in>=t_in) et RARE dans le reste de
        # la lignee (out<=t_out). Exclusivite globale = garde-fou OPTIONNEL (KGLOB>0 ; off par defaut).
        w=W[nid]; ct=CT[nid]; ot=nR-w
        return sum(1 for x,k in ct.items() if k>=T_IN*w and (rcnt[x]-k)<=T_OUT*max(ot,1) and (KGLOB<=0 or gexcl(x)<=KGLOB))
    SYN={k:synapo(k) for k in STR}
    return dict(root=root,STR=STR,CT=CT,W=W,SYN=SYN,nR=nR,geo=geo,is_markers=is_markers,Rprof=Rprof,
                gexcl=gexcl,rcnt=rcnt)

def make_dp(B,LAM):
    STR=B['STR']; W=B['W']; SYN=B['SYN']; geo=B['geo']
    def nbp(ss): return len(set(geo[s]['bp'] for s in ss if geo.get(s,{}).get('bp')))
    def geo_ll(ss):
        v=[geo[s]['c'] for s in ss if geo.get(s,{}).get('c')]; n=len(v)
        if n==0: return 0.0
        c=Counter(v); return sum(k*math.log(k/n) for k in c.values())
    def cost(ss): return LAM*(1.0 if nbp(ss)>=2 else 1.5)
    def gval(g): return (geo_ll(g)-cost(g)) if len(g)>=5 else 0.0
    def feasible(nid): return W[nid]>=5 and SYN[nid]>=MINSYN
    def fchildren(node):
        out=[]; st=[node.left,node.right] if not node.is_leaf() else []
        while st:
            x=st.pop()
            if feasible(x.id): out.append(x)
            elif not x.is_leaf(): st+=[x.left,x.right]
        return out
    memo={}; struct={}   # struct[nid] = ('T',) terminal | ('S', [child_ids inclus], [grade]) subdivisé
    def dp(node):
        nid=node.id
        if nid in memo: return memo[nid]
        v_term=geo_ll(STR[nid])-cost(STR[nid]); fch=fchildren(node)
        if not fch: memo[nid]=(v_term,[('T',nid)]); struct[nid]=('T',); return memo[nid]
        cb={c.id:dp(c) for c in fch}; cs={c.id:set(STR[c.id]) for c in fch}
        inc=[]; grade=set(STR[nid]); gv=gval(list(grade)); imp=True
        while imp:
            imp=False; bc=None; bgain=1e-9; bg=None; bgv=0.0
            for c in fch:
                if c.id in inc: continue
                ng=grade-cs[c.id]; ngv=gval(list(ng)); gn=cb[c.id][0]+ngv-gv
                if gn>bgain: bgain=gn; bc=c; bg=ng; bgv=ngv
            if bc is not None: inc.append(bc.id); grade=bg; gv=bgv; imp=True
        sv=sum(cb[i][0] for i in inc)+gv; sp=[p for i in inc for p in cb[i][1]]
        if len(grade)>=5: sp.append(('G',nid,sorted(grade)))
        if v_term>=sv: memo[nid]=(v_term,[('T',nid)]); struct[nid]=('T',)
        else: memo[nid]=(sv,sp); struct[nid]=('S',list(inc),sorted(grade))
        return memo[nid]
    return dp,geo_ll,nbp,struct

# parametres communs
def cargs(i0):
    MINSYN=int(sys.argv[i0]) if len(sys.argv)>i0 else 2
    T_IN=float(sys.argv[i0+1]) if len(sys.argv)>i0+1 else 0.9
    T_OUT=float(sys.argv[i0+2]) if len(sys.argv)>i0+2 else 0.02
    KGLOB=int(sys.argv[i0+3]) if len(sys.argv)>i0+3 else 0   # 0 = exclusivite globale OFF (definissabilite per-pool)
    return MINSYN,T_IN,T_OUT,KGLOB

if MODE=='optimize':
    LAMBDAS=[float(x) for x in sys.argv[3].split(',')] if len(sys.argv)>3 else [5,10,20,35,55,90]
    MINSYN,T_IN,T_OUT,KGLOB=cargs(4)
    B=build()
    nfeas=sum(1 for k in B['STR'] if B['W'][k]>=5 and B['SYN'][k]>=MINSYN)
    print(f"[{ROOT}] reps={len(B['STR'])} faisables(>= {MINSYN} synapo, >=5)={nfeas}")
    print(f"{'lambda':>7}{'lignees':>9}{'%res':>6}{'coh':>6}{'obj':>9}")
    for LAM in LAMBDAS:
        dp,geo_ll,nbp,_=make_dp(B,LAM); val,part=dp(B['root'])
        terms=[p for p in part if p[0] in ('T','G')]
        nin=sum(B['W'][p[1]] if p[0]=='T' else len(p[2]) for p in terms)
        tot=cw=0
        for p in terms:
            ss=B['STR'][p[1]] if p[0]=='T' else p[2]
            v=[B['geo'][s]['c'] for s in ss if B['geo'].get(s,{}).get('c')]
            if len(v)>=3: f=Counter(v).most_common(1)[0][1]/len(v); tot+=len(v); cw+=f*len(v)
        print(f"{LAM:>7.0f}{len(terms):>9}{100*nin/B['nR']:>5.0f}%{(cw/tot if tot else 0):>6.2f}{val:>9.0f}",flush=True)
    sys.exit(0)

if MODE in ('inspect','materialize'):
    LAM=float(sys.argv[3]); MINSYN,T_IN,T_OUT,KGLOB=cargs(4)
    APPLY = (MODE=='materialize' and sys.argv[-1]=='apply')
    B=build(); dp,geo_ll,nbp,struct=make_dp(B,LAM); val,part=dp(B['root'])
    STR=B['STR']; SYN=B['SYN']; geo=B['geo']; is_markers=B['is_markers']; Rprof=B['Rprof']
    s1=set(STR[B['root'].left.id])
    def yr(s):
        m=re.search(r'(1[89]\d\d|20[012]\d)',s or ''); return int(m.group(1)) if m else None
    F_PAYS,F_SPAN,F_IS=4,30,3
    terms=[]
    for p in part:
        if p[0]=='T': nid=p[1]; ss=STR[nid]; kind='clade'
        else: nid=p[1]; ss=list(p[2]); kind='grade'
        terms.append((nid,ss,SYN[nid],kind))
    rows=[]
    for nid,ss,syn,kind in terms:
        cc=Counter(geo[s]['c'] for s in ss if geo.get(s,{}).get('c')); ncov=sum(cc.values())
        bd=", ".join(f"{c} {round(100*k/ncov)}%" for c,k in cc.most_common(3)) if ncov else "—"
        npays=sum(1 for c,k in cc.items() if k>=2)
        yrs=[y for s in ss for y in [yr(geo.get(s,{}).get('dmin')),yr(geo.get(s,{}).get('dmax'))] if y]
        span=(max(yrs)-min(yrs)) if yrs else 0; yr_s=f"{min(yrs)}-{max(yrs)}" if yrs else "—"
        n=len(ss); isd=0
        if is_markers:
            ic=Counter()
            for s in ss:
                for x in Rprof.get(s,()):
                    if x in is_markers: ic[x]+=1
            isd=sum(1 for x,k in ic.items() if 2<=k<=n-2)
        nb=len(set(geo[s]['bp'] for s in ss if geo.get(s,{}).get('bp')))
        f1=sum(1 for s in ss if s in s1)/n
        flag=(npays>=F_PAYS) or (span>=F_SPAN) or (isd>=F_IS)
        rows.append(('.1' if f1>=0.5 else '.2',n,syn,nb,npays,span,isd,bd,yr_s,kind,flag,ss,nid))
    rows.sort(key=lambda r:(r[0],-r[1]))
    print(f"=== {ROOT} MDL+repli lambda={LAM} MINSYN={MINSYN} : {len(rows)} lignees, {sum(r[1] for r in rows)}/{B['nR']} ===")
    print(f"{'br':>3}{'n':>6}{'syn':>4}{'BP':>3}{'pays':>5}{'span':>5}{'ISd':>4} {'fenetre':<11}{'k':<6} pays [⚑]")
    for br,n,syn,nb,npays,span,isd,bd,yr_s,kind,flag,ss,nid in rows:
        print(f"{br:>3}{n:>6}{syn:>4}{nb:>3}{npays:>5}{span:>5}{isd:>4} {yr_s:<11}{kind:<6} {bd[:36]} {'⚑' if flag else ''}")
    print(f"lignees={len(rows)} flaguees(pays>={F_PAYS}|span>={F_SPAN}|ISd>={F_IS})={sum(1 for r in rows if r[10])}")
    tsv=RES/f'inspect_lam{int(LAM)}.tsv'
    with open(tsv,'w') as f:
        f.write("branche\tn\tsynapo\tn_bioproject\tn_pays\tspan\tIS_div\tdate_range\tkind\tflag\tpays\n")
        for br,n,syn,nb,npays,span,isd,bd,yr_s,kind,flag,ss,nid in rows:
            f.write(f"{br}\t{n}\t{syn}\t{nb}\t{npays}\t{span}\t{isd}\t{yr_s}\t{kind}\t{int(flag)}\t{bd}\n")
    print(f"-> {tsv}")
    if MODE=='inspect': sys.exit(0)
    # ---- MATERIALIZE HIÉRARCHIQUE : nomme les NŒUDS INTERNES synapo-soutenus comme parents ----
    # (corrige la matérialisation plate qui ratait les clades intermédiaires type Ancien Monde)
    STR=B['STR']; SYN=B['SYN']
    named=[]   # (name, nid, kind, strains_propres) ; kind='clade'(terminal) | 'node'(intermédiaire: grade)
    def emit(nid,name):
        s=struct.get(nid,('T',))
        if s[0]=='T': named.append((name,nid,'clade',STR[nid])); return
        inc,grade=s[1],s[2]
        # COLLAPSE pass-through : nœud d'épine à 1 enfant + grade<5 -> ne pas créer de niveau
        if len(inc)==1 and len(grade)<5: emit(inc[0],name); return
        for k,cid in enumerate(sorted(inc,key=lambda i:-len(STR[i])),1): emit(cid,f"{name}.{k}")
        if len(grade)>=5: named.append((name,nid,'node',grade))
    emit(B['root'].id,ROOT)
    # RENUMÉROTATION PROPRE séquentielle par niveau (option CG) : A.1,A.2 ; A.1.1,A.1.2 ; ... (triés par taille)
    names_set={tn for tn,_,_,_ in named}
    def parent_of(tn):
        parts=tn.split('.')
        for i in range(len(parts)-1,0,-1):
            p='.'.join(parts[:i])
            if p in names_set: return p
        return None
    childs=defaultdict(list)
    for rec in named: childs[parent_of(rec[0])].append(rec)
    clean={}
    if ROOT in names_set: clean[ROOT]=ROOT
    def assign(par_tn,par_clean):
        for k,rec in enumerate([r for r in sorted(childs[par_tn],key=lambda t:-len(t[3])) if r[0]!=ROOT],1):
            cn=f"{par_clean}.{k}"; clean[rec[0]]=cn; assign(rec[0],cn)
    assign(None,ROOT)
    if ROOT in names_set: assign(ROOT,ROOT)
    named=[(clean.get(tn,tn),nid,kind,strains) for tn,nid,kind,strains in named]
    # ---- ASSIGNATION CHARACTER-BASED (corrige le misplacement des GRADES par le dendrogramme phenetique) ----
    # Le dendrogramme average-linkage misplace les souches de GRADE (faible signal) -> un grade ressort
    # polyphyletique (vecu A.2 17 souches, D 15 souches). On REASSIGNE chaque souche au noeud nomme le plus
    # profond dont elle PORTE la signature synapomorphique (markers), pas par appartenance au noeud du dendro.
    # Principe : membership = porteurs du SNP signature. Les CLADES (haute synapo) sont robustes ; ce passage
    # corrige surtout les GRADES. Descente : a chaque niveau, la souche descend dans l'enfant dont elle porte
    # le PLUS de marqueurs-signature, si dominance nette (>=1 marqueur ET >=2x le 2e enfant ou 2e=0) ; sinon
    # elle reste au grade du noeud courant (robuste au missing-data).
    _CT=B['CT']; _W=B['W']; _nR=B['nR']; _rcnt=B['rcnt']; _gexcl=B['gexcl']; _root=B['root']
    def _synset(nid):
        w=_W[nid]; ct=_CT[nid]; ot=_nR-w
        return set(x for x,k in ct.items() if k>=T_IN*w and (_rcnt[x]-k)<=T_OUT*max(ot,1) and (KGLOB<=0 or _gexcl(x)<=KGLOB))
    _names={nm for nm,_,_,_ in named}
    _nidof={nm:nid for nm,nid,_,_ in named}
    _kindof={nm:kind for nm,_,kind,_ in named}
    _SS={nm:_synset(_nidof[nm]) for nm in _names}
    def _parent(nm):
        parts=nm.split('.')
        for i in range(len(parts)-1,0,-1):
            p='.'.join(parts[:i])
            if p in _names: return p
        return None
    _kids=defaultdict(list)
    for nm in _names: _kids[_parent(nm)].append(nm)
    CLADE_FRAC=0.4   # pour ENTRER dans un clade crown (terminal) : fraction min de sa signature portée
    def _deepest(s):
        # descente : NODE (branche) = dominance RELATIVE (>=2 markers, comme un test de bipartition) ;
        # CLADE (crown terminal) = appartenance ABSOLUE (>=CLADE_FRAC de la signature crown). Évite de jeter
        # une souche de grade basale dans un crown sur 1-2 markers profonds (sur-pull qui rend le crown
        # polyphylétique) tout en la plaçant sur la BONNE branche (ce que le dendrogramme rate).
        prof=Rprof.get(s,())
        cur = ROOT if ROOT in _names else None
        kids = _kids.get(cur, [])
        while kids:
            cnt={k:sum(1 for x in _SS[k] if x in prof) for k in kids if _SS[k]}
            if not cnt: break
            best=max(cnt,key=cnt.get); srt=sorted(cnt.values(),reverse=True)
            dominant = srt[0]>=2 and (len(srt)<2 or srt[1]==0 or srt[0]>=2*srt[1])
            if _kindof[best]=='clade':
                ok = dominant and cnt[best] >= CLADE_FRAC*len(_SS[best])
            else:  # node (branche)
                ok = dominant
            if ok: cur=best; kids=_kids.get(best,[])
            else: break
        return cur   # None ou ROOT -> reste dans le dir ROOT (grade racine)
    _assigned=defaultdict(list)
    for s in STR[_root.id]:
        d=_deepest(s)
        if d is not None and d!=ROOT: _assigned[d].append(s)
    named=[(nm,nid,kind,_assigned.get(nm,[])) for nm,nid,kind,_ in named]
    with open(RES/f'assign_lam{int(LAM)}.tsv','w') as _af:
        _af.write("sra\tdest\n")
        for _nm,_,_,_ss in named:
            for _s in _ss: _af.write(f"{_s}\t{_nm}\n")
    def annot2(strains):
        cc=Counter(geo[s]['c'] for s in strains if geo.get(s,{}).get('c')); ncov=sum(cc.values())
        bd=", ".join(f"{c} {round(100*k/ncov)}%" for c,k in cc.most_common(3)) if ncov else "—"
        nb=len(set(geo[s]['bp'] for s in strains if geo.get(s,{}).get('bp'))); return bd,nb
    named.sort(key=lambda t:t[0])
    MAP=RES/f'materialize_map_lam{int(LAM)}.tsv'
    with open(MAP,'w') as mf:
        mf.write("dest\tn_propre\tsynapo\tkind\tn_bioproject\tpays\n")
        for name,nid,kind,strains in named:
            bd,nb=annot2(strains); mf.write(f"{name}\t{len(strains)}\t{SYN[nid]}\t{kind}\t{nb}\t{bd}\n")
    nnode=sum(1 for x in named if x[2]=='node'); nclade=sum(1 for x in named if x[2]=='clade')
    print(f"\n[materialize {'APPLY' if APPLY else 'DRY'}] HIÉRARCHIQUE : {len(named)} nœuds ({nnode} intermédiaires + {nclade} terminaux) ; map: {MAP}")
    for name,nid,kind,strains in [x for x in named if x[0].count('.')<=ROOT.count('.')+2][:30]:
        bd,_=annot2(strains); ind='  '*(name.count('.')-ROOT.count('.'))
        print(f"  {ind}{name:<36} propre={len(strains):<5} syn={SYN[nid]:<3} {kind:<6} {bd[:32]}")
    if not APPLY:
        print("  DRY-RUN : aucun ecrit. Ajouter 'apply' pour matérialiser (log réversible)."); sys.exit(0)
    LOG=RES/'materialize_log.tsv'; (BDD/ROOT).mkdir(exist_ok=True)
    # 1) flatten : ramener toutes les souches des sous-dirs existants vers ROOT
    old=[x for x in os.listdir(BDD) if (BDD/x).is_dir() and inroot(x) and x!=ROOT]
    for d in old:
        for s in os.listdir(BDD/d):
            if has(d,s) and not (BDD/ROOT/s).exists(): os.rename(BDD/d/s, BDD/ROOT/s)
    # 2) trash des anciens dirs vidés (gio trash, jamais rm)
    empt=[str(BDD/d) for d in old if (BDD/d).is_dir() and not any(has(d,x) for x in os.listdir(BDD/d))]
    if empt: subprocess.run(['gio','trash']+empt, check=False)
    # 3) créer la hiérarchie + déplacer (parents avant enfants via tri par nom)
    moved=0
    with open(LOG,'w') as lf:
        lf.write("sra\tdest\n")
        for name,nid,kind,strains in named:
            if name==ROOT: continue   # le grade racine reste dans le dir A
            (BDD/name).mkdir(parents=True, exist_ok=True)
            for s in strains:
                src=BDD/ROOT/s
                if src.is_dir() and not (BDD/name/s).exists(): os.rename(src, BDD/name/s); lf.write(f"{s}\t{name}\n"); moved+=1
    rest=sum(1 for s in os.listdir(BDD/ROOT) if has(ROOT,s))
    print(f"  APPLY: {moved} souches déplacées ; {len(named)} nœuds créés ; anciens dirs trashés={len(empt)} ; restant à {ROOT}={rest} ; log {LOG}")
    sys.exit(0)

# ---------- DEEPEN : ré-investigation RELACHEE d'un coeur flaggé (geo homogene -> synapo+IS) ----------
if MODE=='deepen':
    LAM=float(sys.argv[3]); MINSYN,T_IN,T_OUT,KGLOB=cargs(4)
    TARGET=int(os.environ.get('DEEPEN_IDX','0'))   # 0 = plus gros terminal/grade FLAGGE
    DMIN=int(os.environ.get('DEEPEN_MINSYN','1')); DTIN=float(os.environ.get('DEEPEN_TIN','0.85'))
    B=build(); dp,_,_,_=make_dp(B,LAM); val,part=dp(B['root'])
    STR=B['STR']; SYN=B['SYN']; geo=B['geo']; is_markers=B['is_markers']; Rprof=B['Rprof']
    F_PAYS,F_SPAN,F_IS=4,30,3
    def yr(s):
        m=re.search(r'(1[89]\d\d|20[012]\d)',s or ''); return int(m.group(1)) if m else None
    cands=[]
    for p in part:
        nid=p[1]; ss=STR[nid] if p[0]=='T' else list(p[2])
        cc=Counter(geo[s]['c'] for s in ss if geo.get(s,{}).get('c'))
        npays=sum(1 for c,k in cc.items() if k>=2)
        yrs=[y for s in ss for y in [yr(geo.get(s,{}).get('dmin')),yr(geo.get(s,{}).get('dmax'))] if y]
        span=(max(yrs)-min(yrs)) if yrs else 0
        ic=Counter()
        for s in ss:
            for x in Rprof.get(s,()):
                if x in is_markers: ic[x]+=1
        isd=sum(1 for x,k in ic.items() if 2<=k<=len(ss)-2)
        if (npays>=F_PAYS) or (span>=F_SPAN) or (isd>=F_IS): cands.append((len(ss),ss,nid))
    cands.sort(key=lambda t:-t[0])
    if not cands: print("aucun terminal flagge."); sys.exit(0)
    tgt=cands[min(TARGET,len(cands)-1)][1]; tset=set(tgt)
    print(f"[deepen] cible = terminal flagge #{TARGET} : {len(tgt)} souches ; relache MINSYN={DMIN} t_in={DTIN} ; arbre SNP+IS+RD",flush=True)
    # marqueurs variables DANS la cible (SNP cand + RD/IS deja dans Rprof) ; arbre sur SNP+IS+RD
    sub=[s for s in tgt if s in Rprof]; cnt=Counter()
    for s in sub:
        for x in Rprof[s]: cnt[x]+=1
    ns=len(sub); subm=[x for x,k in cnt.items() if 3<=k<=ns-3]
    if len(subm)<2 or ns<10: print(f"  cible trop petite/homogene ({ns} souches, {len(subm)} marqueurs)"); sys.exit(0)
    idx={x:i for i,x in enumerate(subm)}; MM=np.zeros((ns,len(subm)),np.uint8)
    for i,s in enumerate(sub):
        for x in Rprof[s]:
            if x in idx: MM[i,idx[x]]=1
    cl=fcluster(linkage(pdist(MM,'hamming'),'complete'),t=2.5/len(subm),criterion='distance')
    grp=defaultdict(list)
    for i,c in enumerate(cl): grp[c].append(sub[i])
    repl=[grp[c] for c in sorted(grp)]; MR=np.zeros((len(repl),len(subm)),np.uint8)
    for j,mem in enumerate(repl):
        cc=np.zeros(len(subm))
        for s in mem:
            for x in Rprof[s]:
                if x in idx: cc[idx[x]]+=1
        MR[j]=(cc>=len(mem)/2.0).astype(np.uint8)
    rt=to_tree(linkage(pdist(MR,'hamming'),'average'))
    po=[]; stk=[(rt,False)]
    while stk:
        n,d=stk.pop()
        if n.is_leaf(): po.append(n); continue
        if d: po.append(n)
        else: stk+=[(n,True),(n.left,False),(n.right,False)]
    LVS={}; CTs={}
    for n in po:
        if n.is_leaf(): LVS[n.id]=repl[n.id]; c=Counter()
        else: LVS[n.id]=LVS[n.left.id]+LVS[n.right.id]; c=CTs[n.left.id].copy(); c.update(CTs[n.right.id]); CTs[n.id]=c; continue
        for s in repl[n.id]:
            for x in Rprof[s]:
                if x in idx: c[x]+=1
        CTs[n.id]=c
    DGAIN=int(os.environ.get('DEEPEN_GAIN','8'))   # GAIN-de-synapo mini vs parent (evite la cascade clonale)
    def nbp_local(mem): return len(set(geo[s]['bp'] for s in mem if geo.get(s,{}).get('bp')))
    # pectination par GAIN-de-synapo (marqueurs NOUVEAUX vs parent, PAS absolu) + multi-BioProject
    named=[]; counter=[0]
    def gain(cid,par_ct,par_n):
        w=len(LVS[cid]); ct=CTs[cid]
        return sum(1 for x,k in ct.items() if k>=DTIN*w and (par_ct.get(x,0)-k)<=0.05*max(par_n-w,1))
    def walk(node,par_ct,par_n):
        if node.is_leaf(): return
        for c in sorted([node.left,node.right],key=lambda k:-len(LVS[k.id])):
            mem=LVS[c.id]
            if len(mem)<5: continue
            g=gain(c.id,par_ct,par_n)
            if g>=DGAIN and nbp_local(mem)>=2:
                counter[0]+=1; named.append((counter[0],mem,g)); walk(c,CTs[c.id],len(mem))
            else: walk(c,par_ct,par_n)
    walk(rt,CTs[rt.id],ns)
    named.sort(key=lambda t:-len(t[1]))
    print(f"  {len(named)} sous-clades relaches dans la cible :")
    print(f"  {'n':>5}{'syn':>5}{'IS':>4}{'span':>6} pays / hote")
    for k,mem,sy in named[:40]:
        cc=Counter(geo[s]['c'] for s in mem if geo.get(s,{}).get('c')); ncov=sum(cc.values())
        bd=", ".join(f"{c} {round(100*v/ncov)}%" for c,v in cc.most_common(2)) if ncov else "—"
        ic=Counter()
        for s in mem:
            for x in Rprof.get(s,()):
                if x in is_markers: ic[x]+=1
        nis=sum(1 for x,v in ic.items() if v>=0.85*len(mem))
        yrs=[y for s in mem for y in [yr(geo.get(s,{}).get('dmin')),yr(geo.get(s,{}).get('dmax'))] if y]
        sp=f"{min(yrs)}-{max(yrs)}" if yrs else "—"
        print(f"  {len(mem):>5}{sy:>5}{nis:>4}{sp:>11} {bd[:40]}")
    print(f"\n[deepen] cible {len(tgt)} souches -> {len(named)} sous-clades relaches (MINSYN={DMIN}, SNP+IS).")
    sys.exit(0)
usage()
