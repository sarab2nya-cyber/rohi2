*==============================================================================
* 00_run_all.do  -  MASTER FILE: run this file only.
*
* "The Asymmetric Impact of Managerial Ability on Investment Efficiency under
*  Capital Structure Deviation: Evidence from Emerging Markets"
*
* Implements docs/Research_Methodology (Sections 3.1-3.11) step by step:
*   10_programs.do      helper programs (winsorizing, DEA, GMM, tests, plots)
*   20_build.do         data import and construction of every variable
*   30_descriptives.do  descriptive statistics, correlations, life-cycle
*                       tables, first stages, VIF, classical-assumption tests
*   40_main_models.do   Eqs. (6)-(13) by two-step System GMM, hypothesis
*                       tests, marginal effects, economic magnitude
*   50_robustness.do    R1-R10
*   60_sensitivity.do   S1-S8, Oster bounds, placebo, bootstrap
*
* Folder layout expected (edit section 0 if different):
*   C:/Users/Rohi/Desktop/Data/Final_Master_Data.xlsx      the data
*   C:/Users/Rohi/Desktop/Data/stata/                      these do-files
*   C:/Users/Rohi/Desktop/stata_pkgs/                      offline packages
* Results: C:/Users/Rohi/Desktop/Data/output/  (Tables.xlsx, *.rtf, *.png, log)
*==============================================================================
version 17.0
clear all
set more off
set seed 20261001

*------------------------------------------------------------------------------
* 0. PATHS AND SWITCHES  (forward slashes on purpose)
*------------------------------------------------------------------------------
global ROOT   "C:/Users/Rohi/Desktop/Data"
global CODE   "$ROOT/stata"
global DATA   "Final_Master_Data.xlsx"
global OUT    "$ROOT/output"
global PLUS   "C:/Users/Rohi/Desktop/plus"
global PKGDIR "C:/Users/Rohi/Desktop/stata_pkgs"

global RUN_ROBUST    1      // 1 = run 50_robustness.do
global RUN_SENS      1      // 1 = run 60_sensitivity.do
global PLACEBO_REPS  500    // placebo permutations (static FE, fast)
global BOOT_REPS     0      // full-procedure bootstrap replications (slow; e.g. 199)

* controls and model definitions (Section 3.7)
global XCTRL  "L_LTA L_MTB L_PROFIT L_FCF"   // controls at t-1 (Biddle et al. 2009)
global MODELS    "6a 6b 6 7 8 9 10 11 12"   // 6a = H1a, 6b = H1b, 6 = asymmetry test
global KEYMODELS "6a 6b 7 8 9 10 11 12"     // models with a hypothesis coefficient
global INVDEF_MAIN "cash" // main investment measure: "cash" = -CFI / TA(t-1) (unaffected by
                          // asset revaluations); "net" = increase in PPE + IA / TA(t-1)
global CTRL_TYPE "pred"   // controls: "pred" (lags t-1,t-2, main) or "endog" (lags t-2,t-3)
* endogenous regressors (lags t-2, t-3)          * predetermined (lags t-1, t-2)
global E6a "CSDP UNDERLEV"
global P6a ""
global E6b "CSDN OVERLEV"
global P6b ""
global E6  "CSDP CSDN"
global P6  ""
global E7  "CSDP CSDN CSDP_GROW CSDP_DEC"
global P7  "GROW DEC"
global E8  "CSDP CSDN CSDN_MAT"
global P8  "MAT"
global E9  "CSDP CSDN MA CSDP_MA"
global P9  ""
global E10 "CSDP CSDN MA CSDP_MA CSDP_GD MA_GD CSDP_MA_GD"
global P10 "GD"
global E11 "CSDP CSDN MA CSDN_MA"
global P11 ""
global E12 "CSDP CSDN MA CSDN_MA CSDN_MAT MA_MAT CSDN_MA_MAT"
global P12 "MAT"

cap mkdir "$OUT"
cd "$ROOT"
cap log close _all
log using "$OUT/master_log.smcl", replace name(master)

