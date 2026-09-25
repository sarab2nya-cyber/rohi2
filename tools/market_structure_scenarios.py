import market_structure_sim as sim_ms
class B:
    def __init__(s): s.bars=[]; s.p=100.0
    def c(s,o,cl,up=0.05,dn=0.05,vol=100):
        s.bars.append((o,max(o,cl)+up,min(o,cl)-dn,cl,vol)); s.p=cl; return len(s.bars)-1
    def flat(s,n):
        for i in range(n): s.c(s.p, s.p+(0.1 if i%2 else -0.1),0.3,0.3)
    def maru_to(s,target,n,vol=100):        # strong marubozu leg
        st=(target-s.p)/n
        for i in range(n): s.c(s.p,s.p+st,0.05,0.05,vol)
    def slow_to(s,target,n):                # normal candles (body ~40%), no marubozu, no pullback pattern
        st=(target-s.p)/n
        for i in range(n):
            w=abs(st)*0.75
            s.c(s.p,s.p+st,w,w)
    def pb_down(s,drop=4.5):                # Real Pullback rule 1 (bearish): two bear marubozus, high volume
        a=s.p; s.c(a,a-drop/2,0.05,0.05,400); s.c(a-drop/2,a-drop,0.05,0.05,400)
    def pb_up(s,rise=4.5):
        a=s.p; s.c(a,a+rise/2,0.05,0.05,400); s.c(a+rise/2,a+rise,0.05,0.05,400)
    def chop(s,n,amp=0.6):                  # range: alternating small normal candles
        base=s.p
        for i in range(n):
            o=s.p; cl=base+(amp if i%2==0 else -amp)*0.5
            s.c(o,cl,0.3,0.3)

def show(name,b):
    print('==',name)
    for e in sim_ms.run(b.bars):
        print('   bar',e[0],':',', '.join(str(round(x,2)) if isinstance(x,float) else str(x) for x in e[1:]))

# ---------------- A: image 15 ----------------
b=B(); b.flat(25)
b.maru_to(112,6)                   # impulse 1
b.pb_down(4.5); b.slow_to(106.5,2) # valid pullback -> lock 112.05, low ~106
b.maru_to(120,6)                   # real breakout of 112.05 -> CTS / BOS  (trend set up)
b.pb_down(4.0)                     # valid pullback: lock 120.05
b.slow_to(110,8); b.chop(10)       # long correction + range inside it
b.slow_to(119.5,8); b.c(119.5,119.7,0.8,0.2)   # wick above 120.05 (fake), close below
b.slow_to(113,6)                   # back down, lowest of correction still ~109.x
b.maru_to(126,6)                   # real breakout of 120.05 -> CTS 120.05, BOS = lowest low of whole correction
b.pb_down(4.0); b.slow_to(109.0,8) # valid pullback; dips BELOW previous BOS slowly (fake break, no rule)
b.maru_to(132,8)                   # real breakout of 126.05 -> trend still up, BOS = new lower low
show('A (image 15): long correction, fake above CTS, fake below BOS',b)

# ---------------- B: image 16 reversal ----------------
b=B(); b.flat(25)
b.maru_to(112,6); b.pb_down(4.5); b.slow_to(106.5,2)
b.maru_to(120,6)                   # CTS 112.05, BOS ~106 (key level K)
b.pb_down(3.0); b.slow_to(114,3)   # valid pullback, low ~114
b.maru_to(128,6)                   # CTS 120.05, BOS ~113.9  -> K
b.slow_to(129,3)                   # top A ~129.x
b.chop(8)                          # range at the top, no pullback
b.maru_to(105,4)                   # bear marubozus (normal volume): two closes below K -> TREND DOWN
b.slow_to(103,3)                   # L1 ~102.x
b.pb_up(4.0); b.slow_to(109,2)     # valid bullish pullback up to B ~109.x
b.maru_to(94,6)                    # real breakout below L1 -> CTS L1, BOS B
b.chop(8); b.maru_to(86,5)         # range in the down leg, broken down without pullback -> nothing
b.slow_to(108.5,14); b.c(108.5,109.2,1.9,0.3)   # rally, wick above B (fake), no real breakout
b.slow_to(103,5)
show('B (image 16): reversal, CTS/BOS in the downtrend, fake above BOS',b)

# ---------------- C: reversal before any pullback ----------------
b=B(); b.flat(25)
b.maru_to(112,6); b.pb_down(4.5); b.slow_to(106.5,2)
b.maru_to(120,6)                   # CTS 112.05, BOS ~106 (K)
b.maru_to(124,3)                   # impulse continues, NO pullback (phase A)
b.maru_to(100,6)                   # bear marubozus, normal volume: not a pullback, but real breakout of K
b.slow_to(98,3)
show('C: trend reversal before a pullback',b)

# ---------------- D: chart start + range continuation without pullback ----------------
b=B(); b.flat(25)
b.slow_to(108,10); b.chop(8); b.maru_to(118,5)   # rally, range, continuation - no pullback anywhere
b.slow_to(125,8)
b.pb_down(4.0); b.slow_to(118,3)                 # first valid pullback
b.maru_to(131,6)                                 # first real breakout of the locked high -> trend set
show('D: chart start, range continuation without pullback',b)
