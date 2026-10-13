"""V18.2 rules (user spec sections 1-3):
- low volume on C2 (breakout AND pullback rules 2/3), default: up-move C2 is not a Bearish Pin,
  down-move C2 is not a Bullish Pin
- patterns A/B: the Pin Bar slot also takes a Doji; pattern C Normals >= 40% Ref
- pullback rule 1: Close C2 beyond C1's LOW (bearish) / HIGH (bullish)
- range-exit pullback: C1 Marubozu with the pullback, >= 50% of its length outside the box,
  both closes outside, Close C2 beyond C1's low / high (C2 any candle)."""
import market_structure_rules_v181 as R
from market_structure_rules_v181 import metrics, forms, EPS, P

VOL_MODE = 'pin'     # 'pin' (default), 'c1', 'off'
C_NORM = 0.40
OUT = 0.50


def low_sell(m, t):        # C2 of an up move
    return VOL_MODE == 'off' or (not m['cls'][t][2] if VOL_MODE == 'pin' else m['V'][t] < m['V'][t-1])


def low_buy(m, t):         # C2 of a down move
    return VOL_MODE == 'off' or (not m['cls'][t][1] if VOL_MODE == 'pin' else m['V'][t] < m['V'][t-1])


def real_breakout_main(m, t, level, d):
    if level is None or t < 1:
        return False
    H, L, C, rng, bull, bear, maru, big = (m[k] for k in ('H', 'L', 'C', 'rng', 'bull', 'bear', 'maru', 'big'))
    mid = (H[t-1] + L[t-1]) / 2
    big_len = rng[t] >= R.R1_MIN * rng[t-1] - EPS
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
    ref = (m['refu'] if d == 1 else m['refd'])[t-2]
    if ref is None:
        return (False, False, False)
    H, L, C, rng = m['H'], m['L'], m['C'], m['rng']
    col = m['bull'] if d == 1 else m['bear']
    if not (col[t-2] and col[t-1] and col[t]):
        return (False, False, False)
    pin = lambda k: (m['cls'][k][1] if d == 1 else m['cls'][k][2]) or m['cls'][k][0]   # pin bar or doji
    maru = lambda k: m['cls'][k][3]
    norm = lambda k: m['cls'][k][4]
    sz = lambda k: rng[k] >= 0.5 * ref - EPS
    szn = lambda k: rng[k] >= C_NORM * ref - EPS
    c3 = C[t] > max(H[t-1], H[t-2]) if d == 1 else C[t] < min(L[t-1], L[t-2])
    inside = H[t-1] <= H[t-2] and L[t-1] >= L[t-2]
    near = (C[t-1] >= H[t-2] - 0.05 * rng[t-2] - EPS) if d == 1 else (C[t-1] <= L[t-2] + 0.05 * rng[t-2] + EPS)
    A = maru(t-2) and sz(t-2) and pin(t-1) and maru(t) and sz(t) and c3
    B = pin(t-2) and (maru(t-1) or norm(t-1)) and (inside or near) and maru(t) and sz(t) and c3
    Cc = norm(t-2) and szn(t-2) and norm(t-1) and szn(t-1) and maru(t) and sz(t) and c3
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


def pb_exit(m, t, level, d):
    """Range-exit Real Pullback (section 3-3, item 2)."""
    if level is None or t < 1:
        return False
    H, L, C, rng, maru, bull, bear = (m[k] for k in ('H', 'L', 'C', 'rng', 'maru', 'bull', 'bear'))
    if d == -1:
        out = max(0.0, min(H[t-1], level) - L[t-1])
        return maru[t-1] and bear[t-1] and out >= OUT * rng[t-1] - EPS and C[t-1] < level and C[t] < level and C[t] < L[t-1]
    out = max(0.0, H[t-1] - max(L[t-1], level))
    return maru[t-1] and bull[t-1] and out >= OUT * rng[t-1] - EPS and C[t-1] > level and C[t] > level and C[t] > H[t-1]
