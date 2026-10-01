*==============================================================================
* 50_robustness.do  -  Section 3.11.1 (R1-R10)
*   Each test replaces one element of the design; Eqs. (6)-(12) are
*   re-estimated and the key coefficient of every hypothesis is collected.
*   Summary: sheet "T7_robustness" of Tables.xlsx; full log in master log.
*==============================================================================
cap postclose keyres
postfile keyres str24 test byte model str16 term double(b se p ar2p hansenp ninst N) ///
    using "$OUT/R_keyresults.dta", replace

* Main specification (reference row)
rebuild
runkey, test("Main")

* R1 target leverage without IOB
rebuild, target(noiob) tag(R1)
runkey, test("R1 Eq.(2) without IOB")

* R2 market leverage
rebuild, levdef(market) tag(R2)
runkey, test("R2 Market leverage")

* R3 target with firm fixed effects
rebuild, target(firmfe) tag(R3)
runkey, test("R3 Firm-FE target")

* R4 deviation measured at t-1
rebuild
sort FirmID Year
foreach v in CSDP CSDN {
    qui gen double _l = L.`v'
    qui replace `v' = _l
    drop _l
}
buildint
runkey, test("R4 CSD at t-1")

* R5 Chen et al. (2011) expectation model
rebuild, expmodel(chen) tag(R5)
runkey, test("R5 Chen et al. (2011)")

* R6 cash-based investment
rebuild, invdef(cash) tag(R6)
runkey, test("R6 Cash investment (-CFI)")

* R7 alternative managerial-ability measures
rebuild
qui replace MA = MA_rank
buildint
runkey, test("R7a MA percentile rank")
rebuild
qui replace MA = MA_avg
buildint
runkey, test("R7b MA two-year average")

* R8 alternative life-cycle classifications
rebuild, lcdef(pure) tag(R8a)
runkey, test("R8a Dickinson pure stages")
rebuild, lcdef(ar) tag(R8b)
runkey, test("R8b Age-growth stages")

* R10 alternative estimators
rebuild
runkey, test("R10a Static two-way FE") static
runkey, test("R10b Difference GMM") nolevel

postclose keyres
di as res _n "T7. Robustness: key coefficients (two-sided p: * 0.10 ** 0.05 *** 0.01)"
keytable "$OUT/R_keyresults.dta" "T7_robustness"

*------------------------------------------------------------------------------
* R9 Multinomial logit on Biddle et al. (2009) quartile classes
*------------------------------------------------------------------------------
rebuild
xtile _q = InvEff if EST, nq(4)
gen byte INVCLS = 0 if inlist(_q, 2, 3)
replace  INVCLS = 1 if _q == 1
replace  INVCLS = 2 if _q == 4
label define invcls 0 "Benchmark" 1 "Under-investment" 2 "Over-investment", replace
label values INVCLS invcls
mlogit INVCLS CSDP CSDN $XCTRL i.Year i.IndID if EST, base(0) vce(cluster FirmID)
est store ML
margins, dydx(CSDP CSDN) predict(outcome(1)) post
est store ML_under
qui est restore ML
margins, dydx(CSDP CSDN) predict(outcome(2)) post
est store ML_over
esttab ML_under ML_over using "$OUT/OA5_R9_mlogit.rtf", replace b(%9.4f) se(%9.4f) ///
    star(* 0.10 ** 0.05 *** 0.01) mtitles("Pr(under-investment)" "Pr(over-investment)") ///
    title("Table OA5 (R9). Multinomial logit, average marginal effects") ///
    addnotes("Base category: benchmark (middle two quartiles of InvEff)." ///
             "H1a: dPr(under)/dCSD+ > 0; H1b: dPr(over)/dCSD- > 0. SE clustered by firm.")
