*==============================================================================
* 05_screening.do  -  Section 3.1: builds the research file from the raw
*                     Rahavard Novin export and screens the sample
*
* Input  $ROOT/$RAWDATA   raw export (.dta or .xlsx), one row per firm-year,
*                         column names as exported (Persian, no spaces)
*        $ROOT/$AGEFILE   Excel, two columns:  Symbol | FoundYear
*                         (ticker as in column «نماد», Persian founding year)
*        $ROOT/$INFFILE   Excel, two columns:  Year | INF   (CPI inflation, %)
* Output $OUT/screened_data.dta              read by 20_build.do
*        $ROOT/Final_Master_Data_${SCR_Y0}_${SCR_Y1}.xlsx   sorted research file
*        $OUT/screening_log.dta              rows of the screening table
*                                            (completed in 20_build.do -> T0_sample)
*        $OUT/Screening_check.xlsx           lists to verify the automatic choices
*
* Screening (Section 3.1)
*   1  all firm-years $SCR_Y0-$SCR_Y1 in the database (TSE and Farabourse)
*   2  less Farabourse firms                       (column «بازار»)
*   3  less financial firms                        (industry name keywords)
*   4  less firm-years without financial statements in the database
*   5  less book equity <= 0                       (20_build.do)
* All firms have an Esfand year-end (sample characteristic, no step). No
* minimum number of years: a firm-year enters estimation when its lags exist.
*
* Variable construction (million rials):
*   TA   جمعکلداراییها          TD  جمعکلبدهیها
*   BV   جمعحقوقصاحبانسهامدرپایانسا          PPE خالصداراییهایثابت
*   IA   داراییهاینامشهود          INV موجودیموادوکالا
*   Sales درآمدحاصلازخدماتوفروش  (if missing: جمعدرآمدها)
*   COGS بهایتمامشدهکالایفروشرفته
*   SGA  هزینههایعمومیواداری + هزینههایتوزیعوفروش (selling expenses are reported separately in the old format)
*   OI   سودزیانعملیاتی  (if missing: سودوزیانعملیاتی)
*   FinExp هزینههایمالی
*   CFO  net cash from operating activities   (جریانخالصورودخروجنقدحاصل, Persian yeh)
*   CFI  net cash from investing activities   (جريانخالصورودخروجنقدحاصل, Arabic yeh)
*   CFF  net change in cash - net cash flow before financing
*        (خالصافزايشکاهشدرموجودینقد - جريانخالصورودخروجنقدقبلا)
*   The database reports every year in the 3-category cash-flow format;
*   the identity CFO + CFI = cash flow before financing is checked below.
*   MV   year-end closing price x shares; shares = paid-in capital / 1,000 rials
*        (قیمتپایانی x سرمایه / 1000); compared with ارزشروز below
*==============================================================================

*------------------------------------------------------------------------------
* 0. Load
*------------------------------------------------------------------------------
if ustrregexm("$RAWDATA", "\.dta$") use "$ROOT/$RAWDATA", clear
else import excel "$ROOT/$RAWDATA", firstrow clear
local NUM "شرکت کدصنعتکلی جمعکلداراییها جمعکلبدهیها جمعحقوقصاحبانسهامدرپایانسا خالصداراییهایثابت داراییهاینامشهود موجودیموادوکالا درآمدحاصلازخدماتوفروش جمعدرآمدها بهایتمامشدهکالایفروشرفته هزینههایعمومیواداری هزینههایتوزیعوفروش سودزیانعملیاتی سودوزیانعملیاتی هزینههایمالی جریانخالصورودخروجنقدحاصل جريانخالصورودخروجنقدحاصل جريانخالصورودخروجنقدقبلا خالصافزايشکاهشدرموجودینقد قیمتپایانی سرمایه ارزشروز"
foreach v of local NUM {
    cap confirm variable `v'
    if _rc {
        di as err "Column `v' not found in $RAWDATA."
        exit 111
    }
    cap confirm string variable `v'
    if !_rc destring `v', replace ignore(", ") force
}
foreach v in Year {
    cap confirm string variable `v'
    if !_rc destring `v', replace ignore(", ") force
}
foreach v in صنعت بازار نماد حسابرسیشده تجدیدارائهشده نوع {
    cap confirm string variable `v'
    if _rc {
        tostring `v', replace
        replace `v' = "" if `v' == "."
    }
    replace `v' = ustrtrim(`v')
}
keep if inrange(Year, $SCR_Y0, $SCR_Y1)
* the export has its own (unused) columns named Symbol; keep the names free
foreach v in Symbol Industry Market IndID Age INF {
    cap rename `v' _raw_`v'
}

