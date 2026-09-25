"""Market-structure engine per Market_Structure_Prompt_FA.md (confirmed version).
Candle rules (3 real-breakout rules, 3 real-pullback rules) identical to the Pine script V14.4."""
EPS = 0.005
P = dict(maru=0.70, c1_above=0.30, bo_c2_r2=0.30, bo_c2_r3=0.30, pb_min=0.70, pb_r2=0.40, pb_r3=0.30)


def metrics(bars):
    n = len(bars)
    O = [b[0] for b in bars]; H = [b[1] for b in bars]; L = [b[2] for b in bars]; C = [b[3] for b in bars]; V = [b[4] for b in bars]
    rng = [max(H[i] - L[i], 0.01) for i in range(n)]
    body = [abs(C[i] - O[i]) for i in range(n)]
    bull = [C[i] > O[i] for i in range(n)]; bear = [C[i] < O[i] for i in range(n)]
    maru = [body[i] >= P['maru'] * rng[i] - EPS for i in range(n)]
    hv = []
    for i in range(n):
        w = V[max(0, i - 19):i + 1]
        hv.append(V[i] > sum(w) / len(w) if i >= 19 else False)
    sizes = []; big = []
    for i in range(n):
        big.append(maru[i] and sum(1 for s in sizes if rng[i] > s) >= 3)
        if maru[i]:
            sizes.append(rng[i]); sizes[:] = sizes[-5:]
    return dict(O=O, H=H, L=L, C=C, rng=rng, body=body, bull=bull, bear=bear, maru=maru, hv=hv, big=big, n=n)


def real_breakout(m, t, level, d):
    if level is None or t < 1:
        return False
    O, H, L, C, rng, bull, bear, maru, big = (m[k] for k in ('O', 'H', 'L', 'C', 'rng', 'bull', 'bear', 'maru', 'big'))
    top = max(C[t-1], O[t-1]); bot = min(C[t-1], O[t-1]); tot = max(top - bot, 0.01); mid = (H[t-1] + L[t-1]) / 2
    if d == 1:
        r1 = maru[t-1] and maru[t] and bull[t-1] and bull[t] and C[t-1] > level and C[t] > level and C[t] > H[t-1]
        beyond = max(0.0, top - max(bot, level)) > P['c1_above'] * tot + EPS
        r2 = big[t-1] and bull[t-1] and bull[t] and rng[t] < P['bo_c2_r2'] * rng[t-1] - EPS and L[t] > mid and beyond
        r3 = big[t-1] and bull[t-1] and bear[t] and rng[t] < P['bo_c2_r3'] * rng[t-1] - EPS and L[t] > mid and beyond
    else:
        r1 = maru[t-1] and maru[t] and bear[t-1] and bear[t] and C[t-1] < level and C[t] < level and C[t] < L[t-1]
        beyond = max(0.0, min(top, level) - bot) > P['c1_above'] * tot + EPS
        r2 = big[t-1] and bear[t-1] and bear[t] and rng[t] < P['bo_c2_r2'] * rng[t-1] - EPS and H[t] < mid and beyond
        r3 = big[t-1] and bear[t-1] and bull[t] and rng[t] < P['bo_c2_r3'] * rng[t-1] - EPS and H[t] < mid and beyond
    return r1 or r2 or r3


def real_pullback(m, t, d):
    """d = direction of the pullback candles: -1 bearish pullback, +1 bullish pullback."""
    if t < 1:
        return False
    H, L, C, rng, bull, bear, maru, big, hv = (m[k] for k in ('H', 'L', 'C', 'rng', 'bull', 'bear', 'maru', 'big', 'hv'))
    mid = (H[t-1] + L[t-1]) / 2
    if d == -1:
        r1 = bear[t-1] and maru[t-1] and hv[t-1] and bear[t] and maru[t] and hv[t] and rng[t] >= P['pb_min'] * rng[t-1] - EPS and C[t] < C[t-1]
        r2 = bear[t-1] and big[t-1] and hv[t-1] and bear[t] and rng[t] <= P['pb_r2'] * rng[t-1] + EPS and H[t] < mid
        r3 = bear[t-1] and big[t-1] and hv[t-1] and bull[t] and rng[t] <= P['pb_r3'] * rng[t-1] + EPS and H[t] < mid
    else:
        r1 = bull[t-1] and maru[t-1] and hv[t-1] and bull[t] and maru[t] and hv[t] and rng[t] >= P['pb_min'] * rng[t-1] - EPS and C[t] > C[t-1]
        r2 = bull[t-1] and big[t-1] and hv[t-1] and bull[t] and rng[t] <= P['pb_r2'] * rng[t-1] + EPS and L[t] > mid
        r3 = bull[t-1] and big[t-1] and hv[t-1] and bear[t] and rng[t] <= P['pb_r3'] * rng[t-1] + EPS and L[t] > mid
    return r1 or r2 or r3


