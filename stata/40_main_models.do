*==============================================================================
* 40_main_models.do  -  Sections 3.7-3.9
*   Eqs. (6)-(12): two-step System GMM, one model per hypothesis
*   hypothesis tests (one-sided), Wald tests, specification tests,
*   Bond (2002) bounds, static FE benchmarks, marginal effects with
*   Johnson-Neyman intervals, simple slopes and economic magnitude,
*   binned estimator, within-stage estimates, reverse causality Eq. (13)
*==============================================================================
use "$OUT/analysis_panel.dta", clear
xtset FirmID Year
eststo clear

*------------------------------------------------------------------------------
* A. GMM estimation of Eqs. (6)-(12)
*------------------------------------------------------------------------------
foreach m of global MODELS {
    di as res _n "{hline 78}" _n "Eq. (`m'): two-step System GMM" _n "{hline 78}"
    rungmm, dep(InvEff) endog(${E`m'}) pred(${P`m'})
    gmmstats, name(G`m')

    * Bond (2002) bounds: pooled OLS (upward-biased) and within (downward-biased)
    qui reg InvEff L.InvEff ${E`m'} ${P`m'} $XCTRL yd_* ind_* if EST, vce(cluster FirmID)
    local gols = _b[L.InvEff]
    qui reghdfe InvEff L.InvEff ${E`m'} ${P`m'} $XCTRL if EST, absorb(FirmID Year) vce(cluster FirmID)
    local gfe = _b[L.InvEff]
    qui est restore G`m'
    local ggmm = _b[L.InvEff]
    qui estadd scalar g_ols = `gols'
    qui estadd scalar g_fe  = `gfe'
    qui estadd scalar bond_ok = (`ggmm' > min(`gols', `gfe') & `ggmm' < max(`gols', `gfe'))
    di as txt "  Bond bounds: within = " %7.4f `gfe' "  GMM = " %7.4f `ggmm' "  pooled OLS = " %7.4f `gols' ///
        cond(`ggmm' > min(`gols', `gfe') & `ggmm' < max(`gols', `gfe'), "  (inside)", "  (OUTSIDE)")
    est store G`m'

    * static two-way fixed-effects benchmark (Online Appendix OA4)
    qui eststo S`m': reghdfe InvEff ${E`m'} ${P`m'} $XCTRL if EST, absorb(FirmID Year) vce(cluster FirmID)
}

*------------------------------------------------------------------------------
* B. Hypothesis tests (one-sided, predicted sign) and Wald tests
*------------------------------------------------------------------------------
di as res _n "Hypothesis tests"
qui est restore G6
addtest H1a, dir(neg) : CSDP 1
addtest H1b, dir(pos) : CSDN 1
test CSDP + CSDN = 0
qui estadd scalar p_asym = r(p)
est store G6

qui est restore G7
addtest H2aG, dir(neg) : CSDP_GROW 1
addtest H2aD, dir(neg) : CSDP_DEC 1
addtest slopeG, dir(neg) : CSDP 1 CSDP_GROW 1
addtest slopeD, dir(neg) : CSDP 1 CSDP_DEC 1
test CSDP_GROW CSDP_DEC
qui estadd scalar p_joint = r(p)
est store G7

qui est restore G8
addtest H2b, dir(pos) : CSDN_MAT 1
addtest slopeM, dir(pos) : CSDN 1 CSDN_MAT 1
est store G8

qui est restore G9
addtest H3a, dir(pos) : CSDP_MA 1
est store G9

qui est restore G10
addtest H3aM,  dir(pos) : CSDP_MA 1
addtest H3aGD, dir(pos) : CSDP_MA 1 CSDP_MA_GD 1
addtest H3a3,  dir(pos) : CSDP_MA_GD 1
est store G10

qui est restore G11
addtest H3b, dir(neg) : CSDN_MA 1
est store G11

qui est restore G12
addtest H3bGD, dir(neg) : CSDN_MA 1
addtest H3bM,  dir(neg) : CSDN_MA 1 CSDN_MA_MAT 1
addtest H3b3,  dir(neg) : CSDN_MA_MAT 1
est store G12

*------------------------------------------------------------------------------
* C. Tables
*------------------------------------------------------------------------------
local KEEP "L.InvEff CSDP CSDN MA GROW DEC MAT GD CSDP_GROW CSDP_DEC CSDN_MAT CSDP_MA CSDN_MA CSDP_GD MA_GD CSDP_MA_GD MA_MAT CSDN_MA_MAT $XCTRL"
local STATS "N nfirms ninst ar1p ar2p hansenp dhansenp Fstat g_fe g_ols p_H1a p_H1b p_asym p_H2aG p_H2aD p_joint p_H2b p_H3a p_H3aM p_H3aGD p_H3a3 p_H3b p_H3bGD p_H3bM p_H3b3"
local SLAB `"Observations Firms Instruments "AR(1) p" "AR(2) p" "Hansen p" "Diff-in-Hansen (levels) p" "Wald F" "gamma1 within (lower bound)" "gamma1 pooled OLS (upper bound)" "H1a p" "H1b p" "Asymmetry p (b1+b2=0)" "H2a growth p" "H2a decline p" "H2a joint Wald p" "H2b p" "H3a p" "H3a maturity p" "H3a growth/decline p" "H3a three-way p" "H3b p" "H3b growth/decline p" "H3b maturity p" "H3b three-way p""'

esttab G6 G7 G8 G9 G10 G11 G12 using "$OUT/T5_main_GMM.rtf", replace label ///
    b(%9.4f) se(%9.4f) star(* 0.10 ** 0.05 *** 0.01) keep(`KEEP') order(`KEEP') ///
    mtitles("Eq.(6) H1" "Eq.(7) H2a" "Eq.(8) H2b" "Eq.(9) H3a" "Eq.(10) H3a" "Eq.(11) H3b" "Eq.(12) H3b") ///
    stats(`STATS', labels(`SLAB') fmt(%9.0f %9.0f %9.0f %9.3f)) ///
    title("Table 5. Capital structure deviation, life cycle, managerial ability and investment inefficiency: two-step System GMM") ///
    addnotes("Dependent variable: InvEff (signed residual of Eq. 1). Windmeijer-corrected SE in parentheses." ///
             "Year dummies (both equations) and industry dummies (levels equation) included. Hypothesis p-values are one-sided.")
esttab G6 G7 G8 G9 G10 G11 G12 using "$OUT/T5_main_GMM.csv", replace ///
    b(%9.5f) se(%9.5f) star(* 0.10 ** 0.05 *** 0.01) keep(`KEEP') order(`KEEP') stats(`STATS')

esttab S6 S7 S8 S9 S10 S11 S12 using "$OUT/OA4_static_FE.rtf", replace label ///
    b(%9.4f) se(%9.4f) star(* 0.10 ** 0.05 *** 0.01) ///
    keep(CSDP CSDN MA GROW DEC MAT GD CSDP_GROW CSDP_DEC CSDN_MAT CSDP_MA CSDN_MA CSDP_GD MA_GD CSDP_MA_GD MA_MAT CSDN_MA_MAT $XCTRL) ///
    mtitles("Eq.(6)" "Eq.(7)" "Eq.(8)" "Eq.(9)" "Eq.(10)" "Eq.(11)" "Eq.(12)") ///
    stats(N r2_within, labels("Observations" "Within R-squared")) ///
    title("Table OA4. Static two-way fixed-effects benchmarks") ///
    addnotes("Firm and year fixed effects. SE clustered by firm.")

*------------------------------------------------------------------------------
* D. Marginal effects over MA with Johnson-Neyman intervals (Section 3.9)
*------------------------------------------------------------------------------
qui est restore G9
meplot, x(CSDP) xma(CSDP_MA) name(Fig1_H3a_eq9) title("Eq. (9): effect of over-leverage (CSD+) on InvEff")
qui est restore G10
meplot, x(CSDP) xma(CSDP_MA) xg(CSDP_GD) xmag(CSDP_MA_GD) name(Fig2_H3a_eq10) ///
    title("Eq. (10): effect of CSD+ by life-cycle stage") glab0("Maturity") glab1("Growth / Decline")
qui est restore G11
meplot, x(CSDN) xma(CSDN_MA) name(Fig3_H3b_eq11) title("Eq. (11): effect of under-leverage (CSD-) on InvEff")
qui est restore G12
meplot, x(CSDN) xma(CSDN_MA) xg(CSDN_MAT) xmag(CSDN_MA_MAT) name(Fig4_H3b_eq12) ///
    title("Eq. (12): effect of CSD- by life-cycle stage") glab0("Growth / Decline") glab1("Maturity")

*------------------------------------------------------------------------------
* E. Simple slopes (MA = mean -/+ 1 SD) and economic magnitude
*    effect of a 1-SD increase in CSD+ / CSD-, in % of mean |InvEff|
*------------------------------------------------------------------------------
qui su MA if EST
local sdma = r(sd)
qui su CSDP if EST
local sdp = r(sd)
qui su CSDN if EST
local sdn = r(sd)
gen double absInvEff = abs(InvEff)
qui su absInvEff if EST
local mabs = r(mean)
drop absInvEff

cap postclose econ
postfile econ str12 eq str40 condition double(slope se p effect_1sd pct_mean_absInvEff) ///
    using "$OUT/T6_economic.dta", replace
cap program drop postslope
program define postslope
    args eq cond sd
    macro shift 3
    lcw `*'
    local p = 2 * ttail(r(df), abs(r(est) / r(se)))
    post econ ("`eq'") ("`cond'") (r(est)) (r(se)) (`p') (r(est) * `sd') (100 * r(est) * `sd' / $MABS)
end
global MABS = `mabs'

qui est restore G6
postslope "(6)" "CSD+" `sdp' CSDP 1
postslope "(6)" "CSD-" `sdn' CSDN 1
qui est restore G7
postslope "(7)" "CSD+, maturity" `sdp' CSDP 1
postslope "(7)" "CSD+, growth"   `sdp' CSDP 1 CSDP_GROW 1
postslope "(7)" "CSD+, decline"  `sdp' CSDP 1 CSDP_DEC 1
qui est restore G8
postslope "(8)" "CSD-, growth/decline" `sdn' CSDN 1
postslope "(8)" "CSD-, maturity"       `sdn' CSDN 1 CSDN_MAT 1
qui est restore G9
postslope "(9)" "CSD+, low MA (-1 SD)"  `sdp' CSDP 1 CSDP_MA `=-`sdma''
postslope "(9)" "CSD+, high MA (+1 SD)" `sdp' CSDP 1 CSDP_MA `sdma'
qui est restore G10
postslope "(10)" "CSD+, maturity, low MA"        `sdp' CSDP 1 CSDP_MA `=-`sdma''
postslope "(10)" "CSD+, maturity, high MA"       `sdp' CSDP 1 CSDP_MA `sdma'
postslope "(10)" "CSD+, growth/decline, low MA"  `sdp' CSDP 1 CSDP_GD 1 CSDP_MA `=-`sdma'' CSDP_MA_GD `=-`sdma''
postslope "(10)" "CSD+, growth/decline, high MA" `sdp' CSDP 1 CSDP_GD 1 CSDP_MA `sdma' CSDP_MA_GD `sdma'
qui est restore G11
postslope "(11)" "CSD-, low MA (-1 SD)"  `sdn' CSDN 1 CSDN_MA `=-`sdma''
postslope "(11)" "CSD-, high MA (+1 SD)" `sdn' CSDN 1 CSDN_MA `sdma'
qui est restore G12
postslope "(12)" "CSD-, growth/decline, low MA"  `sdn' CSDN 1 CSDN_MA `=-`sdma''
postslope "(12)" "CSD-, growth/decline, high MA" `sdn' CSDN 1 CSDN_MA `sdma'
postslope "(12)" "CSD-, maturity, low MA"        `sdn' CSDN 1 CSDN_MAT 1 CSDN_MA `=-`sdma'' CSDN_MA_MAT `=-`sdma''
postslope "(12)" "CSD-, maturity, high MA"       `sdn' CSDN 1 CSDN_MAT 1 CSDN_MA `sdma' CSDN_MA_MAT `sdma'
postclose econ
preserve
    use "$OUT/T6_economic.dta", clear
    format slope se effect_1sd %9.4f
    format p %6.4f
    format pct_mean_absInvEff %7.2f
    di as res _n "T6. Simple slopes and economic magnitude"
    list, noobs sep(0) abbrev(20)
    export excel using "$OUT/Tables.xlsx", sheet("T6_economic", replace) firstrow(variables)
restore

*------------------------------------------------------------------------------
* F. Binned estimator (Hainmueller, Mummolo & Xu 2019): effect of CSD+/CSD-
*    within MA terciles vs the linear-interaction prediction (static FE)
*------------------------------------------------------------------------------
di as res _n "OA. Binned estimator: CSD effects by MA tercile"
xtile MAbin = MA if EST, nq(3)
forvalues b = 1/3 {
    gen double CSDP_b`b' = CSDP * (MAbin == `b')
    gen double CSDN_b`b' = CSDN * (MAbin == `b')
    qui su MA if EST & MAbin == `b', d
    local med`b' = r(p50)
}
eststo BIN: reghdfe InvEff CSDP_b1 CSDP_b2 CSDP_b3 CSDN_b1 CSDN_b2 CSDN_b3 i.MAbin $XCTRL ///
    if EST, absorb(FirmID Year) vce(cluster FirmID)
