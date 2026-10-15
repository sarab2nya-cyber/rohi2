# -*- coding: utf-8 -*-
import json, os, numpy as np
import figlib as fl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Ellipse
from matplotlib.ticker import FuncFormatter
BLUE, ORANGE, GREY, INK = "#1f5fa8", "#c4501b", "#8a8a8a", "#222222"
PD = fl.PD
pf = FuncFormatter(lambda v, _: ("−" if v < 0 else "") + f"{abs(v):.2f}".rstrip("0").rstrip(".").translate(PD) if abs(v) > 1e-9 else "۰")
def _sig(p): return "∗∗∗" if p < .001 else "∗∗" if p < .01 else "∗" if p < .05 else "ns"
def structural(path, R=None):
    g = fl.Diagram(10.5, 5.6)
    N = lambda k, x, y, t, w=19, h=10: g.node(k, x, y, t, "lat", w=w, h=h, fs=10)
    N("COE", 11, 42, "فشار الزامی\nCOE"); N("NOR", 11, 28, "فشار هنجاری\nNOR"); N("MIM", 11, 14, "فشار تقلیدی\nMIM")
    N("SUB", 66, 38, "اجرای ماهوی\nSUB", w=20); N("SYM", 66, 16, "انطباق نمادین\nSYM", w=20)
    N("INCN", 38, 53, "COE × NOR", w=15, h=6.5); N("INCM", 38, 3.5, "COE × MIM", w=15, h=6.5)
    P = (lambda k: fl.num(R["paths"][k]["beta"]) + " " + _sig(R["paths"][k]["p"])) if R else (lambda k: None)
    ts = {"SUB~COE": (.5, (0, 2.4)), "SUB~NOR": (.6, (0, 2.4)), "SUB~MIM": (.86, (0, -2.6)), "SYM~COE": (.8, (3.5, 2.4)), "SYM~NOR": (.5, (0, -2.6)), "SYM~MIM": (.5, (0, -2.4))}
    for k, (t, off) in ts.items():
        dv, iv = k.split("~"); g.edge(iv, dv, P(k), off=off, fs=9, t=t, dashed=(k == "SUB~MIM"), color="#777" if k == "SUB~MIM" else INK)
    g.edge("INCN", "SUB", P("SUB~INCN"), off=(0, 2.2), fs=9, color=ORANGE, dashed=True); g.edge("INCM", "SYM", P("SYM~INCM"), off=(0, -2.2), fs=9, color=ORANGE, dashed=True)
    g.ax.add_patch(FancyArrowPatch((76, 33.2), (76, 20.8), arrowstyle="<|-|>", mutation_scale=13, lw=1.4, color=INK, connectionstyle="arc3,rad=-0.55", zorder=2))
    if R: g.ax.text(90.5, 27, fl.num(R["resid_cov"]["beta"]) + " " + _sig(R["resid_cov"]["p"]), fontsize=9, ha="center", va="center", bbox=dict(fc="white", ec="none", pad=1))
    if R:
        for k, (x, y) in {"SUB": (66, 31.2), "SYM": (66, 9.2)}.items(): g.ax.text(x, y, "R² = " + fl.num(R["r2"][k]), ha="center", fontsize=9.5)
    g.ax.set_ylim(-1, 58); g.save(path)
def conditional(path, R):
    C = R["cond"]; fig, axs = plt.subplots(2, 2, figsize=(8.4, 6.2))
    specs = [("COE_SUB_atNOR", "اثر فشار الزامی بر اجرای ماهوی\nبه تفکیک سطح فشار هنجاری"), ("NOR_SUB_atCOE", "اثر فشار هنجاری بر اجرای ماهوی\nبه تفکیک سطح فشار الزامی"),
             ("COE_SYM_atMIM", "اثر فشار الزامی بر انطباق نمادین\nبه تفکیک سطح فشار تقلیدی"), ("MIM_SYM_atCOE", "اثر فشار تقلیدی بر انطباق نمادین\nبه تفکیک سطح فشار الزامی")]
    lv = [("low", "پایین\n(−۱ انحراف معیار)", ORANGE), ("mean", "میانگین", GREY), ("high", "بالا\n(+۱ انحراف معیار)", BLUE)]
    for ax, (k, ttl) in zip(axs.ravel(), specs):
        for i, (t, lab, col) in enumerate(lv):
            v = C[f"{k}_{t}"]; ax.plot([i, i], [v["lo"], v["hi"]], color=col, lw=2.4); ax.scatter(i, v["est"], color=col, s=46, zorder=3)
            ax.text(i + .12, v["est"], fl.num(v["est"]), fontsize=8.5, va="center")
        ax.axhline(0, color=INK, lw=.8); ax.set_xticks(range(3)); ax.set_xticklabels([fl.fa(l, digits=True) for _, l, _ in lv], fontsize=8); ax.yaxis.set_major_formatter(pf)
        ax.set_title(fl.fa(ttl, digits=False), fontsize=9.5); ax.spines[["top", "right"]].set_visible(False); ax.set_xlim(-.4, 2.6)
    fig.tight_layout(); fig.savefig(path, dpi=230, facecolor="white"); plt.close(fig)
