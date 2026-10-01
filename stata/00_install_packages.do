*==============================================================================
* 00_install_packages.do  -  run ONCE (no internet and no Java needed)
* Installs ftools, require, reghdfe, estout (+ optional xtabond2, boottest)
* from the stata_pkgs folder that ships with this project.
* Edit the three paths below if your folders are elsewhere.
*==============================================================================
version 16.0
clear all
global PLUS   "C:/Users/Rohi/Desktop/plus"
global PKGDIR "C:/Users/Rohi/Desktop/stata_pkgs"
global ROOT   "C:/Users/Rohi/Desktop/Data"

*------------------------------------------------------------------------------
* PACKAGE SETUP - fully offline (no internet, no Java).
* Packages are taken from the project's stata_pkgs folder. NOTE: paths use "/"
* on purpose: in Stata a backslash written directly before a local macro
* (backslash + local-macro quote) stops the macro from expanding - this broke the previous
* version of this block.
*------------------------------------------------------------------------------
cap mkdir "$PLUS"
sysdir set PLUS "$PLUS"
adopath + "$PLUS"

local REQ "ftools require reghdfe estout"      // required
local OPT "xtabond2 boottest"                   // optional (robustness only)

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
