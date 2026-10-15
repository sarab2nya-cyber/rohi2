# -*- coding: utf-8 -*-
import figlib as fl
from matplotlib.patches import FancyArrowPatch
def _sig(p): return "∗∗∗" if p < .001 else "∗∗" if p < .01 else "∗" if p < .05 else "ns"
def _mid(g, a, b):
    xa, ya = g.pos[a][:2]; xb, yb = g.pos[b][:2]; return ((xa+xb)/2, (ya+yb)/2)
def draw(path, R=None):
    g = fl.Diagram(8.4, 5.0)
    N = lambda k, x, y, t, w=19, h=10: g.node(k, x, y, t, "lat", w=w, h=h, fs=10)
    N("COE", 11, 46, "فشار الزامی\nCOE"); N("NOR", 11, 29, "فشار هنجاری\nNOR"); N("MIM", 11, 12, "فشار تقلیدی\nMIM")
    N("SUB", 44, 40, "اجرای ماهوی\nSUB"); N("SYM", 44, 15, "انطباق نمادین\nSYM")
    N("USE", 64, 28, "سودمندی اطلاعات\nUSE", w=22); N("ACC", 88, 28, "پاسخگویی مالی\nACC", w=19)
    N("DIG", 41, 53, "بلوغ نظام اطلاعاتی\nDIG", w=21, h=7.5)
    P = (lambda k: fl.num(R["paths"][k]["beta"]) + " " + _sig(R["paths"][k]["p"])) if R else (lambda k: None)
    pairs = [("COE", "SUB", "SUB~COE"), ("NOR", "SUB", "SUB~NOR"), ("COE", "SYM", "SYM~COE"), ("NOR", "SYM", "SYM~NOR"), ("MIM", "SYM", "SYM~MIM"),
             ("SUB", "USE", "USE~SUB"), ("SYM", "USE", "USE~SYM"), ("USE", "ACC", "ACC~USE")]
    offs = {"SUB~COE": (0, 2.3), "SUB~NOR": (-1, -2.6), "SYM~COE": (-3.5, 2.4), "SYM~NOR": (3, 2.2), "SYM~MIM": (0, -2.4), "USE~SUB": (0, 2.2), "USE~SYM": (0, -2.4), "ACC~USE": (0, 5.5)}
    ts = {"SUB~COE": .5, "SUB~NOR": .72, "SYM~COE": .72, "SYM~NOR": .45, "SYM~MIM": .5, "USE~SUB": .5, "USE~SYM": .5, "ACC~USE": .5}
    offs.update({"SUB~NOR": (0, -2.4), "SYM~COE": (-4.5, 0), "SYM~NOR": (0, -2.6)})
    for a, b, k in pairs: g.edge(a, b, P(k), off=offs[k], fs=10, t=ts[k])
    # direct SUB->ACC and SYM->ACC (curved over/under)
    g.edge("SUB", "ACC", P("ACC~SUB"), rad=-0.32, off=(0, 3.2), fs=10, anchor_a=(44, 44.6), anchor_b=(86, 32.2))
    g.edge("SYM", "ACC", P("ACC~SYM"), rad=0.32, off=(0, -3.2), fs=10, anchor_a=(44, 10.4), anchor_b=(86, 23.8))
    # moderation: DIG -> (SUB->USE) and DIG -> (COE->SYM)
    m1 = _mid(g, "SUB", "USE"); m2 = _mid(g, "COE", "SYM")
    for src, tgt, k, off in [((52, 49.2), m1, "USE~INTS", (4.5, 0)), ((36, 49.2), m2, "SYM~INTC", (-4.5, 1.5))]:
        g.ax.add_patch(FancyArrowPatch(src, tgt, arrowstyle="-|>", mutation_scale=14, lw=1.5, color="#b03a2e", linestyle="--", zorder=2))
        if R: g.ax.text((src[0]+tgt[0])/2 + off[0], (src[1]+tgt[1])/2 + off[1], P(k), fontsize=10, color="#b03a2e", ha="center", va="center", bbox=dict(fc="white", ec="none", pad=1))
    if R:
        for k, (x, y) in {"SUB": (44, 33.4), "SYM": (44, 8.4), "USE": (64, 21), "ACC": (88, 21)}.items():
            g.ax.text(x, y, fl.fa("R² = ", digits=False)[::-1] if False else "R² = " + fl.num(R["r2"][k]), ha="center", fontsize=9.5)
    g.ax.set_ylim(0, 58)
    g.save(path)
if __name__ == "__main__":
    import json, sys
    R = json.load(open("../output/results_gov.json")); draw("/tmp/gov_fig_est.png", R); draw("/tmp/gov_fig_con.png", None)
