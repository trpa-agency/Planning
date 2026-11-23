"""Write every fix layer to outputs/Zoning_QA_Fixes_2026-11-20.gdb (EPSG 26910)."""
import pickle, shutil, pandas as pd, geopandas as gpd, pyogrio, warnings; warnings.filterwarnings('ignore')
from pathlib import Path
G=Path('outputs/Zoning_QA_Fixes_2026-11-20.gdb'); shutil.rmtree(G,ignore_errors=True)
clips,repl,rev=pickle.load(open('data/_spatial.pkl','rb'))
def tbl(name,csv,dt=None):
    d=pd.read_csv('outputs/'+csv,dtype=dt or str,keep_default_na=False,na_values=[''])
    d=d.rename(columns={'OBJECTID':'TARGET_OBJECTID','GlobalID':'TARGET_GLOBALID'})
    if 'Density' in d and 'Inserts' in name: d['Density']=pd.to_numeric(d.Density).astype('Int32')
    if 'TARGET_OBJECTID' in d: d['TARGET_OBJECTID']=pd.to_numeric(d.TARGET_OBJECTID).astype('Int32')
    pyogrio.write_dataframe(d,G,layer=name,driver='OpenFileGDB',append=G.exists()); return len(d)
def fc(name,g):
    g=g.copy().rename(columns={'OBJECTID':'TARGET_OBJECTID','GlobalID':'TARGET_GLOBALID'})
    for c in g.columns:
        if c!='geometry' and g[c].dtype==object: g[c]=g[c].astype(str).replace({'None':None,'nan':None})
    pyogrio.write_dataframe(g,G,layer=name,driver='OpenFileGDB',promote_to_multi=True,append=G.exists()); return len(g)
out={}
out['F25_District_RepairGeometry']=tbl('F25_District_RepairGeometry','district_repair_geometry.csv')
out['F26_F29_District_ClipAndFill']=fc('F26_F29_District_ClipAndFill',clips)
r=repl.copy(); r['last_edited_date']=None; r['created_date']=None
out['F26_F29_District_ReplacementShapes']=fc('F26_F29_District_ReplacementShapes',r)
out['F01_F23_PermissibleUse_Updates']=tbl('F01_F23_PermissibleUse_Updates','pu_updates.csv')
out['F12_F22_PermissibleUse_Deletes']=tbl('F12_F22_PermissibleUse_Deletes','pu_deletes.csv')
out['F15_F19_PermissibleUse_Inserts']=tbl('F15_F19_PermissibleUse_Inserts','pu_inserts.csv')
out['F24_SpecialDesignation_Deletes']=tbl('F24_SpecialDesignation_Deletes','sd_deletes.csv')
out['F30_F33_Parcel_Updates']=tbl('F30_F33_Parcel_Updates','parcel_updates.csv')
out['R01_R05_Pending_Rulings']=tbl('R01_R05_Pending_Rulings','pending_rulings.csv')
out['R07_Pending_SplitParcels']=tbl('R07_Pending_SplitParcels','pending_split_parcels.csv')
out['A01_PermissibleUse_Updates']=tbl('A01_PermissibleUse_Updates','area_pu_updates.csv')
out['A02_A05_PermissibleUse_Deletes']=tbl('A02_A05_PermissibleUse_Deletes','area_pu_deletes.csv')
out['A03_A06_PermissibleUse_Inserts']=tbl('A03_A06_PermissibleUse_Inserts','area_pu_inserts.csv')
out['R11_R18_Pending_Rulings']=tbl('R11_R18_Pending_Rulings','area_pending_rulings.csv')
out['R06_Review_CoverageGaps']=fc('R06_Review_CoverageGaps',rev[['FIX_ID','kind','acres','NOTE','geometry']])
print(out)
