import sys, json, re, pandas as pd
sys.path.insert(0,'src'); from normalize import canon, key
U=pd.DataFrame(json.load(open('raw/permissible_use.json'))); D=pd.DataFrame(json.load(open('raw/district_attr.json')))
vocab={}
for v in U.Use_Type.dropna().str.replace(r'\s+',' ',regex=True).str.strip().value_counts().index: vocab.setdefault(key(v),v)
fam=lambda u: re.sub(r'\s*\(?(less than 10%|10% or more)[^)]*\)?$','',u).strip() if isinstance(u,str) else u
def unit(u):
    u=str(u).lower().strip(' .§*')
    u=u.replace('dwelling ','').replace('people','persons').replace('units','unit').replace('sites','site').replace('lots','lot')
    return re.sub(r'\s+',' ',u)
P=pd.read_csv('pas_densities.csv',dtype={'PLAN_ID':str})
P['use_c']=P.use.apply(lambda x: fam((canon(x,vocab) or [None])[0])); P['unit_n']=P.unit.apply(unit)
print('density lines unmatched:',P.use_c.isna().sum(), P[P.use_c.isna()].use.tolist()[:15])
U['use_c']=U.Use_Type.apply(lambda x: fam((canon(x,vocab) if isinstance(x,str) else [None])[0])); U['unit_n']=U.Unit.apply(unit)
PAS=D[D.PLAN_TYPE=='Plan Area Statement'][['ZONING_ID','PLAN_ID']]
S=U.merge(PAS,left_on='Zoning_ID',right_on='ZONING_ID')
S=S[S.PLAN_ID.isin(P.PLAN_ID)]
M=S.merge(P.drop_duplicates(['PLAN_ID','use_c']),on=['PLAN_ID','use_c'],how='left',suffixes=('','_pdf'))
has_den=M.Density.notna()|M.density.notna()
M=M[has_den & M.use_c.notna()]
M['issue']=''
M.loc[M.density.isna()&M.Density.notna(),'issue']='density in service, none in PDF'
M.loc[M.density.notna()&M.Density.isna(),'issue']='density in PDF, missing in service'
both=M.density.notna()&M.Density.notna()
M.loc[both&(M.density!=M.Density),'issue']='density value mismatch'
M.loc[both&(M.density==M.Density)&(M.unit_n!=M.unit_n_pdf),'issue']='unit mismatch'
M=M[['ZONING_ID','PLAN_ID','Use_Type','Density','Unit','density','unit','issue']].rename(columns={'Density':'svc_density','Unit':'svc_unit','density':'pdf_density','unit':'pdf_unit'})
M.to_csv('out_pas_density_diff.csv',index=False)
print(M.issue.replace('','match').value_counts().to_string())
pd.set_option('display.width',250); pd.set_option('display.max_rows',100)
print(M[M.issue!=''].sort_values(['issue','ZONING_ID']).to_string(index=False))
