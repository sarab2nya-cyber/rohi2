# -*- coding: utf-8 -*-
import os, re, json, shutil
import pandas as pd
H = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(H, ".."); D = os.path.join(ROOT, "deliverables")
rd = lambda f: open(os.path.join(H, f), encoding="utf-8").read()
strip = lambda src: re.sub(r'^# -\*- coding: utf-8 -\*-\n', '', src)
s = rd("gov2_analysis.py")
s = s.replace("from simlib import gen_items\n", "# ---- simlib.py (inlined) ----\n" + strip(rd("simlib.py")) + "\n# ---- end simlib.py ----\n").replace("from mgcfa import MGCFA\n", "# ---- mgcfa.py (inlined) ----\n" + strip(rd("mgcfa.py")) + "\n# ---- end mgcfa.py ----\n")
s = s.replace('OUT = os.path.join(HERE, "..", "paper2", "output")', 'OUT = os.path.join(HERE, "output")')
open(os.path.join(D, "Paper2_Analysis_SEM.py"), "w", encoding="utf-8").write(s)
md = lambda t: {"cell_type": "markdown", "metadata": {}, "source": t.splitlines(True)}
cd = lambda t: {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": t.splitlines(True)}
cells = [md("# پیکربندی فشارهای نهادی و دو چهرهٔ اصلاحات مالی\n\n**اجرا:** `Runtime ← Run all` (حدود ۱۵ تا ۳۰ دقیقه با ۱٬۰۰۰ بوت‌استرپ؛ برای آزمون سریع `BOOT=100`). برای دادهٔ واقعی `DATA_PATH` را برابر مسیر CSV با همان نام ستون‌ها قرار دهید."),
         cd('import os\nos.environ["OMP_NUM_THREADS"] = "1"\n# os.environ["BOOT"] = "100"\n!pip -q install "setuptools<58" wheel\n!pip -q install --no-build-isolation semopy==2.3.11\n!pip -q install pandas numpy scipy statsmodels scikit-learn matplotlib openpyxl'),
         md("## تحلیل کامل"), cd(s.replace('HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else "."', 'HERE = "."')),
         cd("import json\nR = json.load(open('output/results_gov2.json'))\nprint({k: round(v, 3) for k, v in R['sem'].items()})\nfor k, v in R['paths'].items(): print(k, round(v['beta'], 3), round(v['p'], 4))"),
         cd("import shutil\nshutil.make_archive('output_results', 'zip', 'output')\ntry:\n    from google.colab import files\n    files.download('output_results.zip')\nexcept ImportError:\n    pass")]
json.dump({"cells": cells, "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3"}, "colab": {"provenance": []}}, "nbformat": 4, "nbformat_minor": 5}, open(os.path.join(D, "Paper2_Colab.ipynb"), "w"), ensure_ascii=False, indent=1)
R = json.load(open(os.path.join(ROOT, "paper2", "output", "results_gov2.json"))); df = pd.read_csv(os.path.join(ROOT, "paper2", "output", "gov2_data.csv"))
import gov_instrument as G
cb = [(c, v["code"], v["fa"], t, v["cls"]) for v in G.VARS if v["code"] in ("COE", "NOR", "MIM", "SUB", "SYM") for c, t in v["items"]] + [("org", "—", "نوع دستگاه", "۱ وزارتخانه/سازمان ملی؛ ۲ دانشگاه و بهداشتی‌درمانی؛ ۳ شهرداری/محلی؛ ۴ ادارات کل استانی", ""), ("grp", "—", "گروه مقایسه", "۰ اداری/حاکمیتی؛ ۱ خدماتی/محلی", ""), ("role", "—", "سمت", "۱ مدیر مالی؛ ۲ ذی‌حساب؛ ۳ کارشناس بودجه؛ ۴ حسابدار/حسابرس داخلی", ""), ("exp", "—", "سابقه (سال)", "", ""), ("age", "—", "سن", "", ""), ("edu", "—", "تحصیلات", "۱ دیپلم؛ ۲ کارشناسی؛ ۳ ارشد؛ ۴ دکتری", "")]
with pd.ExcelWriter(os.path.join(D, "Paper2_Data_and_Results.xlsx")) as w:
    df.to_excel(w, sheet_name="Data", index=False); pd.DataFrame(cb, columns=["Item", "Latent", "Construct", "Wording", "Origin"]).to_excel(w, sheet_name="Codebook", index=False)
    pd.DataFrame(R["rel"]).T.to_excel(w, sheet_name="Reliability"); pd.DataFrame(R["paths"]).T.to_excel(w, sheet_name="Paths"); pd.DataFrame(R["cond"]).T.to_excel(w, sheet_name="Conditional_effects")
    pd.DataFrame(R["models"]).T.to_excel(w, sheet_name="Competing_models"); pd.DataFrame(R["profiles"]).to_excel(w, sheet_name="Profiles"); pd.DataFrame(R["group_diff"]).T.to_excel(w, sheet_name="Group_path_diff")
print("ok")