def profiles(path, R):
    P = R["profiles"]; order = ["COE", "NOR", "MIM", "SUB", "SYM"]; nm = {"COE": "فشار الزامی", "NOR": "فشار هنجاری", "MIM": "فشار تقلیدی", "SUB": "اجرای ماهوی", "SYM": "انطباق نمادین"}
    fig, ax = plt.subplots(figsize=(8.4, 4.4)); w = .8/len(P); cols = [BLUE, ORANGE, GREY, "#5b8f3c"]
    names = {0: "نیمرخ الف", 1: "نیمرخ ب"}
    for i, p in enumerate(P):
        xs = np.arange(len(order)) + i*w - .4 + w/2; ys = [p[v] for v in order]
        ax.bar(xs, ys, w*.92, color=cols[i], label=fl.fa(f"نیمرخ {['الف','ب','پ','ت'][i]} ({p['pct']:.0f} درصد)"))
        for x_, y_ in zip(xs, ys): ax.text(x_, y_ + (.04 if y_ >= 0 else -.04), fl.num(y_), ha="center", va="bottom" if y_ >= 0 else "top", fontsize=8)
    ax.axhline(0, color=INK, lw=.8); ax.set_xticks(range(len(order))); ax.set_xticklabels([fl.fa(nm[v]) for v in order], fontsize=9.5); ax.yaxis.set_major_formatter(pf)
    ax.set_ylabel(fl.fa("میانگین نمرهٔ عاملی استاندارد")); ax.legend(frameon=False, fontsize=9); ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout(); fig.savefig(path, dpi=230, facecolor="white"); plt.close(fig)
def groups(path, R):
    G = R["group_paths"]; keys = [("SUB~COE", "فشار الزامی ← اجرای ماهوی"), ("SUB~NOR", "فشار هنجاری ← اجرای ماهوی"), ("SUB~MIM", "فشار تقلیدی ← اجرای ماهوی"), ("SYM~COE", "فشار الزامی ← انطباق نمادین"), ("SYM~NOR", "فشار هنجاری ← انطباق نمادین"), ("SYM~MIM", "فشار تقلیدی ← انطباق نمادین")]
    fig, ax = plt.subplots(figsize=(8.4, 4.3))
    for i, (k, lab) in enumerate(keys):
        for j, (g, col, off, nm) in enumerate([("g0", BLUE, .13, "نهادهای اداری و حاکمیتی"), ("g1", ORANGE, -.13, "نهادهای خدماتی و محلی")]):
            v = G[g][k]; y = i + off; ax.plot([v["beta"] - 1.96*v["se"]*.97, v["beta"] + 1.96*v["se"]*.97], [y, y], color=col, lw=2.2); ax.scatter(v["beta"], y, color=col, s=36, zorder=3, label=fl.fa(nm) if i == 0 else None)
    ax.axvline(0, color=INK, lw=.8); ax.set_yticks(range(len(keys))); ax.set_yticklabels([fl.fa(l) for _, l in keys], fontsize=9); ax.invert_yaxis(); ax.xaxis.set_major_formatter(pf)
    ax.set_xlabel(fl.fa("ضریب مسیر استاندارد (فاصلهٔ اطمینان تقریبی ۹۵ درصد)")); ax.legend(frameon=False, fontsize=9, loc="lower right"); ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout(); fig.savefig(path, dpi=230, facecolor="white"); plt.close(fig)
def build_all(out, R):
    structural(os.path.join(out, "fa2_fig1.png"), None); structural(os.path.join(out, "fa2_fig2.png"), R); conditional(os.path.join(out, "fa2_fig3.png"), R); profiles(os.path.join(out, "fa2_fig4.png"), R); groups(os.path.join(out, "fa2_fig5.png"), R)
if __name__ == "__main__":
    O = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "paper2", "output"); R = json.load(open(os.path.join(O, "results_gov2.json"))); build_all("/tmp", R)
