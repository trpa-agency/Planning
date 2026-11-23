import sys,re,json; sys.path.insert(0,'src')
import pandas as pd
from list_parse import parse as lparse
from sparse_parse import parse as sparse
from plan_diff2 import expand, fold
is_use=lambda l: bool(l) and expand(fold(l))!=[None]
D=pd.DataFrame(json.load(open('raw/district_attr.json'))); W=D[D.PLAN_ID=='PCAP']
nm=lambda s: re.sub(r'[^a-z0-9]','',s.lower().replace('subdistrict','').replace('subdivision',''))
tail={nm(d.split(' - ')[-1]):z for z,d in zip(W.ZONING_ID,W.ZONING_DESCRIPTION) if 'Special Area' not in d}
MAN={'alpinepeaks':'PCAP_RES_ALPINE','carnelianbay':'PCAP_RES_CARNELIANBAY','fairwaytract':'PCAP_RES_FAIRWAY','fairwaytractnortheast':'PCAP_RES_FAIRWAYNORTHEAST','fairwaytractsouth':'PCAP_RES_FAIRWAYSOUTH',
 'flickpointagatebay':'PCAP_RES_FLICK','homewoodresidential':'PCAP_RES_HOMEWOOD','mckinneytract':'PCAP_RES_MCKINNEY','tahoevista':'PCAP_RES_SUBTAHOEVISTA','woodvista':'PCAP_RES_WOODVISTA',
 'fairwayservice':'PCAP_COM/PS_FAIRWAY','kingsbeachindustrial':'PCAP_COM/PS_KINGS','tahoecityindustrial':'PCAP_COM/PS_TAHOECITY','tahoevistaindustrial':'PCAP_COM/PS_TAHOEVISTA',
 '64acretract':'PCAP_REC_64ACRE','fishhatchery':'PCAP_REC_HATCHERY','lowertruckee':'PCAP_REC_TRUCKEE','northstar':'PCAP_REC_NORTHSTAR','northtahoehighschool':'PCAP_REC_TAHOEHIGH',
 'northtahoerecreationarea':'PCAP_REC_TAHOEREC','snowcreek':'PCAP_REC_SNOW','tahoecitygolfcourse':'PCAP_REC_TAHOECITY','upperwardvalley':'PCAP_REC_UPPERWARD','granlibakken':'PCAP_TOR',
 'tavernheights':'PCAP_RES_TAVERN','tahoeparkpineland':'PCAP_RES_TAHOEPARK','martispeak':'PCAP_CONS_MARTIS','mckinneylake':'PCAP_CONS_MCKINNEY','blackwood':'PCAP_CONS_BLACKWOOD',
 'burtoncreek':'PCAP_CONS_BURTON','lowerwardvalley':'PCAP_CONS_LOWERWARD','watsoncreek':'PCAP_CONS_WATSON','lakeforest':'PCAP_RES_LAKEFOREST','lakeforestglen':'PCAP_RES_LAKEFORESTGLEN','cedarflat':'PCAP_RES_CEDAR'}
t=open('txt/PCAP.txt',errors='ignore').read()
TB=re.compile(r'TABLE (2\.0[3-8]\.[A-Z]+)-1:?\s*(?:LAND USE REGULATIONS\s*[—-]\s*)?(.+?)\s*$')
skip_multi=('2.04.','2.05.C')
def zs(l):
    m=TB.search(l)
    if not m: return None
    if m.group(1).startswith(skip_multi): return '__SKIP__'
    k=nm(m.group(2)); z=MAN.get(k) or tail.get(k)
    if not z: print('UNMAPPED',m.group(1),m.group(2)); return '__SKIP__'
    return z
stop=lambda l: bool(re.match(r'^\s*(TABLE 2\.0[3-8]\.[A-Z]+-[2-9]|[A-Z]{1,2}\.\s+\S.*Subdistrict\.)',l))
rows=[r for r in lparse(t,zs,None,stop,is_use=is_use) if r['zone']!='__SKIP__']
R=pd.DataFrame(rows)
# rows flagged "Limited to Special Area #1" in the Add'l Regs column (same, previous, or next line)
from list_parse import ROW
def sa_only(c):
    if not isinstance(c,str): return False
    prev,cur,nxt=(c.split(' ||| ')+['',''])[:3]
    if 'Limited to Special Area' in cur: return True
    if re.search(r'#\s*1\.?\s*$',cur) and 'Limited to Special Area' in prev: return True
    if re.search(r'Limited to Special Area #\s*1',prev) and not ROW.match(prev) and not re.search(r'\b(A|C|CUP|MUP)\b',prev): return True
    return False
R['sa_only']=R.ctx.apply(sa_only)
out=[]
SA={'PCAP_RES_CEDAR':'PCAP_RES_CEDAR_SA1','PCAP_RES_LAKEFOREST':'PCAP_RES_LAKEFOREST_SA1','PCAP_RES_TAHOEPARK':'PCAP_RES_TAHOEPARK_SA1','PCAP_RES_TAVERN':'PCAP_RES_TAVERN_SA1','PCAP_REC_TAHOEHIGH':'PCAP_REC_TAHOEHIGH_SA1','PCAP_CONS_MARTIS':'PCAP_CONS_MARTIS_SA1'}
for r in R.itertuples():
    if not r.sa_only: out.append(dict(page=r.page,label=r.label,zone=r.zone,raw=r.raw,category=r.category,basis='listed'))
    if r.zone in SA: out.append(dict(page=r.page,label=r.label,zone=SA[r.zone],raw=r.raw,category=r.category,basis='special area: base list' if not r.sa_only else 'limited to special area'))
# multi-column tables
MULTI=[([116,117,118,119,120],[('PCAP_MU_TC','MU-TC'),('PCAP_MU_N','MU-N'),('PCAP_MU_S','MU-S'),('PCAP_MU_NT','MU-NT'),('PCAP_MU_REC','MU-REC'),('PCAP_MUN_DH','DH'),('PCAP_MUN_LFG','LFG')],190),
 ([142,143,144],[('PCAP_MU_MTC','MU-MTC'),('PCAP_MU_LTC','MU-LTC'),('PCAP_MU_R','MU-R'),('PCAP_MU_TOR','MU-TOR'),('PCAP_MU_WREC','MU-WREC')],235),
 ([166,167,168,169],[('PCAP_MU_GW','MU-GW'),('PCAP_MU_CCW','MU-CCW'),('PCAP_MU_CCE','MU-CCE'),('PCAP_MU_GE','MU-GE'),('PCAP_MU_NC','MU-NC')],235),
 ([186,187,188,189],[('PCAP_MU_VC_TAHOMA','Tahoma'),('PCAP_MU_VC_HOMEWOOD','Homewood'),('PCAP_MU_VC_SUNNYSIDE','Sunnyside')],262),
 ([208,209,210],[('PCAP_COM/PS_LAKEFOREST_SA1','#1'),('PCAP_COM/PS_LAKEFOREST_SA2','#2')],285)]
for pages,spec,lx in MULTI:
    for r in sparse('pdfs/PCAP.pdf',pages,spec,lx,is_use=is_use):
        out.append(dict(page=r['page'],label=r['label'],zone=r['zone'],raw=r['raw'],category=r['category'],basis='matrix'))
P=pd.DataFrame(out); P=P[~P.category.fillna('').str.contains('Shorezone',case=False)]
P.to_csv('pcap_pdf_rows.csv',index=False)
z=set(P.zone); print('zones',len(z),'missing',sorted(set(W.ZONING_ID)-z))