* identifiers: company code «شرکت»; rows without a code take the code of
* the same ticker in other years
rename شرکت FirmCode
bys نماد (FirmCode): replace FirmCode = FirmCode[1] if missing(FirmCode) & نماد != ""
qui count if missing(FirmCode)
if r(N) di as txt "Note: " r(N) " rows have neither a company code nor a ticker - dropped."
drop if missing(FirmCode)
gen Symbol   = نماد
gen Industry = صنعت
gen double IndID  = کدصنعتکلی
gen Market   = بازار
* fill ticker, industry and market from the firm's other years
gen int _negY = -Year
foreach v in Symbol Industry Market {
    bys FirmCode (Year):  replace `v' = `v'[_n-1] if `v' == "" & _n > 1
    bys FirmCode (_negY): replace `v' = `v'[_n-1] if `v' == "" & _n > 1
}
bys FirmCode (Year):  replace IndID = IndID[_n-1] if missing(IndID) & _n > 1
bys FirmCode (_negY): replace IndID = IndID[_n-1] if missing(IndID) & _n > 1
drop _negY
* one industry per firm: the most frequent code (reported)
bys FirmCode IndID: gen int _nind = _N if !missing(IndID)
bys FirmCode (_nind Year): gen byte _indchg = IndID != IndID[_N] & !missing(IndID)
qui count if _indchg
if r(N) di as txt "Note: " r(N) " firm-years carry a different industry code; the firm's most frequent code is used."
bys FirmCode (_nind Year): replace IndID = IndID[_N]
bys FirmCode (_nind Year): replace Industry = Industry[_N]
drop _nind _indchg

*------------------------------------------------------------------------------
* text normalisation for matching (yeh/kaf variants, half-spaces, spaces)
*------------------------------------------------------------------------------
foreach v in Market Industry {
    gen _n_`v' = ustrregexra(`v', "[\x{200C}\x{200F}\s]", "")
    replace _n_`v' = ustrregexra(_n_`v', "\x{064A}", "\x{06CC}")
    replace _n_`v' = ustrregexra(_n_`v', "\x{0643}", "\x{06A9}")
    replace _n_`v' = ustrregexra(_n_`v', "[\x{0622}\x{0623}\x{0625}]", "\x{0627}")
}

cap erase "$OUT/Screening_check.xlsx"
local xmode "replace"                     // first sheet creates the file
cap postclose scr
postfile scr int step str90 label double(firms firmyears) using "$OUT/screening_log.dta", replace
cap program drop scrpost
program define scrpost
    args step label
    tempvar t
    qui egen byte `t' = tag(FirmCode)
    qui count if `t'
    local f = r(N)
    post scr (`step') ("`label'") (`f') (_N)
    di as res %-75s "`label'" " firms = " %5.0f `f' "  firm-years = " %6.0f _N
end

*------------------------------------------------------------------------------
* Step 1: one row per firm-year
*------------------------------------------------------------------------------
duplicates tag FirmCode Year, gen(_dup)
qui count if _dup
if r(N) {
    di as err "Warning: " r(N) " rows share a company code and year; the row with total assets is kept."
    preserve
        keep if _dup
        export excel FirmCode Year Symbol using "$OUT/Screening_check.xlsx", sheet("duplicates") firstrow(variables) `xmode'
    restore
    local xmode "sheetmodify"
}
gen byte _hasTA = !missing(جمعکلداراییها)
bys FirmCode Year (_hasTA): keep if _n == _N
drop _dup _hasTA
scrpost 1 "All firm-years in the database, TSE and Farabourse, $SCR_Y0-$SCR_Y1"

*------------------------------------------------------------------------------
* Step 2: Farabourse
*------------------------------------------------------------------------------
di as txt _n "Market (after filling from the firm's other years):"
tab Market, missing
gen byte _fara = ustrregexm(_n_Market, "$SCR_FARA")
qui count if Market == ""
if r(N) di as txt "Note: " r(N) " firm-years with unknown market are kept with the TSE firms; see Screening_check.xlsx."
drop if _fara
scrpost 2 "Less: Farabourse firms"

