import geopandas as gpd, pandas as pd, numpy as np, warnings; warnings.filterwarnings('ignore')
pd.set_option('display.width',250); pd.set_option('display.max_rows',100); pd.set_option('display.max_colwidth',50)
CRS=26910
P=gpd.read_file('raw/parcels.geojson').to_crs(CRS); D=gpd.read_file('raw/district.geojson').to_crs(CRS); D['geometry']=D.buffer(0)
P['geometry']=P.buffer(0); P['parea']=P.area
print('parcels',len(P),'| empty geom',P.is_empty.sum())
P['ZONING_ID']=P.ZONING_ID.fillna('').str.strip()
# overlay: share of each parcel in each district
X=gpd.overlay(P[['OBJECTID','geometry']],D[['ZONING_ID','PLAN_ID','geometry']],how='intersection',keep_geom_type=True)
X['a']=X.area; X=X.merge(P[['OBJECTID','parea']],on='OBJECTID'); X['share']=X['a']/X['parea']
X=X.sort_values(['OBJECTID','share'],ascending=[True,False])
top=X.groupby('OBJECTID').agg(spatial_zid=('ZONING_ID','first'),spatial_pid=('PLAN_ID','first'),top_share=('share','first'),n_districts=('ZONING_ID','nunique')).reset_index()
stored_share=X.rename(columns={'ZONING_ID':'Z'})[['OBJECTID','Z','share']]
R=P.drop(columns='geometry').merge(top,on='OBJECTID',how='left')
R=R.merge(stored_share,left_on=['OBJECTID','ZONING_ID'],right_on=['OBJECTID','Z'],how='left').drop(columns='Z').rename(columns={'share':'stored_share'})
R['stored_share']=R.stored_share.fillna(0)
def cls(r):
    if r.ZONING_ID=='' and pd.isna(r.spatial_zid): return 'blank, outside all districts'
    if r.ZONING_ID=='': return 'blank, but inside a district'
    if pd.isna(r.spatial_zid): return 'has ZONING_ID, outside all districts'
    if r.ZONING_ID==r.spatial_zid: return 'match'
    if r.stored_share>=0.05: return 'split parcel, stored is minority district'
    return 'wrong district'
R['result']=R.apply(cls,axis=1)
R['pid_ok']=R.PLAN_ID.fillna('').str.strip().eq(R.spatial_pid.fillna('').replace({'TVAP':'110'}))|R.PLAN_ID.fillna('').str.strip().eq(R.spatial_pid.fillna(''))
R.to_csv('out_parcel_zoning_check.csv',index=False)
print(R.result.value_counts().to_string())
print('\ninside TRPA boundary only:'); print(R[R.WITHIN_TRPA_BNDY==1].result.value_counts().to_string())
w=R[R.result=='wrong district']
print('\nwrong district by top share bucket:',pd.cut(w.top_share,[0,.5,.9,.99,1.01]).value_counts().sort_index().to_dict())
print(w.groupby(['ZONING_ID','spatial_zid']).size().sort_values(ascending=False).head(25).to_string())
b=R[R.result=='blank, but inside a district']; print('\nblank but inside district, by spatial district:'); print(b.groupby(['JURISDICTION','spatial_zid']).size().sort_values(ascending=False).head(15).to_string())
print('\nsplit parcels (any district <95% share):',(R.top_share<0.95).sum())
