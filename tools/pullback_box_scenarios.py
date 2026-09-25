import io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    import market_structure_scenarios
from market_structure_scenarios import B
import market_structure_sim_v153 as sim_ms4
KEEP=('PULLBACK','CTS-up','CTS-dn','TREND SET','TREND->DOWN','TREND->UP','BOX-OPEN','BOX-CLOSE')
def show(name,bars,mirror=False):
    if mirror: bars=[(200-o,200-l,200-h,200-c,v) for o,h,l,c,v in bars]
    print('==',name+(' [MIRRORED -> downtrend]' if mirror else ''))
    for e in sim_ms4.run(bars):
        if e[1] in KEEP and e[0]>=38:
            print('   bar',e[0],':',', '.join(str(round(x,2)) if isinstance(x,float) else str(x) for x in e[1:]))
def base():
    b=B(); b.flat(25)
    b.maru_to(112,6); b.pb_down(4.5); b.slow_to(106.5,2); b.maru_to(120,6)   # uptrend: CTS 112.05 / BOS ~106
    return b
# P1
b=base(); b.slow_to(123,3)
b.c(123,120,0.5,0.5); b.c(120.5,121,0.4,0.4); b.c(121,122.6,0.2,0.2); b.c(122.6,121.5,0.3,0.3)   # range 119.5-123.5
b.c(121.5,119.0,0.05,0.05); b.c(119.0,116.8,0.05,0.05)     # Real Pullback breaks the floor -> range closes, pullback box opens
b.slow_to(115,3)                                            # pullback low ~114.5
b.slow_to(123,6)
b.c(123,124.3,0.9,0.1); b.c(124.3,123.9,0.3,0.3)           # fake above CTS line: close above, next candle no pattern -> box top expands (~125.2)
b.slow_to(121,3)
b.c(121,124.4,0.05,0.05); b.c(124.4,124.95,0.05,0.05)      # Rule 1 above the ORIGINAL CTS line but below the expanded edge -> no CTS
b.slow_to(123,3)
b.maru_to(131,4)                                            # Real Breakout above the expanded edge -> CTS on the original line
b.flat(3)
show('P1: range -> pullback closes it -> pullback box -> fake -> real breakout', b.bars)
show('P1: range -> pullback closes it -> pullback box -> fake -> real breakout', b.bars, mirror=True)
# P3: no new range inside a pullback box
b=base(); b.slow_to(123,3); b.pb_down(3.0)                 # pullback outside any range -> pullback box
b.c(120,119,0.4,0.4); b.c(119.2,119.6,0.3,0.3)             # C1 + inside C2 -> would be a range, but a pullback box is active
b.chop(4); b.maru_to(130,5); b.flat(3)
show('P3: no range inside a pullback box', b.bars)
show('P3: no range inside a pullback box', b.bars, mirror=True)
