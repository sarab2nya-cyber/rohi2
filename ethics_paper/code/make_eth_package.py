# -*- coding: utf-8 -*-
import os, re, json, shutil
import pandas as pd
import eth_instrument as G
H = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(H, ".."); D = os.path.join(ROOT, "deliverables")
rd = lambda f: open(os.path.join(H, f), encoding="utf-8").read(); strip = lambda src: re.sub(r'^# -\*- coding: utf-8 -\*-\n', '', src)
a = rd("eth_analysis.py"); sim = strip(rd("simlib.py"))
s = a.replace("from simlib import gen_items\n", "# ---- simlib.py (inlined) ----\n" + sim + "\n# ---- end simlib.py ----\n").replace('OUT = os.path.join(HERE, "..", "output")', 'OUT = os.path.join(HERE, "output")')
open(os.path.join(D, "Analysis_SEM.py"), "w", encoding="utf-8").write(s)
i0 = a.index("SEED, N = "); i1 = a.index("df = pd.read_csv(DATA_PATH)")
gen = '# -*- coding: utf-8 -*-\n"""Data-generation script (demonstration data with the structure of the questionnaire; use it to test the analysis code and replace it by the real survey CSV with the same column names)."""\nimport os, numpy as np, pandas as pd\n' + sim.split("import numpy as np, pandas as pd")[-1] + "\n" + a[i0:i1].replace("DATA_PATH = None\n", "").replace('OUT = os.path.join(HERE, "..", "output"); os.makedirs(OUT, exist_ok=True)\n', 'OUT = "."\n').replace('B = int(os.environ.get("BOOT", 2000))\n', "") + '\nif __name__ == "__main__":\n    df = simulate(); df.to_csv("eth_data.csv", index=False, encoding="utf-8-sig"); df.to_excel("eth_data.xlsx", index=False); print(df.shape)\n'
open(os.path.join(D, "Generate_Data.py"), "w", encoding="utf-8").write(gen)
open(os.path.join(D, "requirements.txt"), "w").write("numpy\npandas\nscipy\nstatsmodels\nmatplotlib\nopenpyxl\n# semopy 2.3.11 separately:\n# pip install \"setuptools<58\" wheel && pip install --no-build-isolation semopy==2.3.11\n")
open(os.path.join(D, "run_linux_mac.sh"), "w").write('#!/usr/bin/env bash\nset -e\nexport OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1\npip install "setuptools<58" wheel\npip install --no-build-isolation semopy==2.3.11\npip install -r requirements.txt\npython3 Analysis_SEM.py\n')
open(os.path.join(D, "run_windows.bat"), "w").write('@echo off\r\nset OMP_NUM_THREADS=1\r\npip install "setuptools<58" wheel\r\npip install --no-build-isolation semopy==2.3.11\r\npip install -r requirements.txt\r\npython Analysis_SEM.py\r\npause\r\n')
md = lambda t: {"cell_type": "markdown", "metadata": {}, "source": t.splitlines(True)}; cd = lambda t: {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": t.splitlines(True)}
cells = [md("# فشار زمانی، جو اخلاقی، رفع تعهد اخلاقی، وجدان حرفه‌ای و سکوت حسابرسان\n\n**اجرا:** `Runtime ← Run all` (حدود ۱۵ تا ۳۰ دقیقه با ۲٬۰۰۰ بوت‌استرپ؛ برای آزمون سریع `BOOT=100`). برای دادهٔ واقعی `DATA_PATH` را برابر مسیر CSV با همان نام ستون‌ها قرار دهید."),
         cd('import os\nos.environ["OMP_NUM_THREADS"] = "1"\n# os.environ["BOOT"] = "100"\n!pip -q install "setuptools<58" wheel\n!pip -q install --no-build-isolation semopy==2.3.11\n!pip -q install pandas numpy scipy statsmodels matplotlib openpyxl'),
         md("## تحلیل کامل"), cd(s.replace('HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else "."', 'HERE = "."')),
         cd("import json\nR = json.load(open('output/results_eth.json'))\nprint({k: round(v, 3) for k, v in R['sem'].items()})\nfor k, v in R['paths'].items(): print(k, round(v['beta'], 3), round(v['p'], 4))"),
         cd("import shutil\nshutil.make_archive('output_results', 'zip', 'output')\ntry:\n    from google.colab import files\n    files.download('output_results.zip')\nexcept ImportError:\n    pass")]
json.dump({"cells": cells, "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3"}, "colab": {"provenance": []}}, "nbformat": 4, "nbformat_minor": 5}, open(os.path.join(D, "Colab_SEM_Analysis.ipynb"), "w"), ensure_ascii=False, indent=1)
R = json.load(open(os.path.join(ROOT, "output", "results_eth.json"))); df = pd.read_csv(os.path.join(ROOT, "output", "eth_data.csv"))
cb = [(c, v["code"], v["fa"], t, v["cls"]) for v in G.VARS for c, t in v["items"]] + [("rank", "—", "رتبه", "۱ مقدماتی؛ ۲ ارشد؛ ۳ سرپرست؛ ۴ مدیر/شریک", ""), ("emp", "—", "محل کار", "۱ سازمان حسابرسی؛ ۲ مؤسسهٔ خصوصی؛ ۳ سایر", ""), ("exp", "—", "سابقه (سال)", "", ""), ("age", "—", "سن", "", ""), ("gender", "—", "جنسیت", "۱ مرد؛ ۰ زن", ""), ("edu", "—", "تحصیلات", "۱ کارشناسی؛ ۲ ارشد؛ ۳ دکتری", ""), ("cert", "—", "عضو جامعهٔ حسابداران رسمی", "۱ بله؛ ۰ خیر", ""), ("senior", "—", "رتبهٔ سرپرست و بالاتر", "۱ بله؛ ۰ خیر", "")]
with pd.ExcelWriter(os.path.join(D, "Data_and_Results.xlsx")) as w:
    df.to_excel(w, sheet_name="Data", index=False); pd.DataFrame(cb, columns=["Item", "Latent", "Construct", "Wording", "Origin"]).to_excel(w, sheet_name="Codebook", index=False)
    pd.DataFrame(R["rel"]).T.to_excel(w, sheet_name="Reliability"); pd.DataFrame(R["paths"]).T.to_excel(w, sheet_name="Paths"); pd.DataFrame(R["indirect"]).T.to_excel(w, sheet_name="Indirect_effects"); pd.DataFrame(R["models"]).T.to_excel(w, sheet_name="Competing_models")
