*==============================================================================
* MASTER DO-FILE (revised identification & measurement)
*
* "The Asymmetric Impact of Managerial Ability on Investment Efficiency under
*  Capital Structure Deviation: Evidence from Emerging Markets"
*
* Hypotheses (tested exactly as stated):
*  H1a  Over-leverage (positive CSD)  -> under-investment
*  H1b  Under-leverage (negative CSD) -> over-investment
*  H2a  Over-leverage's effect on under-investment is intensified in growth
*       and decline stages
*  H2b  Under-leverage's effect on over-investment is intensified in the
*       maturity stage
*  H3a  High managerial ability mitigates under-investment from over-leverage
*       (especially growth/decline stages)
*  H3b  High managerial ability limits over-investment from under-leverage
*       (especially maturity stage)
*
* See docs/METHODOLOGY.md for the diagnosis of the original script and the
* justification of every design choice below. Section numbers match.
*
* Required raw columns (names as in Final_Master_Data.xlsx):
*   Symbol Year IndID TA TD BV PPE IA INV Sales COGS SGA OI FinExp
*   CFO CFI CFF MV Age INF
* Optional columns (used automatically if present):
*   Country (string) or CountryID (numeric), Capex, Div (cash dividends)
*
* Packages: ftools require reghdfe estout (required); xtabond2 boottest
*           (optional). Installed offline from the stata_pkgs folder (see
*           INSTALL_PACKAGES.md). winsor2 is built in. Stata 16+ (Mata
*           LinearProgram() is used for DEA, so the user-written -dea- is NOT
*           needed).
*==============================================================================
version 16.0
clear all
set more off
set seed 20261001

*------------------------------------------------------------------------------
* 0. PATHS & SWITCHES  (edit here only)
*------------------------------------------------------------------------------
global ROOT      "C:\Users\Rohi\Desktop\Data"
global PLUS      "C:\Users\Rohi\Desktop\plus"
global DATA      "Final_Master_Data.xlsx"
global OUT       "$ROOT\output"

global WCUT      "1 99"     // winsorize RATIOS at 1/99 (never raw levels)
global MIN_CELL  10         // min obs per industry-year for first-stage models
global MIN_DEA   20         // min obs per DEA frontier (else industry-pooled)
global DEA_VRS   1          // 1 = VRS frontier, 0 = CRS
global INF_SCALE 100        // INF in percent (e.g. 35 = 35%) -> 100; decimals -> 1
global INVDEF    "cash"     // "cash" = -CFI/L.TA (revaluation-proof); "accrual" = d(PPE+IA)/L.TA
global FIN_IND   ""         // IndID codes of financial/holding firms to exclude, e.g. "30 31"
global CLUST     "FirmID"

cap mkdir "$OUT"
cd "$ROOT"

* Community packages are installed from the LOCAL folder stata_pkgs (shipped
* with this project) - no internet and no Java needed. Each package sits in
* its own sub-folder, e.g. $PKGDIR\reghdfe\reghdfe.pkg. SSC is tried only if
* the local folder is missing.
global PKGDIR    "C:\Users\Rohi\Desktop\stata_pkgs"
cap mkdir "$PLUS"
sysdir set PLUS "$PLUS"
adopath + "$PLUS"
local REQ "ftools require reghdfe estout"      // required
local OPT "xtabond2 boottest"                   // optional (robustness only)
foreach p in `REQ' `OPT' {
    cap which `p'
    if _rc {
        cap confirm file "$PKGDIR\`p'\`p'.pkg"
        if !_rc {
            di as txt "Installing `p' from $PKGDIR ..."
            cap noi net install `p', from("$PKGDIR\`p'") replace
        }
        else {
            di as txt "Local copy of `p' not found - trying SSC ..."
            cap noi ssc install `p', replace
        }
    }
}
cap noi ftools, compile
cap noi reghdfe, compile

* Stop early with a clear message if anything required is still missing
local MISSING ""
foreach p of local REQ {
    cap which `p'
    if _rc local MISSING "`MISSING' `p'"
}
qui sysuse auto, clear
cap reghdfe price weight, absorb(rep78)
local RHDFE_OK = (_rc == 0)
clear
if "`MISSING'" != "" | !`RHDFE_OK' {
    di as err _n "Required packages are missing or not working:`MISSING'"
    if !`RHDFE_OK' di as err "reghdfe is installed but does not run (usually ftools/require missing)."
    di as err "Check that PKGDIR points to the unzipped stata_pkgs folder (see stata/INSTALL_PACKAGES.md)."
    exit 199
}
foreach p of local OPT {
    cap which `p'
    if _rc di as txt "Note: optional package `p' not installed - its robustness block will be skipped."
}

* Built-in winsorizer (replaces the SSC package winsor2; same syntax as used
* here: winsor2 varlist, replace cuts(lo hi))
cap program drop winsor2
program define winsor2
    syntax varlist(numeric), CUTS(numlist min=2 max=2) [REPLACE]
    gettoken lo hi : cuts
    foreach v of local varlist {
        qui _pctile `v', percentiles(`lo' `hi')
        local a = r(r1)
        local b = r(r2)
        if missing(`a', `b') continue
        qui replace `v' = `a' if `v' < `a' & !missing(`v')
        qui replace `v' = `b' if `v' > `b' & !missing(`v')
    }
end

cap log close _all
log using "$OUT\master_log.smcl", replace name(master)

*------------------------------------------------------------------------------
* 0b. HELPER PROGRAMS
*------------------------------------------------------------------------------

* --- cellresid: residuals of y on x estimated WITHIN each cell (industry-year),
*     falling back to an industry-pooled regression with year FE for cells
*     that are too small (small cells give residuals mechanically close to 0)
cap program drop cellresid
program define cellresid
    syntax varlist(min=2 numeric), GENerate(name) CELL(varname) ///
        FALLback(varname) MINobs(integer) [FALLFE(string)]
    gettoken y xs : varlist
    tempvar touse n r
    mark `touse'
    markout `touse' `varlist' `cell' `fallback'
    qui bys `cell': egen `n' = total(`touse')
    qui gen double `generate' = .
    qui gen byte `generate'_src = .
    qui levelsof `cell' if `touse' & `n' >= `minobs', local(cells)
    foreach c of local cells {
        qui reg `y' `xs' if `touse' & `cell' == `c'
        qui predict double `r' if e(sample), resid
        qui replace `generate' = `r' if !missing(`r')
        qui replace `generate'_src = 1 if !missing(`r')
        drop `r'
    }
    qui levelsof `fallback' if `touse' & `n' < `minobs', local(groups)
    foreach g of local groups {
        cap qui reg `y' `xs' `fallfe' if `touse' & `fallback' == `g'
        if _rc continue
        qui predict double `r' if e(sample) & `n' < `minobs', resid
        qui replace `generate' = `r' if !missing(`r')
        qui replace `generate'_src = 2 if !missing(`r')
        drop `r'
    }
    qui count if `generate'_src == 1
    local n1 = r(N)
    qui count if `generate'_src == 2
    di as txt "cellresid `generate': `n1' obs from cell regressions, " r(N) " from fallback"
end

