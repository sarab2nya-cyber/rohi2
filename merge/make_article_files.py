#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
از خروجی build_variables.py (نمونه ۹ از ۱۱ سال) برای هر مقاله یک فایل آماده تحلیل می‌سازد:
  article1_data_min9.xlsx/.dta  (انحراف مصرف تسهیلات؛ شامل gvar رویدادپژوهی)
  article2_data_min9.xlsx/.dta  (بندهای پیمان/نکول؛ شامل تقسیم آموزش-آزمون زمانی و برچسب فولد اعتبارسنجی)
اجرا: python make_article_files.py --in analysis_1394_1404.xlsx --outdir .
"""
import argparse, pathlib
import numpy as np, pandas as pd

ID = ["company", "firm_id", "ticker", "industry", "year", "market"]
A1_VARS = ["NONOP", "LOAN", "LARGE", "DIV", "OPINV", "SIZE", "LEV", "LEV_INT", "ROA", "ROA_NI", "CFO_TA", "CASH_TA", "TANG", "GROW", "MTB", "Q", "LOSS", "ICR", "DIV_PAYOUT", "AGE_PROXY", "F_ROA", "F_LOSS"]
A2_PRED = ["CR", "QR", "WC", "LEV", "LEV_INT", "ICR", "DSCR", "CFO_TD", "ROA", "ROA_NI", "TNW", "AQ", "CASH_TA", "ZSCORE", "DEBT_EBIT", "DEBT_OPCASH", "DIV", "SIZE", "CFO_TA", "GROW"]
A2_DV = ["F_DEF_ICR", "F_LOSS", "F_DEF_Z", "F_DEF_141", "F_DEF_NEGEQ", "F_DEF_ANY", "DEF_141", "DEF_Z", "DEF_ICR"]
EXTRA_A1 = ["AUDSIZE", "AUDSPEC", "AUDTEN", "AUDSWITCH", "AUDOPN", "STATE", "CONC", "INST"]       # خالی؛ بعداً از rohi_extra/auditor_extract پر شود
EXTRA_A2 = ["AUDSIZE", "AUDSPEC", "AUDTEN", "AUDOPN", "DEF_BANK"]

def desc(df, cols):
    d = df[[c for c in cols if c in df]].describe(percentiles=[.01, .5, .99]).T.reset_index().rename(columns={"index": "variable"})
    d["missing_%"] = [round(100 * df[c].isna().mean(), 1) for c in d["variable"]]; return d

def main(a):
    x = pd.ExcelFile(a.inp); m = x.parse("Sample_Master"); rep = x.parse("Screening_Report"); dic = x.parse("Variable_Dictionary"); na = x.parse("Not_Available")
    out = pathlib.Path(a.outdir)
    w = lambda c: [c, c + "_w"]
    # ---------------- مقاله ۱ ----------------
    d1 = m[m["A1_sample"] == 1].copy()
    first_large = d1[d1["LARGE"] == 1].groupby("firm_id")["year"].min()
    d1["gvar"] = d1["firm_id"].map(first_large).fillna(0).astype(int)                       # نخستین سال وام بزرگ (۰ = هرگز) برای csdid
    d1["event_time"] = np.where(d1["gvar"] > 0, d1["year"] - d1["gvar"], np.nan)
    d1["ever_large"] = (d1["gvar"] > 0).astype(int)
    def clean_gvar(thr):
        """gvar تمیز: نخستین سالی که LOAN ≥ thr و دو سال قبل (مشاهده‌شده و متوالی) LOAN < thr بوده؛ هرگز = ۰؛ سانسور چپ/نامشخص = NaN"""
        lk = d1.set_index(["firm_id", "year"])["LOAN"]; res = {}
        for fid, g in d1.groupby("firm_id"):
            ys = sorted(g["year"]); big = [y for y in ys if lk.loc[(fid, y)] >= thr]
            if not big: res[fid] = 0; continue
            y0 = big[0]; p1, p2 = (fid, y0 - 1), (fid, y0 - 2)
            ok = p1 in lk.index and p2 in lk.index and lk.loc[p1] < thr and lk.loc[p2] < thr
            res[fid] = y0 if ok else np.nan
        return d1["firm_id"].map(res)
    d1["LARGE10"] = np.where(d1["LOAN"].notna(), (d1["LOAN"] >= 0.10).astype(float), np.nan)
    d1["gvar_clean5"] = clean_gvar(0.05); d1["gvar_clean10"] = clean_gvar(0.10)
    cols1 = ID + [c for v in A1_VARS if v in d1 for c in ([v, v + "_w"] if v + "_w" in d1 else [v])] + ["gvar", "gvar_clean5", "gvar_clean10", "LARGE10", "event_time", "ever_large", "audited_flag", "restated", "tse_only", "A1_balanced"]
    for c in EXTRA_A1: d1[c] = np.nan
    d1 = d1[[c for c in cols1 if c in d1] + EXTRA_A1]
    # ---------------- مقاله ۲ ----------------
    d2 = m[m["A2_sample"] == 1].copy()
    d2["oos_test"] = (d2["year"] >= 1401).astype(int)                                      # آموزش: ۱۳۹۵–۱۴۰۰ ؛ آزمون زمانی: ۱۴۰۱–۱۴۰۳
    rng = np.random.default_rng(1234); firms = d2["firm_id"].unique(); fold = dict(zip(firms, rng.integers(1, 11, len(firms))))
    d2["cv_fold"] = d2["firm_id"].map(fold)                                                 # فولد ۱۰تایی براساس شرکت (جلوگیری از نشت شرکت)
    for c in EXTRA_A2: d2[c] = np.nan
    cols2 = ID + [c for v in A2_DV for c in [v]] + [c for v in A2_PRED if v in d2 for c in ([v, v + "_w"] if v + "_w" in d2 else [v])] + ["oos_test", "cv_fold", "A2_balanced_1395_1403", "audited_flag", "tse_only"]
    d2 = d2[[c for c in cols2 if c in d2] + EXTRA_A2]
    ev = []
    for dv in ("F_DEF_ICR", "F_LOSS", "F_DEF_Z", "F_DEF_141", "F_DEF_NEGEQ"):
        g = d2.groupby("year")[dv].agg(["sum", "count"]).reset_index(); g["variable"] = dv; ev.append(g)
    ev = pd.concat(ev)[["variable", "year", "sum", "count"]].rename(columns={"sum": "events", "count": "n"})
    split = d2.groupby("oos_test").agg(rows=("firm_id", "size"), firms=("firm_id", "nunique"), ev_ICR=("F_DEF_ICR", "sum"), ev_LOSS=("F_LOSS", "sum"), ev_Z=("F_DEF_Z", "sum"), ev_141=("F_DEF_141", "sum"), ev_NEGEQ=("F_DEF_NEGEQ", "sum")).reset_index()
    notes1 = pd.DataFrame({"نکته": [
        "متغیر وابسته مدل ۱: NONOP (خام) یا NONOP_w (وینزورایز ۱٪/۹۹٪)؛ متغیر مستقل: LOAN؛ اثر ثابت شرکت و سال و خطای خوشه‌ای شرکت.",
        "رویدادپژوهی: gvar = نخستین سال LARGE=1 (۰ = هرگز) ولی ۸۸٪ شرکت‌ها حداقل یک بار وام بزرگ دارند و بسیاری در همان ۱۳۹۵ (سانسور چپ) هستند؛ پیشنهاد: gvar_clean5 / gvar_clean10 (رویداد تمیز؛ ۰ = هرگز؛ خالی = سانسور) با csdid: csdid NONOP controls if !missing(gvar_clean10), ivar(firm_id) time(year) gvar(gvar_clean10) notyet.",
        "گروه کنترل «هرگز تیمارنشده» کوچک است؛ از کنترل «هنوز تیمارنشده» (notyet) استفاده و آستانه ۱۰٪ را نسبت به ۵٪ مقایسه کنید.",
        "نمونه نامتوازن است (۹ از ۱۱ سال)؛ سال پایه ۱۳۹۴ فقط برای تأخیرها استفاده شده و در این فایل نیست.",
        "ستون‌های AUDSIZE/AUDSPEC/AUDTEN/AUDSWITCH/AUDOPN/STATE/CONC/INST خالی‌اند؛ با خروجی auditor_extract.py و rohi_extra.py پر شوند.",
        "جریان نقد ۱۴۰۳ برای حدود ۲۶٪ شرکت‌ها موجود نیست (LOAN آن سال کمتر مشاهده دارد)؛ اثر ثابت سال بگذارید و تحلیل بدون ۱۴۰۳ هم گزارش کنید.",
        "DIV برای LOAN<۰٫۰۲ صفر است؛ تعریف جایگزین با آستانه‌های ۱٪/۵٪ را در آزمون استحکام بسنجید.",
    ]})
    notes2 = pd.DataFrame({"نکته": [
        "متغیر وابسته پیشنهادی (اصلی): F_DEF_ICR (پوشش بهره سال بعد < ۱)؛ جایگزین‌ها F_LOSS و F_DEF_Z. F_DEF_141 و F_DEF_NEGEQ رویداد کم دارند (شیت Events_by_year) و فقط برای تحلیل حساسیت‌اند.",
        "F_DEF_Z مبتنی بر Z″ است و اجزای آن (WC، ROA، TNW/LEV) همان پیش‌بین‌ها هستند: خطر دور (circularity)؛ در مدل F_DEF_Z از ZSCORE و اجزایش پیش‌بین نسازید.",
        "نشت اطلاعات: ZSCORE نباید هم پیش‌بین و هم (در F_DEF_Z/F_DEF_ANY) جزء متغیر وابسته باشد؛ در مدل‌های Z″ آن را کنار بگذارید.",
        "اعتبارسنجی: oos_test=1 (۱۴۰۱–۱۴۰۳) آزمون زمانی؛ cv_fold (۱ تا ۱۰) برای اعتبارسنجی متقاطع براساس شرکت (lasso: اعتبارسنجی در کد را با این فولدها تنظیم کنید).",
        "AQ فقط برای بخشی از مشاهدات موجود است (پنجره ۵ ساله)؛ در لاسو ردیف‌های ناقص حذف می‌شوند یا AQ را کنار بگذارید.",
        "سوگیری بقا: شرکت‌هایی که زود از بورس رفته‌اند در نمونه نیستند؛ در بخش محدودیت‌ها ذکر شود.",
        "DEF_BANK (تسهیلات سررسیدگذشته) از صورت‌های مالی درنمی‌آید؛ ستون خالی است.",
    ]})
    for name, d, ex, nt in (("article1_data_min9", d1, None, notes1), ("article2_data_min9", d2, (ev, split), notes2)):
        with pd.ExcelWriter(out / f"{name}.xlsx", engine="openpyxl") as wr:
            d.to_excel(wr, sheet_name="Data", index=False)
            rep.to_excel(wr, sheet_name="Screening_Report", index=False)
            use = [c for c in d.columns]
            dic[dic["مقاله"].astype(str).str.contains("۱" if "1" in name else "۲") | dic["مقاله"].astype(str).str.contains("—")].to_excel(wr, sheet_name="Variable_Dictionary", index=False)
            desc(d, [c for c in d.columns if c not in ID and not c.startswith(("AUD", "STATE", "CONC", "INST", "DEF_BANK"))]).to_excel(wr, sheet_name="Descriptives", index=False)
            if ex: ex[0].to_excel(wr, sheet_name="Events_by_year", index=False); ex[1].to_excel(wr, sheet_name="Train_Test_split", index=False)
            na.to_excel(wr, sheet_name="Not_Available", index=False)
            nt.to_excel(wr, sheet_name="Modeling_Notes", index=False)
        dd = d.replace([np.inf, -np.inf], np.nan)
        dd = dd.dropna(axis=1, how="all") if False else dd
        try: dd.to_stata(out / f"{name}.dta", write_index=False, version=118)
        except Exception as e: print("dta:", e)
        print(name, d.shape, "شرکت", d.firm_id.nunique())
    print({c: (int((d1[c] > 0).sum()), int((d1[c] == 0).sum()), int(d1[c].isna().sum())) for c in ("gvar_clean5", "gvar_clean10")}, "(رویدادی، هرگز، سانسور)  ردیف‌ها")
    print(d1.groupby("firm_id")[["gvar_clean5", "gvar_clean10"]].first().apply(lambda c: ((c > 0).sum(), (c == 0).sum(), c.isna().sum())).to_dict())
    print(split.to_string(index=False)); print(ev.groupby("variable").events.sum().to_dict())

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--in", dest="inp", required=True); ap.add_argument("--outdir", default=".")
    main(ap.parse_args())
