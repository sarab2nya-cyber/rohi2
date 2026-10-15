# -*- coding: utf-8 -*-
import json, os, numpy as np
import figlib as fl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
from matplotlib.ticker import FuncFormatter
BLUE, ORANGE, GREY, INK = "#1f5fa8", "#c4501b", "#8a8a8a", "#222222"
pf = FuncFormatter(lambda v, _: (("−" if v < 0 else "") + f"{abs(v):.2f}".rstrip("0").rstrip(".")).translate(fl.PD) if abs(v) > 1e-9 else "۰")
def _sig(p): return "∗∗∗" if p < .001 else "∗∗" if p < .01 else "∗" if p < .05 else "ns"
def structural(path, R=None):
    g = fl.Diagram(10.5, 5.8)
    N = lambda k, x, y, t, w=19, h=10: g.node(k, x, y, t, "lat", w=w, h=h, fs=10)
    N("TBP", 11, 40, "فشار بودجهٔ زمانی\nTBP", w=21); N("ECL", 11, 14, "جو اخلاقی سازمان\nECL", w=21)
    N("MD", 47, 27, "رفع تعهد اخلاقی\nMD", w=21); N("SIL", 85, 27, "سکوت دربارهٔ تخلف\nSIL", w=21); N("CON", 47, 52, "وجدان حرفه‌ای\nCON", w=20, h=8.5)
    P = (lambda k: fl.num(R["paths"][k]["beta"]) + " " + _sig(R["paths"][k]["p"])) if R else (lambda k: None)
    g.edge("TBP", "MD", P("MD~TBP"), off=(0, 2.4), fs=9, t=.5); g.edge("ECL", "MD", P("MD~ECL"), off=(0, -2.4), fs=9, t=.5); g.edge("MD", "SIL", P("SIL~MD"), off=(0, 2.4), fs=9, t=.5)
    g.edge("ECL", "SIL", P("SIL~ECL"), rad=.3, off=(0, -3.2), fs=9, anchor_a=(14, 8.6), anchor_b=(82, 21.2))
    g.edge("TBP", "SIL", P("SIL~TBP"), rad=-.17, off=(0, 3.0), fs=9, dashed=True, color="#777", anchor_a=(16, 44.6), anchor_b=(80, 32.5))
    m1 = (29, 33.5); m2 = (66, 27)
    for src, tgt, k, off in [((43, 47.7), m1, "MD~INTT", (-4.5, 0)), ((51, 47.7), (66, 28.2), "SIL~INTM", (4.5, 0))]:
        g.ax.add_patch(FancyArrowPatch(src, tgt, arrowstyle="-|>", mutation_scale=14, lw=1.5, color=ORANGE, linestyle="--", zorder=2))
        if R: g.ax.text((src[0]+tgt[0])/2 + off[0], (src[1]+tgt[1])/2 + off[1], P(k), fontsize=9.5, color=ORANGE, ha="center", va="center", bbox=dict(fc="white", ec="none", pad=1))
    if R:
        for k, (x, y) in {"MD": (47, 20.4), "SIL": (85, 20.4)}.items(): g.ax.text(x, y, "R² = " + fl.num(R["r2"][k]), ha="center", fontsize=9.5)
    g.ax.set_ylim(0, 58); g.save(path)
def slopes(path, R, U):
    sd = R["sd_latent"]["CON"]; xs = np.linspace(-2, 2, 50); fig, axs = plt.subplots(1, 2, figsize=(9.2, 4.0))
    for ax, (dv, x, w, xl, yl) in zip(axs, [("MD", "TBP", "INTT", "فشار بودجهٔ زمانی (واحد پنهان مرکزی‌شده)", "رفع تعهد اخلاقی"), ("SIL", "MD", "INTM", "رفع تعهد اخلاقی (واحد پنهان مرکزی‌شده)", "سکوت دربارهٔ تخلف")]):
        b, wi = U[f"{dv}~{x}"]["b"], U[f"{dv}~{w}"]["b"]
        for k, col, nm in [(-1, ORANGE, "وجدان پایین (۱− انحراف معیار)"), (0, GREY, "وجدان میانگین"), (1, BLUE, "وجدان بالا (۱+ انحراف معیار)")]:
            ax.plot(xs, (b + wi*sd*k)*xs, color=col, lw=2.2, label=fl.fa(f"{nm}: شیب {abs(b+wi*sd*k):.2f}".replace("-", "−")))
        ax.axhline(0, color="#ccc", lw=.8); ax.set_xlabel(fl.fa(xl)); ax.set_ylabel(fl.fa(yl)); ax.xaxis.set_major_formatter(pf); ax.yaxis.set_major_formatter(pf)
        ax.legend(frameon=False, fontsize=8, loc="upper left"); ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout(); fig.savefig(path, dpi=230, facecolor="white"); plt.close(fig)
def forest(path, R):
    IN = R["indirect"]; fig, ax = plt.subplots(figsize=(7.6, 3.9)); y = 0; yt = []; yl = []
    for k, nm in [("TBP_MD_SIL", "فشار زمانی ← رفع تعهد ← سکوت"), ("ECL_MD_SIL", "جو اخلاقی ← رفع تعهد ← سکوت")]:
        for tag, lab, col in [("low", "وجدان پایین", ORANGE), ("mean", "وجدان میانگین", GREY), ("high", "وجدان بالا", BLUE)]:
            v = IN[f"{k}_{tag}"]; ax.plot([v["lo"], v["hi"]], [y, y], color=col, lw=2.4); ax.scatter(v["est"], y, color=col, s=40, zorder=3)
            ax.text(v["hi"] + .01, y, fl.num(v["est"]), fontsize=8.5, va="center"); yt.append(y); yl.append(fl.fa(f"{nm}\n{lab}" if tag == "mean" else lab)); y += 1
        y += .7
    ax.axvline(0, color=INK, lw=.9); ax.set_yticks(yt); ax.set_yticklabels(yl, fontsize=8.5); ax.invert_yaxis(); ax.xaxis.set_major_formatter(pf)
    ax.set_xlabel(fl.fa("اثر غیرمستقیم (غیراستاندارد) و فاصلهٔ اطمینان ۹۵ درصد بوت‌استرپ")); ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout(); fig.savefig(path, dpi=230, facecolor="white"); plt.close(fig)
def build_all(out, R, U):
    structural(os.path.join(out, "fa_fig1.png"), None); structural(os.path.join(out, "fa_fig2.png"), R); slopes(os.path.join(out, "fa_fig3.png"), R, U); forest(os.path.join(out, "fa_fig4.png"), R)
