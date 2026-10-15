# -*- coding: utf-8 -*-
import json, os
import fullsem as F
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "..", "output")
def build(path):
    R = json.load(open(os.path.join(OUT, "results_eth.json"))); E = json.load(open(os.path.join(OUT, "eth_sem_extra.json"))); L = E["loadings_std"]; P = R["paths"]
    N = lambda k, x, y, lab, w=21, h=9: dict(x=x, y=y, w=w, h=h, label=lab)
    nodes = {"TBP": N("TBP", 24, 52, "Time-budget\npressure (TBP)"), "ECL": N("ECL", 24, 14, "Ethical climate\n(ECL)"), "MD": N("MD", 62, 33, "Moral\ndisengagement (MD)"), "SIL": N("SIL", 98, 33, "Silence about\nirregularity (SIL)"), "CON": N("CON", 62, 66, "Professional\nconscience (CON)", h=8.5)}
    it = lambda k, n, side, **kw: {k: dict(side=side, loads=[(f"{k}{i}", L[f"{k}{i}"]) for i in range(1, n+1)], **kw)}
    items = {}; items.update(it("TBP", 4, "left")); items.update(it("ECL", 4, "left")); items.update(it("CON", 4, "top", sp=7.6, off=10)); items.update(it("MD", 5, "bottom", sp=7.6, off=11)); items.update(it("SIL", 5, "right", off=9))
    paths = [("TBP", "MD", P["MD~TBP"]["beta"], P["MD~TBP"]["p"], dict(t=.55, off=(0, 2.4))), ("ECL", "MD", P["MD~ECL"]["beta"], P["MD~ECL"]["p"], dict(t=.5, off=(0, -2.4))), ("MD", "SIL", P["SIL~MD"]["beta"], P["SIL~MD"]["p"], dict(t=.5, off=(0, -2.6))),
             ("ECL", "SIL", P["SIL~ECL"]["beta"], P["SIL~ECL"]["p"], dict(rad=.36, t=.8, off=(1, -3.6), pa=(28, 9.4), pb=(95, 28.6))),
             ("TBP", "SIL", P["SIL~TBP"]["beta"], P["SIL~TBP"]["p"], dict(rad=-.2, t=.5, off=(0, 3.4), dash=True, color="#777", pa=(30, 56.4), pb=(93, 37.4)))]
    inter = [("CON", ("TBP", "MD"), P["MD~INTT"]["beta"], P["MD~INTT"]["p"], (-5, 0)), ("CON", ("MD", "SIL"), P["SIL~INTM"]["beta"], P["SIL~INTM"]["p"], (5.5, 0))]
    F.draw(path, nodes, items, paths, inter, R["r2"], (-12, 124), (-6, 82), (13, 9),
           note="Standardized estimates from the full structural model (maximum likelihood). Arrows to boxes: standardized loadings (λ); arrows between latent variables: standardized path coefficients (β).\n* p < .05, ** p < .01, *** p < .001, ns = not significant. Dashed orange: latent interaction paths (conscience × pressure; conscience × disengagement). Product indicators of the interaction terms are omitted.")
if __name__ == "__main__": build("/tmp/eth_full.png")