*------------------------------------------------------------------------------
* Step 3: financial firms
*------------------------------------------------------------------------------
gen byte _fin = ustrregexm(_n_Industry, "$SCR_FINWORDS")
if "$SCR_FINCODES" != "" {
    foreach c of global SCR_FINCODES {
        replace _fin = 1 if IndID == `c'
    }
}
bys FirmCode: egen byte _finf = max(_fin)
preserve
    keep if _finf
    local nfin = _N
    if `nfin' {
        contract IndID Industry, freq(firmyears)
        di as txt _n "Industries classified as FINANCIAL (removed) - check this list:"
        list, noobs sep(0)
        export excel using "$OUT/Screening_check.xlsx", sheet("financial_removed") firstrow(variables) `xmode'
    }
    else di as err "No industry matched the financial keywords - check SCR_FINWORDS."
restore
if `nfin' local xmode "sheetmodify"
preserve
    keep if !_finf
    contract IndID Industry Market, freq(firmyears)
    di as txt _n "Industries kept:"
    list, noobs sep(0)
    export excel using "$OUT/Screening_check.xlsx", sheet("industries_kept") firstrow(variables) `xmode'
restore
drop if _finf
scrpost 3 "Less: banks, insurance, leasing, investment, holding and other financial firms"

*------------------------------------------------------------------------------
* Step 4: firm-years without financial statements in the database
*------------------------------------------------------------------------------
drop if missing(جمعکلداراییها)
scrpost 4 "Less: firm-years without financial statements in the database"
postclose scr

*------------------------------------------------------------------------------
* Variables used by the study (million rials)
*------------------------------------------------------------------------------
gen double TA     = جمعکلداراییها
gen double TD     = جمعکلبدهیها
gen double BV     = جمعحقوقصاحبانسهامدرپایانسا
gen double PPE    = خالصداراییهایثابت
gen double IA     = داراییهاینامشهود
gen double INV    = موجودیموادوکالا
gen double Sales  = درآمدحاصلازخدماتوفروش
qui count if missing(Sales) & !missing(جمعدرآمدها)
di as txt "Sales taken from total revenue for " r(N) " firm-years (operating revenue column empty)"
replace Sales     = جمعدرآمدها if missing(Sales)
gen double COGS   = abs(بهایتمامشدهکالایفروشرفته)
gen double SGA    = abs(هزینههایعمومیواداری) + cond(missing(هزینههایتوزیعوفروش), 0, abs(هزینههایتوزیعوفروش)) if !missing(هزینههایعمومیواداری) | !missing(هزینههایتوزیعوفروش)
gen double OI     = سودزیانعملیاتی
replace OI        = سودوزیانعملیاتی if missing(OI)
gen double FinExp = abs(هزینههایمالی)
gen double CFO    = جریانخالصورودخروجنقدحاصل
gen double CFI    = جريانخالصورودخروجنقدحاصل
gen double CFF    = خالصافزايشکاهشدرموجودینقد - جريانخالصورودخروجنقدقبلا
gen double MV     = قیمتپایانی * سرمایه / 1000
gen byte AUDITED  = ustrregexm(حسابرسیشده, "^بل[\x{06CC}\x{064A}]") if حسابرسیشده != "" & حسابرسیشده != "-"

*------------------------------------------------------------------------------
* Checks (read them in the log before running the models)
*------------------------------------------------------------------------------
di as res _n "CHECK 1. Cash-flow identity CFO + CFI = cash flow before financing"
gen double _gap = abs(CFO + CFI - جريانخالصورودخروجنقدقبلا)
qui count if !missing(_gap)
local n = r(N)
qui count if _gap <= 2 & !missing(_gap)
di as txt "  holds (|gap| <= 2) in " r(N) " of `n' firm-years"
qui count if !missing(MT, CFF)
if r(N) {
    qui corr CFF MT
    di as txt "  correlation of CFF with column MT (probably net financing cash flow) = " %6.4f r(rho)
}
di as res _n "CHECK 2. Sign of investing cash flow (should be mostly negative)"
qui count if CFI < 0
local a = r(N)
qui count if !missing(CFI)
di as txt "  share CFI < 0 = " %5.3f `a' / r(N)
di as res _n "CHECK 3. Market value: price x shares versus column ارزشروز (in rials)"
gen double _r = MV / (ارزشروز / 1e6)
tabstat _r, by(Year) stat(n p25 p50 p75) format(%6.3f)
di as txt "  a median ratio near 1 in every year: both measure year-end market value"
di as res _n "CHECK 4. Units: median total assets, sales and MV by year (million rials)"
tabstat TA Sales MV, by(Year) stat(p50) format(%14.0fc)
di as res _n "CHECK 5. Unaudited statements"
tab Year AUDITED, missing
di as res _n "CHECK 6. Missing values in the study variables"
foreach v in TA TD BV PPE IA INV Sales COGS SGA OI FinExp CFO CFI CFF MV {
    qui count if missing(`v')
    di as txt %-7s "`v'" " missing: " %6.0f r(N)
}
drop _gap _r

*------------------------------------------------------------------------------
* Age and inflation
*------------------------------------------------------------------------------
cap confirm file "$ROOT/$AGEFILE"
if !_rc {
    preserve
        import excel "$ROOT/$AGEFILE", firstrow clear
        keep Symbol FoundYear
        cap confirm string variable Symbol
        if _rc tostring Symbol, replace
        replace Symbol = ustrtrim(Symbol)
        destring FoundYear, replace force
        duplicates drop Symbol, force
        tempfile age
        save `age'
    restore
    merge m:1 Symbol using `age', keep(master match) nogen
    gen double Age = Year - FoundYear if Year >= FoundYear
    qui count if missing(Age)
    di as txt "Age missing for " r(N) " firm-years (ticker not in $AGEFILE)"
    drop FoundYear
}
else {
    di as err "$AGEFILE not found: Age is left empty. Add the file (Symbol | FoundYear) before running the models."
    gen double Age = .
}
cap confirm file "$ROOT/$INFFILE"
if !_rc {
    preserve
        import excel "$ROOT/$INFFILE", firstrow clear
        keep Year INF
        destring Year INF, replace force
        tempfile inf
        save `inf'
    restore
    merge m:1 Year using `inf', keep(master match) nogen
}
else {
    di as err "$INFFILE not found: INF is left empty. Add the file (Year | INF) before running the models."
    gen double INF = .
}

*------------------------------------------------------------------------------
* Save: research file sorted by firm and year
*------------------------------------------------------------------------------
keep FirmCode Symbol Year Industry IndID Market AUDITED Age INF INV IA PPE TA TD BV ///
    Sales COGS SGA OI FinExp CFO CFI CFF MV
order FirmCode Symbol Year Industry IndID Market AUDITED Age INF INV IA PPE TA TD BV ///
    Sales COGS SGA OI FinExp CFO CFI CFF MV
sort FirmCode Year
compress
export excel using "$ROOT/Final_Master_Data_${SCR_Y0}_${SCR_Y1}.xlsx", firstrow(variables) replace
di as res "Sorted research file: $ROOT/Final_Master_Data_${SCR_Y0}_${SCR_Y1}.xlsx"
drop Market
save "$OUT/screened_data.dta", replace

*------------------------------------------------------------------------------
* Screening table (Section 3.1) -> $ROOT/Screening_Table.xlsx
*   steps 1-4 from above; step 5 (book equity <= 0) previewed here and
*   applied in 20_build.do; firm-years by year after all steps
*------------------------------------------------------------------------------
qui count if BV <= 0
local nbv = r(N)
egen byte _tf = tag(FirmCode) if !(BV <= 0)
qui count if _tf == 1
local ffin = r(N)
qui count if !(BV <= 0)
local nfin = r(N)
drop _tf
preserve
    use "$OUT/screening_log.dta", clear
    sort step
    gen double firms_removed     = firms[_n-1] - firms
    gen double firmyears_removed = firmyears[_n-1] - firmyears
    local N = _N + 2
    set obs `N'
    replace step = 5 in `=_N - 1'
    replace label = "Less: firm-years with book equity <= 0" in `=_N - 1'
    replace firmyears_removed = `nbv' in `=_N - 1'
    replace firmyears = firmyears[_N - 2] - `nbv' in `=_N - 1'
    replace firms = `ffin' in `=_N - 1'
    replace firms_removed = firms[_N - 2] - `ffin' in `=_N - 1'
    replace step = 6 in `=_N'
    replace label = "Final sample, ${SCR_Y0}-${SCR_Y1} (incl. base year ${SCR_Y0})" in `=_N'
    replace firms = `ffin' in `=_N'
    replace firmyears = `nfin' in `=_N'
    order step label firms_removed firmyears_removed firms firmyears
    format firms* firmyears* %9.0fc
    di as res _n "SAMPLE SCREENING TABLE"
    list, noobs sep(0) abbrev(20)
    export excel using "$ROOT/Screening_Table.xlsx", sheet("screening") firstrow(variables) replace
restore
preserve
    keep if !(BV <= 0)
    egen byte _tf = tag(FirmCode Year)
    collapse (sum) firms = _tf, by(Year)
    rename firms firms_in_year
    di as res _n "Firms per year in the final sample"
    list, noobs sep(0)
    export excel using "$ROOT/Screening_Table.xlsx", sheet("firms_per_year") firstrow(variables) sheetmodify
restore
di as res "Screening table: $ROOT/Screening_Table.xlsx"
qui count if missing(Age) | missing(INF)
if r(N) == _N & "$SCREEN_ONLY" != "1" {
    di as err _n "Age and/or INF are empty: the research file is saved, but the models cannot be"
    di as err "estimated until $AGEFILE and $INFFILE are added. Stopping here."
    exit 459
}
