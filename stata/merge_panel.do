*==============================================================================
* ادغام صورت‌های مالی ۱۳۸۰–۱۴۰۴ (رهاورد نوین) در استتا
* ورودی : اکسل اصلی ۱۳۸۰–۱۴۰۲ + فایل‌های ۱۴۰۳ و ۱۴۰۴ (پس از تبدیل با xml_to_xlsx.py به xlsx)
* خروجی : panel_1380_1404.dta  و  panel_1380_1404.xlsx   (کلید: symbol year)
* هشدار : این کد در استتا آزمون نشده؛ نام ستون‌ها از mapping.csv می‌آید (جدول تطبیق).
*==============================================================================
clear all
set more off

*--------------------------- ۰) تنظیمات (فقط این بخش را ویرایش کنید) ---------------
global ROOT   "C:/rohi"                       // پوشه پروژه
global IN     "$ROOT/data_in"
global OUT    "$ROOT/data_out"
global MAIN   "$IN/main_1380_1402.xlsx"       // اکسل اصلی
global MAINSHEET ""                           // نام شیت (خالی = اولین شیت)
global MAP    "$ROOT/mapping.csv"             // ستون‌ها: old,new  (old = عنوان ستون در فایل، new = نام استاندارد)
global SYM    "symbol"                        // نام استاندارد ستون نماد
global YEAR   "year"                          // نام استاندارد ستون سال
global SCALE_NEW 1                            // اگر واحد ۱۴۰۳/۱۴۰۴ با اکسل اصلی فرق دارد (مثلاً 1000)، ضریب تبدیل
* فایل‌های هر سال: برای هر نوع صورت یک فایل xlsx (خروجی xml_to_xlsx.py)
local types1403 "ترازنامه" "سود و زیان" "جریان وجوه نقد" "نسبت‌های مالی" "بازده 12 ماهه"
local types1404 "ترازنامه" "سود و زیان" "جریان وجوه نقد" "نسبت های مالی" "بازده سالانه سهام"

*--------------------------- ۱) برنامه: خواندن، استانداردسازی نام ستون‌ها --------------
capture program drop apply_map
program define apply_map
    * جدول تطبیق را می‌خواند و نام ستون‌های داده فعلی را براساس label اصلی (عنوان ستون) عوض می‌کند
    preserve
        import delimited using "$MAP", varnames(1) encoding(utf8) stringcols(_all) clear
        local n = _N
        forvalues i = 1/`n' {
            local o`i' = strtrim(old[`i'])
            local w`i' = strtrim(new[`i'])
        }
    restore
    foreach v of varlist _all {
        local lab : variable label `v'
        if `"`lab'"' == "" local lab "`v'"
        forvalues i = 1/`n' {
            if `"`lab'"' == `"`o`i''"' | "`v'" == `"`o`i''"' {
                capture rename `v' `w`i''
                continue, break
            }
        }
    }
end

capture program drop to_numeric
program define to_numeric
    * همه ستون‌های رشته‌ای که عدد هستند را به عدد تبدیل می‌کند (ویرگول، پرانتز منفی)
    foreach v of varlist _all {
        capture confirm string variable `v'
        if _rc == 0 & "`v'" != "$SYM" {
            quietly replace `v' = subinstr(`v', ",", "", .)
            quietly replace `v' = "-" + subinstr(subinstr(`v', "(", "", .), ")", "", .) if substr(`v',1,1)=="("
            capture destring `v', replace force
        }
    }
end

*--------------------------- ۲) فایل اصلی ۱۳۸۰–۱۴۰۲ -----------------------------------
if "$MAINSHEET" == "" import excel using "$MAIN", firstrow clear
else import excel using "$MAIN", sheet("$MAINSHEET") firstrow clear
apply_map
to_numeric
confirm variable $SYM $YEAR
destring $YEAR, replace force
keep if inrange($YEAR, 1380, 1402)
gen byte src_main = 1
tempfile main
save `main'
di as txt "فایل اصلی: " _N " ردیف"

