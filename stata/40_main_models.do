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
* A0. Instrument strength and lag window (Section 3.8.2), fixed BEFORE any
*     hypothesis model is estimated: first-stage F of the collapsed lag-level
*     instruments for the main regressors (CSD+, CSD-, MA). Rule: keep lags
*     t-2..t-3 unless the weakest F < 10 and the window t-2..t-4 is stronger.
*------------------------------------------------------------------------------
cap postclose ivs
postfile ivs str12 variable str6 lags double(F_transformed F_levels) ///
    using "$OUT/OA_instrument_strength.dta", replace
ivstrength CSDP CSDN MA, lags(2 3) post(ivs)
local F23 = r(minF)
ivstrength CSDP CSDN MA, lags(2 4) post(ivs)
local F24 = r(minF)
postclose ivs
global LAGE_MAIN "2 3"
if `F23' < 10 & `F24' > `F23' global LAGE_MAIN "2 4"
di as res _n "Instrument strength: weakest first-stage F, lags 2-3 = " %7.2f `F23' ///
    ", lags 2-4 = " %7.2f `F24' "  ->  lag window used: $LAGE_MAIN"
preserve
    use "$OUT/OA_instrument_strength.dta", clear
    format F_* %9.2f
    list, noobs sep(0)
    export excel using "$OUT/Tables.xlsx", sheet("OA_IV_strength", replace) firstrow(variables)
