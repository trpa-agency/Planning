"""Matrix tables with blank cells. Columns located per page from header words.
spec: list of (zone, header_regex). Label fragments attach to the nearest status line by vertical distance."""
import re, pdfplumber
from matrix_parse import page_lines, TOK
CAT=re.compile(r'^(Resource|Management|Residential|Tourist Accommodation|Commercial|Public Service|Recreation|Resource Management|Open Space|Retail|Entertainment|Services|Light Industrial|Wholesale/Storage|Shorezone)$',re.I)
def find_cols(words, spec, prev=None):
    cols=[];
    for z,pat in spec:
        c=[w for w in words if re.fullmatch(pat,w['text'])]
        if not c: return prev
        w=min(c,key=lambda w:w['top']); cols.append((z,(w['x0']+w['x1'])/2,w['top']))
    return cols
def parse(pdf_path, pages, spec, label_max_x, header_extra=12, stop=None, is_use=None, fixed=None, top_min=None):
    out=[]; prev=None
    with pdfplumber.open(pdf_path) as pdf:
        for pn in pages:
            pg=pdf.pages[pn-1]; words=pg.extract_words(x_tolerance=1.5)
            cols=[(z,x,0) for z,x in fixed] if fixed else find_cols(words,spec,prev)
            if cols is None: continue
            prev=cols; xs=[c[1] for c in cols]
            hdr=max(c[2] for c in cols)+header_extra if cols!=prev or True else 0
            hdr_words=[] if fixed else [c[2] for c in find_cols(words,spec,None) or []]
            hdr=top_min if fixed else ((max(hdr_words)+header_extra) if hdr_words else 60)
            gap=min(b-a for a,b in zip(xs,xs[1:])) if len(xs)>1 else 60; tol=gap*0.5
            recs=[]; cat=None
            for l in page_lines(pg):
                if l['top']<=hdr or l['top']>pg.height-55: continue
                lab=' '.join(w['text'] for w in l['w'] if w['x1']<=label_max_x).strip()
                toks={}
                for w in l['w']:
                    if w['x0']<label_max_x-2: continue
                    t=w['text'].strip(); xc=(w['x0']+w['x1'])/2
                    if not TOK.match(t): continue
                    j=min(range(len(xs)),key=lambda i:abs(xs[i]-xc))
                    if abs(xs[j]-xc)<=tol: toks[j]=t
                if stop and stop(lab): break
                if lab and not toks and CAT.match(lab): recs.append({'kind':'CAT','lab':lab,'top':l['top']}); continue
                if not lab and not toks: continue
                recs.append({'kind':'T' if toks else 'L','lab':lab,'toks':toks,'top':l['top']})
            T=[r for r in recs if r['kind']=='T']
            for r in T: r['parts']=[(r['top'],r['lab'])] if r['lab'] else []
            for i,r in enumerate(recs):
                if r['kind']!='L': continue
                # nearest token line, not crossing a category heading
                cands=[]
                for t in T:
                    between=[c for c in recs if c['kind']=='CAT' and min(t['top'],r['top'])<c['top']<max(t['top'],r['top'])]
                    if between: continue
                    d=abs(t['top']-r['top']); cands.append((round(d,0), 0 if not t['lab'] else 1, -1 if t['top']<r['top'] else 0, t))
                if not cands: continue
                cands.sort(key=lambda c:(c[0],c[1],c[2]))
                if is_use:
                    dmin=cands[0][0]; near=[c for c in cands if c[0]<=dmin*1.6+1]
                    def lab_of(t,extra=None):
                        p=sorted(t['parts']+([extra] if extra else [])); return re.sub(r'\s+',' ',' '.join(x for _,x in p)).strip()
                    pick=None
                    for c in near:
                        t=c[3]; cur=lab_of(t); new=lab_of(t,(r['top'],r['lab']))
                        if is_use(new) and not is_use(cur): pick=t; break
                    if pick is None:
                        for c in near:
                            t=c[3]; cur=lab_of(t)
                            if not cur or not is_use(cur): pick=t; break
                    if pick is not None: pick['parts'].append((r['top'],r['lab']))
                    continue
                cands[0][3]['parts'].append((r['top'],r['lab']))
            cat=None; ci=0
            for r in recs:
                if r['kind']=='CAT': cat=r['lab']
                if r['kind']=='T':
                    lab=' '.join(p for _,p in sorted(r['parts']))
                    lab=re.sub(r'(?<=[a-z\)])\d+(,\d+)*\b','',re.sub(r'\s+',' ',lab)).strip()
                    out.append({'page':pn,'label':lab,'category':cat,'toks':{cols[j][0]:v for j,v in r['toks'].items()}})
    rows=[]
    for o in out:
        for z,_ in spec: rows.append(dict(page=o['page'],label=o['label'],category=o['category'],zone=z,raw=o['toks'].get(z)))
    return rows
