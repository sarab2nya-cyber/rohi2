# -*- coding: utf-8 -*-
"""نمودارهای کامل مدل معادلات ساختاری (گویه‌ها ← متغیر پنهان) برای دو مقاله"""
import figlib as fl
from figlib import Diagram, add_items, latent_label
def sig(p): return "∗∗∗" if p < .001 else "∗∗" if p < .01 else "∗" if p < .05 else "ns"
def lab(P, k): return fl.num(P[k]["beta"]) + " " + sig(P[k]["p"])

def sem_paper1(path, R, conceptual=False):
    P, Ld = R["paths"], R["sem_loadings"]
    g = Diagram(11.5, 8.0); g.ax.set_xlim(0, 100); g.ax.set_ylim(0, 70)
    NM = {"SME": ("مواجهه با محتوای\nشبکه‌های اجتماعی", "SME"), "FOMO": ("فومو", "FOMO"), "HRD": ("رفتار توده‌وار", "HRD"), "IDQ": ("کیفیت تصمیم\nسرمایه‌گذاری", "IDQ"), "AIU": ("استفاده از اطلاعات\nحسابداری", "AIU")}
    pos = {"SME": (20, 46, 15, 12), "FOMO": (41, 46, 13, 11), "HRD": (62, 46, 15, 11), "IDQ": (82, 46, 14, 12), "AIU": (76, 17, 17, 11)}
    for k, (x, y, w, h) in pos.items():
        g.node(k, x, y, latent_label(*NM[k]), w=w, h=h, raw=True, fs=9.5)
    cnt = {"SME": 5, "FOMO": 6, "HRD": 5, "IDQ": 5, "AIU": 5}
    codes = lambda k: [f"{k}{i}" for i in range(1, cnt[k] + 1)]
    ld = lambda k: [Ld[c] for c in codes(k)] if not conceptual else [0]*cnt[k]
    add_items(g, "SME", codes("SME"), ld("SME"), "left", sp=7.6, off=8.0)
    add_items(g, "FOMO", codes("FOMO"), ld("FOMO"), "bottom", sp=7.4, off=11.0)
    add_items(g, "HRD", codes("HRD"), ld("HRD"), "top", sp=7.6, off=11.0)
    add_items(g, "IDQ", codes("IDQ"), ld("IDQ"), "right", sp=7.6, off=6.5)
    add_items(g, "AIU", codes("AIU"), ld("AIU"), "bottom", sp=7.6, off=8.0)
    L = lambda k, h: (fl.fa(h) if conceptual else lab(P, k))
    g.edge("SME", "FOMO", L("FOMO~SME", "H1"), off=(0, 2.8), fs=9); g.edge("FOMO", "HRD", L("HRD~FOMO", "H2"), off=(0, 2.8), fs=9); g.edge("HRD", "IDQ", L("IDQ~HRD", "H3"), off=(0, 2.8), fs=9)
    g.edge("SME", "HRD", L("HRD~SME", "H4"), rad=-0.32, off=(0, 7.5), anchor_a=(18, 52.5), anchor_b=(58.5, 51.5), fs=9)
    g.edge("AIU", "IDQ", L("IDQ~AIU", "H8"), off=(6.5, 0), anchor_a=(79, 22.5), anchor_b=(82, 40), fs=9)
    g.edge("AIU", "FOMO", None, anchor_a=(70, 21.5), anchor_b=(51.5, 45.2), dashed=True)
    g.ax.text(67, 34, "H6, H7" + ("" if conceptual else "\n" + fl.fa("تعامل") + " " + fl.num(P["HRD~INT"]["beta"]) + " " + sig(P["HRD~INT"]["p"])), fontsize=9, ha="center", va="center", bbox=dict(fc="white", ec="none", pad=1))
    g.save(path)

def sem_paper2(path, R, conceptual=False):
    P, Ld = R["paths"], R["sem_loadings"]
    g = Diagram(11.0, 12.2); g.ax.set_xlim(0, 100); g.ax.set_ylim(10, 122)
    NM = {"SC": ("مقایسهٔ اجتماعی", "SC"), "AR": ("پشیمانی\nپیش‌بینی‌شده", "AR"), "SME": ("مواجهه با محتوای\nشبکه‌ها", "SME"), "AL": ("سواد حسابداری", "AL"),
          "FOMO": ("فومو", "FOMO"), "AIU": ("استفاده از اطلاعات\nحسابداری", "AIU"), "IDQ": ("کیفیت تصمیم\nسرمایه‌گذاری", "IDQ")}
    pos = {"SC": (24, 108, 15, 10), "AR": (24, 86, 15, 11), "SME": (24, 62, 16, 11), "AL": (24, 24, 15, 10),
           "FOMO": (56, 96, 13, 10), "AIU": (56, 36, 17, 11), "IDQ": (80, 66, 14, 12)}
    for k, (x, y, w, h) in pos.items(): g.node(k, x, y, latent_label(*NM[k]), w=w, h=h, raw=True, fs=9.5)
    cnt = {"SC": 4, "AR": 4, "SME": 5, "AL": 4, "FOMO": 6, "AIU": 5, "IDQ": 5}
    codes = lambda k: [f"{k}{i}" for i in range(1, cnt[k] + 1)]
    ld = lambda k: [Ld[c] for c in codes(k)] if not conceptual else [0]*cnt[k]
    for k in ("SC", "AR", "SME", "AL"): add_items(g, k, codes(k), ld(k), "left", sp=5.2, off=9.0, fs=8.3)
    add_items(g, "FOMO", codes("FOMO"), ld("FOMO"), "top", sp=7.4, off=9.0)
    add_items(g, "AIU", codes("AIU"), ld("AIU"), "bottom", sp=7.6, off=9.0)
    add_items(g, "IDQ", codes("IDQ"), ld("IDQ"), "right", sp=7.6, off=6.0, fs=8.3)
    L = lambda k, h: (fl.fa(h) if conceptual else lab(P, k))
    g.edge("SC", "FOMO", L("FOMO~SC", "H1"), off=(-1, 3.0), fs=9); g.edge("AR", "FOMO", L("FOMO~AR", "H2"), off=(-2, 3.0), fs=9)
    g.edge("SME", "FOMO", L("FOMO~SME", "(+)"), off=(-1, 3.0), fs=9)
    g.edge("SME", "AIU", L("AIU~SME", "H3"), off=(1, 3.0), fs=9); g.edge("AL", "AIU", L("AIU~AL", "H4"), off=(0, -3.0), fs=9)
    g.edge("FOMO", "IDQ", L("IDQ~FOMO", "H5"), off=(5, 3.0), fs=9); g.edge("AIU", "IDQ", L("IDQ~AIU", "H6"), off=(5, -3.0), fs=9)
    g.save(path)
