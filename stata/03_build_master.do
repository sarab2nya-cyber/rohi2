*==============================================================================
* 03_build_master.do  -  ONE comprehensive database, 1380-1403, BEFORE screening
*
* Put these files in  C:/Users/Rohi/Desktop/Data/Raw/   (.dta preferred,
* .xlsx is used when the .dta is not there):
*     Main_1380_1402.dta
*     File1_1403.dta  File2_1403.dta  ...  File6_1403.dta
* Run this file on its own (Do-file Editor > Execute, nothing selected).
*
* What it does
*   1  reads the main file (1380-1402) and the six 1403 files
*   2  1403 files: merged on company code and year. Files with the same columns
*      for different firms are stacked; files with different columns for the
*      same firms are joined side by side. The first non-missing value is kept
*      when two files report the same item (conflicts are counted)
*   3  adds 1403 to 1380-1402; firms without a company code in 1403 get it
*      from their ticker in the main file
*   4  one row per company-year; columns that are empty in every row are dropped
*   5  sorted by company and year, identifiers first
* Output (in C:/Users/Rohi/Desktop/Data)
*   Master_1380_1403.dta    research database (Persian column names)
*   Master_1380_1403.xlsx   sheet Persian    : all columns, Persian headers
*                           sheet English    : the same data, English headers
*                           sheet Dictionary : Persian name, English name,
*                                              non-missing rows, years covered
*                           sheet Merge_report: what happened in each step
*==============================================================================
version 17.0
clear all
set more off
cap set maxvar 10000

global ROOT    "C:/Users/Rohi/Desktop/Data"
global RAW     "$ROOT/Raw"
global CODE    "$ROOT/stata"
global MAIN    "Main_1380_1402"
global F1403   "File1_1403 File2_1403 File3_1403 File4_1403 File5_1403 File6_1403"
global FIRMKEY "شرکت"          // company code
global TICKER  "نماد"          // ticker
* text columns (kept as text); every other column is made numeric
global TEXTVARS "Symbol صنعت طبقه بازار نماد تاریخمصوب نوع تلفیقی حسابرسیشده تجدیدارائهشده"

*------------------------------------------------------------------------------
* helpers
*------------------------------------------------------------------------------
cap program drop loadraw
program define loadraw
    args base
    cap confirm file "$RAW/`base'.dta"
    if !_rc {
        use "$RAW/`base'.dta", clear
        di as txt "Loaded $RAW/`base'.dta  (" _N " rows, " c(k) " columns)"
        exit
    }
    cap confirm file "$RAW/`base'.xlsx"
    if !_rc {
        import excel "$RAW/`base'.xlsx", firstrow clear
        di as txt "Loaded $RAW/`base'.xlsx  (" _N " rows, " c(k) " columns)"
        exit
    }
    di as err "Not found: $RAW/`base'.dta or $RAW/`base'.xlsx"
    exit 601
end

