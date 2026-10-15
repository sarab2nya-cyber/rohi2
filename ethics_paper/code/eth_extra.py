# -*- coding: utf-8 -*-
"""Refit the full model once to save unstandardized path estimates (used for simple-slope plots)."""
import os, json, numpy as np, pandas as pd, warnings
from semopy import Model
warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "..", "output")
df = pd.read_csv(os.path.join(OUT, "eth_data.csv")); FAC = dict(TBP=4, ECL=4, CON=4, MD=5, SIL=5); ITEMS = [f"{f}{j}" for f, k in FAC.items() for j in range(1, k+1)]
dfc = df[ITEMS] - df[ITEMS].mean()
for i in range(1, 5): dfc[f"IT{i}"] = dfc[f"TBP{i}"]*dfc[f"CON{i}"]; dfc[f"IM{i}"] = dfc[f"MD{i}"]*dfc[f"CON{i}"]
CFA = "".join(f"{k} =~ " + "+".join(f"{k}{j}" for j in range(1, n+1)) + "\n" for k, n in FAC.items())
EXO = ["TBP", "ECL", "CON", "INTT"]
COV = "".join(f"{a} ~~ {b}\n" for i, a in enumerate(EXO) for b in EXO[i+1:]) + "INTM ~~ TBP\nINTM ~~ ECL\nINTM ~~ CON\nINTM ~~ INTT\n"
M = CFA + "INTT =~ IT1+IT2+IT3+IT4\nINTM =~ IM1+IM2+IM3+IM4\n" + "MD ~ TBP + ECL + CON + INTT\nSIL ~ MD + ECL + CON + TBP + INTM\n" + COV
m = Model(M); m.fit(dfc); iu = m.inspect()
out = {"paths_unstd": {f"{r.lval}~{r.rval}": dict(b=float(r.Estimate), se=float(r["Std. Err"])) for _, r in iu[(iu.op == "~") & (iu.lval.isin(["MD", "SIL"]))].iterrows()},
       "loadings_unstd": {r.lval: float(r.Estimate) for _, r in iu[(iu.op == "~") & (iu.rval.isin(list(FAC)))].iterrows()}}
json.dump(out, open(os.path.join(OUT, "eth_sem_extra.json"), "w"), indent=1); print("ok")
