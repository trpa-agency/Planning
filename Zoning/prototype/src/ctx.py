import sys,re
t=open(f'txt/{sys.argv[1]}.txt',errors='ignore').read().split('\f')
for a in sys.argv[2:]:
    pg,pat=a.split('::'); L=t[int(pg)-1].splitlines()
    for i,l in enumerate(L):
        if re.search(pat,l,re.I): print(f'--- p{pg} /{pat}/'); print('\n'.join(x.rstrip()[:140] for x in L[max(0,i-2):i+3]))
