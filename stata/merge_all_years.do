*==============================================================================
* ادغام اصلی: اکسل ۱۳۸۰–۱۴۰۲  +  فایل‌های ۱۴۰۳ (File1..File6)  +  فایل‌های ۱۴۰۴ (File1..File5)
* خروجی: panel_1380_1404.dta — همان چیدمان ۴۲۸ ستونی اکسل اصلی (هیچ شرکتی حذف نمی‌شود)
*
* پیش‌نیاز: فایل‌های ۱۴۰۴ (XML اکسل) را با  python merge/ssml_to_xlsx.py --year 1404 --in raw/1404 --out xlsx1404
*           به xlsx با نام‌های File1_1404.xlsx … File5_1404.xlsx تبدیل کنید (قالب یکسان با فایل‌های ۱۴۰۳).
* قالب هر فایل: ستون ۱ = Symbol (نام شرکت)، ستون ۲ = Year؛ بقیه ستون‌ها دقیقاً به ترتیب اکسل اصلی.
*   File1 ترازنامه | File2 سود و زیان | File3 جریان نقد | File4 نسبت‌ها | File5 بازده ۱۲ماهه/سالانه | File6 بازده ۱۶ماهه
* روش: نام‌گذاری ستون‌ها براساس «موقعیت» در اکسل اصلی (نه نام فارسی) تا با نام‌های تکراری/فارسی مشکلی نباشد.
* هشدار: این کد در استتا اجرا نشده (استتا در محیط من نبود). اگر خطا داد، پیام خطا را بفرستید.
*==============================================================================
clear all
set more off

*------------------------------ ۰) تنظیمات --------------------------------------
global ROOT   "C:/rohi"
global MAIN   "$ROOT/Main_1380_1402.xlsx"
global DIR1403 "$ROOT/xlsx1403"        // File1_1403.xlsx ... File6_1403.xlsx
global DIR1404 "$ROOT/xlsx1404"        // File1_1404.xlsx ... File5_1404.xlsx
global OUT    "$ROOT/out"
* نقطه شروع هر بلوک در ستون‌های اکسل اصلی (صفرمبنا) و تعداد ستون‌های غیرکلید
*   بلوک:      1=ترازنامه  2=سود و زیان  3=جریان نقد  4=نسبت‌ها  5=بازده۱  6=بازده۲
global OFF1 7
global OFF2 156
global OFF3 289
global OFF4 365
global OFF5 406
global OFF6 416

*------------------------------ ۱) برنامه‌های کمکی -------------------------------
capture program drop normname
program define normname
    * یکسان‌سازی نام شرکت: ی/ي، ک/ك، نیم‌فاصله، فاصله‌های اضافه
    args v
    quietly replace `v' = ustrregexra(`v', "ي", "ی")
    quietly replace `v' = ustrregexra(`v', "ك", "ک")
    quietly replace `v' = ustrregexra(`v', "\x{200C}", " ")
    quietly replace `v' = strtrim(stritrim(`v'))
end

*------------------------------ ۲) فایل اصلی ۱۳۸۰–۱۴۰۲ ---------------------------
import excel using "$MAIN", firstrow clear
ds
global MV `r(varlist)'                       // نام ۴۲۸ ستون به ترتیب
local nmv : word count $MV
di as txt "ستون‌های اکسل اصلی: `nmv'"
local symv : word 1 of $MV                    // Symbol
local idv  : word 2 of $MV                    // شناسه شرکت
local yrv  : word 3 of $MV                    // Year
local cod1 : word 4 of $MV                    // کد صنعت جزئی
local cod2 : word 5 of $MV                    // کدصنعت کلی
local indv : word 6 of $MV                    // صنعت
local clsv : word 7 of $MV                    // طبقه
global SYMV `symv'
global IDV  `idv'
global YRV  `yrv'
global COD1 `cod1'
global COD2 `cod2'
global INDV `indv'
global CLSV `clsv'

* ستون‌های عددی اکسل اصلی (برای هم‌نوع‌سازی ستون‌های سال‌های جدید)
global NUMLIST ""
foreach v of global MV {
    capture confirm numeric variable `v'
    if _rc == 0 global NUMLIST "$NUMLIST `v'"
}

gen str200 company_key = `symv'
normname company_key
tempfile mainfile idmap codemap
save `mainfile'

