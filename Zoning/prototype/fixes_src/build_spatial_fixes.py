"""Build District polygon fixes and Parcel attribute updates. Run from the repo root.
All geometry in NAD 1983 UTM Zone 10N (EPSG 26910), the District feature class's native projection."""
import json, pandas as pd, geopandas as gpd, shapely, warnings; warnings.filterwarnings('ignore')
AC=4046.8564224; CRS=26910
D=gpd.read_file('data/raw/district_26910.geojson').set_crs(CRS,allow_override=True)
Dv=D.copy(); Dv['geometry']=Dv.buffer(0)
g=Dv.set_index('ZONING_ID').geometry
P=gpd.read_file('data/raw/parcels.geojson').to_crs(CRS); P['geometry']=P.buffer(0)
A=pd.DataFrame(json.load(open('data/raw/parcel_attr.json')))
def clean(geom,min_m2=1.0):
    parts=[p for p in getattr(geom,'geoms',[geom]) if p.geom_type=='Polygon' and p.area>=min_m2]
    return shapely.MultiPolygon(parts) if len(parts)>1 else parts[0]
# ---- F25 repair geometry (no new shapes; listed for the Repair Geometry tool)
rep=pd.DataFrame([dict(FIX_ID='F25',OBJECTID=o,GlobalID=D.loc[D.OBJECTID==o,'GlobalID'].iloc[0],ZONING_ID=D.loc[D.OBJECTID==o,'ZONING_ID'].iloc[0],
      PROBLEM='Ring self-intersection (self-touching ring); repair changes area by 0 m2',CONFIDENCE='Certain') for o in [91,172,416]])
# ---- F26 to F28 overlaps: clip polygons and replacement shapes
clips=[]; repl=[]
for fix,lose,keep,conf,why in [
    ('F26','111_SA2','TVAP_TC_NP','Likely','Overlap lies 100 percent inside the Tahoe Valley Area Plan boundary (LocalPlan layer 1) and the 15 parcels mostly inside it already carry PLAN_ID 110'),
    ('F27','030','040','Likely','142 edge slivers along the shared boundary; the smaller, more detailed district 040 keeps its line'),
    ('F28','114','114_SA1','Likely','6 edge slivers; the special area keeps its line, base district is clipped')]:
    ov=clean(g[lose].intersection(g[keep]),0.0)
    clips.append(dict(FIX_ID=fix,CLIP_FROM_ZONING_ID=lose,KEEP_ZONING_ID=keep,ACRES=round(ov.area/AC,3),CONFIDENCE=conf,REASON=why,geometry=ov))
    new=clean(g[lose].difference(g[keep]))
    repl.append(dict(FIX_ID=fix,ZONING_ID=lose,geom=new))
# ---- F29 gap fill in Tahoe Valley under parcel 032-141-018
p=P[P.APN=='032-141-018'].geometry.iloc[0]
holes=gpd.GeoSeries([p.buffer(30).difference(shapely.union_all(Dv.geometry.values))],crs=CRS).explode(index_parts=False)
hole=[h for h in holes if h.intersects(p) and h.area>100]; hole=shapely.union_all(hole)
fill=clean(hole.intersection(p.buffer(0.5)) if hole.area>p.area*1.5 else hole)
clips.append(dict(FIX_ID='F29',CLIP_FROM_ZONING_ID='',KEEP_ZONING_ID='TVAP_TC_G',ACRES=round(fill.area/AC,3),CONFIDENCE='Likely',
    REASON='Hole in district coverage inside the Tahoe Valley Area Plan boundary; parcel 032-141-018 in it is stored as TVAP_TC_G',geometry=fill))
repl.append(dict(FIX_ID='F29',ZONING_ID='TVAP_TC_G',geom=clean(shapely.union_all([g['TVAP_TC_G'],fill]))))
# replacement features carry the full current District attributes
cols=[c for c in D.columns if c not in('geometry','Shape.STArea()','Shape.STLength()')]
R=[]
for r in repl:
    row=D[D.ZONING_ID==r['ZONING_ID']].iloc[0][cols].to_dict(); old=g[r['ZONING_ID']]
    row.update(FIX_ID=r['FIX_ID'],ACRES_OLD=row['ACRES'],ACRES=round(r['geom'].area/AC,4),ACRES_CHANGE=round((r['geom'].area-old.area)/AC,4),geometry=r['geom']); R.append(row)
