import sys, json, re, pandas as pd
sys.path.insert(0,'src'); from normalize import key
U=pd.DataFrame(json.load(open('raw/permissible_use.json')))
U['ut']=U.Use_Type.fillna('').str.replace(r'\s+',' ',regex=True).str.strip()
STATUS={'A':'Allowed','S':'Special Use','P':'Allowed','CUP':'Conditional Use','MUP':'Minor Use','AR':'Administrative Review','T':'Temporary Use','TRPA':'TRPA Review'}
def k2(s):
    s=s.lower().replace('&',' and ').replace('–','-').replace('—','-')
    s=re.sub(r'\(.*?\)','',s) if not re.search(r'\((hotel|residential|less|10%)',s) else s
    s=re.sub(r'\b(new non-emergency sites prohibited|includes condominiums)\b','',s)
    return key(s)
def status_of(raw):
    if raw is None or (isinstance(raw,float)): return None
    m=re.match(r'^(TRPA|CUP|MUP|AR|A|S|P|T)',raw)
    return STATUS[m.group(1)] if m else None
def compare(rows, zones, alias={}, plan=''):
    R=pd.DataFrame(rows); R['status']=R.raw.apply(status_of); R['foot']=R.raw.str.extract(r'^(?:TRPA|CUP|MUP|AR|A|S|P|T)(.*)$')[0]
    R['use_key']=R.label.map(lambda l: k2(alias.get(l,l)))
    S=U[U.Zoning_ID.isin(zones)].copy(); S['use_key']=S.ut.map(k2)
    # label -> service name lookup (for reporting)
    svc_name=S.drop_duplicates('use_key').set_index('use_key').ut.to_dict()
    unmatched=sorted(set(R.label[~R.use_key.isin(set(S.use_key))]))
    E=R[R.status.notna()][['zone','label','use_key','status','raw','page']].rename(columns={'zone':'ZONING_ID'})
    Sx=S[['Zoning_ID','use_key','ut','Use_Status','OBJECTID','GlobalID','Notes']].rename(columns={'Zoning_ID':'ZONING_ID'})
    M=E.merge(Sx,on=['ZONING_ID','use_key'],how='outer',indicator=True)
    M['issue']=M._merge.astype(str).map({'left_only':'missing from service','right_only':'in service, not in PDF','both':''})
    M.loc[(M._merge=='both')&(M.status!=M.Use_Status),'issue']='status mismatch'
    # PDF says not permitted ("-") but service has it: flag separately
    dash=R[R.status.isna()&R.raw.notna()][['zone','use_key']].rename(columns={'zone':'ZONING_ID'}).assign(pdf_dash=True)
    M=M.merge(dash.drop_duplicates(),on=['ZONING_ID','use_key'],how='left')
    M.loc[(M.issue=='in service, not in PDF')&(M.pdf_dash==True),'issue']='in service, PDF says not permitted'
    M['plan']=plan
    return M.drop(columns='_merge'), unmatched, R
def summary(M):
    print(M.issue.replace('','match').value_counts().to_string())
