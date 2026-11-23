"""Build Permissible Use and Special Designation fix rows from the verified QA findings.
Run from the repo root. Reads the service snapshot in data/raw and writes outputs/*.csv.
Every row carries FIX_ID, CONFIDENCE, SOURCE (PDF and page), and REASON."""
import json, pandas as pd
from pathlib import Path
R=Path('data/raw'); O=Path('outputs')
U=pd.DataFrame(json.load(open(R/'permissible_use.json'))); S=pd.DataFrame(json.load(open(R/'special_designation.json')))
U=U.set_index('OBJECTID',drop=False); S=S.set_index('OBJECTID',drop=False)
PU_FIELDS=['Zoning_ID','Category','Subcategory','Use_Type','Use_Status','Density','Unit','Notes']
PDF=lambda pid,pg: f'PAS {pid} PDF p{pg} (trpa.gov/wp-content/uploads/documents/archive/2/{pid}.pdf)'
upd=[]; dele=[]; ins=[]; pend=[]
def U_(fix,oid,field,new,src,why,conf='Certain'):
    old=U.loc[oid,field]; assert not (pd.isna(old) and pd.isna(new)) and old!=new, (fix,oid,field,old,new)
    upd.append(dict(FIX_ID=fix,TABLE='PermissibleUses',OBJECTID=oid,GlobalID=U.loc[oid,'GlobalID'],Zoning_ID=U.loc[oid,'Zoning_ID'],
        Use_Type=U.loc[oid,'Use_Type'],FIELD=field,OLD_VALUE=old,NEW_VALUE=new,CONFIDENCE=conf,SOURCE=src,REASON=why))
def D_(fix,oid,src,why,conf='Certain',tbl='PermissibleUses'):
    T=U if tbl=='PermissibleUses' else S; r=T.loc[oid]
    dele.append(dict(FIX_ID=fix,TABLE=tbl,OBJECTID=oid,GlobalID=r.GlobalID,Zoning_ID=r.get('Zoning_ID',r.get('ZONING_ID')),
        Use_Type=r.get('Use_Type',r.get('SPECIAL_DESIGNATION')),CONFIDENCE=conf,SOURCE=src,REASON=why))
def I_(fix,z,cat,sub,use,st,src,why,den=None,unit='NA',notes='NA',conf='Certain'):
    ins.append(dict(FIX_ID=fix,Zoning_ID=z,Category=cat,Subcategory=sub,Use_Type=use,Use_Status=st,Density=den,Unit=unit,Notes=notes,
        CONFIDENCE=conf,SOURCE=src,REASON=why))
    assert not ((U.Zoning_ID==z)&(U.Use_Type==use)).any(), (z,use)
# ---- use status and name errors
U_('F01',3789,'Use_Status','Special Use',PDF('057',3),'PDF lists selection cut (S)')
U_('F01',3786,'Use_Status','Allowed',PDF('057',3),'PDF lists special cut (A)')
U_('F02',5437,'Use_Type','Fuels Treatment Management',PDF('058',2),'Glenbrook has no Special Area 1 use list; general list has fuels treatment/management (A). Row is mislabeled')
for oid,z,pid in [(740,'111_SA1','111'),(772,'111_SA2','111'),(649,'112','112'),(650,'112_SA1','112'),(651,'112_SA2','112')]:
    U_('F03',oid,'Use_Status','Allowed',PDF(pid,3 if pid=='111' else 2),'General list: schools - kindergarten through secondary (A); special areas add to the general list')
