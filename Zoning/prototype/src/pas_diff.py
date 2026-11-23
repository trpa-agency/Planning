import sys, json, re, pandas as pd
sys.path.insert(0,'src')
from normalize import canon, key
U=pd.DataFrame(json.load(open('raw/permissible_use.json'))); D=pd.DataFrame(json.load(open('raw/district_attr.json')))
vocab={}
for v in U.Use_Type.dropna().str.replace(r'\s+',' ',regex=True).str.strip().value_counts().index: vocab.setdefault(key(v),v)
FAM={'Raising Domestic Animals':'Domestic Animal Raising'}
def fam(u):
    if not isinstance(u,str): return u
    u=FAM.get(u,u)
    return re.sub(r'\s*\(?(less than 10%|10% or more)[^)]*\)?$','',u).strip()
U['canon']=U.Use_Type.fillna('').apply(lambda x: canon(x,vocab)[0] if x else None)
R=pd.read_csv('pas_raw_uses.csv',dtype={'PLAN_ID':str}); R=R[R.block!='SHOREZONE']
GENREF=R[R.raw_use=='__GENERAL__']; R=R[R.raw_use!='__GENERAL__']
R['canon']=R.raw_use.apply(lambda x: canon(x,vocab)); R=R.explode('canon'); R['canon']=R.canon.apply(fam)
un=R[R.canon.isna()]; print('unmatched PDF phrases:',len(un), un.raw_use.unique()[:10])
ST={'A':'Allowed','S':'Special Use'}
PAS=D[D.PLAN_TYPE=='Plan Area Statement']
exp=[]
for z,pid in zip(PAS.ZONING_ID,PAS.PLAN_ID):
    r=R[R.PLAN_ID==pid]
    if r.empty: continue
    m=re.search(r'_SA(\d+)$',z)
    gen=r[r.block=='GENERAL']
    if m:
        sa=r[r.block==f'SA{m.group(1)}']
        if sa.empty: rows,basis=gen,'general (no special area list in PDF)'
        elif (sa['mode']=='plus').any(): rows,basis=pd.concat([gen,sa]),'general plus SA additions'
        else:
            rows,basis=sa,'SA list only'
            ref=GENREF[(GENREF.PLAN_ID==pid)&(GENREF.block==f'SA{m.group(1)}')]
            if len(ref):
                cats=set(ref.category.str.replace('Services','Service'))
                rows=pd.concat([gen[gen.category.str.replace('Services','Service').isin(cats)],sa]); basis='SA list plus general list categories: '+', '.join(sorted(cats))
    else: rows,basis=gen,'general'
    rows=rows.drop_duplicates('canon',keep='last')   # SA additions override general
    for x in rows.itertuples(): exp.append(dict(ZONING_ID=z,PLAN_ID=pid,use=x.canon,pdf_status=ST[x.status],pdf_phrase=x.raw_use,basis=basis))
E=pd.DataFrame(exp)
U['canon']=U.canon.apply(fam)
S=U[U.Zoning_ID.isin(E.ZONING_ID.unique())][['Zoning_ID','canon','Use_Type','Use_Status','OBJECTID']].rename(columns={'Zoning_ID':'ZONING_ID','canon':'use','Use_Status':'svc_status'})
S=S.drop_duplicates(['ZONING_ID','use'])
M=E.merge(S,on=['ZONING_ID','use'],how='outer',indicator=True)
M['issue']=M._merge.astype(str).map({'left_only':'missing from service','right_only':'in service, not in PDF','both':''})
M.loc[(M._merge=='both')&(M.pdf_status!=M.svc_status),'issue']='status mismatch'
M['PLAN_ID']=M.PLAN_ID.fillna(M.ZONING_ID.str.extract(r'^(\d{3}[A-Z]?)')[0])
M=M.drop(columns='_merge'); M.to_csv('out_pas_use_diff.csv',index=False)
nd=sorted(set(PAS.ZONING_ID)-set(E.ZONING_ID)); print('PAS districts not compared (no PDF list):',nd)
print('compared districts',E.ZONING_ID.nunique(),'| pdf rows',len(E),'| service rows',len(S))
print(M.issue.replace('', 'match').value_counts().to_string())
iss=M[M.issue!='']
print('\ndistricts with any issue:',iss.ZONING_ID.nunique(),'of',E.ZONING_ID.nunique())
print(iss.groupby('ZONING_ID').issue.value_counts().unstack(fill_value=0).sort_values(by=list(iss.issue.unique()),ascending=False).head(40).to_string())
print('\nmost common uses in issues:'); print(iss.groupby(['issue','use']).size().sort_values(ascending=False).head(30).to_string())
