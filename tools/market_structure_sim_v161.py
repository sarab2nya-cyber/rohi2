"""V15.1 replica: Range Box engine + market-structure engine, bar by bar, in Pine order.
Changes vs V15.0: no volume filter on Real Pullback; a pullback pattern completed
INSIDE an active range counts only when it breaks the range against its leg."""
from market_structure_rules_v152 import metrics as _metrics, EPS, P
from market_structure_rules_v152 import real_breakout as _rb

R = dict(doji=0.15, nmin=0.50, nmax=0.70, pin=2.0, out30=0.30, maxf=3)


def pb_parts(m, t, d):
    """Real Pullback rules 1-3 (no volume). d=-1 bearish, +1 bullish. Returns (r1, r2, r3)."""
    if t < 1:
        return (False, False, False)
    H, L, C, rng, bull, bear, maru, big = (m[k] for k in ('H', 'L', 'C', 'rng', 'bull', 'bear', 'maru', 'big'))
    mid = (H[t-1] + L[t-1]) / 2
    if d == -1:
        return (bear[t-1] and maru[t-1] and bear[t] and maru[t] and rng[t] >= P['pb_min'] * rng[t-1] - EPS and C[t] < C[t-1],
                bear[t-1] and big[t-1] and bear[t] and H[t] < mid,
                bear[t-1] and big[t-1] and bull[t] and rng[t] <= P['pb_r3'] * rng[t-1] + EPS and H[t] < mid)
    return (bull[t-1] and maru[t-1] and bull[t] and maru[t] and rng[t] >= P['pb_min'] * rng[t-1] - EPS and C[t] > C[t-1],
            bull[t-1] and big[t-1] and bull[t] and L[t] > mid,
            bull[t-1] and big[t-1] and bear[t] and rng[t] <= P['pb_r3'] * rng[t-1] + EPS and L[t] > mid)


COLOUR = True


def metrics(bars):
    """V16.0: Big and Ref compare with the 5 preceding Marubozus of the SAME colour."""
    m = _metrics(bars)
    if not COLOUR:
        return m
    n = m['n']; rng = m['rng']; maru = m['maru']; bull = m['bull']; bear = m['bear']
    sb, sr = [], []; big = []; refu = []; refd = []
    for i in range(n):
        refu.append(max(sb) if sb else None); refd.append(max(sr) if sr else None)
        pool = sb if bull[i] else sr
        big.append(maru[i] and sum(1 for x in pool if rng[i] > x) >= 3)
        if maru[i] and bull[i]:
            sb.append(rng[i]); sb[:] = sb[-5:]
        if maru[i] and bear[i]:
            sr.append(rng[i]); sr[:] = sr[-5:]
    m['big'] = big; m['refu'] = refu; m['refd'] = refd
    return m


C_NORM = 0.40

TRI = True


def maru_ref(m):
    if 'ref' in m:
        return m['ref']
    ref = []; sizes = []
    for i in range(m['n']):
        ref.append(max(sizes) if sizes else None)
        if m['maru'][i]:
            sizes.append(m['rng'][i]); sizes[:] = sizes[-5:]
    m['ref'] = ref
    return ref


def tri(m, t, d):
    """Special three-candle patterns A/B/C ending at t (C1=t-2). d=+1 bullish, -1 bearish."""
    if not TRI or t < 2:
        return (False, False, False)
    ref = (m['refu'] if d == 1 else m['refd'])[t-2] if COLOUR else maru_ref(m)[t-2]
    if ref is None:
        return (False, False, False)
    O, H, L, C, rng = m['O'], m['H'], m['L'], m['C'], m['rng']
    col = m['bull'] if d == 1 else m['bear']
    if not (col[t-2] and col[t-1] and col[t]):
        return (False, False, False)
    f2, f1, f0 = forms(m, t-2), forms(m, t-1), forms(m, t)   # (doji, maru, normal, pin)
    sz = lambda k: rng[k] >= 0.5 * ref - EPS
    c3 = C[t] > max(H[t-1], H[t-2]) if d == 1 else C[t] < min(L[t-1], L[t-2])
    inside = H[t-1] <= H[t-2] and L[t-1] >= L[t-2]
    near = (C[t-1] >= H[t-2] - 0.05 * rng[t-2] - EPS) if d == 1 else (C[t-1] <= L[t-2] + 0.05 * rng[t-2] + EPS)
    A = f2[1] and sz(t-2) and f1[3] and f0[1] and sz(t) and c3
    B = f2[3] and f1[1] and sz(t-1) and (inside or near) and f0[1] and sz(t) and c3
    szn = lambda k: rng[k] >= C_NORM * ref - EPS          # V16.1: the two Normals need 40% of Ref
    Cc = f2[2] and szn(t-2) and f1[2] and szn(t-1) and f0[1] and sz(t) and c3
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
    """Pullback pattern that breaks a range boundary: rule 1 both closes beyond, rules 2/3 C1 close beyond."""
    if level is None:
        return False
    r1, r2, r3 = pb_parts(m, t, d)
    C = m['C']
    if d == -1:
        return (r1 and C[t-1] < level and C[t] < level) or ((r2 or r3) and C[t-1] < level) or tri_level(m, t, level, -1)
    return (r1 and C[t-1] > level and C[t] > level) or ((r2 or r3) and C[t-1] > level) or tri_level(m, t, level, 1)


