import market_structure_sim_v160 as V160, market_structure_sim_v161 as V161
pre=[(100,103,99.9,102.9),(103,106,102.9,105.9),(106,109,105.9,108.9),(109,112,108.9,111.9),(112,115,111.9,114.9)]  # bullish marubozus, Ref = 3.1
def run(mod,bars):
    m=mod.metrics([b+(100,) for b in pre+bars]); return mod.tri(m,len(pre)+2,1)
cases={
 'normals 45% of Ref (1.4), C3 60%':        [(115,116,114.6,115.8),(115.8,116.8,115.4,116.6),(116.6,118.5,116.55,118.45)],
 'normals 35% of Ref (1.1), C3 60%':        [(115,115.8,114.7,115.6),(115.6,116.4,115.3,116.2),(116.2,118.1,116.15,118.05)],
 'normals 45% of Ref, C3 45% (1.4)':        [(115,116,114.6,115.8),(115.8,116.8,115.4,116.6),(116.6,118.05,116.65,118.0)],
}
exp={'normals 45% of Ref (1.4), C3 60%':(False,True),'normals 35% of Ref (1.1), C3 60%':(False,False),'normals 45% of Ref, C3 45% (1.4)':(False,False)}
for k,b in cases.items():
    r=(run(V160,b)[2], run(V161,b)[2])
    print('OK ' if r==exp[k] else 'FAIL', k, ' V16.0 C:',r[0],' V16.1 C:',r[1])