* prepfile: Year, company code, numeric/text types, empty columns, duplicates
cap program drop prepfile
program define prepfile
    args ydef fname
    cap drop _merge*
    cap confirm variable Year
    if _rc gen int Year = `ydef'
    cap confirm string variable Year
    if !_rc destring Year, replace force ignore(", ")
    if "`ydef'" != "." replace Year = `ydef' if missing(Year)
    cap confirm variable $FIRMKEY
    if _rc gen double $FIRMKEY = .
    cap confirm string variable $FIRMKEY
    if !_rc destring $FIRMKEY, replace force ignore(", ")
    cap confirm variable $TICKER
    if _rc gen str1 $TICKER = ""
    local T "$TEXTVARS"
    foreach v of varlist _all {
        local istext : list v in T
        cap confirm string variable `v'
        local isstr = (_rc == 0)
        if `istext' & !`isstr' {
            qui tostring `v', replace
            qui replace `v' = "" if `v' == "."
        }
        else if !`istext' & `isstr' & !inlist("`v'", "$FIRMKEY", "Year") {
            * numbers stored as text: convert only if every value is numeric
            cap destring `v', replace ignore(", ")
        }
        cap confirm string variable `v'
        if !_rc {
            qui replace `v' = ustrtrim(`v')
            qui count if `v' != ""
        }
        else qui count if !missing(`v')
        if r(N) == 0 & !inlist("`v'", "$FIRMKEY", "Year", "$TICKER") drop `v'
    }
    * ticker spelling: Arabic yeh/kaf -> Persian, no spaces or half-spaces
    qui replace $TICKER = ustrregexra($TICKER, "[\x{200C}\s]", "")
    qui replace $TICKER = ustrregexra($TICKER, "\x{064A}", "\x{06CC}")
    qui replace $TICKER = ustrregexra($TICKER, "\x{0643}", "\x{06A9}")
    qui drop if missing($FIRMKEY) & $TICKER == ""
    * one row per company-year: keep the row with most information
    tempvar nm dup
    qui egen int `nm' = rownonmiss(_all), strok
    qui duplicates tag $FIRMKEY $TICKER Year, gen(`dup')
    qui count if `dup'
    local nd = r(N)
    qui bys $FIRMKEY $TICKER Year (`nm'): keep if _n == _N
    post mrep ("`fname'") ("rows after cleaning") (_N) (`nd')
    drop `nm' `dup'
end

* harmonise: make column types of the file in memory match the master file
cap program drop harmon
program define harmon
    args mstr mnum
    foreach v of varlist _all {
        cap confirm string variable `v'
        local isstr = (_rc == 0)
        local inS : list v in mstr
        local inN : list v in mnum
        if `isstr' & `inN' qui destring `v', replace force ignore(", ")
        if !`isstr' & `inS' {
            qui tostring `v', replace
            qui replace `v' = "" if `v' == "."
        }
    }
end

cap postclose mrep
postfile mrep str40 file str60 step double(rows extra) using "$ROOT/_merge_report.dta", replace

*------------------------------------------------------------------------------
* 1. Main file 1380-1402
*------------------------------------------------------------------------------
loadraw $MAIN
local nraw = _N
post mrep ("$MAIN") ("rows read") (`nraw') (.)
prepfile . "$MAIN"
* ticker -> company code lookup (for 1403 rows without a company code)
preserve
    keep $TICKER $FIRMKEY
    drop if $TICKER == "" | missing($FIRMKEY)
    bys $TICKER ($FIRMKEY): keep if _n == _N
    rename $FIRMKEY _code_main
    tempfile tick
    save `tick'
restore
tempfile main
save `main'

*------------------------------------------------------------------------------
* 2. The six 1403 files
*------------------------------------------------------------------------------
local k = 0
foreach f of global F1403 {
    local ++k
    loadraw `f'
    post mrep ("`f'") ("rows read") (_N) (.)
    prepfile 1403 "`f'"
    qui count if Year != 1403
    if r(N) di as err "Note: `f' has " r(N) " rows with a year other than 1403 (kept as they are)."
    * company code from ticker where missing
    merge m:1 $TICKER using `tick', keep(master match) nogen
    qui count if missing($FIRMKEY) & !missing(_code_main)
    post mrep ("`f'") ("company code taken from ticker") (r(N)) (.)
    replace $FIRMKEY = _code_main if missing($FIRMKEY)
    drop _code_main
    qui count if missing($FIRMKEY)
    if r(N) {
        di as err "Note: " r(N) " rows of `f' have no company code (ticker not in the main file); kept with their ticker."
        post mrep ("`f'") ("rows without company code") (r(N)) (.)
    }
    tempfile p`k'
    save `p`k''
}

* combine the 1403 files
use `p1', clear
forvalues j = 2/`k' {
    qui ds, has(type string)
    local mstr `r(varlist)'
    qui ds, has(type numeric)
    local mnum `r(varlist)'
    preserve
        use `p`j'', clear
        harmon "`mstr'" "`mnum'"
        save `p`j'', replace
    restore
    merge 1:1 $FIRMKEY $TICKER Year using `p`j'', update
    qui count if _merge == 2
    local add = r(N)
    qui count if inlist(_merge, 3, 4)
    local mat = r(N)
    qui count if _merge == 5
    local con = r(N)
    local fj : word `j' of $F1403
    post mrep ("`fj'") ("1403: rows added (other firms)") (`add') (.)
    post mrep ("`fj'") ("1403: rows joined (same firms, more columns)") (`mat') (.)
    post mrep ("`fj'") ("1403: rows with conflicting values (first kept)") (`con') (.)
    drop _merge
}
tempfile y1403
save `y1403'

*------------------------------------------------------------------------------
* 3. 1380-1402 + 1403
*------------------------------------------------------------------------------
use `main', clear
qui count if Year == 1403
if r(N) di as err "Note: the main file already has " r(N) " rows for 1403; the 1403 files fill their gaps."
qui ds, has(type string)
local mstr `r(varlist)'
qui ds, has(type numeric)
local mnum `r(varlist)'
preserve
    use `y1403', clear
    harmon "`mstr'" "`mnum'"
    save `y1403', replace
restore
merge 1:1 $FIRMKEY $TICKER Year using `y1403', update
qui count if _merge == 2
post mrep ("All") ("1403 rows added") (r(N)) (.)
qui count if _merge == 5
post mrep ("All") ("rows with conflicting values (main file kept)") (r(N)) (.)
drop _merge

* one row per company-year (a firm whose ticker differs between files)
tempvar nm dd
qui egen int `nm' = rownonmiss(_all), strok
qui duplicates tag $FIRMKEY Year if !missing($FIRMKEY), gen(`dd')
qui count if `dd' > 0 & !missing(`dd')
post mrep ("All") ("company-years reported twice (row with most data kept)") (r(N)) (.)
qui bys $FIRMKEY Year (`nm'): drop if _n < _N & !missing($FIRMKEY)
drop `nm' `dd'

* identifiers that are fixed within a firm: fill gaps from the firm's other years
foreach v in Symbol صنعت طبقه بازار {
    cap confirm string variable `v'
    if _rc continue
    bys $FIRMKEY (Year): replace `v' = `v'[_n-1] if `v' == "" & _n > 1 & !missing($FIRMKEY)
    gen int _negY = -Year
    bys $FIRMKEY (_negY): replace `v' = `v'[_n-1] if `v' == "" & _n > 1 & !missing($FIRMKEY)
    drop _negY
}
foreach v in کدصنعتجزئی کدصنعتکلی {
    cap confirm numeric variable `v'
    if _rc continue
    bys $FIRMKEY (Year): replace `v' = `v'[_n-1] if missing(`v') & _n > 1 & !missing($FIRMKEY)
    gen int _negY = -Year
    bys $FIRMKEY (_negY): replace `v' = `v'[_n-1] if missing(`v') & _n > 1 & !missing($FIRMKEY)
    drop _negY
}

*------------------------------------------------------------------------------
* 4-5. Final cleaning and order
*------------------------------------------------------------------------------
keep if inrange(Year, 1380, 1403)
foreach v of varlist _all {
    cap confirm string variable `v'
    if !_rc qui count if `v' != ""
    else    qui count if !missing(`v')
    if r(N) == 0 drop `v'
}
local ids ""
foreach v in $FIRMKEY $TICKER Symbol Year کدصنعتکلی کدصنعتجزئی صنعت طبقه بازار تاریخمصوب نوع تلفیقی حسابرسیشده تجدیدارائهشده {
    cap confirm variable `v'
    if !_rc local ids "`ids' `v'"
}
order `ids'
sort $FIRMKEY $TICKER Year
compress
egen byte _tf = tag($FIRMKEY $TICKER)
qui count if _tf
post mrep ("Master") ("companies") (r(N)) (.)
post mrep ("Master") ("company-years, 1380-1403") (_N) (.)
drop _tf
di as res _n "Company-years per year:"
tab Year
save "$ROOT/Master_1380_1403.dta", replace

*------------------------------------------------------------------------------
* 6. Excel: Persian sheet, English sheet, dictionary, merge report
*------------------------------------------------------------------------------
cap erase "$ROOT/Master_1380_1403.xlsx"
export excel using "$ROOT/Master_1380_1403.xlsx", sheet("Persian") firstrow(variables) replace

* English headers: clear labels, apply the English dictionary, unnamed columns
foreach v of varlist _all {
    label variable `v' ""
}
do "$CODE/03_labels_en.do"
foreach v of varlist _all {
    local l : variable label `v'
    if "`l'" == "" {
        if ustrregexm("`v'", "^[A-Z]{1,3}$") label variable `v' "Unnamed source column `v'"
        else label variable `v' "`v'"
    }
}
export excel using "$ROOT/Master_1380_1403.xlsx", sheet("English") firstrow(varlabels) sheetmodify