* جدول شناسه شرکت‌ها
preserve
    keep company_key `idv'
    duplicates drop company_key, force
    rename `idv' idm
    save `idmap'
restore
* جدول کدهای صنعت (از نام صنعت)
preserve
    keep `indv' `cod1' `cod2' `clsv'
    drop if missing(`indv')
    duplicates drop `indv', force
    rename (`cod1' `cod2' `clsv') (cod1_new cod2_new cls_new)
    save `codemap'
restore
quietly summarize `idv'
global MAXID = r(max)

*------------------------------ ۳) ساخت یک سال جدید -------------------------------
capture program drop build_year
program define build_year
    args y dir
    local have ""
    forvalues b = 1/6 {
        capture confirm file "`dir'/File`b'_`y'.xlsx"
        if _rc {
            di as txt "  (فایل File`b'_`y' نیست؛ بلوک خالی می‌ماند)"
            continue
        }
        import excel using "`dir'/File`b'_`y'.xlsx", firstrow clear
        capture drop Year
        rename Symbol company_key
        normname company_key
        duplicates drop company_key, force
        * گام الف: همه ستون‌های غیرکلید → نام موقت
        ds company_key, not
        local vl `r(varlist)'
        local k = 0
        foreach v of local vl {
            local ++k
            rename `v' tmp_`b'_`k'
        }
        * گام ب: نام موقت → نام ستون متناظر در اکسل اصلی (براساس موقعیت)
        local off = ${OFF`b'}
        forvalues j = 1/`k' {
            local tgt : word `=`off' + `j'' of $MV
            rename tmp_`b'_`j' `tgt'
        }
        tempfile blk`b'
        save `blk`b''
        local have "`have' `b'"
    }
    * اجتماع شرکت‌ها از همه بلوک‌ها
    local first : word 1 of `have'
    use `blk`first'', clear
    foreach b of local have {
        if `b' != `first' merge 1:1 company_key using `blk`b'', nogenerate
    }
    * کلیدها
    gen `=word("$MV", 1)' = company_key
    gen `=word("$MV", 3)' = `y'
    merge m:1 company_key using `idmap', keep(master match) nogenerate
    quietly replace idm = . if idm == 0
    egen long grp = group(company_key) if missing(idm)
    replace idm = $MAXID + grp if missing(idm)
    gen `=word("$MV", 2)' = idm
    drop idm grp
    * صنعت و طبقه از جدول بازده (بلوک ۵): ستون‌های ۴۰۷ و ۴۰۸ (۱-مبنا) = صنعت و طبقه
    local ind_src : word 407 of $MV
    local cls_src : word 408 of $MV
    capture gen `=word("$MV", 6)' = `ind_src'
    capture gen `=word("$MV", 7)' = `cls_src'
    capture confirm variable `=word("$MV", 6)'
    if _rc == 0 {
        merge m:1 `=word("$MV", 6)' using `codemap', keep(master match) nogenerate
        replace `=word("$MV", 4)' = cod1_new
        replace `=word("$MV", 5)' = cod2_new
        capture drop cod1_new cod2_new cls_new
    }
    * هم‌نوع‌سازی با اکسل اصلی (ستون‌های عددی)
    foreach v of global NUMLIST {
        capture confirm string variable `v'
        if _rc == 0 {
            quietly replace `v' = subinstr(`v', ",", "", .)
            capture destring `v', replace force
        }
    }
    gen str12 data_source = "new_`y'"
end

*------------------------------ ۴) ساخت ۱۴۰۳ و ۱۴۰۴ ------------------------------------
build_year 1403 "$DIR1403"
tempfile y1403
save `y1403'
build_year 1404 "$DIR1404"
tempfile y1404
save `y1404'

*------------------------------ ۵) چسباندن و ذخیره --------------------------------------
use `mainfile', clear
gen str12 data_source = "main"
append using `y1403'
append using `y1404'
drop company_key

* کنترل کلید
duplicates report $SYMV $YRV
duplicates report $IDV $YRV
isid $IDV $YRV
tab $YRV data_source if $YRV >= 1402
xtset $IDV $YRV
compress
save "$OUT/panel_1380_1404.dta", replace
export excel using "$OUT/panel_1380_1404.xlsx", firstrow(variables) replace
di as txt "پایان: " _N " ردیف"
