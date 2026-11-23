import sys, json, re, pandas as pd
sys.path.insert(0,'src'); from normalize import canon, key
from pas_parse import clean_lines, section
U=pd.DataFrame(json.load(open('raw/permissible_use.json'))); D=pd.DataFrame(json.load(open('raw/district_attr.json')))
vocab={}
for v in U.Use_Type.dropna().str.replace(r'\s+',' ',regex=True).str.strip().value_counts().index: vocab.setdefault(key(v),v)
EXTRA={'bed and breakfast':'Bed and Breakfast Facilities','hotel motel and other transient unit':'Hotel, Motel, and Other Transient Dwelling Units',
 'hotel motel and other transient dwelling':'Hotel, Motel, and Other Transient Dwelling Units','hotel motel and other':'Hotel, Motel, and Other Transient Dwelling Units',
 'timeshare':'Time Sharing','resort':'Resort','rural group facilitie':'Group Facilities'}
def cu(x):
    k=key(x)
    if k in EXTRA: return EXTRA[k]
    c=canon(x,vocab)[0]; return c
NUM=re.compile(r'^(.*?)\s{2,}(\d+(?:\.\d+)?)\s+([a-z].*?)\s*(Recreation|Tourist Accommodation|Residential)?$',re.I)
rows=[]
LP=pd.read_csv('out_pdf_inventory.csv',dtype={'PLAN_ID':str})
for p in LP[LP.PLAN_TYPE=='Plan Area Statement'].PLAN_ID:
    try: L=clean_lines(open(f'txt/{p}.txt',errors='ignore').read())
    except FileNotFoundError: continue
    sec=section(L,r'^\s*MAXIMUM DENSITIES',r'^\s*MAXIMUM COMMUNITY|^\s*ADDITIONAL DEVELOPMENT|^\s*IMPROVEMENT PROGRAMS')
    last=None
    for l in sec[2:]:
        s=l.strip()
        if not s or s.upper().startswith(('USE','DENSITY','RESIDENTIAL','TOURIST ACC','RECREATION','PUBLIC SERV','COMMERCIAL')) and not re.search(r'\d',s): continue
        bullet=s.startswith(('•','-','·'))
        m=NUM.match(re.sub(r'^[•·\-]\s*','',s)) if True else None
        if m:
            name=m.group(1).strip(' :'); dens=float(m.group(2)); unit=m.group(3).strip(' .§*')
            if bullet and last:
                sa=re.findall(r'#(\d)',name) if 'special area' in name.lower() else []
                q='less' if 'less than' in name.lower() else ('more' if 'or more' in name.lower() else '')
                rows.append(dict(PLAN_ID=p,use=last,qual=q,sa=','.join(sa),density=dens,unit=unit))
            else:
                last=cu(name); rows.append(dict(PLAN_ID=p,use=last,qual='',sa='',density=dens,unit=unit,raw=name))
        elif not bullet and not re.search(r'\d',s) and len(s)<70:
            last=cu(s)
P=pd.DataFrame(rows); P.to_csv('pas_densities2.csv',index=False)
print('density rows',len(P),'| uncanon:',P.use.isna().sum(), P[P.use.isna()].raw.tolist() if 'raw' in P else '')
def unit(u):
    u=str(u).lower().strip(' .§*'); u=u.replace('dwelling ','').replace('people','persons').replace('units','unit').replace('sites','site')
    return re.sub(r'\s+',' ',u)
PAS=D[D.PLAN_TYPE=='Plan Area Statement'][['ZONING_ID','PLAN_ID']]
S=U.merge(PAS,left_on='Zoning_ID',right_on='ZONING_ID'); S=S[S.PLAN_ID.isin(P.PLAN_ID)&S.Use_Type.notna()]
out=[]
for r in S.itertuples():
    ut=re.sub(r'\s+',' ',r.Use_Type).strip()
    q='less' if 'less than 10%' in ut else ('more' if '10% or more' in ut else '')
    base=re.sub(r'\s*\(?(less than 10%|10% or more)[^)]*\)?$','',ut).strip()
    b=cu(base) or base
    if b.startswith('Time Sharing'): b='Time Sharing'
    sa=(re.search(r'_SA(\d+)$',r.ZONING_ID) or [None,''])[1]
    cand=P[(P.PLAN_ID==r.PLAN_ID)&(P.use==b)]
    if q and (cand.qual==q).any(): cand=cand[cand.qual==q]
    elif q: cand=cand[cand.qual=='']
    else: cand=cand[cand.qual=='']
    sac=cand[cand.sa.fillna('').str.split(',').apply(lambda x: sa in x and sa!='')]
    cand=sac if len(sac) else cand[cand.sa.fillna('')=='']
    pd_=cand.iloc[0] if len(cand) else None
    if pd.isna(r.Density) and pd_ is None: continue
    iss=''
    if pd_ is None: iss='density in service, none in PDF'
    elif pd.isna(r.Density): iss='density in PDF, missing in service'
    elif pd_.density!=r.Density: iss='density value mismatch'
    elif unit(pd_.unit)!=unit(r.Unit) and not unit(pd_.unit).startswith(unit(r.Unit)): iss='unit mismatch'
    out.append(dict(ZONING_ID=r.ZONING_ID,Use_Type=ut,svc_density=r.Density,svc_unit=r.Unit,pdf_density=None if pd_ is None else pd_.density,pdf_unit=None if pd_ is None else pd_.unit,issue=iss))
M=pd.DataFrame(out); M.to_csv('out_pas_density_diff.csv',index=False)
print(M.issue.replace('','match').value_counts().to_string())
pd.set_option('display.width',250); pd.set_option('display.max_rows',100); pd.set_option('display.max_colwidth',70)
print(M[M.issue!=''].sort_values(['issue','ZONING_ID']).to_string(index=False))
