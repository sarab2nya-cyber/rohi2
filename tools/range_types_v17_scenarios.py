"""V17.0 range-type scenarios (uptrend; downtrend is the mirror)."""
import io, contextlib, sys
with contextlib.redirect_stdout(io.StringIO()):
    import market_structure_scenarios as scen_ms
from market_structure_scenarios import B
import market_structure_sim_v172 as S

SHOW = ('BOX-OPEN', 'BOX-CLOSE', 'BOX-CANCEL', 'BOX-DELETE', 'PULLBACK', 'CTS-up', 'CTS-dn', 'TREND SET', 'TREND->UP', 'TREND->DOWN', 'FBO-START', 'FBO-CONFIRMED', 'FBO-DELETED')


def show(name, b, since=0, expect=None):
    log = [e for e in S.run(b.bars) if e[1] in SHOW and e[0] >= since]
    print('==', name)
    for e in log:
        print('   bar', e[0], ':', ', '.join(str(x) for x in e[1:]))
    if expect:
        got = [e[1] for e in log]
        ok = all(any(g.startswith(x) for g in got) for x in expect[0]) and not any(any(g.startswith(x) for g in got) for x in expect[1])
        print('   ->', 'OK' if ok else 'FAIL', '(expected', expect[0], 'not', expect[1], ')')
        return ok
    return True


def base():                      # uptrend established: CTS 112 / BOS ~106, then a new wave to 120
    b = B(); b.flat(25)
    b.maru_to(112, 6); b.pb_down(4.5); b.slow_to(106.5, 2); b.maru_to(120, 6)
    return b

res = []
# ---- Type 1: marubozu, then 2 candles closing inside it -> range from the marubozu
b = base(); n0 = len(b.bars); a = b.p
b.c(a, a + 2.0, 0.05, 0.05)                  # green marubozu 120 -> 122
b.c(a + 2.0, a + 1.2, 0.1, 0.1)              # red, closes inside
b.c(a + 1.2, a + 1.6, 0.1, 0.1)              # green, closes inside
b.chop(4); b.maru_to(130, 4)
res.append(show('Type 1: marubozu + 2 closes inside', b, n0, (['BOX-OPEN'], ['PULLBACK'])))

# ---- Type 2: pin bar (body < 50%), then 2 closes inside
b = base(); n0 = len(b.bars); a = b.p
b.c(a, a + 0.4, 1.5, 1.2)                    # pin/spinning top, body 0.4 of ~3.1
b.c(a + 0.4, a + 0.9, 0.2, 0.2)
b.c(a + 0.9, a + 0.3, 0.2, 0.2)
b.chop(3); b.maru_to(130, 4)
res.append(show('Type 2: pin bar + 2 closes inside', b, n0, (['BOX-OPEN'], ['PULLBACK'])))

# ---- Type 3: red + green inside it (no real pullback) -> range
b = base(); n0 = len(b.bars); a = b.p
b.c(a, a - 0.8, 0.2, 0.2)                    # red
b.c(a - 0.8, a - 0.4, 0.1, 0.1)              # green inside the red
b.chop(4); b.maru_to(130, 4)
res.append(show('Type 3: red + green inside (failed pullback)', b, n0, (['BOX-OPEN'], ['PULLBACK'])))

# ---- Type 3 negative: red, then green closing above the red high -> nothing
b = base(); n0 = len(b.bars); a = b.p
b.c(a, a - 0.8, 0.1, 0.2)
b.c(a - 0.8, a + 1.5, 0.1, 0.1)              # closes above the red high: trend continues
b.maru_to(126, 3)
res.append(show('Type 3 negative: single red, next closes above it', b, n0, ([], ['BOX-OPEN'])))

# ---- Start candles are a real pullback (3-candle pattern C) -> no range, pullback
b = base(); n0 = len(b.bars); a = b.p
b.c(a, a - 1.4, 0.5, 0.5); b.c(a - 1.4, a - 2.8, 0.5, 0.5); b.c(a - 2.8, a - 5.2, 0.05, 0.05)
b.slow_to(113, 3)
res.append(show('Start candles form pattern C -> pullback, no range', b, n0, (['PULLBACK'], ['BOX-CLOSE'])))