def forms(m, t):
    O, H, L, C, rng, body = (m[k] for k in ('O', 'H', 'L', 'C', 'rng', 'body'))
    vb = body[t] > 0.01
    bp = body[t] / rng[t]
    uw = H[t] - max(O[t], C[t]); lw = min(O[t], C[t]) - L[t]
    doji = bp <= R['doji']
    maru = vb and body[t] >= P['maru'] * rng[t] - EPS
    normal = vb and R['nmin'] <= bp <= R['nmax']
    pin = vb and ((uw >= body[t] * R['pin'] and uw > lw) or (lw >= body[t] * R['pin'] and lw > uw))
    return doji, maru, normal, pin


def run(bars, log=None, box_log=None):
    m = metrics(bars); O, H, L, C = m['O'], m['H'], m['L'], m['C']
    n = m['n']
    pdn = [any(pb_parts(m, t, -1)) or any(tri(m, t, -1)) for t in range(n)]
    pup = [any(pb_parts(m, t, 1)) or any(tri(m, t, 1)) for t in range(n)]
    log = [] if log is None else log
    # box state
    active = False; bdir = 0; top = bot = None; left = None; outU = outD = 0; exH = exL = None
    lastClose = None; seedBias = 0
    # structure state
    trend = 0
    u = dict(ext=None, bar=None, lock=False, pbx=None, pbxBar=None)
    d = dict(ext=None, bar=None, lock=False, pbx=None, pbxBar=None)
    key = None
    for t in range(n):
        ev = []
        # ---------------- Range Box (runs first, like the Pine script) ----------------
        ceil = top if active else None; floor = bot if active else None
        boUp = real_breakout(m, t, ceil, 1); boDn = real_breakout(m, t, floor, -1)
        pbDnExit = pb_exit(m, t, floor, -1); pbUpExit = pb_exit(m, t, ceil, 1)
        seedUp = seedDn = False
        if t >= 1:
            d1, m1, n1, p1 = forms(m, t-1); d2, m2, n2, p2 = forms(m, t)
            c1ok = d1 or m1 or n1 or p1
            inside = H[t] <= H[t-1] and L[t] >= L[t-1]
            prot = max(H[t] - H[t-1], 0) + max(L[t-1] - L[t], 0)
            w30 = prot / m['rng'][t] <= R['out30']
            c2 = inside or (w30 and not n2 and not m2) or p2 or d2 or (n2 and (p1 or d1) and w30)
            leg = seedBias if seedBias != 0 else trend
            after = lastClose is None or t - 1 > lastClose
            seedUp = leg == 1 and after and C[t-1] < O[t-1] and (C[t] <= O[t] or d2) and c2 and not pdn[t] and not pdn[t-1]
            seedDn = leg == -1 and after and C[t-1] > O[t-1] and (C[t] >= O[t] or d2) and c2 and not pup[t] and not pup[t-1]
        wasActive = active; closedNow = False; closedBy = None
        if active:
            realBO = boUp if bdir == 1 else boDn
            realPB = (pbDnExit or boDn) if bdir == 1 else (pbUpExit or boUp)
            if realBO:
                closedNow = True; closedBy = 'breakout'; seedBias = bdir
            elif realPB:
                closedNow = True; closedBy = 'pullback'; seedBias = -bdir
            else:
                # hold the boundary while closes stay beyond it (every consecutive pair is tested
                # against it); when price closes back inside with no pattern -> absorb the whole excursion
                if C[t] > top:
                    outU += 1; exH = H[t] if exH is None else max(exH, H[t])
                else:
                    top = max(top, exH if exH is not None else H[t], H[t]); outU = 0; exH = None
                if C[t] < bot:
                    outD += 1; exL = L[t] if exL is None else min(exL, L[t])
                else:
                    bot = min(bot, exL if exL is not None else L[t], L[t]); outD = 0; exL = None
            if closedNow:
                ev.append(('BOX-CLOSE', closedBy, 'dir', bdir, 'C1', left, 'top', top, 'bot', bot))
                active = False; lastClose = t
        if not wasActive and not closedNow and (seedUp or seedDn):
            active = True; bdir = 1 if seedUp else -1; top = H[t-1]; bot = L[t-1]; left = t - 1
            outU = outD = 0; exH = exL = None
            ev.append(('BOX-OPEN', 'dir', bdir, 'C1', t - 1))
        # ---------------- Structure ----------------
        # A pullback pattern completed inside a range that was already active counts only if it breaks the range.
        pbDn = pdn[t] and (not wasActive or pbDnExit)
        pbUp = pup[t] and (not wasActive or pbUpExit)
        revDn = real_breakout(m, t, key if trend == 1 else None, -1)
        revUp = real_breakout(m, t, key if trend == -1 else None, 1)
        ctsUp = real_breakout(m, t, u['ext'] if u['lock'] else None, 1)
        ctsDn = real_breakout(m, t, d['ext'] if d['lock'] else None, -1)
        sig = 0; tp = trend
        if tp == 1 and revDn:
            sig = -2; trend = -1
            ev.append(('TREND->DOWN', 'broken BOS', key, 'A', u['ext']))
            if u['pbx'] is None or L[t] < u['pbx']:
                d.update(ext=L[t], bar=t)
            else:
                d.update(ext=u['pbx'], bar=u['pbxBar'])
            d.update(lock=False, pbx=None, pbxBar=None); key = u['ext']
        elif tp == -1 and revUp:
            sig = 2; trend = 1
            ev.append(('TREND->UP', 'broken BOS', key, 'A', d['ext']))
            if d['pbx'] is None or H[t] > d['pbx']:
                u.update(ext=H[t], bar=t)
            else:
                u.update(ext=d['pbx'], bar=d['pbxBar'])
            u.update(lock=False, pbx=None, pbxBar=None); key = d['ext']
        else:
            for s, sd, brk, pbflag, ext_px, pb_px in ((u, 1, ctsUp, pbDn, H[t], L[t]), (d, -1, ctsDn, pbUp, L[t], H[t])):
                if not ((sd == 1 and tp >= 0) or (sd == -1 and tp <= 0)):
                    continue
                beyond = (lambda a, b: a > b) if sd == 1 else (lambda a, b: a < b)
                if s['ext'] is None:
                    s.update(ext=ext_px, bar=t); continue
                if s['lock']:
                    if brk:
                        sig = sd
                        if trend == 0:
                            trend = sd; ev.append(('TREND SET', 'up' if sd == 1 else 'down'))
                        ev.append(('CTS-' + ('up' if sd == 1 else 'dn'), s['ext'], 'BOS', s['pbx']))
                        key = s['pbx']
                        s.update(ext=ext_px, bar=t, lock=False, pbx=None, pbxBar=None)
                    elif s['pbx'] is None or beyond(s['pbx'], pb_px):
                        s.update(pbx=pb_px, pbxBar=t)
                else:
                    if beyond(ext_px, s['ext']):
                        s.update(ext=ext_px, bar=t, pbx=None, pbxBar=None)
                    elif s['pbx'] is None or beyond(s['pbx'], pb_px):
                        s.update(pbx=pb_px, pbxBar=t)
                    if pbflag:
                        s['lock'] = True
                        if s['pbx'] is None:
                            s.update(pbx=pb_px, pbxBar=t)
                        ev.append(('PULLBACK', 'locks', s['ext']))
                    elif (pdn[t] if sd == 1 else pup[t]):
                        ev.append(('pullback pattern INSIDE range - ignored',))
        if sig != 0:
            seedBias = 1 if sig > 0 else -1
        for e in ev:
            log.append((t,) + e)
    return log
