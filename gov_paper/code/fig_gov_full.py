# -*- coding: utf-8 -*-
import json, os
import fullsem as F
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "..", "output")
def build(path):
    R = json.load(open(os.path.join(OUT, "results_gov.json"))); E = json.load(open(os.path.join(OUT, "gov_sem_extra.json"))); L = E["loadings"]; P = R["paths"]
    N = lambda x, y, lab, w=21, h=9: dict(x=x, y=y, w=w, h=h, label=lab)
    nodes = {"COE": N(26, 70, "Coercive\npressure (COE)", 20), "NOR": N(26, 44, "Normative\npressure (NOR)", 20), "MIM": N(26, 18, "Mimetic\npressure (MIM)", 20),
             "SUB": N(62, 64, "Substantive\nimplementation (SUB)", 24), "SYM": N(62, 22, "Symbolic\ncompliance (SYM)", 22), "USE": N(94, 43, "Usefulness of\ninformation (USE)", 24),
             "ACC": N(126, 43, "Financial\naccountability (ACC)", 22), "DIG": N(94, 78, "Information-system\nmaturity (DIG)", 24, 8)}
    def it(k, n, side, **kw): return {k: dict(side=side, loads=[(f"{k}{i}", L[f"{k}{i}"]) for i in range(1, n+1)], **kw)}
    items = {}; items.update(it("COE", 4, "left", off=9)); items.update(it("NOR", 4, "left", off=9)); items.update(it("MIM", 4, "left", off=9))
    items.update(it("SUB", 5, "top", sp=7.6, off=9)); items.update(it("SYM", 4, "bottom", sp=7.6, off=9)); items.update(it("USE", 4, "bottom", sp=7.6, off=9)); items.update(it("ACC", 5, "right", off=8)); items.update(it("DIG", 4, "top", sp=7.6, off=8))
    g = lambda k: (P[k]["beta"], P[k]["p"])
    paths = [("COE", "SUB", *g("SUB~COE"), dict(t=.5, off=(0, 2.4))), ("COE", "SYM", *g("SYM~COE"), dict(t=.8, off=(4, 2.4))), ("NOR", "SUB", *g("SUB~NOR"), dict(t=.6, off=(0, 2.4))), ("NOR", "SYM", *g("SYM~NOR"), dict(t=.5, off=(0, -2.6))),
             ("MIM", "SYM", *g("SYM~MIM"), dict(t=.5, off=(0, -2.4))), ("SUB", "USE", *g("USE~SUB"), dict(t=.5, off=(0, 2.4))), ("SYM", "USE", *g("USE~SYM"), dict(t=.35, off=(2, -2.6))), ("USE", "ACC", *g("ACC~USE"), dict(t=.5, off=(0, 2.6))),
             ("SUB", "ACC", *g("ACC~SUB"), dict(rad=-.3, t=.55, off=(0, 3.4), pa=(74, 67), pb=(120, 47.6))), ("SYM", "ACC", *g("ACC~SYM"), dict(rad=.3, t=.55, off=(0, -3.6), pa=(73, 17), pb=(120, 38.6)))]
    inter = [("DIG", ("SUB", "USE"), *g("USE~INTS"), (5.5, 0)), ("DIG", ("COE", "SYM"), *g("SYM~INTC"), (-5.5, 0), .88)]
    F.draw(path, nodes, items, paths, inter, {k: R["r2"][k] for k in ("SUB", "SYM", "USE", "ACC")}, (-2, 156), (-18, 100), (16.5, 10.6),
           note="Standardized estimates from the full structural model (maximum likelihood). Arrows to boxes: standardized loadings (λ); arrows between latent variables: standardized path coefficients (β).\n* p < .05, ** p < .01, *** p < .001. Dashed orange: latent interaction paths (maturity × substantive implementation; maturity × coercive pressure), product indicators omitted.\nNon-hypothesised paths (mimetic → substantive; maturity main effects) and the control (experience) are estimated but not drawn.", fs=8.4, ifs=6.4)
if __name__ == "__main__": build("/tmp/gov_full.png")