U_('F04',767,'Use_Status','Allowed',PDF('111',3),'Special Area 2 additions: multiple family dwellings (A)')
U_('F05',14031,'Use_Type','Multiple Family Dwelling',PDF('155',2),'Standard use name; row was entered as Multi-Family Dwelling')
U_('F05',14031,'Use_Status','Special Use',PDF('155',2),'PDF lists multiple family dwelling (S)')
# ---- densities
U_('F06',3566,'Density',15,PDF('099',3),'Multiple family dwellings 15 units per acre; values were swapped with multi-person')
U_('F06',3566,'Unit','units per acre',PDF('099',3),'Unit swapped with multi-person row')
U_('F06',3312,'Density',25,PDF('099',3),'Multi-person dwellings 25 people per acre; values were swapped with multiple family')
U_('F06',3312,'Unit','persons per acre',PDF('099',3),'Unit swapped with multiple family row')
for oid,pid in [(3313,'099'),(2376,'114')]:
    U_('F07',oid,'Density',10,PDF(pid,3),'Bed and breakfast facilities 10 units per acre')
    U_('F07',oid,'Unit','units per acre',PDF(pid,3),'Unit for the density above')
U_('F08',12748,'Density',15,PDF('116',3),'Employee housing 15 units per acre')
U_('F08',12748,'Unit','units per acre',PDF('116',3),'Unit for the density above')
U_('F09',804,'Density',None,PDF('114',3),'No density applies to public health and safety facilities; 8 units per acre belongs to Special Area 3 multiple family dwellings, which already carries it')
U_('F09',804,'Unit','NA',PDF('114',3),'Clear unit with the density')
for oid in [2163,10717]: U_('F10',oid,'Unit','unit per parcel',PDF('154',3),'Single family dwelling 1 unit per parcel')
for oid in [2195,2197]: U_('F11',oid,'Unit','persons per acre',PDF('155',3),'25 people per acre; stored as units per acre. Uses the table\'s standard spelling')
# ---- uses in service but not in PDF
D_('F12',3516,PDF('100',4),'Reforestation is not in the Truckee Marsh resource management list')
for oid in [2403,2404]: D_('F13',oid,PDF('111',3),'Nursing and personal care and residential care are Special Area 2 additions only')
for oid in [2976,2977]: D_('F14',oid,PDF('089','2-3'),'Special Area 1 has its own list (general list excluded) with no Commercial uses')
# ---- uses missing from service
TSN='Based on Hotel, Motel and Other Transient Dwelling Units use densities'
I_('F15','103','Tourist Accommodation','Tourist Accommodation','Time Sharing (Hotel/Motel Design) less than 10% of units with kitchens','Special Use',PDF('103','2-3'),'PDF lists timeshare (hotel/motel design) (S); density per the hotel limits, following the table\'s convention for 103 residential-design timeshare',40,'units per acre',TSN)
I_('F15','103','Tourist Accommodation','Tourist Accommodation','Time Sharing (Hotel/Motel Design) 10% or more units with kitchens','Special Use',PDF('103','2-3'),'Same as above',15,'units per acre',TSN)
for z in ['127','128']: I_('F16',z,'Public Services','Linear Public Facilities','Transmission and Receiving Facilities','Special Use',PDF(z,2),'PDF lists transmission and receiving facilities (S)')
I_('F17','146','Public Services','General','Cultural Facilities','Special Use',PDF('146',2),'PDF lists cultural facilities (S)')
for z in ['149','151']: I_('F18',z,'Resource Management','Timber Management','Thinning','Allowed',PDF(z,2),'PDF lists thinning (A)')
for z,pid in [('151','151'),('154','154'),('154_MF','154')]: I_('F19',z,'Public Services','General','Local Post Office','Special Use',PDF(pid,2),'PDF lists local post offices (S)')
# ---- table integrity (no document needed)
for oid in [10579,10196,9952,9911,9906,14030,2364,9289,9214,9242]:
    D_('F20',oid,'Table integrity','Exact duplicate of another row for the same district and use; the lower OBJECTID copy is kept (for PCAP_COM/PS_FAIRWAY the copy with a status is kept)')
U_('F21',5652,'Zoning_ID','045','Table integrity','"45" matches no district; 045 has every other timeshare variant but this one','Likely')
D_('F21',9208,'Table integrity','Second copy of the "45" row','Likely')
D_('F22',12762,'Table integrity','Every field is null')
# ---- vocabulary
for oid in U[U.Use_Type.fillna('').str.strip().eq('Ranch Pasture Management')].OBJECTID:
    U_('F23',oid,'Use_Type','Range Pasture Management','PAS PDFs, resource management lists','Every PAS says range pasture management; Ranch is a typo','Likely')
