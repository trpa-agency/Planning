import sys,re,json; sys.path.insert(0,'src')
import pas_parse as pp, pandas as pd
from plan_diff2 import compare
L=pp.clean_lines(open('txt/071.txt',errors='ignore').read())
pg=[]; n=0
for i,page in enumerate(open('txt/071.txt',errors='ignore').read().split('\f'),1): pass
L=[re.sub(r'^\s*θ\s*','     ',l) for l in L]
perm=pp.section(L,r'^\s*PERMISSIBLE USES\s*:',r'^\s*MAXIMUM DENSITIES')
blk={}; cur=None
for l in perm:
    s=l.strip(); m=re.match(r'Special Area\s*#?\s*(\d+)\s*(\([^)]*\))?\s*[:.]',s)
    if m: cur=f'071_SA{m.group(1)}'; blk[cur]=[]; continue
    if cur: blk[cur].append(l)
rows=[]
for z,lines in blk.items():
    for cat,txt in pp.cat_text(lines):
        if 'same as special area #1' in txt.lower():
            rows+= [dict(r,zone=z,basis='same as Special Area #1') for r in rows if r['zone']=='071_SA1' and r['category']==cat]; continue
        txt=re.sub(r'\b[A-F]\.\s+(Retail|Entertainment|Services|Light Industrial|Wholesale/Storage|General|Linear Public Facilities|Timber Management|Wildlife and Fishes|Open Space|Vegetation Protection|Watershed Improvements|Range)\s+',' ',txt)
        txt=re.sub(r'Round Hill Community Plan\s+\w+, \d{4}\s+CHAPTER II . LAND USE ELEMENT\s+II-\d+','',txt).replace('§','')
        txt=re.sub(r'(Allowed in all areas of the region)\.',r'\1 (A),',txt,flags=re.I)
        its,tail=pp.items(txt)
        for name,st in its: rows.append(dict(page=None,zone=z,category=cat,label=re.sub(r'\s*\(nevada only\)','',name,flags=re.I),raw=st,basis='listed'))
P=pd.DataFrame(rows); P['page']=P.label.map(lambda x: None); P.to_csv('071_pdf_rows.csv',index=False)
M,un=compare(P,['071_SA1','071_SA2'],{'A':'Allowed','S':'Special Use'},plan='071'); M.to_csv('out_071_diff.csv',index=False)
print(P.groupby('zone').size().to_dict(),'unmatched',un); print(M.issue.replace('','match').value_counts().to_string())
x=M[M.issue!='']; print(x[['ZONING_ID','use','issue','pdf_raw','Use_Status']].to_string(index=False))
