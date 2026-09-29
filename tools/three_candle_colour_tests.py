import market_structure_sim_v158 as S
from market_structure_rules_v152 import metrics
pre=[(100,103,99.9,102.9),(103,106,102.9,105.9),(106,109,105.9,108.9),(109,112,108.9,111.9),(112,115,111.9,114.9)]
PAT={'A':[(115,117,114.9,116.9),(117,117.3,115.5,117.2),(117.2,119,117.1,118.9)],
     'B':[(115,117.5,113.5,115.5),(115.5,117.4,115.4,117.3),(117.3,119,117.2,118.9)],
     'C':[(115,117,114.6,116.3),(116.3,118.2,115.9,117.5),(117.5,119.5,117.4,119.4)]}
idx={'A':0,'B':1,'C':2}
mirror=lambda b:(230-b[0],230-b[2],230-b[1],230-b[3])       # reflect prices: bull <-> bear
flip=lambda b:(b[3],b[1],b[2],b[0])                           # swap open/close: other colour, same shape
doji=lambda b:(b[3],b[1],b[2],b[3])                           # open == close
def run(bars,d):
    m=metrics([b+(100,) for b in bars]); t=len(bars)-1
    return S.tri(m,t,d)
fails=0; n=0
for name,p in PAT.items():
    for d in (1,-1):
        base=[x if d==1 else mirror(x) for x in pre+p]
        got=run(base,d); n+=1
        if not got[idx[name]]: fails+=1; print('FAIL valid',name,d,got)
        for k in range(3):
            for tag,fn in (('other colour',flip),('doji',doji)):
                bars=list(base); bars[5+k]=fn(bars[5+k]); n+=1
                g1=run(bars,d); g2=run(bars,-d)
                if any(g1) or any(g2): fails+=1; print('FAIL',name,'dir',d,'C%d'%(k+1),tag,g1,g2)
print(f'{n} cases, {fails} failures')
