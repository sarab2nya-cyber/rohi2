"""V18.1 Real Breakout rules (user spec, section 2):
Rule 1: + C2 length >= 70% of C1 length.  Rule 2/3: + low volume on C2 (C2 volume < C1 volume);
Rule 3: C2 length <= 30% of C1.  Patterns: B's C2 = Marubozu or Normal (no size test),
C's Normals >= 50% Ref; level test A: C1 and C3 close beyond, B/C: C3 closes beyond.
Candle classifier, Big/Ref and pullback rules = V18.0."""
from market_structure_rules_v180 import metrics as _metrics, forms, EPS, P, pb_parts


def metrics(bars):
    m = _metrics(bars)
    m['V'] = [b[4] for b in bars]
    return m

VOL_MODE = 'c1'          # 'c1' (C2 volume < C1 volume), 'off'
R1_MIN = 0.70
C_NORM = 0.50


def low_vol(m, t):
    if VOL_MODE == 'off':
        return True
    V = m['V']
    return V[t] < V[t-1]


def real_breakout_main(m, t, level, d):
    if level is None or t < 1:
        return False
    H, L, C, rng, bull, bear, maru, big = (m[k] for k in ('H', 'L', 'C', 'rng', 'bull', 'bear', 'maru', 'big'))
    mid = (H[t-1] + L[t-1]) / 2
    lv = low_vol(m, t)
    big_len = rng[t] >= R1_MIN * rng[t-1] - EPS
    small = rng[t] <= P['bo_c2_r3'] * rng[t-1] + EPS
    if d == 1:
        r1 = maru[t-1] and maru[t] and bull[t-1] and bull[t] and C[t-1] > level and C[t] > level and C[t] > H[t-1] and big_len
        beyond = max(0.0, H[t-1] - max(L[t-1], level)) > P['c1_above'] * rng[t-1] + EPS
        r2 = big[t-1] and bull[t-1] and bull[t] and L[t] > mid and lv and beyond
        r3 = big[t-1] and bull[t-1] and bear[t] and small and L[t] > mid and lv and beyond
    else:
        r1 = maru[t-1] and maru[t] and bear[t-1] and bear[t] and C[t-1] < level and C[t] < level and C[t] < L[t-1] and big_len
        beyond = max(0.0, min(H[t-1], level) - L[t-1]) > P['c1_above'] * rng[t-1] + EPS
        r2 = big[t-1] and bear[t-1] and bear[t] and H[t] < mid and lv and beyond
        r3 = big[t-1] and bear[t-1] and bull[t] and small and H[t] < mid and lv and beyond
    return r1 or r2 or r3


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
    pin = lambda k: m['cls'][k][1] if d == 1 else m['cls'][k][2]
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
    if level is None:
        return False
    r1, r2, r3 = pb_parts(m, t, d)
    C = m['C']
    if d == -1:
        return (r1 and C[t-1] < level and C[t] < level) or ((r2 or r3) and C[t-1] < level) or tri_level(m, t, level, -1)
    return (r1 and C[t-1] > level and C[t] > level) or ((r2 or r3) and C[t-1] > level) or tri_level(m, t, level, 1)
