*==============================================================================
* 70_report.do  -  collects ALL results into ONE report that opens in Word:
*                  $OUT/Results_Report.rtf   (Word: File > Save As > .docx)
*   Built with esttab (estout), not putdocx: putdocx fails to load on some
*   Stata 17 installations ("wrong number of arguments for _docx_append()").
*   1 Data  2 Assumptions  3 Hypothesis decisions  4 One table per hypothesis
*   5 Economic magnitude  6 Robustness / sensitivity / identification
*   7 First stages and within-stage estimates  8 Figures (linked pictures)
*==============================================================================
di as res "70_report.do version 2026-10-01d"
if "$Y0" == "" {                          // report run on its own
    preserve
    qui use Year using "$OUT/raw_panel.dta", clear
    qui su Year
    global Y0 = r(min)
    global YN = r(max)
    restore
}
global RPT     "$OUT/Results_Report.rtf"
global RPTMODE "replace"

*------------------------------------------------------------------------------
* helpers
*------------------------------------------------------------------------------
* matrix -> table in the report
cap program drop rpt_mat
program define rpt_mat
    syntax namelist(max=1), TITLE(string) [NOTE(string) FMT(string)]
    local M `namelist'
    if "`fmt'" == "" local fmt "%9.4f"
    cap confirm matrix `M'
    if _rc exit
    qui esttab matrix(`M', fmt(`fmt')) using "$RPT", $RPTMODE nomtitles ///
        title(`"`title'"') addnotes(`"`note'"')
    global RPTMODE "append"
end

* .dta file -> matrix (numeric variables), row names from string variables
cap program drop dta2mat
program define dta2mat
    syntax using/, Matrix(name) ROWvars(string) KEEPvars(string) [TAGval(string)]
    preserve
    cap use "`using'", clear
    if _rc {
        restore
        exit
    }
    if "`tagval'" != "" qui keep if tag == "`tagval'"
    if _N == 0 {
        restore
        exit
    }
    qui gen str200 _rn = ""
    foreach r of local rowvars {
        cap confirm string variable `r'
        if _rc qui replace _rn = _rn + "_" + string(`r')
        else   qui replace _rn = _rn + "_" + `r'
    }
    qui replace _rn = strtoname(substr(_rn, 2, .))
    mkmat `keepvars', matrix(`matrix') rownames(_rn)
    restore
end

* sheet of Tables.xlsx -> matrix: column A = labels, numeric columns kept
cap program drop sheet2mat
program define sheet2mat
    syntax , SHEET(string) Matrix(name) [COLS(string) CNAMES(string)]
    if "`cols'" == "" local cols "B C"
    preserve
    cap import excel using "$OUT/Tables.xlsx", sheet("`sheet'") allstring clear
    if _rc {
        restore
        exit
    }
    local keep ""
    foreach c of local cols {
        cap confirm variable `c'
        if _rc continue
        qui destring `c', replace force
        local keep "`keep' `c'"
    }
    if "`keep'" == "" {
        restore
        exit
    }
    qui egen _nn = rownonmiss(`keep')
    qui keep if _nn > 0 & A != ""
    if _N == 0 {
        restore
        exit
    }
    qui gen str200 _rn = strtoname(A)
    mkmat `keep', matrix(`matrix') rownames(_rn)
    if "`cnames'" != "" matrix colnames `matrix' = `cnames'
    restore
end

