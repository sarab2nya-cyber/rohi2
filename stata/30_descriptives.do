*==============================================================================
* 30_descriptives.do  -  Section 3.10: descriptive statistics, correlations,
*   life-cycle tables, first-stage results, multicollinearity and the
*   classical-assumption / specification tests of the static benchmark.
*   Output: sheets of $OUT/Tables.xlsx and .rtf tables.
*==============================================================================
use "$OUT/analysis_panel.dta", clear
xtset FirmID Year

local DV   "InvEff Invest SalesGrowth TDA TDAhat CSDev CSDX CSDP CSDN FE MA $XCTRL IOB COL INDLEV INF Age"
local CV   "InvEff CSDP CSDN MA $XCTRL GROW MAT DEC"

*------------------------------------------------------------------------------
* OA1 Sample by year and industry (estimation sample)
*------------------------------------------------------------------------------
di as res _n "OA1. Estimation sample by year and by industry"
tab Year if EST, matcell(FY) matrow(RY)
tab IndID if EST, matcell(FI) matrow(RI)
putexcel set "$OUT/Tables.xlsx", sheet("OA1_sample") modify
putexcel A1 = "Year" B1 = "Firm-years" D1 = "IndID" E1 = "Firm-years"
putexcel A2 = matrix(RY) B2 = matrix(FY) D2 = matrix(RI) E2 = matrix(FI)

*------------------------------------------------------------------------------
* T1 Descriptive statistics (estimation sample)
*------------------------------------------------------------------------------
di as res _n "T1. Descriptive statistics (estimation sample)"
tabstat `DV' if EST, stat(n mean sd min p25 p50 p75 max skewness kurtosis) ///
    columns(statistics) format(%10.4f) save
matrix T1 = r(StatTotal)'
putexcel set "$OUT/Tables.xlsx", sheet("T1_descriptives") modify
putexcel A1 = matrix(T1), names nformat("0.0000")

* direction of deviations: over/under-investment and over/under-leverage
di as res _n "T1b. Direction of investment and leverage deviations"
gen byte OVERINV = InvEff > 0 if !missing(InvEff)
tab OVERINV OVERLEV if EST, cell row col matcell(DIR)
ttest InvEff if EST, by(OVERLEV)
local mu1 = r(mu_1)
local mu2 = r(mu_2)
local tp  = r(p)
putexcel set "$OUT/Tables.xlsx", sheet("T1b_directions") modify
putexcel A1 = "Rows: over-investment (0/1); columns: over-leverage (0/1)"
putexcel A2 = matrix(DIR)
putexcel A5 = "Mean InvEff, under-leveraged"  B5 = (`mu1')
putexcel A6 = "Mean InvEff, over-leveraged"   B6 = (`mu2')
putexcel A7 = "t-test p (two-sided)"           B7 = (`tp')

*------------------------------------------------------------------------------
* T2 Life cycle: Dickinson five stages, consolidated stages, transitions,
*    stage x deviation-direction cells
*------------------------------------------------------------------------------
di as res _n "T2. Dickinson (2011) original stages, `=$Y0 + 1'-$YN"
tab LC5 if Year >= $Y0 + 1, matcell(F5)
di as res _n "T2. Consolidated stages (t-1) in the estimation sample"
tab STAGE_L if EST, matcell(F3)
di as res _n "T2b. Stage transition matrix (row = stage at t-1, column = stage at t)"
tab STAGE_L STAGE if Year >= $Y0 + 2, row matcell(TR)
di as res _n "T2c. Stage (t-1) x leverage direction: cells identifying the interactions"
tab STAGE_L OVERLEV if EST, matcell(SC)
putexcel set "$OUT/Tables.xlsx", sheet("T2_lifecycle") modify
putexcel A1 = "Dickinson stage" B1 = "Firm-years (`=$Y0 + 1'-$YN)"
putexcel A2 = "Introduction" A3 = "Growth" A4 = "Mature" A5 = "Shake-out" A6 = "Decline"
putexcel B2 = matrix(F5)
putexcel D1 = "Consolidated stage (t-1)" E1 = "Firm-years (estimation sample)"
putexcel D2 = "Growth" D3 = "Maturity" D4 = "Decline"
putexcel E2 = matrix(F3)
putexcel A9 = "Transitions (rows t-1: G, M, D; columns t: G, M, D)"
putexcel A10 = matrix(TR)
putexcel E9 = "Stage (t-1) x leverage direction (columns: under, over)"
putexcel E10 = matrix(SC)

*------------------------------------------------------------------------------
* T3 Correlations: Pearson below the diagonal, Spearman above (listwise)
*------------------------------------------------------------------------------
di as res _n "T3. Correlation matrix: Pearson (lower) / Spearman (upper)"
pwcorr `CV' if EST, star(0.05)
qui corr `CV' if EST
matrix P = r(C)
local n = r(N)
qui spearman `CV' if EST, stats(rho)
matrix S = r(Rho)
local k : word count `CV'
putexcel set "$OUT/Tables.xlsx", sheet("T3_correlations") modify
putexcel A1 = "Pearson below / Spearman above the diagonal; * p<0.10, ** p<0.05, *** p<0.01; N = `n'"
forvalues i = 1/`k' {
    local vi : word `i' of `CV'
    local r = `i' + 2
    putexcel A`r' = "`vi'"
    local col = char(65 + `i')
    putexcel `col'2 = "`vi'"
    forvalues j = 1/`k' {
        local col = char(65 + `j')
        if `i' == `j' {
            putexcel `col'`r' = "1"
            continue
        }
        local rho = cond(`i' > `j', P[`i', `j'], S[`i', `j'])
        local tt  = `rho' * sqrt((`n' - 2) / max(1e-12, 1 - `rho'^2))
        local pp  = 2 * ttail(`n' - 2, abs(`tt'))
        local st  = cond(`pp' < 0.01, "***", cond(`pp' < 0.05, "**", cond(`pp' < 0.10, "*", "")))
        putexcel `col'`r' = "`: di %6.3f `rho''`st'"
    }
}