* --- pctrank: percentile rank in [0,1] within groups
cap program drop pctrank
program define pctrank
    syntax varname, GENerate(name) BY(varlist)
    tempvar r n
    qui bys `by': egen double `r' = rank(`varlist') if !missing(`varlist')
    qui bys `by': egen `n' = count(`varlist')
    qui gen double `generate' = cond(`n' > 1, (`r' - 1) / (`n' - 1), 0.5) ///
        if !missing(`varlist')
end

* --- lcw: linear combination of coefficients by NAME with numeric weights,
*     robust to factor-variable naming. Usage: lcw POS 1 POS_MA 0.25
cap program drop lcw
program define lcw, rclass
    tempname b V w e v
    matrix `b' = e(b)
    matrix `V' = e(V)
    matrix `w' = J(1, colsof(`b'), 0)
    while "`1'" != "" {
        local j = colnumb(`b', "`1'")
        if missing(`j') {
            di as err "lcw: coefficient `1' not found"
            exit 111
        }
        matrix `w'[1, `j'] = `2'
        macro shift 2
    }
    matrix `e' = `w' * `b''
    matrix `v' = `w' * `V' * `w''
    local df = e(df_r)
    if missing(`df') local df = e(N_clust) - 1
    if missing(`df') local df = e(N) - colsof(`b')
    return scalar est = `e'[1, 1]
    return scalar se  = sqrt(`v'[1, 1])
    return scalar df  = `df'
end

* --- addtest: one-sided p-value of a directional hypothesis, stored with
*     estadd so it prints under the table. dir(neg): H: comb<0 ; dir(pos): >0
*     Usage: addtest H1a, dir(neg) : POS 1
cap program drop addtest
program define addtest
    _on_colon_parse `0'
    local lhs `s(before)'
    local rhs `s(after)'
    local 0 `lhs'
    syntax name, DIR(string)
    lcw `rhs'
    local est = r(est)
    local se  = r(se)
    local t   = `est' / `se'
    if "`dir'" == "neg" local p = ttail(r(df), -`t')
    else                local p = ttail(r(df),  `t')
    qui estadd scalar b_`namelist' = `est'
    qui estadd scalar p_`namelist' = `p'
    di as res %-12s "`namelist'" as txt "  est = " %9.5f `est' "  se = " %9.5f `se' ///
        "  one-sided p (`dir') = " %6.4f `p'
end

* --- econsig: economic significance of a (combination of) coefficient(s):
*     effect of a 1-SD move in x (SD taken where x>0 for the CSD splines),
*     scaled by SD(DV) and by mean |investment residual|
cap program drop econsig
program define econsig
    syntax, MODEL(string) XVAR(varname) DV(varname) TERMS(string) [XCOND(string)]
    if "`xcond'" == "" local xcond "1"
    lcw `terms'
    local b  = r(est)
    local se = r(se)
    qui su `xvar' if e(sample) & (`xcond')
    local sdx = r(sd)
    qui su `dv' if e(sample)
    local sddv = r(sd)
    qui su INVEFF_ABS if e(sample)
    local mabs = r(mean)
    post econ ("`model'") ("`terms'") (`b') (`se') (`sdx') (`b'*`sdx') ///
        (`b'*`sdx'/`sddv') (100*`b'*`sdx'/`mabs')
end

* --- DEA (input-oriented; VRS or CRS) solved with Mata's LinearProgram().
*     Writes the efficiency score (0,1] for the observations flagged by tv.
*     Replaces the original -dea- call, whose r(dearslt) matrix was mapped
*     back to the data by row position (misalignment risk) and whose first
*     column is NOT the efficiency score.
cap mata mata drop dea_score()
mata:
void dea_score(string scalar xv, string scalar yv, string scalar tv,
               string scalar sv, real scalar vrs)
{
    real matrix X, Y, A
    real rowvector c, lb, ub, mx, my
    real colvector b, theta
    real scalar n, m, s, o, val
    class LinearProgram scalar q

    X = st_data(., tokens(xv), tv)
    Y = st_data(., tokens(yv), tv)
    n = rows(X); m = cols(X); s = cols(Y)
    // DEA is units-invariant: rescale columns to mean 1 for numerical stability
    mx = colsum(X) :/ n; mx = mx + (mx :== 0)
    my = colsum(Y) :/ n; my = my + (my :== 0)
    X  = X :/ mx
    Y  = Y :/ my
    theta = J(n, 1, .)
    c  = (1, J(1, n, 0))           // min theta ; decision vars = (theta, lambda_1..n)
    lb = J(1, n + 1, 0)
    ub = J(1, n + 1, .)
    for (o = 1; o <= n; o++) {
        q = LinearProgram()
        q.setMaxOrMin("min")
        q.setCoefficients(c)
        // sum_j lambda_j x_ij - theta x_io <= 0 ;  -sum_j lambda_j y_rj <= -y_ro
        A = ((-X[o, .]', X') \ (J(s, 1, 0), -Y'))
        b = (J(m, 1, 0) \ -Y[o, .]')
        q.setInequality(A, b)
        if (vrs) q.setEquality((0, J(1, n, 1)), 1)
        q.setBounds(lb, ub)
        val = q.optimize()
        if (q.errorcode() == 0) theta[o] = val
    }
    st_store(., sv, tv, theta)
}
end

*==============================================================================
* 1. IMPORT, IDENTIFIERS, PANEL
*==============================================================================
import excel "$DATA", firstrow clear

* Country identifier (single-country panels get CountryID = 1)
cap confirm string variable Country
if !_rc encode Country, gen(CountryID)
cap confirm variable CountryID
if _rc gen CountryID = 1

* FIX: the original -destring _all, force- silently turns Symbol (and any other
* string id) into missing. Destring numeric content only.
foreach v of varlist _all {
    if inlist("`v'", "Symbol", "Country") continue
    cap confirm string variable `v'
    if !_rc destring `v', replace ignore(", ") force
}

encode Symbol, gen(FirmID)
duplicates tag FirmID Year, gen(_dup)
qui count if _dup
if r(N) di as err "WARNING: " r(N) " duplicate firm-year rows; keeping first"
duplicates drop FirmID Year, force
drop _dup
xtset FirmID Year

* Hard validity filters (economically impossible rows only)
drop if missing(TA, Sales, IndID, Year) | TA <= 0 | Sales < 0 | TD < 0
if "$FIN_IND" != "" {
    foreach k of global FIN_IND {
        drop if IndID == `k'
    }
}

* CPI deflator from INF (country-year) - needed because nominal sizes/sales in
* high-inflation economies are not comparable across years (DEA, size, growth)
preserve
    keep CountryID Year INF
    collapse (mean) INF, by(CountryID Year)
    sort CountryID Year
    by CountryID: gen double CPI = exp(sum(ln(1 + INF / $INF_SCALE)))
    keep CountryID Year CPI
    tempfile cpi
    save `cpi'
restore
merge m:1 CountryID Year using `cpi', nogen keep(master match)
replace CPI = 1 if missing(CPI)

*==============================================================================
* 2. VARIABLE CONSTRUCTION (ratios first; winsorize ratios, never raw levels)
*==============================================================================
sort FirmID Year
foreach v in TA Sales COGS SGA PPE IA {
    gen double r_`v' = `v' / CPI
}

gen double TDA    = TD / TA                    // book leverage
gen double MLEV   = TD / (TD + MV)             // market leverage (robustness)
gen double SIZE   = ln(r_TA)
gen double MTB    = (MV + TD) / TA             // market-to-book of assets
gen double ROA    = OI / TA
gen double TANG   = PPE / TA
gen double COL    = (INV + PPE) / TA
gen double CFO_TA = CFO / TA
gen byte   LOSS   = OI < 0 if !missing(OI)
gen double LNAGE  = ln(1 + Age)
gen double SG     = r_Sales / L.r_Sales - 1    // REAL sales growth

gen double INV_CASH = -CFI / L.TA
gen double INV_ACC  = ((PPE + IA) - (L.PPE + L.IA)) / L.TA
cap confirm variable Capex
if !_rc gen double INV_CAPEX = Capex / L.TA
gen double INVEST = cond("$INVDEF" == "cash", INV_CASH, INV_ACC)

* Rolling volatility controls (>= 3 of the last 5 years)
foreach v in CFO_TA SG {
    forvalues k = 1/4 {
        gen double _`v'_L`k' = L`k'.`v'
    }
    egen double SD_`v' = rowsd(`v' _`v'_L1 _`v'_L2 _`v'_L3 _`v'_L4)
    egen _nn = rownonmiss(`v' _`v'_L1 _`v'_L2 _`v'_L3 _`v'_L4)
    replace SD_`v' = . if _nn < 3
    drop _`v'_L* _nn
}

local W "TDA MLEV MTB ROA TANG COL CFO_TA SG INV_CASH INV_ACC INVEST SD_CFO_TA SD_SG"
cap confirm variable INV_CAPEX
if !_rc local W "`W' INV_CAPEX"
winsor2 `W', replace cuts($WCUT)

* Leave-one-out industry-year mean leverage (own firm excluded)
bys IndID Year: egen double _s = total(TDA)
bys IndID Year: egen double _c = count(TDA)
gen double INDLEV = (_s - cond(missing(TDA), 0, TDA)) / (_c - !missing(TDA))
drop _s _c
sort FirmID Year

* Lagged determinants / controls (all predetermined w.r.t. year-t investment)
foreach v in ROA SIZE MTB TANG COL INDLEV CFO_TA LOSS SG INVEST {
    gen double L_`v' = L.`v'
}

egen INDYR = group(IndID Year)

*==============================================================================
* 3. CAPITAL STRUCTURE DEVIATION (CSD)
*    Target: TDA_it = b'X_{i,t-1} + industry FE + (country-)year FE
*    FIXES vs original: (i) FinExp/TA (IOB) removed - interest expense is
*    r x Debt, so it mechanically absorbs actual leverage and shrinks the
*    "deviation" to noise; (ii) determinants lagged (no simultaneity);
*    (iii) INF is a country-year constant: absorbed by Country x Year FE
*    (in a single country it is collinear with year FE); (iv) leave-one-out
*    INDLEV; (v) fitted value includes the fixed effects.
*==============================================================================
reghdfe TDA L_ROA L_SIZE L_MTB L_TANG L_COL L_INDLEV, ///
    absorb(T_IND=IndID T_CY=CountryID#Year) vce(cluster FirmID)
estimates store TARGET
predict double TDA_HAT, xbd
replace TDA_HAT = min(max(TDA_HAT, 0), 1) if !missing(TDA_HAT)
gen double CSD = TDA - TDA_HAT

* Robustness targets: (a) firm FE target -> transitory deviation;
*                     (b) market leverage target
reghdfe TDA L_ROA L_SIZE L_MTB L_TANG L_COL L_INDLEV, ///
    absorb(T2_F=FirmID T2_CY=CountryID#Year) vce(cluster FirmID)
estimates store TARGET_FE
predict double TDA_HAT_FE, xbd
gen double CSD_FE = TDA - min(max(TDA_HAT_FE, 0), 1) if !missing(TDA_HAT_FE)

reghdfe MLEV L_ROA L_SIZE L_MTB L_TANG L_COL L_INDLEV, ///
    absorb(T3_IND=IndID T3_CY=CountryID#Year) vce(cluster FirmID)
predict double MLEV_HAT, xbd
gen double CSD_MKT = MLEV - min(max(MLEV_HAT, 0), 1) if !missing(MLEV_HAT)
drop T_* T2_* T3_*

winsor2 CSD CSD_FE CSD_MKT, replace cuts($WCUT)

* Piecewise-linear (spline) decomposition: both parts are MAGNITUDES >= 0.
* NOTE max(x,0) returns 0 when x is missing in Stata - hence the -if-.
foreach s in "" "_FE" "_MKT" {
    gen double CSDPOS`s' = max( CSD`s', 0) if !missing(CSD`s')
    gen double CSDNEG`s' = max(-CSD`s', 0) if !missing(CSD`s')
}
gen byte OVERLEV = CSD > 0 if !missing(CSD)

* Deviation measured at the START of the investment year (t-1): removes the
* mechanical link "debt-financed investment in t raises leverage in t", which
* biases the contemporaneous CSD-investment relation AGAINST H1a/H1b.
sort FirmID Year
foreach s in "" "_FE" "_MKT" {
    gen double POS`s' = L.CSDPOS`s'
    gen double NEG`s' = L.CSDNEG`s'
}
gen double CSD_L    = L.CSD
gen byte OVERLEV_L  = L.OVERLEV

*==============================================================================
* 4. INVESTMENT (IN)EFFICIENCY
*    Biddle, Hilary & Verdi (2009): INVEST_t = a + b*SG_{t-1} + e, estimated
*    BY INDUSTRY-YEAR (original estimated ONE pooled regression, so the
*    residual contained industry and macro-year investment cycles = noise).
*    Robustness: Chen, Hope, Li & Wang (2011, emerging-market model with
*    asymmetric response to sales declines); Richardson (2006) WITHOUT
*    leverage (keeping leverage in the expectation model would partial out
*    the very CSD effect being tested).
*==============================================================================
cellresid INVEST L_SG, gen(RES_B) cell(INDYR) fallback(IndID) ///
    minobs($MIN_CELL) fallfe(i.Year)

gen byte   NEGSG  = L_SG < 0 if !missing(L_SG)
gen double NEGxSG = NEGSG * L_SG
cellresid INVEST NEGSG L_SG NEGxSG, gen(RES_C) cell(INDYR) fallback(IndID) ///
    minobs($MIN_CELL) fallfe(i.Year)

cellresid INVEST L_MTB L_SIZE L_CFO_TA L_INVEST LNAGE, gen(RES_R) ///
    cell(INDYR) fallback(IndID) minobs($MIN_CELL) fallfe(i.Year)

winsor2 RES_B RES_C RES_R, replace cuts($WCUT)

* Primary residual and its directional components
gen double INVRES     = RES_B
gen double INVEFF_ABS = abs(INVRES)
gen double UNDERINV   = -INVRES if INVRES < 0                       // magnitude
gen double OVERINV    =  INVRES if INVRES > 0 & !missing(INVRES)    // magnitude
gen byte   UNDER_D    = INVRES < 0 if !missing(INVRES)

* Biddle et al. (2009) categorical classification (mlogit robustness)
xtile _q = INVRES, nq(4)
gen byte INVCAT = 0 if inlist(_q, 2, 3)
replace  INVCAT = 1 if _q == 1          // under-investment
replace  INVCAT = 2 if _q == 4          // over-investment
drop _q
label define invcat 0 "Benchmark" 1 "Under-invest" 2 "Over-invest"
label values INVCAT invcat

*==============================================================================
* 5. CORPORATE LIFE CYCLE
*    Dickinson (2011) - ALL eight cash-flow sign patterns are classified (the
*    original coded only 3 stages and DROPPED introduction & shake-out
*    firm-years, i.e. typically 25-40% of the sample).
*    Measured at t-1: Dickinson uses the sign of CFI, and -CFI_t is investment,
*    so a contemporaneous stage would be mechanically related to the DV.
*==============================================================================
gen byte LC = .
replace LC = 1 if CFO <= 0 & CFI <= 0 & CFF >  0                        // Introduction
replace LC = 2 if CFO >  0 & CFI <= 0 & CFF >  0                        // Growth
replace LC = 3 if CFO >  0 & CFI <= 0 & CFF <= 0                        // Maturity
replace LC = 4 if (CFO <= 0 & CFI <= 0 & CFF <= 0) | (CFO > 0 & CFI > 0) // Shake-out
replace LC = 5 if CFO <= 0 & CFI >  0                                   // Decline
replace LC = . if missing(CFO, CFI, CFF)
label define lc 1 "Introduction" 2 "Growth" 3 "Maturity" 4 "Shake-out" 5 "Decline"
label values LC lc

* Robustness: Anthony & Ramesh (1992)-type composite (no cash-flow signs, so
* no mechanical overlap with investment): percentile ranks within
* industry-year of 3-year real sales growth, firm youth (and low payout if Div)
sort FirmID Year
gen double SG3 = (SG + L.SG + L2.SG) / 3
pctrank SG3,   gen(_pr_sg)  by(INDYR)
pctrank LNAGE, gen(_pr_age) by(INDYR)
gen double AR_SCORE = _pr_sg + (1 - _pr_age)
cap confirm variable Div
if !_rc {
    gen double PAYOUT = Div / OI if OI > 0
    pctrank PAYOUT, gen(_pr_pay) by(INDYR)
    replace AR_SCORE = AR_SCORE + (1 - _pr_pay)
}
pctrank AR_SCORE, gen(_pr_ar) by(Year)
gen byte LC_AR = cond(_pr_ar > 2/3, 2, cond(_pr_ar < 1/3, 5, 3)) if !missing(_pr_ar)
label values LC_AR lc
drop _pr_*

sort FirmID Year
gen byte LC_L    = L.LC
gen byte LC_AR_L = L.LC_AR
label values LC_L LC_AR_L lc

*==============================================================================
* 6. MANAGERIAL ABILITY  (Demerjian, Lev & McVay 2012)
*    Stage 1 - DEA, input-oriented, frontier BY INDUSTRY-YEAR (industry-pooled
*      if too few firms), output = real Sales; inputs = real COGS, SGA,
*      PPE_{t-1}, intangibles_{t-1}, in LEVELS. (Original: one frontier for all
*      industries & years, ratio inputs scaled by TA - violates DEA convexity -,
*      output orientation, and the first column of r(dearslt) is not theta.)
*    Stage 2 - Tobit (right-censored at 1, original censored at 0) on firm
*      characteristics that help/hinder efficiency regardless of the manager;
*      MA = unexplained part.
*==============================================================================
sort FirmID Year
gen double DEA_X1 = r_COGS
gen double DEA_X2 = r_SGA
gen double DEA_X3 = L.r_PPE
gen double DEA_X4 = L.r_IA
gen double DEA_Y  = r_Sales
gen byte dea_ok = !missing(DEA_X1, DEA_X2, DEA_X3, DEA_X4, DEA_Y) & DEA_Y > 0 & ///
    DEA_X1 >= 0 & DEA_X2 >= 0 & DEA_X3 >= 0 & DEA_X4 >= 0
bys INDYR: egen n_dea = total(dea_ok)
gen DEA_CELL = INDYR if n_dea >= $MIN_DEA
replace DEA_CELL = -IndID if n_dea < $MIN_DEA     // industry-pooled frontier (real values)

gen double FE_SCORE = .
qui levelsof DEA_CELL if dea_ok, local(dcells)
foreach c of local dcells {
    tempvar t
    qui gen byte `t' = dea_ok & DEA_CELL == `c'
    mata: dea_score("DEA_X1 DEA_X2 DEA_X3 DEA_X4", "DEA_Y", "`t'", "FE_SCORE", $DEA_VRS)
    drop `t'
}
replace FE_SCORE = 1 if FE_SCORE > 0.999999 & !missing(FE_SCORE)
di as txt _n "DEA diagnostics: share of efficient (theta = 1) firm-years"
gen byte _eff = FE_SCORE == 1 if !missing(FE_SCORE)
su _eff
drop _eff

bys INDYR: egen double _isales = total(r_Sales)
gen double MKTSH  = r_Sales / _isales
gen byte   POSFCF = (CFO + CFI) > 0 if !missing(CFO, CFI)
drop _isales
sort FirmID Year

tobit FE_SCORE SIZE MKTSH POSFCF LNAGE i.Year i.IndID, ul(1) vce(cluster FirmID)
estimates store MA_TOBIT
predict double FE_HAT, xb
gen double MA_RAW = FE_SCORE - FE_HAT

* MA used in the interactions: percentile rank within industry-year in [0,1]
* (Demerjian et al. publish decile ranks); centred at 0 so that the main
* effect of POS/NEG is evaluated at the median manager. Bounded -> immune to
* the fat tails that a z-score of a Tobit residual has.
pctrank MA_RAW, gen(MA_RANK) by(INDYR)
gen double MA_C = MA_RANK - 0.5
egen double MA_Z = std(MA_RAW)
sort FirmID Year
gen double MA    = L.MA_C                         // predetermined (t-1)
gen double MA_ZL = L.MA_Z
gen double MA_AV = (L.MA_C + L2.MA_C) / 2         // 2-yr average: less noise
gen byte   MA_HI = L.MA_RANK >= 2/3 if !missing(L.MA_RANK)  // top tercile

*==============================================================================
* 7. INTERACTION TERMS (built explicitly; transparent names for lincom)
*==============================================================================
gen byte INTRO = LC_L == 1 if !missing(LC_L)
gen byte GROW  = LC_L == 2 if !missing(LC_L)
gen byte MATU  = LC_L == 3 if !missing(LC_L)
gen byte SHAKE = LC_L == 4 if !missing(LC_L)
gen byte DECL  = LC_L == 5 if !missing(LC_L)
gen byte GD    = (GROW | DECL) if !missing(LC_L)
gen byte GMD   = inlist(LC_L, 2, 3, 5)            // stages named in H2/H3

cap program drop buildint
program define buildint
    // (re)build every interaction from the CURRENT POS NEG MA and stage dummies
    foreach v in POS_INTRO POS_GROW POS_SHAKE POS_DECL NEG_INTRO NEG_GROW ///
        NEG_SHAKE NEG_DECL POS_MA NEG_MA POS_GD NEG_GD MA_GD POS_MA_GD NEG_MA_GD {
        cap drop `v'
    }
    foreach s in INTRO GROW SHAKE DECL {
        qui gen double POS_`s' = POS * `s'
        qui gen double NEG_`s' = NEG * `s'
    }
    qui gen double POS_MA    = POS * MA
    qui gen double NEG_MA    = NEG * MA
    qui gen double POS_GD    = POS * GD
    qui gen double NEG_GD    = NEG * GD
    qui gen double MA_GD     = MA  * GD
    qui gen double POS_MA_GD = POS * MA * GD
    qui gen double NEG_MA_GD = NEG * MA * GD
end
buildint

label var POS        "CSD+ (over-leverage, t-1)"
label var NEG        "|CSD-| (under-leverage, t-1)"
label var MA         "Managerial ability (rank, centred, t-1)"
label var POS_GROW   "CSD+ x Growth"
label var POS_DECL   "CSD+ x Decline"
label var POS_INTRO  "CSD+ x Introduction"
label var POS_SHAKE  "CSD+ x Shake-out"
label var NEG_GROW   "|CSD-| x Growth"
label var NEG_DECL   "|CSD-| x Decline"
label var NEG_INTRO  "|CSD-| x Introduction"
label var NEG_SHAKE  "|CSD-| x Shake-out"
label var POS_MA     "CSD+ x MA"
label var NEG_MA     "|CSD-| x MA"
label var POS_GD     "CSD+ x GrowthDecline"
label var NEG_GD     "|CSD-| x GrowthDecline"
label var MA_GD      "MA x GrowthDecline"
label var POS_MA_GD  "CSD+ x MA x GrowthDecline"
label var NEG_MA_GD  "|CSD-| x MA x GrowthDecline"
label var INVRES     "Investment residual (signed)"
label var UNDERINV   "Under-investment (magnitude)"
label var OVERINV    "Over-investment (magnitude)"
label var INVEFF_ABS "|Investment residual|"

*==============================================================================
* 8. ESTIMATION SAMPLE (held constant across H1-H3 for comparability)
*    Controls: Biddle et al. (2009)-type determinants, all at t-1.
*    Age is kept only in specifications WITHOUT firm FE (with firm & year FE
*    it is perfectly collinear: Age = Year - founding year).
*==============================================================================
global CTRL "L_SIZE L_MTB L_ROA L_CFO_TA L_TANG L_LOSS LNAGE SD_CFO_TA SD_SG"
global FE1  "IndID#Year CountryID#Year"                // two-step models
global FE0  "IndID#Year CountryID#Year IndID#c.L_SG"   // one-step models

gen byte SAMPLE = !missing(INVEST, INVRES, POS, NEG, LC_L, MA, L_SG) & BV > 0
foreach c of global CTRL {
    replace SAMPLE = 0 if missing(`c')
}
tab SAMPLE
save "$OUT\analysis_panel.dta", replace

*==============================================================================
* 9. DIAGNOSTICS  (why results can be weak - read these BEFORE the tables)
*==============================================================================
di as res _n "D1. Target-leverage model fit and CSD properties"
estimates replay TARGET
xtsum CSD TDA if SAMPLE          // within vs between SD: firm FE keeps only "within"
corr CSD L.CSD if SAMPLE         // persistence; ~0.8+ => firm FE leaves little variation

di as res _n "D2. Mechanical contemporaneous link (why CSD must be lagged)"
gen double _dDebt = D.TD / L.TA
pwcorr CSD INVEST _dDebt CSD_L if SAMPLE, sig
drop _dDebt

di as res _n "D3. Investment-model cells: share estimated in cells vs fallback"
tab RES_B_src if SAMPLE

di as res _n "D4. Life-cycle distribution and stage x deviation-direction cells"
tab LC_L if SAMPLE
tab LC_L OVERLEV_L if SAMPLE, row
tab LC_L INVCAT if SAMPLE, row

di as res _n "D5. Managerial ability: discrimination & correlates"
su FE_SCORE MA_RAW MA_RANK if SAMPLE, d
pwcorr MA POS NEG L_SIZE L_ROA if SAMPLE, sig

di as res _n "D6. Multicollinearity among MAIN effects (VIF on interactions is"
di as res    "    uninformative - Brambor, Clark & Golder 2006)"
qui reg INVRES POS NEG MA GD $CTRL if SAMPLE
estat vif

*==============================================================================
* 10. DESCRIPTIVES
*==============================================================================
local DESC "INVEST INVRES INVEFF_ABS UNDERINV OVERINV TDA TDA_HAT CSD_L POS NEG MA FE_SCORE $CTRL"
estpost tabstat `DESC' if SAMPLE, statistics(n mean sd p25 p50 p75) columns(statistics)
esttab using "$OUT\T1_descriptives.rtf", replace cells("count mean(fmt(4)) sd(fmt(4)) p25(fmt(4)) p50(fmt(4)) p75(fmt(4))") ///
    nomtitle nonumber noobs label title("Table 1. Descriptive statistics (estimation sample)")
estpost tabstat INVRES POS NEG MA if SAMPLE, by(LC_L) statistics(n mean sd) columns(statistics)
esttab using "$OUT\T1b_by_stage.rtf", replace cells("count mean(fmt(4)) sd(fmt(4))") ///
    nomtitle nonumber noobs label title("Table 1b. Key variables by life-cycle stage (t-1)")
pwcorr INVRES INVEFF_ABS POS NEG MA $CTRL if SAMPLE, star(0.05)
estpost correlate INVRES INVEFF_ABS POS NEG MA $CTRL if SAMPLE, matrix listwise
esttab using "$OUT\T2_correlations.rtf", replace unstack not noobs compress b(%6.3f) ///
    star(* 0.05) title("Table 2. Pearson correlations")

* Economic-significance collector
cap postclose econ
postfile econ str24 model str90 terms double(b se sdx effect eff_sdDV eff_pctMeanAbs) ///
    using "$OUT\T7_economic_significance.dta", replace

*==============================================================================
* 11. H1 - DIRECT EFFECTS
*  (1) ONE-STEP (primary; Chen, Hribar & Melessa 2018): INVEST on POS NEG with
*      industry-specific sales-growth slopes + industry-year intercepts absorbed
*      -> avoids the attenuation bias of using a residual as the DV.
*      H1a: b(POS) < 0   H1b: b(NEG) > 0
*  (2) TWO-STEP signed residual: same predictions.
*  (3) Under-investment subsample (INVRES<0), DV = magnitude: H1a b(POS) > 0
*  (4) Over-investment subsample (INVRES>0), DV = magnitude: H1b b(NEG) > 0
*  (5) Multinomial logit on Biddle quartile classes (table T3b).
*  Asymmetry test (paper title): b(POS) + b(NEG) = 0 in (1)/(2).
*==============================================================================
eststo clear
eststo H1_1: reghdfe INVEST POS NEG $CTRL if SAMPLE, absorb($FE0) vce(cluster $CLUST)
addtest H1a, dir(neg) : POS 1
addtest H1b, dir(pos) : NEG 1
test POS + NEG = 0
estadd scalar p_asym = r(p)
econsig, model(H1 one-step) terms(POS 1) xvar(POS) xcond(POS>0) dv(INVEST)
econsig, model(H1 one-step) terms(NEG 1) xvar(NEG) xcond(NEG>0) dv(INVEST)

eststo H1_2: reghdfe INVRES POS NEG $CTRL if SAMPLE, absorb($FE1) vce(cluster $CLUST)
addtest H1a, dir(neg) : POS 1
addtest H1b, dir(pos) : NEG 1
test POS + NEG = 0
estadd scalar p_asym = r(p)
econsig, model(H1 two-step) terms(POS 1) xvar(POS) xcond(POS>0) dv(INVRES)
econsig, model(H1 two-step) terms(NEG 1) xvar(NEG) xcond(NEG>0) dv(INVRES)

eststo H1_3: reghdfe UNDERINV POS NEG $CTRL if SAMPLE & INVRES < 0, absorb($FE1) vce(cluster $CLUST)
addtest H1a, dir(pos) : POS 1
econsig, model(H1 under-subsample) terms(POS 1) xvar(POS) xcond(POS>0) dv(UNDERINV)

eststo H1_4: reghdfe OVERINV POS NEG $CTRL if SAMPLE & INVRES > 0, absorb($FE1) vce(cluster $CLUST)
addtest H1b, dir(pos) : NEG 1
econsig, model(H1 over-subsample) terms(NEG 1) xvar(NEG) xcond(NEG>0) dv(OVERINV)

esttab H1_* using "$OUT\T3_H1_direct.rtf", replace label b(%9.4f) se(%9.4f) ///
    star(* 0.10 ** 0.05 *** 0.01) keep(POS NEG) order(POS NEG) ///
    mtitles("INVEST (1-step)" "INVRES (2-step)" "UnderInv" "OverInv") ///
    stats(b_H1a p_H1a b_H1b p_H1b p_asym N r2_within N_clust, ///
        labels("H1a coef" "H1a one-sided p" "H1b coef" "H1b one-sided p" ///
        "p (|CSD+| effect = |CSD-| effect)" "Obs" "Within R2" "Firms")) ///
    title("Table 3. H1 - capital structure deviation and investment inefficiency") ///
    addnotes("All regressors at t-1. Controls, Industry x Year FE (and industry-specific sales-growth slopes in col. 1) included. SE clustered by firm.")
esttab H1_* using "$OUT\T3_H1_direct.csv", replace b(%9.5f) se(%9.5f) ///
    star(* 0.10 ** 0.05 *** 0.01) stats(b_H1a p_H1a b_H1b p_H1b p_asym N r2_within N_clust)

eststo H1_ML: mlogit INVCAT POS NEG $CTRL i.Year i.IndID if SAMPLE, base(0) vce(cluster $CLUST)
margins, dydx(POS NEG) predict(outcome(1)) post
eststo H1_ML_under
estimates restore H1_ML
margins, dydx(POS NEG) predict(outcome(2)) post
eststo H1_ML_over
esttab H1_ML_under H1_ML_over using "$OUT\T3b_H1_mlogit_AME.rtf", replace ///
    b(%9.4f) se(%9.4f) star(* 0.10 ** 0.05 *** 0.01) ///
    mtitles("Pr(Under-invest)" "Pr(Over-invest)") ///
    title("Table 3b. H1 - multinomial logit, average marginal effects") ///
    addnotes("H1a: dPr(Under)/dCSD+ > 0 ; H1b: dPr(Over)/d|CSD-| > 0.")

*==============================================================================
* 12. H2 - LIFE-CYCLE MODERATION  (Maturity = base stage)
*  Signed DV (cols 1-2): H2a  POS_GROW < 0 and POS_DECL < 0
*                        H2b  NEG > 0 (maturity slope) and NEG_GROW < 0,
*                             NEG_DECL < 0 (weaker outside maturity)
*  UnderInv (col 3):     H2a  POS_GROW > 0 and POS_DECL > 0
*  OverInv  (col 4):     H2b  NEG_GROW < 0 and NEG_DECL < 0
*==============================================================================
global H2X "POS NEG POS_INTRO POS_GROW POS_SHAKE POS_DECL NEG_INTRO NEG_GROW NEG_SHAKE NEG_DECL INTRO GROW SHAKE DECL"

eststo clear
eststo H2_1: reghdfe INVEST $H2X $CTRL if SAMPLE, absorb($FE0) vce(cluster $CLUST)
addtest H2a_G, dir(neg) : POS_GROW 1
addtest H2a_D, dir(neg) : POS_DECL 1
addtest H2b_G, dir(neg) : NEG_GROW 1
addtest H2b_D, dir(neg) : NEG_DECL 1
test POS_GROW POS_DECL
estadd scalar p_H2a_joint = r(p)
test NEG_GROW NEG_DECL
estadd scalar p_H2b_joint = r(p)

eststo H2_2: reghdfe INVRES $H2X $CTRL if SAMPLE, absorb($FE1) vce(cluster $CLUST)
addtest H2a_G, dir(neg) : POS_GROW 1
addtest H2a_D, dir(neg) : POS_DECL 1
addtest H2b_G, dir(neg) : NEG_GROW 1
addtest H2b_D, dir(neg) : NEG_DECL 1
test POS_GROW POS_DECL
estadd scalar p_H2a_joint = r(p)
test NEG_GROW NEG_DECL
estadd scalar p_H2b_joint = r(p)
econsig, model(H2 two-step) terms(POS 1 POS_GROW 1) xvar(POS) xcond(POS>0 & GROW==1) dv(INVRES)
econsig, model(H2 two-step) terms(POS 1 POS_DECL 1) xvar(POS) xcond(POS>0 & DECL==1) dv(INVRES)
econsig, model(H2 two-step) terms(POS 1)            xvar(POS) xcond(POS>0 & MATU==1) dv(INVRES)
econsig, model(H2 two-step) terms(NEG 1)            xvar(NEG) xcond(NEG>0 & MATU==1) dv(INVRES)

* Stage-specific slopes for Figure 1 (coefficient plot)
cap postclose stg
postfile stg str12 stage str4 side double(est lo hi) using "$OUT\_stage_slopes.dta", replace
foreach side in POS NEG {
    local i = 0
    foreach s in INTRO GROW MATU SHAKE DECL {
        local ++i
        if "`s'" == "MATU" lcw `side' 1
        else               lcw `side' 1 `side'_`s' 1
        local cv = invttail(r(df), 0.025)
        post stg ("`s'") ("`side'") (r(est)) (r(est) - `cv' * r(se)) (r(est) + `cv' * r(se))
    }
}
postclose stg

eststo H2_3: reghdfe UNDERINV $H2X $CTRL if SAMPLE & INVRES < 0, absorb($FE1) vce(cluster $CLUST)
addtest H2a_G, dir(pos) : POS_GROW 1
addtest H2a_D, dir(pos) : POS_DECL 1
test POS_GROW POS_DECL
estadd scalar p_H2a_joint = r(p)

eststo H2_4: reghdfe OVERINV $H2X $CTRL if SAMPLE & INVRES > 0, absorb($FE1) vce(cluster $CLUST)
addtest H2b_G, dir(neg) : NEG_GROW 1
addtest H2b_D, dir(neg) : NEG_DECL 1
test NEG_GROW NEG_DECL
estadd scalar p_H2b_joint = r(p)

esttab H2_* using "$OUT\T4_H2_lifecycle.rtf", replace label b(%9.4f) se(%9.4f) ///
    star(* 0.10 ** 0.05 *** 0.01) keep(POS NEG POS_GROW POS_DECL NEG_GROW NEG_DECL POS_INTRO POS_SHAKE NEG_INTRO NEG_SHAKE) ///
    order(POS POS_GROW POS_DECL NEG NEG_GROW NEG_DECL) ///
    mtitles("INVEST (1-step)" "INVRES (2-step)" "UnderInv" "OverInv") ///
    stats(p_H2a_G p_H2a_D p_H2a_joint p_H2b_G p_H2b_D p_H2b_joint N r2_within, ///
        labels("H2a growth one-sided p" "H2a decline one-sided p" "H2a joint Wald p" ///
        "H2b growth one-sided p" "H2b decline one-sided p" "H2b joint Wald p" "Obs" "Within R2")) ///
    title("Table 4. H2 - life-cycle moderation (base stage = Maturity)") ///
    addnotes("Stage = Dickinson (2011) at t-1; stage main effects and controls included.")
esttab H2_* using "$OUT\T4_H2_lifecycle.csv", replace b(%9.5f) se(%9.5f) ///
    star(* 0.10 ** 0.05 *** 0.01) stats(p_H2a_G p_H2a_D p_H2a_joint p_H2b_G p_H2b_D p_H2b_joint N r2_within)

*==============================================================================
* 13. H3 - MANAGERIAL ABILITY x CSD x LIFE CYCLE
*  Sample: growth, maturity, decline (the stages named in H3); GD = 1 for
*  growth/decline, 0 for maturity, so every lower-order term is a maturity
*  effect and every x GD term is the growth/decline increment.
*  Signed DV:  H3a  POS_MA > 0 (mitigation) and POS_MA_GD > 0 (stronger in G/D);
*                   slope of POS_MA in G/D = POS_MA + POS_MA_GD > 0
*              H3b  NEG_MA < 0 (limits over-investment in maturity) and
*                   NEG_MA_GD > 0 (mitigation weaker outside maturity)
*  UnderInv:   H3a  POS_MA < 0, POS_MA_GD < 0
*  OverInv:    H3b  NEG_MA < 0, NEG_MA_GD > 0
*==============================================================================
global H3X "POS NEG MA GD POS_MA NEG_MA POS_GD NEG_GD MA_GD POS_MA_GD NEG_MA_GD"

eststo clear
eststo H3_1: reghdfe INVEST $H3X $CTRL if SAMPLE & GMD, absorb($FE0) vce(cluster $CLUST)
addtest H3a_M,  dir(pos) : POS_MA 1
addtest H3a_GD, dir(pos) : POS_MA 1 POS_MA_GD 1
addtest H3a_dif, dir(pos) : POS_MA_GD 1
addtest H3b_M,  dir(neg) : NEG_MA 1
addtest H3b_dif, dir(pos) : NEG_MA_GD 1

eststo H3_2: reghdfe INVRES $H3X $CTRL if SAMPLE & GMD, absorb($FE1) vce(cluster $CLUST)
addtest H3a_M,  dir(pos) : POS_MA 1
addtest H3a_GD, dir(pos) : POS_MA 1 POS_MA_GD 1
addtest H3a_dif, dir(pos) : POS_MA_GD 1
addtest H3b_M,  dir(neg) : NEG_MA 1
addtest H3b_dif, dir(pos) : NEG_MA_GD 1
* economic meaning: slope of CSD+ for a p75 vs p25 manager in growth/decline
econsig, model(H3 G/D, MA=p25) terms(POS 1 POS_GD 1 POS_MA -0.25 POS_MA_GD -0.25) xvar(POS) xcond(POS>0 & GD==1) dv(INVRES)
econsig, model(H3 G/D, MA=p75) terms(POS 1 POS_GD 1 POS_MA 0.25 POS_MA_GD 0.25)  xvar(POS) xcond(POS>0 & GD==1) dv(INVRES)
econsig, model(H3 Mat, MA=p25) terms(NEG 1 NEG_MA -0.25) xvar(NEG) xcond(NEG>0 & MATU==1) dv(INVRES)
econsig, model(H3 Mat, MA=p75) terms(NEG 1 NEG_MA 0.25)  xvar(NEG) xcond(NEG>0 & MATU==1) dv(INVRES)
estimates store H3_PLOT

eststo H3_3: reghdfe UNDERINV $H3X $CTRL if SAMPLE & GMD & INVRES < 0, absorb($FE1) vce(cluster $CLUST)
addtest H3a_M,  dir(neg) : POS_MA 1
addtest H3a_GD, dir(neg) : POS_MA 1 POS_MA_GD 1
addtest H3a_dif, dir(neg) : POS_MA_GD 1

eststo H3_4: reghdfe OVERINV $H3X $CTRL if SAMPLE & GMD & INVRES > 0, absorb($FE1) vce(cluster $CLUST)
addtest H3b_M,  dir(neg) : NEG_MA 1
addtest H3b_dif, dir(pos) : NEG_MA_GD 1

esttab H3_* using "$OUT\T5_H3_ability.rtf", replace label b(%9.4f) se(%9.4f) ///
    star(* 0.10 ** 0.05 *** 0.01) keep($H3X) order(POS POS_MA POS_GD POS_MA_GD NEG NEG_MA NEG_GD NEG_MA_GD MA GD MA_GD) ///
    mtitles("INVEST (1-step)" "INVRES (2-step)" "UnderInv" "OverInv") ///
    stats(p_H3a_M p_H3a_GD p_H3a_dif p_H3b_M p_H3b_dif N r2_within, ///
        labels("H3a maturity p" "H3a growth/decline p" "H3a G/D vs Mat p" ///
        "H3b maturity p" "H3b Mat vs G/D p" "Obs" "Within R2")) ///
    title("Table 5. H3 - managerial ability, capital structure deviation and life cycle") ///
    addnotes("Sample: growth, maturity and decline firm-years. MA = industry-year percentile rank at t-1, centred at 0.5. One-sided p-values.")
esttab H3_* using "$OUT\T5_H3_ability.csv", replace b(%9.5f) se(%9.5f) ///
    star(* 0.10 ** 0.05 *** 0.01) stats(p_H3a_M p_H3a_GD p_H3a_dif p_H3b_M p_H3b_dif N r2_within)

* Stage-split version (transparent; reviewers like to see it)
eststo clear
foreach s in GROW MATU DECL {
    eststo S_`s': reghdfe INVRES POS NEG MA POS_MA NEG_MA $CTRL if SAMPLE & `s' == 1, ///
        absorb($FE1) vce(cluster $CLUST)
}
esttab S_* using "$OUT\T5b_H3_by_stage.rtf", replace label b(%9.4f) se(%9.4f) ///
    star(* 0.10 ** 0.05 *** 0.01) keep(POS NEG MA POS_MA NEG_MA) ///
    mtitles("Growth" "Maturity" "Decline") stats(N r2_within) ///
    title("Table 5b. H3 by life-cycle stage (DV = signed investment residual)")

*==============================================================================
* 14. FIGURES - interaction effects
*==============================================================================
graph set window fontface "Times New Roman"

* Figure 1: slope of CSD+ and |CSD-| on investment, by life-cycle stage (H2)
preserve
    use "$OUT\_stage_slopes.dta", clear
    gen x = .
    local i = 0
    foreach s in INTRO GROW MATU SHAKE DECL {
        local ++i
        replace x = `i' + cond(side == "POS", -0.12, 0.12) if stage == "`s'"
    }
    twoway (rcap lo hi x if side == "POS", lc(maroon)) (scatter est x if side == "POS", mc(maroon) m(O)) ///
           (rcap lo hi x if side == "NEG", lc(navy))   (scatter est x if side == "NEG", mc(navy) m(D)), ///
        yline(0, lp(dash) lc(gs8)) xlabel(1 "Intro" 2 "Growth" 3 "Maturity" 4 "Shake-out" 5 "Decline") ///
        xtitle("Life-cycle stage (t-1)") ytitle("dInvestment residual / dDeviation") ///
        legend(order(2 "Over-leverage CSD+ (H1a/H2a: < 0)" 4 "Under-leverage |CSD-| (H1b/H2b: > 0)") pos(6) rows(1)) ///
        title("Effect of capital structure deviation on investment by stage", size(medsmall)) ///
        note("95% CIs, SE clustered by firm. Model: Table 4, col. 2.") graphregion(color(white))
    graph export "$OUT\Fig1_H2_stage_slopes.png", replace width(2400)
restore

* Figure 2: marginal effect of CSD+ (and |CSD-|) as a function of MA,
*           growth/decline vs maturity (Brambor et al. 2006 style)
estimates restore H3_PLOT
cap postclose me
postfile me str4 side byte gd double(m est lo hi) using "$OUT\_me_ma.dta", replace
forvalues k = 0/20 {
    local m = -0.5 + `k' * 0.05
    foreach g in 0 1 {
        lcw POS 1 POS_GD `g' POS_MA `m' POS_MA_GD `=`m' * `g''
        local cv = invttail(r(df), 0.025)
        post me ("POS") (`g') (`m') (r(est)) (r(est) - `cv' * r(se)) (r(est) + `cv' * r(se))
        lcw NEG 1 NEG_GD `g' NEG_MA `m' NEG_MA_GD `=`m' * `g''
        local cv = invttail(r(df), 0.025)
        post me ("NEG") (`g') (`m') (r(est)) (r(est) - `cv' * r(se)) (r(est) + `cv' * r(se))
    }
}
postclose me
preserve
    use "$OUT\_me_ma.dta", clear
    replace m = m + 0.5
    foreach side in POS NEG {
        local ttl = cond("`side'" == "POS", "Over-leverage (CSD+): H3a", "Under-leverage (|CSD-|): H3b")
        twoway (rarea lo hi m if side == "`side'" & gd == 1, color(maroon%20) lw(none)) ///
               (line est m if side == "`side'" & gd == 1, lc(maroon) lw(medthick)) ///
               (rarea lo hi m if side == "`side'" & gd == 0, color(navy%20) lw(none)) ///
               (line est m if side == "`side'" & gd == 0, lc(navy) lw(medthick) lp(dash)), ///
            yline(0, lp(dot) lc(gs8)) xtitle("Managerial ability (industry-year percentile, t-1)") ///
            ytitle("Marginal effect on investment residual") title("`ttl'", size(medsmall)) ///
            legend(order(2 "Growth / Decline" 4 "Maturity") pos(6) rows(1)) ///
            graphregion(color(white)) name(g_`side', replace)
    }
    graph combine g_POS g_NEG, rows(1) graphregion(color(white)) ycommon ///
        title("Marginal effect of capital structure deviation conditional on managerial ability", size(medsmall)) ///
        note("Shaded: 95% CI. Model: Table 5, col. 2. H3a: the CSD+ line rises toward 0 with ability; H3b: the |CSD-| line falls toward 0.")
    graph export "$OUT\Fig2_H3_marginal_effects.png", replace width(2600)
restore

* Figure 3: predicted investment deviation along the FULL CSD axis
*           (negative = under-leveraged, positive = over-leveraged),
*           low (p10) vs high (p90) ability, by stage group. The asymmetric
*           "V/kinked" shape is the paper's headline picture.
estimates restore H3_PLOT
qui su CSD_L if SAMPLE & GMD, d
local lo = r(p5)
local hi = r(p95)
cap postclose pr
postfile pr byte gd double(m x est lo hi) using "$OUT\_pred_csd.dta", replace
forvalues k = 0/40 {
    local x = `lo' + (`hi' - `lo') * `k' / 40
    foreach g in 0 1 {
        foreach m in -0.4 0.4 {
            if `x' >= 0 lcw POS `x' POS_GD `=`x'*`g'' POS_MA `=`x'*`m'' POS_MA_GD `=`x'*`m'*`g''
            else        lcw NEG `=-`x'' NEG_GD `=-`x'*`g'' NEG_MA `=-`x'*`m'' NEG_MA_GD `=-`x'*`m'*`g''
            local cv = invttail(r(df), 0.025)
            post pr (`g') (`m') (`x') (r(est)) (r(est) - `cv' * r(se)) (r(est) + `cv' * r(se))
        }
    }
}
postclose pr
preserve
    use "$OUT\_pred_csd.dta", clear
    foreach g in 1 0 {
        local ttl = cond(`g' == 1, "Growth / Decline", "Maturity")
        twoway (rarea lo hi x if gd == `g' & m < 0, color(maroon%15) lw(none)) ///
               (line est x if gd == `g' & m < 0, lc(maroon) lw(medthick)) ///
               (rarea lo hi x if gd == `g' & m > 0, color(navy%15) lw(none)) ///
               (line est x if gd == `g' & m > 0, lc(navy) lw(medthick) lp(dash)), ///
            xline(0, lc(gs10)) yline(0, lp(dot) lc(gs8)) ///
            xtitle("Capital structure deviation at t-1 (actual - target)") ///
            ytitle("Predicted investment residual vs on-target firm") title("`ttl'", size(medsmall)) ///
            legend(order(2 "Low ability (p10)" 4 "High ability (p90)") pos(6) rows(1)) ///
            graphregion(color(white)) name(p_`g', replace)
    }
    graph combine p_1 p_0, rows(1) ycommon graphregion(color(white)) ///
        title("Investment response to capital structure deviation", size(medsmall)) ///
        note("Left of 0: under-leveraged (H1b/H2b/H3b). Right of 0: over-leveraged (H1a/H2a/H3a). 95% CIs.")
    graph export "$OUT\Fig3_H3_prediction_CSD_axis.png", replace width(2600)
restore

*==============================================================================
* 15. ROBUSTNESS & IDENTIFICATION
*  Key coefficients re-estimated under alternative measurement/specification.
*  Each block swaps the core variable(s), rebuilds the interactions, re-runs
*  H1 (signed two-step), H2 (signed) and H3 (signed), and restores the data.
*==============================================================================
cap program drop runrob
program define runrob
    // runrob TAG, dv(var) fe(absorb list) [vce(...) cond(condition) ctrl(list)]
    syntax name, DV(varname) FE(string) [VCE(string) COND(string) CTRL(string)]
    if "`vce'"  == "" local vce "cluster $CLUST"
    if "`cond'" == "" local cond "1"
    if "`ctrl'" == "" local ctrl "$CTRL"
    buildint
    local base "SAMPLE & !missing(`dv', POS, NEG, MA) & (`cond')"
    qui eststo R1_`namelist': reghdfe `dv' POS NEG `ctrl' if `base', absorb(`fe') vce(`vce')
    qui eststo R2_`namelist': reghdfe `dv' $H2X `ctrl' if `base', absorb(`fe') vce(`vce')
    qui eststo R3_`namelist': reghdfe `dv' $H3X `ctrl' if `base' & GMD, absorb(`fe') vce(`vce')
    di as res "Robustness `namelist' done"
end

eststo clear
runrob BASE, dv(INVRES) fe($FE1)

* (a) alternative deviation measures
preserve
    replace POS = POS_FE
    replace NEG = NEG_FE
    runrob CSDFE, dv(INVRES) fe($FE1)
restore
preserve
    replace POS = POS_MKT
    replace NEG = NEG_MKT
    runrob CSDMKT, dv(INVRES) fe($FE1)
restore
* (b) materiality band: drop firms within +/- 0.25 SD of target (sign noise)
qui su CSD_L if SAMPLE
local band = 0.25 * r(sd)
runrob BAND, dv(INVRES) fe($FE1) cond(abs(CSD_L) >= `band')

* (c) alternative investment-expectation models
runrob CHEN, dv(RES_C) fe($FE1)
runrob RICH, dv(RES_R) fe($FE1)

* (d) accrual-based investment (re-estimate first stage)
preserve
    cellresid INV_ACC L_SG, gen(RES_ACC) cell(INDYR) fallback(IndID) minobs($MIN_CELL) fallfe(i.Year)
    winsor2 RES_ACC, replace cuts($WCUT)
    runrob ACCR, dv(RES_ACC) fe($FE1)
restore

* (e) alternative managerial-ability measures
preserve
    replace MA = MA_ZL                  // z-score (coefficients per 1 SD of MA)
    runrob MAZ, dv(INVRES) fe($FE1)
restore
preserve
    replace MA = MA_AV
    runrob MAAV, dv(INVRES) fe($FE1)
restore
preserve
    replace MA = MA_HI - 0.5 if !missing(MA_HI)
    runrob MAHI, dv(INVRES) fe($FE1)
restore

* (f) alternative life-cycle classification (Anthony-Ramesh-type composite)
preserve
    replace INTRO = 0 if !missing(LC_AR_L)
    replace SHAKE = 0 if !missing(LC_AR_L)
    replace GROW  = LC_AR_L == 2 if !missing(LC_AR_L)
    replace MATU  = LC_AR_L == 3 if !missing(LC_AR_L)
    replace DECL  = LC_AR_L == 5 if !missing(LC_AR_L)
    replace GD    = (GROW | DECL) if !missing(LC_AR_L)
    replace GMD   = !missing(LC_AR_L)
    runrob LCAR, dv(INVRES) fe($FE1) cond(!missing(LC_AR_L))
restore

* (g) within-firm identification: firm FE + year FE (Age dropped: collinear)
runrob FIRMFE, dv(INVRES) fe(FirmID IndID#Year) ///
    ctrl(L_SIZE L_MTB L_ROA L_CFO_TA L_TANG L_LOSS SD_CFO_TA SD_SG)

* (h) two-way clustering (firm and year)
runrob CL2, dv(INVRES) fe($FE1) vce(cluster FirmID Year)

* (i) Mundlak / correlated random effects: firm means of POS and NEG
bys FirmID: egen double POS_bar = mean(cond(SAMPLE, POS, .))
bys FirmID: egen double NEG_bar = mean(cond(SAMPLE, NEG, .))
sort FirmID Year
runrob MUND, dv(INVRES) fe($FE1) ctrl($CTRL POS_bar NEG_bar)

foreach h in 1 2 3 {
    local keep = cond(`h' == 1, "POS NEG", cond(`h' == 2, "POS_GROW POS_DECL NEG_GROW NEG_DECL", ///
        "POS_MA POS_MA_GD NEG_MA NEG_MA_GD"))
    esttab R`h'_* using "$OUT\T6_robustness_H`h'.rtf", replace b(%9.4f) se(%9.4f) ///
        star(* 0.10 ** 0.05 *** 0.01) keep(`keep') stats(N r2_within) compress ///
        title("Table 6.`h'. Robustness - key H`h' coefficients") ///
        addnotes("BASE baseline; CSDFE firm-FE target; CSDMKT market leverage; BAND |CSD|>=0.25SD; CHEN Chen et al. (2011) model; RICH Richardson (2006) w/o leverage; ACCR accrual investment; MAZ/MAAV/MAHI alternative MA; LCAR composite life cycle; FIRMFE firm FE; CL2 two-way clustering; MUND Mundlak.")
    esttab R`h'_* using "$OUT\T6_robustness_H`h'.csv", replace b(%9.5f) se(%9.5f) ///
        star(* 0.10 ** 0.05 *** 0.01) keep(`keep') stats(N r2_within)
}

* (j) Dynamic panel: system GMM (Blundell-Bond), POS/NEG predetermined
*     Report AR(2) p > 0.10 and Hansen p in (0.10, 0.90); instruments < groups
qui tab Year if SAMPLE, gen(YD_)
drop YD_1
cap noi xtabond2 INVRES L.INVRES POS NEG $CTRL YD_* if SAMPLE, ///
    gmm(L.INVRES, lag(1 2) collapse) gmm(POS NEG, lag(1 2) collapse) ///
    iv(L_SIZE L_MTB L_ROA L_CFO_TA L_TANG L_LOSS LNAGE SD_CFO_TA SD_SG YD_*) twostep robust small
if !_rc {
    di as res "AR(2) p = " e(ar2p) "   Hansen p = " e(hansenp) "   #instr = " e(j) "   #groups = " e(N_g)
    eststo GMM
    estadd scalar ar1p = e(ar1p)
    estadd scalar ar2p = e(ar2p)
    estadd scalar hansenp = e(hansenp)
    estadd scalar ninst = e(j)
    esttab GMM using "$OUT\T6g_systemGMM.rtf", replace b(%9.4f) se(%9.4f) ///
        star(* 0.10 ** 0.05 *** 0.01) keep(L.INVRES POS NEG) ///
        stats(N N_g ninst ar1p ar2p hansenp) title("Table 6g. System GMM")
}

* (k) Few clusters? Wild-cluster bootstrap p-values for the H1 coefficients
qui reghdfe INVRES POS NEG $CTRL if SAMPLE, absorb($FE1) vce(cluster $CLUST)
if e(N_clust) < 50 {
    cap noi boottest POS, reps(9999) weight(webb) nograph
    cap noi boottest NEG, reps(9999) weight(webb) nograph
}

* (l) Coefficient stability / omitted variables (Oster 2019), if installed
cap which psacalc
if !_rc {
    qui areg INVRES POS NEG $CTRL if SAMPLE, absorb(INDYR) vce(cluster $CLUST)
    local rmax = min(1, 1.3 * e(r2))
    cap noi psacalc delta POS, rmax(`rmax')
    cap noi psacalc delta NEG, rmax(`rmax')
}

* (m) Country/industry subsamples (multi-country panels): leave-one-out
qui levelsof CountryID if SAMPLE, local(ctys)
if `: word count `ctys'' > 1 {
    foreach c of local ctys {
        di as res "Excluding country `c'"
        reghdfe INVRES POS NEG $CTRL if SAMPLE & CountryID != `c', absorb($FE1) vce(cluster $CLUST)
    }
}

*==============================================================================
* 16. LEGACY SPECIFICATION (for the response letter: shows what changed)
*     Original: contemporaneous |CSD| on |residual| with firm FE.
*==============================================================================
gen double CSD_ABS_t = abs(CSD)
reghdfe INVEFF_ABS CSD_ABS_t MA $CTRL if SAMPLE, absorb(FirmID Year) vce(cluster $CLUST)
di as txt "Compare with Table 3: magnitude-on-magnitude pools two opposite-signed"
di as txt "mechanisms (H1a & H1b) into one coefficient and firm FE removes most CSD variation."

*==============================================================================
* 17. ECONOMIC SIGNIFICANCE TABLE
*==============================================================================
postclose econ
preserve
    use "$OUT\T7_economic_significance.dta", clear
    format b se sdx effect eff_sdDV %9.4f
    format eff_pctMeanAbs %7.1f
    list, noobs sep(0) abbrev(20)
    export delimited using "$OUT\T7_economic_significance.csv", replace
restore

log close master
* ============================== END =========================================
