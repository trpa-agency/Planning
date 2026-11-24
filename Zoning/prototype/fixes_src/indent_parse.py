"""Matrix with blank cells where each row label starts at the left margin and continuation lines are indented."""
import re, pdfplumber
from matrix_parse import page_lines, TOK
def parse(pdf_path, pages, fixed, label_max_x, top_min, base_tol=3, skip=r'^([IVX]+\.\s|[A-F]\.\s)'):
    xs=[x for _,x in fixed]; tol=min(b-a for a,b in zip(xs,xs[1:]))*0.5
    out=[]; cur=None
    with pdfplumber.open(pdf_path) as pdf:
        for pn in pages:
            pg=pdf.pages[pn-1]; L=[l for l in page_lines(pg) if top_min<l['top']<pg.height-60]
            labx=[min(w['x0'] for w in l['w'] if w['x1']<=label_max_x) for l in L if any(w['x1']<=label_max_x for w in l['w'])]
            import collections
            base=collections.Counter(round(x) for x in labx).most_common(1)[0][0] if labx else 0
            for l in L:
                lw=[w for w in l['w'] if w['x1']<=label_max_x]; lab=' '.join(w['text'] for w in lw).strip()
                toks={}
                for w in l['w']:
                    if w['x0']<label_max_x-2: continue
                    xc=(w['x0']+w['x1'])/2; j=min(range(len(xs)),key=lambda i:abs(xs[i]-xc))
                    if TOK.match(w['text']) and abs(xs[j]-xc)<=tol: toks[fixed[j][0]]=w['text']
                if lab and re.match(skip,lab): cur=None; continue
                if lab and abs(lw[0]['x0']-base)<=base_tol:
                    cur={'page':pn,'label':lab,'toks':dict(toks)}; out.append(cur)
                elif cur is not None:
                    if lab: cur['label']+=' '+lab
                    for k,v in toks.items(): cur['toks'].setdefault(k,v)
    rows=[]
    for o in out:
        lab=re.sub(r'[§*]+','',re.sub(r'\s+',' ',o['label'])).strip()
        for z,_ in fixed: rows.append(dict(page=o['page'],label=lab,zone=z,raw=o['toks'].get(z)))
    return rows
