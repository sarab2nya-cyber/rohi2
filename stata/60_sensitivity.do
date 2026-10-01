*==============================================================================
* 60_sensitivity.do  -  Sections 3.11.2 and 3.11.3
*   S1-S8 sensitivity to researcher-chosen parameters; Oster (2019) bounds;
*   placebo test; firm-level cluster bootstrap of the full procedure.
*==============================================================================
cap postclose keyres
postfile keyres str24 test str4 model str16 term double(b se p ar2p hansenp ninst N) ///
    using "$OUT/S_keyresults.dta", replace

* S1 winsorization
rebuild, cuts(2.5 97.5) tag(S1a)
runkey, test("S1a Winsor 2.5/97.5")
rebuild, cuts(5 95) tag(S1b)
runkey, test("S1b Winsor 5/95")
rebuild, cuts(1 99) trim tag(S1c)
runkey, test("S1c Trim 1/99")

* S2 minimum industry-year cell in Eq. (1)
rebuild, mincell(8) tag(S2a)
runkey, test("S2a Min cell 8")
rebuild, mincell(15) tag(S2b)
runkey, test("S2b Min cell 15")

* S3 DEA specification
rebuild, rts(crs) tag(S3a)
runkey, test("S3a DEA CRS")
rebuild, deafront(indyr) mindea(15) tag(S3b)
runkey, test("S3b DEA industry-year frontier")
rebuild, deafront(indyr) mindea(20) tag(S3c)
runkey, test("S3c DEA ind-year, min 20")

