*==============================================================================
* 05_screening.do  -  Section 3.1: sample screening from the raw data file
*
* Input : $ROOT/$RAWDATA  (all firm-years exported from the database: both
*         markets, all industries). First row = column names:
*           FirmCode Firm Year IndDetail IndID Industry Category Market Symbol
*           Age INF INV IA PPE TA TD BV Sales COGS SGA OI FinExp CFO CFI CFF MV
*         (Firm, IndDetail and Category are optional.)
* Output: $OUT/screened_data.dta  (read by 20_build.do)
*         $OUT/screening_log.dta  (rows of the sample-construction table;
*                                  completed in 20_build.do, sheet T0_sample)
*         $OUT/Screening_check.xlsx (lists to verify the automatic choices)
*
* Steps
*   1  TSE and Farabourse firm-years, $SCR_Y0-$SCR_Y1, one row per firm-year
*   2  less Farabourse firm-years (Market)
*   3  less financial firms: banks, credit institutions, insurance, leasing,
*      investment companies, holdings, brokers, funds (industry)
* All firms have an Esfand fiscal year-end (sample characteristic, no step).
* No minimum number of years: a firm-year enters estimation when the lagged
* data it needs exist. Book equity <= 0 is removed in 20_build.do.
*==============================================================================
local NEED "FirmCode Year IndID Industry Market Symbol Age INF INV IA PPE TA TD BV Sales COGS SGA OI FinExp CFO CFI CFF MV"

import excel "$ROOT/$RAWDATA", firstrow clear allstring
foreach v of local NEED {
    cap confirm variable `v'
    if _rc {
        di as err "Column `v' is missing in $RAWDATA (check the header row spelling)."
        exit 111
    }
}

* text normalisation for matching Persian labels: Arabic yeh/kaf -> Persian,
* remove zero-width non-joiners and spaces
foreach v in Market Industry {
    gen strL _n_`v' = ustrregexra(`v', "[\x{200C}\x{200F}\s]", "")
    replace _n_`v' = ustrregexra(_n_`v', "\x{064A}", "\x{06CC}")
    replace _n_`v' = ustrregexra(_n_`v', "\x{0643}", "\x{06A9}")
    replace _n_`v' = ustrregexra(_n_`v', "[\x{0622}\x{0623}\x{0625}]", "\x{0627}")
}

* numeric columns
foreach v of local NEED {
    if inlist("`v'", "FirmCode", "Industry", "Market", "Symbol") continue
    destring `v', replace ignore(", ") force
}
keep if inrange(Year, $SCR_Y0, $SCR_Y1)

cap postclose scr
postfile scr int step str80 label double(firms firmyears) using "$OUT/screening_log.dta", replace
cap program drop scrpost
program define scrpost
    args step label
    tempvar t
    qui egen byte `t' = tag(FirmCode)
    qui count if `t'
    local f = r(N)
    post scr (`step') ("`label'") (`f') (_N)
    di as res %-70s "`label'" "  firms = " %5.0f `f' "  firm-years = " %6.0f _N
end

*------------------------------------------------------------------------------
* Step 1: one row per firm-year
*------------------------------------------------------------------------------
duplicates tag FirmCode Year, gen(_dup)
qui count if _dup
if r(N) {
    di as err "Warning: " r(N) " rows share a FirmCode-Year; the first of each is kept. See Screening_check.xlsx, sheet duplicates."
    preserve
        keep if _dup
        export excel FirmCode Year Symbol Market Industry using "$OUT/Screening_check.xlsx", ///
            sheet("duplicates", replace) firstrow(variables)
    restore
}
sort FirmCode Year
by FirmCode Year: keep if _n == 1
drop _dup
scrpost 1 "Firm-years on TSE and Farabourse, $SCR_Y0-$SCR_Y1"

*------------------------------------------------------------------------------
* Step 2: Farabourse firm-years
*------------------------------------------------------------------------------
di as txt _n "Market values in the data:"
tab Market, missing
gen byte _fara = ustrregexm(_n_Market, "$SCR_FARA")
di as txt "Classified as Farabourse (removed):"
tab Market if _fara, missing
drop if _fara
scrpost 2 "Less: Farabourse firm-years"

*------------------------------------------------------------------------------
* Step 3: financial firms (industry name keywords or industry codes)
*------------------------------------------------------------------------------
gen byte _fin = ustrregexm(_n_Industry, "$SCR_FINWORDS")
if "$SCR_FINCODES" != "" {
    foreach c of global SCR_FINCODES {
        replace _fin = 1 if IndID == `c'
    }
}
* a firm is financial if it is classified as financial in any year
bys FirmCode: egen byte _finf = max(_fin)
preserve
    keep if _finf
    contract IndID Industry
    di as txt _n "Industries classified as financial (removed) - CHECK THIS LIST:"
    list, noobs sep(0)
    export excel using "$OUT/Screening_check.xlsx", sheet("financial_removed", replace) firstrow(variables)
restore
preserve
    keep if !_finf
    contract IndID Industry
    di as txt _n "Industries kept:"
    list, noobs sep(0)
    export excel using "$OUT/Screening_check.xlsx", sheet("industries_kept", replace) firstrow(variables)
restore
drop if _finf
scrpost 3 "Less: banks, insurance, leasing, investment, holding, broker and fund firms"
postclose scr

*------------------------------------------------------------------------------
* Data-quality checks (look before running the models)
*------------------------------------------------------------------------------
di as txt _n "Firm-years per year after screening:"
tab Year
di as txt _n "Median total assets by year (a sudden 10x or 1000x jump = unit change):"
tabstat TA Sales MV, by(Year) stat(p50) format(%14.0fc)
di as txt _n "Missing values by variable:"
foreach v in TA TD BV Sales CFO CFI CFF MV {
    qui count if missing(`v')
    di as txt %-8s "`v'" " missing: " %6.0f r(N)
}
di as txt _n "Sign of CFI (investing cash flow should be mostly negative):"
qui count if CFI < 0
local neg = r(N)
qui count if !missing(CFI)
di as txt "  share negative = " %5.3f `neg' / r(N)

* industry ID as stored by the database; IndID must be constant within firm
bys FirmCode (Year): gen byte _indchg = IndID != IndID[1]
qui count if _indchg
if r(N) {
    di as err "Note: " r(N) " firm-years have an IndID different from the firm's first year;" ///
        " the most frequent IndID of each firm is used."
    bys FirmCode IndID: gen _nind = _N
    bys FirmCode (_nind Year): replace IndID = IndID[_N]
    bys FirmCode (_nind Year): replace Industry = Industry[_N]
    drop _nind
}

keep `NEED'
drop Market
order FirmCode Symbol Year IndID Industry
compress
save "$OUT/screened_data.dta", replace
di as res _n "Screened data saved: $OUT/screened_data.dta"
