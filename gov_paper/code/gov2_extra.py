# -*- coding: utf-8 -*-
import os, json, numpy as np, pandas as pd, warnings
from semopy import Model
warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "..", "paper2", "output")
df = pd.read_csv(os.path.join(OUT, "gov2_data.csv")); FAC = dict(COE=4, NOR=4, MIM=4, SUB=5, SYM=4); ITEMS = [f"{f}{j}" for f, k in FAC.items() for j in range(1, k+1)]
dfc = df[ITEMS] - df[ITEMS].mean()
for i in range(1, 5): dfc[f"IN{i}"] = dfc[f"COE{i}"]*dfc[f"NOR{i}"]; dfc[f"IM{i}"] = dfc[f"COE{i}"]*dfc[f"MIM{i}"]
CFA = "".join(f"{k} =~ " + "+".join(f"{k}{j}" for j in range(1, n+1)) + "\n" for k, n in FAC.items())
EXO = ["COE", "NOR", "MIM", "INCN", "INCM"]
M = CFA + "INCN =~ IN1+IN2+IN3+IN4\nINCM =~ IM1+IM2+IM3+IM4\nSUB ~ COE + NOR + MIM + INCN\nSYM ~ COE + NOR + MIM + INCM\n" + "".join(f"{a} ~~ {b}\n" for i, a in enumerate(EXO) for b in EXO[i+1:]) + "SUB ~~ SYM\n"
m = Model(M); m.fit(dfc); isd = m.inspect(std_est=True)
json.dump({"loadings_std": {r.lval: float(r["Est. Std"]) for _, r in isd[(isd.op == "~") & (isd.rval.isin(list(FAC)))].iterrows()}}, open(os.path.join(OUT, "gov2_sem_extra.json"), "w"), indent=1); print("ok")
