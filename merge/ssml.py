import xml.etree.ElementTree as ET, pandas as pd, sys
NS={'s':'urn:schemas-microsoft-com:office:spreadsheet'}
SS='{urn:schemas-microsoft-com:office:spreadsheet}'
def read(path):
    root=ET.parse(path).getroot(); out={}
    for ws in root.findall('s:Worksheet',NS):
        rows=[]
        for r in ws.findall('s:Table/s:Row',NS):
            row=[]; 
            for c in r.findall('s:Cell',NS):
                idx=c.get(SS+'Index')
                if idx: row += [None]*(int(idx)-1-len(row))
                d=c.find('s:Data',NS); row.append(d.text if d is not None else None)
                ma=c.get(SS+'MergeAcross')
                if ma: row += [None]*int(ma)
            rows.append(row)
        out[ws.get(SS+'Name')]=rows
    return out
if __name__=='__main__':
    for p in sys.argv[1:]:
        o=read(p); print('==',p)
        for n,rows in o.items():
            print(' sheet',n,'rows',len(rows),'maxcols',max(map(len,rows)) if rows else 0)
            for r in rows[:4]: print('   ',r[:14])
