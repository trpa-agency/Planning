import json, urllib.request, urllib.parse, sys, os
B="https://maps.trpa.org/server/rest/services/Zoning/MapServer"
def q(layer, **p):
    p.setdefault('f','json')
    url=f"{B}/{layer}/query?"+urllib.parse.urlencode(p)
    with urllib.request.urlopen(url, timeout=120) as r:
        return json.load(r)
def pull(layer, fields='*', geom=False, fmt='json', page=2000, order='OBJECTID'):
    out=[]; off=0
    while True:
        d=q(layer, where='1=1', outFields=fields, returnGeometry=str(geom).lower(), orderByFields=order,
            resultOffset=off, resultRecordCount=page, f=fmt, outSR=4326)
        if 'error' in d: raise SystemExit(d)
        feats=d['features']; out+=feats; off+=len(feats)
        if len(feats)<page: break
    return out
os.makedirs('raw',exist_ok=True)
for layer,name,fields in [(6,'permissible_use','*'),(7,'special_designation','*'),(0,'district_attr','*'),
    (1,'parcel_attr','OBJECTID,APN,JURISDICTION,OWNERSHIP_TYPE,EXISTING_LANDUSE,PLAN_ID,PLAN_NAME,ZONING_ID,ZONING_DESCRIPTION,TOWN_CENTER,WITHIN_TRPA_BNDY,STATUS,PARCEL_ACRES')]:
    f=pull(layer,fields)
    json.dump([x['attributes'] for x in f], open(f'raw/{name}.json','w'))
    print(name,len(f))
g=pull(0,'OBJECTID,ZONING_ID,PLAN_ID,PLAN_NAME,PLAN_TYPE',geom=True,fmt='geojson',page=100)
json.dump({'type':'FeatureCollection','features':g}, open('raw/district.geojson','w'))
print('district geojson',len(g), os.path.getsize('raw/district.geojson'))