for k, nm in [(1, "Figure1_conceptual"), (2, "Figure2_estimated"), (3, "Figure3_simple_slopes"), (4, "Figure4_indirect_effects")]: shutil.copy(os.path.join(ROOT, "output", f"fa_fig{k}.png"), os.path.join(D, nm + ".png"))
open(os.path.join(D, "README.md"), "w", encoding="utf-8").write("""# بستهٔ پژوهش — چرا حسابرسان سکوت می‌کنند؟
- `Paper_FA_Auditor_Silence.docx`: مقاله (فارسی، چکیدهٔ انگلیسی در پایان)
- `Extended_Abstract_Persian.docx`, `Extended_Abstract_English.docx`: چکیدهٔ گسترده
- `Questionnaire_Persian.docx`: پرسشنامه با منبع و نوع منشأ (محقق‌ساخته/پژوهش‌محور) هر متغیر
- `Colab_SEM_Analysis.ipynb`, `Analysis_SEM.py`: تحلیل کامل (semopy)؛ `Generate_Data.py`: تولید دادهٔ نمونه؛ `Data_and_Results.xlsx`: داده و نتایج؛ نمودارها
**نکتهٔ مهم:** داده‌های همراه این بسته نمونه‌ای برای آزمون کد است. پیش از ارسال به مجله، پرسشنامه را اجرا کنید، CSV واقعی را با همان نام ستون‌ها جایگزین (`DATA_PATH`) و تحلیل و متن را با اعداد واقعی به‌روز کنید؛ موارد زردرنگ (نمونه‌گیری، تأییدیهٔ اخلاق، CVR/CVI و جزئیات منابع فارسی) باید با اطلاعات واقعی پر شود. DOIها را با Crossref بررسی کنید.
""")
print("package ok")
