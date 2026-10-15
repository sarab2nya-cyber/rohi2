# -*- coding: utf-8 -*-
import json, os
import fullsem as F
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "..", "paper2", "output")
def build(path):
    R = json.load(open(os.path.join(OUT, "results_gov2.json"))); L = json.load(open(os.path.join(OUT, "gov2_sem_extra.json")))["loadings_std"]; P = R["paths"]
    N = lambda x, y, lab, w=21, h=9: dict(x=x, y=y, w=w, h=h, label=lab)
    nodes = {"COE": N(26, 62, "Coercive\npressure (COE)", 20), "NOR": N(26, 38, "Normative\npressure (NOR)", 20), "MIM": N(26, 14, "Mimetic\npressure (MIM)", 20),
             "SUB": N(78, 56, "Substantive\nimplementation (SUB)", 24), "SYM": N(78, 18, "Symbolic\ncompliance (SYM)", 22), "INCN": N(52, 82, "COE × NOR", 16, 7), "INCM": N(52, -8, "COE × MIM", 16, 7)}
    it = lambda k, n, side, **kw: {k: dict(side=side, loads=[(f"{k}{i}", L[f"{k}{i}"]) for i in range(1, n+1)], **kw)}
    items = {}; items.update(it("COE", 4, "left", off=9)); items.update(it("NOR", 4, "left", off=9)); items.update(it("MIM", 4, "left", off=9)); items.update(it("SUB", 5, "right", off=9)); items.update(it("SYM", 4, "right", off=9))
    g = lambda k: (P[k]["beta"], P[k]["p"])
    paths = [("COE", "SUB", *g("SUB~COE"), dict(t=.5, off=(0, 2.6))), ("NOR", "SUB", *g("SUB~NOR"), dict(t=.6, off=(0, 2.4))), ("MIM", "SUB", *g("SUB~MIM"), dict(t=.78, off=(0, -2.6), dash=True, color="#777")),
             ("COE", "SYM", *g("SYM~COE"), dict(t=.78, off=(3, 2.6))), ("NOR", "SYM", *g("SYM~NOR"), dict(t=.5, off=(0, -2.6))), ("MIM", "SYM", *g("SYM~MIM"), dict(t=.5, off=(0, -2.6))),
             ("INCN", "SUB", *g("SUB~INCN"), dict(t=.5, off=(0, 2.4), color=F.ORANGE, dash=True)), ("INCM", "SYM", *g("SYM~INCM"), dict(t=.5, off=(0, -2.4), color=F.ORANGE, dash=True)),
             ("SUB", "SYM", R["resid_cov"]["beta"], R["resid_cov"]["p"], dict(both=True, rad=-.5, t=.5, off=(8, 0), pa=(86, 51), pb=(86, 23)))]
    F.draw(path, nodes, items, paths, [], {k: R["r2"][k] for k in ("SUB", "SYM")}, (-2, 126), (-20, 94), (14.5, 9.8),
           note="Standardized estimates from the full structural model (maximum likelihood). Arrows to boxes: standardized loadings (λ); arrows between latent variables: standardized path coefficients (β).\n* p < .05, ** p < .01, *** p < .001, ns = not significant. Dashed orange: latent interaction terms (product indicators omitted); curved double-headed arrow: residual correlation between the two responses.", fs=8.6)
if __name__ == "__main__": build("/tmp/gov2_full.png")