qui reghdfe InvEff CSDP CSDN MA CSDP_MA CSDN_MA $XCTRL if EST, absorb(FirmID Year) vce(cluster FirmID)
forvalues b = 1/3 {
    lcw CSDP 1 CSDP_MA `med`b''
    local lp`b' = r(est)
    lcw CSDN 1 CSDN_MA `med`b''
    local ln`b' = r(est)
}
qui est restore BIN
forvalues b = 1/3 {
    qui estadd scalar linP`b' = `lp`b''
    qui estadd scalar linN`b' = `ln`b''
}
est store BIN
esttab BIN using "$OUT/OA_binned_estimator.rtf", replace b(%9.4f) se(%9.4f) ///
    star(* 0.10 ** 0.05 *** 0.01) keep(CSDP_b1 CSDP_b2 CSDP_b3 CSDN_b1 CSDN_b2 CSDN_b3) ///
    stats(linP1 linP2 linP3 linN1 linN2 linN3 N, labels("Linear CSD+ effect at bin-1 median MA" ///
    "... bin 2" "... bin 3" "Linear CSD- effect at bin-1 median MA" "... bin 2" "... bin 3" "Observations")) ///
    title("Table OA. Binned estimator: CSD effects by managerial-ability tercile") ///
    addnotes("Bins = MA terciles. Static model with firm and year fixed effects, SE clustered by firm." ///
             "Binned estimates close to the linear predictions support the linear interaction.")
