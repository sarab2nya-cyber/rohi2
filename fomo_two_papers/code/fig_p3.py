# -*- coding: utf-8 -*-
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, Rectangle, FancyArrowPatch

def f2(x): return f"{x:.2f}".replace("0.", ".", 1).replace("-0.", "−.") if abs(x) < 1 else f"{x:.2f}"
def star(p): return "***" if p < .001 else "**" if p < .01 else "*" if p < .05 else ""

def sem_fig(R, path):
    P, L, rel, r2 = R["paths"], R["loadings"], R["rel"], R["r2"]
    fig, ax = plt.subplots(figsize=(13, 8.2)); ax.set_xlim(0, 13); ax.set_ylim(-0.6, 8.2); ax.axis("off")
    pos = {"GUI": (1.7, 4.1), "PCA": (6.0, 6.7), "CGz": (6.0, 4.9), "UR": (6.0, 3.3), "VER": (6.0, 1.5), "IDQ": (11.2, 4.1)}
    name = {"GUI": "Generative-AI use\n(GUI)", "PCA": "Perceived competence\nwith AI (PCA)", "UR": "Uncritical reliance\n(UR)", "VER": "Verification\n(VER)", "IDQ": "Investment decision\nquality (IDQ)", "CGz": "Calibration gap\n(CG, observed)"}
    def node(k, w=2.5, h=1.0, obs=False):
        x, y = pos[k]
        if obs: ax.add_patch(Rectangle((x-w/2, y-h/2), w, h, fc="#f3f3f3", ec="black", lw=1.4))
        else: ax.add_patch(Ellipse((x, y), w, h*1.1, fc="white", ec="black", lw=1.4))
        ax.text(x, y, name[k], ha="center", va="center", fontsize=9.5, fontweight="bold")
        if k in rel:
            keys = [c for c in L if c.startswith(k) and c[len(k):].isdigit()]
            ls = [L[c] for c in keys]
            ax.text(x, y-h*.72, f"{k}1–{k}{len(keys)}: λ = {min(ls):.2f}–{max(ls):.2f}; CR = {rel[k]['cr']:.2f}", ha="center", va="top", fontsize=7.2, color="#444")
    for k in pos: node(k, obs=(k == "CGz"))
    # exogenous moderators (observed/latent)
    ax.add_patch(Rectangle((0.5, 6.9), 2.4, .8, fc="#f3f3f3", ec="black", lw=1.4)); ax.text(1.7, 7.3, "Financial knowledge\n(FKz, test score)", ha="center", va="center", fontsize=9, fontweight="bold")
    ax.add_patch(Ellipse((1.7, 1.2), 2.4, .95, fc="white", ec="black", lw=1.4)); ax.text(1.7, 1.2, "AI literacy (AIL)", ha="center", va="center", fontsize=9.5, fontweight="bold")
    ax.text(1.7, .55, f"AIL1–AIL6: λ = {min(L[f'AIL{i}'] for i in range(1,7)):.2f}–{max(L[f'AIL{i}'] for i in range(1,7)):.2f}; CR = {rel['AIL']['cr']:.2f}", ha="center", fontsize=7.2, color="#444")
    def arr(a, b, txt=None, lo=(0, 0), dash=False, color="black", lw=1.4, t=.5, off=(0, .14), fs=8.6):
        ar = FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=13, lw=lw, color=color, ls="--" if dash else "-", shrinkA=0, shrinkB=0); ax.add_patch(ar)
        if txt: ax.text(a[0]+(b[0]-a[0])*t+off[0], a[1]+(b[1]-a[1])*t+off[1], txt, ha="center", va="center", fontsize=fs, color=color, bbox=dict(fc="white", ec="none", pad=.6, alpha=.85))
    lab = lambda key: f"{f2(P[key]['beta'])}{star(P[key]['p'])}"
    X0 = pos["GUI"][0]+1.25; XM = pos["PCA"][0]-1.25; XR = pos["IDQ"][0]-1.25
    for k, y in [("PCA", 6.7), ("CGz", 4.9), ("UR", 3.3), ("VER", 1.5)]:
        arr((X0, pos["GUI"][1]+(y-pos["GUI"][1])*.18), (XM, y), lab(f"{k}~GUI"), t=.5, off=(0, .17))
        arr((XM+2.5, y) if False else (pos[k][0]+1.25, y), (XR, pos["IDQ"][1]+(y-pos["IDQ"][1])*.2), lab(f"IDQ~{k}"), t=.5, off=(0, .17))
    # moderation: FK -> PCA and CG paths ; AIL -> UR and VER paths
    for k, y, (src, srcpos, key) in [("PCA", 6.7, ("FK", (2.9, 7.3), "PCA~INTF")), ("CGz", 4.9, ("FK", (2.9, 7.1), "CGz~INTF")), ("UR", 3.3, ("AIL", (2.9, 1.35), "UR~INTA")), ("VER", 1.5, ("AIL", (2.9, 1.1), "VER~INTA"))]:
        tgt = (X0+(XM-X0)*.5, pos["GUI"][1]+(y-pos["GUI"][1])*.18+(y-pos["GUI"][1]*.82-pos["GUI"][1]*.18*0)*0)
        gy = pos["GUI"][1]+(y-pos["GUI"][1])*.18; mid = (X0+(XM-X0)*.5, gy+(y-gy)*.5)
        arr(srcpos, mid, f"{f2(P[key]['beta'])}{star(P[key]['p'])}", dash=True, color="#b03a2e", t=.45, off=(0, .12), fs=8)
    # direct path: curved below the mediators
    ar = FancyArrowPatch((pos["GUI"][0], pos["GUI"][1]-.62), (pos["IDQ"][0], pos["IDQ"][1]-.62), connectionstyle="arc3,rad=0.28", arrowstyle="-|>", mutation_scale=13, lw=1.4, color="#555"); ax.add_patch(ar)
    ax.text(6.45, 0.22, f"direct effect c\u2032 (GUI \u2192 IDQ) = {lab('IDQ~GUI')}", ha="center", fontsize=8.6, color="#555", bbox=dict(fc="white", ec="none", pad=.6))
    # FK, AIL direct to IDQ not drawn (controls); note
    ax.text(0.2, -0.25, "Solid = structural paths (standardized β); red dashed = latent/observed interaction (moderation) paths. *p<.05  **p<.01  ***p<.001.\n"
            "Controls on IDQ (FKz, AIL, experience, age, gender) and covariances among exogenous variables are estimated but omitted for clarity.", fontsize=7.6, color="#333", va="bottom")
    ax.text(11.2, 3.0, f"R² = {r2['IDQ']:.2f}", ha="center", fontsize=8.6)
    for k, y in [("PCA", 7.35), ("UR", 3.95), ("VER", 2.15)]: ax.text(pos[k][0]+1.45, y, f"R² = {r2[k]:.2f}", fontsize=8.6)
    ax.text(pos["CGz"][0]+1.45, 5.5, f"R² = {r2['CGz']:.2f}", fontsize=8.6)
    fig.tight_layout(); fig.savefig(path, dpi=220); plt.close(fig)