# ---- Type 4: FBO range above the CTS; price falls far below it (box stays), then real breakout above box top
b = base(); b.pb_down(4.0); n0 = len(b.bars)          # pullback locks CTS ~120.05
b.maru_to(119.2, 2)                                   # V-bounce, no trapped closes
b.c(119.2, 119.6, 1.2, 0.1)                           # wick above the CTS, closes below: FBO (no pattern)
b.slow_to(110, 8)                                     # far below the CTS, no pullback pattern
b.slow_to(119, 6)
b.maru_to(130, 4)                                     # real breakout above the FBO box top
res.append(show('Type 4: FBO range, falls below CTS, real breakout above box', b, n0, (['FBO-START', 'BOX-OPEN', 'CTS-up'], ['BOX-DELETE'])))

# ---- Type 4: immediate real breakout (the crossing candle is C1 of rule 1) -> FBO box deleted, CTS registered
b = base(); b.pb_down(4.0); n0 = len(b.bars)
b.maru_to(119.2, 2); b.maru_to(126, 4)
res.append(show('Immediate real breakout at CTS -> not fake', b, n0, (['CTS-up'], ['FBO-CONFIRMED'])))

# ---- Type 4: after the FBO box is older than 2 bars, a real breakout of the CTS line INSIDE the box is not enough
b = base(); b.pb_down(4.0); n0 = len(b.bars)
b.maru_to(119.2, 2)
b.c(119.2, 120.3, 2.5, 0.1)                           # fake candle with a long wick: box top ~122.8
b.slow_to(118.5, 4)                                   # back under the CTS line
b.c(118.5, 120.2, 0.05, 0.05); b.c(120.2, 121.9, 0.05, 0.05)   # rule 1 vs the CTS line, but below the box top
b.slow_to(119, 3)
res.append(show('Rule 1 above CTS but inside the FBO box -> no CTS', b, n0, (['FBO-START', 'BOX-OPEN'], ['CTS-up'])))

# ---- Image 58: uptrend; after a DOWN move (pullback) the first green candles must not open a type-3 range
b = base(); b.pb_down(4.0); n0 = len(b.bars)                      # pullback down in the uptrend (phase B)
a = b.p; b.c(a, a + 0.9, 0.1, 0.1); b.c(a + 0.9, a + 0.5, 0.1, 0.1)  # green, then a red inside it
b.maru_to(119, 3)
log = [e for e in S.run(b.bars) if e[1] == 'BOX-OPEN' and e[0] >= n0 and e[3] == 3]
print('== Image 58: no type-3 box against the pullback direction ->', 'OK' if not log else 'FAIL', log); res.append(not log)

# ---- Images 60 / 65: correction = red normal candle, then pattern C (normal, normal, marubozu) from candle 2
b = base(); n0 = len(b.bars); a = b.p
b.c(a, a - 0.6, 0.2, 0.2)                                         # red 1 (no pattern yet)
b.c(a - 0.6, a - 1.9, 0.5, 0.5); b.c(a - 1.9, a - 3.2, 0.5, 0.5); b.c(a - 3.2, a - 5.6, 0.05, 0.05)   # pattern C
b.slow_to(113, 3)
res.append(show('Images 60/65: pullback by pattern C from the 2nd correction candle', b, n0, (['PULLBACK'], ['BOX-CLOSE'])))

# ---- Image 67: type-3 box ceiling from the box candles, NOT the wave peak
b = base(); n0 = len(b.bars); peak = max(x[1] for x in b.bars)
a = b.p; b.c(a, a - 0.8, 0.1, 0.2); b.c(a - 0.8, a - 0.5, 0.1, 0.1); b.chop(4)
lg = [e for e in S.run(b.bars) if e[1] == 'BOX-OPEN' and e[0] >= n0]
top = None
for e in S.run(b.bars):
    if e[1] == 'BOX-OPEN' and e[0] >= n0: first = e; break
print('== Image 67: type-3 box opened', lg[:1], ' wave peak', round(peak, 3))
print('\nSUMMARY:', sum(res), 'of', len(res), 'scenarios OK')
