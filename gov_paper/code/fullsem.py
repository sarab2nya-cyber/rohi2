# -*- coding: utf-8 -*-
"""Generic English full SEM diagram: latent ellipses, item boxes with standardized loadings, standardized structural paths, interaction arrows, R²."""
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, Rectangle, FancyArrowPatch
INK, ORANGE, GREY, BLUE = "#222222", "#c4501b", "#8a8a8a", "#1f5fa8"
def star(p): return "***" if p < .001 else "**" if p < .01 else "*" if p < .05 else " ns"
def s2(x): return (f"{x:.2f}".replace("0.", ".", 1) if abs(x) < 1 else f"{x:.2f}").replace("-", "−")
def _ept(n, tx, ty):
    dx, dy = tx-n["x"], ty-n["y"]; s = 1/np.sqrt((dx/(n["w"]/2))**2 + (dy/(n["h"]/2))**2 + 1e-9); return n["x"]+dx*s, n["y"]+dy*s
def _rpt(x, y, w, h, tx, ty):
    dx, dy = tx-x, ty-y; s = min((w/2)/abs(dx) if dx else 1e9, (h/2)/abs(dy) if dy else 1e9); return x+dx*s, y+dy*s
def draw(path, nodes, items, paths, inter, r2, xlim, ylim, figsize, note="", fs=8.6, bw=6.6, bh=3.2, ifs=6.6):
    fig, ax = plt.subplots(figsize=figsize); ax.set_xlim(*xlim); ax.set_ylim(*ylim); ax.axis("off")
    for k, n in nodes.items():
        if n.get("obs"): ax.add_patch(Rectangle((n["x"]-n["w"]/2, n["y"]-n["h"]/2), n["w"], n["h"], fc="#f1f1f1", ec=INK, lw=1.3, zorder=3))
        else: ax.add_patch(Ellipse((n["x"], n["y"]), n["w"], n["h"], fc="white", ec=INK, lw=1.3, zorder=3))
        ax.text(n["x"], n["y"], n["label"], ha="center", va="center", fontsize=fs, fontweight="bold", zorder=4, linespacing=1.1)
    for k, it in items.items():
        n = nodes[k]; side = it["side"]; L = it["loads"]; m = len(L); sp = it.get("sp", bw + 1.0); off = it.get("off", 14.0)
        for i, (code, lam) in enumerate(L):
            t = i - (m-1)/2
            if side in ("left", "right"): bx = n["x"] + (-1 if side == "left" else 1)*(n["w"]/2 + off); by = n["y"] - t*(bh + 1.6)
            else: bx = n["x"] + t*sp; by = n["y"] + (1 if side == "top" else -1)*(n["h"]/2 + off)
            ax.add_patch(Rectangle((bx-bw/2, by-bh/2), bw, bh, fc="#f7f7f7", ec="#555", lw=.9, zorder=3)); ax.text(bx, by, code, ha="center", va="center", fontsize=ifs, zorder=4)
            p0 = _ept(n, bx, by); p1 = _rpt(bx, by, bw, bh, *p0)
            ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=7, lw=.8, color="#666", zorder=2))
            f = .55 if side in ("left", "right") else .5
            ax.text(p0[0]+(p1[0]-p0[0])*f, p0[1]+(p1[1]-p0[1])*f + (.9 if side in ("left", "right") else 0), s2(lam), fontsize=ifs, color="#333", ha="center", va="center", bbox=dict(fc="white", ec="none", pad=.3), zorder=5)
    for a, b_, beta, p, kw in paths:
        na, nb = nodes[a], nodes[b_]; pa = kw.get("pa") or _ept(na, nb["x"], nb["y"]) if not kw.get("pa") else kw["pa"]; pb = kw.get("pb") or _ept(nb, na["x"], na["y"])
        col = kw.get("color", INK)
        ax.add_patch(FancyArrowPatch(pa, pb, arrowstyle="<|-|>" if kw.get("both") else "-|>", mutation_scale=12, lw=kw.get("lw", 1.5), color=col, ls="--" if kw.get("dash") else "-", connectionstyle=f"arc3,rad={kw.get('rad', 0)}", zorder=2))
        t = kw.get("t", .5); off = kw.get("off", (0, 2.0))
        ax.text(pa[0]+(pb[0]-pa[0])*t+off[0], pa[1]+(pb[1]-pa[1])*t+off[1], f"{s2(beta)}{star(p)}", fontsize=fs, color=col, ha="center", va="center", bbox=dict(fc="white", ec="none", pad=.6), zorder=5)
    for row in inter:
        src, tgt, beta, p, off = row[:5]; tt = row[5] if len(row) > 5 else .5
        if isinstance(tgt[0], str):
            na_, nb_ = nodes[tgt[0]], nodes[tgt[1]]; a_ = _ept(na_, nb_['x'], nb_['y']); b_ = _ept(nb_, na_['x'], na_['y']); tgt = ((a_[0]+b_[0])/2, (a_[1]+b_[1])/2)
        s = nodes[src]; pa = _ept(s, *tgt)
        ax.add_patch(FancyArrowPatch(pa, tgt, arrowstyle="-|>", mutation_scale=12, lw=1.4, color=ORANGE, ls="--", zorder=2))
        ax.text(pa[0]+(tgt[0]-pa[0])*tt+off[0], pa[1]+(tgt[1]-pa[1])*tt+off[1], f"{s2(beta)}{star(p)}", fontsize=fs, color=ORANGE, ha="center", va="center", bbox=dict(fc="white", ec="none", pad=.6), zorder=5)
    for k, v in r2.items(): n = nodes[k]; ax.text(n["x"], n["y"]-n["h"]*.30, f"R² = {v:.2f}", ha="center", va="center", fontsize=7.6, color="#444", zorder=5)
    ax.text(xlim[0]+1, ylim[0]+.5, note, fontsize=7.2, color="#333", va="bottom")
    fig.tight_layout(); fig.savefig(path, dpi=250, facecolor="white"); plt.close(fig)
