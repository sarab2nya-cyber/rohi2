"""V18.5 range-formation tests. Run: python3 tools/range_v185_tests.py
A range needs a mother candle holding the closes of the next 3 candles, with no 2- or 3-candle
Real Breakout / Real Pullback pattern on them; type 3 = the mother is the impulse candle."""
import io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    from market_structure_scenarios import B
import market_structure_sim_v185 as S

SHOW = ('BOX-OPEN', 'BOX-CLOSE', 'BOX-CANCEL', 'PULLBACK', 'CTS-up', 'CTS-dn', 'FBO-START')
ok_all = []


def run(name, b, n0, want, dont):
    log = [e for e in S.run(b.bars) if e[0] >= n0 and e[1] in SHOW]
    got = [e[1] for e in log]
    ok = all(any(g.startswith(w) for g in got) for w in want) and not any(any(g.startswith(x) for g in got) for x in dont)
    ok_all.append(ok)
    print('==', name, '->', 'OK' if ok else 'FAIL')
    for e in log:
        print('    ', e[:8])
    return log


def up_base():
    b = B(); b.flat(25); b.maru_to(112, 6); b.pb_down(4.5); b.slow_to(106.5, 2); b.maru_to(120, 6); return b


def dn_base():
    b = B(); b.flat(25); b.maru_to(88, 6); b.pb_up(4.5); b.slow_to(93.5, 2); b.maru_to(80, 6); return b


# Image 90 (downtrend): big red impulse, 3 small greens inside it, then a big red breaks below
b = dn_base(); n0 = len(b.bars); a = b.p
b.c(a, a - 3.0, 0.3, 0.3)                                   # impulse candle (red)
b.c(a - 3.0, a - 1.9, 0.2, 0.2); b.c(a - 1.9, a - 1.4, 0.2, 0.2); b.c(a - 1.4, a - 0.9, 0.2, 0.2)   # 3 greens inside (1st > 30% of the red: not breakout rule 3)
b.c(a - 0.9, a - 4.5, 0.2, 0.05); b.maru_to(a - 8, 3)        # big red breaks the floor
log = run('Image 90: impulse red + 3 small greens inside -> type 3 box from the impulse candle', b, n0, ['BOX-OPEN'], [])
ok_all.append(any(e[1] == 'BOX-OPEN' and e[3] == 3 and e[7] == n0 for e in log))
print('     box type 3 starting on the impulse candle:', 'OK' if ok_all[-1] else 'FAIL')

# Only 2 candles inside, the 3rd breaks out -> no range (V18.4 would have opened one)
b = up_base(); n0 = len(b.bars); a = b.p
b.c(a, a + 2.0, 0.05, 0.05); b.c(a + 2.0, a + 1.4, 0.1, 0.1); b.c(a + 1.4, a + 1.7, 0.1, 0.1)
b.c(a + 1.7, a + 3.5, 0.05, 0.05); b.maru_to(a + 8, 3)
run('2 closes inside, 3rd closes above the mother -> no range', b, n0, [], ['BOX-OPEN'])

# The 3rd candle after the mother completes a 3-candle Real Pullback (pattern C) -> no range, pullback
b = up_base(); n0 = len(b.bars); a = b.p                   # mother = the last green marubozu of the leg (high 120.05)
b.c(a, a - 0.6, 0.3, 0.3); b.c(a - 0.6, a - 1.2, 0.3, 0.3)   # two red Normals inside the mother
b.c(a - 1.2, a - 2.5, 0.05, 0.05)                           # red marubozu closing below both lows: pattern C on the 3rd candle
b.slow_to(113, 3)
run('3rd candle completes pattern C (bearish) -> pullback, no range', b, n0, ['PULLBACK'], ['BOX-OPEN'])

# Pattern on the 4th candle (after the range was confirmed on the 3rd): start-candle exception
b = up_base(); n0 = len(b.bars); a = b.p
b.c(a, a - 0.05, 3.0, 0.05)
b.c(a - 0.05, a - 1.0, 0.4, 0.4); b.c(a - 1.0, a - 1.9, 0.4, 0.4); b.c(a - 1.9, a - 3.6, 0.05, 0.05)
b.slow_to(113, 3)
run('Pattern C on the 4th candle -> range confirmed, then removed (exception), pullback', b, n0, ['BOX-OPEN', 'BOX-CANCEL', 'PULLBACK'], [])

# FBO while a range (confirmed by 3 candles) is active -> range closed, FBO box opened
b = up_base(); b.pb_down(4.0); n0 = len(b.bars)
b.maru_to(119.2, 2)
a = b.p; b.c(a, a - 0.5, 0.2, 0.2); b.c(a - 0.5, a - 0.2, 0.1, 0.1); b.c(a - 0.2, a - 0.35, 0.1, 0.1)
b.c(b.p, b.p + 0.3, 1.4, 0.1); b.slow_to(117, 4); b.maru_to(126, 4)
run('FBO inside an active range -> range closed, FBO box, CTS', b, n0, ['BOX-OPEN', 'FBO-START', 'CTS-up'], [])

print('\nSUMMARY:', sum(ok_all), 'of', len(ok_all), 'OK')