* PACKAGE SETUP - fully offline (no internet, no Java).
* Packages are taken from the project's stata_pkgs folder. NOTE: paths use "/"
* on purpose: in Stata a backslash written directly before a local macro
* (backslash + local-macro quote) stops the macro from expanding - this broke the previous
* version of this block.
*------------------------------------------------------------------------------
cap mkdir "$PLUS"
sysdir set PLUS "$PLUS"
adopath + "$PLUS"

local REQ "ftools require reghdfe estout xtabond2"   // all required
local OPT ""

* Locate stata_pkgs (also handles Windows "Extract All" nesting it twice)
local CANDS `""$PKGDIR" "$PKGDIR/stata_pkgs" "$ROOT/stata_pkgs" "$ROOT/stata_pkgs/stata_pkgs" "`c(pwd)'/stata_pkgs" "`c(pwd)'/../stata_pkgs" "`c(pwd)'""'
local PKGBASE ""
foreach c of local CANDS {
    if "`PKGBASE'" == "" {
        cap confirm file "`c'/reghdfe/reghdfe.pkg"
        if !_rc local PKGBASE "`c'"
    }
}

local NEED 0
foreach p in `REQ' `OPT' {
    cap which `p'
    if _rc local NEED 1
}

if `NEED' & "`PKGBASE'" == "" {
    di as err _n "Cannot find the stata_pkgs folder. Looked for reghdfe/reghdfe.pkg in:"
    foreach c of local CANDS {
        di as err "   `c'"
    }
    di as err "Unzip stata_pkgs.zip and set global PKGDIR (section 0) to the folder that"
    di as err "directly contains the sub-folders ftools, require, reghdfe, estout, ..."
    exit 601
}

foreach p in `REQ' `OPT' {
    cap which `p'
    if _rc {
        cap confirm file "`PKGBASE'/`p'/`p'.pkg"
        if _rc {
            di as txt "   `p': not in `PKGBASE' - skipped"
            continue
        }
        di as txt "Installing `p' from `PKGBASE'/`p' ..."
        cap noi net install `p', from("`PKGBASE'/`p'") replace
        cap which `p'
        if _rc {
            * Fallback: run the package directly from its folder (no install)
            adopath + "`PKGBASE'/`p'"
            di as txt "   `p': using files in place (adopath)"
        }
    }
}
cap noi ftools, compile
cap noi reghdfe, compile

* Verify: every required package found AND reghdfe actually runs
local MISSING ""
foreach p of local REQ {
    cap which `p'
    if _rc local MISSING "`MISSING' `p'"
}
preserve
qui sysuse auto, clear
cap noi reghdfe price weight, absorb(rep78)
local RHDFE_OK = (_rc == 0)
restore
if "`MISSING'" != "" | !`RHDFE_OK' {
    di as err _n "Required packages missing or not working:`MISSING'"
    if !`RHDFE_OK' di as err "reghdfe is found but does not run - see the error printed just above."
    exit 199
}
foreach p of local OPT {
    cap which `p'
    if _rc di as txt "Note: optional package `p' not installed - its robustness block will be skipped."
}
di as res "All required packages are installed and working."


*------------------------------------------------------------------------------
* RUN
*------------------------------------------------------------------------------
do "$CODE/10_programs.do"
do "$CODE/20_build.do"
do "$CODE/30_descriptives.do"
do "$CODE/40_main_models.do"
if $RUN_ROBUST do "$CODE/50_robustness.do"
if $RUN_SENS   do "$CODE/60_sensitivity.do"
do "$CODE/70_report.do"            // all tables and figures in one Word file

log close master
* printed copies of the complete Stata output
cap translate "$OUT/master_log.smcl" "$OUT/Stata_Output_Log.pdf", replace
cap translate "$OUT/master_log.smcl" "$OUT/Stata_Output_Log.txt", replace translator(smcl2log)
di as res "Done. See $OUT: Results_Report.docx, Tables.xlsx, Stata_Output_Log.pdf / .txt, figures."
