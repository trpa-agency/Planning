import sys,re,json; sys.path.insert(0,'src')
import pandas as pd
from matrix_parse import parse
from plan_diff2 import expand, fold, compare
is_use=lambda l: bool(l) and expand(fold(l))!=[None]
HEAD=r'^(Residential|Tourist Accommodation|Commercial(\s*\([^)]*\))?|Public Services?(\s*\([^)]*\))?|Recreation|Resource Management|Open Space|RETAIL COMMERCIAL|ENTERTAINMENT COMMERCIAL|SERVICE COMMERCIAL|LIGHT INDUSTRIAL COMMERCIAL|WHOLESALE/STORAGE COMMERCIAL|GENERAL PUBLIC SERVICE|LINEAR PUBLIC FACILITIES|RESOURCE MANAGEMENT|OPEN SPACE|TOURIST ACCOMMODATION|RESIDENTIAL|RECREATION)\s+'
def clean(l):
    if is_use(l): return l
    m=re.match(HEAD,l)
    if m and is_use(l[m.end():]): return l[m.end():]
    return l
def run(pdf,pages,cols,lx,stop_label=None):
    rows=parse(pdf,pages,cols,lx)
    out=[]
    for r in rows:
        if stop_label and re.search(stop_label,r['label']): break
        r['label']=clean(r['label']); out.append(r)
    return pd.DataFrame(out)
if __name__=='__main__':
    D=pd.DataFrame(json.load(open('raw/district_attr.json')))
    jobs={
     'TVAP':('pdfs/110.pdf',[189,190,191],[('TVAP_TC_C',290),('TVAP_TC_MUC',321),('TVAP_TC_G',352),('TVAP_TC_NP',384),('TVAP_TC_HC',416),('TVAP_EB_CC',446),('TVAP_CMX_S',481),('TVAP_TC_OS',514)],280,None,{'A':'Allowed','S':'Special Use'}),
     'TCAP':('pdfs/TCAP.pdf',[180,181,182],[('TCAP_TSC_C',248),('TCAP_TSC_MU',280),('TCAP_TSC_MUC',320),('TCAP_TSC_NMX',352),('TCAP_TSC_G',384),('TCAP_TSC_G_SA1',424),('TCAP_REC_TOURIST',464),('TCAP_OS',500)],235,r'SHOREZONE|Tolerance District',{'A':'Allowed','S':'Special Use'}),
     'MAP':('pdfs/MAP.pdf',[25,26,27],[('MAP_1',280),('MAP_2',336),('MAP_3',396),('MAP_4',452),('MAP_5',512)],255,None,{'P':'Allowed','CUP':'Conditional Use'})}
    for plan,(pdf,pages,cols,lx,stop,st) in jobs.items():
        P=run(pdf,pages,cols,lx,stop)
        if plan=='TCAP':   # one column covers TSC-MUC and TSC-MUC Special Area #1
            P=pd.concat([P,P[P.zone=='TCAP_TSC_MUC'].assign(zone='TCAP_TSC_MUC_SA1')])
        P.to_csv(f'{plan.lower()}_pdf_rows.csv',index=False)
        Z=[c for c,_ in cols]+(['TCAP_TSC_MUC_SA1'] if plan=='TCAP' else [])
        M,un=compare(P,Z,st,plan=plan); M.to_csv(f'out_{plan.lower()}_diff.csv',index=False)
        print(f'\n##### {plan} rows {len(P)} unmatched:',un); print(M.issue.replace('','match').value_counts().to_string())
