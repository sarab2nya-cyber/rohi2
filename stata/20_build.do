*==============================================================================
* 20_build.do  -  imports the raw data and constructs every variable exactly as
*                 in Sections 3.1-3.6 of the methodology.
*
* buildpanel is a program so that the robustness/sensitivity files can rebuild
* the panel with a different choice (cut-offs, cell sizes, DEA returns to
* scale, expectation model, investment / leverage definition, target model,
* life-cycle definition). Defaults = the main specification.
*==============================================================================

cap program drop buildpanel
program define buildpanel
    syntax [, CUTS(numlist min=2 max=2) TRIM MINCELL(integer 10) MINDEA(integer 15) ///
        RTS(string) EXPMODEL(string) INVDEF(string) LEVDEF(string) TARGET(string) ///
        LCDEF(string) TAG(string) DEAFRONT(string) VERBOSE]
    if "`cuts'"     == "" local cuts     "1 99"
    if "`rts'"      == "" local rts      "vrs"
    if "`expmodel'" == "" local expmodel "biddle"
    if "`invdef'"   == "" local invdef   "$INVDEF_MAIN"
    if "`invdef'"   == "" local invdef   "net"
    if "`levdef'"   == "" local levdef   "book"
    if "`target'"   == "" local target   "base"
    if "`lcdef'"    == "" local lcdef    "cons"
    if "`deafront'" == "" local deafront "ind"     // DEA frontier: ind (all years) | indyr
    if "`tag'"      == "" local tag      "main"
    local trimopt = cond("`trim'" != "", "trim", "")
    local V = cond("`verbose'" != "", "noisily", "quietly")
    local W "cuts(`cuts') `trimopt' tag(`tag')"

    quietly {
    *--------------------------------------------------------------------------
    * CPI index from INF (1392 = 1); used only to deflate DEA inputs/outputs
    *--------------------------------------------------------------------------
    preserve
        keep Year INF
        collapse (mean) INF, by(Year)
        sort Year
        gen double CPI = 1 if _n == 1
        replace CPI = CPI[_n-1] * (1 + INF / $INF_SCALE) if _n > 1
        keep Year CPI
        tempfile cpi
        save `cpi'
    restore
    merge m:1 Year using `cpi', nogen keep(master match)
    sort FirmID Year

    *--------------------------------------------------------------------------
    * 3.2 / 3.3 / 3.6  Ratios (winsorized after construction, pooled 1/99)
    *--------------------------------------------------------------------------
    if "`invdef'" == "net" gen double Invest = ((PPE + IA) - (L.PPE + L.IA)) / L.TA
    else                   gen double Invest = -CFI / L.TA
    gen double SalesGrowth = (Sales - L.Sales) / L.Sales
    if "`levdef'" == "book" gen double TDA = TD / TA
    else                    gen double TDA = TD / (TD + MV)
    gen double IOB    = FinExp / TA
    gen double COL    = (INV + PPE) / TA
    gen double LTA    = ln(TA / CPI)          // real size, 1392 prices
    gen double MTB    = MV / BV
    gen double PROFIT = OI / TA
    gen double FCF    = CFO / TA
    gen double lnAge  = ln(1 + Age)
    wins Invest SalesGrowth TDA IOB COL LTA MTB PROFIT FCF, `W'

    * INDLEV: median TDA of the industry-year, excluding the firm itself
    egen long INDYR = group(IndID Year)
    * industries with fewer than 5 firms are pooled into one group (IND_D);
    * used for INDLEV, the DEA frontier and the industry dummies
    egen byte _tf = tag(IndID FirmID)
    bys IndID: egen _nf = total(_tf)
    gen long IND_D = cond(_nf >= 5, IndID, 9999)
    drop _tf _nf
    egen long INDYR_D = group(IND_D Year)
    gen double INDLEV = .
    tempvar tv
    gen byte `tv' = !missing(TDA, INDYR_D)
    sort INDYR_D FirmID
    mata: loo_median("TDA", "INDYR_D", "INDLEV", "`tv'")
    sort FirmID Year
    drop `tv'

    sort FirmID Year
    foreach v in IOB COL LTA MTB PROFIT FCF INDLEV INF {
        gen double L_`v' = L.`v'
    }

    *--------------------------------------------------------------------------
    * 3.3 Target leverage, Eq. (2), and deviation, Eqs. (3)-(4)
    *     industry dummies, no year dummies (INF carries the time variation)
    *--------------------------------------------------------------------------
    local det "L_IOB L_COL L_LTA L_MTB L_PROFIT L_INDLEV L_INF"
    if "`target'" == "noiob" {
        local dropiob "L_IOB"
        local det : list det - dropiob
    }
    if inlist("`target'", "base", "noiob") {
        `V' reg TDA `det' i.IndID if Year >= 1393, vce(cluster FirmID)
        est store TGT_`tag'
        predict double TDAhat if e(sample), xb
    }
    else {
        `V' reghdfe TDA `det' if Year >= 1393, absorb(FirmID) vce(cluster FirmID) resid(_rtg)
        est store TGT_`tag'
        predict double TDAhat, xbd
        drop _rtg
    }
    replace TDAhat = min(max(TDAhat, 0), 1) if !missing(TDAhat)
    gen double CSDev = TDA - TDAhat
    wins CSDev, `W'
    gen double CSDP = max( CSDev, 0) if !missing(CSDev)
    gen double CSDN = max(-CSDev, 0) if !missing(CSDev)
    gen byte OVERLEV  = CSDev > 0 if !missing(CSDev)
    gen byte UNDERLEV = CSDev < 0 if !missing(CSDev)

    *--------------------------------------------------------------------------
    * 3.2 Expectation model, Eq. (1), by industry-year (>= mincell obs);
    *     smaller cells: industry regression with year dummies
    *--------------------------------------------------------------------------
    sort FirmID Year
    gen double L_SG = L.SalesGrowth
    if "`expmodel'" == "biddle" {
        cellresid Invest L_SG, gen(InvEff) cell(INDYR) fallback(IndID) ///
            minobs(`mincell') fallfe(i.Year)
    }
    else {
        gen byte   NEGSG  = L_SG < 0 if !missing(L_SG)
        gen double NEGxSG = NEGSG * L_SG
        cellresid Invest NEGSG L_SG NEGxSG, gen(InvEff) cell(INDYR) fallback(IndID) ///
            minobs(`mincell') fallfe(i.Year)
    }
    wins InvEff, `W'
    sort FirmID Year

    *--------------------------------------------------------------------------
    * 3.4 Life cycle (Dickinson 2011), measured at t-1
    *--------------------------------------------------------------------------
    gen byte LC5 = .
    replace LC5 = 1 if CFO <= 0 & CFI <= 0 & CFF >  0
    replace LC5 = 2 if CFO >  0 & CFI <= 0 & CFF >  0
    replace LC5 = 3 if CFO >  0 & CFI <= 0 & CFF <= 0
    replace LC5 = 4 if (CFO <= 0 & CFI <= 0 & CFF <= 0) | (CFO > 0 & CFI > 0)
    replace LC5 = 5 if CFO <= 0 & CFI >  0
    replace LC5 = . if missing(CFO, CFI, CFF)
    label define lc5 1 "Introduction" 2 "Growth" 3 "Mature" 4 "Shake-out" 5 "Decline", replace
    label values LC5 lc5

    gen byte STAGE = .
    if "`lcdef'" == "cons" {
        replace STAGE = 1 if inlist(LC5, 1, 2)
        replace STAGE = 2 if LC5 == 3
        replace STAGE = 3 if inlist(LC5, 4, 5)
    }
    else if "`lcdef'" == "pure" {
        replace STAGE = 1 if LC5 == 2
        replace STAGE = 2 if LC5 == 3
        replace STAGE = 3 if LC5 == 5
    }
    else {
        * age- and growth-based classification (Anthony & Ramesh 1992 type)
        sort FirmID Year
        gen double _sg3 = (SalesGrowth + L.SalesGrowth + L2.SalesGrowth) / 3
        replace _sg3 = SalesGrowth if missing(_sg3)
        pctrank _sg3, gen(_prsg) by(INDYR)
        pctrank Age,  gen(_prage) by(INDYR)
        gen double _score = _prsg + (1 - _prage)
        pctrank _score, gen(_prsc) by(Year)
        replace STAGE = cond(_prsc > 2/3, 1, cond(_prsc < 1/3, 3, 2)) if !missing(_prsc)
        drop _sg3 _prsg _prage _score _prsc
    }
    label define stg 1 "Growth" 2 "Maturity" 3 "Decline", replace
    label values STAGE stg
    sort FirmID Year
    gen byte STAGE_L = L.STAGE
    label values STAGE_L stg
    gen byte GROW = STAGE_L == 1 if !missing(STAGE_L)
    gen byte MAT  = STAGE_L == 2 if !missing(STAGE_L)
    gen byte DEC  = STAGE_L == 3 if !missing(STAGE_L)
    gen byte GD   = (GROW == 1 | DEC == 1) if !missing(STAGE_L)

    *--------------------------------------------------------------------------
    * 3.5 Managerial ability (Demerjian, Lev & McVay 2012)
    *     Stage 1: input-oriented DEA. Main: one frontier per industry over all
    *     years (values in 1392 prices) - industry-year frontiers put more than
    *     half of the firms on the frontier (no discrimination). Option
    *     deafront(indyr): per industry-year (>= mindea firms), else pooled.
    *--------------------------------------------------------------------------
    sort FirmID Year
    gen double rSales = Sales / CPI
    gen double rCOGS  = COGS  / CPI
    gen double rSGA   = SGA   / CPI
    gen double rPPE_L = L.PPE / L.CPI
    gen double rIA_L  = L.IA  / L.CPI
    gen byte dea_ok = !missing(rSales, rCOGS, rSGA, rPPE_L, rIA_L) & rSales > 0 & ///
        rCOGS >= 0 & rSGA >= 0 & rPPE_L >= 0 & rIA_L >= 0
    if "`deafront'" == "indyr" {
        bys INDYR: egen n_dea = total(dea_ok)
        gen long DEA_CELL = INDYR if n_dea >= `mindea'
        replace DEA_CELL = -IndID if n_dea < `mindea'
    }
    else {
        bys IND_D: egen n_dea = total(dea_ok)
        gen long DEA_CELL = -IND_D
    }
    gen double FE = .
    local vrs = ("`rts'" == "vrs")
    levelsof DEA_CELL if dea_ok, local(dcells)
    foreach c of local dcells {
        tempvar t
        gen byte `t' = dea_ok & DEA_CELL == `c'
        mata: dea_score("rCOGS rSGA rPPE_L rIA_L", "rSales", "`t'", "FE", `vrs')
        drop `t'
    }
    replace FE = 1 if FE > 0.999999 & !missing(FE)

    *     Stage 2: Tobit censored from above at 1, Eq. (5)
    bys INDYR: egen double _isales = total(Sales)
    gen double MktShare = Sales / _isales
    drop _isales
    gen byte FCFpos = (CFO + CFI) > 0 if !missing(CFO, CFI)
    sort FirmID Year
    `V' tobit FE LTA MktShare FCFpos lnAge i.Year i.IndID, ul(1) vce(cluster FirmID)
    est store TOB_`tag'
    predict double FEhat if e(sample), xb
    gen double MA_raw = FE - FEhat
    wins MA_raw, `W'
    su MA_raw if Year >= 1393, meanonly
    gen double MA = MA_raw - r(mean)
    * alternatives used in robustness R7
    pctrank MA_raw, gen(MA_rank) by(INDYR)
    replace MA_rank = MA_rank - 0.5
    sort FirmID Year
    gen double MA_avg = (MA + L.MA) / 2

    *--------------------------------------------------------------------------
    * Dummies, interactions, estimation-sample flag
    *--------------------------------------------------------------------------
    tab Year, gen(yd_)
    drop yd_1
    * industry dummies: industries with fewer than 5 firms are pooled into one
    * category (single-firm industry dummies are not identified in GMM)
    sort FirmID Year
    tab IND_D, gen(ind_)
    drop ind_1
    buildint
    sort FirmID Year
    gen byte EST = !missing(InvEff, L.InvEff, CSDP, CSDN, MA, STAGE_L, ///
        L_LTA, L_MTB, L_PROFIT, L_FCF) & Year >= 1395
    }
    xtset FirmID Year
end

*==============================================================================
* Import and prepare the raw panel (once)
*==============================================================================
import excel "$ROOT/$DATA", firstrow clear

* string identifiers are kept; everything else must be numeric
foreach v of varlist _all {
    if inlist("`v'", "Symbol", "Industry") continue
    cap confirm string variable `v'
    if !_rc destring `v', replace ignore(", ") force
}
encode Symbol, gen(FirmID)

* checks: duplicates, years, balance
duplicates report FirmID Year
duplicates drop FirmID Year, force
xtset FirmID Year
xtdescribe
tab Year

* expenses may be stored with a negative sign in some databases: use magnitudes
foreach v in COGS SGA FinExp {
    qui count if `v' < 0
    if r(N) di as txt "Note: `v' has " r(N) " negative values - absolute values are used."
    replace `v' = abs(`v')
}

* INF in percent or in decimals?
qui su INF
global INF_SCALE = cond(r(max) > 1, 100, 1)
di as txt "INF treated as " cond($INF_SCALE == 100, "percent", "decimal")

* basic validity: total assets must be positive
* negative or zero book equity: target leverage is not defined (standard
* exclusion in the capital-structure literature)
qui count if BV <= 0
di as txt "Excluding " r(N) " firm-years with non-positive book equity (BV <= 0)"
drop if BV <= 0
qui count if TA <= 0
if r(N) di as err "Dropping " r(N) " firm-years with non-positive total assets"
drop if TA <= 0
save "$OUT/raw_panel.dta", replace

*==============================================================================
* Main build, with winsorization and first-stage logs
*==============================================================================
cap postclose winlog
postfile winlog str16 tag str16 variable double(N p_low p_high n_low n_high) ///
    using "$OUT/log_winsorization.dta", replace
cap postclose cellog
postfile cellog double(cell N b_salesgrowth r2) byte source ///
    using "$OUT/log_expectation_model_cells.dta", replace

use "$OUT/raw_panel.dta", clear
buildpanel, verbose
postclose winlog
postclose cellog

* label the analysis variables
label var InvEff  "Investment inefficiency (signed residual, Eq. 1)"
label var Invest  "Investment"
label var SalesGrowth "Sales growth"
label var TDA     "Total debt / total assets"
label var TDAhat  "Target leverage (Eq. 2)"
label var CSDev   "Capital structure deviation"
label var CSDP    "CSD+ (over-leverage)"
label var CSDN    "CSD- (under-leverage)"
label var OVERLEV  "Over-leveraged (CSDev > 0)"
label var UNDERLEV "Under-leveraged (CSDev < 0)"
label var FE      "DEA firm efficiency"
label var MA      "Managerial ability (centered)"
label var LTA     "Size: ln(real total assets)"
label var MTB     "Market-to-book"
label var PROFIT  "Profitability"
label var FCF     "Operating cash flow / TA"
label var L_LTA    "Size (t-1)"
label var L_MTB    "Market-to-book (t-1)"
label var L_PROFIT "Profitability (t-1)"
label var L_FCF    "Operating cash flow / TA (t-1)"
label var IOB     "Interest burden"
label var COL     "Collateral"
label var INDLEV  "Industry median leverage"
label var GROW    "Growth stage (t-1)"
label var MAT     "Maturity stage (t-1)"
label var DEC     "Decline stage (t-1)"
label var GD      "Growth or decline (t-1)"
label var CSDP_GROW   "CSD+ x Growth"
label var CSDP_DEC    "CSD+ x Decline"
label var CSDN_MAT    "CSD- x Maturity"
label var CSDP_MA     "CSD+ x MA"
label var CSDN_MA     "CSD- x MA"
label var CSDP_GD     "CSD+ x GD"
label var MA_GD       "MA x GD"
label var CSDP_MA_GD  "CSD+ x MA x GD"
label var MA_MAT      "MA x Maturity"
label var CSDN_MA_MAT "CSD- x MA x Maturity"

save "$OUT/analysis_panel.dta", replace

* winsorization report (Excel): cut-offs and number of values changed
preserve
    use "$OUT/log_winsorization.dta", clear
    gen double pct_changed = 100 * (n_low + n_high) / N
    format p_low p_high %12.4f
    format pct_changed %5.2f
    list, noobs sep(0) abbrev(16)
    export excel using "$OUT/Tables.xlsx", sheet("T0_winsorization") firstrow(variables) replace
restore
