import sys, json, re, pandas as pd
sys.path.insert(0,'src'); from normalize import canon, key, ALIAS
U=pd.DataFrame(json.load(open('raw/permissible_use.json')))
U['ut']=U.Use_Type.fillna('').str.replace(r'\s+',' ',regex=True).str.strip()
VOC={}
for v in U.ut[U.ut!=''].value_counts().index: VOC.setdefault(key(v),v)
EXTRA={'church':'Religious Assembly','churche':'Religious Assembly','fuels treatment':'Fuels Treatment Management','fuels treatment management':'Fuels Treatment Management',
 'stream environment zone restoration':'Stream Environmental Zone (SEZ) Restoration','sez restoration':'Stream Environmental Zone (SEZ) Restoration',
 'recreational center':'Recreation Centers','visitor information center':'Visitor Information Centers','fuel and ice dealer':'Fuel and Ice Dealers',
 'day care center preschool':'Day Care Centers/Pre-Schools','day care center pre school':'Day Care Centers/Pre-Schools','daycare center preschool':'Day Care Centers/Pre-Schools',
 'hotel motel other transient dwelling unit':'Hotel, Motel, and Other Transient Dwelling Units','hotel motel and other transient dwelling unit':'Hotel, Motel, and Other Transient Dwelling Units',
 'hotel motel and other transient dwelling':'Hotel, Motel, and Other Transient Dwelling Units','hotel motel other transient dwelling':'Hotel, Motel, and Other Transient Dwelling Units',
 'time sharing hotel motel design':'Time Sharing (Hotel/Motel Design)','timesharing hotel motel design':'Time Sharing (Hotel/Motel Design)',
 'time sharing residential design':'Time Sharing (Residential Design)','timesharing residential design':'Time Sharing (Residential Design)',
 'local post office':'Local Post Office','post office':'Local Post Office','school kindergarten through secondary':'Schools - Kindergarten Through Secondary',
 'school college':'Schools - College','school business and vocational':'Schools - Business and Vocational','single family dwelling':'Single Family Dwelling',
 'multiple family dwelling':'Multiple Family Dwelling','multiple family dwellings':'Multiple Family Dwelling','multi person dwelling':'Multi-Person Dwelling','multiple person dwelling':'Multi-Person Dwelling',
 'participant sport facilitie':'Participant Sports Facilities','sales lot':'Sales Lots','nursery':'Nursery','service station':'Service Stations',
 'animal husbandry':'Animal Husbandry Services','range pasture management':'Range Pasture Management','ranch pasture management':'Range Pasture Management',
 'public assembly and entertainment facilitie':'Publicly Owned Assembly and Entertainment','food and beverage sale':'Food and Beverage Retail Sales','food and beverage retail sale':'Food and Beverage Retail Sales',
 'riding and hiking trail':'Riding and Hiking Trails','cross country skiing course':'Cross Country Ski Courses','early successional stage vegetation management':'Early Successional Vegetation Management'}
def k3(s):
    s=re.sub(r'\(section [^)]*\)|\(see [^)]*\)|\(nevada only\)|\*+|§','',s,flags=re.I)
    s=s.replace('–','-').replace('—','-'); return key(s)
def expand(label, alias={}):
    lab=alias.get(label,label)
    if isinstance(lab,list): return lab
    k=k3(lab)
    if k in MULTI: return MULTI[k]
    if k in EXTRA: return [EXTRA[k]]
    c=canon(lab,VOC)
    if c!=[None]: return c
    c=canon(re.sub(r'\(.*?\)','',lab),VOC)
    return c if c!=[None] else [None]
KIT=re.compile(r'\s*[\(\-–]*\s*(less than 10%|10%\s*\d*\s*or more)[^)]*\)?\s*$',re.I)
def fold(u): return KIT.sub('',u).strip() if isinstance(u,str) else u
EXTRA.update({'gaming non restricted':'Gaming - Nonrestricted (Nevada Only)','gaming nonrestricted':'Gaming - Nonrestricted (Nevada Only)','general merchandising store':'General Merchandise Stores',
 'local public and safety facilitie':'Local Public Health and Safety Facilities','fuels management treatment':'Fuels Treatment Management','timeshare hotel motel design':'Time Sharing (Hotel/Motel Design)',
 'timeshare residential design':'Time Sharing (Residential Design)','raising domestic animal':'Domestic Animal Raising','fuel management treatment':'Fuels Treatment Management','sports assembly':'Sport Assembly','fuel treatment management':'Fuels Treatment Management','fuel treatment':'Fuels Treatment Management',
 'amusement and recreation':'Amusements and Recreation Services','business support':'Business Support Services','contract construction':'Contract Construction Services',
 'local assembly and':'Local Assembly and Entertainment','privately owned assembly and':'Privately Owned Assembly and Entertainment','publicly owned assembly and':'Publicly Owned Assembly and Entertainment',
 'nonstructural fish habitat':'Nonstructural Fish Habitat Management','nonstructural wildlife habitat':'Nonstructural Wildlife Habitat Management','structural fish habitat':'Structural Fish Habitat Management',
 'structural wildlife habitat':'Structural Wildlife Habitat Management','sensitive plant':'Sensitive Plant Management','uncommon plant community':'Uncommon Plant Community Management',
 'uncommon plant management':'Uncommon Plant Community Management','early successional stage vegetation':'Early Successional Vegetation Management','early successional state vegetation management':'Early Successional Vegetation Management',
 'cross county skiing course':'Cross Country Ski Courses','downhill skiing facilitie':'Downhill Ski Facilities','tire sharing hotel motel design':'Time Sharing (Hotel/Motel Design)',
 'threshold related facilitie':'Threshold-Related Research Facilities','pipeline and power transmission facilitie':'Pipelines and Power Transmission','light industrial batch plant':'Batch Plants',
 'regional local public health and safety facilitie':'Regional Public Health and Safety Facilities','old tahoe pine post office':'Professional Offices'})
