# -*- coding: utf-8 -*-
"""Refit the full model of Paper 1 once on the saved data to extract standardized loadings, factor correlations and standardized path CIs (for figures/appendices)."""
import os, json, numpy as np, pandas as pd, warnings
from semopy import Model
warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "..", "output")
df = pd.read_csv(os.path.join(OUT, "gov_data.csv"))
FAC = dict(COE=4, NOR=4, MIM=4, SUB=5, SYM=4, DIG=4, USE=4, ACC=5); ITEMS = [f"{f}{j}" for f, k in FAC.items() for j in range(1, k+1)]
z = lambda x: (x-x.mean())/x.std()
dfc = df[ITEMS] - df[ITEMS].mean()
for i in range(1, 5): dfc[f"IS{i}"] = dfc[f"SUB{i}"]*dfc[f"DIG{i}"]; dfc[f"IC{i}"] = dfc[f"COE{i}"]*dfc[f"DIG{i}"]
dfc["exp"] = z(df.exp.astype(float)).values
CFA = "".join(f"{k} =~ " + "+".join(f"{k}{j}" for j in range(1, n+1)) + "\n" for k, n in FAC.items())
EXO = ["COE", "NOR", "MIM", "DIG", "INTS", "INTC"]
M = CFA + "INTS =~ IS1+IS2+IS3+IS4\nINTC =~ IC1+IC2+IC3+IC4\n" + "SUB ~ COE + NOR + MIM + DIG\nSYM ~ COE + NOR + MIM + DIG + INTC\nUSE ~ SUB + SYM + DIG + INTS\nACC ~ SUB + SYM + USE + exp\n" + "".join(f"{a} ~~ {b}\n" for i, a in enumerate(EXO) for b in EXO[i+1:])
m = Model(M); m.fit(dfc); ii = m.inspect(std_est=True)
f = lambda c: pd.to_numeric(ii[c], errors="coerce")
ld = ii[(ii.op == "~") & (ii.rval.isin(FAC)) & (ii.lval.isin(ITEMS))]
out = {"loadings": {r.lval: float(r["Est. Std"]) for _, r in ld.iterrows()}}
cor = ii[(ii.op == "~~") & (ii.lval.isin(list(FAC) + EXO)) & (ii.rval.isin(list(FAC) + EXO)) & (ii.lval != ii.rval)]
out["factor_cov_std"] = {f"{r.lval}~~{r.rval}": float(r["Est. Std"]) for _, r in cor.iterrows()}
# bootstrap CIs for std paths are expensive; use delta-method approx from unstandardised b/se scaled by sd ratio
iu = m.inspect(); out["paths_unstd"] = {f"{r.lval}~{r.rval}": dict(b=float(r.Estimate), se=float(r["Std. Err"])) for _, r in iu[(iu.op == "~") & (iu.lval.isin(["SUB","SYM","USE","ACC"]))].iterrows()}
out["var"] = {r.lval: float(r.Estimate) for _, r in iu[(iu.op == "~~") & (iu.lval == iu.rval) & (iu.lval.isin(list(FAC)+EXO))].iterrows()}
json.dump(out, open(os.path.join(OUT, "gov_sem_extra.json"), "w"), indent=1)
print(len(out["loadings"]), "loadings;", len(out["factor_cov_std"]), "covs")
