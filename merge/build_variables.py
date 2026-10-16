#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ساخت همه متغیرهای قابل استخراج از صورت‌های مالی برای مقاله ۱ (DIV/انحراف تسهیلات) و مقاله ۲ (بندهای پیمان/نکول)
+ غربالگری مرحله‌به‌مرحله با گزارش حذف (شیت جدا) + نمونه نهایی هر مقاله.

اجرا:  python build_variables.py --panel panel_1380_1404.xlsx --out analysis_1394_1404.xlsx
خروجی (اکسل): Screening_Report, Sample_Master, Excluded_Rows, Variable_Dictionary, Not_Available_From_Statements
ملاک اصلی: شرکت‌های بورسی (بورس تهران + فرابورس؛ ستون tse_only برای پژوهش فقط بورس تهران).
واحد: ارقام ریالی صورت‌ها «میلیون ریال»؛ ارزش بازار (ارزش روز) در منبع «ریال» است و در این کد به میلیون ریال تبدیل می‌شود.
"""
import argparse, re, sys
import numpy as np, pandas as pd

Y0, Y1 = 1394, 1404                       # ۱۳۹۴ = سال پایه (برای تأخیرها)، ۱۳۹۵–۱۴۰۴ = ده سال تحلیل
ANA0 = Y0 + 1
MIN_RUN = 3
MIN_YEARS = 9                             # حداقل سال‌های حضور از ۱۱ (۱۱ = پنل کاملاً متوازن)
INCLUDE_FARA = False                      # فقط بورس تهران؛ برای افزودن فرابورس: --include-fara
FIN_IND = None                            # صنایع خارج از فهرست اکسل اصلی = مالی/سرمایه‌گذاری/...
HOLDING_IND = "چندرشته ای صنعتی"          # هلدینگ‌های صنعتی (سرمایه‌گذاری برای آنها دارایی عملیاتی است)
FIN_NAME = re.compile(r"^بانک|بانک |بیمه|لیزینگ|^سر\.|سرمایه گذاری|مالی|ارزش آفرینان|سپرده گذاری|تامین آتیه|تعاونی|اعتباری|کارگزاری|صندوق|تامین سرمایه|بورس|واسپاری")

# موقعیت ستون‌ها در چیدمان ثابت اکسل (صفرمبنا)
POS = dict(company=0, firm_id=1, year=2, ind_code=3, ind_group=4, industry=5, category=6, market=7, ticker=8, approval_date=9,
           report_type=10, consolidated=11, audited=12, restated=13,
           cash=14, st_inv=15, trade_rec=21, rel_rec=23, inventory=45, tca=59, lt_inv=61, intang=75, ppe_net=82, tnca=83, ta=84,
           loan_st=99, tcl=113, loan_lt=118, tl=124, capital=126, ret_earn=127, equity=144,
           mktcap_rial=163, revenue=226, cogs=227, ebit=241, fin_cost=246, ebt=264, tax=265, net_income=267, eps=287,
           cfo=298, op_cash=296, capex_ppe=302, loan_in=330, loan_repay=331, div_paid=353,
           market1=156, market2=289, ret12=414, ret16=424, price_end12=413, dps12=411, liq12=415)

def lag(df, col, k=1):
    """مقدار k سال قبل همان شرکت (فقط اگر سال قبل دقیقاً موجود باشد)"""
    key = df[["firm_id", "year"]].copy(); key["year"] -= k
    m = key.merge(df[["firm_id", "year", col]], on=["firm_id", "year"], how="left")
    return m[col].values

def lead(df, col, k=1): return lag(df, col, -k)

def winsor(s, lo=0.01, hi=0.99):
    a, b = s.quantile([lo, hi]); return s.clip(a, b)

def dd_aq(df):
    """Dechow-Dichev (2002): ΔWC_t = φ0 + φ1 CFO_{t-1} + φ2 CFO_t + φ3 CFO_{t+1} (مقطعی هر سال)؛ AQ = انحراف معیار ۵ ساله باقیمانده‌ها (≥۳ مشاهده)"""
    d = df[["firm_id", "year", "dWC", "CFO_l1", "CFO_0", "CFO_f1"]].dropna().copy(); d["res"] = np.nan
    for y, g in d.groupby("year"):
        if len(g) < 30: continue
        X = np.column_stack([np.ones(len(g)), g["CFO_l1"], g["CFO_0"], g["CFO_f1"]])
        b, *_ = np.linalg.lstsq(X, g["dWC"].values, rcond=None); d.loc[g.index, "res"] = g["dWC"].values - X @ b
    out = df[["firm_id", "year"]].merge(d[["firm_id", "year", "res"]], on=["firm_id", "year"], how="left")
    res = out.pivot_table(index="firm_id", columns="year", values="res")
    aq = res.T.rolling(5, min_periods=3).std().T.stack().rename("AQ").reset_index()
    return df[["firm_id", "year"]].merge(aq, on=["firm_id", "year"], how="left")["AQ"].values

def main(a):
    raw = pd.read_excel(a.panel)
    cols = list(raw.columns)
    df = pd.DataFrame({k: raw.iloc[:, i] for k, i in POS.items()})
    for c in ("data_source", "new_company", "industry_missing", "industry_in_main_list"):
        df[c] = raw[c] if c in raw else np.nan
    df["market"] = df["market"].fillna(df["market1"]).fillna(df["market2"])
    df = df.drop(columns=["market1", "market2"])
    df["year"] = df["year"].astype(int); df["firm_id"] = df["firm_id"].astype(int)
    df = df.sort_values(["firm_id", "year"]).reset_index(drop=True)
    num = ["cash", "st_inv", "trade_rec", "rel_rec", "inventory", "tca", "lt_inv", "intang", "ppe_net", "tnca", "ta", "loan_st", "tcl",
           "loan_lt", "tl", "capital", "ret_earn", "equity", "mktcap_rial", "revenue", "cogs", "ebit", "fin_cost", "ebt", "tax", "net_income",
           "eps", "cfo", "op_cash", "capex_ppe", "loan_in", "loan_repay", "div_paid", "ret12", "ret16", "price_end12", "dps12", "liq12"]
    for c in num: df[c] = pd.to_numeric(df[c], errors="coerce")
    df["mktcap"] = df["mktcap_rial"] / 1e6                              # → میلیون ریال

    # ---------------- ساخت متغیرها (روی کل پنل، قبل از غربالگری، تا تأخیرها درست باشند) ----------------
    has_cf = df["cfo"].notna()
    for c in ("loan_in", "loan_repay", "capex_ppe", "div_paid"):            # سلول خالی در صورت جریان نقد موجود = صفر
        df[c + "_f"] = np.where(has_cf, df[c].fillna(0), np.nan)
    df["ta_l1"] = lag(df, "ta"); df["ta_f1"] = lead(df, "ta")
    df["avg_ta"] = (df["ta"] + df["ta_l1"]) / 2
    df["rev_l1"] = lag(df, "revenue")
    # --- مقاله ۱ ---
    df["LOAN"] = (df["loan_in_f"] - df["loan_repay_f"].abs()) / df["ta_l1"]                  # خالص تسهیلات / دارایی‌های ابتدای دوره
    df["LARGE"] = np.where(df["LOAN"].notna(), (df["LOAN"] >= 0.05).astype(float), np.nan)
    df["NONOP_AMT"] = df[["st_inv", "lt_inv", "rel_rec"]].fillna(0).sum(axis=1).where(df["ta"].notna())
    df["NONOP_l1"] = lag(df, "NONOP_AMT")
    df["NONOP"] = (df["NONOP_AMT"] - df["NONOP_l1"]) / df["ta_l1"]
    net_amt = df["loan_in_f"] - df["loan_repay_f"].abs()
    df["DIV"] = np.where(df["LOAN"] >= 0.02, ((df["NONOP_AMT"] - df["NONOP_l1"]) / net_amt).clip(0, 1), np.where(df["LOAN"].notna() & df["NONOP"].notna(), 0.0, np.nan))
    df["OPINV"] = (df["ppe_net"] - lag(df, "ppe_net") + df["inventory"] - lag(df, "inventory")) / df["ta_l1"]   # سرمایه‌گذاری عملیاتی (ثابت+موجودی)
    df["SIZE"] = np.log(df["ta"].where(df["ta"] > 0))
    df["LEV"] = df["tl"] / df["ta"]
    df["ROA"] = df["ebit"] / df["ta_l1"]
    df["ROA_NI"] = df["net_income"] / df["ta_l1"]
    df["CFO_TA"] = df["cfo"] / df["ta_l1"]
    df["CASH_TA"] = df["cash"] / df["ta"]
    df["TANG"] = df["ppe_net"] / df["ta"]
    df["GROW"] = df["revenue"] / df["rev_l1"] - 1
    df["MTB"] = df["mktcap"] / df["equity"].where(df["equity"] > 0)
    df["Q"] = (df["mktcap"] + df["tl"]) / df["ta"]
    df["LOSS"] = np.where(df["net_income"].notna(), (df["net_income"] < 0).astype(float), np.nan)
    df["ICR"] = df["ebit"] / df["fin_cost"].abs().where(df["fin_cost"].abs() > 0)
    df["AGE_PROXY"] = df.groupby("firm_id")["year"].rank(method="first")                      # سال‌های حضور در پنل (سن واقعی تأسیس موجود نیست)
    df["DEBT_INT"] = df["loan_st"].fillna(0) + df["loan_lt"].fillna(0)                        # بدهی بهره‌دار
    df["LEV_INT"] = df["DEBT_INT"] / df["ta"]
    df["DIV_PAYOUT"] = df["div_paid_f"].abs() / df["net_income"].where(df["net_income"] > 0)
    # --- مقاله ۲: معیارهای کاندید قرارداد ---
    df["CR"] = df["tca"] / df["tcl"]; df["QR"] = (df["tca"] - df["inventory"]) / df["tcl"]
    df["WC"] = (df["tca"] - df["tcl"]) / df["ta"]
    df["DEBT_EBIT"] = df["DEBT_INT"] / df["ebit"].where(df["ebit"] > 0)                       # استهلاک در منبع موجود نیست → EBITDA ساخته نشد
    df["DEBT_OPCASH"] = df["DEBT_INT"] / df["op_cash"].where(df["op_cash"] > 0)
    df["DSCR"] = df["cfo"] / (df["fin_cost"].abs() + df["loan_st"].fillna(0)).where((df["fin_cost"].abs() + df["loan_st"].fillna(0)) > 0)
    df["CFO_TD"] = df["cfo"] / df["tl"]
    df["TNW"] = (df["equity"] - df["intang"].fillna(0)) / df["ta"]
    df["ZSCORE"] = 6.56 * df["WC"] + 3.26 * df["ret_earn"] / df["ta"] + 6.72 * df["ebit"] / df["ta"] + 1.05 * df["equity"] / df["tl"].where(df["tl"] > 0)
    df["dWC"] = ((df["tca"] - lag(df, "tca")) - (df["tcl"] - lag(df, "tcl")) - (df["cash"] - lag(df, "cash")) + (df["loan_st"] - lag(df, "loan_st"))) / df["avg_ta"]
    df["CFO_0"] = df["cfo"] / df["avg_ta"]; df["CFO_l1"] = lag(df, "CFO_0"); df["CFO_f1"] = lead(df, "CFO_0")
    df["AQ"] = dd_aq(df)
    df["DEF_141"] = np.where(df["ret_earn"].notna() & df["capital"].notna(), ((-df["ret_earn"]).clip(lower=0) >= 0.5 * df["capital"]).astype(float), np.nan)
    df["DEF_Z"] = np.where(df["ZSCORE"].notna(), (df["ZSCORE"] < 1.1).astype(float), np.nan)
    df["DEF_ICR"] = np.where(df["ICR"].notna(), (df["ICR"] < 1).astype(float), np.nan)               # پوشش بهره < ۱ (مستقل از Z″)
    df["DEF_NEGEQ"] = np.where(df["equity"].notna(), (df["equity"] < 0).astype(float), np.nan)        # حقوق صاحبان سهام منفی
    for c in ("DEF_141", "DEF_Z", "DEF_ICR", "DEF_NEGEQ", "ROA", "LOSS", "ZSCORE"): df["F_" + c] = lead(df, c)
    df["F_DEF_ANY"] = np.where(df["F_DEF_141"].notna() | df["F_DEF_Z"].notna(), np.fmax(df["F_DEF_141"].fillna(0), df["F_DEF_Z"].fillna(0)), np.nan)
    df["base_year"] = (df["year"] == Y0).astype(int)
    df["tse_only"] = (df["market"] == "بورس تهران").astype(int)
    df["audited_flag"] = np.where(df["audited"].astype(str) == "خیر", 0, 1)

    # ---------------- غربالگری مرحله‌به‌مرحله ----------------
    log, excl = [], []
    alive = pd.Series(True, index=df.index)
    ind_main = set(raw["صنعت"].where(raw["industry_in_main_list"] == 1).dropna())
    def step(name, crit, keep_mask):
        nonlocal alive
        rm = alive & ~keep_mask
        for i in df.index[rm]: excl.append((df.at[i, "company"], df.at[i, "firm_id"], df.at[i, "year"], name))
        n_before = int(alive.sum()); alive = alive & keep_mask
        log.append({"گام": len(log), "معیار غربالگری": name, "توضیح": crit, "ردیف قبل": n_before, "حذف‌شده (ردیف)": int(rm.sum()),
                    "ردیف باقی‌مانده": int(alive.sum()), "شرکت باقی‌مانده": int(df.loc[alive, "firm_id"].nunique()),
                    "شرکت‌های حذف‌شده در این گام": int(df.loc[rm, "firm_id"].nunique())})
    log.append({"گام": 0, "معیار غربالگری": "کل پنل (۱۳۸۰–۱۴۰۴)", "توضیح": "همه ردیف‌های شرکت-سال در فایل ادغام‌شده", "ردیف قبل": len(df), "حذف‌شده (ردیف)": 0,
                "ردیف باقی‌مانده": len(df), "شرکت باقی‌مانده": int(df["firm_id"].nunique()), "شرکت‌های حذف‌شده در این گام": 0})
    mk = ["بورس تهران", "فرابورس"] if INCLUDE_FARA else ["بورس تهران"]
    step("۱) بورسی بودن (ملاک اصلی)", "بازار همان سال = " + " یا ".join(mk) + "؛ فرابورس و ردیف بدون بازار قابل‌شناسایی حذف" if not INCLUDE_FARA else "بازار = بورس تهران یا فرابورس", df["market"].isin(mk))
    step(f"۲) بازه {Y0}–{Y1} (سال پایه + ۱۰ سال)", f"سال‌های قبل از {Y0} حذف (فقط برای ساخت تأخیرها استفاده شده‌اند)", df["year"].between(Y0, Y1))
    step("۳) دسترسی به صورت‌های مالی", "ترازنامه موجود (جمع دارایی، بدهی و حقوق صاحبان سهام) و دارایی > ۰", df[["ta", "tl", "equity"]].notna().all(axis=1) & (df["ta"] > 0))
    step("۴) صورت سود و زیان موجود", "درآمد، سود عملیاتی و سود خالص موجود", df[["revenue", "ebit", "net_income"]].notna().all(axis=1))
    step("۵) صورت‌های حسابرسی‌شده", "حذف ردیف‌هایی که «حسابرسی شده = خیر» (نوع «مجمع» حسابرسی‌شده فرض می‌شود)", df["audited_flag"] == 1)
    fin_ind = df["ind_code"].isna() & df["industry"].notna() | ((df["industry_in_main_list"] == 0))
    fin_name = df["industry"].isna() & df["company"].astype(str).map(lambda s: bool(FIN_NAME.search(s)))
    step("۶) حذف شرکت‌های مالی", "بانک، بیمه، لیزینگ، سرمایه‌گذاری، واسطه‌گری مالی و ...: صنعت خارج از فهرست اکسل اصلی، یا (صنعت نامشخص و نام مالی)", ~(fin_ind | fin_name))
    inv_name = df["company"].astype(str).str.contains(r"سرمایه گذاری|هلدینگ|^سر\.", regex=True)
    step("۷) حذف هلدینگ و شرکت‌های سرمایه‌گذاری", f"صنعت «{HOLDING_IND}» یا نام شامل «سرمایه‌گذاری/هلدینگ» (سرمایه‌گذاری برای آنها دارایی عملیاتی است و DIV بی‌معنی می‌شود)", (df["industry"].astype(str) != HOLDING_IND) & ~inv_name)
    step("۸) سال مالی ۱۲ ماهه", "داده‌های رهاورد همه ۱۲ ماهه‌اند؛ پایان ۲۹ اسفند در فایل قابل‌آزمون نیست (حذفی ندارد)", pd.Series(True, index=df.index))
    # حضور در همه سال‌های ۱۳۹۰–۱۴۰۴ (پنل متوازن)؛ شرط اصلی نمونه
    need_years = set(range(Y0, Y1 + 1))
    cnt_years = df.loc[alive].groupby("firm_id")["year"].nunique()
    def longest_run(ys):
        ys = sorted(ys); best = cur = 1
        for p_, q_ in zip(ys[:-1], ys[1:]): cur = cur + 1 if q_ == p_ + 1 else 1; best = max(best, cur)
        return best
    run_len = df.loc[alive].groupby("firm_id")["year"].apply(lambda y: longest_run(set(y)))
    last_ok = df.loc[alive & (df["year"] == Y1)].groupby("firm_id").size()
    sens = pd.DataFrame([{"حداقل سال‌های حاضر (از %d)" % (Y1 - Y0 + 1): k, "شرکت (غیرمتوالی)": int((cnt_years >= k).sum()),
                          "ردیف (غیرمتوالی)": int(df.loc[alive & df["firm_id"].isin(cnt_years[cnt_years >= k].index)].shape[0]),
                          "شرکت (متوالی)": int((run_len >= k).sum()),
                          "شرکت (غیرمتوالی + حاضر در %d)" % Y1: int(((cnt_years >= k) & cnt_years.index.isin(last_ok.index)).sum())} for k in range(Y1 - Y0 + 1, 4, -1)])
    ok = set(cnt_years[cnt_years >= MIN_YEARS].index)
    nyears = Y1 - Y0 + 1
    step(f"۹) حضور در حداقل {MIN_YEARS} سال از {nyears} سال {Y0}–{Y1} (شرط اصلی نمونه)", f"شرکت باید پس از گام‌های قبل (بورس تهران، غیرمالی، صورت‌های کامل و حسابرسی‌شده) در حداقل {MIN_YEARS} سال ردیف داشته باشد (نه لزوماً متوالی)" + ("؛ پنل کاملاً متوازن" if MIN_YEARS >= nyears else ""), df["firm_id"].isin(ok))
    df["n_years_firm"] = df["firm_id"].map(cnt_years); df["longest_run_firm"] = df["firm_id"].map(run_len)
    n_all = alive.copy(); df["in_common_sample"] = n_all.astype(int)
    # نمونه‌های اختصاصی هر مقاله
    alive_c = alive.copy()
    a1_cols = ["LOAN", "NONOP", "SIZE", "LEV", "ROA", "CFO_TA", "CASH_TA", "TANG", "GROW", "MTB"]
    step("۱۰-الف) مقاله ۱: صورت جریان نقد و تسهیلات", f"LOAN قابل‌محاسبه؛ سال پایه {Y0} کنار گذاشته می‌شود (فقط برای تأخیر)", df["LOAN"].notna() & (df["year"] >= ANA0))
    step("۱۱-الف) مقاله ۱: NONOP و کنترل‌ها", "NONOP و ‌SIZE, LEV, ROA, CFO_TA, CASH_TA, TANG, GROW موجود (MTB اختیاری)", df[["NONOP", "SIZE", "LEV", "ROA", "CFO_TA", "CASH_TA", "TANG", "GROW"]].notna().all(axis=1))
    loans_any = df.loc[alive].groupby("firm_id")[["loan_in_f", "loan_repay_f"]].apply(lambda g: (g.abs().sum().sum() > 0))
    step("۱۲-الف) مقاله ۱: وام‌گیرنده", "شرکت حداقل در یک سال دریافت یا بازپرداخت تسهیلات داشته", df["firm_id"].map(loans_any).fillna(False).astype(bool))
    df["A1_sample"] = alive.astype(int)
    alive = alive_c.copy()
    a2_core = ["CR", "QR", "WC", "LEV", "ROA", "CFO_TD", "TNW", "ZSCORE", "CASH_TA"]
    step("۱۰-ب) مقاله ۲: معیارهای قرارداد", f"CR, QR, WC, LEV, ROA, CFO_TD, TNW, ZSCORE, CASH_TA موجود؛ سال پایه {Y0} کنار گذاشته می‌شود", df[a2_core].notna().all(axis=1) & (df["year"] >= ANA0))
    step("۱۱-ب) مقاله ۲: متغیر وابسته سال بعد", "F_DEF_141 موجود (سال t+1 وجود دارد؛ ۱۴۰۴ طبیعتاً حذف)", df["F_DEF_141"].notna())
    df["A2_sample"] = alive.astype(int)
    def strict(flag, need, years):
        ok_rows = df[need].notna().all(axis=1) & (df["in_common_sample"] == 1) & df["year"].isin(years)
        cnt = df[ok_rows].groupby("firm_id")["year"].nunique()
        firms = set(cnt[cnt == len(years)].index)
        return df["firm_id"].isin(firms) & (df["in_common_sample"] == 1)
    df["A1_balanced"] = strict("A1", ["LOAN", "NONOP", "SIZE", "LEV", "ROA", "CFO_TA", "CASH_TA", "TANG", "GROW"], range(ANA0, Y1 + 1)).astype(int)
    df["A2_balanced"] = strict("A2", a2_core + ["F_DEF_141"], range(ANA0, Y1)).astype(int)   # ۱۴۰۴ F_DEF ندارد → ۱۳۹۵–۱۴۰۳
    df["A2_balanced_1395_1403"] = 0
    ok2 = df[(df["in_common_sample"] == 1) & df[a2_core + ["F_DEF_141"]].notna().all(axis=1)].groupby("firm_id")["year"].apply(lambda y: set(range(ANA0, Y1)) <= set(y))
    df.loc[df["firm_id"].map(ok2).fillna(False).astype(bool) & (df["in_common_sample"] == 1), "A2_balanced_1395_1403"] = 1

    # وینزورایز (۱٪/۹۹٪) روی نمونه مشترک
    cont = ["LOAN", "NONOP", "DIV", "OPINV", "SIZE", "LEV", "ROA", "ROA_NI", "CFO_TA", "CASH_TA", "TANG", "GROW", "MTB", "Q", "ICR", "LEV_INT", "DIV_PAYOUT",
            "CR", "QR", "WC", "DEBT_EBIT", "DEBT_OPCASH", "DSCR", "CFO_TD", "TNW", "ZSCORE", "AQ", "F_ROA", "F_ZSCORE"]
    for c in cont:
        s = df[c].replace([np.inf, -np.inf], np.nan); m = df["in_common_sample"] == 1
        lo, hi = s[m].quantile([0.01, 0.99]); df[c + "_w"] = s.clip(lo, hi)

    nc = df.select_dtypes(include="number").columns
    df[nc] = df[nc].replace([np.inf, -np.inf], np.nan)
    master = df[df["in_common_sample"] == 1].copy()
    drop = [c for c in master.columns if c in ("mktcap_rial", "ta_l1", "ta_f1", "rev_l1", "NONOP_l1", "CFO_0", "CFO_l1", "CFO_f1", "dWC")]
    master = master.drop(columns=drop)

    # ---------------- اکسل کامل صورت‌های مالی شرکت‌های نمونه (همه ستون‌های رهاورد، به تفکیک صورت) ----------------
    orig = [str(c) for c in raw.columns]
    rawp = raw.copy(); rawp.columns = [f"c{i}" for i in range(len(orig))]
    flags = master[["firm_id", "year", "A1_sample", "A2_sample", "base_year"]].rename(columns={"firm_id": "c1", "year": "c2"})
    rawp["c1"] = pd.to_numeric(rawp["c1"], errors="coerce"); rawp["c2"] = pd.to_numeric(rawp["c2"], errors="coerce")
    sel = rawp.merge(flags, on=["c1", "c2"], how="inner").sort_values(["c1", "c2"])
    def clean(names):
        out, seen = [], set()
        for n_ in names:
            b = re.sub(r"\.\d+$", "", n_); b = b if b not in seen else n_
            seen.add(b); out.append(b)
        return out
    keycols = [0, 1, 2, 5, 8]; keynames = ["company", "firm_id", "year", "industry", "ticker"]
    def block(lo, hi):
        idx = list(range(lo, hi + 1)); d = sel[[f"c{i}" for i in keycols] + [f"c{i}" for i in idx]].copy()
        d.columns = keynames + clean([orig[i] for i in idx]); return d
    sheets = {"Balance_Sheet": block(7, 155), "Income_Statement": block(163, 287), "Cash_Flow": block(296, 363),
              "Financial_Ratios": block(370, 404), "Stock_Returns": block(406, 425)}
    ids = sel[["c0", "c1", "c2", "c5", "c7", "c8", "A1_sample", "A2_sample", "base_year"]].copy()
    ids.columns = ["company", "firm_id", "year", "industry", "market", "ticker", "A1_sample", "A2_sample", "base_year"]
    fs_path = str(a.out).replace("analysis_", "financial_statements_")
    with pd.ExcelWriter(fs_path, engine="openpyxl") as w:
        ids.to_excel(w, sheet_name="Firm_Years", index=False)
        for k, d in sheets.items(): d.to_excel(w, sheet_name=k, index=False)
    print("صورت‌های مالی کامل:", fs_path, {k: d.shape for k, d in sheets.items()})
    # ---------------- گزارش و فرهنگ‌نامه ----------------
    rep = pd.DataFrame(log)
    exc = pd.DataFrame(excl, columns=["شرکت", "firm_id", "year", "گام حذف"])
    dic = pd.DataFrame(DICT, columns=["متغیر", "مقاله", "تعریف", "فرمول/ستون‌های منبع", "توضیح"])
    na = pd.DataFrame(NA, columns=["متغیر", "مقاله", "دلیل", "منبع پیشنهادی"])
    desc = master[["LOAN", "NONOP", "DIV", "LEV", "ROA", "CFO_TA", "CR", "ZSCORE", "DEF_141", "F_DEF_141", "A1_sample", "A2_sample"]].describe().T.reset_index().rename(columns={"index": "متغیر"})
    with pd.ExcelWriter(a.out, engine="openpyxl") as w:
        rep.to_excel(w, sheet_name="Screening_Report", index=False)
        master.to_excel(w, sheet_name="Sample_Master", index=False)
        exc.to_excel(w, sheet_name="Excluded_Rows", index=False)
        dic.to_excel(w, sheet_name="Variable_Dictionary", index=False)
        na.to_excel(w, sheet_name="Not_Available", index=False)
        desc.to_excel(w, sheet_name="Descriptives", index=False)
        sens.to_excel(w, sheet_name="Years_Sensitivity", index=False)
    try: master.to_stata(str(a.out).replace(".xlsx", ".dta"), write_index=False, version=118)
    except Exception as e: print("dta ذخیره نشد:", e)
    pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 60)
    print(rep[["گام", "معیار غربالگری", "ردیف قبل", "حذف‌شده (ردیف)", "ردیف باقی‌مانده", "شرکت باقی‌مانده"]].to_string(index=False))
    print("مشترک:", len(master), "ردیف،", master.firm_id.nunique(), "شرکت ؛ A1:", int(master.A1_sample.sum()), "؛ A2:", int(master.A2_sample.sum()))
    print("متوازن سخت‌گیرانه: A1 =", master.loc[master.A1_balanced == 1, "firm_id"].nunique(), "شرکت ؛ A2 (۱۳۹۵–۱۴۰۳) =", master.loc[master.A2_balanced_1395_1403 == 1, "firm_id"].nunique(), "شرکت")
    return df, master, rep

DICT = [
 ("LOAN", "۱", "خالص تسهیلات دریافتی نسبت به دارایی‌های ابتدای دوره", "(دریافت نقدی تسهیلات − |پرداخت نقدی اصل تسهیلات|) ÷ دارایی t−1", "سلول خالی در صورت جریان نقد = صفر؛ اگر صورت جریان نقد نبود = گمشده. ستون‌های ۳۳۰ و ۳۳۱"),
 ("LARGE", "۱", "وام بزرگ", "۱ اگر LOAN ≥ ۰٫۰۵", "برای رویدادپژوهی"),
 ("NONOP_AMT", "۱", "دارایی‌های غیرعملیاتی (ریال)", "سرمایه‌گذاری کوتاه‌مدت + سرمایه‌گذاری بلندمدت + طلب از شرکت‌های گروه/وابسته", "املاک سرمایه‌گذاری و سپرده‌های بلندمدت جدا در منبع نیست"),
 ("NONOP", "۱", "تغییر دارایی غیرعملیاتی نسبت به دارایی t−1", "(NONOP_AMT_t − NONOP_AMT_{t−1}) ÷ دارایی t−1", "متغیر وابسته مدل ۱"),
 ("DIV", "۱", "شاخص انحراف مصرف تسهیلات", "سهم افزایش دارایی غیرعملیاتی از وام خالص؛ فقط وقتی LOAN ≥ ۰٫۰۲، محدود به [۰،۱]؛ در غیر این صورت ۰", "آستانه ۲٪ قابل تغییر"),
 ("OPINV", "۱", "سرمایه‌گذاری عملیاتی", "(Δدارایی ثابت خالص + Δموجودی مواد و کالا) ÷ دارایی t−1", "مقایسه با NONOP"),
 ("SIZE", "۱،۲", "اندازه", "ln(جمع دارایی‌ها)", ""),
 ("LEV", "۱،۲", "اهرم", "جمع بدهی‌ها ÷ جمع دارایی‌ها", ""),
 ("LEV_INT", "۱،۲", "اهرم بهره‌دار", "(تسهیلات کوتاه‌مدت + بلندمدت) ÷ دارایی", ""),
 ("ROA", "۱،۲", "بازده دارایی", "سود عملیاتی ÷ دارایی t−1", "ROA_NI با سود خالص"),
 ("CFO_TA", "۱", "جریان نقد عملیاتی", "جریان خالص نقد عملیاتی ÷ دارایی t−1", ""),
 ("CASH_TA", "۱،۲", "وجه نقد", "موجودی نقد ÷ دارایی", ""),
 ("TANG", "۱", "ملموس بودن دارایی", "خالص دارایی ثابت ÷ دارایی", ""),
 ("GROW", "۱", "رشد درآمد", "درآمد_t ÷ درآمد_{t−1} − ۱", "درآمد = «جمع درآمدها»"),
 ("MTB", "۱", "ارزش بازار به دفتری", "ارزش روز (ریال÷۱e6) ÷ حقوق صاحبان سهام", "فقط حقوق > ۰"),
 ("Q", "۱", "کیوتوبین تقریبی", "(ارزش بازار + بدهی) ÷ دارایی", ""),
 ("LOSS", "۱", "زیان", "۱ اگر سود خالص منفی", ""),
 ("ICR", "۱،۲", "پوشش بهره", "سود عملیاتی ÷ |هزینه مالی|", ""),
 ("AGE_PROXY", "۱", "سابقه در پنل", "ترتیب سال‌های حضور شرکت در پنل", "سن واقعی تأسیس در صورت‌های مالی نیست"),
 ("DIV_PAYOUT", "۱", "نسبت سود تقسیمی", "|سود نقدی پرداختی| ÷ سود خالص مثبت", ""),
 ("CR", "۲", "نسبت جاری", "دارایی جاری ÷ بدهی جاری", ""),
 ("QR", "۲", "نسبت آنی", "(دارایی جاری − موجودی مواد و کالا) ÷ بدهی جاری", ""),
 ("WC", "۲", "سرمایه در گردش", "(دارایی جاری − بدهی جاری) ÷ دارایی", ""),
 ("DEBT_EBIT", "۲", "بدهی بهره‌دار به سود عملیاتی", "(تسهیلات کوتاه+بلندمدت) ÷ سود عملیاتی مثبت", "جایگزین DEBT_EBITDA؛ ستون استهلاک در منبع تقریباً خالی است"),
 ("DEBT_OPCASH", "۲", "بدهی بهره‌دار به نقد حاصل از عملیات", "(تسهیلات) ÷ نقد حاصل از عملیات مثبت", ""),
 ("DSCR", "۲", "پوشش بازپرداخت بدهی", "CFO ÷ (|هزینه مالی| + تسهیلات کوتاه‌مدت)", "تقریبی (حصه جاری بلندمدت جدا نیست)"),
 ("CFO_TD", "۲", "جریان نقد به بدهی", "CFO ÷ جمع بدهی‌ها", ""),
 ("TNW", "۲", "خالص دارایی ملموس", "(حقوق صاحبان سهام − دارایی نامشهود) ÷ دارایی", ""),
 ("ZSCORE", "۲", "زد آلتمن بازارهای نوظهور (Z″)", "۶٫۵۶·WC + ۳٫۲۶·سودانباشته/دارایی + ۶٫۷۲·EBIT/دارایی + ۱٫۰۵·حقوق/بدهی", "Altman, Hartzell & Peck (1995)"),
 ("AQ", "۲", "کیفیت اقلام تعهدی", "انحراف معیار ۵ ساله باقیمانده رگرسیون مقطعی سالانه دچو-دیچف (ΔWC روی CFO_{t−1}, CFO_t, CFO_{t+1})", "حداقل ۳ سال؛ استفاده از CFO_{t+1} اطلاعات آینده است"),
 ("DEF_141", "۲", "ماده ۱۴۱ قانون تجارت", "۱ اگر زیان انباشته ≥ ۵۰٪ سرمایه", ""),
 ("DEF_Z", "۲", "آشفتگی بر پایه Z″", "۱ اگر ZSCORE < ۱٫۱", ""),
 ("F_DEF_141 / F_DEF_Z / F_DEF_ANY", "۲", "متغیر وابسته سال بعد", "مقدار t+1 (و یای منطقی دو تعریف)", "۱۴۰۴ ندارد"),
 ("F_DEF_ICR", "۲", "آشفتگی: پوشش بهره سال بعد < ۱", "ICR_{t+1} < ۱", "مستقل از Z″؛ پیشنهاد برای متغیر وابسته اصلی"),
 ("F_DEF_NEGEQ", "۲", "حقوق صاحبان سهام منفی سال بعد", "equity_{t+1} < ۰", "رویداد کم"),
 ("F_ROA, F_LOSS, F_ZSCORE", "۱،۲", "مقدار سال بعد", "t+1", ""),
 ("ret12, ret16, dps12, price_end12, liq12", "۱", "بازده سهام، سود نقدی، قیمت پایانی، رتبه نقدشوندگی", "از ستون‌های رهاورد (۱۲ و ۱۶ ماهه)", "۱۶ ماهه برای ۱۴۰۴ ندارد"),
 ("tse_only", "—", "بورس تهران = ۱ (فرابورس = ۰)", "از ستون «بازار»", "برای پژوهش فقط بورس تهران"),
 ("*_w", "—", "نسخه وینزورایز ۱٪/۹۹٪", "روی نمونه مشترک", ""),
]
NA = [
 ("AUDSIZE, AUDSPEC, AUDTEN, AUDSWITCH, AUDOPN", "۱،۲", "نام حسابرس/اظهارنظر در داده نیست", "گزارش حسابرس در کدال (auditor_extract.py)"),
 ("STATE, CONC, INST", "۱", "مالکیت در صورت‌های مالی نیست", "سهامداران TSETMC/کدال (rohi_extra.py)"),
 ("DEF_BANK (سررسیدگذشته/جرائم دیرکرد)", "۲", "یادداشت‌ها در فایل نیست", "یادداشت تسهیلات مالی کدال"),
 ("سن واقعی تأسیس (AGE)", "۱", "در فایل نیست", "کدال/TSETMC"),
 ("EBITDA / DEBT_EBITDA", "۲", "ستون استهلاک ۹۹٪ خالی", "یادداشت‌ها یا نقد حاصل از عملیات (DEBT_OPCASH جایگزین شد)"),
 ("پایان سال مالی ۲۹ اسفند", "۱،۲", "ستون تاریخ پایان دوره در فایل نیست", "کدال"),
]
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--panel", required=True); ap.add_argument("--out", default="analysis_1394_1404.xlsx"); ap.add_argument("--include-fara", action="store_true")
    ap.add_argument("--min-years", type=int, default=9)
    args = ap.parse_args(); INCLUDE_FARA = args.include_fara; MIN_YEARS = args.min_years
    main(args)
