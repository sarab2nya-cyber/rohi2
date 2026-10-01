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
* English labels (same list as 03_labels_en.do, included here so no extra file is needed)
cap label variable Symbol "Company (database label)"
cap label variable شرکت "Company code"
cap label variable Year "Fiscal year"
cap label variable کدصنعتجزئی "Industry code (detailed)"
cap label variable کدصنعتکلی "Industry code (general)"
cap label variable صنعت "Industry"
cap label variable طبقه "Industry sub-class"
cap label variable بازار "Market (TSE / Farabourse)"
cap label variable نماد "Ticker"
cap label variable تاریخمصوب "Approval date"
cap label variable نوع "Statement type"
cap label variable تلفیقی "Consolidated statements (yes/no)"
cap label variable حسابرسیشده "Audited (yes/no)"
cap label variable تجدیدارائهشده "Restated (yes/no)"
cap label variable وجوهنقدوموجودیهاینزدبانکه "Cash and bank balances"
cap label variable سرمایهگذاریهایکوتاهمدت "Short-term investments"
cap label variable سرمایهاجارهایحصهجاری "Finance lease receivable, current portion"
cap label variable داراییهایآمادهواگذاری "Assets held for sale"
cap label variable حصهجاریخالصتسهیلاتاعطائی "Loans granted, net, current portion"
cap label variable تسهیلاتاعطاییعقوداسلامی "Loans granted, Islamic contracts"
cap label variable تسهیلاتاعطاییقرضالحسنه "Loans granted, Qard al-Hasan"
cap label variable حسابهاواسناددریافتیتجاری "Trade notes and accounts receivable"
cap label variable سایرحسابهاواسناددریافتیتجا "Other trade receivables"
cap label variable طلبازشرکتهایگروهوشرکتهایو "Receivables from group and associated companies"
cap label variable موجودیمواداولیهوبستهبندی "Inventory: raw materials and packaging"
cap label variable موجودیکالایدرجریانساخت "Inventory: work in progress"
cap label variable موجودیکالایساختهشده "Inventory: finished goods"
cap label variable موجودیقطعاتولوازمیدکی "Inventory: spare parts"
cap label variable موجودیکالایخریداریشده "Inventory: purchased goods"
cap label variable کالایدرراه "Goods in transit"
cap label variable کالایامانیمانزددیگران "Own goods held by others (consignment)"
cap label variable کالایامانیدیگراننزدما "Others' goods held by the company (consignment)"
cap label variable سایرموجودیها "Other inventories"
cap label variable افزایشیاکاهشارزشموجودیها "Inventory valuation adjustment"
cap label variable انبارملزومات "Supplies store"
cap label variable موجودیضایعات "Scrap inventory"
cap label variable دارائیهایمالی "Financial assets"
cap label variable پروژههایدرجریانپیشرفت "Projects in progress"
cap label variable داراییهایزیستیغیرمولدومولد "Biological assets"
cap label variable داراییهایغیرجارینگهداریشده "Non-current assets held for sale"
cap label variable مطالباتازبیمهگذارانونمایندگ "Receivables from policyholders and agents"
cap label variable مطالباتازبیمهگرانوبیمهگران "Receivables from insurers and reinsurers"
cap label variable حسابهاواسناددریافتنی "Notes and accounts receivable"
cap label variable سایرحسابهاواسناددریافتنی "Other notes and accounts receivable"
cap label variable سهمبیمهگراناتکاییازذخائرفن "Reinsurers' share of technical reserves"
cap label variable موجودیموادوکالا "Inventories, total"
cap label variable سفارشاتواعتباراتاسنادی "Orders and letters of credit"
cap label variable سفارشاتموادوکالا "Orders of materials and goods"
cap label variable سفارشاتوپیشپرداختها "Orders and prepayments"
cap label variable وجوهومنابعحاصلازاوراقمشارک "Funds from participation bonds"
cap label variable مطالباتازبانکمرکزی "Claims on the Central Bank"
cap label variable مطالباتازسایربانکهاوموسسات "Claims on other banks and credit institutions"
cap label variable مطالباتازدولت "Claims on the government"
cap label variable تسهیلاتاعطایی "Loans granted"
cap label variable تسهیلاتاعطاییومطالباتازبخش "Loans and receivables, private sector"
cap label variable تسهیلاتاعطاییومطالباتازشرکت "Loans and receivables, companies"
cap label variable تسهیلاتاعطاییومطالباتازسایر "Loans and receivables, other"
cap label variable مطالباتبابتاعتباراتاسنادیوب "Receivables for letters of credit and guarantees"
cap label variable پیشپرداختها "Prepayments"
cap label variable جمعداراییهایجاری "Total current assets"
cap label variable مطالباتبلندمدت "Long-term receivables"
cap label variable سرمایهگذاریهایبلندمدت "Long-term investments"
cap label variable سرمایهاجارهایبلندمدت "Finance lease receivable, long-term portion"
cap label variable حصهبلندمدتخالصتسهیلاتاعطائی "Loans granted, net, long-term portion"
cap label variable اجارههایسرمایهای "Capital leases"
cap label variable وجوهومنابعحاصلازمشارکت "Funds from participations"
cap label variable سرمایهگذاریبلندمدتدرشرکتها "Long-term investments in companies"
cap label variable سایرسرمایهگذاریهایبلندمدت "Other long-term investments"
cap label variable طرحهایتوسعهوتکمیل "Development and completion projects"
cap label variable سفارشاتوپیشپرداختهایسرمایه "Capital orders and prepayments"
cap label variable حسابهاواسناددریافتنیتجاریبل "Long-term trade notes and accounts receivable"
cap label variable اوراقمشارکت "Participation bonds"
cap label variable گواهیسپردهکوتاهمدت "Short-term certificates of deposit"
cap label variable اوراقاجارهپرداختنی "Ijara (lease) bonds payable"
cap label variable سرمایهگذاریهاومشارکتها "Investments and participations"
cap label variable داراییهاینامشهود "Intangible assets"
cap label variable سرقفلی "Goodwill"
cap label variable سایرداراییها "Other assets"
cap label variable سرمایهگذاریهاوسایرداراییها "Investments and other assets"
cap label variable اموالماشینآلاتوتجهیزات "Property, plant and equipment"
cap label variable اقلامدرراه "Items in transit (assets)"
cap label variable ذخیرهاستهلاکداراییها "Accumulated depreciation"
cap label variable خالصداراییهایثابت "Net fixed assets"
cap label variable جمعداراییهایغیرجاری "Total non-current assets"
cap label variable جمعکلداراییها "Total assets"
cap label variable اوراقمشارکتحصهجاری "Participation bonds, current portion"
cap label variable حسابهاواسنادپرداختنیتجاری "Trade notes and accounts payable"
cap label variable سایرحسابهاواسنادپرداختنی "Other notes and accounts payable"
cap label variable بدهیبهشرکتهایگروهوشرکتهای "Payables to group and associated companies"
cap label variable سپردههاوپیشدریافتها "Deposits and advances received"
cap label variable ذخیرهمالیاتبردرآمد "Income tax provision"
cap label variable بدهیبهبانکمرکزی "Due to the Central Bank"
cap label variable بدهیبهسایربانکهاوموسساتاعت "Due to other banks and credit institutions"
cap label variable سپردههایدیداری "Demand deposits"
cap label variable سپردههایقرضالحسنهوپسانداز "Qard al-Hasan and savings deposits"
cap label variable سپردههایسرمایهگذاریمدتدار "Term investment deposits"
cap label variable سایرسپردهها "Other deposits"
cap label variable مالیاتپرداختنی "Taxes payable"
cap label variable سایرذخائر "Other provisions"
cap label variable تسهیلاتجاریمالیدریافتی "Short-term financial facilities (loans)"
cap label variable سودپرداختنیبهسپردهگذاران "Profit payable to depositors"
cap label variable بدهیبانکبابتپذیرشاعتباراتاس "Bank liability for accepted letters of credit"
cap label variable بدهیبهبیمهگذارانونمایندگان "Due to policyholders and agents"
cap label variable بدهیبهبیمهگذاراناتکایی "Due to reinsurers"
cap label variable سپردهاتکاییواگذاری "Reinsurance deposits"
cap label variable بدهیبهبیمهمرکزیایران "Due to Central Insurance of Iran"
cap label variable سودسهامدولت "Government dividends"
cap label variable ذخیرهحقبیمه "Premium reserve"
cap label variable ذخیرهخسارتمعوق "Outstanding claims reserve"
cap label variable ذخیرهریسکهایمنقضینشده "Unexpired risk reserve"
cap label variable سایرذخائرفنی "Other technical reserves"
cap label variable سودسهامپیشنهادیوپرداختنی "Proposed and payable dividends"
cap label variable بدهیهایمرتبطباداراییهایغیر "Liabilities of non-current assets held for sale"
cap label variable جمعبدهیهایجاری "Total current liabilities"
cap label variable حسابهاواسنادپرداختنیبلندمدت "Long-term notes and accounts payable"
cap label variable گواهیسپردهبلندمدت "Long-term certificates of deposit"
cap label variable پیشدریافتهایبلندمدت "Long-term advances received"
cap label variable سپردههایسرمایهگذاریبلندمدت "Long-term investment deposits"
cap label variable تسهیلاتمالیدریافتیبلندمدت "Long-term financial facilities (loans)"
cap label variable حقبیمهسالهایآینده "Premiums of future years"
cap label variable ذخیرهمزایایپایانخدمتکارکنان "Employee end-of-service benefits provision"
cap label variable اقلامدرراهبدهی "Items in transit (liabilities)"
cap label variable سایربدهیها "Other liabilities"
cap label variable جمعبدهیهایغیرجاری "Total non-current liabilities"
cap label variable جمعکلبدهیها "Total liabilities"
cap label variable حقوقعمومی "Public rights"
cap label variable سرمایه "Paid-in capital"
cap label variable سودوزیانانباشته "Retained earnings (accumulated profit or loss)"
cap label variable اندوختهقانونی "Legal reserve"
cap label variable اندوختهطرحوتوسعه "Expansion and development reserve"
cap label variable اندوختهاحتیاطی "Contingency reserve"
cap label variable اندوختهصرفسهام "Share premium reserve"
cap label variable اندوختهمخصوص "Special reserve"
cap label variable مازادزیانانباشتهسهماقلیت "Minority accumulated loss surplus"
cap label variable سایراندوختهها "Other reserves"
cap label variable مازادتجدیدارزیابیداراییهایغ "Revaluation surplus of non-current assets"
cap label variable افزایشسرمایهدرجریان "Capital increase in progress"
cap label variable سودوزیانناشیازتسعیردارائیه "Gain or loss on translation of assets"
cap label variable نتیجهتغییراتناشیازیکسانسازی "Effect of harmonising accounting policies"
cap label variable اندوختهتسعیردارائیهاوبدهیها "Translation reserve"
cap label variable مازادتجدیدارزیابیدارائیهایثا "Revaluation surplus of fixed assets"
cap label variable تفاوتناشیازتسعیرارز "Foreign-exchange translation difference"
cap label variable سهماقلیت "Minority interest"
cap label variable سهمشرکتاصلیدرفرعی "Parent's share in subsidiaries"
cap label variable جمعحقوقصاحبانسهامدرپایانسا "Total shareholders' equity at year end"
cap label variable جمعکلبدهیهاوحقوقصاحبانسها "Total liabilities and shareholders' equity"
cap label variable حقوقعمومیمصوب "Public rights, AGM-approved"
cap label variable سرمایهمصوب "Capital, AGM-approved"
cap label variable سودوزیانانباشتهمصوب "Retained earnings, AGM-approved"
cap label variable اندوختهقانونیمصوب "Legal reserve, AGM-approved"
cap label variable اندوختهسرمایهایمصوب "Capital reserve, AGM-approved"
cap label variable اندوختهاحتیاطیمصوب "Contingency reserve, AGM-approved"
cap label variable اندوختهطرحوتوسعهمصوب "Expansion reserve, AGM-approved"
cap label variable سایراندوختههایمصوب "Other reserves, AGM-approved"
cap label variable افزایشسرمایهدرجریانمصوب "Capital increase in progress, AGM-approved"
cap label variable جمعحقوقصاحبانسهاممصوبدرمج "Total shareholders' equity, AGM-approved"
cap label variable ارزشروز "Market value of equity (rials)"
cap label variable PS "Column PS (probably price-to-sales)"
cap label variable درآمدحقبیمهصادره "Gross premiums written"
cap label variable کاهشافزایشذخایرحقبیمه "Change in premium reserves"
cap label variable درآمدحقبیمه "Premium income"
cap label variable حقبیمهاتکائیواگذاری "Reinsurance premiums ceded"
cap label variable کاهشافزایشذخیرهحقبیمهاتکا "Change in reinsurance premium reserve"
cap label variable هزینهحقبیمهاتکائیواگذاری "Reinsurance premium expense"
cap label variable درآمدحقبیمهسهمنگهداری "Net retained premium income"
cap label variable خسارتپرداختی "Claims paid"
cap label variable افزایشکاهشذخایرخسارت "Change in claims reserves"
cap label variable هزینهخسارت "Claims expense"
cap label variable خسارتدریافتیازبیمهگراناتکائ "Claims recovered from reinsurers"
cap label variable افزایشکاهشذخیرهخسارتمعوقب "Change in outstanding claims reserve, reinsurers"
cap label variable خسارتسهمبیمهگراناتکائی "Reinsurers' share of claims"
cap label variable هزینهخسارتسهمنگهداری "Net retained claims expense"
cap label variable هزینهکارمزدوکارمزدمنافعاتکا "Commission expense (incl. reinsurance profit commission)"
cap label variable درآمدکارمزدوکارمزدمنافعاتکا "Commission income (incl. reinsurance profit commission)"
cap label variable خالصدرآمدهزینهکارمزدوکارم "Net commission income or expense"
cap label variable کاهشافزایشسایرذخایرفنی "Change in other technical reserves"
cap label variable هزینهعوارضشخصثالث "Third-party levy expense"
cap label variable هزینهسهمصندوقتامینخسارتهایب "Compensation-fund contribution expense"
cap label variable هزینهسهموزارتکشور "Ministry of Interior share expense"
cap label variable هزینهسهمناجا "Police (NAJA) share expense"
cap label variable هزینهسهمبهداشت "Health-sector share expense"
cap label variable سایرهزینههایبیمهای "Other insurance expenses"
cap label variable خالصسایردرآمدهاوهزینههایب "Net other insurance income and expenses"
cap label variable درآمدسرمایهگذاریازمحلذخایر "Investment income from reserves"
cap label variable کاهشافزایشذخیرهکاهشارزشسر "Change in investment impairment provision"
cap label variable خالصدرآمدسرمایهگذاریهاازمحل "Net investment income from reserves"
cap label variable سودناخالصفعالیتبیمهای "Gross profit from insurance activities"
cap label variable درآمدسرمایهگذاریازمحلسایرم "Investment income from other sources"
cap label variable هزینههایاداریوعمومیوپرسنلی "Administrative, general and personnel expenses"
cap label variable درآمدحاصلازخدماتوفروش "Revenue from sales and services (operating revenue)"
cap label variable سودحاصلازسرمایهگذاریها "Income from investments"
cap label variable سودحاصلازفروشسرمایهگذاریها "Gain on sale of investments"
cap label variable سودحاصلازسایرفعالیتها "Income from other activities"
cap label variable سودتسهیلاتاعطایی "Interest income on loans granted"
cap label variable درآمدحاصلازعملیاتلیزینگوخد "Leasing and service income"
cap label variable سوداوراقمشارکت "Interest on participation bonds"
cap label variable درآمدحاصلازقراردادهایمشارکت "Income from participation contracts"
cap label variable درآمدحاصلازفروشسرمایهگذاری "Income from sale of investments"
cap label variable سودحاصلازسرمایهگذاریهاوسپر "Income from investments and deposits"
cap label variable جایزهسپردهقانونی "Statutory deposit bonus"
cap label variable سودوجهالتزامدریافتی "Penalty income received"
cap label variable سایردرآمدهایمشاع "Other joint income"
cap label variable فروشخالصدرآمدحاصلازخدمات "Net sales and service revenue"
cap label variable سودعلیالحسابسپردههایسرمایه "Provisional profit on investment deposits"
cap label variable تفاوتسودقطعیوعلیالحسابسپرد "Difference between final and provisional deposit profit"
cap label variable هزینهافزایشنسبتدارائیهایثابت "Expense of fixed-asset ratio increase"
cap label variable سودتسهیلاتاعطاییغیرمشاع "Interest income on loans, non-joint"
cap label variable سوداوراقمشارکتغیرمشاع "Interest on participation bonds, non-joint"
cap label variable درآمدکارمزد "Commission income"
cap label variable درآمداجارهسرمایهای "Capital lease income"
cap label variable درآمدقراردادهایعاملیت "Agency contract income"
cap label variable نتیجهمعاملاتارزی "Foreign-exchange trading result"
cap label variable سودوجهالتزامدریافتیغیرمشاع "Penalty income, non-joint"
cap label variable سایردرآمدهایغیرمشاع "Other non-joint income"
cap label variable حقالوکاله "Agency fee (wakala)"
cap label variable جمعدرآمدها "Total revenue"
cap label variable بهایتمامشدهکالایفروشرفته "Cost of goods sold"
cap label variable بهایتمامشدهاملاکواگذارشدهو "Cost of real estate transferred"
cap label variable هزینهتامینمنابعمالیعملیاتلی "Funding cost of leasing operations"
cap label variable سودناویژه "Gross profit"
cap label variable هزینههایمالیتسهیلاتلیزینگ "Financial expenses of leasing facilities"
cap label variable کارمزدنقلوانتقالسهام "Share transfer fees"
cap label variable هزینههایتوزیعوفروش "Distribution and selling expenses"
cap label variable سودپرداختیبهاستثناءسودسپرد "Interest paid excluding deposit interest"
cap label variable سودپرداختیبهسپردهگذاران "Interest paid to depositors"
cap label variable مازادپرداختیبهسپردهگذاران "Excess paid to depositors"
cap label variable هزینههایعمومیواداری "General and administrative expenses"
cap label variable خالصدرآمدهاوهزینههایعملیاتی "Net other operating income and expenses"
cap label variable درآمدهاوهزینههایاستثنایی "Exceptional income and expenses"
cap label variable برگشتذخیرهکاهشارزشسرمایهگذا "Reversal of investment impairment provision"
cap label variable سودزیانعملیاتی "Operating profit (loss)"
cap label variable سایردرآمدهاوهزینههایغیربیمه "Other non-insurance income and expenses"
cap label variable هزینهمطالباتمشکوکالوصول "Doubtful receivables expense"
cap label variable هزینهاستهلاک "Depreciation expense"
cap label variable کارمزدپرداختیهزینهکارمزد "Commission and fee expense"
cap label variable هزینههایمالی "Financial expenses"
cap label variable سودزیانتسعیرتسهیلاتارزیدر "Translation gain or loss on foreign-currency loans"
cap label variable هزینهکل "Total expenses"
cap label variable درآمدحاصلازسرمایهگذاری "Investment income"
cap label variable اضافهکسرجذبسربار "Over- or under-absorbed overhead"
cap label variable خالصسایردرآمدهاهزینهها "Net other income and expenses"
cap label variable سودزیانفروشدارائیهایزیستیمو "Gain or loss on sale of biological assets"
cap label variable تعدیلارزشسرمایهگذاریها "Investment value adjustment"
cap label variable پاداشهیئتمدیره "Board of directors' bonus"
cap label variable سودسپردههایارزی "Interest on foreign-currency deposits"
cap label variable سایرهزینهها "Other expenses"
cap label variable سایردرآمدهاوهزینههایعملیاتی "Other operating income and expenses"
cap label variable سودوزیانعملیاتی "Operating profit (loss), alternative format"
cap label variable سایردرآمدهاوهزینههایغیرعمل "Other non-operating income and expenses"
cap label variable سهمگروهازسودشرکتهایوابسته "Group share of associates' profit"
cap label variable سودزیانقبلازتحصیلشرکتهای "Profit before acquisition of subsidiaries"
cap label variable اقلامغیرمترقبهاثراتانباشته "Extraordinary items and cumulative effects"
cap label variable سودزیانقبلازکسرمالیات "Profit (loss) before tax"
cap label variable مالیات "Income tax"
cap label variable سهماقلیتازسودسالجاری "Minority share of current-year profit"
cap label variable سودزیانپسازکسرمالیات "Net profit (loss) after tax"
cap label variable سودانباشتهابتدایدوره "Retained earnings at beginning of period"
cap label variable تعدیلاتسنواتی "Prior-period adjustments"
cap label variable سودسهاممصوبمجمعسالقبل "Dividends approved by previous AGM"
cap label variable انتقالازسایراندوختههابهسود "Transfer from other reserves to retained earnings"
cap label variable پاداشهیئتمدیرهمصوبهسالقبل "Board bonus approved for prior year"
cap label variable سایراندوختههایمصوبسالقبل "Other reserves approved for prior year"
cap label variable انتقالازحسابسودوزیانانباشت "Transfer from retained earnings"
cap label variable کاهشافزایشسرمایهازمحلزیان "Capital change from accumulated losses"
cap label variable سودقابلتخصیص "Distributable profit"
cap label variable ذخیرهپاداشهیئتمدیره "Board bonus provision"
cap label variable سودسهاممصوبسالجاری "Dividends approved for current year"
cap label variable خالصسایردرآمدهاوهزینههایع "Net other income and expenses (appropriation)"
cap label variable سودوزیانانباشتهدرپایاندوره "Retained earnings at end of period"
cap label variable نسبتسودبهفروش "Profit-to-sales ratio"
cap label variable EPSناخالص "EPS, gross"
cap label variable EPSخالص "EPS, net"
cap label variable نقدحاصلازعملیات "Cash generated from operations"
cap label variable پرداختهاینقدیبابتمالیاتبرد "Income tax paid"
cap label variable جریانخالصورودخروجنقدحاصل "Net cash flow from operating activities"
cap label variable دریافتهاینقدیحاصلازفروشدار "Proceeds from sale of assets (truncated header)"
cap label variable پرداختهاینقدیبرایخریددارایی "Payments to purchase assets (truncated header)"
cap label variable دریافتهاینقدیحاصلازفروشسرم "Proceeds from sale of investments"
cap label variable دریافتهاینقدیحاصلازفروششرک "Proceeds from sale of subsidiaries"
cap label variable پرداختهاینقدیبرایخریدشرکته "Payments to acquire subsidiaries"
cap label variable پرداختهاینقدیبرایخریدسرمایه "Payments to purchase investments"
cap label variable پرداختهاینقدیبرایتحصیلسرمای "Payments to acquire investments (truncated header)"
cap label variable پرداختهاینقدیبابتتسهیلاتاعط "Payments for loans granted"
cap label variable دریافتهاینقدیحاصلازاسترداد "Proceeds from repayment of loans granted"
cap label variable دریافتهاینقدیحاصلازسودتسهی "Interest received on loans granted"
cap label variable دریافتهاینقدیحاصلازسودسهام "Dividends received"
cap label variable دریافتهاینقدیحاصلازسودسرما "Interest received on investments"
cap label variable دریافتهاینقدیحاصلازسودسایر "Other interest received"
cap label variable سایرجریانهاینقدیحاصلازفعال "Other cash flows from investing activities"
cap label variable جريانخالصورودخروجنقدحاصل "Net cash flow from investing activities"
cap label variable جريانخالصورودخروجنقدقبلا "Net cash flow before financing activities"
cap label variable دریافتهاینقدیحاصلازافزایشس "Proceeds from capital increase"
cap label variable دریافتهاینقدیحاصلازافزايشس "Proceeds from capital increase (second column)"
cap label variable دریافتهاینقدیحاصلازصرفسهام "Proceeds from share premium"
cap label variable دریافتهاینقدیحاصلازفروشسها "Proceeds from sale of treasury shares"
cap label variable پرداختهاینقدیبرایخریدسهامخ "Payments to buy treasury shares"
cap label variable دریافتهاینقدیحاصلازتسهیلات "Proceeds from financial facilities (loans)"
cap label variable پرداختهاینقدیبابتاصلتسهیلات "Repayment of loan principal"
cap label variable پرداختهاینقدیبابتسودتسهیلات "Interest paid on loans"
cap label variable دریافتهاینقدیحاصلازانتشارا "Proceeds from issuing participation bonds"
cap label variable پرداختهاینقدیبابتاصلاوراقم "Repayment of participation bond principal"
cap label variable پرداختهاینقدیبابتسوداوراقم "Interest paid on participation bonds"
cap label variable پرداختهاینقدیبابتاصلاوراقخ "Repayment of bond principal (type truncated)"
cap label variable پرداختهاینقدیبابتسوداوراقخ "Interest paid on bonds (type truncated)"
cap label variable پرداختهاینقدیبابتسودسهامبه "Dividends paid (recipient truncated)"
cap label variable دریافتهاینقدیبابتانتشاراورا "Proceeds from issuing bonds"
cap label variable کاهشافزایشوجوهمسدودیبابتا "Change in restricted deposits"
cap label variable پرداختهاینقدیبابتسوداوراقس "Interest paid on bonds (type truncated, s)"
cap label variable پرداختهاینقدیبابتسوداوراقص "Interest paid on bonds (type truncated, sukuk)"
cap label variable دریافتهاینقدیبابتاستقراض "Proceeds from borrowing"
cap label variable بازپرداختهاینقدیبابتاستقراض "Repayment of borrowing"
cap label variable پرداختهاینقدیبابتاصلاقساطا "Repayment of lease instalment principal"
cap label variable پرداختهاینقدیبابتسوداجارهس "Interest paid on capital leases"
cap label variable پرداختهاینقدیبابتسودسهام "Dividends paid"
cap label variable بازپرداختودایعمشترکین "Repayment of subscriber deposits"
cap label variable دریافتهاینقدیبابتودایعمشترک "Proceeds from subscriber deposits"
cap label variable MT "Column MT (probably net cash flow from financing activities)"
cap label variable خالصافزايشکاهشدرموجودینقد "Net increase (decrease) in cash"
cap label variable ماندهموجودینقددرابتدایدوره "Cash at beginning of period"
cap label variable تعدیلاتتلفیقی "Consolidation adjustments"
cap label variable تاثيرتغييراتنرخارز "Effect of exchange-rate changes on cash"
cap label variable ماندهموجودینقددرپاياندوره "Cash at end of period"
cap label variable معاملاتغیرنقدی "Non-cash transactions"
cap label variable حاشیهسودخالص "Net profit margin (%)"
cap label variable حاشیهسودناخالص "Gross margin (%)"
cap label variable حاشیهسودعملیاتی "Operating profit margin (%)"
cap label variable حاشیهسودناویژه "Gross profit margin (%), alternative"
cap label variable سودبهسودناویژه "Net profit to gross profit (%)"
cap label variable بازدهداراییهاROA "Return on assets, ROA (%)"
cap label variable بازدهسرمایه "Return on capital (%)"
cap label variable بازدهیسرمایهROE "Return on equity, ROE (%)"
cap label variable بازدهسرمایهدرگردش "Return on working capital (%)"
cap label variable بازدهداراییثابت "Return on fixed assets (%)"
cap label variable سنجشسودمندیوام "Loan usefulness ratio"
cap label variable نسبتجاری "Current ratio"
cap label variable نسبتآنی "Quick ratio"
cap label variable نسبتنقدینگی "Cash ratio"
cap label variable نسبتداراییهایجاری "Current assets to total assets"
cap label variable نسبتکفایتنقد "Cash adequacy ratio"
cap label variable نسبتگردشنقد "Cash turnover ratio"
cap label variable سرمایهدرگردشخالص "Net working capital"
cap label variable دورهموجودیموادوکالا "Inventory holding period (days)"
cap label variable دورهوصولمطالبات "Collection period (days)"
cap label variable نسبتکالابهسرمایهدرگردش "Inventory to working capital"
cap label variable گردشسرمایهجاری "Working capital turnover"
cap label variable گردشداراییهایثابت "Fixed asset turnover"
cap label variable گردشمجموعداراییها "Total asset turnover"
cap label variable نسبتبدهی "Debt ratio"
cap label variable نسبتبدهیبهارزشویژه "Debt to equity"
cap label variable نسبتداراییثابتبهارزشویژه "Fixed assets to equity"
cap label variable نسبتبدهیبلندمدتبهارزشویژه "Long-term debt to equity"
cap label variable نسبتبدهیجاریبهارزشویژه "Current debt to equity"
cap label variable نسبتمالکانه "Equity ratio (%)"
cap label variable نسبتپوششبدهی "Debt coverage ratio"
cap label variable نسبتپوششبهره "Interest coverage ratio"
cap label variable نسبتبارمالیوام "Financial burden ratio"
cap label variable هزینههایمالیبهسودخالص "Financial expenses to net profit (%)"
cap label variable هزینههایمالیبهسودعملیاتی "Financial expenses to operating profit (%)"
cap label variable حقتقدم "Rights issue (%)"
cap label variable سهامجایزه "Bonus shares (%)"
cap label variable DPS "Dividend per share (DPS)"
cap label variable قیمتپایه "Base price"
cap label variable قیمتپایانی "Closing price at year end"
cap label variable بازدهی "Annual return (%)"
cap label variable رتبهنقدشوندگی "Liquidity rank"
cap label variable PD "Column PD (price block 2: rights issue)"
cap label variable PE "Column PE (price block 2: bonus shares)"
cap label variable PF "Column PF (price block 2: DPS)"
cap label variable PG "Column PG (price block 2: base price)"
cap label variable PH "Column PH (price block 2: closing price)"
cap label variable PI "Column PI (price block 2: return)"
cap label variable PJ "Column PJ (price block 2: liquidity rank)"
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
