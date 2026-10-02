"""V17.0 replica: Range Box with the 4 formation types + market structure + FBO range.

Range types (Range_Box_Prompt_FA.md, section 0):
  1/2 "trapped": any candle whose range (H-L, wicks) holds the CLOSES of the next 2 candles
  3   invalid pullback: after a real move, a counter candle whose next candle does not close
      beyond it in the trend direction, and no real pullback pattern
  4   fake breakout: first candle beyond the pending CTS without a real breakout -> box between
      the CTS line (fixed) and the fake highs, expanding only away from the CTS
Start candles that themselves complete a real pullback (range at most 2 bars old) -> no range,
it is the pullback.
"""
from market_structure_sim_v161 import metrics, tri, real_breakout, pb_parts, pb_exit, forms, EPS


def run(bars, log=None, fbo_log=None):
    m = metrics(bars); O, H, L, C = m['O'], m['H'], m['L'], m['C']
    n = m['n']
    pdn = [any(pb_parts(m, t, -1)) or any(tri(m, t, -1)) for t in range(n)]
    pup = [any(pb_parts(m, t, 1)) or any(tri(m, t, 1)) for t in range(n)]
    pdn2 = [any(pb_parts(m, t, -1)) for t in range(n)]; pdn3 = [any(tri(m, t, -1)) for t in range(n)]
    pup2 = [any(pb_parts(m, t, 1)) for t in range(n)]; pup3 = [any(tri(m, t, 1)) for t in range(n)]
    seedBar = None
    log = [] if log is None else log
    active = False; bdir = 0; rtype = 0; top = bot = None; left = None; exH = exL = None
    lastClose = None; seedBias = 0
    trend = 0
    u = dict(ext=None, bar=None, lock=False, pbx=None, pbxBar=None)
    d = dict(ext=None, bar=None, lock=False, pbx=None, pbxBar=None)
    key = None
    fbActive = False; fbLevel = None; fbDir = 0; fbDone = None

    def close_box(t, how):
        nonlocal active, lastClose
        log.append((t, 'BOX-CLOSE', how, 'type', rtype, 'dir', bdir, 'left', left, 'top', round(top, 3), 'bot', round(bot, 3)))
        active = False; lastClose = t

    for t in range(n):
        ceil = top if active else None; floor = bot if active else None
        boUp = real_breakout(m, t, ceil, 1); boDn = real_breakout(m, t, floor, -1)
        pbDnExit = pb_exit(m, t, floor, -1); pbUpExit = pb_exit(m, t, ceil, 1)
        leg = seedBias if seedBias != 0 else trend
        seed3Up = seed3Dn = seed12 = False
        if t >= 1:
            after3 = lastClose is None or t - 1 > lastClose
            # escape only when C2 closes beyond the wave extreme (the impulse high/low), else the failed pullback is a range
            waveU = max(H[t-1], u['ext']) if (trend >= 0 and u['ext'] is not None and not u['lock']) else H[t-1]
            waveD = min(L[t-1], d['ext']) if (trend <= 0 and d['ext'] is not None and not d['lock']) else L[t-1]
            seed3Up = leg == 1 and after3 and C[t-1] < O[t-1] and C[t] <= waveU and not pdn[t] and not pdn[t-1]
            seed3Dn = leg == -1 and after3 and C[t-1] > O[t-1] and C[t] >= waveD and not pup[t] and not pup[t-1]
        if t >= 2:
            after12 = lastClose is None or t - 2 > lastClose
            trap = L[t-2] <= C[t-1] <= H[t-2] and L[t-2] <= C[t] <= H[t-2]
            seed12 = trap and after12 and not (pdn[t] or pdn[t-1] or pup[t] or pup[t-1])
        wasActive = active; closedNow = False; cancelDn = cancelUp = False
        if active:
            p2 = pdn2[t] if bdir == 1 else pup2[t]
            p3 = pdn3[t] if bdir == 1 else pup3[t]
            young = (p2 and t - 1 <= seedBar) or (p3 and t - 2 <= seedBar)
            realBO = boUp if bdir == 1 else boDn
            if rtype == 4:
                realPB = boDn if bdir == 1 else boUp
            else:
                realPB = (pbDnExit or boDn) if bdir == 1 else (pbUpExit or boUp)
            cancel = young and rtype != 4
            if realBO:
                close_box(t, 'breakout'); closedNow = True; seedBias = bdir
            elif cancel:
                log.append((t, 'BOX-CANCEL', 'start candles are a real pullback', 'type', rtype, 'left', left))
                active = False; lastClose = t; closedNow = True
                cancelDn = bdir == 1; cancelUp = bdir == -1
            elif realPB:
                close_box(t, 'pullback'); closedNow = True; seedBias = -bdir
            else:
                keep_floor = rtype == 4 and bdir == 1      # FBO up: floor fixed on the CTS line
                keep_ceil = rtype == 4 and bdir == -1      # FBO down: ceiling fixed on the CTS line
                if C[t] > top:
                    exH = H[t] if exH is None else max(exH, H[t])
                elif not keep_ceil:
                    top = max(top, exH if exH is not None else H[t], H[t]); exH = None
                else:
                    exH = None
                if C[t] < bot:
                    exL = L[t] if exL is None else min(exL, L[t])
                elif not keep_floor:
                    bot = min(bot, exL if exL is not None else L[t], L[t]); exL = None
                else:
                    exL = None
        if not wasActive and not closedNow:
            if seed3Up or seed3Dn:
                bdir = 1 if seed3Up else -1; rtype = 3; left = t - 1
                top = max(H[t-1], H[t]); bot = min(L[t-1], L[t]); seedBar = t
                active = True; exH = exL = None
                log.append((t, 'BOX-OPEN', 'type', 3, 'dir', bdir, 'left', left))
            elif seed12:
                bdir = leg if leg != 0 else (1 if C[t-2] >= O[t-2] else -1); rtype = 1; left = t - 2; seedBar = t
                top = max(H[t-2], H[t-1], H[t]); bot = min(L[t-2], L[t-1], L[t])
                active = True; exH = exL = None
                log.append((t, 'BOX-OPEN', 'type', '1/2', 'dir', bdir, 'left', left))
        # ---------------- Structure ----------------
        pbDn = pdn[t] and (not wasActive or pbDnExit or cancelDn)
        pbUp = pup[t] and (not wasActive or pbUpExit or cancelUp)
        fbo4 = active and rtype == 4 and t - left > 2
        ctsUpLvl = (max(u['ext'], top) if (fbo4 and bdir == 1) else u['ext']) if u['lock'] else None
        ctsDnLvl = (min(d['ext'], bot) if (fbo4 and bdir == -1) else d['ext']) if d['lock'] else None
        revDn = real_breakout(m, t, key if trend == 1 else None, -1)
        revUp = real_breakout(m, t, key if trend == -1 else None, 1)
        ctsUp = real_breakout(m, t, ctsUpLvl, 1)
        ctsDn = real_breakout(m, t, ctsDnLvl, -1)
        preLevel = u['ext'] if (trend == 1 and u['lock']) else d['ext'] if (trend == -1 and d['lock']) else None
        preTrend = trend
        sig = 0; tp = trend
        if tp == 1 and revDn:
            sig = -2; trend = -1
            log.append((t, 'TREND->DOWN', 'broken BOS', key))
            if u['pbx'] is None or L[t] < u['pbx']:
                d.update(ext=L[t], bar=t)
            else:
                d.update(ext=u['pbx'], bar=u['pbxBar'])
            d.update(lock=False, pbx=None, pbxBar=None, fake=None); key = u['ext']
        elif tp == -1 and revUp:
            sig = 2; trend = 1
            log.append((t, 'TREND->UP', 'broken BOS', key))
            if d['pbx'] is None or H[t] > d['pbx']:
                u.update(ext=H[t], bar=t)
            else:
                u.update(ext=d['pbx'], bar=d['pbxBar'])
            u.update(lock=False, pbx=None, pbxBar=None, fake=None); key = d['ext']
        else:
            for s, sd, brk, pbflag, ext_px, pb_px in ((u, 1, ctsUp, pbDn, H[t], L[t]), (d, -1, ctsDn, pbUp, L[t], H[t])):
                if not ((sd == 1 and tp >= 0) or (sd == -1 and tp <= 0)):
                    continue
                beyond = (lambda a, b: a > b) if sd == 1 else (lambda a, b: a < b)
                if s['ext'] is None:
                    s.update(ext=ext_px, bar=t); continue
                if s['lock']:
                    if brk:
                        s['fake'] = None
                        sig = sd
                        if trend == 0:
                            trend = sd; log.append((t, 'TREND SET', 'up' if sd == 1 else 'down'))
                        log.append((t, 'CTS-' + ('up' if sd == 1 else 'dn'), round(s['ext'], 3), 'BOS', round(s['pbx'], 3) if s['pbx'] is not None else None))
                        key = s['pbx']
                        s.update(ext=ext_px, bar=t, lock=False, pbx=None, pbxBar=None)
                    elif s.get('fake') is not None and s['pbx'] is not None and beyond(s['pbx'], pb_px):
                        # state 2: fakes beyond the CTS, then the correction breaks the previous pullback
                        log.append((t, 'STATE2', 'CTS moves', round(s['ext'], 3), '->', round(s['fake'], 3)))
                        s.update(ext=s['fake'], bar=s['fakeBar'], pbx=pb_px, pbxBar=t, fake=None, fakeBar=None)
                    else:
                        if s['pbx'] is None or beyond(s['pbx'], pb_px):
                            s.update(pbx=pb_px, pbxBar=t)
                        if beyond(ext_px, s['ext']) and (s.get('fake') is None or beyond(ext_px, s['fake'])):
                            s.update(fake=ext_px, fakeBar=t)
                else:
                    if beyond(ext_px, s['ext']):
                        s.update(ext=ext_px, bar=t, pbx=None, pbxBar=None)
                    elif s['pbx'] is None or beyond(s['pbx'], pb_px):
                        s.update(pbx=pb_px, pbxBar=t)
                    if pbflag:
                        s['lock'] = True; s['fake'] = None
                        if s['pbx'] is None:
                            s.update(pbx=pb_px, pbxBar=t)
                        log.append((t, 'PULLBACK', 'locks', round(s['ext'], 3)))
        # ---------------- FBO (after structure, like the Pine script) ----------------
        if active and rtype == 4 and sig != 0:
            if t - left <= 2:
                log.append((t, 'BOX-DELETE', 'FBO was a real breakout')); active = False
            else:
                close_box(t, 'structure')
        if fbActive and (sig != 0 or preLevel is None or preLevel != fbLevel):
            log.append((t, 'FBO-DELETED')); fbActive = False
        attempt = preLevel is not None and sig == 0 and preLevel != fbDone and (H[t] > preLevel if preTrend == 1 else L[t] < preLevel)
        if attempt and not fbActive:
            fbActive = True; fbLevel = preLevel; fbDir = preTrend
            log.append((t, 'FBO-START', round(fbLevel, 3)))
            if active and rtype != 4:
                close_box(t, 'FBO starts')
            if not active:
                rtype = 4; bdir = fbDir; left = t; exH = exL = None
                if bdir == 1:
                    top = H[t]; bot = fbLevel
                else:
                    top = fbLevel; bot = L[t]
                active = True
                log.append((t, 'BOX-OPEN', 'type', 4, 'dir', bdir, 'left', left, 'top', round(top, 3), 'bot', round(bot, 3)))
        if fbActive and sig == 0 and (C[t] < fbLevel if fbDir == 1 else C[t] > fbLevel):
            fbActive = False; fbDone = fbLevel; log.append((t, 'FBO-CONFIRMED'))
        if sig != 0:
            seedBias = 1 if sig > 0 else -1
    return log
