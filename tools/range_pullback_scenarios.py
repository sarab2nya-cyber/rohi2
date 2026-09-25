import io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    import market_structure_scenarios
from market_structure_scenarios import B
import market_structure_sim_v152 as sim_ms2
def show(name,b,only=None):
    print('==',name)
    for e in sim_ms2.run(b.bars):
        if only and e[1] not in only: continue
        print('   bar',e[0],':',', '.join(str(round(x,2)) if isinstance(x,float) else str(x) for x in e[1:]))
KEY=('PULLBACK','CTS-up','CTS-dn','TREND SET','TREND->DOWN','TREND->UP','BOX-OPEN','BOX-CLOSE','pullback pattern INSIDE range - ignored')

def base():
    b=B(); b.flat(25)
    b.maru_to(112,6); b.pb_down(4.5); b.slow_to(106.5,2); b.maru_to(120,6)   # CTS 112.05 / BOS ~106 -> uptrend
    return b

# T1: range first, pullback pattern INSIDE it (does not break the floor), then range broken up
b=base(); b.slow_to(123,3)
b.c(123,120,0.5,0.5)            # C1: bearish normal candle, range 119.5-123.5
b.c(120.5,121,0.4,0.4)          # C2: inside
b.c(121,122.6,0.2,0.2); b.c(122.6,121.5,0.3,0.3)
b.c(122.8,121.8,0.03,0.03,100); b.c(121.8,120.8,0.03,0.03,100)   # two bear marubozus inside the box (closes 121.8/120.8 > floor 119.5)
b.chop(4)
b.maru_to(130,5)                # range broken UP
b.slow_to(133,3)
show('T1 (image 18): pullback pattern inside a range, range broken up', b, KEY)

# T2: same range, but the pullback pattern breaks the floor
b=base(); b.slow_to(123,3)
b.c(123,120,0.5,0.5); b.c(120.5,121,0.4,0.4); b.c(121,122.6,0.2,0.2); b.c(122.6,121.5,0.3,0.3)
b.c(121.5,119.0,0.05,0.05); b.c(119.0,116.8,0.05,0.05)            # two bear marubozus closing below floor 119.5
b.slow_to(115,3); b.maru_to(130,6)
show('T2: pullback pattern breaks the range floor', b, KEY)

# T3: pullback first, then a range forms, then breakout
b=base(); b.slow_to(123,3)
b.pb_down(3.0)                   # valid pullback outside any range -> lock 123.x
b.c(120,119,0.4,0.4); b.c(119.2,119.6,0.3,0.3); b.chop(6)   # range forms afterwards
b.maru_to(130,6)
show('T3: pullback first, range afterwards', b, KEY)

# T4: pullback with NORMAL volume now counts
b=B(); b.flat(25)
b.maru_to(112,6)
a=b.p; b.c(a,a-2.25,0.05,0.05,100); b.c(a-2.25,a-4.5,0.05,0.05,100)
b.slow_to(106.5,2); b.maru_to(120,6)
show('T4: pullback on normal volume', b, KEY)