repl=gpd.GeoDataFrame(R,crs=CRS); clips=gpd.GeoDataFrame(clips,crs=CRS)
# check: replacements remove the overlaps and stay valid
after=Dv.set_index('ZONING_ID').geometry.copy()
for r in repl.itertuples(): after[r.ZONING_ID]=r.geometry
for a,b in [('111_SA2','TVAP_TC_NP'),('030','040'),('114','114_SA1')]: assert after[a].intersection(after[b]).area<1.0,(a,b,after[a].intersection(after[b]).area)
assert repl.is_valid.all()
assert p.difference(shapely.union_all(after.values)).area<5, p.difference(shapely.union_all(after.values)).area
# ---- review-only layer: remaining coverage gaps and slivers outside the TRPA boundary
rev=gpd.read_file('data/raw/gaps_outside.geojson' if False else 'data/raw/out_gaps_outside.geojson').to_crs(CRS)
rev=rev[rev.acres>0.05].copy(); rev['FIX_ID']='R06'; rev['NOTE']=rev.kind.map({'gap':'Inside TRPA boundary, no district. Excludes Lake Tahoe','outside':'District area outside the TRPA boundary'})
rev=rev[~((rev.kind=='gap')&(rev.acres>100000))]  # drop the lake
# ---- parcel updates
pmode=A[A.ZONING_ID.fillna('').str.strip()!=''].groupby('ZONING_ID').agg(PLAN_ID=('PLAN_ID',lambda s:s.mode().iat[0]),PLAN_NAME=('PLAN_NAME',lambda s:s.mode().iat[0]),ZONING_DESCRIPTION=('ZONING_DESCRIPTION',lambda s:s.mode().iat[0]))
pu=[]
def PU(fix,apn,z,conf,why,src):
    a=A[A.APN==apn].iloc[0]; new=pmode.loc[z]
    for f in ['ZONING_ID','PLAN_ID','PLAN_NAME','ZONING_DESCRIPTION']:
        nv=z if f=='ZONING_ID' else new[f]
        if str(a[f])!=str(nv): pu.append(dict(FIX_ID=fix,APN=apn,OBJECTID=a.OBJECTID,FIELD=f,OLD_VALUE=a[f],NEW_VALUE=nv,CONFIDENCE=conf,REASON=why,SOURCE=src))
ov111=clips.loc[clips.FIX_ID=='F26','geometry'].iloc[0]
for apn in P[P.intersects(ov111)&(P.geometry.intersection(ov111).area/P.area>0.5)].APN:
    PU('F30',apn,'TVAP_TC_NP','Likely','Parcel lies in the F26 overlap that Tahoe Valley keeps','District overlay after F26')
PU('F31','032-141-003','TVAP_TC_OS','Likely','Parcel is 100 percent inside TVAP_TC_OS','District overlay')
PU('F31','032-192-005','TVAP_TC_G','Likely','Parcel is 100 percent inside TVAP_TC_G','District overlay')
PU('F31','032-141-018','TVAP_TC_G','Likely','Parcel sits in the F29 gap fill; stored value kept, plan fields normalized','District overlay after F29')
PU('F32','1318-09-810-113','067','Likely','Blank ZONING_ID; 71 percent inside 067','District overlay')
PU('F32','1319-19-717-015','082','Likely','Blank ZONING_ID; 54 percent inside 082','District overlay')
for apn,z in [('025-360-019','101'),('031-103-002','100')]:
    a=A[A.APN==apn].iloc[0]
    for f in ['PLAN_ID','PLAN_NAME']:
        nv=pmode.loc[z][f]
        if a[f]!=nv: pu.append(dict(FIX_ID='F33',APN=apn,OBJECTID=a.OBJECTID,FIELD=f,OLD_VALUE=a[f],NEW_VALUE=nv,CONFIDENCE='Certain',REASON=f'PLAN_ID disagrees with its own ZONING_ID {z}',SOURCE='Parcel attributes'))
pu=pd.DataFrame(pu)
# split-parcel minority list for ruling
C=pd.read_csv('data/raw/out_parcel_zoning_check.csv',dtype={'APN':str,'ZONING_ID':str})
mino=C[C.result=='split parcel, stored is minority district'][['APN','JURISDICTION','ZONING_ID','stored_share','spatial_zid','top_share']].assign(FIX_ID='R07',
    QUESTION='Parcel spans two districts and carries the one covering less area. Confirm intended zoning').rename(columns={'spatial_zid':'MAJORITY_ZONING_ID','stored_share':'STORED_SHARE','top_share':'MAJORITY_SHARE'})
mino=mino[~mino.APN.isin(pu.APN)]
# write
rep.to_csv('outputs/district_repair_geometry.csv',index=False)
clips.drop(columns='geometry').to_csv('outputs/district_clip_and_fill_polygons.csv',index=False)
repl.drop(columns='geometry').to_csv('outputs/district_replacement_shapes.csv',index=False)
pu.to_csv('outputs/parcel_updates.csv',index=False); mino.to_csv('outputs/pending_split_parcels.csv',index=False)
clips.to_file('data/processed_clips.gpkg',driver='GPKG') if False else None
import pickle; pickle.dump((clips,repl,rev),open('data/_spatial.pkl','wb'))
print('repair',len(rep),'| clip/fill',len(clips),clips[['FIX_ID','ACRES']].values.tolist(),'| replacements',repl[['FIX_ID','ZONING_ID','ACRES_OLD','ACRES','ACRES_CHANGE']].values.tolist())
print('parcel updates',len(pu),pu.groupby('FIX_ID').APN.nunique().to_dict(),'| pending split',len(mino),'| review polygons',len(rev),rev.groupby('kind').acres.sum().round(1).to_dict())