*--------------------------- ۳) سال‌های ۱۴۰۳ و ۱۴۰۴: ادغام انواع صورت‌ها روی نماد -------------
foreach y in 1403 1404 {
    local first = 1
    foreach t of local types`y' {
        local f "$IN/`y'/`t'.xlsx"
        capture confirm file "`f'"
        if _rc {
            di as err "یافت نشد: `f'"
            continue
        }
        import excel using "`f'", firstrow clear      // اگر چند شیت دارد: sheet("t1")
        apply_map
        to_numeric
        capture confirm variable $SYM
        if _rc {
            di as err "ستون نماد ($SYM) در `f' نیست؛ mapping را کامل کنید"
            continue
        }
        capture drop $YEAR
        bysort $SYM: keep if _n == 1                  // اگر نماد تکراری بود (خطا ؟) فقط اولی
        tempfile part_`y'_`first'
        save `part_`y'_`first''
        if `first' == 1 {
            tempfile acc`y'
            save `acc`y''
        }
        else {
            use `acc`y'', clear
            merge 1:1 $SYM using `part_`y'_`first'', nogenerate update   // update: مقادیر خالی را از فایل بعدی پر می‌کند
            save `acc`y'', replace
        }
        local first = 0
    }
    use `acc`y'', clear
    gen $YEAR = `y'
    gen byte src_main = 0
    * تبدیل واحد (در صورت لزوم) برای ستون‌های ریالی؛ لیست ستون‌ها را اینجا بنویسید:
    * foreach v in TA TL EQUITY SALES EBIT NI CFO { capture replace `v' = `v' * $SCALE_NEW }
    tempfile s`y'
    save `s`y''
    di as txt "سال `y': " _N " شرکت"
}

*--------------------------- ۴) چسباندن سال‌ها و کنترل کیفیت -------------------------------
use `main', clear
append using `s1403'
append using `s1404'

* نماد را رشته و تمیز کن (حذف فاصله‌های اضافه، یکسان‌سازی «ی/ي» و «ک/ك»)
capture confirm string variable $SYM
if _rc tostring $SYM, replace
replace $SYM = ustrregexra($SYM, "ي", "ی")
replace $SYM = ustrregexra($SYM, "ك", "ک")
replace $SYM = strtrim(itrim($SYM))

* تکراری‌ها
duplicates report $SYM $YEAR
duplicates drop $SYM $YEAR, force      // اگر می‌خواهید دستی بررسی کنید این خط را غیرفعال کنید
isid $SYM $YEAR

* شناسه عددی شرکت و ساختار تابلویی
egen firm_id = group($SYM)
xtset firm_id $YEAR
xtdescribe

* شرکت‌ها/سال‌های ناقص
bysort firm_id: gen n_years = _N
tab $YEAR
summarize n_years, detail

* بررسی پیوستگی بین ۱۴۰۲ و ۱۴۰۳ و ۱۴۰۴ (جهش‌های غیرعادی؛ نام TA را با ستون خودتان عوض کنید)
capture confirm variable TA
if _rc == 0 {
    gen lnTA = ln(TA) if TA > 0
    gen d_lnTA = D.lnTA
    list $SYM $YEAR TA d_lnTA if abs(d_lnTA) > 2 & !missing(d_lnTA), sepby($SYM) abbrev(14)
}

* درصد مقادیر گمشده هر متغیر به تفکیک سال (برای کشف ستون‌هایی که در سال جدید تطبیق نخورده‌اند)
quietly ds, has(type numeric)
foreach v of varlist `r(varlist)' {
    quietly count if missing(`v') & $YEAR >= 1403
    local m1 = r(N)
    quietly count if $YEAR >= 1403
    local t1 = r(N)
    quietly count if missing(`v') & $YEAR < 1403
    local m0 = r(N)
    quietly count if $YEAR < 1403
    local t0 = r(N)
    if `t1' > 0 & `t0' > 0 {
        local p1 = 100*`m1'/`t1'
        local p0 = 100*`m0'/`t0'
        if abs(`p1' - `p0') > 30 di as err "هشدار: `v' گمشده ≤1402: " %4.1f `p0' "٪ ؛ ≥1403: " %4.1f `p1' "٪ (احتمال عدم تطبیق نام ستون)"
    }
}

*--------------------------- ۵) ذخیره -----------------------------------------------------
compress
save "$OUT/panel_1380_1404.dta", replace
export excel using "$OUT/panel_1380_1404.xlsx", firstrow(variables) replace
di as txt "پایان: " _N " ردیف"
