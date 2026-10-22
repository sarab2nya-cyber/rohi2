"""V19.0 rules (final prompt): classifier V18.0; Big Marubozu / Big Pin Bar (same colour /
direction first, fallback any, none -> not Big); Real Breakout rules 1-3 with the
'no opposite Pin Bar' test; 3-candle patterns with Big Marubozus, Pin Bar by direction,
Doji without colour, pattern C Normals >= 40% of C3; no Ref."""
from market_structure_rules_v152 import metrics as _metrics, EPS, P
from market_structure_rules_v180 import classify

C_NORM = 0.40
NEAR = 0.05


def _big(pool_same, pool_all, x):
    pool = pool_same if len(pool_same) >= 3 else pool_all
    return sum(1 for v in pool if x > v) >= 3


def metrics(bars):
    m = _metrics(bars)
    n = m['n']; rng = m['rng']; bull = m['bull']; bear = m['bear']
    cls = [classify(m['O'][i], m['H'][i], m['L'][i], m['C'][i]) for i in range(n)]
    m['cls'] = cls
    m['maru'] = [c[3] for c in cls]
    mb, mr, ma, pb, ps, pa = [], [], [], [], [], []
    big, bigpin = [], []
    for i in range(n):
        d, bp, sp, mu, nm = cls[i]
        big.append(mu and ((bull[i] and _big(mb, ma, rng[i])) or (bear[i] and _big(mr, ma, rng[i]))))
        bigpin.append((bp and _big(pb, pa, rng[i])) or (sp and _big(ps, pa, rng[i])))
        for cond, lst in ((mu, ma), (mu and bull[i], mb), (mu and bear[i], mr), (bp or sp, pa), (bp, pb), (sp, ps)):
            if cond:
                lst.append(rng[i]); lst[:] = lst[-5:]
    m['big'] = big; m['bigpin'] = bigpin
    return m


def low_sell(m, t):        # C2 of an up move: not a Bearish Pin
    return not m['cls'][t][2]


def low_buy(m, t):         # C2 of a down move: not a Bullish Pin
    return not m['cls'][t][1]


def real_breakout_main(m, t, level, d):
    if level is None or t < 1:
        return False
    H, L, C, rng, bull, bear, maru, big = (m[k] for k in ('H', 'L', 'C', 'rng', 'bull', 'bear', 'maru', 'big'))
    mid = (H[t-1] + L[t-1]) / 2
    big_len = rng[t] >= 0.70 * rng[t-1] - EPS
    small = rng[t] <= P['bo_c2_r3'] * rng[t-1] + EPS
    if d == 1:
        lv = low_sell(m, t)
        r1 = maru[t-1] and maru[t] and bull[t-1] and bull[t] and C[t-1] > level and C[t] > level and C[t] > H[t-1] and big_len
        beyond = max(0.0, H[t-1] - max(L[t-1], level)) > P['c1_above'] * rng[t-1] + EPS
        r2 = big[t-1] and bull[t-1] and bull[t] and L[t] > mid and lv and beyond
        r3 = big[t-1] and bull[t-1] and bear[t] and small and L[t] > mid and lv and beyond
    else:
        lv = low_buy(m, t)
        r1 = maru[t-1] and maru[t] and bear[t-1] and bear[t] and C[t-1] < level and C[t] < level and C[t] < L[t-1] and big_len
        beyond = max(0.0, min(H[t-1], level) - L[t-1]) > P['c1_above'] * rng[t-1] + EPS
        r2 = big[t-1] and bear[t-1] and bear[t] and H[t] < mid and lv and beyond
        r3 = big[t-1] and bear[t-1] and bull[t] and small and H[t] < mid and lv and beyond
    return r1 or r2 or r3


def pb_parts(m, t, d):
    if t < 1:
        return (False, False, False)
    H, L, C, rng, bull, bear, maru, big = (m[k] for k in ('H', 'L', 'C', 'rng', 'bull', 'bear', 'maru', 'big'))
    mid = (H[t-1] + L[t-1]) / 2
    if d == -1:
        lv = low_buy(m, t)
        return (bear[t-1] and maru[t-1] and bear[t] and maru[t] and rng[t] >= P['pb_min'] * rng[t-1] - EPS and C[t] < L[t-1],
                bear[t-1] and big[t-1] and bear[t] and H[t] < mid and lv,
                bear[t-1] and big[t-1] and bull[t] and rng[t] <= P['pb_r3'] * rng[t-1] + EPS and H[t] < mid and lv)
    lv = low_sell(m, t)
    return (bull[t-1] and maru[t-1] and bull[t] and maru[t] and rng[t] >= P['pb_min'] * rng[t-1] - EPS and C[t] > H[t-1],
            bull[t-1] and big[t-1] and bull[t] and L[t] > mid and lv,
            bull[t-1] and big[t-1] and bear[t] and rng[t] <= P['pb_r3'] * rng[t-1] + EPS and L[t] > mid and lv)


def tri(m, t, d):
    if t < 2:
        return (False, False, False)
    H, L, C, rng, big = m['H'], m['L'], m['C'], m['rng'], m['big']
    col = m['bull'] if d == 1 else m['bear']
    cls = m['cls']
    pin = lambda k: (cls[k][1] if d == 1 else cls[k][2]) or cls[k][0]    # Pin Bar by direction, or Doji
    bm = lambda k: big[k] and col[k]                                     # Big Marubozu of the move's colour
    c3 = C[t] > max(H[t-1], H[t-2]) if d == 1 else C[t] < min(L[t-1], L[t-2])
    inside = H[t-1] <= H[t-2] and L[t-1] >= L[t-2]
    near = (C[t-1] >= H[t-2] - NEAR * rng[t-2] - EPS) if d == 1 else (C[t-1] <= L[t-2] + NEAR * rng[t-2] + EPS)
    A = bm(t-2) and pin(t-1) and bm(t) and c3
    B = pin(t-2) and (cls[t-1][3] or cls[t-1][4]) and col[t-1] and (inside or near) and bm(t) and c3
    nC = rng[t-2] >= C_NORM * rng[t] - EPS and rng[t-1] >= C_NORM * rng[t] - EPS
    Cc = cls[t-2][4] and col[t-2] and cls[t-1][4] and col[t-1] and nC and bm(t) and c3
    return (A, B, Cc)


def tri_level(m, t, level, d):
    if level is None:
        return False
    A, B, Cc = tri(m, t, d)
    C = m['C']
    beyond = (lambda x: x > level) if d == 1 else (lambda x: x < level)
    return (A and beyond(C[t-2]) and beyond(C[t])) or ((B or Cc) and beyond(C[t]))


def real_breakout(m, t, level, d):
    return real_breakout_main(m, t, level, d) or tri_level(m, t, level, d)
