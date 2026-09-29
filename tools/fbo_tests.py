"""FBO state machine (mirror of the Pine V15.9 block) on top of the V15.8 structure replica."""
import io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    import scen_ms
from scen_ms import B
import market_structure_sim_v158 as S


def fbo(bars):
    log = S.run(bars)
    H = [b[1] for b in bars]; L = [b[2] for b in bars]; C = [b[3] for b in bars]
    ev = {}
    for e in log:
        ev.setdefault(e[0], []).append(e[1:])
    trend = 0; lock = None; out = []
    active = False; level = None; lab = None; done = None
    for t in range(len(bars)):
        # state BEFORE this bar's update (Pine: fbLevelPre / fbTrendPre)
        pre_level = lock if trend == 1 else None
        sig = any(x[0] in ('CTS-up', 'CTS-dn', 'TREND->UP', 'TREND->DOWN') for x in ev.get(t, []))
        # apply this bar's structure events
        for x in ev.get(t, []):
            if x[0] == 'TREND SET': trend = 1 if x[1] == 'up' else -1
            if x[0] == 'TREND->UP': trend = 1; lock = None
            if x[0] == 'TREND->DOWN': trend = -1; lock = None
            if x[0] == 'PULLBACK': lock = x[2]
            if x[0] in ('CTS-up', 'CTS-dn'): lock = None
        if active and (sig or pre_level is None or pre_level != level):
            out.append((t, 'FBO deleted (real breakout)', lab)); active = False
        if pre_level is not None and not sig and pre_level != done and H[t] > pre_level and not active:
            active = True; level = pre_level; lab = t; out.append((t, 'FBO start', round(level, 2)))
        if active and not sig and C[t] < level:
            active = False; done = level; out.append((t, 'FBO confirmed', 'label bar', lab))
    return out, log


def base():
    b = B(); b.flat(25)
    b.maru_to(112, 6); b.pb_down(4.5); b.slow_to(106.5, 2); b.maru_to(120, 6)   # uptrend set, CTS 112 / BOS ~106
    b.pb_down(4.0); b.slow_to(113, 4)                                              # pullback locks ~120.05
    return b

# 1) price grinds above the CTS with normal candles, then closes back below -> FBO start + confirmed
b = base(); b.slow_to(119.5, 3); b.c(119.5, 120.6, 0.3, 0.3); b.c(120.6, 120.4, 0.3, 0.3); b.c(120.4, 120.8, 0.2, 0.2); b.slow_to(117, 3)
print('== 1: grind above CTS, back below'); [print('  ', x) for x in fbo(b.bars)[0]]
# 2) wick-only crossing -> FBO start and confirmed on the same bar
b = base(); b.slow_to(119.5, 3); b.c(119.5, 119.7, 0.8, 0.2); b.slow_to(116, 3)
print('== 2: wick above CTS only'); [print('  ', x) for x in fbo(b.bars)[0]]
# 3) C1 of a real breakout (two marubozus) crosses first -> FBO start, then deleted by the real breakout
b = base(); b.slow_to(118.5, 3); b.maru_to(126, 4)
print('== 3: real breakout'); r, log = fbo(b.bars); [print('  ', x) for x in r]
b.slow_to(121,2); b.pb_down(4.0); b.slow_to(117,3); b.c(117,117.3,12.0,0.2); b.slow_to(116,2)
print('== 4: after a new CTS the next line gets its own FBO'); [print('  ', x) for x in fbo(b.bars)[0]]
print('   structure:', [e for e in log if e[1] in ('CTS-up',)])
