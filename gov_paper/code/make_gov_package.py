# -*- coding: utf-8 -*-
import os, re, json, shutil
import pandas as pd
import gov_instrument as G
H = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(H, ".."); D = os.path.join(ROOT, "deliverables"); os.makedirs(D, exist_ok=True)
rd = lambda f: open(os.path.join(H, f), encoding="utf-8").read()
strip = lambda src: re.sub(r'^# -\*- coding: utf-8 -\*-\n', '', src)
sim_src = strip(rd("simlib.py"))
a = rd("gov_analysis.py")
# ---- 1) analysis script (single file)
s = a.replace("from simlib import gen_items\n", "# ---- simlib.py (inlined) ----\n" + sim_src + "\n# ---- end simlib.py ----\n")
s = s.replace('OUT = os.path.join(HERE, "..", "output")', 'OUT = os.path.join(HERE, "output")')
open(os.path.join(D, "Analysis_SEM.py"), "w", encoding="utf-8").write(s)
# ---- 2) data-generation script (single file)
i0 = a.index("SEED, N = "); i1 = a.index("df = pd.read_csv(DATA_PATH)")
gen = '''# -*- coding: utf-8 -*-
"""Data-generation script (demonstration data with the structure of the questionnaire: 8 constructs, 34 items + 5 background variables).
Use it to test the analysis code; replace the CSV by the real survey data (same column names) before any substantive use."""
import os, numpy as np, pandas as pd
''' + sim_src.split("import numpy as np, pandas as pd")[-1] + "\n" + a[i0:i1].replace("DATA_PATH = None\n", "").replace('OUT = os.path.join(HERE, "..", "output"); os.makedirs(OUT, exist_ok=True)\n', 'OUT = "."\n').replace('B = int(os.environ.get("BOOT", 2000))\n', "")
gen = gen.replace('HERE = os.path.dirname(os.path.abspath(__file__))', '')
gen += '''
if __name__ == "__main__":
    df = simulate()
    df.to_csv("gov_data.csv", index=False, encoding="utf-8-sig"); df.to_excel("gov_data.xlsx", index=False)
    print(df.shape, "columns:", list(df.columns)[:8], "...")
'''
open(os.path.join(D, "Generate_Data.py"), "w", encoding="utf-8").write(gen)
# ---- 3) requirements, run scripts, Colab
open(os.path.join(D, "requirements.txt"), "w").write("numpy\npandas\nscipy\nstatsmodels\nmatplotlib\nopenpyxl\n# semopy 2.3.11 separately:\n# pip install \"setuptools<58\" wheel && pip install --no-build-isolation semopy==2.3.11\n")
open(os.path.join(D, "run_linux_mac.sh"), "w").write('#!/usr/bin/env bash\nset -e\nexport OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1\npip install "setuptools<58" wheel\npip install --no-build-isolation semopy==2.3.11\npip install -r requirements.txt\npython3 Analysis_SEM.py\n')
open(os.path.join(D, "run_windows.bat"), "w").write('@echo off\r\nset OMP_NUM_THREADS=1\r\npip install "setuptools<58" wheel\r\npip install --no-build-isolation semopy==2.3.11\r\npip install -r requirements.txt\r\npython Analysis_SEM.py\r\npause\r\n')
md = lambda t: {"cell_type": "markdown", "metadata": {}, "source": t.splitlines(True)}
cd = lambda t: {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": t.splitlines(True)}
cells = [md("# مدل معادلات ساختاری: فشارهای نهادی ← اجرای ماهوی / انطباق نمادین ← سودمندی اطلاعات ← پاسخگویی مالی (تعدیل‌گر: بلوغ نظام اطلاعاتی)\n\n**نحوهٔ اجرا:** `Runtime ← Run all`؛ زمان تقریبی ۲۰ تا ۴۰ دقیقه با ۲٬۰۰۰ بوت‌استرپ (برای آزمون سریع مقدار `BOOT` را ۲۰۰ بگذارید). برای تحلیل دادهٔ واقعی، مقدار `DATA_PATH` را برابر مسیر فایل CSV با همان نام ستون‌ها قرار دهید."),
         cd('import os\nos.environ["OMP_NUM_THREADS"] = "1"\n# os.environ["BOOT"] = "200"   # آزمون سریع\n!pip -q install "setuptools<58" wheel\n!pip -q install --no-build-isolation semopy==2.3.11\n!pip -q install pandas numpy scipy statsmodels matplotlib openpyxl'),
         md("## تحلیل کامل (مدل اندازه‌گیری، مدل ساختاری، بوت‌استرپ، مدل‌های رقیب و آزمون‌های استواری)"),
         cd(s.replace('HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else "."', 'HERE = "."')),
         cd("import json, glob\nR = json.load(open('output/results_gov.json'))\nprint({k: round(v, 3) for k, v in R['sem'].items()})\nfor k, v in R['paths'].items(): print(k, round(v['beta'], 3), round(v['p'], 4))"),
         cd("import shutil\nshutil.make_archive('output_results', 'zip', 'output')\ntry:\n    from google.colab import files\n    files.download('output_results.zip')\nexcept ImportError:\n    pass")]
json.dump({"cells": cells, "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3"}, "colab": {"provenance": []}}, "nbformat": 4, "nbformat_minor": 5}, open(os.path.join(D, "Colab_SEM_Analysis.ipynb"), "w"), ensure_ascii=False, indent=1)
# ---- 4) Excel (data + codebook + results)
R = json.load(open(os.path.join(ROOT, "output", "results_gov.json"))); df = pd.read_csv(os.path.join(ROOT, "output", "gov_data.csv"))
cb = [(c, v["code"], v["fa"], t, v["cls"]) for v in G.VARS for c, t in v["items"]] + [("org", "—", "نوع دستگاه", "۱ وزارتخانه/سازمان ملی؛ ۲ دانشگاه و بهداشتی‌درمانی؛ ۳ شهرداری/محلی؛ ۴ ادارات کل استانی", "جمعیت‌شناختی"),
      ("role", "—", "سمت", "۱ مدیر مالی؛ ۲ ذی‌حساب؛ ۳ کارشناس بودجه؛ ۴ حسابدار/حسابرس داخلی", "جمعیت‌شناختی"), ("exp", "—", "سابقه (سال)", "", "جمعیت‌شناختی"), ("age", "—", "سن", "", "جمعیت‌شناختی"), ("edu", "—", "تحصیلات", "۱ دیپلم؛ ۲ کارشناسی؛ ۳ ارشد؛ ۴ دکتری", "جمعیت‌شناختی")]