drop CSDP_b* CSDN_b* MAbin

*------------------------------------------------------------------------------
* G. Within-stage estimates (descriptive; Online Appendix OA9) - static FE
*------------------------------------------------------------------------------
foreach s in 1 2 3 {
    qui eststo W6_`s':  reghdfe InvEff CSDP CSDN $XCTRL if EST & STAGE_L == `s', absorb(FirmID Year) vce(cluster FirmID)
    qui eststo W9_`s':  reghdfe InvEff CSDP CSDN MA CSDP_MA $XCTRL if EST & STAGE_L == `s', absorb(FirmID Year) vce(cluster FirmID)
    qui eststo W11_`s': reghdfe InvEff CSDP CSDN MA CSDN_MA $XCTRL if EST & STAGE_L == `s', absorb(FirmID Year) vce(cluster FirmID)
}
esttab W6_1 W6_2 W6_3 W9_1 W9_2 W9_3 W11_1 W11_2 W11_3 using "$OUT/OA9_within_stage.rtf", replace ///
    b(%9.4f) se(%9.4f) star(* 0.10 ** 0.05 *** 0.01) keep(CSDP CSDN MA CSDP_MA CSDN_MA) ///
    mtitles("(6) G" "(6) M" "(6) D" "(9) G" "(9) M" "(9) D" "(11) G" "(11) M" "(11) D") ///
    stats(N r2_within) title("Table OA9. Within-stage estimates (descriptive only)") ///
    addnotes("G = growth, M = maturity, D = decline at t-1. Static FE (firm, year). Not used to test H2/H3.")

