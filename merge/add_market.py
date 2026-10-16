"""افزودن متغیرهای بازار (تی‌اس‌ای‌سی) به پنل تحلیل: python add_market.py analysis_1394_1404"""
import sys, pandas as pd
base = sys.argv[1] if len(sys.argv) > 1 else "analysis_1394_1404"
mf = pd.read_csv("market_features_1394_1404.csv")
keep = ["firm_id", "fiscal_year"] + [c for c in mf if c.startswith("mk_")] + ["cap_change_n", "tse_sector", "tse_industry_index", "tse_shares", "tseinfo_cgrValCotTitle", "tseinfo_flowTitle", "tseinfo_cIsin"]
mf = mf[[c for c in keep if c in mf]].rename(columns={"fiscal_year": "year", "tse_sector": "tse_sector_name", "tse_shares": "tse_shares_now", "tseinfo_cgrValCotTitle": "tse_board_group", "tseinfo_flowTitle": "tse_market_flow", "tseinfo_cIsin": "isin"})
x = pd.ExcelFile(base + ".xlsx"); sheets = {s: x.parse(s) for s in x.sheet_names}
sm = sheets["Sample_Master"]; n0 = len(sm)
sm = sm.drop(columns=[c for c in mf if c not in ("firm_id", "year") and c in sm], errors="ignore").merge(mf, on=["firm_id", "year"], how="left")
assert len(sm) == n0
sheets["Sample_Master"] = sm
desc = {"mk_trade_days": "تعداد روز معاملاتی سال", "mk_price_close": "قیمت پایانی پایان سال", "mk_vol_sum": "حجم کل معاملات سال", "mk_val_sum": "ارزش کل معاملات سال", "mk_turnover": "گردش سهام (حجم/تعداد سهام)",
        "mk_volat_daily": "انحراف معیار بازده روزانه", "mk_volat_ann": "نوسان سالانه‌شده", "mk_amihud": "عدم نقدشوندگی آمیهود", "mk_zero_ret_share": "سهم روزهای بازده صفر",
        "mk_ret_m_mean": "میانگین بازده ماهانه", "mk_ret_m_sd": "انحراف معیار بازده ماهانه", "mk_r2": "R² مدل بازار-صنعت (هفتگی)", "mk_synch": "همزمانی قیمت = ln(R²/(1−R²))",
        "mk_ncskew": "چولگی منفی بازده خاص شرکت", "mk_duvol": "DUVOL", "mk_crash": "ریسک سقوط (۱ اگر بازده هفتگی ≤ میانگین−۳٫۲۹ انحراف)", "mk_jump": "ریسک پرش", "mk_beta": "بتای بازار",
        "cap_change_n": "تعداد تغییر تعداد سهام (افزایش سرمایه) در سال"}
vd = sheets["Variable_Dictionary"]
add = pd.DataFrame([[k, "هر دو", v, "تی‌اس‌ای‌سی: قیمت روزانه تعدیل‌شده", "پنجرهٔ سال مالی"] for k, v in desc.items() if k in sm], columns=vd.columns[:5])
sheets["Variable_Dictionary"] = pd.concat([vd[~vd.iloc[:, 0].isin(add.iloc[:, 0])], add], ignore_index=True)
with pd.ExcelWriter(base + ".xlsx") as w:
    for s, d in sheets.items(): d.to_excel(w, sheet_name=s, index=False)
d = sm.copy(); d.columns = [str(c)[:32] for c in d.columns]
for c in d.columns:
    if d[c].dtype == object: d[c] = d[c].astype(str).replace("nan", "")
d = d.replace([float("inf"), float("-inf")], float("nan"))
d.to_stata(base + ".dta", write_index=False, version=118)
print(base, sm.shape, "ردیف با بازار:", int(sm["mk_trade_days"].gt(0).sum()))
