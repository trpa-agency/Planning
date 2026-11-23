"""Build fixes for the area plans and community plans from the verified comparison (out_area_plan_diff_all.csv)
and the Tahoe Valley and Tourist Core replacement sets (replacement_tvap_tcap.csv). Run from the repo root."""
import json, re, pandas as pd
R='data/raw/'; O='outputs/'
U=pd.DataFrame(json.load(open(R+'permissible_use.json'))).set_index('OBJECTID',drop=False)
D=pd.DataFrame(json.load(open(R+'district_attr.json')))
A=pd.read_csv(R+'area/out_area_plan_diff_all.csv',dtype={'ZONING_ID':str,'OBJECTID':'Int64'},keep_default_na=False,na_values=[''])
A=A[A.issue.notna()&(A.issue!='')].copy()
DOC={'WCTAP':'Washoe County Development Code Article 220, Tahoe Area (Dec 17, 2025), page','PCAP':'Placer County Tahoe Basin Area Plan Implementing Regulations (Feb 2021), page',
     'MAP':'Meyers Area Plan Table 2-1 (March 2018), page','071':'Round Hill Community Plan (Nov 1993), Chapter II','098':'Bijou/Al Tahoe Community Plan matrix (Oct 1995), page','113':'South Y Industrial Tract Community Plan (March 2003), page'}
# rows checked by hand against the document and found to be parser artifacts (service is right)
ARTIFACT={('046','Nonstructural Fish Habitat Management'),('046','Nonstructural Wildlife Habitat Management'),('046','Structural Fish Habitat Management'),('046','Structural Wildlife Habitat Management'),
 ('048','Nonstructural Wildlife Habitat Management'),('048','Multiple Family Dwelling'),('054_SA1','Hotel, Motel, and Other Transient Dwelling Units'),
 ('PCAP_MU_CCW','Hotel, Motel, and Other Transient Dwelling Units'),('PCAP_MU_GW','Hotel, Motel, and Other Transient Dwelling Units'),('PCAP_MU_NC','Hotel, Motel, and Other Transient Dwelling Units'),
 ('PCAP_RES_TAHOEPINES','Professional Offices'),('113','Schools - Business and Vocational')}
RULING={('PCAP_COM/PS_KINGS','Single Family Dwelling'):'R11',
 **{(z,u):'R12' for z in ['PCAP_MU_R','PCAP_MU_TOR','PCAP_MU_WREC'] for u in ['Nonstructural Fish Habitat Management','Structural Fish Habitat Management']},
 ('113','Allowed in all Areas of the Region'):'R13'}
upd=[]; dele=[]; ins=[]; pend=[]
conv={}
J=U.merge(D[['ZONING_ID','PLAN_ID']],left_on='Zoning_ID',right_on='ZONING_ID',how='left')
for (p,u),g in J.groupby(['PLAN_ID','Use_Type']): conv[(p,u)]=g.groupby(['Category','Subcategory']).size().idxmax()
for u,g in J.groupby('Use_Type'): conv[(None,u)]=g.groupby(['Category','Subcategory']).size().idxmax()
for r in A.itertuples():
    k=(r.ZONING_ID,r.use); src=DOC[r.plan]+(f' {int(float(r.page))}' if isinstance(r.page,(str,float)) and str(r.page) not in ('nan','') and r.plan!='071' else '')
    if k in ARTIFACT: continue
    if k in RULING: pend.append(dict(FIX_ID=RULING[k],TABLE='PermissibleUses',ACTION='review',OBJECTID=r.OBJECTID,GlobalID=r.GlobalID,Zoning_ID=r.ZONING_ID,FIELD='Use_Type',OLD_VALUE=r.ut,NEW_VALUE=r.use,SOURCE=src,
        QUESTION={'R11':'Code lists single family dwellings only as accessory to a commercial use, with no permit code. Keep as Allowed with a note, or remove?',
                  'R12':'North Tahoe East table lists wildlife habitat management but no fish habitat rows. Plan omission, or delete the service rows?',
                  'R13':'Open space line "Allowed in all areas of the region" has no status code. Add it as Allowed, as the service does for other plans?'}[RULING[k]])); continue
    if r.issue=='status mismatch':
        new=r.pdf_status.split('/')[0]
        if r.ZONING_ID=='032B': pass
        upd.append(dict(FIX_ID='A01',TABLE='PermissibleUses',OBJECTID=int(r.OBJECTID),GlobalID=r.GlobalID,Zoning_ID=r.ZONING_ID,Use_Type=r.ut,FIELD='Use_Status',OLD_VALUE=r.Use_Status,NEW_VALUE=new,
            CONFIDENCE='Certain',SOURCE=src,REASON=f'Document lists this use as {r.pdf_raw}'))
    elif r.issue in ('in service, not in PDF','in service, PDF says not permitted'):
        dele.append(dict(FIX_ID='A02',TABLE='PermissibleUses',OBJECTID=int(r.OBJECTID),GlobalID=r.GlobalID,Zoning_ID=r.ZONING_ID,Use_Type=r.ut,CONFIDENCE='Certain',SOURCE=DOC[r.plan],
            REASON='Use is not in this district\'s list in the document' if r.issue=='in service, not in PDF' else 'Document marks this use as not permitted in this district'))
    elif r.issue=='missing from service':
        st=r.pdf_status.split('/')
        status='Allowed' if 'Allowed' in st else st[0]
        note='NA'
        if r.ZONING_ID=='032B' and r.use=='Multiple Family Dwelling': note='Four units or less: Allowed. More than four units: Administrative Review, processed as a TRPA special use (Washoe Code 110.220.130).'
        cat,sub=conv.get((r.plan,r.use)) or conv.get((None,r.use)) or (None,None)
        fix='A04' if r.ZONING_ID in ('032B','035_SA1','055','056') else 'A03'
        ins.append(dict(FIX_ID=fix,Zoning_ID=r.ZONING_ID,Category=cat,Subcategory=sub,Use_Type=r.use,Use_Status=status,Density=None,Unit='NA',Notes=note,CONFIDENCE='Certain',SOURCE=src,
            REASON='District has no rows in the service; full list from the document' if fix=='A04' else 'Document lists this use; service has no row'))