* S4 GMM instrument depth (main data)
rebuild
local altl = cond("$LAGE_MAIN" == "2 3", "2 4", "2 3")
runkey, test("S4a Lags `altl'") lage(`altl')
runkey, test("S4b Lags 3-4") lage(3 4)
runkey, test("S4c Uncollapsed") nocollapse

* S5 exclude near-target firm-years (|deviation| < 0.25 SD)
qui su CSDX if EST
local thr = 0.25 * r(sd)
runkey, test("S5 Exclude near-target") cond(abs(CSDX) >= `thr')

* S6 exclude crisis years 1397-1398 (sanctions, currency) and 1399 (COVID-19)
runkey, test("S6 Exclude 1397-1399") cond(!inlist(Year, 1397, 1398, 1399))

* S10 original study period (estimation from 1395, i.e. data from 1392);
*     relevant when the data start earlier than 1392
if $Y0 < 1392 runkey, test("S10 Period 1395-1403") cond(Year >= 1395)

* S9 elements of the previous main specification
local ORTHO0 "$ORTHO"
local XCTRL0 "$XCTRL"
global ORTHO 0
runkey, test("S9a First differences")
global ORTHO `ORTHO0'
global XCTRL "$XCTRL4"
runkey, test("S9b Original 4 controls")
rebuild, timing(cont) tag(S9c)
global ORTHO 0
runkey, test("S9c Previous main spec") lage(2 3)
global ORTHO `ORTHO0'
global XCTRL "`XCTRL0'"
rebuild                                   // back to the main specification

postclose keyres
di as res _n "T8. Sensitivity: key coefficients (two-sided p: * 0.10 ** 0.05 *** 0.01)"
keytable "$OUT/S_keyresults.dta" "T8_sensitivity"

*------------------------------------------------------------------------------
* S7 leave one industry out (Eq. 6a: beta1, Eq. 6b: beta2)
*------------------------------------------------------------------------------
cap postclose loo
postfile loo int industry double(b1 p1 b2 p2) using "$OUT/S7_leave_industry_out.dta", replace
qui levelsof IndID if EST, local(inds)
foreach j of local inds {
    cap rungmm, dep(InvEff) endog($E6a) cond(IndID != `j') quiet
    if _rc continue
    local b1 = _b[CSDP]
    lcw CSDP 1
    local p1 = 2 * ttail(r(df), abs(r(est) / r(se)))
    cap rungmm, dep(InvEff) endog($E6b) cond(IndID != `j') quiet
    if _rc continue
    local b2 = _b[CSDN]
    lcw CSDN 1
    local p2 = 2 * ttail(r(df), abs(r(est) / r(se)))
    post loo (`j') (`b1') (`p1') (`b2') (`p2')
}
postclose loo
preserve
    use "$OUT/S7_leave_industry_out.dta", clear
    di as res _n "S7. Leave-one-industry-out, Eqs. (6a) and (6b)"
    gen byte sig1 = p1 < 0.05 & b1 < 0
    gen byte sig2 = p2 < 0.05 & b2 > 0
    tabstat b1 b2 sig1 sig2, stat(n min mean max) format(%9.4f)
    export excel using "$OUT/Tables.xlsx", sheet("T8b_leave_industry_out", replace) firstrow(variables)
restore

* S8 unbalanced panel
di as txt _n "S8: requires the firms removed by the continuity filter (not in the current" ///
    _n "    data file). Add them to Final_Master_Data.xlsx with a flag and re-run."

*------------------------------------------------------------------------------
* Oster (2019) coefficient stability for beta1 and beta2 (static OLS)
*   delta = b_full (R_full - R_short) / [(b_short - b_full)(R_max - R_full)],
*   R_max = min(1, 1.3 R_full); |delta| > 1 indicates robustness
*------------------------------------------------------------------------------
rebuild
qui reg InvEff CSDP CSDN if EST
local bs1 = _b[CSDP]
local bs2 = _b[CSDN]
local Rs  = e(r2)
qui reg InvEff CSDP CSDN $XCTRL i.Year i.IndID if EST
local bf1 = _b[CSDP]
local bf2 = _b[CSDN]
local Rf  = e(r2)
local Rm  = min(1, 1.3 * `Rf')
local d1 = `bf1' * (`Rf' - `Rs') / ((`bs1' - `bf1') * (`Rm' - `Rf'))
local d2 = `bf2' * (`Rf' - `Rs') / ((`bs2' - `bf2') * (`Rm' - `Rf'))
di as res _n "Oster (2019): delta for CSD+ = " %8.3f `d1' "   delta for CSD- = " %8.3f `d2'
putexcel set "$OUT/Tables.xlsx", sheet("T9_identification") modify
putexcel A1 = "Oster (2019) delta, R_max = 1.3 x R2 (static OLS with year and industry dummies)"
putexcel A2 = "CSD+ (beta1)" B2 = (`d1') A3 = "CSD- (beta2)" B3 = (`d2')
putexcel A4 = "R2 short / full / max" B4 = (`Rs') C4 = (`Rf') D4 = (`Rm')

*------------------------------------------------------------------------------
* Placebo: CSDev permuted within industry-year ($PLACEBO_REPS times);
*          Eq. (6) re-estimated with two-way FE on each permutation
*------------------------------------------------------------------------------
qui reghdfe InvEff CSDP CSDN $XCTRL if EST, absorb(FirmID Year) vce(cluster FirmID)
local a1 = _b[CSDP]
local a2 = _b[CSDN]
set seed 20261001
cap postclose plc
postfile plc int rep double(b1 b2) using "$OUT/placebo.dta", replace
tempvar tv
gen byte `tv' = !missing(CSDX, INDYR)
gen double CSDev_pl = .
forvalues r = 1/$PLACEBO_REPS {
    mata: permute_within("CSDX", "INDYR", "CSDev_pl", "`tv'")
    qui replace CSDP = max( CSDev_pl, 0) if !missing(CSDev_pl)
    qui replace CSDN = max(-CSDev_pl, 0) if !missing(CSDev_pl)
    qui reghdfe InvEff CSDP CSDN $XCTRL if EST, absorb(FirmID Year) vce(cluster FirmID)
    post plc (`r') (_b[CSDP]) (_b[CSDN])
}
postclose plc
preserve
    use "$OUT/placebo.dta", clear
    qui count if abs(b1) >= abs(`a1')
    local pp1 = r(N) / _N
    qui count if abs(b2) >= abs(`a2')
    local pp2 = r(N) / _N
    di as res _n "Placebo: actual b1 = " %8.4f `a1' "  permutation p = " %6.4f `pp1'
    di as res    "         actual b2 = " %8.4f `a2' "  permutation p = " %6.4f `pp2'
    histogram b1, xline(`a1', lc(maroon)) graphregion(color(white)) ///
        title("Placebo distribution of b1 (CSD+)", size(medsmall)) ///
        note("Vertical line: actual estimate. `=$PLACEBO_REPS' within industry-year permutations.")
    graph export "$OUT/Fig5_placebo_b1.png", replace width(2000)
    histogram b2, xline(`a2', lc(maroon)) graphregion(color(white)) ///
        title("Placebo distribution of b2 (CSD-)", size(medsmall)) ///
        note("Vertical line: actual estimate. `=$PLACEBO_REPS' within industry-year permutations.")
    graph export "$OUT/Fig6_placebo_b2.png", replace width(2000)
restore
putexcel set "$OUT/Tables.xlsx", sheet("T9_identification") modify
putexcel A6 = "Placebo (static FE, Eq. 6)" B6 = "actual" C6 = "permutation p"
putexcel A7 = "CSD+ (beta1)" B7 = (`a1') C7 = (`pp1')
putexcel A8 = "CSD- (beta2)" B8 = (`a2') C8 = (`pp2')

*------------------------------------------------------------------------------
* Firm-level cluster bootstrap of the full procedure (Section 3.10.4):
* resample firms, rebuild Eqs. (1), (2), (5), re-estimate Eqs. (6), (9), (11)
* ($BOOT_REPS replications; set to 0 in 00_run_all.do to skip - slow)
*------------------------------------------------------------------------------
if $BOOT_REPS > 0 {
    set seed 20261001
    cap postclose bt
    postfile bt int rep double(b1 b2 b4 b8) using "$OUT/bootstrap.dta", replace
    forvalues r = 1/$BOOT_REPS {
        qui use "$OUT/raw_panel.dta", clear
        qui bsample, cluster(FirmID) idcluster(BID)
        qui drop FirmID
        qui rename BID FirmID
        qui xtset FirmID Year
        cap buildpanel, tag(boot)
        if _rc continue
        local B1 = .
        local B2 = .
        local B4 = .
        local B8 = .
        cap rungmm, dep(InvEff) endog($E6a) quiet
        if !_rc local B1 = _b[CSDP]
        cap rungmm, dep(InvEff) endog($E6b) quiet
        if !_rc local B2 = _b[CSDN]
        cap rungmm, dep(InvEff) endog($E9) quiet
        if !_rc local B4 = _b[CSDP_MA]
        cap rungmm, dep(InvEff) endog($E11) quiet
        if !_rc local B8 = _b[CSDN_MA]
        post bt (`r') (`B1') (`B2') (`B4') (`B8')
        if mod(`r', 10) == 0 di as txt "  bootstrap replication `r' of $BOOT_REPS"
    }
    postclose bt
    preserve
        use "$OUT/bootstrap.dta", clear
        di as res _n "Bootstrap standard errors (full procedure, firm clusters)"
        tabstat b1 b2 b4 b8, stat(n mean sd p5 p95) format(%9.4f)
        export excel using "$OUT/Tables.xlsx", sheet("T9b_bootstrap", replace) firstrow(variables)
    restore
}