restore

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
* H1a - its own model, Eq. (6a)
qui est restore G6a
addtest H1a, dir(neg) : CSDP 1
est store G6a
* H1b - its own model, Eq. (6b)
qui est restore G6b
addtest H1b, dir(pos) : CSDN 1
est store G6b
* asymmetry - joint model, Eq. (6)
qui est restore G6
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
* B2. ONE TABLE PER HYPOTHESIS (GMM model + static FE benchmark side by side)
*------------------------------------------------------------------------------
local T6a "Table 5.1 - H1a: over-leverage (CSD+) and investment inefficiency, Eq. (6a)"
local T6b "Table 5.2 - H1b: under-leverage (CSD-) and investment inefficiency, Eq. (6b)"
local T6  "Table 5.3 - Asymmetry of the two effects, Eq. (6)"
local T7  "Table 5.4 - H2a: over-leverage x life cycle (reference = maturity), Eq. (7)"
local T8  "Table 5.5 - H2b: under-leverage x maturity (reference = growth/decline), Eq. (8)"
local T9  "Table 5.6 - H3a: over-leverage x managerial ability, Eq. (9)"
local T10 "Table 5.7 - H3a: over-leverage x managerial ability x growth/decline, Eq. (10)"
local T11 "Table 5.8 - H3b: under-leverage x managerial ability, Eq. (11)"
local T12 "Table 5.9 - H3b: under-leverage x managerial ability x maturity, Eq. (12)"
local H6a "p_H1a"
local H6b "p_H1b"
local H6  "p_asym"
local H7  "p_H2aG p_H2aD p_joint"
local H8  "p_H2b"
local H9  "p_H3a"
local H10 "p_H3aM p_H3aGD p_H3a3"
local H11 "p_H3b"
local H12 "p_H3bGD p_H3bM p_H3b3"
foreach m of global MODELS {
    esttab G`m' S`m' using "$OUT/T5_eq`m'.rtf", replace label ///
        b(%9.4f) se(%9.4f) star(* 0.10 ** 0.05 *** 0.01) ///
        keep(L.InvEff ${E`m'} ${P`m'} $XCTRL) order(L.InvEff ${E`m'} ${P`m'}) ///
        mtitles("Two-step System GMM" "Static two-way FE") ///
        stats(N nfirms ninst ar1p ar2p hansenp dhansenp `H`m'', fmt(%9.0f %9.0f %9.0f %9.3f)) ///
        title("`T`m''") ///
        addnotes("Dependent variable: InvEff. GMM: Windmeijer-corrected SE; FE: SE clustered by firm." ///
                 "Hypothesis p-values (p_H...) are one-sided in the predicted direction; p_asym and p_joint are Wald tests.")
}

*------------------------------------------------------------------------------
* B3. HYPOTHESIS DECISION TABLE (one row per hypothesis)
*------------------------------------------------------------------------------
cap postclose hyp
postfile hyp str8 hypothesis str6 eq str26 coefficient str4 predicted double(estimate se p) ///
    str16 decision double(ar2p hansenp) using "$OUT/T5_hypothesis_summary.dta", replace
cap program drop posthyp
program define posthyp
    args h eq coef pred dir
    macro shift 5
    lcw `*'
    local b  = r(est)
    local se = r(se)
    local t  = `b' / `se'
    if "`dir'" == "neg"      local p = ttail(r(df), -`t')
    else if "`dir'" == "pos" local p = ttail(r(df),  `t')
    else                     local p = 2 * ttail(r(df), abs(`t'))
    local dec = cond(`p' < 0.01, "Supported (1%)", cond(`p' < 0.05, "Supported (5%)", ///
        cond(`p' < 0.10, "Supported (10%)", "Not supported")))
    if "`dir'" == "two" local dec = cond(`p' < 0.10, "Asymmetric", "Symmetric")
    post hyp ("`h'") ("`eq'") ("`coef'") ("`pred'") (`b') (`se') (`p') ("`dec'") (e(ar2p)) (e(hansenp))
end
qui est restore G6a
posthyp "H1a" "(6a)" "CSD+"                 "-" neg CSDP 1
qui est restore G6b
posthyp "H1b" "(6b)" "CSD-"                 "+" pos CSDN 1
qui est restore G6
posthyp "Asym" "(6)" "CSD+ + CSD- = 0"      "!=0" two CSDP 1 CSDN 1
qui est restore G7
posthyp "H2a-G" "(7)" "CSD+ x Growth"       "-" neg CSDP_GROW 1
posthyp "H2a-D" "(7)" "CSD+ x Decline"      "-" neg CSDP_DEC 1
qui est restore G8
posthyp "H2b" "(8)" "CSD- x Maturity"       "+" pos CSDN_MAT 1
qui est restore G9
posthyp "H3a" "(9)" "CSD+ x MA"             "+" pos CSDP_MA 1
qui est restore G10
posthyp "H3a-GD" "(10)" "CSD+ x MA in G/D"  "+" pos CSDP_MA 1 CSDP_MA_GD 1
posthyp "H3a-3w" "(10)" "CSD+ x MA x GD"    "+" pos CSDP_MA_GD 1
qui est restore G11
posthyp "H3b" "(11)" "CSD- x MA"            "-" neg CSDN_MA 1
qui est restore G12
posthyp "H3b-MAT" "(12)" "CSD- x MA in MAT" "-" neg CSDN_MA 1 CSDN_MA_MAT 1
posthyp "H3b-3w" "(12)" "CSD- x MA x MAT"  "-" neg CSDN_MA_MAT 1
postclose hyp
preserve
    use "$OUT/T5_hypothesis_summary.dta", clear
    format estimate se %9.4f
    format p ar2p hansenp %6.4f
    di as res _n "{hline 100}" _n "HYPOTHESIS DECISIONS (one-sided p in the predicted direction; two-step System GMM)" _n "{hline 100}"
    list, noobs sep(0) abbrev(12)
    di as txt "Valid only if AR(2) p > 0.10 and Hansen p > 0.10 for that model (Section 3.8.4)."
    export excel using "$OUT/Tables.xlsx", sheet("T5_hypotheses", replace) firstrow(variables)
restore

*------------------------------------------------------------------------------
* C. Tables
*------------------------------------------------------------------------------
local KEEP "L.InvEff CSDP CSDN UNDERLEV OVERLEV MA GROW DEC MAT GD CSDP_GROW CSDP_DEC CSDN_MAT CSDP_MA CSDN_MA CSDP_GD MA_GD CSDP_MA_GD MA_MAT CSDN_MA_MAT $XCTRL"
local STATS "N nfirms ninst ar1p ar2p hansenp dhansenp F g_fe g_ols p_H1a p_H1b p_asym p_H2aG p_H2aD p_joint p_H2b p_H3a p_H3aM p_H3aGD p_H3a3 p_H3b p_H3bGD p_H3bM p_H3b3"
local SLAB `"Observations Firms Instruments "AR(1) p" "AR(2) p" "Hansen p" "Diff-in-Hansen (levels) p" "Wald F" "gamma1 within (lower bound)" "gamma1 pooled OLS (upper bound)" "H1a p" "H1b p" "Asymmetry p (b1+b2=0)" "H2a growth p" "H2a decline p" "H2a joint Wald p" "H2b p" "H3a p" "H3a maturity p" "H3a growth/decline p" "H3a three-way p" "H3b p" "H3b growth/decline p" "H3b maturity p" "H3b three-way p""'

esttab G6a G6b G6 G7 G8 G9 G10 G11 G12 using "$OUT/T5_main_GMM.rtf", replace label ///
    b(%9.4f) se(%9.4f) star(* 0.10 ** 0.05 *** 0.01) keep(`KEEP') order(`KEEP') ///
    mtitles("Eq.(6a) H1a" "Eq.(6b) H1b" "Eq.(6) asymmetry" "Eq.(7) H2a" "Eq.(8) H2b" "Eq.(9) H3a" "Eq.(10) H3a" "Eq.(11) H3b" "Eq.(12) H3b") ///
    stats(`STATS', labels(`SLAB') fmt(%9.0f %9.0f %9.0f %9.3f)) ///
    title("Table 5. Capital structure deviation, life cycle, managerial ability and investment inefficiency: two-step System GMM") ///
    addnotes("Dependent variable: InvEff (signed residual of Eq. 1). Windmeijer-corrected SE in parentheses." ///
             "Year dummies (both equations) and industry dummies (levels equation) included. Hypothesis p-values are one-sided." ///
             "CSD and MA at t-1; controls at t-1. Forward orthogonal deviations; collapsed instruments, lags $LAGE_MAIN.")
esttab G6a G6b G6 G7 G8 G9 G10 G11 G12 using "$OUT/T5_main_GMM.csv", replace ///
    b(%9.5f) se(%9.5f) star(* 0.10 ** 0.05 *** 0.01) keep(`KEEP') order(`KEEP') stats(`STATS')

esttab S6a S6b S6 S7 S8 S9 S10 S11 S12 using "$OUT/OA4_static_FE.rtf", replace label ///
    b(%9.4f) se(%9.4f) star(* 0.10 ** 0.05 *** 0.01) ///
    keep(CSDP CSDN UNDERLEV OVERLEV MA GROW DEC MAT GD CSDP_GROW CSDP_DEC CSDN_MAT CSDP_MA CSDN_MA CSDP_GD MA_GD CSDP_MA_GD MA_MAT CSDN_MA_MAT $XCTRL) ///
    mtitles("Eq.(6a)" "Eq.(6b)" "Eq.(6)" "Eq.(7)" "Eq.(8)" "Eq.(9)" "Eq.(10)" "Eq.(11)" "Eq.(12)") ///
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

qui est restore G6a
postslope "(6a)" "CSD+" `sdp' CSDP 1
qui est restore G6b
postslope "(6b)" "CSD-" `sdn' CSDN 1
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
    gmm(CSDev, lag($LAGE_MAIN) collapse) gmm(L.InvEff, lag(1 2) collapse) ///
    gmm($XCTRL, lag($LAGE_MAIN) collapse) iv(yd_*) iv(ind_*, eq(level)) iv(lnAge, eq(level)) ///
    twostep robust small artests(2) `=cond("$ORTHO" == "1", "orthogonal", "")'
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

*------------------------------------------------------------------------------
* I. Save all estimates to disk (used by 70_report.do if run on its own)
*------------------------------------------------------------------------------
foreach m of global MODELS {
    qui est restore G`m'
    qui estimates save "$OUT/est_G`m'", replace
    qui est restore S`m'
    qui estimates save "$OUT/est_S`m'", replace
}
qui est restore G13
qui estimates save "$OUT/est_G13", replace
foreach s in 1 2 3 {
    foreach w in W6 W9 W11 {
        qui est restore `w'_`s'
        qui estimates save "$OUT/est_`w'_`s'", replace
    }
}
foreach e in TGT_main TOB_main {
    cap qui est restore `e'
    if !_rc qui estimates save "$OUT/est_`e'", replace
}
