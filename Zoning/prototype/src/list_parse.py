"""Parse one-column 'use ... status' tables from pdftotext -layout text.
zone_start(line) -> zone label or None. Returns rows: page, zone, block (BASE or SA), category, label, raw status."""
import re
ST=r'(TRPA-A|CUP|MUP|AR|A|S|C|P|X|N|No|Allowed|Special Use|Prohibited)'
ROW=re.compile(r'^(?P<ind>\s{0,6})(?P<label>[A-Za-z0-9(•\-–].*?)\s{3,}(?P<st>'+ST+r')(?P<foot>\s*\(\d+\)(\(\d+\))*|\d+|\s*\*+)?(?=\s{2,}|\s*$)')
LONE=re.compile(r'^\s{8,}(?P<st>'+ST+r')(?P<foot>\s*\(\d+\)|\d+|\*+)?(\s{2,}.*)?$')
CATS=['Residential','Tourist Accommodation','Commercial','Public Service','Recreation','Resource Management','Open Space','Shorezone','Retail','Entertainment','Services','Light Industrial','Wholesale/Storage','Wholesale / Storage']
def parse(text, zone_start, sa_start=None, stop=None, keep_page=True, is_use=None):
    rows=[]; zone=None; block='BASE'; cat=None; pend=None; last=None; li=0; float_st=None
    ALL=[]
    for pn,page in enumerate(text.split('\f'),1):
        PL=page.splitlines()
        for k,line in enumerate(PL):
            li+=1; ctx=(PL[k-1] if k>0 else '')+' ||| '+line+' ||| '+(PL[k+1] if k+1<len(PL) else '')
            s=line.strip()
            if not s: continue
            z=zone_start(line)
            if z: zone=z; block='BASE'; cat=None; pend=None; last=None; float_st=None; continue
            if zone is None: continue
            if stop and stop(line): zone=None; continue
            if sa_start:
                sa=sa_start(line)
                if sa: block=sa; cat=None; pend=None; last=None; continue
            if re.match(r'^(Washoe County Development Code|TAHOE AREA|Implementing Regulations|\d+$|Page )',s): continue
            if re.match(r'^\s{15,}('+'|'.join(CATS)+r')\s*$',line) or re.match(r'^\s*[IVX]+\.\s+[A-Z ]+(USES)?\s*$',line):
                cat=s; pend=None; last=None; continue
            if re.match(r'^\s{0,6}Same as General List',line):
                rows.append(dict(page=pn,zone=zone,block=block,category=cat,label='__SAME__',raw='SAME',foot='',plus='Plus' in line)); pend=None
                ma=re.search(r'Addition of (?P<u>.+?)\s{3,}(?P<st>'+ST+r')\s*$',line)
                if ma: last=dict(page=pn,zone=zone,block=block,category=cat,label=ma.group('u').strip(),raw=ma.group('st'),foot=''); rows.append(last)
                elif 'Addition of' in line: pend={'label':line.split('Addition of')[1].strip(),'ind':' ','same_add':True}
                continue
            ma=re.match(r'^\s{0,6}(?P<label>\S.*?)\s{3,}As above',line)
            if ma and not ROW.match(line):
                rows.append(dict(page=pn,zone=zone,block=block,category=cat,label=ma.group('label').strip(),raw='ASABOVE',foot='')); pend=None; continue
            m=ROW.match(line)
            if m:
                lab=m.group('label').strip(' •')
                if pend and len(m.group('ind'))>len(pend['ind'])+1: lab=pend['label']+' '+lab   # sub-row of a parent
                elif pend and not pend.get('used'):
                    if re.search(r'(and|of|,|&|/|–|-)$',pend['label']) or (is_use and is_use(pend['label']+' '+lab) and not is_use(lab)): lab=pend['label']+' '+lab
                last=dict(page=pn,zone=zone,block=block,category=cat,label=lab,raw=m.group('st'),foot=(m.group('foot') or '').strip(),li=li,ctx=ctx); rows.append(last)
                if pend and len(m.group('ind'))>len(pend['ind'])+1: pend['used']=True
                else: pend=None
                continue
            m=LONE.match(line)
            if m and not pend:
                float_st=(m.group('st'),(m.group('foot') or '').strip(),li); continue
            if m and (last is not None or pend):
                pass
                if pend and not pend.get('used'):
                    last=dict(page=pn,zone=zone,block=block,category=cat,label=pend['label'],raw=m.group('st'),foot=(m.group('foot') or '').strip(),li=li,ctx=ctx); rows.append(last); pend=None
                continue
            ind=len(line)-len(line.lstrip())
            if ind<=6 and re.match(r'^[A-Za-z(•]',s):
                lab=re.split(r'\s{3,}',s)[0].strip(' •')
                if float_st and li-float_st[2]<=2 and not (is_use and last and is_use(last['label']) and not is_use(lab) and re.match(r'^[a-z(]',lab)):
                    last=dict(page=pn,zone=zone,block=block,category=cat,label=lab,raw=float_st[0],foot=float_st[1],li=li,ctx=ctx); rows.append(last); float_st=None; pend=None; continue
                cont=bool(re.match(r'^[a-z(]|^(Facilities|Management|Entertainment|Vegetation|Services|Dwelling|Units|Terminals|Safety|Suppression|Transmission|Sales|Restoration|Concessions|Vocational|Treatment|Plant|Fish|Wildlife|Habitat)\b',lab))
                if is_use and last and not pend and not cont:
                    cont = (not is_use(last['label'])) and is_use(last['label']+' '+lab)
                elif is_use and last and cont and is_use(last['label']) and is_use(lab) and not is_use(last['label']+' '+lab):
                    cont=False
                if last and not pend and cont and not lab.startswith(('Less than','10%')):
                    last['label']=last['label']+' '+lab
                else: pend={'label':lab,'ind':line[:ind]}
    return rows
