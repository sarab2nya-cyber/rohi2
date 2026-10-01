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

* prepfile: Year, identifiers, numeric/text types, empty columns
*   identifiers: company code (شرکت), ticker (نماد) and company label (Symbol);
*   the 1403 files may carry only one of them
cap program drop prepfile
program define prepfile
    args ydef fname
    cap drop _merge*
    cap confirm variable Year
    if _rc gen int Year = `ydef'
    cap confirm string variable Year
    if !_rc destring Year, replace force ignore(", ")
    if "`ydef'" != "." qui replace Year = `ydef' if missing(Year)
    * which identifiers does this file have?
    local hasid = 0
    foreach v in $FIRMKEY $TICKER Symbol {
        cap confirm variable `v'
        if !_rc local hasid = 1
    }
    if !`hasid' {
        di as err _n "`fname' has none of the identifier columns $FIRMKEY, $TICKER or Symbol."
        di as err "Its first columns are:"
        local i = 0
        foreach v of varlist _all {
            local ++i
            if `i' <= 25 di as err "   `i'. `v'"
        }
        di as err "Rename the column that identifies the company to $TICKER (ticker) or $FIRMKEY (code) in this file and run again."
        exit 111
    }
    cap confirm variable $FIRMKEY
    if _rc gen double $FIRMKEY = .
    cap confirm string variable $FIRMKEY
    if !_rc destring $FIRMKEY, replace force ignore(", ")
    foreach v in $TICKER Symbol {
        cap confirm variable `v'
        if _rc gen str1 `v' = ""
    }
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
            * numbers stored as text: converted only if every value is numeric
            cap destring `v', replace ignore(", ")
        }
        cap confirm string variable `v'
        if !_rc {
            qui replace `v' = ustrtrim(`v')
            qui count if `v' != ""
        }
        else qui count if !missing(`v')
        if r(N) == 0 & !inlist("`v'", "$FIRMKEY", "Year", "$TICKER", "Symbol") drop `v'
    }
    * matching keys: Arabic yeh/kaf -> Persian, no spaces, half-spaces or dashes
    foreach v in $TICKER Symbol {
        local k = cond("`v'" == "Symbol", "_ksy", "_ktk")
        qui gen `k' = ustrregexra(`v', "[\x{200C}\x{200F}\s\-_]", "")
        qui replace `k' = ustrregexra(`k', "\x{064A}", "\x{06CC}")
        qui replace `k' = ustrregexra(`k', "\x{0643}", "\x{06A9}")
    }
    qui drop if missing($FIRMKEY) & _ktk == "" & _ksy == ""
    post mrep ("`fname'") ("rows with an identifier") (_N) (.)
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

* one row per company-year: keep the row with most information
cap program drop onerow
program define onerow
    args fname
    tempvar nm dup
    qui egen int `nm' = rownonmiss(_all), strok
    qui duplicates tag $FIRMKEY Year, gen(`dup')
    qui count if `dup'
    if r(N) post mrep ("`fname'") ("company-years reported twice (row with most data kept)") (r(N)) (.)
    qui bys $FIRMKEY Year (`nm'): keep if _n == _N
    drop `nm' `dup'
end

cap postclose mrep
postfile mrep str40 file str60 step double(rows extra) using "$ROOT/_merge_report.dta", replace

*------------------------------------------------------------------------------
* 1. Read and clean the seven files (0 = main file 1380-1402)
*------------------------------------------------------------------------------
local files "$MAIN $F1403"
local k = -1
foreach f of local files {
    local ++k
    loadraw `f'
    post mrep ("`f'") ("rows read") (_N) (.)
    local yd = cond(`k' == 0, ".", "1403")
    prepfile `yd' "`f'"
    if `k' > 0 {
        qui count if Year != 1403
        if r(N) di as err "Note: `f' has " r(N) " rows with a year other than 1403 (kept as they are)."
    }
    tempfile p`k'
    save `p`k''
}
local K = `k'

*------------------------------------------------------------------------------
* 2. Company code for every row
*    from the main file: ticker -> code and company label -> code;
*    companies not in the main file get a new code 9000001, 9000002, ...
*------------------------------------------------------------------------------
use `p0', clear
foreach key in _ktk _ksy {
    preserve
        keep `key' $FIRMKEY
        drop if `key' == "" | missing($FIRMKEY)
        bys `key' ($FIRMKEY): keep if _n == _N
        rename $FIRMKEY _c`key'
        tempfile L`key'
        save `L`key''
    restore
}
forvalues j = 0/`K' {
    use `p`j'', clear
    local f : word `=`j' + 1' of `files'
    qui count if !missing($FIRMKEY)
    local n0 = r(N)
    foreach key in _ktk _ksy {
        qui merge m:1 `key' using `L`key'', keep(master match) nogen
        qui replace $FIRMKEY = _c`key' if missing($FIRMKEY)
        drop _c`key'
    }
    qui count if !missing($FIRMKEY)
    post mrep ("`f'") ("company code found from ticker or name") (r(N) - `n0') (.)
    save `p`j'', replace
}
* registry of companies that are not in the main file
clear
gen str1 _kname = ""
forvalues j = 0/`K' {
    preserve
        use `p`j'', clear
        keep if missing($FIRMKEY)
        gen _kname = cond(_ktk != "", _ktk, _ksy)
        keep _kname
        tempfile u
        save `u'
    restore
    append using `u'
}
duplicates drop _kname, force
drop if _kname == ""
sort _kname
gen double _cnew = 9000000 + _n
post mrep ("All") ("companies not in the 1380-1402 file (new codes 9000001+)") (_N) (.)
tempfile reg
save `reg'
forvalues j = 0/`K' {
    use `p`j'', clear
    local f : word `=`j' + 1' of `files'
    gen _kname = cond(_ktk != "", _ktk, _ksy)
    qui merge m:1 _kname using `reg', keep(master match) nogen
    qui replace $FIRMKEY = _cnew if missing($FIRMKEY)
    drop _cnew _kname
    onerow "`f'"
    save `p`j'', replace
}

*------------------------------------------------------------------------------
* 3. Merge: main file, then each 1403 file, on company code and year.
*    Same columns for other firms -> rows added; other columns for the same
*    firms -> joined side by side; the first non-missing value is kept.
*------------------------------------------------------------------------------
use `p0', clear
forvalues j = 1/`K' {
    qui ds, has(type string)
    local mstr `r(varlist)'
    qui ds, has(type numeric)
    local mnum `r(varlist)'
    preserve
        use `p`j'', clear
        harmon "`mstr'" "`mnum'"
        save `p`j'', replace
    restore
    qui merge 1:1 $FIRMKEY Year using `p`j'', update
    local fj : word `=`j' + 1' of `files'
    qui count if _merge == 2
    post mrep ("`fj'") ("rows added (company-years not yet present)") (r(N)) (.)
    qui count if inlist(_merge, 3, 4)
    post mrep ("`fj'") ("rows joined (same company-year, more columns)") (r(N)) (.)
    qui count if _merge == 5
    post mrep ("`fj'") ("cells with conflicting values (first file kept)") (r(N)) (.)
    drop _merge
}
drop _ktk _ksy

* identifiers that are fixed within a firm: fill gaps from the firm's other years
foreach v in $TICKER Symbol صنعت طبقه بازار {
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
sort $FIRMKEY Year
compress
egen byte _tf = tag($FIRMKEY)
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
