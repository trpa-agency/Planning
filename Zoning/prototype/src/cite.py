import re,sys
def find(pid,pat,ctx=1,maxhits=4):
    t=open(f'txt/{pid}.txt',errors='ignore').read(); pages=t.split('\f'); hits=[]
    for i,p in enumerate(pages,1):
        L=p.splitlines()
        for j,l in enumerate(L):
            if re.search(pat,l,re.I):
                hits.append((i,'\n'.join(x.rstrip() for x in L[max(0,j-ctx):j+ctx+1])))
    return hits[:maxhits]
if __name__=='__main__':
    for pid,pat in [a.split('::') for a in sys.argv[1:]]:
        for pg,txt in find(pid,pat): print(f'--- {pid} p{pg} /{pat}/\n{txt}')
