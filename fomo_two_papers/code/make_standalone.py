# -*- coding: utf-8 -*-
"""ساخت اسکریپت‌های مستقل (تک‌فایل) و دفترچه‌های Colab برای هر مقاله در پوشهٔ deliverables"""
import os, re, json
H = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(H, "..", "deliverables")
rd = lambda f: open(os.path.join(H, f), encoding="utf-8").read()
def strip_mod(src): return re.sub(r'^# -\*- coding: utf-8 -\*-\n', '', src)
def bundle(script, mods, paper):
    s = rd(script)
    for m in mods:
        s = s.replace(f"from {m} import gen_items, demographics" if m == "simlib" else f"from {m} import MGCFA",
                      f"# ---- ماژول {m}.py (درون‌خطی) ----\n" + strip_mod(rd(m + ".py")) + f"\n# ---- پایان {m}.py ----\n")
    s = s.replace(f'OUT = os.path.join(HERE, "..", "paper{paper}", "output")', 'OUT = os.path.join(HERE, "output")')
    s = s.replace('DATA_DIR = os.path.join(HERE, "..", "data")', 'DATA_DIR = os.path.join(HERE, "output")')
    if paper == 2:
        s = s.replace("df = pd.read_csv(DATA_PATH) if DATA_PATH else simulate()",
                      "df = pd.read_csv(DATA_PATH) if DATA_PATH else simulate()\ndf = df[[c for c in df.columns if not c.startswith('HRD')]]      # گویه‌های HRD در این مقاله استفاده نمی‌شوند")
    s = s.replace("from simlib import gen_items, demographics\n", "") if "def gen_items" in s else s
    return s
REQ = "numpy\npandas\nscipy\nstatsmodels\nscikit-learn\nshap\nmatplotlib\nopenpyxl\n"
for p, (script, mods) in {1: ("paper1_analysis.py", ["simlib"]), 2: ("paper2_analysis.py", ["simlib", "mgcfa"])}.items():
    s = bundle(script, mods, p); out = os.path.join(D, f"paper{p}")
    open(os.path.join(out, f"Paper{p}_Python_Analysis.py"), "w", encoding="utf-8").write(s)
    open(os.path.join(out, "requirements.txt"), "w").write(REQ + "# semopy را جداگانه نصب کنید (نسخهٔ ۲٫۳٫۱۱):\n# pip install \"setuptools<58\" wheel && pip install --no-build-isolation semopy==2.3.11\n")
    open(os.path.join(out, "run_windows.bat"), "w", encoding="utf-8").write(
        f'@echo off\r\nset OMP_NUM_THREADS=1\r\npip install "setuptools<58" wheel\r\npip install --no-build-isolation semopy==2.3.11\r\npip install -r requirements.txt\r\npython Paper{p}_Python_Analysis.py\r\npause\r\n')
    open(os.path.join(out, "run_linux_mac.sh"), "w", encoding="utf-8").write(
        f'#!/usr/bin/env bash\nset -e\nexport OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1\npip install "setuptools<58" wheel\npip install --no-build-isolation semopy==2.3.11\npip install -r requirements.txt\npython3 Paper{p}_Python_Analysis.py\n')
    md = lambda t: {"cell_type": "markdown", "metadata": {}, "source": t.splitlines(True)}
    cd = lambda t: {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": t.splitlines(True)}
    title = {1: "مقالهٔ ۱ — مواجهه با محتوای شبکه‌های اجتماعی ← فومو ← رفتار توده‌وار ← کیفیت تصمیم (تعدیل‌گر: اطلاعات حسابداری)",
             2: "مقالهٔ ۲ — پیش‌برنده‌های فومو، رقابت منابع اطلاعاتی، ناوردایی اندازه‌گیری، مقایسهٔ گروه‌ها و یادگیری ماشین + SHAP"}[p]
    t_run = {1: "حدود ۵ تا ۱۰ دقیقه", 2: "حدود ۲۰ تا ۴۰ دقیقه"}[p]
    cells = [md(f"# {title}\n\n**نحوهٔ اجرا:** `Runtime ← Run all`؛ زمان تقریبی: {t_run}. خروجی‌ها در پوشهٔ `output/` ساخته و در پایان به‌صورت zip دانلود می‌شوند.\n\n> داده‌ها شبیه‌سازی‌شده‌اند. برای داده‌ٔ واقعی، در سلول کد مقدار `DATA_PATH` را برابر مسیر فایل CSV خود (ستون‌ها مطابق کدنامهٔ پرسشنامه) قرار دهید."),
             cd('import os\nos.environ["OMP_NUM_THREADS"] = "1"          # سرعت بسیار بیشتر در بازنمونه‌گیری‌ها\n!pip -q install "setuptools<58" wheel\n!pip -q install --no-build-isolation semopy==2.3.11\n!pip -q install numpy pandas scipy statsmodels scikit-learn shap matplotlib openpyxl'),
             md("## تحلیل کامل"), cd(s.replace('HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else "."', 'HERE = "."')),
             md("## نمایش خلاصهٔ نتایج و دانلود"),
             cd("import json, glob\nR = json.load(open(glob.glob('output/results_paper*.json')[0], encoding='utf-8'))\nprint({k: (round(v, 3) if isinstance(v, float) else v) for k, v in R['cfa'].items()})\nprint({k: (round(v, 3) if isinstance(v, float) else v) for k, v in R.get('sem', {}).items()})"),
             cd("import shutil\nshutil.make_archive('output_results', 'zip', 'output')\ntry:\n    from google.colab import files\n    files.download('output_results.zip')\nexcept ImportError:\n    pass")]
    json.dump({"cells": cells, "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3"}, "colab": {"provenance": []}}, "nbformat": 4, "nbformat_minor": 5},
              open(os.path.join(out, f"Paper{p}_Colab.ipynb"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("standalone ok")
