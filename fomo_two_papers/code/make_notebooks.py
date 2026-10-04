# -*- coding: utf-8 -*-
import json, os
H = os.path.dirname(os.path.abspath(__file__))
rd = lambda f: open(os.path.join(H, f), encoding="utf-8").read()
md = lambda t: {"cell_type": "markdown", "metadata": {}, "source": t.splitlines(True)}
cd = lambda t: {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": t.splitlines(True)}
INSTALL = '!pip -q install "setuptools<58" wheel\n!pip -q install --no-build-isolation semopy==2.3.11\n!pip -q install pandas numpy scipy statsmodels scikit-learn shap matplotlib arabic-reshaper python-bidi openpyxl'
def nb(name, title, script, extra):
    cells = [md(f"# {title}\nاجرای ترتیبی سلول‌ها در Google Colab. داده‌ها **شبیه‌سازی‌شده**‌اند؛ برای داده‌ٔ واقعی مقدار `DATA_PATH` را در سلول اسکریپت به مسیر CSV تغییر دهید (نام ستون‌ها مطابق دفترکد پرسشنامه)."),
             cd(INSTALL), md("## ماژول‌های کمکی (simlib / mgcfa)"), cd("%%writefile simlib.py\n" + rd("simlib.py"))]
    if extra: cells.append(cd("%%writefile mgcfa.py\n" + rd("mgcfa.py")))
    cells += [md("## تحلیل اصلی"), cd(rd(script).replace('HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else "."', 'HERE = "."')),
              md("## دانلود خروجی‌ها"), cd("import shutil\nfor d in ['paper1','paper2','data']:\n    if os.path.isdir('../'+d): shutil.make_archive(d,'zip','../'+d)\ntry:\n    from google.colab import files\n    [files.download(f) for f in os.listdir('.') if f.endswith('.zip')]\nexcept ImportError: pass")]
    json.dump({"cells": cells, "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3"}, "colab": {"provenance": []}}, "nbformat": 4, "nbformat_minor": 5},
              open(os.path.join(H, "..", name), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
nb("colab_paper1.ipynb", "مقالهٔ ۱: شبکه‌های اجتماعی ← فومو ← رفتار توده‌وار ← کیفیت تصمیم (تعدیل‌گر: اطلاعات حسابداری)", "paper1_analysis.py", False)
nb("colab_paper2.ipynb", "مقالهٔ ۲: پیش‌برنده‌های فومو، ناوردایی اندازه‌گیری، مقایسهٔ گروه‌ها و یادگیری ماشین", "paper2_analysis.py", True)
print("notebooks ok")
