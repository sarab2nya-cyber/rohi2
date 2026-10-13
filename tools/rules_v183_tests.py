"""V18.3 tests: range-exit pullback by the 6 patterns. Run: python3 tools/rules_v183_tests.py
Each case shows (V18.2, V18.3) for a pullback breaking the box floor F (bearish) or ceiling (bullish)."""
import market_structure_rules_v182 as O
import market_structure_rules_v183 as N

ok_all = []


def check(name, got, want):
    ok = got == want; ok_all.append(ok)
    print(('OK  ' if ok else 'FAIL'), name, '->', got, '(expected', want, ')')


def ex(seq, level, d):
    b = [x if len(x) == 5 else x + (100,) for x in seq]; t = len(b) - 1
    return O.pb_exit(O.metrics(b), t, level, d), N.pb_exit(N.metrics(b), t, level, d)


red = [(120 - i, 120.1 - i, 119 - i, 119.1 - i) for i in range(6)]       # red marubozus (length 1.1)
F = 110.0
# Rule 1 (two red marubozus, C2 >= 70% of C1, Close C2 < Low C1), C1 only 30% below the floor
c1 = (F + 0.7, F + 0.75, F - 0.3, F - 0.25)
c2 = (F - 0.25, F - 0.2, F - 1.1, F - 1.05)
check('Rule 1 pullback, both closes below the floor, C1 only 30% out', ex(red + [c1, c2], F, -1), (False, True))
check('Rule 1 pullback, C1 closes ABOVE the floor', ex(red + [c1, c2], F - 0.27, -1), (False, False))

grn = [(100 + i, 101 + i, 99.9 + i, 100.9 + i) for i in range(6)]          # green marubozus
T = 110.0
# Rule 2 bullish (big green marubozu, C2 green, Low C2 > M(C1), C2 not a bearish pin), C1 closes above the ceiling
b1 = (T - 2.0, T + 1.05, T - 2.05, T + 1.0)
b2 = (T + 1.0, T + 1.4, T + 0.6, T + 1.3)
check('Rule 2 bullish pullback, C1 closes above the ceiling (downtrend box)', ex(grn + [b1, b2], T, 1), (False, True))
check('Rule 2 bullish pullback, C1 closes below the ceiling', ex(grn + [b1, b2], T + 1.2, 1), (False, False))

print('\nSUMMARY:', sum(ok_all), 'of', len(ok_all), 'OK')
