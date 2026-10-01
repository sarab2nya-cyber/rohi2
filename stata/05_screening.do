*==============================================================================
* 05_screening.do  -  Section 3.1: builds the research file from the raw
*                     Rahavard Novin export and screens the sample
*
* Input  $ROOT/$RAWDATA   raw export (.dta or .xlsx), one row per firm-year,
*                         column names as exported (Persian, no spaces)
* Output $OUT/screened_data.dta              read by 20_build.do
*        $ROOT/Research_Data_${SCR_Y0}_${SCR_Y1}.xlsx  sheets Data, Screening,
*                                            Firms_per_year, Variables
*        $OUT/screening_log.dta              rows of the screening table
*                                            (completed in 20_build.do -> T0_sample)
*        $OUT/Screening_check.xlsx           lists to verify the automatic choices
*
* Screening (Section 3.1)
*   1  all firm-years $SCR_Y0-$SCR_Y1 in the database (TSE and Farabourse)
*   2  less Farabourse firms and firms with no market   (column «بازار»)
*   3  less financial firms                              (industry keywords)
*   4  less printing, retail, utilities, auxiliary financial activities
*   5  less firm-years without financial statements
*   6  less firm-years with book equity <= 0
*   7  less firms without usable data in every year (balanced panel; SCR_BALANCED)
*   Industries with fewer than $SCR_MINFIRMS firms are pooled into code 999.
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
* Settings when this file is run on its own (00_run_all.do sets them otherwise)
*------------------------------------------------------------------------------
if "$ROOT" == "" {
    version 17.0
    clear all
    set more off
    global ROOT    "C:/Users/Rohi/Desktop/Data"
    global OUT     "$ROOT/output"
    global RAWDATA "Master_1380_1403.dta"
    global AGEFILE "Firm_Age.xlsx"
    global INFFILE "Inflation.xlsx"
    global SCR_Y0  1380
    global SCR_Y1  1403
    global SCR_FARA "فرا"
    global SCR_FINWORDS "بانک|بیمه|لیزینگ|سرمایهگذاری|هلدینگ|چندرشته|کارگزاری|صندوق|واسطهگری|اعتباری|تامینسرمایه"
    global SCR_FINCODES ""
    global SCR_EXWORDS "چاپ|خردهفروشی|عرضهبرق|کمکیبهنهادهایمالی"
    global SCR_MINFIRMS 2
    global SCR_BALANCED 0
    global SCR_BAL_Y0 1393
    global SCREEN_ONLY 1
}
cap mkdir "$OUT"

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
gen byte _fara = ustrregexm(_n_Market, "$SCR_FARA") | Market == ""
qui count if Market == ""
if r(N) di as txt "Note: " r(N) " firm-years with no market in the database are removed with the Farabourse firms."
drop if _fara
scrpost 2 "Less: Farabourse firms and firms with no market in the database"

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
* Step 4: other excluded industries (printing, retail, utilities - electricity,
*         gas, steam and hot water -, activities auxiliary to financial
*         intermediation); keywords in SCR_EXWORDS
*------------------------------------------------------------------------------
gen byte _ex = ustrregexm(_n_Industry, "$SCR_EXWORDS")
bys FirmCode: egen byte _exf = max(_ex)
preserve
    keep if _exf
    if _N {
        contract IndID Industry, freq(firmyears)
        di as txt _n "Other EXCLUDED industries - check this list:"
        list, noobs sep(0)
        export excel using "$OUT/Screening_check.xlsx", sheet("other_excluded") firstrow(variables) sheetmodify
    }
    else di as err "No industry matched SCR_EXWORDS - check the keywords."
restore
drop if _exf
scrpost 4 "Less: printing, retail, utilities and auxiliary financial activities"
postclose scr

*------------------------------------------------------------------------------
* Step 4: full panel - every remaining firm in every year $SCR_Y0-$SCR_Y1.
*   Firms that entered the exchange later, left earlier, or have gaps are
*   NOT removed: their missing years stay in the panel as empty rows
*   (HasData = 0) and are reported in the screening table.
*------------------------------------------------------------------------------
local NY = $SCR_Y1 - $SCR_Y0 + 1
preserve
    keep FirmCode
    duplicates drop
    expand `NY'
    bys FirmCode: gen int Year = $SCR_Y0 + _n - 1
    tempfile grid
    save `grid'
