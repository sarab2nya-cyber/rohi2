*==============================================================================
* 03b_merge_check.do  -  ONE-OFF check: how does each file identify companies,
*                        and how many of its companies are found in the main file?
* Run on its own (Do-file Editor > Execute, nothing selected). Changes nothing.
* Output: C:/Users/Rohi/Desktop/Data/Merge_check.xlsx
*   ids        for each file: rows, identifier columns found, rows matched to
*              the main file by company code / ticker / company label
*   columns    first 15 columns of each file and an example value
*   unmatched  up to 60 identifiers per file that are NOT in the main file
*==============================================================================
version 17.0
clear all
set more off

global ROOT  "C:/Users/Rohi/Desktop/Data"
global RAW   "$ROOT/Raw"
global FILES "Main_1380_1402 File1_1403 File2_1403 File3_1403 File4_1403 File5_1403 File6_1403"
local  XL    "$ROOT/Merge_check.xlsx"
cap erase "`XL'"

cap program drop loadraw
program define loadraw
    args base
    cap confirm file "$RAW/`base'.dta"
    if !_rc {
        use "$RAW/`base'.dta", clear
        exit
    }
    import excel "$RAW/`base'.xlsx", firstrow clear
end

* normalised identifier: Persian yeh/kaf, no spaces, half-spaces or dashes
cap program drop normid
program define normid
    args src dst
    cap confirm string variable `src'
    if _rc qui tostring `src', gen(`dst') format(%20.0f)
    else   qui gen `dst' = `src'
    qui replace `dst' = ustrregexra(`dst', "[\x{200C}\x{200F}\s\-_]", "")
    qui replace `dst' = ustrregexra(`dst', "\x{064A}", "\x{06CC}")
    qui replace `dst' = ustrregexra(`dst', "\x{0643}", "\x{06A9}")
    qui replace `dst' = "" if `dst' == "."
end

* keys of the main file
loadraw Main_1380_1402
local k = 0
foreach v in شرکت نماد Symbol {
    local ++k
    local has`k' = 0
    cap confirm variable `v'
    if _rc continue
    local has`k' = 1
    preserve
        normid `v' _key
        keep _key
        drop if _key == ""
        duplicates drop
        gen byte _inmain = 1
        tempfile M`k'
        save `M`k''
    restore
}

cap postclose ids
postfile ids str20 file double(rows) str40 id_columns ///
    double(code_matched ticker_matched label_matched no_identifier) using "$ROOT/_ids.dta", replace
cap postclose cols
postfile cols str20 file int position str128 column str100 example using "$ROOT/_cols.dta", replace
cap postclose um
postfile um str20 file str20 id_type str100 identifier using "$ROOT/_um.dta", replace

foreach f of global FILES {
    loadraw `f'
    local N = _N
    * first 15 columns with an example value
    local i = 0
    foreach v of varlist _all {
        local ++i
        if `i' > 15 continue
        cap confirm string variable `v'
        if !_rc local ex = `v'[1]
        else    local ex = string(`v'[1], "%20.0g")
        post cols ("`f'") (`i') ("`v'") (`"`ex'"')
    }
    local idc ""
    gen byte _matched = 0
    local k = 0
    foreach v in شرکت نماد Symbol {
        local ++k
        local m`k' = .
        cap confirm variable `v'
        if _rc continue
        local idc "`idc' `v'"
        if !`has`k'' continue
        normid `v' _key
        qui merge m:1 _key using `M`k'', keep(master match) nogen
        qui count if _inmain == 1
        local m`k' = r(N)
        qui replace _matched = 1 if _inmain == 1
        * identifiers not found in the main file
        preserve
            qui keep if _inmain != 1 & _key != ""
            qui keep `v'
            cap confirm string variable `v'
            if _rc qui tostring `v', replace format(%20.0f)
            qui duplicates drop
            forvalues j = 1/`=min(_N, 60)' {
                post um ("`f'") ("`v'") (`"`=`v'[`j']'"')
            }
        restore
        drop _key _inmain
    }
    qui count if !_matched
    post ids ("`f'") (`N') ("`idc'") (`m1') (`m2') (`m3') (r(N))
    di as res "`f': " `N' " rows; identifier columns:`idc'; rows matched to the main file: " `N' - r(N)
}
postclose ids
postclose cols
postclose um

use "$ROOT/_ids.dta", clear
label variable file           "File"
label variable rows           "Rows"
label variable id_columns     "Identifier columns found"
label variable code_matched   "Rows matched by company code"
label variable ticker_matched "Rows matched by ticker"
label variable label_matched  "Rows matched by company label (Symbol)"
label variable no_identifier  "Rows NOT matched to the main file"
list, noobs sep(0) abbrev(20)
export excel using "`XL'", sheet("ids") firstrow(varlabels) replace
use "$ROOT/_cols.dta", clear
export excel using "`XL'", sheet("columns") firstrow(variables) sheetmodify
use "$ROOT/_um.dta", clear
export excel using "`XL'", sheet("unmatched") firstrow(variables) sheetmodify
erase "$ROOT/_ids.dta"
erase "$ROOT/_cols.dta"
erase "$ROOT/_um.dta"
di as res _n "Done: `XL'"
