"""V19.0 tests (final prompt). Run: python3 tools/rules_v190_tests.py"""
import io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    from market_structure_scenarios import B
import market_structure_sim_v190 as S
import market_structure_rules_v190 as R

ok_all = []
SHOW = ('BOX-OPEN', 'BOX-CLOSE', 'BOX-CANCEL', 'BOX-DELETE', 'PULLBACK', 'CTS-up', 'CTS-dn', 'FBO-START', 'FBO-CONFIRMED', 'TREND->DOWN')


def check(name, ok, log=()):
    ok_all.append(bool(ok)); print(('OK  ' if ok else 'FAIL'), name)
    for e in log:
        print('      ', e[:10])


def ev(b, n0):
    return [e for e in S.run(b.bars) if e[0] >= n0 and e[1] in SHOW]


def up_base():
    b = B(); b.flat(25); b.maru_to(112, 6); b.pb_down(4.5); b.slow_to(106.5, 2); b.maru_to(120, 6); return b


# 1) pattern A with a RED bullish pin bar in the middle (pin by direction, colour free)
b = up_base(); a = b.p
b.c(a, a + 2.4, 0.05, 0.05)                           # Big green marubozu
b.c(a + 2.6, a + 2.5, 0.05, 1.5)                      # RED candle, long lower shadow = Bullish Pin
b.c(a + 2.5, a + 5.2, 0.05, 0.05)                     # Big green marubozu closing above both highs
m = R.metrics(b.bars); t = len(b.bars) - 1
check('Pattern A with a red Bullish Pin in the middle', R.tri(m, t, 1)[0])

# 2) pattern C: Normals at least 40% of C3 (not of Ref)
b = up_base(); a = b.p
b.c(a, a + 0.5, 0.2, 0.3); b.c(a + 0.5, a + 1.0, 0.2, 0.3)      # green Normals, length 1.0
b.c(a + 1.0, a + 3.6, 0.05, 0.05)                                # Big green marubozu, length 2.7 -> Normals = 37%
m = R.metrics(b.bars); t = len(b.bars) - 1
check('Pattern C rejected: Normals 37% of C3', not R.tri(m, t, 1)[2])
b.bars[-1] = (a + 1.0, a + 3.4, a + 0.95, a + 3.35, 100)         # C3 length 2.45 (Big) -> Normals = 41%
m = R.metrics(b.bars)
check('Pattern C accepted: Normals 41% of C3', R.tri(m, t, 1)[2])

# 3) type 1: Big green marubozu anchor, then 2 green candles closing inside it (window 3)
b = up_base(); n0 = len(b.bars); a = b.p
b.c(a, a + 3.0, 0.05, 0.05)                           # Big anchor (larger than the 2.3 leg marubozus)
b.c(a + 1.2, a + 2.0, 0.1, 0.1)                       # green, low below the anchor's middle (no rule-2 shape), closes inside
b.c(a + 2.0, a + 1.4, 0.1, 0.1)                       # red, closes inside
b.chop(3); b.maru_to(a + 9, 3)
log = ev(b, n0)
check('Type 1 box from the Big Marubozu anchor (window of 3)', any(e[1] == 'BOX-OPEN' and e[3] == 1 for e in log), log)

# 4) type 2: Big Pin Bar anchor (3 earlier small pins make it Big)
b = up_base(); a = b.p
for i in range(3):
    b.c(a, a + 0.1, 0.1, 0.6); b.c(a + 0.1, a + 0.5, 0.05, 0.05)    # small bullish pins between green candles
n0 = len(b.bars); a = b.p
b.c(a, a + 0.4, 0.1, 2.5)                             # Big Bullish Pin (long lower shadow)
b.c(a + 0.4, a + 0.5, 0.0, 0.3); b.c(a + 0.5, a + 0.3, 0.0, 0.3)   # closes inside the pin (High a+0.5)
b.chop(3); b.maru_to(a + 8, 3)
log = ev(b, n0)
check('Type 2 box from the Big Pin Bar anchor', any(e[1] == 'BOX-OPEN' and e[3] == 2 for e in log), log)

# 5) range closed by the 6 patterns against the leg: two red marubozus closing below the floor
b = up_base(); n0 = len(b.bars); a = b.p
b.c(a, a - 0.8, 0.2, 0.2); b.c(a - 0.8, a - 0.4, 0.1, 0.1)       # type 3 box
b.chop(3)
fl = min(x[2] for x in b.bars[n0:])
b.c(b.p, fl - 0.4, 0.05, 0.05); b.c(fl - 0.4, fl - 2.0, 0.05, 0.05)   # rule 1 (bearish), both closes below the floor
b.slow_to(113, 3)
log = ev(b, n0)
check('Range closed orange by pullback rule 1 below the floor, pullback counted',
      any(e[1] == 'BOX-CLOSE' and e[2] == 'pullback' for e in log) and any(e[1] == 'PULLBACK' for e in log), log)

# 6) FBO: CTS while the FBO is still unconfirmed (box older than 2 candles) -> box deleted
b = up_base(); b.pb_down(4.0); n0 = len(b.bars)
b.maru_to(119.2, 2)
b.c(119.2, 120.6, 1.0, 0.1)                           # closes ABOVE the CTS line (120.05): FBO starts, not confirmed
b.c(120.6, 120.4, 0.3, 0.1); b.c(120.4, 120.7, 0.2, 0.1)
b.maru_to(128, 4)                                     # real breakout above the box top
log = ev(b, n0)
check('Unconfirmed FBO + CTS on candle 3+ -> FBO box deleted', any(e[1] == 'BOX-DELETE' for e in log) and any(e[1] == 'CTS-up' for e in log), log)

# 7) FBO confirmed, then a Real Breakout DOWN of the CTS line ends the FBO box (section 5-2)
b = up_base(); b.pb_down(4.0); n0 = len(b.bars)
b.maru_to(119.2, 2); b.c(119.2, 119.6, 1.2, 0.1)    # wick above the CTS, close below: FBO confirmed
b.c(119.6, 119.7, 0.2, 0.1)
b.c(119.7, 117.5, 0.05, 0.05); b.c(117.5, 115.6, 0.05, 0.05)   # rule 1 bearish below the CTS line
b.slow_to(114, 3)
log = ev(b, n0)
check('Confirmed FBO box closed by a Real Breakout down of the CTS line', any(e[1] == 'BOX-CLOSE' and e[4] == 4 for e in log), log)

print('\nSUMMARY:', sum(ok_all), 'of', len(ok_all), 'OK')
