"""Parse 'use x district' matrix tables from PDF pages using word coordinates.
cols: list of (zone_id, x_center). label_max_x: words left of this are label text.
Returns rows: page, label, zone, raw token."""
import re, pdfplumber
TOK=re.compile(r'^(TRPA|CUP|MUP|AR|Al|A|S|P|T|X|N|C|M|[-–—]+)(\d[\d,]*(/\d+)?|\(\d+\)(\(\d+\))*|\*+|,\d+|/\d+)?$')
def page_lines(page, ytol=4.0):
    words=page.extract_words(keep_blank_chars=False, use_text_flow=False, x_tolerance=1.5, y_tolerance=2)
    words=sorted(words,key=lambda w:(round(w['top']),w['x0']))
    lines=[]
    for w in words:
        if lines and abs(w['top']-lines[-1]['top'])<=ytol: lines[-1]['w'].append(w)
        else: lines.append({'top':w['top'],'w':[w]})
    for l in lines: l['w'].sort(key=lambda w:w['x0'])
    return lines
def parse(pdf_path, pages, cols, label_max_x, coltol=None, stop_words=(), skip_label=None, header_until=None):
    xs=[c[1] for c in cols]; gap=min(b-a for a,b in zip(xs,xs[1:])) if len(xs)>1 else 50
    coltol=coltol or gap*0.55
    out=[]
    with pdfplumber.open(pdf_path) as pdf:
        for pn in pages:
            pg=pdf.pages[pn-1]; lines=page_lines(pg)
            if header_until: lines=[l for l in lines if l['top']>header_until(pg,lines)]
            recs=[]
            for l in lines:
                lab=' '.join(w['text'] for w in l['w'] if w['x1']<=label_max_x).strip()
                toks={}
                for w in l['w']:
                    if w['x0']<label_max_x-2: continue
                    t=w['text'].strip()
                    if not TOK.match(t): 
                        lab=(lab+' '+t).strip() if w['x0']<xs[0]-coltol else lab; continue
                    xc=(w['x0']+w['x1'])/2; j=min(range(len(xs)),key=lambda i:abs(xs[i]-xc))
                    if abs(xs[j]-xc)<=coltol: toks[j]=t
                recs.append({'lab':lab,'toks':toks,'top':l['top']})
            # assemble rows
            pend_lab=[]; pend_tok={}; last=None; cont_ok=False
            for r in recs:
                main=len(r['toks'])>=max(2,len(cols)//2)
                if main and not r['lab'] and not pend_lab and last and last['page']==pn and not (set(r['toks'])&set(last['toks'])) and len(last['toks'])<len(cols):
                    last['toks'].update(r['toks']); continue
                if main:
                    lab=' '.join(pend_lab+([r['lab']] if r['lab'] else [])).strip()
                    toks=dict(pend_tok); toks.update(r['toks'])
                    last={'page':pn,'label':lab,'toks':toks}; out.append(last); pend_lab=[]; pend_tok={}
                    cont_ok = (r['lab']=='' or bool(re.search(r'[(,&/]$|\band$|\bof$|-$',lab)))
                else:
                    if r['toks']:
                        # lone tokens go to the next main row
                        pend_tok.update(r['toks'])
                    if r['lab']:
                        if last and cont_ok and not pend_lab:
                            last['label']=(last['label']+' '+r['lab']).strip(); cont_ok=False
                        else: pend_lab.append(r['lab'])
            # drop dangling
    rows=[]; head=None
    for o in out:
        lab=re.sub(r'\s+',' ',o['label']).strip()
        lab=re.sub(r'^.*Not Permitted\s*','',lab)
        mh=re.match(r'^((?:[A-Z][A-Z/&,]+\s+)+)(?=[A-Z][a-z])',lab)
        if mh: head=mh.group(1).strip()
        lab=re.sub(r'^(?:[A-Z][A-Z/&,]+\s+)+(?=[A-Z][a-z])','',lab)   # leading ALL CAPS category headings
        lab=re.sub(r'(?<=[a-z\)])\d+(,\d+)*\b','',lab).strip()      # footnote digits on words
        if any(s.lower() in lab.lower() for s in stop_words): continue
        for j,(z,_) in enumerate(cols):
            rows.append(dict(page=o['page'],label=lab,zone=z,raw=o['toks'].get(j),heading=head))
    return rows
def words_on(pdf_path,pn,pat):
    with pdfplumber.open(pdf_path) as pdf:
        for w in pdf.pages[pn-1].extract_words():
            if re.search(pat,w['text']): print(round(w['x0'],1),round(w['x1'],1),round(w['top'],1),w['text'])
