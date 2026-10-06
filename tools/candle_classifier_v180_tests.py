"""V18.0 candle-classifier tests: what changed vs V17.9 (run: python3 tools/candle_classifier_v180_tests.py)."""
import market_structure_rules_v180 as N
import market_structure_sim_v161 as O
from market_structure_rules_v180 import classify

ok_all = []


def check(name, got, want):
    ok = got == want; ok_all.append(ok)
    print(('OK  ' if ok else 'FAIL'), name, '->', got, '(expected', want, ')')


def kind(o, h, l, c):
    r = classify(o, h, l, c)
    k = [n for n, x in zip(('doji', 'bullPin', 'bearPin', 'maru', 'normal'), r) if x]
    return k[0] if k else 'none'


# 1) classifier table
check('body 15 / up 42 / low 43 is Doji, not Pin', kind(0.43, 1, 0, 0.58), 'doji')
check('green, long lower shadow = Bullish Pin', kind(0.70, 1, 0, 0.90), 'bullPin')
check('RED, long lower shadow = still Bullish Pin', kind(0.90, 1, 0, 0.70), 'bullPin')
check('GREEN, long upper shadow = Bearish Pin', kind(0.05, 1, 0, 0.25), 'bearPin')
check('body 80% = Marubozu', kind(0.1, 1, 0, 0.9), 'maru')
check('body 40% = Normal (was not Normal in V17.9)', kind(0.3, 1, 0, 0.7), 'normal')
check('body 30%, shadows 40/30 = no type', kind(0.40, 1, 0, 0.70), 'none')

V = 1.0


def bars(seq):
    return [(o, h, l, c, V) for (o, h, l, c) in seq]


base = [(100 + i, 101 + i, 99.9 + i, 100.9 + i) for i in range(6)]     # 6 green marubozus, length 1.1


def tri_both(seq, t, d):
    b = bars(seq)
    return any(O.tri(O.metrics(b), t, d)), any(N.tri(N.metrics(b), t, d))


# 2) pattern A: maru + PIN + maru. Middle green candle with a dominant UPPER shadow (bearish pin)
p = base[-1][3]
seqA = base + [(p, p + 1.0, p - 0.05, p + 0.95),          # C1 maru
               (p + 0.95, p + 1.95, p + 0.90, p + 1.15),   # C2 green, long upper shadow
               (p + 1.15, p + 2.6, p + 1.1, p + 2.55)]     # C3 maru closing above both highs
check('Pattern A with a GREEN BEARISH pin in the middle (V17.9, V18.0)', tri_both(seqA, len(seqA) - 1, 1), (True, False))
seqA2 = base + [(p, p + 1.0, p - 0.05, p + 0.95),
                (p + 1.30, p + 1.40, p + 0.70, p + 1.38),  # C2 green, long LOWER shadow (bullish pin)
                (p + 1.38, p + 2.6, p + 1.35, p + 2.55)]
check('Pattern A with a GREEN BULLISH pin in the middle (V17.9, V18.0)', tri_both(seqA2, len(seqA2) - 1, 1), (True, True))

# 3) pattern C: two Normals with 40% bodies now count
seqC = base + [(p + 0.3, p + 1.0, p, p + 0.7),               # body 40% (0.3 -> 0.7), normal
               (p + 0.9, p + 1.6, p + 0.6, p + 1.3),         # body 40%
               (p + 1.3, p + 2.6, p + 1.25, p + 2.55)]       # maru closing above both highs
check('Pattern C with 40%-body Normals (V17.9, V18.0)', tri_both(seqC, len(seqC) - 1, 1), (False, True))

# 4) Big fallback: only bearish marubozus so far, then a large bullish marubozu
bear = [(110 - i, 110.1 - i, 109 - i, 109.1 - i) for i in range(4)]   # 4 red marubozus, length 1.1
q = bear[-1][3]
seqB = bear + [(q, q + 2.0, q - 0.05, q + 1.95)]                     # green marubozu, length 2.05
b = bars(seqB)
check('Big bull marubozu with no previous green marubozu (V17.9, V18.0)', (O.metrics(b)['big'][-1], N.metrics(b)['big'][-1]), (False, True))

# 5) Ref fallback: bullish pattern with no previous green marubozu uses the red ones
seqR = bear + [(q + 0.3, q + 1.0, q, q + 0.7), (q + 0.9, q + 1.6, q + 0.6, q + 1.3), (q + 1.3, q + 2.6, q + 1.25, q + 2.55)]
mo, mn = O.metrics(bars(seqR)), N.metrics(bars(seqR))
check('Ref for a bullish pattern with only red marubozus before (V17.9, V18.0)', (mo['refu'][len(bear)] is not None, mn['refu'][len(bear)] is not None), (False, True))

print('\nSUMMARY:', sum(ok_all), 'of', len(ok_all), 'OK')
