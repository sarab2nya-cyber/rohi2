#!/usr/bin/env python3
"""ساخت پنل از خروجی‌های codal_collector (cells_*.csv، letters.csv) و tsetmc_collector،
اعمال غربالگری، ساخت همه متغیرهای دو مقاله و خروجی panel.csv / panel.dta.
اجرا: python build_panel.py
"""
import re, glob, numpy as np, pandas as pd
import config as C
from text_utils import norm, to_num

SHEET_KEYS = {"bs": ["وضعیت مالی", "ترازنامه"], "is": ["سود و زیان", "سود (زیان)"], "cf": ["جریان", "وجوه نقد"]}

def sheet_kind(title):
    t = norm(title or "")
    for k, keys in SHEET_KEYS.items():
        if any(norm(x) in t for x in keys): return k

def extract_items(cells):
    """cells: sheet,row,col,value -> {var: مقدار سال جاری (اولین عدد ردیف)}"""
    out = {}
    cells = cells.copy(); cells["kind"] = cells["sheet"].map(sheet_kind)
    for (sh, kind, row), g in cells.groupby(["sheet", "kind", "row"]):
        if kind is None: continue
        g = g.sort_values("col")
        label = next((norm(v) for v in g["value"] if to_num(v) is None and str(v).strip()), None)
        nums = [to_num(v) for v in g["value"] if to_num(v) is not None]
        if not label or not nums: continue
        for var, (k, pat) in C.ITEMS.items():
            if k == kind and var not in out and re.search(pat, label):
                out[var] = nums[0]
    return out

def fiscal_end(title):
    m = re.search(r"(\d{4})/(\d{2}/\d{2})", norm(title))
    return (int(m.group(1)), m.group(2)) if m else (None, None)

