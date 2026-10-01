*==============================================================================
* 04_inspect_raw.do  -  ONE-OFF inspection of the raw database export
*
* Run this file on its own (not from 00_run_all.do). It changes nothing in the
* data; it writes C:/Users/Rohi/Desktop/Data/raw_inspection.xlsx with:
*   dictionary         every column: Stata name, ORIGINAL header text,
*                      non-missing count before 1398 and from 1398, median
*   flag1 ... flag6    values of the statement-type columns (consolidated,
*                      audited, restated, type, market, category)
*   rows_per_firmyear  how many rows each Symbol-Year has
*   example_multirows  30 rows of firm-years that have more than one row
*   ids                Symbol versus company-name identifiers
* Send raw_inspection.xlsx back; the screening/mapping code is written from it.
*==============================================================================
version 17.0
clear all
set more off

global ROOT    "C:/Users/Rohi/Desktop/Data"
global RAWFILE "Raw_All_Data.xlsx"        // the raw export (.xlsx or .dta)
local  OUTX    "$ROOT/raw_inspection.xlsx"

if ustrregexm("$RAWFILE", "\.dta$") use "$ROOT/$RAWFILE", clear
else import excel "$ROOT/$RAWFILE", firstrow clear

cap confirm variable Year
if _rc {
    di as err "No column named Year. Rename the fiscal-year column to Year and re-run."
    exit 111
}
cap confirm string variable Year
if !_rc destring Year, replace force ignore(", ")
di as txt "Rows: " _N
tab Year

*------------------------------------------------------------------------------
* 1. Dictionary of all columns
*------------------------------------------------------------------------------
tempname P
postfile `P' int pos str128 name str244 header str12 type ///
    double(n_all n_before1398 n_from1398 median) using "$ROOT/_raw_dictionary.dta", replace
local i = 0
foreach v of varlist _all {
    local ++i
    local lab : variable label `v'
    local typ : type `v'
    tempvar z
    cap confirm numeric variable `v'
    if !_rc qui gen double `z' = `v'
    else    qui destring `v', gen(`z') force ignore(", ")
    qui count if !missing(`z')
    local na = r(N)
    qui count if !missing(`z') & Year < 1398
    local n1 = r(N)
    qui count if !missing(`z') & Year >= 1398
    local n2 = r(N)
    local md = .
    if `na' > 0 {
        qui su `z', d
        local md = r(p50)
    }
    post `P' (`i') ("`v'") (`"`lab'"') ("`typ'") (`na') (`n1') (`n2') (`md')
    drop `z'
}
postclose `P'
preserve
    use "$ROOT/_raw_dictionary.dta", clear
    export excel using "`OUTX'", sheet("dictionary", replace) firstrow(variables)
restore

*------------------------------------------------------------------------------
* 2. Statement-type columns: which values occur
*------------------------------------------------------------------------------
local k = 0
foreach f in تلفیقی حسابرسیشده تجدیدارائهشده نوع بازار طبقه {
    local ++k
    cap confirm variable `f'
    if _rc continue
    preserve
        contract `f', freq(rows)
        export excel using "`OUTX'", sheet("flag`k'", replace) firstrow(variables)
    restore
}

*------------------------------------------------------------------------------
* 3. Rows per firm-year and an example of firm-years with several rows
*------------------------------------------------------------------------------
bys Symbol Year: gen int _nrows = _N
preserve
    contract _nrows, freq(firmyears)
    export excel using "`OUTX'", sheet("rows_per_firmyear", replace) firstrow(variables)
restore
local show ""
foreach f in Symbol شرکت Year _nrows تلفیقی حسابرسیشده تجدیدارائهشده نوع تاریخمصوب ///
    بازار جمعکلداراییها جمعکلبدهیها فروشخالصدرآمدحاصلازخدمات {
    cap confirm variable `f'
    if !_rc local show "`show' `f'"
}
preserve
    keep if _nrows > 1
    if _N > 0 {
        sort Symbol Year
        keep in 1/`=min(30, _N)'
        keep `show'
        export excel using "`OUTX'", sheet("example_multirows", replace) firstrow(variables)
    }
restore

*------------------------------------------------------------------------------
* 4. Identifiers: does a company keep one Symbol over time?
*------------------------------------------------------------------------------
putexcel set "`OUTX'", sheet("ids", replace) modify
egen byte _t1 = tag(Symbol)
qui count if _t1
putexcel A1 = "Distinct Symbol" B1 = (r(N))
cap confirm variable شرکت
if !_rc {
    egen byte _t2 = tag(شرکت)
    qui count if _t2
    putexcel A2 = "Distinct company (شرکت)" B2 = (r(N))
    bys شرکت (Symbol): gen byte _ms = Symbol[1] != Symbol[_N]
    egen byte _t3 = tag(شرکت) if _ms
    qui count if _t3 == 1
    putexcel A3 = "Companies with more than one Symbol" B3 = (r(N))
}
erase "$ROOT/_raw_dictionary.dta"
di as res _n "Done: `OUTX'  - please send this file."
