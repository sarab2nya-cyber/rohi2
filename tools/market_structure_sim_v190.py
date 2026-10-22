"""V19.0 replica of the Pine script (final prompt). Order of events on every bar (section 4-2):
1 structure (CTS / trend change), 2 start-candle exception, 3 FBO, 4 active box (expansion / end),
5 range start (type 3 first, else type 1/2 window of 3-5 candles with a Big Marubozu / Big Pin Bar
anchor). Range exit pullback = one of the 6 patterns against the leg with line = boundary.
The Hide display option (default off) is not modelled."""
from market_structure_rules_v190 import metrics, tri, real_breakout, pb_parts, EPS


def run(bars, log=None):
    m = metrics(bars); O, H, L, C = m['O'], m['H'], m['L'], m['C']
    n = m['n']; big = m['big']; bigpin = m['bigpin']
    pdn = [any(pb_parts(m, t, -1)) or any(tri(m, t, -1)) for t in range(n)]
    pup = [any(pb_parts(m, t, 1)) or any(tri(m, t, 1)) for t in range(n)]
    pdn2 = [any(pb_parts(m, t, -1)) for t in range(n)]; pdn3 = [any(tri(m, t, -1)) for t in range(n)]
    pup2 = [any(pb_parts(m, t, 1)) for t in range(n)]; pup3 = [any(tri(m, t, 1)) for t in range(n)]
    log = [] if log is None else log
    st = dict(active=False, dir=0, type=0, top=None, bot=None, left=None, exH=None, exL=None, seedBar=None)
    lastClose = None; seedBias = 0; trend = 0
    u = dict(ext=None, bar=None, lock=False, pbx=None, pbxBar=None, fake=None, fakeBar=None)
    d = dict(ext=None, bar=None, lock=False, pbx=None, pbxBar=None, fake=None, fakeBar=None)
    key = None
    fbActive = False; fbLevel = None; fbDir = 0; fbDone = None

    def end_box(t, how, ev='BOX-CLOSE'):
        nonlocal lastClose
        log.append((t, ev, how, 'type', st['type'], 'dir', st['dir'], 'left', st['left'], 'top', round(st['top'], 3), 'bot', round(st['bot'], 3)))
        st.update(active=False, dir=0, type=0, exH=None, exL=None); lastClose = t

    for t in range(n):
        # ---- frozen state at the start of the bar ----
        act0 = st['active']; typ0 = st['type']; dir0 = st['dir']
        ceil = st['top'] if act0 else None; floor = st['bot'] if act0 else None
        boUp = real_breakout(m, t, ceil, 1); boDn = real_breakout(m, t, floor, -1)
        pbDnExit = act0 and typ0 != 4 and dir0 == 1 and boDn
        pbUpExit = act0 and typ0 != 4 and dir0 == -1 and boUp
        sb = st['seedBar']
        startDn = (pdn2[t] and sb is not None and t - 1 <= sb) or (pdn3[t] and sb is not None and t - 2 <= sb)
        startUp = (pup2[t] and sb is not None and t - 1 <= sb) or (pup3[t] and sb is not None and t - 2 <= sb)
        cancelNow = act0 and typ0 != 4 and (startDn if dir0 == 1 else startUp)
        cancelDn = cancelNow and dir0 == 1; cancelUp = cancelNow and dir0 == -1
        waveU = max(H[t-1], u['ext']) if (t >= 1 and trend >= 0 and u['ext'] is not None and not u['lock']) else (H[t-1] if t >= 1 else H[t])
        waveD = min(L[t-1], d['ext']) if (t >= 1 and trend <= 0 and d['ext'] is not None and not d['lock']) else (L[t-1] if t >= 1 else L[t])
        # ---- STEP 1: structure ----
        pbDn = (pdn[t] and (not act0 or cancelDn)) or pbDnExit
        pbUp = (pup[t] and (not act0 or cancelUp)) or pbUpExit
        fboOld = act0 and typ0 == 4 and t - st['left'] >= 2
        ctsUpLvl = (max(u['ext'], st['top']) if (fboOld and dir0 == 1) else u['ext']) if u['lock'] else None
        ctsDnLvl = (min(d['ext'], st['bot']) if (fboOld and dir0 == -1) else d['ext']) if d['lock'] else None
        revDn = real_breakout(m, t, key if trend == 1 else None, -1)
        revUp = real_breakout(m, t, key if trend == -1 else None, 1)
        ctsUp = real_breakout(m, t, ctsUpLvl, 1); ctsDn = real_breakout(m, t, ctsDnLvl, -1)
        preLevel = u['ext'] if (trend == 1 and u['lock']) else d['ext'] if (trend == -1 and d['lock']) else None
        preTrend = trend
        sig = 0; tp = trend
        if tp == 1 and revDn:
            sig = -2; trend = -1; log.append((t, 'TREND->DOWN', 'broken BOS', key))
            if u['pbx'] is None or L[t] < u['pbx']:
                d.update(ext=L[t], bar=t)
            else:
                d.update(ext=u['pbx'], bar=u['pbxBar'])
            d.update(lock=False, pbx=None, pbxBar=None, fake=None); key = u['ext']
        elif tp == -1 and revUp:
            sig = 2; trend = 1; log.append((t, 'TREND->UP', 'broken BOS', key))
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
                        s['fake'] = None; sig = sd
                        if trend == 0:
                            trend = sd; log.append((t, 'TREND SET', 'up' if sd == 1 else 'down'))
                        log.append((t, 'CTS-' + ('up' if sd == 1 else 'dn'), round(s['ext'], 3), 'BOS', round(s['pbx'], 3) if s['pbx'] is not None else None))
                        key = s['pbx']; s.update(ext=ext_px, bar=t, lock=False, pbx=None, pbxBar=None)
                    elif s['fake'] is not None and s['pbx'] is not None and beyond(s['pbx'], pb_px):
                        log.append((t, 'STATE2', 'CTS moves', round(s['ext'], 3), '->', round(s['fake'], 3)))
                        s.update(ext=s['fake'], bar=s['fakeBar'], pbx=pb_px, pbxBar=t, fake=None, fakeBar=None)
                    else:
                        if s['pbx'] is None or beyond(s['pbx'], pb_px):
                            s.update(pbx=pb_px, pbxBar=t)
                        if beyond(ext_px, s['ext']) and (s['fake'] is None or beyond(ext_px, s['fake'])):
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
        # ---- STEP 2: start-candle exception ----
        if cancelNow and st['active'] and st['type'] != 4:
            end_box(t, 'start candles are a real pullback', 'BOX-CANCEL')
        # ---- STEP 3: FBO ----
        boxNew = False
        if st['active'] and st['type'] == 4 and sig != 0:
            if t - st['left'] <= 1 or fbActive:
                end_box(t, 'FBO was not fake', 'BOX-DELETE')
            else:
                end_box(t, 'structure')
        if fbActive and (sig != 0 or preLevel is None or preLevel != fbLevel):
            log.append((t, 'FBO-DELETED')); fbActive = False
        attempt = preLevel is not None and sig == 0 and preLevel != fbDone and (H[t] > preLevel if preTrend == 1 else L[t] < preLevel)
        if attempt and not fbActive:
            fbActive = True; fbLevel = preLevel; fbDir = preTrend
            log.append((t, 'FBO-START', round(fbLevel, 3)))
            if st['active'] and st['type'] != 4:
                end_box(t, 'FBO starts')
            if not st['active']:
                st.update(active=True, type=4, dir=fbDir, left=t, exH=None, exL=None,
                          top=H[t] if fbDir == 1 else fbLevel, bot=fbLevel if fbDir == 1 else L[t])
                boxNew = True
                log.append((t, 'BOX-OPEN', 'type', 4, 'dir', fbDir, 'left', t, 'top', round(st['top'], 3), 'bot', round(st['bot'], 3)))
        if fbActive and sig == 0 and (C[t] < fbLevel if fbDir == 1 else C[t] > fbLevel):
            fbActive = False; fbDone = fbLevel; log.append((t, 'FBO-CONFIRMED'))
        # ---- STEP 4: active box ----
        if st['active'] and act0 and not boxNew:
            bdir = st['dir']
            realBO = boUp if bdir == 1 else boDn
            realPB = (boDn if bdir == 1 else boUp) if st['type'] == 4 else (pbDnExit if bdir == 1 else pbUpExit)
            if realBO:
                end_box(t, 'breakout'); seedBias = bdir
            elif realPB:
                end_box(t, 'pullback'); seedBias = -bdir
            else:
                keep_floor = st['type'] == 4 and bdir == 1
                keep_ceil = st['type'] == 4 and bdir == -1
                if C[t] > st['top']:
                    st['exH'] = H[t] if st['exH'] is None else max(st['exH'], H[t])
                else:
                    if not keep_ceil:
                        st['top'] = max(st['top'], st['exH'] if st['exH'] is not None else H[t], H[t])
                    st['exH'] = None
                if C[t] < st['bot']:
                    st['exL'] = L[t] if st['exL'] is None else min(st['exL'], L[t])
                else:
                    if not keep_floor:
                        st['bot'] = min(st['bot'], st['exL'] if st['exL'] is not None else L[t], L[t])
                    st['exL'] = None
        if sig != 0:
            seedBias = 1 if sig > 0 else -1
        # ---- STEP 5: range start ----
        if not st['active'] and t >= 1:
            leg = seedBias if seedBias != 0 else trend
            c1After = lastClose is None or t - 1 > lastClose
            noPbUp = not pdn[t] and not pdn[t-1]; noPbDn = not pup[t] and not pup[t-1]
            s3u = leg == 1 and c1After and C[t-1] < O[t-1] and C[t] <= waveU and noPbUp
            s3d = leg == -1 and c1After and C[t-1] > O[t-1] and C[t] >= waveD and noPbDn
            if s3u or s3d:
                st.update(active=True, type=3, dir=1 if s3u else -1, left=t-1, seedBar=t, exH=None, exL=None,
                          top=max(H[t-1], H[t]), bot=min(L[t-1], L[t]))
                log.append((t, 'BOX-OPEN', 'type', 3, 'dir', st['dir'], 'left', t - 1))
            elif noPbUp and noPbDn:
                found = None
                for W in (5, 4, 3):
                    f = t - (W - 1)
                    if f < 0 or not (lastClose is None or f > lastClose):
                        continue
                    for a in range(f, t):                     # anchor: any window candle but the last
                        if big[a] or bigpin[a]:
                            if all(L[a] <= C[k] <= H[a] for k in range(f, t + 1) if k != a):
                                found = (W, a); break
                    if found:
                        break
                if found:
                    W, a = found; f = t - (W - 1)
                    st.update(active=True, type=2 if not big[a] else 1, dir=leg if leg != 0 else (1 if C[a] >= O[a] else -1),
                              left=f, seedBar=t, exH=None, exL=None, top=max(H[f:t+1]), bot=min(L[f:t+1]))
                    log.append((t, 'BOX-OPEN', 'type', st['type'], 'dir', st['dir'], 'left', f, 'anchor', a))
    return log
