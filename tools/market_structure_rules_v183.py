"""V18.3: the range-exit Real Pullback is ALSO any of the 6 Real Pullback patterns breaking the
current (expanded) box boundary - rule 1: both closes beyond, rules 2/3: C1 closes beyond,
3-candle patterns: tri_level. The V18.2 rule (Marubozu >= 50% out + C2 beyond C1) stays."""
import market_structure_rules_v182 as R
from market_structure_rules_v182 import metrics, forms, tri, real_breakout, pb_parts, tri_level, EPS


def pb_exit(m, t, level, d):
    if level is None or t < 1:
        return False
    r1, r2, r3 = pb_parts(m, t, d)
    C = m['C']
    beyond = (lambda x: x < level) if d == -1 else (lambda x: x > level)
    six = (r1 and beyond(C[t-1]) and beyond(C[t])) or ((r2 or r3) and beyond(C[t-1])) or tri_level(m, t, level, d)
    return R.pb_exit(m, t, level, d) or six