def main():
    letters = pd.read_csv(C.OUT / "letters.csv")
    rows = []
    for f in glob.glob(str(C.OUT / "cells_*.csv")):
        cells = pd.read_csv(f)
        tn = cells["TracingNo"].iloc[0]
        meta = letters[letters["TracingNo"] == tn].iloc[0]
        yr, md = fiscal_end(meta["Title"])
        d = {"TracingNo": tn, "Symbol": meta["Symbol"], "year": yr, "fy_end": md,
             "publish": meta.get("PublishDateTime")}
        d.update(extract_items(cells)); rows.append(d)
    df = pd.DataFrame(rows)
    for v in C.ITEMS:
        if v not in df: df[v] = np.nan   # ردیف پیدا نشده: NaN (بعداً دستی کنترل شود)
    # اصلاحیه‌ها: آخرین انتشار هر نماد-سال
    df = df.sort_values("publish").drop_duplicates(["Symbol", "year"], keep="last")

    # ---- غربالگری ----
    s = C.SCREEN
    df = df[df["year"].between(s["year_from"] - 1, s["year_to"])]
    df = df[df["fy_end"] == s["fiscal_year_end"]]
    tse = C.OUT / "tse_instruments.csv"
    if tse.exists():
        ins = pd.read_csv(tse)[["Symbol", "sector", "shares"]]
        df = df.merge(ins, on="Symbol", how="left")
        bad = "|".join(map(re.escape, s["exclude_sectors"]))
        df = df[~df["sector"].fillna("").map(norm).str.contains(bad)]
    need = ["TA", "TL", "EQUITY", "CA", "CL", "CFO"]
    df = df.dropna(subset=need)
    df = df.sort_values(["Symbol", "year"])
    # حداقل سال‌های متوالی
    def run_ok(g):
        y = g["year"].to_numpy(); best = cur = 1
        for a, b in zip(y[:-1], y[1:]):
            cur = cur + 1 if b == a + 1 else 1; best = max(best, cur)
        return best >= s["min_consecutive_years"]
    df = df.groupby("Symbol").filter(run_ok)
    if s["require_loans_any_year"]:
        df = df.groupby("Symbol").filter(lambda g: (g[["LOAN_IN", "LOAN_REPAY"]].abs().sum().sum() > 0))

    # ---- ساخت متغیرها ----
    g = df.groupby("Symbol")
    for v in ["TA", "ST_INV", "LT_INV", "INV_PROP", "REL_REC", "LOAN_BAL"]:
        if v in df: df["L_" + v] = g[v].shift(1)
    z = lambda c: df[c].fillna(0) if c in df else 0
    df["LOAN"] = (z("LOAN_IN") - z("LOAN_REPAY").abs()) / df["L_TA"]
    nonop = z("ST_INV") + z("LT_INV") + z("INV_PROP") + z("REL_REC")
    df["NONOP_AMT"] = nonop
    df["NONOP"] = (nonop - nonop.groupby(df["Symbol"]).shift(1)) / df["L_TA"]
    d_nonop = nonop - nonop.groupby(df["Symbol"]).shift(1)
    net = z("LOAN_IN") - z("LOAN_REPAY").abs()
    df["DIV"] = np.where(df["LOAN"] >= 0.02, (d_nonop / net).clip(0, 1), 0.0)
    df["LARGE"] = (df["LOAN"] >= 0.05).astype(int)
    df["SIZE"] = np.log(df["TA"]); df["LEV"] = df["TL"] / df["TA"]
    df["ROA"] = df["EBIT"] / df["L_TA"]; df["CFO_TA"] = df["CFO"] / df["L_TA"]
    df["CASH_TA"] = df["CASH"] / df["TA"]; df["TANG"] = df["PPE"] / df["TA"]
    df["GROW"] = df["SALES"] / g["SALES"].shift(1) - 1
    df["LOSS"] = (df["NI"] < 0).astype(int)
    df["AGE_PROXY"] = g.cumcount() + 1
    # معیارهای مقاله ۲
    df["CR"] = df["CA"] / df["CL"]; df["QR"] = (df["CA"] - df["INVENTORY"]) / df["CL"]
    df["WC"] = (df["CA"] - df["CL"]) / df["TA"]
    df["ICR"] = df["EBIT"] / df["FINCOST"].abs()
    df["EBITDA"] = df["EBIT"] + z("DEPRECIATION")
    df["DEBT_EBITDA"] = df["TL"] / df["EBITDA"]       # جایگزین: فقط بدهی بهره‌دار پس از ورود یادداشت
    df["CFO_TD"] = df["CFO"] / df["TL"]
    df["TNW"] = (df["EQUITY"] - z("INTANG")) / df["TA"]
    df["ZSCORE"] = (6.56 * df["WC"] + 3.26 * df["RETEARN"] / df["TA"] +
                    6.72 * df["EBIT"] / df["TA"] + 1.05 * df["EQUITY"] / df["TL"])
    # متغیر وابسته ماده ۱۴۱: زیان انباشته >= نصف سرمایه
    df["DEF_141"] = ((-df["RETEARN"]).clip(lower=0) >= 0.5 * df["CAPITAL"]).astype(int)
    df["F_DEF_141"] = df.groupby("Symbol")["DEF_141"].shift(-1)
    df["F_DEF_Z"] = (df.groupby("Symbol")["ZSCORE"].shift(-1) < 1.1).astype(float)
    df["F_ROA"] = df.groupby("Symbol")["ROA"].shift(-1)
    # مالکیت و حسابرس (در صورت وجود فایل‌ها)
    h = C.OUT / "tse_holders.csv"
    if h.exists():
        hd = pd.read_csv(h)
        hd["pct"] = pd.to_numeric(hd["pct"], errors="coerce")
        top = hd.sort_values("pct", ascending=False).groupby("Symbol").head(5)
        conc = top.groupby("Symbol")["pct"].apply(lambda x: ((x / 100) ** 2).sum()).rename("CONC")
        df = df.merge(conc, on="Symbol", how="left")
    df.to_csv(C.OUT / "panel.csv", index=False, encoding="utf-8-sig")
    try: df.to_stata(C.OUT / "panel.dta", write_index=False, version=118)
    except Exception as e: print("dta ذخیره نشد:", e)
    print("پنل:", df.shape, "شرکت:", df["Symbol"].nunique())
    print("متغیرهای دستی/نیمه‌خودکار: AUDQ، STATE، OVERDUE، PENALTY، DEF_BANK، REL_REC (از یادداشت‌ها)")

if __name__ == "__main__": main()
