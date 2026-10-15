# -*- coding: utf-8 -*-
"""English figures for the Paper 1 manuscript (conceptual model, standardized path diagram, loadings, simple slopes, indirect-effect forest)."""
import json, os
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, FancyArrowPatch
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
BLUE, ORANGE, GREY, INK = "#1f5fa8", "#c4501b", "#8a8a8a", "#222222"
NAMES = {"COE": "Coercive\npressure", "NOR": "Normative\npressure", "MIM": "Mimetic\npressure", "SUB": "Substantive\nimplementation", "SYM": "Symbolic\ncompliance",
         "USE": "Usefulness of\nreported information", "ACC": "Financial\naccountability", "DIG": "Information-system\nmaturity"}
POS = {"COE": (11, 46), "NOR": (11, 29), "MIM": (11, 12), "SUB": (42, 40), "SYM": (42, 15), "USE": (64, 28), "ACC": (88, 28), "DIG": (41, 53)}
WID = {"COE": 18, "NOR": 18, "MIM": 18, "SUB": 19, "SYM": 19, "USE": 22, "ACC": 19, "DIG": 23}
def star(p): return "***" if p < .001 else "**" if p < .01 else "*" if p < .05 else " ns"
def sgn(x): return f"{x:.2f}".replace("-", "−").replace("0.", ".", 1) if abs(x) < 1 else f"{x:.2f}"
def _ell(ax, k, h=9.5, fs=9.5):
    x, y = POS[k]; w = WID[k]; h = 7.5 if k == "DIG" else h
    ax.add_patch(Ellipse((x, y), w, h, fc="white", ec=INK, lw=1.3, zorder=3)); ax.text(x, y, NAMES[k] + f"\n({k})", ha="center", va="center", fontsize=fs-1.5, fontweight="bold", zorder=4, linespacing=1.15)
def _pt(k, tx, ty):
    x, y = POS[k]; w = WID[k]; h = 7.5 if k == "DIG" else 9.5; dx, dy = tx-x, ty-y; s = 1/np.sqrt((dx/(w/2))**2 + (dy/(h/2))**2 + 1e-9); return x+dx*s, y+dy*s
def _edge(ax, a, b, txt, t=.5, off=(0, 2.2), rad=0, color=INK, dashed=False, anchors=None, fs=8.6, lw=1.5):
    pa, pb = anchors if anchors else (_pt(a, *POS[b]), _pt(b, *POS[a]))
    ax.add_patch(FancyArrowPatch(pa, pb, arrowstyle="-|>", mutation_scale=13, lw=lw, color=color, ls="--" if dashed else "-", connectionstyle=f"arc3,rad={rad}", zorder=2))
    if txt: ax.text(pa[0]+(pb[0]-pa[0])*t+off[0], pa[1]+(pb[1]-pa[1])*t+off[1], txt, fontsize=fs, ha="center", va="center", color=color, bbox=dict(fc="white", ec="none", pad=.8), zorder=5)
def model(path, R=None):
    fig, ax = plt.subplots(figsize=(11.5, 6.4)); ax.set_xlim(0, 100); ax.set_ylim(0, 58); ax.axis("off")
    for k in POS: _ell(ax, k)
    P = (lambda k: f"{sgn(R['paths'][k]['beta'])}{star(R['paths'][k]['p'])}") if R else (lambda k: None)
    spec = [("COE", "SUB", "SUB~COE", .5, (0, 2.3)), ("COE", "SYM", "SYM~COE", .72, (-4.5, 0)), ("NOR", "SUB", "SUB~NOR", .72, (0, -2.4)), ("NOR", "SYM", "SYM~NOR", .45, (0, -2.6)),
            ("MIM", "SYM", "SYM~MIM", .5, (0, -2.4)), ("SUB", "USE", "USE~SUB", .5, (0, 2.2)), ("SYM", "USE", "USE~SYM", .5, (0, -2.4)), ("USE", "ACC", "ACC~USE", .5, (0, 4.2))]
    for a, b, k, t, off in spec: _edge(ax, a, b, P(k), t=t, off=off)
    _edge(ax, "SUB", "ACC", P("ACC~SUB"), rad=-.32, off=(0, 3.2), anchors=((42, 44.8), (86, 32.5))); _edge(ax, "SYM", "ACC", P("ACC~SYM"), rad=.32, off=(0, -3.2), anchors=((42, 10.2), (86, 23.5)))
    m1 = ((POS["SUB"][0]+POS["USE"][0])/2, (POS["SUB"][1]+POS["USE"][1])/2); m2 = ((POS["COE"][0]+POS["SYM"][0])/2, (POS["COE"][1]+POS["SYM"][1])/2)
    for src, tgt, k, off in [((52, 49.2), m1, "USE~INTS", (4.8, 0)), ((34, 49.2), m2, "SYM~INTC", (-4.8, 1.5))]:
        ax.add_patch(FancyArrowPatch(src, tgt, arrowstyle="-|>", mutation_scale=13, lw=1.4, color=ORANGE, ls="--", zorder=2))
        if R: ax.text((src[0]+tgt[0])/2+off[0], (src[1]+tgt[1])/2+off[1], P(k), fontsize=8.6, color=ORANGE, ha="center", va="center", bbox=dict(fc="white", ec="none", pad=.8))
    if R:
        for k, (x, y) in {"SUB": (42, 33.3), "SYM": (42, 8.3), "USE": (64, 20.8), "ACC": (88, 20.8)}.items(): ax.text(x, y, f"R² = {R['r2'][k]:.2f}", ha="center", fontsize=8.6, color="#444")
        ax.text(1, 1.5, "Standardized coefficients (β). * p < .05, ** p < .01, *** p < .001. Dashed orange paths: latent interaction (moderation) terms.\nNon-hypothesised paths (mimetic pressure → substantive implementation; maturity main effects) and the control (experience) are estimated but omitted for clarity.", fontsize=7.6, color="#444", va="bottom")
    fig.tight_layout(); fig.savefig(path, dpi=250, facecolor="white"); plt.close(fig)
