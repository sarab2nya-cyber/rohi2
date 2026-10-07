"""V18.1 Real Breakout tests (user spec, section 2). Run: python3 tools/real_breakout_v181_tests.py
Each case: (V18.0 result, V18.1 result) for a breakout of LEVEL on the last bar."""
import market_structure_rules_v181 as N
import market_structure_rules_v180 as O

ok_all = []


def check(name, got, want):
    ok = got == want; ok_all.append(ok)
    print(('OK  ' if ok else 'FAIL'), name, '->', got, '(expected', want, ')')


def both(seq, level, d=1):
    b = [x if len(x) == 5 else x + (100,) for x in seq]
    t = len(b) - 1
    return O.real_breakout(O.metrics(b), t, level, d), N.real_breakout(N.metrics(b), t, level, d)


base = [(100 + i, 101 + i, 99.9 + i, 100.9 + i) for i in range(6)]   # 6 green marubozus, length 1.1
p = base[-1][3]

# Rule 1: C2 length must be >= 70% of C1 length
c1 = (p, p + 2.0, p - 0.05, p + 1.95)                                      # length 2.05
check('Rule 1, C2 = 60% of C1', both(base + [c1, (p + 1.95, p + 3.20, p + 1.93, p + 3.18)], p + 1.0), (True, False))
check('Rule 1, C2 = 80% of C1', both(base + [c1, (p + 1.95, p + 3.60, p + 1.93, p + 3.58)], p + 1.0), (True, True))

# Rule 2: Big C1 + green C2 with low above M(C1); volume of C2 lower than C1
big = (p, p + 3.0, p - 0.05, p + 2.95, 200)                                # big marubozu (length 3.05)
c2 = (p + 2.95, p + 3.4, p + 2.0, p + 3.3)
check('Rule 2, C2 volume higher than C1', both(base + [big, c2 + (300,)], p + 2.0), (True, False))
check('Rule 2, C2 volume lower than C1', both(base + [big, c2 + (100,)], p + 2.0), (True, True))

# Rule 3: red C2 exactly 30% of C1 (was "below 30%", now "at most 30%")
c2r = (p + 2.90, p + 2.95, p + 2.035, p + 2.10, 100)                       # length 0.915 = 30% of 3.05
check('Rule 3, red C2 exactly 30% of C1, low volume', both(base + [big, c2r], p + 2.0), (False, True))

# Pattern C: Normals now need 50% of Ref (Ref = 1.1): 0.45 length < 0.55 fails
nC = [(p + 0.10, p + 0.50, p + 0.05, p + 0.30), (p + 0.35, p + 0.75, p + 0.30, p + 0.60)]  # normals, length 0.45
check('Pattern C with normals at 41% of Ref', both(base + nC + [(p + 0.55, p + 1.40, p + 0.53, p + 1.38)], p), (True, False))

# Pattern B: C2 may be a Normal now; line test on C3's close
pinB = (p + 0.70, p + 1.0, p, p + 0.90)                                    # green bullish pin (body 20%, lower shadow 70%)
normB = (p + 0.55, p + 0.98, p + 0.40, p + 0.85)                           # green normal, inside C1
c3B = (p + 0.85, p + 1.70, p + 0.83, p + 1.68)                             # green marubozu closing above both highs
check('Pattern B with a NORMAL C2, C3 closes above the line', both(base + [pinB, normB, c3B], p + 1.2), (False, True))

# Pattern A: C1 and C3 must both close above the line
c1A = (p, p + 1.0, p - 0.05, p + 0.95)
pinA = (p + 1.30, p + 1.40, p + 0.70, p + 1.38)
c3A = (p + 1.38, p + 2.6, p + 1.35, p + 2.55)
check('Pattern A, C1 and C3 close above the line', both(base + [c1A, pinA, c3A], p + 0.40), (True, True))
check('Pattern A, C1 closes just below the line', both(base + [c1A, pinA, c3A], p + 0.97), (False, False))
check('Pattern A, C1 closes above the line but only 5% of its body is above', both(base + [c1A, pinA, c3A], p + 0.90), (False, True))

print('\nSUMMARY:', sum(ok_all), 'of', len(ok_all), 'OK')