* coefficient matrix (b, se, p) for a stored estimate and a coefficient list
cap program drop coefmat
program define coefmat
    args est M coefs
    cap qui est restore `est'
    if _rc {
        qui estimates use "$OUT/est_`est'"
        qui est store `est'
    }
    local k : word count `coefs'
    matrix `M' = J(`k', 3, .)
    local rn ""
    local i = 0
    foreach c of local coefs {
        local ++i
        local cc = subinstr("`c'", ".", "_", .)
        local rn "`rn' `cc'"
        cap local b = _b[`c']
        if _rc continue
        local se = _se[`c']
        if `se' == 0 | missing(`se') continue
        local df = e(df_r)
        if missing(`df') local df = e(N_g) - 1
        if missing(`df') local df = e(N_clust) - 1
        matrix `M'[`i', 1] = `b'
        matrix `M'[`i', 2] = `se'
        matrix `M'[`i', 3] = cond(missing(`df'), 2 * normal(-abs(`b' / `se')), ///
            2 * ttail(`df', abs(`b' / `se')))
    }
    matrix rownames `M' = `rn'
    matrix colnames `M' = b se p
end


* load stored estimates from memory or disk
cap program drop getest
program define getest
    args e
    cap qui est restore `e'
    if _rc {
        cap qui estimates use "$OUT/est_`e'"
        if !_rc qui est store `e'
    }
end

*==============================================================================
* 1. DATA
*==============================================================================
dta2mat using "$OUT/log_winsorization.dta", matrix(W) rowvars(variable) ///
    keepvars(N p_low p_high n_low n_high) tagval(main)
rpt_mat W, title("Table 0. Winsorization of ratios and generated measures at the 1st and 99th percentiles") ///
    note("p_low/p_high: cut-offs; n_low/n_high: values replaced.")

use "$OUT/analysis_panel.dta", clear
xtset FirmID Year

qui tabstat InvEff Invest SalesGrowth TDA TDAhat CSDev CSDX CSDP CSDN FE MA ///
    $XCTRL IOB COL INDLEV INF Age if EST, ///
    stat(n mean sd min p25 p50 p75 max skewness kurtosis) save
matrix D = r(StatTotal)'
rpt_mat D, title("Table 1. Descriptive statistics (estimation sample)") fmt(%9.3f)

gen byte OVERINV = InvEff > 0 if !missing(InvEff)
qui tab OVERINV OVERLEV if EST, matcell(DIR)
cap matrix rownames DIR = Under_investment Over_investment
cap matrix colnames DIR = Under_leveraged Over_leveraged
rpt_mat DIR, title("Table 1b. Direction of investment and leverage deviations (firm-years)") fmt(%9.0f)

local CV "InvEff CSDP CSDN MA $XCTRL GROW MAT DEC"
qui corr `CV' if EST
matrix P = r(C)
local n = r(N)
qui spearman `CV' if EST, stats(rho)
matrix S = r(Rho)
local k : word count `CV'
matrix C = P
forvalues i = 1/`k' {
    forvalues j = 1/`k' {
        if `j' > `i' matrix C[`i', `j'] = S[`i', `j']
    }
}
local crit  = invttail(`n' - 2, 0.025)
local rcrit = `crit' / sqrt(`n' - 2 + `crit'^2)
rpt_mat C, title("Table 2. Correlations: Pearson (lower triangle) and Spearman (upper triangle)") fmt(%6.3f) ///
    note("N = `n'. |r| > `: di %5.3f `rcrit'' is significant at 5%. Stars: Tables.xlsx, sheet T3_correlations.")

qui tab LC5 if Year >= $Y0 + 1, matcell(F5)
cap matrix rownames F5 = Introduction Growth Mature Shake_out Decline
cap matrix colnames F5 = Firm_years
rpt_mat F5, title("Table 3a. Dickinson (2011) life-cycle stages, `=$Y0 + 1'-$YN") fmt(%9.0f)
qui tab STAGE_L OVERLEV if EST, matcell(SC)
cap matrix rownames SC = Growth Maturity Decline
cap matrix colnames SC = Under_leveraged Over_leveraged
rpt_mat SC, title("Table 3b. Consolidated stage (t-1) by leverage direction") fmt(%9.0f)
qui tab STAGE_L STAGE if Year >= $Y0 + 2, matcell(TR)
cap matrix rownames TR = Growth_t1 Maturity_t1 Decline_t1
cap matrix colnames TR = Growth_t Maturity_t Decline_t
rpt_mat TR, title("Table 3c. Stage transitions (counts)") fmt(%9.0f)

sheet2mat, sheet("OA2b_DEA") matrix(DEA) cols(B) cnames(Value)
rpt_mat DEA, title("Table 4. Data envelopment analysis (stage 1 of managerial ability)")

*==============================================================================
* 2. ASSUMPTIONS
*==============================================================================
sheet2mat, sheet("T4_VIF") matrix(VIF) cols(B) cnames(VIF)
rpt_mat VIF, title("Table 5. Variance inflation factors (static main-effects model)") fmt(%9.2f)
sheet2mat, sheet("T4b_assumptions") matrix(AS) cols(B C) cnames(Statistic p_value)
rpt_mat AS, title("Table 6. Specification and classical-assumption tests (static benchmark of Eq. 6)") ///
    note("Decision column and H0 of each test: Tables.xlsx, sheet T4b_assumptions.")
dta2mat using "$OUT/OA_instrument_strength.dta", matrix(IVS) rowvars(variable lags) ///
    keepvars(F_transformed F_levels)
rpt_mat IVS, title("Table 6b. Instrument strength: first-stage F of the collapsed GMM instruments") fmt(%9.2f) ///
    note("Rule fixed before estimation: lags t-2..t-3 unless the weakest F < 10 and t-2..t-4 is stronger. Window used: $LAGE_MAIN.")

*==============================================================================
* 3. HYPOTHESIS DECISIONS
*==============================================================================
dta2mat using "$OUT/T5_hypothesis_summary.dta", matrix(HY) rowvars(hypothesis eq) ///
    keepvars(estimate se p ar2p hansenp)
rpt_mat HY, title("Table 7. Hypothesis tests: estimate, one-sided p-value, AR(2) and Hansen p of the model") ///
    note("Supported if p < 0.05 (0.10 = weak) AND AR(2) p > 0.10 AND Hansen p > 0.10. Decision text: Tables.xlsx, sheet T5_hypotheses.")

*==============================================================================
* 4. ONE TABLE PER HYPOTHESIS (GMM next to static FE)
*==============================================================================
local T6a "Table 8.1 - H1a: over-leverage (CSD+), Eq. (6a)"
local T6b "Table 8.2 - H1b: under-leverage (CSD-), Eq. (6b)"
local T6  "Table 8.3 - Asymmetry of the two effects, Eq. (6)"
local T7  "Table 8.4 - H2a: over-leverage x life cycle (reference = maturity), Eq. (7)"
local T8  "Table 8.5 - H2b: under-leverage x maturity, Eq. (8)"
local T9  "Table 8.6 - H3a: over-leverage x managerial ability, Eq. (9)"
local T10 "Table 8.7 - H3a: over-leverage x MA x growth/decline, Eq. (10)"
local T11 "Table 8.8 - H3b: under-leverage x managerial ability, Eq. (11)"
local T12 "Table 8.9 - H3b: under-leverage x MA x maturity, Eq. (12)"
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
    getest G`m'
    getest S`m'
    cap est restore G`m'
    if _rc continue
    qui esttab G`m' S`m' using "$RPT", append label b(%9.4f) se(%9.4f) ///
        star(* 0.10 ** 0.05 *** 0.01) keep(L.InvEff ${E`m'} ${P`m'} $XCTRL) ///
        order(L.InvEff ${E`m'} ${P`m'}) mtitles("Two-step System GMM" "Static two-way FE") ///
        stats(N N_g j ar1p ar2p hansenp dhansenp `H`m'', fmt(%9.0f %9.0f %9.0f %9.3f) ///
        labels("Observations" "Firms" "Instruments" "AR(1) p" "AR(2) p" "Hansen p" "Diff-in-Hansen p")) ///
        title("`T`m''") addnotes("Dependent variable: InvEff. GMM: Windmeijer-corrected SE; FE: SE clustered by firm. p_H...: one-sided.")
}
getest G13
cap est restore G13
if !_rc {
    qui esttab G13 using "$RPT", append label b(%9.4f) se(%9.4f) star(* 0.10 ** 0.05 *** 0.01) ///
        keep(L.CSDev L.InvEff $XCTRL) stats(N N_g j ar1p ar2p hansenp dhansenp p_theta, fmt(%9.0f %9.0f %9.0f %9.3f)) ///
        title("Table 8.10 - Reverse causality, Eq. (13): dependent variable CSDev")
}

*==============================================================================
* 5. ECONOMIC MAGNITUDE
*==============================================================================
dta2mat using "$OUT/T6_economic.dta", matrix(EC) rowvars(eq condition) ///
    keepvars(slope se p effect_1sd pct_mean_absInvEff)
rpt_mat EC, title("Table 9. Simple slopes and economic magnitude") ///
    note("effect_1sd: change in InvEff for a 1-SD increase in CSD+ / CSD-; pct: % of mean |InvEff|. Low/high MA = mean -/+ 1 SD.")

*==============================================================================
* 6. ROBUSTNESS, SENSITIVITY, IDENTIFICATION
*==============================================================================
* (analysis data are no longer needed from here on)
foreach f in R S {
    local lab = cond("`f'" == "R", "Robustness R1-R10", "Sensitivity S1-S10")
    local tn  = cond("`f'" == "R", "10", "11")
    cap use "$OUT/`f'_keyresults.dta", clear
    if _rc continue
    if _N == 0 continue
    qui gen str32 col = strtoname(term)
    qui gen int ord = _n
    qui bys test: egen int o = min(ord)
    tempfile base
    qui save `base'
    foreach s in b p {
        qui use `base', clear
        keep test o col `s'
        qui reshape wide `s', i(test o) j(col) string
        sort o
        qui gen str32 _rn = strtoname(test)
        qui ds `s'?*
        mkmat `r(varlist)', matrix(K`s') rownames(_rn)
    }
    rpt_mat Kb, title("Table `tn'a. `lab': key coefficients")
    rpt_mat Kp, title("Table `tn'b. `lab': two-sided p-values of the key coefficients") fmt(%6.3f)
}
dta2mat using "$OUT/S7_leave_industry_out.dta", matrix(LO) rowvars(industry) keepvars(b1 p1 b2 p2)
rpt_mat LO, title("Table 12. Leave one industry out: Eq. (6a) beta1 and Eq. (6b) beta2")
sheet2mat, sheet("T9_identification") matrix(ID) cols(B C D)
rpt_mat ID, title("Table 13. Oster (2019) delta and placebo test") ///
    note("Oster rows: delta (|delta| > 1 = robust); R2 row: short / full / max. Placebo rows: actual estimate and permutation p.")

*==============================================================================
* 7. FIRST STAGES AND WITHIN-STAGE ESTIMATES
*==============================================================================
getest TGT_main
cap coefmat TGT_main A "L_IOB L_COL L_LTA L_MTB L_PROFIT L_INDLEV L_INF _cons"
rpt_mat A, title("Table 14. Target leverage model, Eq. (2)")
getest TOB_main
cap coefmat TOB_main B "LTA MktShare FCFpos lnAge _cons"
rpt_mat B, title("Table 15. Tobit model of DEA efficiency, Eq. (5)")
foreach s in 1 2 3 {
    local sn = cond(`s' == 1, "Growth", cond(`s' == 2, "Maturity", "Decline"))
    foreach w in W6 W9 W11 {
        getest `w'_`s'
        cap est restore `w'_`s'
    }
    cap qui esttab W6_`s' W9_`s' W11_`s' using "$RPT", append b(%9.4f) se(%9.4f) ///
        star(* 0.10 ** 0.05 *** 0.01) keep(CSDP CSDN MA CSDP_MA CSDN_MA) ///
        mtitles("Eq. (6)" "Eq. (9)" "Eq. (11)") stats(N r2_within) ///
        title("Table 16. Within-stage estimates, `sn' stage (static FE; descriptive)")
}

*==============================================================================
* 8. FIGURES: linked pictures appended before the closing brace of the RTF
*==============================================================================
local figs : dir "$OUT" files "Fig*.png"
local figs : list sort figs
tempname fin fout
file open `fin' using "$RPT", read text
file open `fout' using "$OUT/_rpt_tmp.rtf", write text replace
file read `fin' line
local first = 1
while r(eof) == 0 {
    if !`first' file write `fout' `"`macval(prev)'"' _n
    local prev `"`macval(line)'"'
    local first = 0
    file read `fin' line
}
file write `fout' "{\pard\par\b Figures\b0\par}" _n
foreach f of local figs {
    file write `fout' `"{\pard\qc {\field{\*\fldinst INCLUDEPICTURE "$OUT/`f'"}{\fldrslt }}\par `f'\par}"' _n
}
file write `fout' `"`macval(prev)'"' _n
file close `fin'
file close `fout'
copy "$OUT/_rpt_tmp.rtf" "$RPT", replace
erase "$OUT/_rpt_tmp.rtf"

di as res _n "Report saved: $RPT"
di as txt "Open it in Word and use File > Save As > Word Document (.docx)."
di as txt "If the figures are not visible, press Ctrl+A and then F9 in Word."
