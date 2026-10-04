# -*- coding: utf-8 -*-
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, FancyBboxPatch, FancyArrowPatch
import arabic_reshaper
from bidi.algorithm import get_display
plt.rcParams["font.family"] = "DejaVu Sans"
PD = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
def fa(s, digits=True):
    out = []
    for line in s.split("\n"):
        t = get_display(arabic_reshaper.reshape(line))
        out.append(t.translate(PD) if digits else t)
    return "\n".join(out)
def num(x, nd=2):
    t = f"{abs(x):.{nd}f}".translate(PD)
    return ("−" if x < 0 else "") + t
def stars(p): return "***" if p < .001 else "**" if p < .01 else "*" if p < .05 else "ns"

class Diagram:
    def __init__(self, w=11, h=5.6):
        self.fig, self.ax = plt.subplots(figsize=(w, h)); self.ax.set_xlim(0, 100); self.ax.set_ylim(0, 56); self.ax.axis("off"); self.pos = {}
    def node(self, key, x, y, label, kind="lat", w=17, h=9, fc="#ffffff", raw=False, fs=11):
        self.pos[key] = (x, y, w, h)
        if kind == "lat": self.ax.add_patch(Ellipse((x, y), w, h, fc=fc, ec="#222", lw=1.4, zorder=3))
        else: self.ax.add_patch(FancyBboxPatch((x-w/2, y-h/2), w, h, boxstyle="round,pad=0.2,rounding_size=0.8", fc=fc, ec="#222", lw=1.4, zorder=3))
        self.ax.text(x, y, label if raw else fa(label, digits=False), ha="center", va="center", fontsize=fs, zorder=4, fontweight="bold")
    def edge(self, a, b, label=None, rad=0.0, lw=1.6, off=(0, 1.8), style="-|>", color="#222", dashed=False, fs=10, anchor_a=None, anchor_b=None):
        xa, ya, wa, ha = self.pos[a]; xb, yb, wb, hb = self.pos[b]
        def edgept(x, y, w, h, tx, ty):
            dx, dy = tx-x, ty-y; s = 1/np.sqrt((dx/(w/2))**2 + (dy/(h/2))**2 + 1e-9); return x+dx*s, y+dy*s
        pa = anchor_a or edgept(xa, ya, wa, ha, xb, yb); pb = anchor_b or edgept(xb, yb, wb, hb, xa, ya)
        ar = FancyArrowPatch(pa, pb, arrowstyle=style, mutation_scale=15, lw=lw, color=color, connectionstyle=f"arc3,rad={rad}", zorder=2, linestyle="--" if dashed else "-")
        self.ax.add_patch(ar)
        if label:
            mx, my = (pa[0]+pb[0])/2 + off[0], (pa[1]+pb[1])/2 + off[1]
            self.ax.text(mx, my, label, ha="center", va="center", fontsize=fs, zorder=5, bbox=dict(fc="white", ec="none", pad=1.2))
    def save(self, path):
        self.fig.tight_layout(); self.fig.savefig(path, dpi=220, bbox_inches="tight", facecolor="white"); plt.close(self.fig)


# ---------------------------------------------------------------- نمودار مدل معادلات ساختاری کامل (گویه‌ها ← متغیر پنهان)
def _ell_pt(x, y, w, h, tx, ty):
    dx, dy = tx - x, ty - y; s = 1/np.sqrt((dx/(w/2))**2 + (dy/(h/2))**2 + 1e-12); return x + dx*s, y + dy*s
def _rect_pt(x, y, w, h, tx, ty):
    dx, dy = tx - x, ty - y
    s = min((w/2)/abs(dx) if dx else 1e9, (h/2)/abs(dy) if dy else 1e9); return x + dx*s, y + dy*s

def add_items(g, key, codes, loads, side, sp=7.4, off=15.0, bw=6.9, bh=3.9, fs=8.5, lab_t=0.55):
    x, y, w, h = g.pos[key]; n = len(codes)
    for i, (c, l) in enumerate(zip(codes, loads)):
        t = i - (n-1)/2
        if side in ("left", "right"):
            bx = x + (-1 if side == "left" else 1)*(w/2 + off); by = y - t*sp
        else:
            bx = x + t*sp; by = y + (1 if side == "top" else -1)*(h/2 + off)
        g.ax.add_patch(plt.Rectangle((bx - bw/2, by - bh/2), bw, bh, fc="#f4f4f4", ec="#222", lw=1.0, zorder=3))
        g.ax.text(bx, by, c.translate(PD), ha="center", va="center", fontsize=fs, zorder=4)
        p0 = _ell_pt(x, y, w, h, bx, by); p1 = _rect_pt(bx, by, bw, bh, p0[0], p0[1])
        g.ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=9, lw=0.9, color="#333", zorder=2))
        mx, my = p0[0] + (p1[0]-p0[0])*lab_t, p0[1] + (p1[1]-p0[1])*lab_t
        g.ax.text(mx, my, num(l, 2), ha="center", va="center", fontsize=fs - 0.5, zorder=5, bbox=dict(fc="white", ec="none", pad=0.6))

def latent_label(fa_name, latin):
    return fa(fa_name, digits=False) + "\n" + latin
