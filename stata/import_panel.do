*==============================================================================
* وارد کردن پنل نهایی ۱۳۸۰–۱۴۰۴ (خروجی merge_years.py) در استتا و استانداردسازی نام متغیرهای اصلی
* ورودی : panel_1380_1404.xlsx   (۴۲۸ ستون اکسل اصلی + data_source, new_company, industry_missing)
* خروجی : panel_1380_1404.dta    (کلید: firm_id year ؛ xtset)
* نام‌گذاری بر پایه «موقعیت ستون» انجام می‌شود (چیدمان ثابت)، نه نام فارسی؛ عنوان فارسی در label هر متغیر می‌ماند.
* هشدار : این کد در استتا اجرا نشده (استتا در محیط من نبود)؛ اگر خطا داد، خطا را بفرستید.
*==============================================================================
clear all
set more off
global FILE "C:/rohi/panel_1380_1404.xlsx"     // مسیر فایل را تنظیم کنید
global OUTD "C:/rohi/panel_1380_1404.dta"

import excel using "$FILE", firstrow clear
ds
global VARS `r(varlist)'

capture program drop rn
program define rn
    * rn <شماره ستون صفرمبنا> <نام جدید>
    args idx newname
    local k = `idx' + 1
    local old : word `k' of $VARS
    capture rename `old' `newname'
    if _rc di as err "rename ناموفق: ستون `idx' (`old') ← `newname'"
end

* ---- کلیدها و شناسه ----
rn 0  company
rn 1  firm_id
rn 2  year
rn 3  ind_code
rn 4  ind_group_code
rn 5  industry
rn 6  category
rn 7  market
rn 8  ticker
rn 9  approval_date
rn 10 report_type          // مجمع / *12ماهه
rn 11 consolidated
rn 12 audited
rn 13 restated

* ---- ترازنامه ----
rn 14 cash
rn 15 st_inv
rn 21 trade_rec
rn 23 rel_party_rec
rn 45 inventory
rn 59 tca
rn 61 lt_inv
rn 75 intang
rn 79 ppe_gross
rn 82 ppe_net
rn 83 tnca
rn 84 ta
rn 86 trade_pay
rn 99 loan_st
rn 113 tcl
rn 118 loan_lt
rn 124 tl
rn 126 capital
rn 127 ret_earn
rn 144 equity

* ---- سود و زیان ----
rn 163 mktcap
rn 226 revenue
rn 227 cogs
rn 233 selling_exp
rn 237 admin_exp
rn 241 ebit
rn 244 deprec_exp
rn 246 fin_cost
rn 264 ebt
rn 265 tax
rn 267 net_income
rn 287 eps

* ---- جریان وجوه نقد ----
rn 298 cfo
rn 302 capex_ppe
rn 330 loan_inflow
rn 331 loan_repay
rn 332 loan_interest_paid
rn 353 dividends_paid

* ---- نسبت‌های رهاورد ----
rn 375 roa_r
rn 377 roe_r
rn 381 cr_r
rn 382 qr_r
rn 394 debt_ratio_r
rn 401 icr_r

* ---- بازده سهام: مجموعه اول = ۱۲ ماهه ؛ مجموعه دوم = ۱۶ ماهه (۱۴۰۴: فقط ۱۲ ماهه/سالانه) ----
rn 409 rights12
rn 410 bonus12
rn 411 dps12
rn 412 p_base12
rn 413 p_end12
rn 414 ret12
rn 415 liq_rank12
rn 419 rights16
rn 420 bonus16
rn 421 dps16
rn 422 p_base16
rn 423 p_end16
rn 424 ret16
rn 425 liq_rank16

* ---- ستون‌های پایانی ----
rn 428 data_source
rn 429 new_company
rn 430 industry_missing

* ---- ستون‌های کمکی بی‌مصرف اکسل اصلی ----
capture drop _merge4 _merge5
capture drop Unnamed*

* ---- کنترل و ساختار تابلویی ----
destring year firm_id, replace force
isid company year
isid firm_id year
xtset firm_id year
xtdescribe
tab year
tab data_source
summarize ta tl equity revenue net_income cfo if year >= 1402

compress
save "$OUTD", replace
di as txt "ذخیره شد: $OUTD"