restore
merge 1:1 FirmCode Year using `grid', nogen
gen int _negY = -Year
foreach v in Symbol Industry {
    bys FirmCode (Year):  replace `v' = `v'[_n-1] if `v' == "" & _n > 1
    bys FirmCode (_negY): replace `v' = `v'[_n-1] if `v' == "" & _n > 1
}
bys FirmCode (Year):  replace IndID = IndID[_n-1] if missing(IndID) & _n > 1
bys FirmCode (_negY): replace IndID = IndID[_n-1] if missing(IndID) & _n > 1
drop _negY
gen byte HasData = !missing(جمعکلداراییها)

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
* Step 5: book equity <= 0 (target leverage undefined): flagged, not used
gen byte InSample = HasData & !(BV <= 0)
gen str40 Note = ""
replace Note = "no financial statements in the database" if !HasData
replace Note = "book equity <= 0" if HasData & BV <= 0
qui count if HasData & BV <= 0
di as txt r(N) " firm-years with book equity <= 0 are flagged (InSample = 0)"

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
cap confirm numeric variable MT
if !_rc qui count if !missing(MT, CFF)
if !_rc & r(N) {
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
    qui count if missing(`v') & HasData
    di as txt %-7s "`v'" " missing (firm-years with statements): " %6.0f r(N)
}
drop _gap _r

*------------------------------------------------------------------------------
* Save: one workbook  $ROOT/Research_Data_${SCR_Y0}_${SCR_Y1}.xlsx
*   Data            research variables, sorted by firm and year
*   Screening       sample-construction table (English)
*   Firms_per_year  firms in the final sample, by year
*   Variables       definition and source of every variable
*------------------------------------------------------------------------------
local XL "$ROOT/Research_Data_${SCR_Y0}_${SCR_Y1}.xlsx"
cap erase "`XL'"
keep FirmCode Symbol Year Industry IndID HasData InSample Note AUDITED ///
    INV IA PPE TA TD BV Sales COGS SGA OI FinExp CFO CFI CFF MV
order FirmCode Symbol Year Industry IndID HasData InSample Note AUDITED ///
    INV IA PPE TA TD BV Sales COGS SGA OI FinExp CFO CFI CFF MV
sort FirmCode Year
compress

*------------------------------------------------------------------------------
* Screening table: Panel A sample construction, Panel B data availability
*------------------------------------------------------------------------------
cap postclose tbl
postfile tbl str8 panel str4 step str110 criterion str244 criterion_fa double(firms firmyears) ///
    using "$OUT/screening_table.dta", replace
preserve
    use "$OUT/screening_log.dta", clear
    sort step
    post tbl ("A") ("1") ("All firm-years in the database (TSE and Farabourse), ${SCR_Y0}-${SCR_Y1}") ///
        ("همه‌ی سال-شرکت‌های ۱۳۸۰ تا ۱۴۰۳ در پایگاه داده") (firms[1]) (firmyears[1])
    post tbl ("A") ("2") ("Less: Farabourse firms and firms with no market in the database") ///
        ("حذف شرکت‌های فرابورس و شرکت‌هایی که بازارشان در پایگاه داده مشخص نیست") ///
        (firms[2] - firms[1]) (firmyears[2] - firmyears[1])
    post tbl ("A") ("3") ("Less: banks, insurance, leasing, investment, holding, brokerage and fund companies") ///
        ("حذف شرکت‌های مالی: بانک، بیمه، لیزینگ، سرمایه‌گذاری، هلدینگ، کارگزاری، صندوق") ///
        (firms[3] - firms[2]) (firmyears[3] - firmyears[2])
    post tbl ("A") ("4") ("Less: printing, retail, utilities (electricity, gas, steam, hot water) and auxiliary financial activities") ///
        ("حذف صنایع چاپ، خرده‌فروشی، عرضه برق، گاز، بخار و آب گرم، و فعالیت‌های کمکی به نهادهای مالی واسط") ///
        (firms[4] - firms[3]) (firmyears[4] - firmyears[3])