* dictionary
tempname D
postfile `D' int position str128 persian_name str244 english_name double(nonmissing first_year last_year) ///
    using "$ROOT/_dictionary.dta", replace
local i = 0
foreach v of varlist _all {
    local ++i
    local l : variable label `v'
    cap confirm string variable `v'
    if !_rc qui su Year if `v' != "", meanonly
    else    qui su Year if !missing(`v'), meanonly
    post `D' (`i') ("`v'") (`"`l'"') (r(N)) (r(min)) (r(max))
}
postclose `D'
postclose mrep
preserve
    use "$ROOT/_dictionary.dta", clear
    export excel using "$ROOT/Master_1380_1403.xlsx", sheet("Dictionary") firstrow(variables) sheetmodify
    use "$ROOT/_merge_report.dta", clear
    list, noobs sep(0) abbrev(30)
    export excel using "$ROOT/Master_1380_1403.xlsx", sheet("Merge_report") firstrow(variables) sheetmodify
restore
erase "$ROOT/_dictionary.dta"
erase "$ROOT/_merge_report.dta"

* restore Persian labels in the .dta (name = label)
use "$ROOT/Master_1380_1403.dta", clear
di as res _n "Done."
di as res "  $ROOT/Master_1380_1403.dta"
di as res "  $ROOT/Master_1380_1403.xlsx  (sheets: Persian, English, Dictionary, Merge_report)"
