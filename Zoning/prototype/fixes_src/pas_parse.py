"""Parse TRPA Plan Area Statement text (pdftotext -layout) into permissible use rows."""
import re, glob, os, json, pandas as pd

CATS = ['Residential','Tourist Accommodation','Commercial','Public Service','Public Services','Recreation',
        'Resource Management','Primary Use','Accessory Structures']
CAT_RE = re.compile(r'^\s{0,16}(' + '|'.join(re.escape(c) for c in CATS) + r')(?: [A-Z][a-z]+)?\s{2,}(.*)$')
HDR_RE = re.compile(r'^(TRPA Plan Area Statements|\d{3}[A-Z]? - .*Page \d+|\s*Page \d+\s*$)')

def clean_lines(txt):
    out=[]
    for l in txt.splitlines():
        if HDR_RE.match(l.strip()) or re.match(r'^\s*(§+|\d)\s*$', l) or re.match(r'^\s*Amended \d', l): continue
        out.append(l.rstrip())
    return out

def section(lines, start_pat, end_pat):
    s=None
    for i,l in enumerate(lines):
        if s is None and re.search(start_pat,l): s=i
        elif s is not None and re.search(end_pat,l): return lines[s:i]
    return lines[s:] if s is not None else []

def blocks(perm):
    """Split permissible-use section into (label, mode, header_text, lines). label: GENERAL, SA1.., SHOREZONE"""
    out=[]; cur=None
    for l in perm:
        s=l.strip()
        m=re.match(r'General List',s)
        sa=re.match(r'Special Area\s*#?\s*(\d+)\s*[:.]',s)
        if m: cur=['GENERAL','',[s],[]]; out.append(cur); continue
        if sa: cur=[f'SA{sa.group(1)}','',[s],[]]; out.append(cur); continue
        if re.match(r'Shorezone\s*:',s): cur=['SHOREZONE','',[s],[]]; out.append(cur); continue
        if cur is None: continue
        if not cur[3] and not CAT_RE.match(l): cur[2].append(s)   # header continuation
        else: cur[3].append(l)
    for b in out:
        h=' '.join(b[2]).lower()
        b[1]='plus' if re.search(r'plus|in addition|additions|modification|applicable to only',h) else 'replace'
    return out

def cat_text(lines):
    """Return list of (category, joined content text)."""
    res=[]; cur=None
    for l in lines:
        m=CAT_RE.match(l)
        if m: cur=[m.group(1), m.group(2).strip()]; res.append(cur); continue
        if cur is None: continue
        s=l.strip()
        if not s: continue
        if re.match(r'^(Tolerance District|Special Area|Shorezone)',s): cur=None; continue
        cur[1]+=' '+s
    return [(c,re.sub(r'\s+',' ',t)) for c,t in res]

ITEM_RE = re.compile(r'(.+?)\(\s*(A|S)\s*§*\s*\)')
def items(text):
    out=[]
    for m in ITEM_RE.finditer(text):
        name=m.group(1)
        name=re.sub(r'^[\s,;.]*(and\s+)?','',name).strip(' ,;.')
        name=re.sub(r'^and\s+','',name)
        out.append((name,m.group(2)))
    # trailing qualifier after last (A)/(S) e.g. "only on lots..."
    tail=text[ITEM_RE.search(text).end():].strip(' .,') if ITEM_RE.search(text) else text
    return out, tail

def densities(lines):
    sec=section(lines,r'^\s*MAXIMUM DENSITIES',r'MAXIMUM COMMUNITY NOISE|ADDITIONAL DEVELOPMENT|IMPROVEMENT PROGRAMS|^\s*[A-Z ]{12,}:')
    out=[]
    for l in sec:
        m=re.match(r'^\s{2,}([A-Z][A-Za-z/,()\-& .]+?)\s{2,}(\d+(?:\.\d+)?)\s+(.+?)\s*[§*]*$',l)
        if m and not m.group(1).strip().startswith('USE'): out.append((m.group(1).strip(),float(m.group(2)),m.group(3).strip(' §*')))
    return out

def parse(path):
    pid=os.path.basename(path)[:-4]
    L=clean_lines(open(path,encoding='utf-8',errors='ignore').read())
    perm=section(L,r'^\s*PERMISSIBLE USES\s*:',r'^\s*MAXIMUM (DENSITIES|COMMUNITY)')
    rows=[]
    for label,mode,hdr,bl in blocks(perm):
        for cat,txt in cat_text(bl):
            if re.search(r'listed on the general list',txt,re.I):
                rows.append(dict(PLAN_ID=pid,block=label,mode=mode,category=cat,raw_use='__GENERAL__',status='',tail=txt)); continue
            its,tail=items(txt)
            for name,st in its: rows.append(dict(PLAN_ID=pid,block=label,mode=mode,category=cat,raw_use=name,status=st,tail=tail))
    return rows, densities(L), ' '.join(L)

if __name__=='__main__':
    LP=pd.read_csv('out_pdf_inventory.csv',dtype={'PLAN_ID':str})
    pas=LP[LP.PLAN_TYPE=='Plan Area Statement'].PLAN_ID
    R=[];DEN=[]
    for p in pas:
        f=f'txt/{p}.txt'
        if not os.path.exists(f): continue
        r,d,_=parse(f); R+=r; DEN+=[dict(PLAN_ID=p,use=a,density=b,unit=c) for a,b,c in d]
    R=pd.DataFrame(R); DEN=pd.DataFrame(DEN)
    R.to_csv('pas_raw_uses.csv',index=False); DEN.to_csv('pas_densities.csv',index=False)
    print('rows',len(R),'plans',R.PLAN_ID.nunique(),'| blocks',R.groupby(['block','mode']).size().to_dict())
    print('plans with zero rows:',sorted(set(pas)-set(R.PLAN_ID)))
    print('density rows',len(DEN),'plans',DEN.PLAN_ID.nunique())
