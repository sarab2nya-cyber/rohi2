# -*- coding: utf-8 -*-
import json, os
import fullsem as F
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "..", "paper3", "output")
def build(path):
    R = json.load(open(os.path.join(OUT, "results_paper3.json"))); L = R["sem_loadings"]; P = R["paths"]
    N = lambda x, y, lab, w=21, h=9, obs=False: dict(x=x, y=y, w=w, h=h, label=lab, obs=obs)
    nodes = {"GUI": N(24, 50, "Generative-AI\nuse (GUI)", 20), "AIL": N(24, 12, "AI literacy\n(AIL)", 20), "FKz": N(24, 96, "Financial knowledge\n(FKz, test score)", 24, 8, True),
             "PCA": N(66, 92, "Perceived competence\nwith AI (PCA)", 26), "CGz": N(66, 70, "Calibration gap\n(CG, observed)", 24, 8, True), "UR": N(66, 44, "Uncritical\nreliance (UR)", 22), "VER": N(66, 12, "Verification\n(VER)", 20),
             "IDQ": N(106, 52, "Investment decision\nquality (IDQ)", 24)}
    it = lambda k, n, side, **kw: {k: dict(side=side, loads=[(f"{k}{i}", L[f"{k}{i}"]) for i in range(1, n+1)], **kw)}
    items = {}; items.update(it("GUI", 4, "left", off=9)); items.update(it("AIL", 6, "left", off=9)); items.update(it("PCA", 4, "top", sp=7.6, off=8)); items.update(it("UR", 4, "bottom", sp=7.6, off=8)); items.update(it("VER", 4, "bottom", sp=7.6, off=8)); items.update(it("IDQ", 5, "right", off=8))
    g = lambda k: (P[k]["beta"], P[k]["p"])
    paths = [("GUI", "PCA", *g("PCA~GUI"), dict(t=.62, off=(0, 2.4))), ("GUI", "CGz", *g("CGz~GUI"), dict(t=.55, off=(0, 2.2))), ("GUI", "UR", *g("UR~GUI"), dict(t=.55, off=(0, 2.4))), ("GUI", "VER", *g("VER~GUI"), dict(t=.6, off=(0, -2.4))),
             ("PCA", "IDQ", *g("IDQ~PCA"), dict(t=.5, off=(2, 2.4))), ("CGz", "IDQ", *g("IDQ~CGz"), dict(t=.5, off=(2, 2.2))), ("UR", "IDQ", *g("IDQ~UR"), dict(t=.5, off=(2, -2.2))), ("VER", "IDQ", *g("IDQ~VER"), dict(t=.5, off=(2, -2.4)))]
    inter = [("FKz", ("GUI", "PCA"), *g("PCA~INTF"), (-5, 1.5), .55), ("FKz", ("GUI", "CGz"), *g("CGz~INTF"), (5.5, 0), .6), ("AIL", ("GUI", "UR"), *g("UR~INTA"), (-5.5, 0), .65), ("AIL", ("GUI", "VER"), *g("VER~INTA"), (5.5, 0), .6)]
    F.draw(path, nodes, items, paths, inter, {k: R["r2"][k] for k in ("PCA", "UR", "VER", "IDQ")}, (-2, 134), (-16, 112), (14.5, 10.6),
           note="Standardized estimates from the full structural model (maximum likelihood). Arrows to boxes: standardized loadings (λ); arrows between variables: standardized path coefficients (β).\n* p < .05, ** p < .01, *** p < .001, ns = not significant. Dashed orange: latent/observed interaction paths (knowledge × use; AI literacy × use), product indicators omitted.\nMain effects of knowledge and AI literacy, the direct effect of use on decision quality and the controls (experience, age, gender) are estimated but not drawn.", fs=8.4)
if __name__ == "__main__": build("/tmp/p3_full.png")
