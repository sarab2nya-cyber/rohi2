"""Image 42: strong impulse with huge bullish marubozus, then a pullback made of smaller red candles."""
import io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    import market_structure_scenarios as scen_ms
from market_structure_scenarios import B
import market_structure_sim_v158 as V159, market_structure_sim_v160 as V160
KEY=('PULLBACK','CTS-up','TREND SET','TREND->DOWN','TREND->UP')
def build(kind):
    b=B(); b.flat(25)
    b.maru_to(112,6); b.pb_down(4.5); b.slow_to(106.5,2); b.maru_to(120,6)      # uptrend, earlier red marubozus ~2.25
    b.pb_down(3.0); b.slow_to(117,3)                                            # pullback (reds ~1.5), CTS 120
    b.maru_to(150,4)                                                            # HUGE impulse: bullish marubozus ~7.5 each
    b.slow_to(151,2)
    a=b.p
    if kind=='C':   # pattern C bearish: normal, normal, marubozu (each ~2.4)
        b.c(a,a-1.4,0.5,0.5); b.c(a-1.4,a-2.8,0.5,0.5); b.c(a-2.8,a-5.2,0.05,0.05)
    else:           # rule 2: big red marubozu (vs previous reds) + small red candle under its 50%
        b.c(a,a-3.4,0.05,0.05); b.c(a-3.4,a-3.9,0.2,0.3)
    b.slow_to(143,3); b.maru_to(160,4)                                          # back up through the peak
    return b
for kind in ('C','R2'):
    print('== pullback by', 'pattern C (3 candles)' if kind=='C' else 'rule 2 (Big + small)')
    for name,mod in (('V15.9',V159),('V16.0',V160)):
        ev=[e for e in mod.run(build(kind).bars) if e[1] in KEY and e[0]>=44]
        print('  ',name, ev if ev else 'no pullback, no CTS/BOS')