*------------------------------------------------------------------------------
* OA2 First-stage models: target leverage (Eq. 2), Tobit (Eq. 5),
*     expectation model cells (Eq. 1), DEA scores
*------------------------------------------------------------------------------
di as res _n "OA2. First-stage estimates"
esttab TGT_main TOB_main using "$OUT/OA2_first_stage.rtf", replace ///
    b(%9.4f) se(%9.4f) star(* 0.10 ** 0.05 *** 0.01) drop(*.IndID *.Year) ///
    mtitles("Target leverage, Eq. (2)" "Tobit, Eq. (5)") stats(N r2 r2_p, ///
    labels("Observations" "R-squared" "Pseudo R-squared")) ///
    title("Table OA2. First-stage models") addnotes("Industry dummies (and year dummies in the Tobit) included, not reported. SE clustered by firm.")

preserve
    use "$OUT/log_expectation_model_cells.dta", clear
    di as res _n "Expectation model, Eq. (1): cell regressions (source 1) and industry fallbacks (2)"
    tabstat N b_salesgrowth r2, by(source) stat(n mean p50 sd min max) format(%9.3f)
    export excel using "$OUT/Tables.xlsx", sheet("OA2_eq1_cells", replace) firstrow(variables)
restore
di as res _n "Share of firm-years whose InvEff comes from cell regressions (1) vs fallback (2)"
tab InvEff_src if EST

