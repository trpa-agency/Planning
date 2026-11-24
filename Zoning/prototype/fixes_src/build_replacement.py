import sys,re,json; sys.path.insert(0,'src')
import pandas as pd
from plan_diff2 import expand, fold, U, svc_canon, key
FOOT={'TVAP':{'1':'Land use category is identified in TRPA Code Section 60.3 as a “possible contaminating activity,” triggering special requirements pursuant to TRPA Code Section 60.4 if located within Source Water Protection Zone (see Figure 9).',
 '2':'Condominiums only. Refer to multiple family dwelling density standards.','3':'As part of a mixed-use project only.','4':'Limited to existing warehouse uses within the Town Center Gateway District (TC-G).',
 '5':'New non-emergency sites prohibited.','6':'Facilities with the capacity for 200 or more persons require a special use permit.'},
 'TCAP':{'1':'Caretaker Residence Only.','2':'All Health Care Services are allowed except emergency outpatient or urgent care facilities and shall not front Lake Tahoe Boulevard.',
 '3':'Allow Realty Offices within the district and limit financial services to ATMs.','4':'Allow consideration for placement of Realty Offices within the district, and only when operated in conjunction with approved Park Avenue Redevelopment fractional ownership tourist accommodation projects. Such use shall occupy no more than five percent (5%) of the commercial floor area with any project area within the district.',
 '5':'All Health Care Services uses permissible throughout special district; provided that any Health Care Services uses proposed to front on either side of US Highway 50 and/or the intersections of Heavenly Village Way (formerly Park Avenue) and Stateline Avenue are limited to second floor or higher. See TRPA Ordinance 2009-05 Exhibit 2 for specific limitation locations.',
 '6':'Outdoor storage and display is prohibited.','7':'Shall not front on US Highway 50.','8':'Condominiums only.','9':'Use not permitted in TSC-MUC Special Area #1. Daycare center allowed as an accessory use.','10':'Daycare center allowed as an accessory use.',
 '11':'Land use category is identified in TRPA Code Section 60.3 as a “possible contaminating activity.” Triggering special requirements pursuant to TRPA Code Section 60.4 if located within a Source Water Protection Zone.',
 '12':'Use only allowed in connection with a retail commercial use where it will enhance the visitor experience and is limited in size to 30% of the associated retail space.','13':'Facilities with the capacity for 200 or more persons require a special use permit.',
 '14':'Only deed restricted Multi-family dwelling units or multi-person dwelling units owned and maintained by public or private entities for purposes of housing employees.','15':'Condominiums only.'}}
HEAD={'RESIDENTIAL':('Residential','Residential'),'TOURIST ACCOMMODATION':('Tourist Accommodation','Tourist Accommodation'),'RETAIL COMMERCIAL':('Commercial','Retail'),
 'ENTERTAIMENT COMMERCIAL':('Commercial','Entertainment'),'ENTERTAINMENT':('Commercial','Entertainment'),'SERVICE COMMERCIAL':('Commercial','Services'),
 'LIGHT INDUSTRIAL COMMERCIAL':('Commercial','Light Industrial'),'LIGHT INDUSTRIAL':('Commercial','Light Industrial'),'WHOLESALE/STORAGE COMMERCIAL':('Commercial','Wholesale/Storage'),'WHOLESALE/STORAGE':('Commercial','Wholesale/Storage'),
 'GENERAL PUBLIC SERVICE':('Public Services','General'),'LINEAR PUBLIC FACILITIES':('Public Services','Linear Public Facilities'),'RECREATION':('Recreation','Recreation'),'OPEN SPACE':('Resource Management','Open Space'),'RESOURCE MANAGEMENT':('Resource Management',None)}
RMSUB=[('Forest','Timber Management'),('Tree Farm','Timber Management'),('Vegetation','Vegetation Protection'),('Water Quality','Watershed Improvements'),('Wildlife','Wildlife And Fishes'),('Range','Range')]
RETAIL={'General Retail and Personal Services','Building Materials and Hardware','Nursery','Outdoor Retail Sales','Eating and Drinking Places','Service Stations','Auto, Mobile Home and Vehicle Dealers'}
def use_name(label):
    lab=re.sub(r'\s*\(includes condominiums\)','',label,flags=re.I).strip()
    c=expand(fold(lab))
    if len(c)==1 and c[0]: return c[0]
    return re.sub(r'\s+',' ',lab.replace(' & ',' and ').replace('&','and')).replace(', and ',', and ').strip()
def build(plan,f):
    P=pd.read_csv(f,dtype=str,keep_default_na=False,na_values=[''])
    P=P[P.raw.fillna('').str.match(r'^(A|S)')]
    rows=[]
    for r in P.itertuples():
        st='Allowed' if r.raw.startswith('A') else 'Special Use'
        feet=re.findall(r'\d+',r.raw[1:]); lab_feet=re.findall(r'(?<=[a-z\)])(\d+)$',r.label)
        if plan=='TCAP' and r.zone=='TCAP_TSC_MUC_SA1' and '9' in feet: continue
        u=use_name(r.label); cat,sub=HEAD.get((r.heading or '').strip(),(None,None))
        if u in RETAIL and plan=='TCAP' and cat=='Tourist Accommodation': cat,sub='Commercial','Retail'
        if cat=='Resource Management' and sub is None: sub=next((s for k,s in RMSUB if k in u),None)
        rows.append(dict(Zoning_ID=r.zone,Category=cat,Subcategory=sub,Use_Type=u,Use_Status=st,feet=feet,pdf_label=r.label,pdf_cell=r.raw,page=r.page))
    R=pd.DataFrame(rows); R['Use_Type']=R.Use_Type.replace({'Water Quality Improvements and Watershed':'Water Quality Improvements and Watershed Management'}); R=R.drop_duplicates(['Zoning_ID','Use_Type'])
    # carry density, unit, and notes from the current service row for the same use where one exists
    S=U[U.Zoning_ID.isin(R.Zoning_ID.unique())].copy(); S['k']=S.ut.map(lambda x: key(svc_canon(x) or ''))
    R['k']=R.Use_Type.map(key)
    S=S.drop_duplicates(['Zoning_ID','k'])
    R=R.merge(S[['Zoning_ID','k','Density','Unit','Notes','ut']].rename(columns={'ut':'service_use_type'}),on=['Zoning_ID','k'],how='left')
    def notes(r):
        fn=[FOOT[plan][x] for x in r.feet if x in FOOT[plan]]
        old=r.Notes if isinstance(r.Notes,str) and r.Notes not in ('NA','') else ''
        parts=list(dict.fromkeys([p for p in [old]+fn if p]))
        return ' '.join(parts) if parts else 'NA'
    R['Notes']=R.apply(notes,axis=1); R['Unit']=R.Unit.fillna('NA'); R['Density']=pd.to_numeric(R.Density).astype('Int64')
    R['carried_from_service']=R.service_use_type.notna()
    assert R.Category.notna().all(), R[R.Category.isna()]
    return R.drop(columns=['k','feet'])
out=[]
for plan,f in [('TVAP','tvap_pdf_rows.csv'),('TCAP','tcap_pdf_rows.csv')]:
    R=build(plan,f); R['plan']=plan; out.append(R)
    print(plan,len(R),R.groupby('Zoning_ID').size().to_dict(),'| carried',int(R.carried_from_service.sum()))
R=pd.concat(out); R.to_csv('replacement_tvap_tcap.csv',index=False)
print(R.Use_Type.nunique()); print(sorted(R.Use_Type.unique()))