# service rows whose status is "See note" where the document gives an explicit status keep their note
for u in upd:
    if u['OLD_VALUE']=='See note': u['REASON']+='. Existing note is kept.'
# ---- Tahoe Valley and Tourist Core: replace all rows from the December 2024 tables
RP=pd.read_csv(R+'area/replacement_tvap_tcap.csv',dtype={'Zoning_ID':str},keep_default_na=False,na_values=[''])
zones=sorted(RP.Zoning_ID.unique())
old=U[U.Zoning_ID.isin(zones)]
for r in old.itertuples(): dele.append(dict(FIX_ID='A05',TABLE='PermissibleUses',OBJECTID=r.OBJECTID,GlobalID=r.GlobalID,Zoning_ID=r.Zoning_ID,Use_Type=r.Use_Type,CONFIDENCE='Certain',
    SOURCE='Tahoe Valley Area Plan Table 1 (amended Dec 18, 2024) or Tourist Core Area Plan Table 1 (Dec 2024)',REASON='Replaced by the full 2024 table (A06)'))
orph=U[U.Zoning_ID.isna()]
for r in orph.itertuples():
    if r.OBJECTID==12762: continue   # already deleted by F22
    dele.append(dict(FIX_ID='A05',TABLE='PermissibleUses',OBJECTID=r.OBJECTID,GlobalID=r.GlobalID,Zoning_ID=None,Use_Type=r.Use_Type,CONFIDENCE='Likely',
        SOURCE='Table integrity',REASON='Orphan Tahoe Valley and Tourist Core template row with no Zoning_ID; superseded by A06 (was R04)'))
src_doc={'TVAP':'Tahoe Valley Area Plan Table 1 (amended Dec 18, 2024), page','TCAP':'Tourist Core Area Plan Table 1 (Dec 2024), page'}
for r in RP.itertuples():
    ins.append(dict(FIX_ID='A06',Zoning_ID=r.Zoning_ID,Category=r.Category,Subcategory=r.Subcategory,Use_Type=r.Use_Type,Use_Status=r.Use_Status,
        Density=None if pd.isna(r.Density) else int(r.Density),Unit=r.Unit,Notes=r.Notes,CONFIDENCE='Certain',SOURCE=f'{src_doc[r.plan]} {r.page}',
        REASON=f'PDF cell {r.pdf_cell}'+(f'; density, unit, and notes carried from the current service row ({r.service_use_type})' if r.carried_from_service else '')))
# ---- decisions specific to area and community plans
for fid,item,q in [('R14','Tahoe Valley Table 1','The 2024 table has no Religious Assembly row (the old rows allowed it in 7 districts). Employee housing and personal services are folded into Multiple Family Dwelling, Multi-Person Dwelling, and General Retail and Personal Services by the 2024 definitions. Confirm religious assembly was meant to drop before A05 and A06 are posted.'),
                   ('R15','South Shore Area Plan (SSAP_ districts)','Uses are set by Douglas County Development Code Chapter 20.703, which is not linked. Supply the adopted chapter so the 179 SSAP rows can be checked.'),
                   ('R16','PCAP_REC_HOMEWOOD','Uses are set by the Homewood Mountain Resort Master Plan, which is not linked. The district has no rows.'),
                   ('R17','PCAP_RES_CEDAR_SA1','Special Area 1 follows Cedar Flat only if the TRPA Ordinance 95-4 findings were made; otherwise Watson Creek applies. Rows were built as Cedar Flat.'),
                   ('R18','055 and 056','Washoe Code tables exist for East Shore and Marlette Lake, but both districts extend about 42 percent into Carson City. A04 inserts apply the Washoe list to the whole polygon.')]:
    pend.append(dict(FIX_ID=fid,TABLE='PermissibleUses',ACTION='decide',Zoning_ID=item,QUESTION=q))
up=pd.DataFrame(upd); de=pd.DataFrame(dele); ins_=pd.DataFrame(ins); pe=pd.DataFrame(pend)
ins_['Density']=ins_.Density.astype('Int64')
assert ins_.Category.notna().all(), ins_[ins_.Category.isna()]
assert not de.OBJECTID.duplicated().any()
up.to_csv(O+'area_pu_updates.csv',index=False); de.to_csv(O+'area_pu_deletes.csv',index=False); ins_.to_csv(O+'area_pu_inserts.csv',index=False); pe.to_csv(O+'area_pending_rulings.csv',index=False)
for n,d in [('updates',up),('deletes',de),('inserts',ins_),('pending',pe)]: print(n,len(d),d.FIX_ID.value_counts().sort_index().to_dict())