*------------------------------------------------------------------------------
* H. Reverse causality, Eq. (13)
*------------------------------------------------------------------------------
di as res _n "{hline 78}" _n "Eq. (13): reverse causality (CSDev on lagged InvEff)" _n "{hline 78}"
xtabond2 CSDev L.CSDev L.InvEff $XCTRL yd_* ind_*, ///
    gmm(CSDev, lag(2 3) collapse) gmm(L.InvEff, lag(1 2) collapse) ///
    gmm($XCTRL, lag(1 2) collapse) iv(yd_*) iv(ind_*, eq(level)) iv(lnAge, eq(level)) ///
    twostep robust small artests(2)
gmmstats, name(G13)
test L.InvEff
qui estadd scalar p_theta = r(p)
est store G13
esttab G13 using "$OUT/OA7_reverse_causality.rtf", replace b(%9.4f) se(%9.4f) ///
    star(* 0.10 ** 0.05 *** 0.01) keep(L.CSDev L.InvEff $XCTRL) ///
    stats(N nfirms ninst ar1p ar2p hansenp dhansenp p_theta, labels("Observations" "Firms" ///
    "Instruments" "AR(1) p" "AR(2) p" "Hansen p" "Diff-in-Hansen (levels) p" "p (theta = 0)")) ///
    title("Table OA7. Reverse causality: Eq. (13)") ///
    addnotes("Dependent variable: CSDev. Two-step System GMM, Windmeijer-corrected SE.")
