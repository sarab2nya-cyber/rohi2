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
    def node(self, key, x, y, label, kind="lat", w=17, h=9, fc="#ffffff"):
        self.pos[key] = (x, y, w, h)
        if kind == "lat": self.ax.add_patch(Ellipse((x, y), w, h, fc=fc, ec="#222", lw=1.4, zorder=3))
        else: self.ax.add_patch(FancyBboxPatch((x-w/2, y-h/2), w, h, boxstyle="round,pad=0.2,rounding_size=0.8", fc=fc, ec="#222", lw=1.4, zorder=3))
        self.ax.text(x, y, fa(label, digits=False), ha="center", va="center", fontsize=11, zorder=4, fontweight="bold")
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
