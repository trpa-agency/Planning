import json, urllib.request, urllib.parse, concurrent.futures as cf
B="https://maps.trpa.org/server/rest/services/LocalPlan/MapServer/0/query"
ids=json.load(urllib.request.urlopen(B+"?"+urllib.parse.urlencode(dict(where='1=1',returnIdsOnly='true',f='json')),timeout=120))['objectIds']
ids.sort(); chunks=[ids[i:i+1000] for i in range(0,len(ids),1000)]
def get(c):
    data=urllib.parse.urlencode(dict(objectIds=','.join(map(str,c)),outFields='OBJECTID,APN,JURISDICTION,PLAN_ID,PLAN_NAME,ZONING_ID,WITHIN_TRPA_BNDY',returnGeometry='true',outSR=4326,f='geojson')).encode()
    for _ in range(3):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(B,data=data),timeout=300))['features']
        except Exception as e: err=e
    raise err
feats=[]
with cf.ThreadPoolExecutor(6) as ex:
    for f in ex.map(get,chunks): feats+=f
json.dump({'type':'FeatureCollection','features':feats},open('raw/parcels.geojson','w'))
print(len(ids),len(feats))