*------------------------------------------------------------------------------
* OA2b Data envelopment analysis (stage 1 of managerial ability)
*------------------------------------------------------------------------------
di as res _n "OA2b. DEA (input-oriented, VRS): frontiers, efficiency scores, share efficient"
gen byte FE1     = FE == 1 if !missing(FE)
gen byte DEA_own = DEA_CELL > 0 if !missing(FE)
egen byte _tagcell = tag(DEA_CELL) if !missing(FE)
tabstat FE FE1 DEA_own if Year >= $Y0 + 1, by(Year) stat(mean n) format(%6.3f)
qui count if _tagcell == 1 & DEA_CELL > 0
local nf_own = r(N)
qui count if _tagcell == 1 & DEA_CELL < 0
local nf_pool = r(N)
qui su FE if Year >= $Y0 + 1
local fe_mean = r(mean)
local fe_n = r(N)
qui su FE1 if Year >= $Y0 + 1
local fe_eff = r(mean)
qui su DEA_own if Year >= $Y0 + 1
local fe_own = r(mean)
di as txt "  frontiers estimated: `nf_own' industry-year, `nf_pool' industry-pooled"
putexcel set "$OUT/Tables.xlsx", sheet("OA2b_DEA") modify
putexcel A1 = "Data envelopment analysis (Demerjian et al. 2012, stage 1)"
putexcel A2 = "Firm-years with an efficiency score" B2 = (`fe_n')
putexcel A3 = "Mean efficiency score (FE)"          B3 = (`fe_mean')
putexcel A4 = "Share on the frontier (FE = 1)"      B4 = (`fe_eff')
putexcel A5 = "Industry-year frontiers"             B5 = (`nf_own')
putexcel A6 = "Industry-pooled frontiers (small cells)" B6 = (`nf_pool')
putexcel A7 = "Share of firm-years scored on an industry-year frontier" B7 = (`fe_own')
drop FE1 DEA_own _tagcell

*------------------------------------------------------------------------------
* Figures of the descriptive analysis (saved before any model is estimated)
*------------------------------------------------------------------------------
graph set window fontface "Times New Roman"
histogram InvEff if EST, bin(50) xline(0, lc(maroon)) graphregion(color(white)) ///
    title("Distribution of investment inefficiency (InvEff)", size(medsmall)) ///
    note("Right of 0: over-investment; left of 0: under-investment.")
graph export "$OUT/Fig0a_InvEff_distribution.png", replace width(2000)
histogram CSDev if EST, bin(50) xline(0, lc(maroon)) graphregion(color(white)) ///
    title("Distribution of capital structure deviation (CSDev)", size(medsmall)) ///
    note("Right of 0: over-leveraged; left of 0: under-leveraged.")
graph export "$OUT/Fig0b_CSDev_distribution.png", replace width(2000)
histogram FE if Year >= $Y0 + 1, bin(40) graphregion(color(white)) ///
    title("DEA efficiency scores (stage 1 of managerial ability)", size(medsmall))
graph export "$OUT/Fig0c_DEA_scores.png", replace width(2000)
histogram MA if EST, bin(50) graphregion(color(white)) ///
    title("Managerial ability (Tobit residual, centered)", size(medsmall))
graph export "$OUT/Fig0d_MA_distribution.png", replace width(2000)
graph bar (mean) InvEff if EST, over(OVERLEV, relabel(1 "Under-leveraged" 2 "Over-leveraged")) ///
    over(STAGE_L) asyvars blabel(bar, format(%9.3f)) graphregion(color(white)) ///
    ytitle("Mean InvEff") title("Mean investment inefficiency by life-cycle stage (t-1) and leverage direction", size(medsmall)) ///
    legend(pos(6) rows(1))
graph export "$OUT/Fig0e_InvEff_by_stage_direction.png", replace width(2200)
twoway (lpoly InvEff CSDev if EST & CSDev < 0, lc(navy) lw(medthick)) ///
       (lpoly InvEff CSDev if EST & CSDev > 0, lc(maroon) lw(medthick)), ///
    xline(0, lc(gs10)) yline(0, lp(dot) lc(gs8)) graphregion(color(white)) ///
    xtitle("Capital structure deviation (CSDev)") ytitle("InvEff (local polynomial)") ///
    legend(order(1 "Under-leveraged side" 2 "Over-leveraged side") pos(6) rows(1)) ///
    title("Investment inefficiency across capital structure deviation", size(medsmall))
graph export "$OUT/Fig0f_InvEff_vs_CSDev.png", replace width(2200)

*------------------------------------------------------------------------------
* T4 Multicollinearity: VIF of the static main-effects model (Section 3.10.1)
*------------------------------------------------------------------------------
di as res _n "T4a. Variance inflation factors (static main-effects model)"
qui reg InvEff CSDP CSDN MA GROW DEC $XCTRL i.Year i.IndID if EST
estat vif
local names "CSDP CSDN MA GROW DEC $XCTRL"
local nv : word count `names'
matrix VIF = J(`nv', 1, .)
matrix rownames VIF = `names'
local i = 0
while "`r(name_`=`i'+1')'" != "" {
    local ++i
    local nm "`r(name_`i')'"
    local pos : list posof "`nm'" in names
    if `pos' > 0 matrix VIF[`pos', 1] = r(vif_`i')
}
putexcel set "$OUT/Tables.xlsx", sheet("T4_VIF") modify
putexcel A1 = matrix(VIF), names nformat("0.00")
putexcel A12 = "Year and industry dummies included in the model; their VIFs are not reported."

*------------------------------------------------------------------------------
* T4b Classical assumptions and specification tests: static benchmark of Eq. (6)
*     (GMM itself does not need normality or homoskedasticity; these tests
*      document the data and justify the robust/GMM approach - Section 3.10)
*------------------------------------------------------------------------------
di as res _n "T4b. Static benchmark of Eq. (6): specification and assumption tests"
qui xtreg InvEff CSDP CSDN $XCTRL i.Year if EST, fe
est store FE6
local Ff  = e(F_f)
local Ffp = Ftail(e(df_a), e(df_r), e(F_f))
predict double e_fe if e(sample), e
qui xtreg InvEff CSDP CSDN $XCTRL i.Year if EST, re
est store RE6
cap noi hausman FE6 RE6, sigmamore
local Hc = cond(_rc, ., r(chi2))
local Hp = cond(_rc, ., r(p))

modwald e_fe
local MW = r(W)
local MWp = r(p)

wooldtest InvEff CSDP CSDN $XCTRL if EST
local WD = r(F)
local WDp = r(p)

tempvar tu
gen byte `tu' = !missing(e_fe)
mata: pesaran_cd("e_fe", "FirmID", "Year", "`tu'")
local CD  = scalar(CD_stat)
local CDp = scalar(CD_p)

sktest e_fe
local SKp = r(P_chi2)

foreach v in InvEff CSDev {
    cap noi xtunitroot fisher `v' if Year >= $Y0 + 2, dfuller lags(0) demean
    local UR_`v'  = cond(_rc, ., r(P))
    local URp_`v' = cond(_rc, ., r(p_P))
}

putexcel set "$OUT/Tables.xlsx", sheet("T4b_assumptions") modify
putexcel A1 = "Test" B1 = "Statistic" C1 = "p-value" D1 = "H0" E1 = "Implication if H0 is rejected" F1 = "Decision (5%)"
putexcel A2 = "F test (pooled OLS vs fixed effects)" B2 = (`Ff') C2 = (`Ffp') ///
    D2 = "All firm effects = 0" E2 = "Rejection: firm effects matter"
putexcel A3 = "Hausman (random vs fixed effects)" B3 = (`Hc') C3 = (`Hp') ///
    D3 = "RE consistent" E3 = "Rejection: use fixed effects"
putexcel A4 = "Modified Wald (groupwise heteroskedasticity)" B4 = (`MW') C4 = (`MWp') ///
    D4 = "Homoskedastic errors" E4 = "Rejection: robust / two-step GMM covariance"
putexcel A5 = "Wooldridge (serial correlation)" B5 = (`WD') C5 = (`WDp') ///
    D5 = "No AR(1) in errors" E5 = "Rejection: cluster by firm; dynamic model"
putexcel A6 = "Pesaran CD (cross-sectional dependence)" B6 = (`CD') C6 = (`CDp') ///
    D6 = "Cross-sectional independence" E6 = "Rejection: keep year dummies"
putexcel A7 = "Skewness-kurtosis (normality of residuals)" B7 = "" C7 = (`SKp') ///
    D7 = "Normal errors" E7 = "Not required by GMM; large-N inference"
putexcel A8 = "Fisher-ADF unit root, InvEff (inverse chi2)" B8 = (`UR_InvEff') C8 = (`URp_InvEff') ///
    D8 = "All panels have a unit root" E8 = "Rejection: stationary"
putexcel A9 = "Fisher-ADF unit root, CSDev (inverse chi2)" B9 = (`UR_CSDev') C9 = (`URp_CSDev') ///
    D9 = "All panels have a unit root" E9 = "Rejection: stationary"
local r = 1
foreach pv in Ffp Hp MWp WDp CDp SKp URp_InvEff URp_CSDev {
    local ++r
    local dec = cond(missing(``pv''), "", cond(``pv'' < 0.05, "Reject H0", "Do not reject H0"))
    putexcel F`r' = "`dec'"
}
drop e_fe OVERINV
