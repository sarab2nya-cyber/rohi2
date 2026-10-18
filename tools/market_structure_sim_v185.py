"""V18.5 replica: V18.4 + range formation by a mother candle holding the closes of 3 candles with no real pattern; type 3 = impulse candle.

Range types (Range_Box_Prompt_FA.md, section 0):
  1/2 "trapped": any candle whose range (H-L, wicks) holds the CLOSES of the next 2 candles
  3   invalid pullback: after a real move, a counter candle whose next candle does not close
      beyond it in the trend direction, and no real pullback pattern
  4   fake breakout: first candle beyond the pending CTS without a real breakout -> box between
      the CTS line (fixed) and the fake highs, expanding only away from the CTS
Start candles that themselves complete a real pullback (range at most 2 bars old) -> no range,
it is the pullback.
"""
from market_structure_rules_v182 import metrics, tri, real_breakout, pb_parts, pb_exit, forms, EPS


NIN = 3


def run(bars, log=None, fbo_log=None):
    m = metrics(bars); O, H, L, C = m['O'], m['H'], m['L'], m['C']
    n = m['n']
    anypat = [any(pb_parts(m, t, -1)) or any(tri(m, t, -1)) or any(pb_parts(m, t, 1)) or any(tri(m, t, 1)) or real_breakout(m, t, -1e18, 1) or real_breakout(m, t, 1e18, -1) for t in range(n)]
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
        seedN = False; impulse = False
        if t > NIN:
            afterN = lastClose is None or t - NIN > lastClose
            mo = t - NIN
            trap = all(L[mo] <= C[k] <= H[mo] for k in range(mo + 1, t + 1))
            nopat = not any(anypat[k] for k in range(mo + 1, t + 1))
            seedN = trap and nopat and afterN
            impulse = (leg == 1 and C[mo] > O[mo] and C[mo+1] < O[mo+1]) or (leg == -1 and C[mo] < O[mo] and C[mo+1] > O[mo+1])
        wasActive = active; closedNow = False; cancelDn = cancelUp = False
        if active:
            p2 = pdn2[t] if bdir == 1 else pup2[t]
            p3 = pdn3[t] if bdir == 1 else pup3[t]
            young = (p2 and t - 1 <= seedBar) or (p3 and t - 2 <= seedBar)
            realBO = boUp if bdir == 1 else boDn
            if rtype == 4:
                realPB = False                       # V18.4: type 4 closes only by a Real Breakout of its far side
            else:
                realPB = pbDnExit if bdir == 1 else pbUpExit
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
            if seedN:
                mo = t - NIN
                bdir = leg if leg != 0 else (1 if C[mo] >= O[mo] else -1); rtype = 3 if impulse else 1; left = mo; seedBar = t
                top = max(H[mo:t+1]); bot = min(L[mo:t+1])
                active = True; exH = exL = None
                log.append((t, 'BOX-OPEN', 'type', 3 if impulse else '1/2', 'dir', bdir, 'left', left))
        # ---------------- Structure ----------------
        pbDn = (pdn[t] and (not wasActive or cancelDn)) or (wasActive and pbDnExit)
        pbUp = (pup[t] and (not wasActive or cancelUp)) or (wasActive and pbUpExit)
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
