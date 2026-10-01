*==============================================================================
* 05b_compare_old.do  -  ONE-OFF check: where are the firm-years of the previous
*   data file (Final_Master_Data.xlsx, 1392-1403, 299 firms) in the new database?
* Run after 03_build_master.do and 05_screening.do. Changes nothing.
* Output: C:/Users/Rohi/Desktop/Data/Compare_old_new.xlsx
*   by_year   for each year: old firm-years; found in the new database; with
*             total assets; market in the new database; in the final sample
*   firms     every old firm: years in the old file, years with statements in
*             the new database, years in the final sample, market, missing years
*==============================================================================
version 17.0
clear all
set more off
global ROOT "C:/Users/Rohi/Desktop/Data"
global OUT  "$ROOT/output"
global OLD  "Final_Master_Data.xlsx"
local  XL   "$ROOT/Compare_old_new.xlsx"
cap erase "`XL'"

cap program drop normtk
program define normtk
    args src
    cap confirm string variable `src'
    if _rc tostring `src', replace
    gen _k = ustrregexra(`src', "[\x{200C}\x{200F}\s\-_]", "")
    replace _k = ustrregexra(_k, "\x{064A}", "\x{06CC}")
    replace _k = ustrregexra(_k, "\x{0643}", "\x{06A9}")
    replace _k = ustrlower(_k)
end

* previous data
import excel "$ROOT/$OLD", firstrow clear
keep Symbol Year
destring Year, replace force
normtk Symbol
keep _k Year
drop if _k == "" | missing(Year)
duplicates drop
gen byte in_old = 1
tempfile old
save `old'

* new database (before screening): keys from both Symbol and the ticker
use "$ROOT/Master_1380_1403.dta", clear
gen byte has_ta = !missing(جمعکلداراییها)
gen market_new  = بازار
rename شرکت code
tempfile base
save `base'
* key from the new Symbol column
normtk Symbol
keep _k Year code has_ta market_new
drop if _k == ""
bys _k Year (has_ta): keep if _n == _N
gen byte in_new = 1
tempfile N_S
save `N_S'
* key from the new ticker column
use `base', clear
normtk نماد
keep _k Year code has_ta market_new
drop if _k == ""
bys _k Year (has_ta): keep if _n == _N
gen byte in_new = 1
tempfile N_T
save `N_T'

* final sample (company codes)
use "$OUT/screened_data.dta", clear
keep FirmCode Year
rename FirmCode code
duplicates drop
gen byte in_final = 1
tempfile fin
save `fin'

* match the old file: first on the new Symbol column, then on the new ticker
use `old', clear
merge 1:1 _k Year using `N_S', keep(master match) gen(_mS)
qui count if _mS == 3
di as res "Old firm-years matched on the new Symbol column: " r(N)
preserve
    use `N_T', clear
    foreach v in code has_ta market_new in_new {
        rename `v' `v'_t
    }
    tempfile NT2
    save `NT2'
restore
merge 1:1 _k Year using `NT2', keep(master match) gen(_mT)
qui count if _mS != 3 & _mT == 3
di as res "Additional old firm-years matched on the new ticker (نماد): " r(N)
foreach v in code has_ta in_new {
    replace `v' = `v'_t if _mS != 3 & _mT == 3
}
replace market_new = market_new_t if _mS != 3 & _mT == 3
drop *_t _mS _mT
merge m:1 code Year using `fin', keep(master match) nogen
foreach v in in_new has_ta in_final {
    replace `v' = 0 if missing(`v')
}
gen byte fara = ustrregexm(market_new, "فرا")

preserve
    gen byte nomarket = in_new & market_new == ""
    collapse (sum) old_firmyears = in_old found_in_new = in_new with_statements = has_ta ///
        farabourse = fara no_market = nomarket in_final_sample = in_final, by(Year)
    di as res _n "PREVIOUS FILE vs NEW DATABASE, by year"
    list, noobs sep(0) abbrev(20)
    export excel using "`XL'", sheet("by_year") firstrow(variables) replace
restore

preserve
    sort _k Year
    gen str200 years_missing = ""
    by _k: replace years_missing = cond(_n > 1, years_missing[_n-1], "") + cond(!has_ta, string(Year) + " ", "")
    by _k: replace years_missing = years_missing[_N]
    by _k: egen int years_old              = total(in_old)
    by _k: egen int years_with_statements  = total(has_ta)
    by _k: egen int years_in_final         = total(in_final)
    by _k: egen int farabourse_years       = total(fara)
    gen str40 market = market_new
    by _k: replace market = market[_n-1] if market == "" & _n > 1
    by _k: keep if _n == _N
    keep _k years_old years_with_statements years_in_final farabourse_years market years_missing
    rename _k ticker
    sort years_in_final ticker
    export excel using "`XL'", sheet("firms") firstrow(variables) sheetmodify
    di as res _n "Old firms by number of years in the final sample:"
    tab years_in_final
restore
di as res _n "Done: `XL'"
