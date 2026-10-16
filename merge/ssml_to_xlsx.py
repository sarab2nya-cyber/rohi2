#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تبدیل فایل‌های XML اکسل (SpreadsheetML رهاورد نوین) به xlsx با همان قالب فایل‌های File1..File6 سال ۱۴۰۳
(ستون اول Symbol = نام شرکت، ستون دوم Year؛ بقیه ستون‌ها با همان ترتیب)، برای استفاده در استتا.

اجرا (۱۴۰۴):  python ssml_to_xlsx.py --year 1404 --in raw/1404 --out xlsx1404
نام فایل‌های ورودی (انگلیسی): balance income cashflow ratios ret12|ret_annual ret16  (.xml)
خروجی: File1_<year>.xlsx (ترازنامه) File2 (سود و زیان) File3 (جریان نقد) File4 (نسبت‌ها) File5 (بازده ۱۲ماهه/سالانه) File6 (۱۶ماهه)
"""
import argparse, pathlib, sys
import pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import ssml

MAP = {"balance": 1, "income": 2, "cashflow": 3, "ratios": 4, "ret12": 5, "ret_annual": 5, "ret16": 6}

def load(path):
    rows = list(ssml.read(path).values())[0]
    hdr = [str(h) if h is not None else f"_c{i}" for i, h in enumerate(rows[0])]
    w = len(hdr)
    return pd.DataFrame([(r + [None] * w)[:w] for r in rows[1:]], columns=hdr)

def standardize(df, year):
    df = df.copy()
    name = "شرکت" if "شرکت" in df else "نام شرکت"
    df = df.rename(columns={name: "Symbol"})
    ycol = "سال مالی" if "سال مالی" in df else ("سال" if "سال" in df else None)
    if ycol: df = df.rename(columns={ycol: "Year"})
    else: df["Year"] = year
    rest = [c for c in df.columns if c not in ("Symbol", "Year")]
    df = df[["Symbol", "Year"] + rest]
    for c in rest:                                   # اعداد رشته‌ای → عدد (ستون‌های متنی دست‌نخورده)
        conv = pd.to_numeric(df[c], errors="coerce")
        if conv.notna().sum() >= 0.9 * df[c].notna().sum() and df[c].notna().any(): df[c] = conv
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").fillna(year).astype(int)
    return df

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--in", dest="inp", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args(); out = pathlib.Path(a.out); out.mkdir(exist_ok=True)
    for f in sorted(pathlib.Path(a.inp).glob("*.xml")):
        k = MAP.get(f.stem)
        if k is None: print("نادیده:", f.name); continue
        d = standardize(load(str(f)), a.year); o = out / f"File{k}_{a.year}.xlsx"
        d.to_excel(o, index=False, sheet_name="Sheet1"); print(f.name, "→", o.name, d.shape)
