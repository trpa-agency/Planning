import sys,re,json; sys.path.insert(0,'src'); from list_parse import parse; from plan_diff import compare
import pandas as pd
D=pd.DataFrame(json.load(open('raw/district_attr.json')))
W=D[D.PLAN_ID=='WCTAP']
nm=lambda s: re.sub(r'[^a-z0-9]','',s.lower().replace('#',''))
base={nm(r.ZONING_DESCRIPTION):r.ZONING_ID for r in W.itertuples() if '_SA' not in r.ZONING_ID}
t=open('txt/WCTAP.txt',errors='ignore').read()
HD=re.compile(r'^\s*(?:PERMISSIBLE USES\s*[–-]\s*)?([A-Z0-9 .]+?) REGULATORY ZONE(\s+SPECIAL(\s+AREA)?\s*#?\s*(\d)?)?\s*$')
state={'z':None}
def zs(l):
    m=HD.match(l)
    if not m: return None
    b=base[nm(m.group(1))]
    if m.group(2): return f'{b}_SA{m.group(4) or 1}'
    return b
stop=lambda l: re.search(r'Section 110\.220\.\d+ .* Special Policies',l) is not None
from plan_diff2 import expand, fold
is_use=lambda l: expand(fold(l))!=[None]
rows=parse(t,zs,None,stop,is_use=is_use)
R=pd.DataFrame(rows); R=R[~R.category.fillna('').str.contains('Shorezone|Tolerance',case=False)]
out=[]
Rb=R[R.raw.isin(['SAME','ASABOVE'])==False]
for r_ in Rb.itertuples(): out.append(dict(page=r_.page,label=r_.label,zone=r_.zone,raw=r_.raw,category=r_.category,foot=r_.foot,basis='listed'))
for r_ in R[R.raw=='SAME'].itertuples():
    b=r_.zone.split('_SA')[0]
    for x in Rb[(Rb.zone==b)&(Rb.category==r_.category)].itertuples(): out.append(dict(page=x.page,label=x.label,zone=r_.zone,raw=x.raw,category=x.category,foot=x.foot,basis='same as general list'))
for r_ in R[R.raw=='ASABOVE'].itertuples():
    b=r_.zone.split('_SA')[0]; x=Rb[(Rb.zone==b)&(Rb.label.str.lower()==r_.label.lower())]
    for x in x.itertuples(): out.append(dict(page=x.page,label=x.label,zone=r_.zone,raw=x.raw,category=x.category,foot=x.foot,basis='as above'))
    if not len(x): print('ASABOVE not found',r_.zone,r_.label)
# 048 residential and tourist rows: labels wrap three levels deep; read by hand from code page 220-37 and 220-38
MAN=[('Employee Housing','S'),('Multiple Family Dwelling (more than four units) Within the Town Center','AR'),('Multiple Family Dwelling (four units or less) Within the Town Center','A'),
 ('Multi-Person Dwelling','S'),('Nursing and Personal Care','S'),('Residential Care','S'),('Single Family Dwelling','A'),('Bed and Breakfast Facilities','A'),
 ('Hotel, Motel, and Other Transient Dwelling Units','A'),('Time Sharing (Residential Design)','S'),('Time Sharing (Hotel/Motel Design)','S')]
pg=int(R[R.zone=='048'].page.min())
out=[o for o in out if not (o['zone'] in ('048','048_SA1') and o['category'] in ('Residential','Tourist Accommodation') and o['basis']=='listed' and o['zone']=='048')]
out+=[dict(page=pg,label=l,zone='048',raw=s_,category='Residential' if i<7 else 'Tourist Accommodation',foot='',basis='read by hand') for i,(l,s_) in enumerate(MAN)]
P=pd.DataFrame(out).drop_duplicates(['zone','label']); P.to_csv('wctap_pdf_rows.csv',index=False)
zones=sorted(set(P.zone)); print('zones parsed',len(zones),'| missing',sorted(set(W.ZONING_ID)-set(zones)))
print(P.groupby('zone').size().to_dict())
