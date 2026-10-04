# -*- coding: utf-8 -*-
"""Package Paper 3: standalone script, Colab notebook, run scripts, Excel (data + codebook + results) in deliverables/paper3."""
import os, re, json, shutil
import pandas as pd
H = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(H, ".."); D = os.path.join(ROOT, "deliverables", "paper3"); os.makedirs(D, exist_ok=True)
import paper3_instrument as P
rd = lambda f: open(os.path.join(H, f), encoding="utf-8").read()
s = rd("paper3_analysis.py")
s = s.replace("from simlib import gen_items, demographics\n", "# ---- simlib.py (inlined) ----\n" + re.sub(r'^# -\*- coding: utf-8 -\*-\n', '', rd("simlib.py")) + "\n# ---- end simlib.py ----\n")
s = s.replace('OUT = os.path.join(HERE, "..", "paper3", "output")', 'OUT = os.path.join(HERE, "output")').replace('DATA_DIR = os.path.join(HERE, "..", "data")', 'DATA_DIR = os.path.join(HERE, "output")')
open(os.path.join(D, "Paper3_Python_Analysis.py"), "w", encoding="utf-8").write(s)
open(os.path.join(D, "requirements.txt"), "w").write("numpy\npandas\nscipy\nstatsmodels\nmatplotlib\nopenpyxl\n# semopy 2.3.11 separately:\n# pip install \"setuptools<58\" wheel && pip install --no-build-isolation semopy==2.3.11\n")
open(os.path.join(D, "run_linux_mac.sh"), "w").write('#!/usr/bin/env bash\nset -e\nexport OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1\npip install "setuptools<58" wheel\npip install --no-build-isolation semopy==2.3.11\npip install -r requirements.txt\npython3 Paper3_Python_Analysis.py\n')
open(os.path.join(D, "run_windows.bat"), "w").write('@echo off\r\nset OMP_NUM_THREADS=1\r\npip install "setuptools<58" wheel\r\npip install --no-build-isolation semopy==2.3.11\r\npip install -r requirements.txt\r\npython Paper3_Python_Analysis.py\r\npause\r\n')
md = lambda t: {"cell_type": "markdown", "metadata": {}, "source": t.splitlines(True)}
cd = lambda t: {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": t.splitlines(True)}
cells = [md("# Paper 3 – Generative-AI use, competence illusion, uncritical reliance, verification and investment decision quality\n\n**Run:** Runtime → Run all (≈ 15–40 min with B = 2000 bootstrap draws; set `BOOT=200` for a quick test). **Data are synthetic**; to analyse real data set `DATA_PATH` to a CSV with the same column names (see Codebook in the Excel file)."),
         cd('import os\nos.environ["OMP_NUM_THREADS"] = "1"\n!pip -q install "setuptools<58" wheel\n!pip -q install --no-build-isolation semopy==2.3.11\n!pip -q install pandas numpy scipy statsmodels matplotlib openpyxl'),
         md("## Full analysis"), cd(s.replace('HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else "."', 'HERE = "."')),
         cd("import json, glob\nR = json.load(open(glob.glob('output/results_paper3.json')[0]))\nprint({k: round(v, 3) for k, v in R['sem'].items()})\nfor k, v in R['paths'].items(): print(k, round(v['beta'], 3), round(v['p'], 4))"),
         cd("import shutil\nshutil.make_archive('output_results', 'zip', 'output')\ntry:\n    from google.colab import files\n    files.download('output_results.zip')\nexcept ImportError:\n    pass")]
json.dump({"cells": cells, "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3"}, "colab": {"provenance": []}}, "nbformat": 4, "nbformat_minor": 5}, open(os.path.join(D, "Paper3_Colab.ipynb"), "w"), ensure_ascii=False, indent=1)
# ---- Excel
R = json.load(open(os.path.join(ROOT, "paper3", "output", "results_paper3.json")))
df = pd.read_csv(os.path.join(ROOT, "data", "paper3_data.csv"))
cb = []
for v in P.VARS:
    for c, e, _ in v["items"]: cb.append((c, v["code"], v["name"], e, v["scale"], v["cls"], "; ".join(re.match(r"([^,]+),", P.REF[k]).group(1) + " " + re.search(r"\((\d{4})\)", P.REF[k]).group(1) for k in v["refs"])))
extra = {"FKz": "Standardized knowledge-test score (moderator)", "CGz": "Standardized calibration gap = predicted − actual score", "CG": "Calibration gap (raw)", "VIGERR": "Wrong AI statements accepted (0–2)"}
cbdf = pd.DataFrame(cb, columns=["Item", "Latent", "Construct", "Wording", "Response", "Origin", "References"])
with pd.ExcelWriter(os.path.join(D, "Paper3_Data.xlsx")) as w:
    df.to_excel(w, sheet_name="Data", index=False); cbdf.to_excel(w, sheet_name="Codebook", index=False)
    pd.DataFrame([dict(Variable=k, Description=v) for k, v in extra.items()]).to_excel(w, sheet_name="Derived_variables", index=False)
    pd.DataFrame(R["rel"]).T.to_excel(w, sheet_name="Reliability")
    pd.DataFrame(R["paths"]).T.to_excel(w, sheet_name="Paths")
    pd.DataFrame(R["indirect"]).T.to_excel(w, sheet_name="Indirect_effects")
    pd.DataFrame(R["models"]).T.to_excel(w, sheet_name="Competing_models")
shutil.copy(os.path.join(ROOT, "paper3", "output", "fig_p3_model.png"), os.path.join(D, "Figure1_model.png")) if os.path.exists(os.path.join(ROOT, "paper3", "output", "fig_p3_model.png")) else None
print("package ok")
