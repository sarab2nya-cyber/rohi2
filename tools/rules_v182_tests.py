"""V18.2 tests (user spec sections 1-3). Run: python3 tools/rules_v182_tests.py
Each case shows (V18.1, V18.2); the range-exit cases show V18.2 only."""
import market_structure_rules_v181 as O
import market_structure_rules_v182 as N

ok_all = []


def check(name, got, want):
    ok = got == want; ok_all.append(ok)
    print(('OK  ' if ok else 'FAIL'), name, '->', got, '(expected', want, ')')


def mk(seq):
    return [x if len(x) == 5 else x + (100,) for x in seq]


def bo(seq, level, d=1):
    b = mk(seq); t = len(b) - 1
    return O.real_breakout(O.metrics(b), t, level, d), N.real_breakout(N.metrics(b), t, level, d)


def pb(seq, d=-1):
    b = mk(seq); t = len(b) - 1
    return any(O.pb_parts(O.metrics(b), t, d)), any(N.pb_parts(N.metrics(b), t, d))


def exit_(seq, level, d=-1):
    b = mk(seq); t = len(b) - 1
    return N.pb_exit(N.metrics(b), t, level, d)


base = [(100 + i, 101 + i, 99.9 + i, 100.9 + i) for i in range(6)]   # green marubozus, length 1.1
p = base[-1][3]
big = (p, p + 3.0, p - 0.05, p + 2.95, 200)                          # big green marubozu

# 2-1 rule 2: green C2 shaped as a Bearish Pin (long upper shadow) = high selling volume -> rejected
check('Breakout rule 2, C2 = green Bearish Pin', bo(base + [big, (p + 2.95, p + 4.0, p + 2.9, p + 3.1, 50)], p + 2.0), (True, False))
check('Breakout rule 2, C2 = green Normal', bo(base + [big, (p + 2.95, p + 3.5, p + 2.9, p + 3.3, 50)], p + 2.0), (True, True))

# 3-1 rule 1: Close C2 must be below C1's LOW (was: below C1's close)
red = [(120 - i, 120.1 - i, 119 - i, 119.1 - i) for i in range(6)]  # red marubozus
q = red[-1][3]
c1 = (q, q + 0.05, q - 2.0, q - 1.95)
c2a = (q - 1.95 + 1.5, q - 1.95 + 1.55, q - 1.98, q - 1.97)          # red marubozu, length 1.53, closes above C1 low (q-2.0)
check('Pullback rule 1, C2 closes ABOVE C1 low (below C1 close)', pb(red + [c1, c2a]), (True, False))
c2b = (q - 0.6, q - 0.55, q - 2.2, q - 2.15)                         # red marubozu closing below C1 low
check('Pullback rule 1, C2 closes BELOW C1 low', pb(red + [c1, c2b]), (True, True))

# 2-2 pattern A: a green Doji in the middle now works
c1A = (p, p + 1.0, p - 0.05, p + 0.95)
doji = (p + 0.95, p + 1.30, p + 0.70, p + 1.0)                       # body 0.05/0.6, both shadows >= 20%, centred
c3A = (p + 1.0, p + 2.6, p + 0.98, p + 2.55)
check('Pattern A with a green Doji in the middle', bo(base + [c1A, doji, c3A], p + 0.5), (False, True))

# 2-2 pattern C: Normals at 45% of Ref pass again (40%)
nC = [(p + 0.10, p + 0.50, p + 0.05, p + 0.30), (p + 0.35, p + 0.75, p + 0.30, p + 0.60)]
check('Pattern C with Normals at 41% of Ref', bo(base + nC + [(p + 0.55, p + 1.40, p + 0.53, p + 1.38)], p), (False, True))

# 3-3 range-exit pullback (floor = F)
F = 110.0
mC1 = (F + 0.8, F + 0.85, F - 1.2, F - 1.15)                         # red marubozu, 60% of length below F
check('Range exit: Marubozu 60% out + Doji closing below C1 low', exit_(red + [mC1, (F - 1.25, F - 1.0, F - 1.6, F - 1.3)], F), True)
mC1b = (F + 1.2, F + 1.25, F - 0.8, F - 0.75)                        # 39% below F
check('Range exit: Marubozu only 39% out', exit_(red + [mC1b, (F - 0.8, F - 0.6, F - 1.6, F - 1.3)], F), False)
check('Range exit: C2 closes above C1 low', exit_(red + [mC1, (F - 1.15, F - 0.9, F - 1.4, F - 1.1)], F), False)

print('\nSUMMARY:', sum(ok_all), 'of', len(ok_all), 'OK')