class Side:
    """One direction's impulse / pullback tracker.
    d=+1: impulse extreme = highest high (ext), pullback extreme = lowest low since ext (pbx).
    d=-1: mirror."""
    def __init__(self, d):
        self.d = d; self.reset()

    def reset(self, ext=None, extBar=None):
        self.ext, self.extBar = ext, extBar
        self.lock = False            # phase B: real pullback happened, ext is the pending CTS
        self.pbx, self.pbxBar = None, None

    def better(self, a, b):          # is a beyond b in this side's direction
        return a > b if self.d == 1 else a < b


def run(bars, log=None):
    m = metrics(bars); H, L = m['H'], m['L']
    log = [] if log is None else log
    trend = 0
    up, dn = Side(1), Side(-1)
    key = None; keyBar = None; keyLabeled = False    # reversal level (last BOS, or A after a reversal)
    for t in range(m['n']):
        hi, lo = H[t], L[t]
        events = []
        # ---- 1. trend reversal: real breakout of the key level against the trend
        if trend == 1 and key is not None and real_breakout(m, t, key, -1):
            A, ABar = up.ext, up.extBar
            events.append(('TREND->DOWN', 'broken BOS', key, 'A (unlabelled reversal level)', A))
            trend = -1
            low0, low0Bar = (lo, t) if up.pbx is None or lo < up.pbx else (up.pbx, up.pbxBar)
            dn.reset(low0, low0Bar)
            key, keyBar, keyLabeled = A, ABar, False
        elif trend == -1 and key is not None and real_breakout(m, t, key, 1):
            A, ABar = dn.ext, dn.extBar
            events.append(('TREND->UP', 'broken BOS', key, 'A (unlabelled reversal level)', A))
            trend = 1
            hi0, hi0Bar = (hi, t) if dn.pbx is None or hi > dn.pbx else (dn.pbx, dn.pbxBar)
            up.reset(hi0, hi0Bar)
            key, keyBar, keyLabeled = A, ABar, False
        else:
            # ---- 2. per-side cycle (both sides while the trend is undetermined)
            for s in ((up,) if trend == 1 else (dn,) if trend == -1 else (up, dn)):
                ext_px = hi if s.d == 1 else lo      # price that extends the impulse
                pb_px = lo if s.d == 1 else hi       # price that extends the pullback
                if s.ext is None:
                    s.ext, s.extBar = ext_px, t
                    continue
                if s.lock:
                    if real_breakout(m, t, s.ext, s.d):
                        # CTS at ext, BOS at pullback extreme -- identified together, now
                        events.append(('CTS-' + ('up' if s.d == 1 else 'dn'), s.ext, 'BOS', s.pbx))
                        if trend == 0:
                            trend = s.d
                            events.append(('TREND SET', 'up' if s.d == 1 else 'down'))
                        key, keyBar, keyLabeled = s.pbx, s.pbxBar, True
                        s.reset(ext_px, t)
                    else:
                        if s.pbx is None or ((pb_px < s.pbx) if s.d == 1 else (pb_px > s.pbx)):
                            s.pbx, s.pbxBar = pb_px, t
                else:
                    if s.better(ext_px, s.ext):
                        s.ext, s.extBar = ext_px, t
                        s.pbx, s.pbxBar = None, None
                    else:
                        if s.pbx is None or ((pb_px < s.pbx) if s.d == 1 else (pb_px > s.pbx)):
                            s.pbx, s.pbxBar = pb_px, t
                    if real_pullback(m, t, -s.d):
                        s.lock = True
                        if s.pbx is None:
                            s.pbx, s.pbxBar = pb_px, t
                        events.append(('PULLBACK', 'locks CTS candidate', s.ext))
        for e in events:
            log.append((t,) + e)
    return log