with pd.ExcelWriter(os.path.join(D, "Data_and_Results.xlsx")) as w:
    df.to_excel(w, sheet_name="Data", index=False); pd.DataFrame(cb, columns=["Item", "Latent", "Construct", "Wording", "Origin"]).to_excel(w, sheet_name="Codebook", index=False)
    pd.DataFrame(R["rel"]).T.to_excel(w, sheet_name="Reliability"); pd.DataFrame(R["paths"]).T.to_excel(w, sheet_name="Paths"); pd.DataFrame(R["indirect"]).T.to_excel(w, sheet_name="Indirect_effects"); pd.DataFrame(R["models"]).T.to_excel(w, sheet_name="Competing_models")
shutil.copy(os.path.join(ROOT, "output", "fig_estimated.png"), os.path.join(D, "Figure2_estimated_model.png")); shutil.copy(os.path.join(ROOT, "output", "fig_conceptual.png"), os.path.join(D, "Figure1_conceptual_model.png"))
open(os.path.join(D, "README.md"), "w", encoding="utf-8").write("""# بستهٔ پژوهش — حسابداری دولتی
- `Paper_PublicSector_Accounting.docx`: مقاله به قالب مجله (بدون نام نویسندگان)
- `Extended_Abstract_Persian.docx`, `Extended_Abstract_English.docx`: چکیدهٔ گسترده
- `Questionnaire_Persian.docx`: پرسشنامه + منبع و نوع منشأ (محقق‌ساخته/پژوهش‌محور) هر متغیر
- `Colab_SEM_Analysis.ipynb`, `Analysis_SEM.py`: تحلیل کامل (semopy)؛ `Generate_Data.py`: تولید دادهٔ نمونه؛ `Data_and_Results.xlsx`: داده و نتایج
**نکتهٔ مهم:** داده‌های همراه این بسته نمونه‌ای برای آزمون کد است. پیش از ارسال به مجله، پرسشنامه را اجرا کنید، فایل CSV واقعی را با همان نام ستون‌ها جایگزین (`DATA_PATH`) و تحلیل و متن مقاله را با اعداد واقعی به‌روز کنید؛ موارد زردرنگ در بخش روش‌شناسی (نمونه‌گیری، CVR/CVI) باید با جزئیات واقعی پر شود. اسامی فارسی نویسندگان منابع فارسی و DOIها را با منبع اصلی تطبیق دهید.
""")
print("package ok")
