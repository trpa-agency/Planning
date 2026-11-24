import sys, collections, pdfplumber, re
from matrix_parse import TOK
pdfp,pn=sys.argv[1],int(sys.argv[2]); lab=float(sys.argv[3]) if len(sys.argv)>3 else 200
with pdfplumber.open(pdfp) as pdf:
    ws=pdf.pages[pn-1].extract_words(x_tolerance=1.5)
xs=[ (w['x0']+w['x1'])/2 for w in ws if TOK.match(w['text']) and w['x0']>lab]
c=collections.Counter(round(x/4)*4 for x in xs)
print(sorted([(k,v) for k,v in c.items() if v>=4]))
hdr=[(round(w['x0']),round(w['top']),w['text']) for w in ws if w['top']<160]
print(hdr[:60])
