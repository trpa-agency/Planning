import geopandas as gpd, pandas as pd, shapely, warnings, itertools
warnings.filterwarnings('ignore')
pd.set_option('display.width',250); pd.set_option('display.max_columns',30); pd.set_option('display.max_colwidth',60); pd.set_option('display.max_rows',300)
CRS=26910; AC=4046.8564224
ld=lambda n: gpd.read_file(f'raw/{n}.geojson').to_crs(CRS)
D=ld('district'); LP=ld('local_plan'); J=ld('jurisdictions'); T=ld('trpa_boundary'); C=ld('county')
print('invalid geoms district:',(~D.is_valid).sum(),'| empty',D.is_empty.sum(),'| multipart',(D.geom_type=='MultiPolygon').sum())
D['geometry']=D.buffer(0); LP['geometry']=LP.buffer(0); J['geometry']=J.buffer(0); T['geometry']=T.buffer(0)
D['ac']=D.area/AC
print('district total acres',round(D.ac.sum()),'| TRPA boundary acres',round(T.area.sum()/AC))
# 1 overlaps
sj=gpd.sjoin(D[['ZONING_ID','geometry']],D[['ZONING_ID','geometry']],predicate='intersects'); sj=sj[sj.ZONING_ID_left<sj.ZONING_ID_right]
g=D.set_index('ZONING_ID').geometry; rows=[]
for a,b in zip(sj.ZONING_ID_left,sj.ZONING_ID_right):
    ar=g[a].intersection(g[b]).area/AC
    if ar>0.01: rows.append((a,b,round(ar,3)))
ov=pd.DataFrame(rows,columns=['a','b','overlap_ac']).sort_values('overlap_ac',ascending=False)
print('\n1 OVERLAPS >0.01 ac: pairs',len(ov),'total ac',round(ov.overlap_ac.sum(),2),'| >0.1ac:',(ov.overlap_ac>0.1).sum(),'| >1ac:',(ov.overlap_ac>1).sum()); print(ov.head(15).to_string(index=False)); ov.to_csv('out_overlaps.csv',index=False)
# 2 gaps vs TRPA boundary
U=shapely.union_all(D.geometry.values); tb=T.geometry.iloc[0]
gap=tb.difference(U); out=U.difference(tb)
gp=gpd.GeoSeries([gap],crs=CRS).explode(index_parts=False); gp=gp[gp.area/AC>0.01]
print('\n2 GAPS inside TRPA boundary not covered by any district: total ac',round(gap.area/AC,1),'| parts>0.01ac',len(gp),'| parts>1ac',(gp.area/AC>1).sum()); print('  largest gap parts (ac):',[round(x,1) for x in sorted(gp.area/AC,reverse=True)[:8]])
op=gpd.GeoSeries([out],crs=CRS).explode(index_parts=False); op=op[op.area/AC>0.01]
print('  District area OUTSIDE TRPA boundary: total ac',round(out.area/AC,1),'| parts>0.01ac',len(op),'| largest',[round(x,1) for x in sorted(op.area/AC,reverse=True)[:8]])
gpd.GeoDataFrame({'kind':['gap']*len(gp)+['outside']*len(op),'acres':list(gp.area/AC)+list(op.area/AC)},geometry=list(gp)+list(op),crs=CRS).to_crs(4326).to_file('out_gaps_outside.geojson')
# 3 district dissolve by plan vs Local Plan layer
print('\n3 PLAN BOUNDARY: District dissolved by PLAN_ID vs Boundaries/Local Plan')
print('  LP rows',len(LP),'distinct PLAN_ID',LP.PLAN_ID.nunique(),'| district PLAN_IDs',D.PLAN_ID.nunique()); print('  in district not LP:',sorted(set(D.PLAN_ID)-set(LP.PLAN_ID)),'| in LP not district:',sorted(set(LP.PLAN_ID)-set(D.PLAN_ID)))
print('  LP dup PLAN_ID:',LP[LP.PLAN_ID.duplicated(keep=False)][['PLAN_ID','PLAN_NAME','JURISDICTION']].to_dict('records'))
dd=D.dissolve('PLAN_ID'); ll=LP.dissolve('PLAN_ID'); rows=[]
for pid in sorted(set(dd.index)&set(ll.index)):
    a,b=dd.geometry[pid],ll.geometry[pid]; rows.append((pid,dd.PLAN_NAME[pid],ll.PLAN_NAME[pid],round(a.area/AC,1),round(b.area/AC,1),round(a.symmetric_difference(b).area/AC,2)))
pb=pd.DataFrame(rows,columns=['PLAN_ID','district_name','lp_name','district_ac','lp_ac','symdiff_ac']).sort_values('symdiff_ac',ascending=False)
print('  plans with symdiff>0.1ac:',(pb.symdiff_ac>0.1).sum(),'| >1ac:',(pb.symdiff_ac>1).sum()); print(pb.head(15).to_string(index=False)); pb.to_csv('out_plan_boundary_diff.csv',index=False)
nm=pb[pb.district_name.str.strip().str.lower()!=pb.lp_name.str.strip().str.lower()]; print('  name mismatches:',len(nm)); print(nm[['PLAN_ID','district_name','lp_name']].head(12).to_string(index=False))
# 4 jurisdiction
print('\n4 JURISDICTION'); print(J[['JURISDICTION','COUNTY']].assign(ac=(J.area/AC).round()).to_string())
x=gpd.overlay(D[['ZONING_ID','PLAN_ID','PLAN_NAME','PLAN_TYPE','ac','geometry']],J[['JURISDICTION','geometry']],how='intersection'); x['xac']=x.area/AC
x=x[x.xac>0.05]; x['pct']=(100*x.xac/x.ac).round(2)
n=x.groupby('ZONING_ID').size(); multi=x[x.ZONING_ID.isin(n[n>1].index)]
print('  districts intersecting >1 jurisdiction (>0.05ac):',multi.ZONING_ID.nunique())
minor=multi.sort_values('xac').groupby('ZONING_ID').head(-1)  # all but largest
print('  of those, minor piece >1 ac:',minor[minor.xac>1].ZONING_ID.nunique()); print(minor.sort_values('xac',ascending=False)[['ZONING_ID','PLAN_NAME','JURISDICTION','xac','pct']].head(25).to_string(index=False))
x.to_csv('out_district_jurisdiction.csv',index=False)
ap=x[x.PLAN_TYPE=='Area Plan'].groupby(['PLAN_NAME','JURISDICTION']).xac.sum().round(1).unstack(fill_value=0); print('\n  Area Plan acres by jurisdiction:'); print(ap.to_string())
LPj=LP[['PLAN_ID','PLAN_NAME','JURISDICTION']]; print('\n  Local Plan layer JURISDICTION values:',LP.JURISDICTION.value_counts(dropna=False).to_dict())
# 5 slivers & acres
D['perim']=D.length; print('\n5 ACRES field vs geometry: max abs pct diff',(100*(D.ACRES-D.ac).abs()/D.ac).max().round(2),'| >1%:',((100*(D.ACRES-D.ac).abs()/D.ac)>1).sum())
parts=D.explode(index_parts=False); parts['pac']=parts.area/AC; sl=parts[parts.pac<0.05]
print('  multipart sliver parts <0.05ac:',len(sl),'in',sl.ZONING_ID.nunique(),'districts')