MULTI={'general merchandise store mail order and vending':['General Merchandise Stores','Mail Order and Vending'],
 'multiple family dwelling multi person dwelling and employee housing':['Multiple Family Dwelling','Multi-Person Dwelling','Employee Housing'],
 'school pre through secondary':['Schools - Pre-Schools','Schools - Kindergarten Through Secondary'],
 'structural and nonstructural fish wildlife habitat':['Structural Fish Habitat Management','Nonstructural Fish Habitat Management','Structural Wildlife Habitat Management','Nonstructural Wildlife Habitat Management'],
 'sensitive and uncommon plant':['Sensitive Plant Management','Uncommon Plant Community Management']}
def svc_canon(ut):
    if not ut: return None
    c=expand(fold(ut)); return fold(c[0] if c[0] else ut)
STATUS={'A':'Allowed','S':'Special Use','P':'Allowed','CUP':'Conditional Use','MUP':'Minor Use','AR':'Administrative Review','C':'Administrative Review','TRPA-A':'Allowed','Allowed':'Allowed','Special Use':'Special Use'}
def compare(P, zones, status_map=STATUS, alias={}, plan=''):
    """P: DataFrame with zone,label,raw,page (+optional). Rows with raw not in status_map = not permitted."""
    E=[]; un=set()
    P=P[P.label.notna()&(P.label.astype(str).str.strip()!='')]
    for r in P.itertuples():
        m_=re.match(r'^(TRPA-A|Special Use|Allowed|CUP|MUP|AR|A|S|C|P)',str(r.raw).replace('Al','A1',1) if re.match(r'^Al(/\d+)?$',str(r.raw)) else str(r.raw)) if isinstance(r.raw,str) else None
        st=status_map.get(m_.group(1)) if m_ else None
        for u in [fold(x) if x else x for x in expand(fold(r.label),alias)]:
            if u is None: un.add(r.label); continue
            E.append(dict(ZONING_ID=r.zone,use=u,pdf_label=r.label,pdf_raw=r.raw,pdf_status=st,page=r.page))
    E=pd.DataFrame(E)
    perm=E[E.pdf_status.notna()].groupby(['ZONING_ID','use'],as_index=False).agg(pdf_label=('pdf_label','first'),pdf_raw=('pdf_raw',lambda s:'/'.join(dict.fromkeys(s))),
        pdf_status=('pdf_status',lambda s:'/'.join(dict.fromkeys(s))),page=('page','first')); notp=E[E.pdf_status.isna()][['ZONING_ID','use']].drop_duplicates().assign(pdf_dash=True)
    S=U[U.Zoning_ID.isin(zones)].copy(); S['use']=S.ut.map(svc_canon)
    S=S.drop_duplicates(['Zoning_ID','use'])
    S=S[['Zoning_ID','use','ut','Use_Status','OBJECTID','GlobalID','Category','Subcategory','Density','Unit','Notes']].rename(columns={'Zoning_ID':'ZONING_ID'})
    M=perm.merge(S,on=['ZONING_ID','use'],how='outer',indicator=True).merge(notp,on=['ZONING_ID','use'],how='left')
    M['issue']=M._merge.astype(str).map({'left_only':'missing from service','right_only':'in service, not in PDF','both':''})
    ok=M.apply(lambda r: isinstance(r.pdf_status,str) and isinstance(r.Use_Status,str) and r.Use_Status in r.pdf_status.split('/'),axis=1)
    M.loc[(M._merge=='both')&~ok,'issue']='status mismatch'
    M.loc[(M.issue=='in service, not in PDF')&(M.pdf_dash==True),'issue']='in service, PDF says not permitted'
    M['plan']=plan
    return M.drop(columns=['_merge']), sorted(un)