restore
egen byte _tf = tag(FirmCode)
qui count if _tf
local F = r(N)
post tbl ("A") ("") ("TSE non-financial firms: full panel (`F' firms x `NY' years)") ///
    ("شرکت‌های بورسی غیرمالی: پنل کامل (شرکت × ۲۴ سال)") (`F') (_N)
qui count if !HasData
post tbl ("A") ("5") ("Less: firm-years without financial statements (not yet listed, delisted or not reported)") ///
    ("حذف سال-شرکت‌هایی که صورت مالی ندارند (هنوز پذیرفته نشده، خارج‌شده یا گزارش‌نشده)") (.) (-r(N))
qui count if HasData & BV <= 0
post tbl ("A") ("6") ("Less: firm-years with zero or negative book equity") ///
    ("حذف سال-شرکت‌هایی که حقوق صاحبان سهام صفر یا منفی دارند") (.) (-r(N))
bys FirmCode: egen int _ny = total(InSample)
egen byte _tfs = tag(FirmCode) if _ny > 0
* flag for sensitivity test S8: usable data in every year ${SCR_BAL_Y0}-${SCR_Y1}
bys FirmCode: egen int _nyb = total(InSample & Year >= $SCR_BAL_Y0)
gen byte Balanced = _nyb == ($SCR_Y1 - $SCR_BAL_Y0 + 1)
drop _nyb
* Step 7 (only if SCR_BALANCED = 1): balanced panel over the whole period
gen byte _keepfirm = _ny > 0
if "$SCR_BALANCED" == "1" {
    replace _keepfirm = _ny == `NY'
    qui count if _tfs == 1 & !_keepfirm
    local f7 = r(N)
    qui count if InSample & !_keepfirm
    post tbl ("A") ("7") ("Less: firms without usable data in every year ${SCR_Y0}-${SCR_Y1} (balanced panel)") ///
        ("حذف شرکت‌هایی که در همه‌ی سال‌های ۱۳۸۰ تا ۱۴۰۳ داده‌ی قابل استفاده ندارند (پنل متوازن)") (-`f7') (-r(N))
}
qui count if _tfs == 1 & _keepfirm
local FS = r(N)
qui count if InSample & _keepfirm
local NS = r(N)
post tbl ("A") ("=") ("Final sample") ("نمونه‌ی نهایی") (`FS') (`NS')
* Panel B: data availability of the firms remaining after step 6
bys FirmCode: egen int _first = min(cond(InSample, Year, .))
bys FirmCode: egen int _last  = max(cond(InSample, Year, .))
gen byte _gap = _ny > 0 & (_last - _first + 1) > _ny
qui count if _tfs == 1 & _ny == `NY'
local fa = r(N)
qui count if InSample & _ny == `NY'
post tbl ("B") ("") ("Firms with data in all `NY' years (after step 6)") ("شرکت‌هایی که داده‌ی هر ۲۴ سال را دارند") (`fa') (r(N))
qui count if _tfs == 1 & inrange(_ny, 2, `NY' - 1)
local fp = r(N)
qui count if InSample & inrange(_ny, 2, `NY' - 1)
post tbl ("B") ("") ("Firms with data for part of the period") ("شرکت‌هایی که داده‌ی بخشی از دوره را دارند") (`fp') (r(N))
qui count if _tfs == 1 & _ny == 1
local f1 = r(N)
qui count if InSample & _ny == 1
post tbl ("B") ("") ("Firms with data in only one year") ("شرکت‌هایی که فقط یک سال داده دارند") (`f1') (r(N))
qui count if _tfs == 1 & _first > $SCR_Y0
post tbl ("B") ("") ("  Of all firms: first year with data after ${SCR_Y0} (listed later)") ///
    ("از این میان: اولین داده بعد از ۱۳۸۰ (پذیرش دیرتر)") (r(N)) (.)
qui count if _tfs == 1 & _last < $SCR_Y1
post tbl ("B") ("") ("  Of all firms: last year with data before ${SCR_Y1} (delisted or not reported)") ///
    ("از این میان: آخرین داده قبل از ۱۴۰۳ (خروج یا عدم گزارش)") (r(N)) (.)
qui count if _tfs == 1 & _gap
post tbl ("B") ("") ("  Of all firms: missing years inside their period") ///
    ("از این میان: سال‌های خالی در میانه‌ی دوره") (r(N)) (.)
qui count if _tfs == 1 & Balanced
local fb = r(N)
qui count if InSample & Balanced
post tbl ("B") ("") ("Firms with data in every year ${SCR_BAL_Y0}-${SCR_Y1} (balanced subsample, sensitivity test S8)") ///
    ("شرکت‌هایی که در همه‌ی سال‌های ۱۳۹۳ تا ۱۴۰۳ داده دارند (زیرنمونه‌ی متوازن، آزمون حساسیت S8)") (`fb') (r(N))
postclose tbl
drop _tf _tfs _ny _first _last _gap

*------------------------------------------------------------------------------
* Final sample only: firm-years without statements or with book equity <= 0
* are removed (no empty rows). Gaps are handled by the panel lags.
*------------------------------------------------------------------------------
keep if InSample & _keepfirm
drop HasData InSample Note _keepfirm

*------------------------------------------------------------------------------
* Industries with fewer than $SCR_MINFIRMS firms in the final sample are pooled
* into one group "سایر صنایع" (Other industries), code 999
*------------------------------------------------------------------------------
* The database code «کدصنعتکلی» is a broad group (1-11) that bundles several
* industries, so industries are defined by their NAME («صنعت»); the group code
* is kept as IndGroup. New industry codes: 1, 2, ... by name; 999 = pooled.
gen double IndGroup      = IndID
gen        Industry_orig = Industry
gen _ik = ustrregexra(Industry, "[\x{200C}\x{200F}\x{0640}\x{064B}-\x{065F}\x{0670}\s\-،,]", "")
replace _ik = ustrregexra(_ik, "\x{064A}", "\x{06CC}")
replace _ik = ustrregexra(_ik, "\x{0643}", "\x{06A9}")
replace _ik = ustrregexra(_ik, "[\x{0622}\x{0623}\x{0625}]", "\x{0627}")
egen byte _tf = tag(FirmCode)
bys _ik: egen int _nf = total(_tf)
gen byte _pool = _nf < $SCR_MINFIRMS | _ik == ""
qui count if _ik == ""
if r(N) di as txt "Note: " r(N) " firm-years have no industry name; they join Other industries (999)."
local pooled ""
preserve
    keep if _pool & _tf & _ik != ""
    if _N {
        di as txt _n "Industries with fewer than $SCR_MINFIRMS firms (pooled into Other industries):"
        list IndGroup Industry, noobs sep(0)
        keep Industry
        duplicates drop
        forvalues i = 1/`=_N' {
            local pooled = cond(`"`pooled'"' == "", Industry[`i'], `"`pooled'; "' + Industry[`i'])
        }
    }
    else di as txt "No industry has fewer than $SCR_MINFIRMS firms; nothing is pooled."
restore
egen int _newid = group(_ik) if !_pool
replace IndID    = _newid
replace IndID    = 999 if _pool
replace Industry = "سایر صنایع" if _pool
drop _tf _nf _pool _ik _newid

* industry names in English (keywords on the normalised Persian name)
gen _k = ustrregexra(Industry, "[\x{200C}\x{200F}\x{0640}\x{064B}-\x{065F}\x{0670}\s\-،,]", "")
replace _k = ustrregexra(_k, "\x{064A}", "\x{06CC}")
replace _k = ustrregexra(_k, "\x{0643}", "\x{06A9}")
replace _k = ustrregexra(_k, "[\x{0622}\x{0623}\x{0625}]", "\x{0627}")
gen Industry_EN = ""
local R1  "سایرصنایع|Other industries"
local R2  "غذایی|Food products and beverages"
local R3  "قندوشکر|قند|Sugar"
local R4  "دارو|Pharmaceuticals"
local R5  "استخراجنفت|Oil and gas extraction services"
local R6  "نفتی|پالایش|کک|Refined petroleum products and coke"
local R7  "شیمیایی|Chemical products"
local R8  "کانههایفلزی|کانهفلزی|Metal ore mining"
local R9  "زغال|Coal mining"
local R10 "معادن|Other mining"
local R11 "فلزاتاساسی|Basic metals"
local R12 "محصولاتفلزی|Fabricated metal products"
local R13 "سیمان|Cement, lime and gypsum"
local R14 "کاشی|سرامیک|Tiles and ceramics"
local R15 "کانیغیرفلزی|Other non-metallic mineral products"
local R16 "لاستیک|پلاستیک|Rubber and plastic products"
local R17 "خودرو|Motor vehicles and parts"
local R18 "تجهیزاتحملونقل|Other transport equipment"
local R19 "برقی|Electrical machinery and apparatus"
local R20 "ماشین|Machinery and equipment"
local R21 "ارتباطی|Communication equipment"
local R22 "پزشکی|اپتیکی|اندازهگیری|Medical, optical and measuring instruments"
local R23 "منسوجات|نساجی|Textiles"
local R24 "چرم|Leather products"
local R25 "چوب|Wood products"
local R26 "کاغذ|Paper products"
local R27 "انبوهسازی|املاک|مستغلات|Real estate and construction"
local R28 "پیمانکاری|Industrial contracting"
local R29 "مخابرات|Telecommunications"
local R30 "رایانه|اطلاعاتوارتباطات|Computer and information services"
local R31 "حملونقل|انبارداری|Transport and storage"
local R32 "مهندسی|Technical and engineering services"
local R33 "هتل|رستوران|Hotels and restaurants"
local R34 "زراعت|کشاورزی|دامپروری|Agriculture"
local R35 "عمدهفروشی|بازرگانی|Wholesale trade"
local R36 "اموزش|Education"
local R37 "بهداشت|درمان|سلامت|Health services"
forvalues i = 1/37 {
    local en = ustrregexrf("`R`i''", "^.*\|", "")
    local kw = ustrregexrf("`R`i''", "\|[^|]*$", "")
    replace Industry_EN = "`en'" if Industry_EN == "" & ustrregexm(_k, "`kw'")
}
drop _k
qui count if Industry_EN == ""
if r(N) di as txt "Note: " r(N) " firm-years have an industry without an English name; add it in the Industries sheet."

* data for the models
preserve
    drop Industry_EN IndGroup Industry_orig
    save "$OUT/screened_data.dta", replace
restore

* Data sheet (final sample, sorted by firm and year)
order FirmCode Symbol Year IndID Industry Industry_EN IndGroup Industry_orig
sort FirmCode Year
export excel using "`XL'", sheet("Data") firstrow(variables) replace

* Industries sheet: code, Persian and English name, firms and firm-years
preserve
    egen byte _tf = tag(FirmCode)
    collapse (sum) firms = _tf (count) firmyears = Year (min) IndGroup, by(IndID Industry Industry_EN)
    order IndID Industry Industry_EN IndGroup firms firmyears
    sort IndID
    gen note = ""
    replace note = `"Pooled: industries with fewer than $SCR_MINFIRMS firms (`pooled') and firms without an industry name"' if IndID == 999
    replace IndGroup = . if IndID == 999
    label variable IndID       "Industry code"
    label variable Industry    "Industry (Persian)"
    label variable Industry_EN "Industry (English)"
    label variable IndGroup    "Database industry group (کدصنعتکلی)"
    label variable firms       "Firms"
    label variable firmyears   "Firm-years"
    label variable note        "Note"
    di as res _n "INDUSTRIES IN THE FINAL SAMPLE"
    list, noobs sep(0) abbrev(15)
    export excel using "`XL'", sheet("Industries") firstrow(varlabels) sheetmodify
restore

* Screening sheets: English and Persian
preserve
    use "$OUT/screening_table.dta", clear
    di as res _n "SAMPLE SCREENING TABLE (Panel A: sample construction; Panel B: data availability)"
    list panel step criterion firms firmyears, noobs sep(0) abbrev(20)
    label variable panel     "Panel"
    label variable step      "Step"
    label variable criterion "Criterion"
    label variable firms     "Firms"
    label variable firmyears "Firm-years"
    export excel panel step criterion firms firmyears using "`XL'", sheet("Screening") firstrow(varlabels) sheetmodify
    export excel panel step criterion firms firmyears using "$OUT/Screening_Table.xlsx", sheet("Screening") firstrow(varlabels) replace
    label variable panel        "بخش"
    label variable step         "مرحله"
    label variable criterion_fa "معیار"
    label variable firms        "شرکت"
    label variable firmyears    "سال-شرکت"
    export excel panel step criterion_fa firms firmyears using "`XL'", sheet("Screening_FA") firstrow(varlabels) sheetmodify
restore

* Firms per year
preserve
    egen byte _tf = tag(FirmCode Year)
    collapse (sum) firms = _tf, by(Year)
    label variable Year  "Fiscal year"
    label variable firms "Firms in the final sample"
    di as res _n "Firms per year in the final sample"
    list, noobs sep(0)
    export excel using "`XL'", sheet("Firms_per_year") firstrow(varlabels) sheetmodify
restore

* Variables
preserve
    clear
    input str14 variable str90 definition str110 source
    "FirmCode" "Company code"                                     "Database company code (شرکت); 9000001+ = firm not in the 1380-1402 file"
    "Symbol"   "Ticker"                                           "نماد"
    "Year"     "Fiscal year (Esfand year-end)"                    "Year"
    "Industry" "Industry (general classification)"                "صنعت"
    "IndID"    "Industry code by industry name (999 = pooled)"    "صنعت"
    "Industry_EN" "Industry (English)"                            "translated from صنعت"
    "IndGroup" "Database industry group (broad, 1-11)"            "کدصنعتکلی"
    "Industry_orig" "Industry name before pooling"                 "صنعت"
    "AUDITED"  "1 = audited statements, 0 = unaudited"            "حسابرسیشده"
    "Balanced" "1 = usable data in every year 1393-1403 (sensitivity S8)" "-"
    "INV"      "Inventories"                                      "موجودیموادوکالا"
    "IA"       "Intangible assets"                                "داراییهاینامشهود"
    "PPE"      "Net property, plant and equipment"                "خالصداراییهایثابت"
    "TA"       "Total assets"                                     "جمعکلداراییها"
    "TD"       "Total liabilities"                                "جمعکلبدهیها"
    "BV"       "Book value of equity"                             "جمعحقوقصاحبانسهامدرپایانسا"
    "Sales"    "Operating revenue"                                "درآمدحاصلازخدماتوفروش (if empty: جمعدرآمدها)"
    "COGS"     "Cost of goods sold"                               "بهایتمامشدهکالایفروشرفته"
    "SGA"      "Selling, general and administrative expenses"     "هزینههایعمومیواداری + هزینههایتوزیعوفروش"
    "OI"       "Operating profit"                                 "سودزیانعملیاتی (if empty: سودوزیانعملیاتی)"
    "FinExp"   "Financial expenses"                               "هزینههایمالی"
    "CFO"      "Net cash flow from operating activities"          "جریانخالصورودخروجنقدحاصل (operating)"
    "CFI"      "Net cash flow from investing activities"          "جريانخالصورودخروجنقدحاصل (investing)"
    "CFF"      "Net cash flow from financing activities"          "net change in cash - cash flow before financing"
    "MV"       "Market value of equity at year end"               "closing price x paid-in capital / 1000"
    end
    label variable variable   "Variable"
    label variable definition "Definition (amounts in million rials)"
    label variable source     "Source column in the database"
    export excel using "`XL'", sheet("Variables") firstrow(varlabels) sheetmodify
restore
di as res _n "Research workbook: `XL'  (sheets Data, Screening, Firms_per_year, Variables)"