def loadings(path, extra):
    L = extra["loadings"]; groups = ["COE", "NOR", "MIM", "SUB", "SYM", "DIG", "USE", "ACC"]
    fig, ax = plt.subplots(figsize=(7.2, 7.6)); y = 0; yt = []; yl = []
    for g in groups:
        its = [k for k in L if k.startswith(g)]
        for k in its:
            ax.plot([0, L[k]], [y, y], color="#c9c9c9", lw=1.2, zorder=1); ax.scatter(L[k], y, s=34, color=BLUE, zorder=3); ax.text(L[k]+.015, y, f"{L[k]:.2f}".replace("0.", ".", 1), va="center", fontsize=8, color="#333")
            yt.append(y); yl.append(k); y += 1
        y += .8
    ax.axvline(.5, color=ORANGE, lw=1, ls="--"); ax.text(.5, -1.1, "0.50", color=ORANGE, ha="center", fontsize=8)
    ax.set_yticks(yt); ax.set_yticklabels(yl, fontsize=8); ax.invert_yaxis(); ax.set_xlim(0, 1); ax.set_xlabel("Standardized factor loading (λ)")
    ax.set_title("Standardized loadings in the full structural model (34 indicators)", fontsize=10, loc="left"); fig.tight_layout(); fig.savefig(path, dpi=250, facecolor="white"); plt.close(fig)
def slopes(path, R, extra):
    U = extra["paths_unstd"]; sd = R["sd_latent"]["DIG"]; xs = np.linspace(-2, 2, 50)
    fig, axs = plt.subplots(1, 2, figsize=(9.6, 3.9), sharey=False)
    for ax, (dv, x, w, lab, ttl) in zip(axs, [("USE", "SUB", "INTS", "Substantive implementation (centred latent units)", "Usefulness of information"), ("SYM", "COE", "INTC", "Coercive pressure (centred latent units)", "Symbolic compliance")]):
        b, wi = U[f"{dv}~{x}"]["b"], U[f"{dv}~{w}"]["b"]
        for k, col, nm in [(-1, ORANGE, "Low maturity (−1 SD)"), (0, GREY, "Mean maturity"), (1, BLUE, "High maturity (+1 SD)")]:
            ax.plot(xs, (b + wi*sd*k)*xs, color=col, lw=2, label=f"{nm}: slope = {b+wi*sd*k:.2f}".replace("-", "−"))
        ax.axhline(0, color="#ccc", lw=.8); ax.set_xlabel(lab); ax.set_ylabel(ttl + " (latent units)"); ax.legend(frameon=False, fontsize=8, loc="upper left" if dv == "USE" else "lower right"); ax.set_title(f"Maturity × {x} → {dv}", fontsize=10, loc="left")
    fig.tight_layout(); fig.savefig(path, dpi=250, facecolor="white"); plt.close(fig)
def forest(path, R):
    IN = R["indirect"]; fig, ax = plt.subplots(figsize=(7.4, 4.3)); y = 0; yt = []; yl = []
    for X_, nm in [("COE", "Coercive pressure"), ("NOR", "Normative pressure"), ("MIM", "Mimetic pressure")]:
        for tag, lab, col in [("low", "Low maturity", ORANGE), ("mean", "Mean maturity", GREY), ("high", "High maturity", BLUE)]:
            v = IN[f"{X_}_tot_{tag}"]; ax.plot([v["lo"], v["hi"]], [y, y], color=col, lw=2.2); ax.scatter(v["est"], y, color=col, s=36, zorder=3)
            yt.append(y); yl.append(f"{nm} – {lab}" if tag == "mean" else lab); y += 1
        y += .7
    ax.axvline(0, color=INK, lw=.9); ax.set_yticks(yt); ax.set_yticklabels(yl, fontsize=8.5); ax.invert_yaxis(); ax.set_xlabel("Total indirect effect on financial accountability (unstandardized, 95% bootstrap CI)")
    fig.tight_layout(); fig.savefig(path, dpi=250, facecolor="white"); plt.close(fig)
def build_all(outdir, R, extra):
    model(os.path.join(outdir, "en_fig1_conceptual.png"), None); model(os.path.join(outdir, "en_fig2_paths.png"), R); loadings(os.path.join(outdir, "en_fig3_loadings.png"), extra)
    slopes(os.path.join(outdir, "en_fig4_slopes.png"), R, extra); forest(os.path.join(outdir, "en_fig5_forest.png"), R)
if __name__ == "__main__":
    O = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output"); R = json.load(open(os.path.join(O, "results_gov.json"))); E = json.load(open(os.path.join(O, "gov_sem_extra.json"))); build_all("/tmp", R, E)