# ---- special designation duplicates
dup=S[S.duplicated(['ZONING_ID','SPECIAL_DESIGNATION','NOTES'],keep='first')]
for oid in dup.OBJECTID: D_('F24',oid,'Table integrity','Exact duplicate special designation row; lower OBJECTID copy kept',tbl='Special_Designation')
# ---- pending rulings (rows prepared, not applied)
P=lambda **k: pend.append(k)
P(FIX_ID='R01',TABLE='PermissibleUses',ACTION='update',OBJECTID=4256,GlobalID=U.loc[4256,'GlobalID'],Zoning_ID='073',FIELD='Use_Status',OLD_VALUE='See note',NEW_VALUE='Allowed',SOURCE=PDF('073',2),QUESTION='PDF says (A) only on lots designated multi-density. Store Allowed and keep the condition in Notes?')
P(FIX_ID='R02',TABLE='PermissibleUses',ACTION='insert',Zoning_ID='154',FIELD='Use_Type',NEW_VALUE='Multiple Family Dwelling | Allowed | 8 units per acre',SOURCE=PDF('154','2-3'),QUESTION='PAS 154 has no special areas, yet the service splits it into 154 and 154_MF. Merge 154_MF into 154 and add these uses, or keep the split and document its basis?')
P(FIX_ID='R02',TABLE='PermissibleUses',ACTION='insert',Zoning_ID='154',FIELD='Use_Type',NEW_VALUE='Multi-Person Dwelling | Special Use | 15 persons per acre',SOURCE=PDF('154','2-3'),QUESTION='Same as above')
P(FIX_ID='R03',TABLE='PermissibleUses',ACTION='update',OBJECTID=676,GlobalID=U.loc[676,'GlobalID'],Zoning_ID='112',FIELD='Use_Type',OLD_VALUE=None,NEW_VALUE='Skiing Facilities',SOURCE=PDF('112',2),QUESTION='Staff note says skiing facilities is not a recognized use and needs a PAS amendment. Leave null, store the PDF term, or map to Downhill Ski Facilities?')
for oid in U[U.Zoning_ID.isna()&U.Use_Type.notna()].OBJECTID:
    P(FIX_ID='R04',TABLE='PermissibleUses',ACTION='delete or assign',OBJECTID=oid,GlobalID=U.loc[oid,'GlobalID'],Zoning_ID=None,FIELD='Zoning_ID',OLD_VALUE=U.loc[oid,'Use_Type'],SOURCE='Table integrity',QUESTION='Orphan row with no Zoning_ID; notes point to Tahoe Valley and Tourist Core area plans. Resolve during the area plan pass')
P(FIX_ID='R05',TABLE='Special_Designation',ACTION='delete',OBJECTID=381,GlobalID=S.loc[381,'GlobalID'],Zoning_ID='PCAP_MUN_DH',FIELD='',OLD_VALUE='TDR Receiving Area MFRU (no note)',SOURCE='Table integrity',QUESTION='398 is the same designation with "Bonus Units for Affordable Housing Only". Keep 398 and delete 381?')
for oid in U[U.Use_Type.fillna('').str.strip().eq('Ranch Pasture Management')].OBJECTID: pass
up=pd.DataFrame(upd); de=pd.DataFrame(dele); ins_=pd.DataFrame(ins); pe=pd.DataFrame(pend)
ins_['Density']=ins_.Density.astype('Int64')
for n,d in [('pu_updates',up[up.TABLE=='PermissibleUses']),('pu_deletes',de[de.TABLE=='PermissibleUses']),('pu_inserts',ins_),('sd_deletes',de[de.TABLE=='Special_Designation']),('pending_rulings',pe)]:
    d.to_csv(O/f'{n}.csv',index=False); print(n,len(d), d.FIX_ID.value_counts().sort_index().to_dict())
