import re, json, sys, pandas as pd
U=pd.DataFrame(json.load(open('raw/permissible_use.json')))
voc=[v.lower() for v in U.Use_Type.dropna().str.replace(r'\s+',' ',regex=True).str.strip().unique() if len(v)>8]
for pid in sys.argv[1:]:
    pages=open(f'txt/{pid}.txt',errors='ignore').read().split('\f'); sc=[]
    for i,p in enumerate(pages,1):
        t=re.sub(r'\s+',' ',p.lower()); hits=sum(1 for v in voc if v in t)
        tok=len(re.findall(r'(?<![A-Za-z])(A|S|MUP|CUP|P|X|-)(?![A-Za-z])',p))
        if hits>=8: sc.append((i,hits,tok))
    print(pid, [f'p{i}:{h}/{t}' for i,h,t in sc])
