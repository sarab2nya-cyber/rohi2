#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تبدیل فایل‌های .xml/.html رهاورد نوین (جدول HTML با پسوند xml) به .xlsx برای import در استتا.
اجرا:  python xml_to_xlsx.py data_in/1403 data_in/1404
خروجی: کنار هر فایل یک .xlsx با همان نام (هر جدول یک شیت) + گزارش ابعاد.
نصب: pip install pandas lxml openpyxl beautifulsoup4 html5lib
"""
import sys, pathlib, io
import pandas as pd

def read_tables(path):
    raw = pathlib.Path(path).read_bytes()
    for enc in ("utf-8-sig", "utf-8", "cp1256", "windows-1256"):
        try: txt = raw.decode(enc); break
        except UnicodeDecodeError: continue
    try:
        return pd.read_html(io.StringIO(txt), flavor="lxml")
    except Exception:
        try: return pd.read_html(io.StringIO(txt))
        except Exception:
            try: return [pd.read_xml(io.StringIO(txt))]      # xml واقعی
            except Exception as e: print("خواندن ممکن نشد:", path, e); return []

def convert(folder):
    for f in sorted(pathlib.Path(folder).glob("*.xml")) + sorted(pathlib.Path(folder).glob("*.html")):
        tabs = read_tables(f)
        if not tabs: continue
        out = f.with_suffix(".xlsx")
        with pd.ExcelWriter(out) as w:
            for i, t in enumerate(tabs):
                t = t.copy(); t.columns = [" ".join(map(str, c)).strip() if isinstance(c, tuple) else str(c) for c in t.columns]
                t.to_excel(w, sheet_name=f"t{i+1}"[:31], index=False)
        print(f"{f.name}: {len(tabs)} جدول؛ ابعاد " + "، ".join(f"{t.shape}" for t in tabs[:5]), "→", out.name)

if __name__ == "__main__":
    for d in sys.argv[1:] or ["."]: convert(d)
