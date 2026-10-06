"""V18.0 candle rules: ratio-based classifier (Doji -> Pin Bar -> Marubozu -> Normal),
directional Pin Bars, and the any-colour fallback for Big / Ref.
Everything else (pullback rules, level tests) is the V16.1 code from market_structure_sim_v161."""
from market_structure_rules_v152 import metrics as _metrics, EPS, P
from market_structure_rules_v152 import real_breakout as _rb
from market_structure_sim_v161 import pb_parts

K = dict(doji_body=0.20, doji_shadow=0.20, doji_center=0.30,
         pin_body=0.35, pin_shadow=0.45, pin_ratio=2.0, pin_opp=0.35,
         maru_body=0.70, maru_shadow=0.30, norm_min=0.35, norm_max=0.70)
C_NORM = 0.40


def classify(o, h, l, c):
    """Returns (doji, bull_pin, bear_pin, maru, normal)."""
    if not h > l:
        return (False,) * 5
    r = h - l; body = abs(c - o); up = h - max(o, c); lo = min(o, c) - l
    br, ur, lr = body / r, up / r, lo / r
    doji = (br <= K['doji_body'] and ur >= K['doji_shadow'] and lr >= K['doji_shadow']
            and abs((o - l) / r - 0.5) <= K['doji_center'] and abs((c - l) / r - 0.5) <= K['doji_center'])
    bpr = lo >= body * K['pin_ratio'] if body > 0 else lo > 0
    spr = up >= body * K['pin_ratio'] if body > 0 else up > 0
    bull_pin = not doji and br <= K['pin_body'] and lr >= K['pin_shadow'] and bpr and ur <= K['pin_opp']
    bear_pin = not doji and br <= K['pin_body'] and ur >= K['pin_shadow'] and spr and lr <= K['pin_opp']
    pin = bull_pin or bear_pin
    maru = not doji and not pin and body >= K['maru_body'] * r - EPS and up + lo <= K['maru_shadow'] * r + EPS
    normal = not doji and not pin and not maru and K['norm_min'] <= br < K['norm_max']
    return doji, bull_pin, bear_pin, maru, normal


def metrics(bars):
    m = _metrics(bars)
    n = m['n']; rng = m['rng']; bull = m['bull']; bear = m['bear']
    cls = [classify(m['O'][i], m['H'][i], m['L'][i], m['C'][i]) for i in range(n)]
    m['cls'] = cls
    maru = [x[3] for x in cls]; m['maru'] = maru
    sb, sr, sa = [], [], []; big = []; refu = []; refd = []
    for i in range(n):
        ra = max(sa) if sa else None
        refu.append(max(sb) if sb else ra); refd.append(max(sr) if sr else ra)
        same = sb if bull[i] else sr
        pool = same if len(same) >= 3 else sa
        big.append(maru[i] and sum(1 for x in pool if rng[i] > x) >= 3)
        if maru[i]:
            sa.append(rng[i]); sa[:] = sa[-5:]
            if bull[i]:
                sb.append(rng[i]); sb[:] = sb[-5:]
            if bear[i]:
                sr.append(rng[i]); sr[:] = sr[-5:]
    m['big'] = big; m['refu'] = refu; m['refd'] = refd
    return m


def forms(m, t):
    """(doji, maru, normal, pin-any) for compatibility with older callers."""
    d, bp, sp, mr, nm = m['cls'][t]
    return d, mr, nm, bp or sp


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
    B = pin(t-2) and maru(t-1) and sz(t-1) and (inside or near) and maru(t) and sz(t) and c3
    Cc = norm(t-2) and szn(t-2) and norm(t-1) and szn(t-1) and maru(t) and sz(t) and c3
    return (A, B, Cc)


def tri_level(m, t, level, d):
    if level is None:
        return False
    A, B, Cc = tri(m, t, d)
    if not (A or B or Cc):
        return False
    O, C = m['O'], m['C']
    top, bot = max(O[t-2], C[t-2]), min(O[t-2], C[t-2]); body = top - bot
    part = max(0.0, top - max(bot, level)) if d == 1 else max(0.0, min(top, level) - bot)
    aok = A and part > P['c1_above'] * body + EPS
    cok = (B or Cc) and (C[t-2] > level if d == 1 else C[t-2] < level)
    return aok or cok


def real_breakout(m, t, level, d):
    return _rb(m, t, level, d) or tri_level(m, t, level, d)


def pb_exit(m, t, level, d):
    if level is None:
        return False
    r1, r2, r3 = pb_parts(m, t, d)
    C = m['C']
    if d == -1:
        return (r1 and C[t-1] < level and C[t] < level) or ((r2 or r3) and C[t-1] < level) or tri_level(m, t, level, -1)
    return (r1 and C[t-1] > level and C[t] > level) or ((r2 or r3) and C[t-1] > level) or tri_level(m, t, level, 1)
