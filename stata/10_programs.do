*==============================================================================
* 10_programs.do  -  helper programs used by every other do-file
* (called from 00_run_all.do; can be re-run safely)
*==============================================================================

*------------------------------------------------------------------------------
* wins: winsorize (or trim) at pooled percentiles; logs cut-offs and the number
*       of values changed to the open postfile "winlog" (if any)
*------------------------------------------------------------------------------
cap program drop wins
program define wins
    syntax varlist(numeric) [, CUTS(numlist min=2 max=2) TRIM TAG(string)]
    if "`cuts'" == "" local cuts "1 99"
    gettoken lo hi : cuts
    foreach v of local varlist {
        qui _pctile `v', percentiles(`lo' `hi')
        local a = r(r1)
        local b = r(r2)
        if missing(`a', `b') continue
        qui count if `v' < `a' & !missing(`v')
        local nl = r(N)
        qui count if `v' > `b' & !missing(`v')
        local nh = r(N)
        qui count if !missing(`v')
        local nn = r(N)
        if "`trim'" == "" {
            qui replace `v' = `a' if `v' < `a' & !missing(`v')
            qui replace `v' = `b' if `v' > `b' & !missing(`v')
        }
        else {
            qui replace `v' = . if (`v' < `a' | `v' > `b') & !missing(`v')
        }
        cap post winlog ("`tag'") ("`v'") (`nn') (`a') (`b') (`nl') (`nh')
    }
end

*------------------------------------------------------------------------------
* pctrank: percentile rank in [0,1] within groups
*------------------------------------------------------------------------------
cap program drop pctrank
program define pctrank
    syntax varname, GENerate(name) BY(varlist)
    tempvar r n
    qui bys `by': egen double `r' = rank(`varlist') if !missing(`varlist')
    qui bys `by': egen `n' = count(`varlist')
    qui gen double `generate' = cond(`n' > 1, (`r' - 1) / (`n' - 1), 0.5) ///
        if !missing(`varlist')
end

*------------------------------------------------------------------------------
* cellresid: residuals of y on x estimated within each cell (industry-year);
*            cells below minobs use an industry regression with year dummies.
*            Per-cell results are posted to the open postfile "cellog" (if any).
*------------------------------------------------------------------------------
cap program drop cellresid
program define cellresid
    syntax varlist(min=2 numeric), GENerate(name) CELL(varname) ///
        FALLback(varname) MINobs(integer) [FALLFE(string)]
    gettoken y xs : varlist
    gettoken x1 : xs
    tempvar touse n r
    mark `touse'
    markout `touse' `varlist' `cell' `fallback'
    qui bys `cell': egen `n' = total(`touse')
    qui gen double `generate' = .
    qui gen byte `generate'_src = .
    qui levelsof `cell' if `touse' & `n' >= `minobs', local(cells)
    foreach c of local cells {
        qui reg `y' `xs' if `touse' & `cell' == `c'
        cap post cellog (`c') (e(N)) (_b[`x1']) (e(r2)) (1)
        qui predict double `r' if e(sample), resid
        qui replace `generate' = `r' if !missing(`r')
        qui replace `generate'_src = 1 if !missing(`r')
        drop `r'
    }
    qui levelsof `fallback' if `touse' & `n' < `minobs', local(groups)
    foreach g of local groups {
        cap qui reg `y' `xs' `fallfe' if `touse' & `fallback' == `g'
        if _rc continue
        cap post cellog (-`g') (e(N)) (_b[`x1']) (e(r2)) (2)
        qui predict double `r' if e(sample) & `n' < `minobs', resid
        qui replace `generate' = `r' if !missing(`r')
        qui replace `generate'_src = 2 if !missing(`r')
        drop `r'
    }
end

*------------------------------------------------------------------------------
* lcw: linear combination of coefficients by NAME with numeric weights
*      usage: lcw CSDP 1 CSDP_MA 0.25      returns r(est) r(se) r(df)
*------------------------------------------------------------------------------
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
    if missing(`df') local df = e(N_g) - 1
    if missing(`df') local df = e(N_clust) - 1
    if missing(`df') local df = e(N) - colsof(`b')
    return scalar est = `e'[1, 1]
    return scalar se  = sqrt(`v'[1, 1])
    return scalar df  = `df'
end

*------------------------------------------------------------------------------
* addtest: one-sided test of a directional hypothesis; stored with estadd
*   usage: addtest H1a, dir(neg) : CSDP 1
*------------------------------------------------------------------------------
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
    di as res %-10s "`namelist'" as txt " estimate = " %9.5f `est' "  se = " %9.5f `se' ///
        "  one-sided p (H: `dir') = " %6.4f `p'
end

*------------------------------------------------------------------------------
* rungmm: two-step System GMM exactly as in Section 3.8.2
*   endogenous (incl. lagged DV and products): levels $LAGE_MAIN (default t-2, t-3)
*   controls: endogenous ($CTRL_TYPE); forward orthogonal deviations if $ORTHO == 1
*   year dummies IV-style (both equations); industry dummies and ln(1+Age)
*   IV-style in the levels equation only; collapsed instruments; Windmeijer SE
*------------------------------------------------------------------------------
cap program drop rungmm
program define rungmm
    syntax , DEP(varname) ENDOG(string) [PRED(string) LAGE(string) LAGP(string) ///
        NOCOLLAPSE NOLEVEL COND(string) QUIET]
    if "`lage'" == "" local lage "$LAGE_MAIN"
    if "`lage'" == "" local lage "2 3"
    if "`lagp'" == "" local lagp "1 2"
    if `"`cond'"' == "" local cond "1"
    local coll = cond("`nocollapse'" == "", "collapse", "")
    local fod  = cond("$ORTHO" == "1", "orthogonal", "")
    local ctrl "$XCTRL"
    local lagc = cond("$CTRL_TYPE" == "endog", "`lage'", "`lagp'")
    if "`nolevel'" == "" {
        local rhs    "L.`dep' `endog' `pred' `ctrl' yd_* ind_*"
        local levopt "iv(ind_*, eq(level)) iv(lnAge, eq(level))"
        local nl     ""
    }
    else {
        local rhs    "L.`dep' `endog' `pred' `ctrl' yd_*"
        local levopt ""
        local nl     "noleveleq"
    }
    local predgmm = cond("`pred'" != "", "gmm(`pred', lag(`lagp') `coll')", "")
    local q = cond("`quiet'" != "", "quietly", "noisily")
    `q' xtabond2 `dep' `rhs' if `cond', ///
        gmm(`dep', lag(`lage') `coll') gmm(`endog', lag(`lage') `coll') ///
        gmm(`ctrl', lag(`lagc') `coll') `predgmm' iv(yd_*) `levopt' ///
        twostep robust small artests(2) `fod' `nl'
end

*------------------------------------------------------------------------------
* ivstrength: first-stage strength of the collapsed GMM instruments
*   (Bun & Windmeijer 2010 type check, one regressor at a time)
*   transformed equation: D.x on x(t-a) ... x(t-b), year dummies
*   levels equation:      x on D.x(t-a+1), year dummies
*   cluster-robust F; returns r(minF) = weakest transformed-equation F
*------------------------------------------------------------------------------
cap program drop ivstrength
program define ivstrength, rclass
    syntax varlist, LAGS(numlist min=2 max=2 integer) [POST(name)]
    local a : word 1 of `lags'
    local b : word 2 of `lags'
    local al = `a' - 1
    local minF = .
    foreach x of local varlist {
        local ins ""
        forvalues l = `a'/`b' {
            local ins "`ins' L`l'.`x'"
        }
        qui reg D.`x' `ins' yd_* if EST, vce(cluster FirmID)
        qui test `ins'
        local Fd = r(F)
        qui reg `x' L`al'D.`x' yd_* if EST, vce(cluster FirmID)
        qui test L`al'D.`x'
        local Fl = r(F)
        if "`post'" != "" post `post' ("`x'") ("`a'-`b'") (`Fd') (`Fl')
        local minF = min(`minF', `Fd')
    }
    return scalar minF = `minF'
end

*------------------------------------------------------------------------------
* gmmstats: stores AR(1), AR(2), Hansen J, Difference-in-Hansen for the
*           levels-equation instruments (xtabond2's own e(diffsargan), group
*           "GMM instruments for levels"), instrument count and firm count.
*   usage (right after rungmm): gmmstats, name(G6)
*------------------------------------------------------------------------------
cap program drop gmmstats
program define gmmstats
    syntax , NAME(name)
    tempname D
    local dh  = .
    local dhp = .
    cap matrix `D' = e(diffsargan)
    if !_rc {
        forvalues g = 1/`=colsof(`D')' {
            if "`e(diffgroup`g')'" == "GMM instruments for levels" {
                local dh  = `D'[2, `g']
                local dhp = `D'[5, `g']
            }
        }
    }
    * e(ar1p) e(ar2p) e(hansen) e(hansenp) are already stored by xtabond2
    qui estadd scalar dhansen  = `dh'
    qui estadd scalar dhansenp = `dhp'
    qui estadd scalar ninst    = e(j)
    qui estadd scalar nfirms   = e(N_g)
    est store `name'
    di as txt "  AR(1) p = " %6.4f e(ar1p) "  AR(2) p = " %6.4f e(ar2p) ///
        "  Hansen p = " %6.4f e(hansenp) "  Diff-in-Hansen (levels) p = " %6.4f `dhp' ///
        "  instruments = " e(j) "  firms = " e(N_g)
    if e(j) >= e(N_g) di as err "  WARNING: instruments >= firms (Roodman 2009a)"
end

*------------------------------------------------------------------------------
* buildint: (re)build every interaction term from CSDP CSDN MA and stage dummies
*------------------------------------------------------------------------------
cap program drop buildint
program define buildint
    foreach v in CSDP_GROW CSDP_DEC CSDN_MAT CSDP_MA CSDN_MA CSDP_GD MA_GD ///
        CSDP_MA_GD MA_MAT CSDN_MA_MAT {
        cap drop `v'
    }
    qui gen double CSDP_GROW   = CSDP * GROW
    qui gen double CSDP_DEC    = CSDP * DEC
    qui gen double CSDN_MAT    = CSDN * MAT
    qui gen double CSDP_MA     = CSDP * MA
    qui gen double CSDN_MA     = CSDN * MA
    qui gen double CSDP_GD     = CSDP * GD
    qui gen double MA_GD       = MA   * GD
    qui gen double CSDP_MA_GD  = CSDP * MA * GD
    qui gen double MA_MAT      = MA   * MAT
    qui gen double CSDN_MA_MAT = CSDN * MA * MAT
end

*------------------------------------------------------------------------------
* meplot: marginal effect of a deviation component over the observed MA range
*         (p1-p99 of MA in the estimation sample), 95% CI, Johnson-Neyman
*         region; optional split by a 0/1 stage indicator.
*   usage: meplot, x(CSDP) xma(CSDP_MA) [xg(CSDP_GD) xmag(CSDP_MA_GD)] name(..) title(..)
*------------------------------------------------------------------------------
cap program drop meplot
program define meplot
    syntax , X(string) XMA(string) NAME(string) TITLE(string) ///
        [XG(string) XMAG(string) GLAB0(string) GLAB1(string)]
    if "`glab0'" == "" local glab0 "Reference stage"
    if "`glab1'" == "" local glab1 "Comparison stage"
    qui su MA if EST, d
    local lo = r(p1)
    local hi = r(p99)
    tempname pf
    tempfile f
    postfile `pf' byte g double(m est lo hi t df) using `f'
    local G = cond("`xg'" == "", "0", "0 1")
    forvalues k = 0/60 {
        local m = `lo' + (`hi' - `lo') * `k' / 60
        foreach g of local G {
            if "`xg'" == "" lcw `x' 1 `xma' `m'
            else            lcw `x' 1 `xg' `g' `xma' `m' `xmag' `=`m' * `g''
            local cv = invttail(r(df), 0.025)
            post `pf' (`g') (`m') (r(est)) (r(est) - `cv' * r(se)) ///
                (r(est) + `cv' * r(se)) (r(est) / r(se)) (r(df))
        }
    }
    postclose `pf'
    preserve
    qui use `f', clear
    qui gen byte sig = abs(t) >= invttail(df, 0.025)
    di as res _n "Johnson-Neyman (5%): MA ranges where the effect of `x' is significant - `title'"
    foreach g of local G {
        qui sort g m
        qui gen byte st_`g' = sig & (g == `g') & (sig[_n-1] == 0 | g[_n-1] != `g' | _n == 1)
        qui gen byte en_`g' = sig & (g == `g') & (sig[_n+1] == 0 | g[_n+1] != `g' | _n == _N)
        qui levelsof m if st_`g', local(starts)
        qui levelsof m if en_`g', local(ends)
        local lab = cond(`g' == 0, "`glab0'", "`glab1'")
        if "`xg'" == "" local lab "All firms"
        if "`starts'" == "" di as txt "   `lab': not significant anywhere in the observed MA range"
        else {
            local k = 0
            foreach s of local starts {
                local ++k
                local e : word `k' of `ends'
                di as txt "   `lab': MA in [" %6.3f `s' ", " %6.3f `e' "]"
            }
        }
    }
    qui export delimited using "$OUT/`name'_grid.csv", replace
    if "`xg'" == "" {
        twoway (rarea lo hi m, color(navy%20) lw(none)) (line est m, lc(navy) lw(medthick)), ///
            yline(0, lp(dash) lc(gs8)) xtitle("Managerial ability (mean-centered)") ///
            ytitle("Marginal effect on InvEff") title("`title'", size(medsmall)) ///
            legend(off) graphregion(color(white)) note("Shaded area: 95% confidence interval.")
    }
    else {
        twoway (rarea lo hi m if g == 1, color(maroon%20) lw(none)) ///
               (line est m if g == 1, lc(maroon) lw(medthick)) ///
               (rarea lo hi m if g == 0, color(navy%20) lw(none)) ///
               (line est m if g == 0, lc(navy) lw(medthick) lp(dash)), ///
            yline(0, lp(dash) lc(gs8)) xtitle("Managerial ability (mean-centered)") ///
            ytitle("Marginal effect on InvEff") title("`title'", size(medsmall)) ///
            legend(order(2 "`glab1'" 4 "`glab0'") pos(6) rows(1)) graphregion(color(white)) ///
            note("Shaded areas: 95% confidence intervals.")
    }
    qui graph export "$OUT/`name'.png", replace width(2400)
    restore
end

*------------------------------------------------------------------------------
* wooldtest: Wooldridge (2002) test for first-order serial correlation in
*            panel residuals (as in xtserial). H0: no serial correlation.
*------------------------------------------------------------------------------
cap program drop wooldtest
program define wooldtest, rclass
    syntax varlist(min=2 numeric ts) [if]
    marksample touse
    gettoken y x : varlist
    tempvar e
    qui reg D.`y' D.(`x') if `touse', nocons vce(cluster FirmID)
    qui predict double `e' if e(sample), resid
    qui reg `e' L.`e', nocons vce(cluster FirmID)
    qui test L.`e' = -0.5
    return scalar F = r(F)
    return scalar p = r(p)
end

*------------------------------------------------------------------------------
* modwald: modified Wald test for groupwise heteroskedasticity in FE residuals
*          (Greene 2000; as in xttest3). H0: equal error variance across firms.
*------------------------------------------------------------------------------
cap program drop modwald
program define modwald, rclass
    syntax varname
    tempvar e2 s2i Ti d vi w tag
    qui gen double `e2' = `varlist'^2 if !missing(`varlist')
    qui bys FirmID: egen double `s2i' = mean(`e2')
    qui bys FirmID: egen `Ti' = count(`e2')
    qui su `e2', meanonly
    local s2 = r(mean)
    qui gen double `d' = (`e2' - `s2i')^2
    qui bys FirmID: egen double `vi' = total(`d')
    qui replace `vi' = `vi' / (`Ti' * (`Ti' - 1))
    * firms whose residual variance is (numerically) zero would divide by ~0:
    * exclude them (relative tolerance), as xttest3 does for singular groups
    qui bys FirmID: gen byte `tag' = (_n == 1) & (`Ti' > 2) & (`vi' > 1e-8 * `s2'^2)
    qui gen double `w' = (`s2i' - `s2')^2 / `vi' if `tag'
    qui su `w', meanonly
    local W = r(sum)
    qui count if `tag'
    local G = r(N)
    sort FirmID Year
    return scalar W  = `W'
    return scalar df = `G'
    return scalar p  = chi2tail(`G', `W')
end

*------------------------------------------------------------------------------
* Mata: leave-one-out median, DEA (input-oriented), Pesaran CD, permutation
*------------------------------------------------------------------------------
cap mata mata drop loo_median()
cap mata mata drop dea_score()
cap mata mata drop pesaran_cd()
cap mata mata drop permute_within()
mata:
// median of x within group g, excluding the observation itself
void loo_median(string scalar xv, string scalar gv, string scalar outv, string scalar tv)
{
    real colvector x, g, out, sel, o, idx
    real scalar i, n, m
    x = st_data(., xv, tv)
    g = st_data(., gv, tv)
    n = rows(x)
    out = J(n, 1, .)
    idx = (1::n)
    for (i = 1; i <= n; i++) {
        sel = selectindex((g :== g[i]) :& (idx :!= i))
        m = rows(sel)
        if (m > 0) {
            o = sort(x[sel], 1)
            out[i] = (o[floor((m + 1) / 2)] + o[ceil((m + 1) / 2)]) / 2
        }
    }
    st_store(., outv, tv, out)
}

// input-oriented DEA; vrs = 1 (VRS) or 0 (CRS); score in (0, 1]
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
    mx = colsum(X) :/ n; mx = mx + (mx :== 0)
    my = colsum(Y) :/ n; my = my + (my :== 0)
    X  = X :/ mx
    Y  = Y :/ my
    theta = J(n, 1, .)
    c  = (1, J(1, n, 0))
    lb = J(1, n + 1, 0)
    ub = J(1, n + 1, .)
    for (o = 1; o <= n; o++) {
        q = LinearProgram()
        q.setMaxOrMin("min")
        q.setCoefficients(c)
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

// Pesaran (2004, 2015) CD statistic from panel residuals (unbalanced-robust)
void pesaran_cd(string scalar ev, string scalar idv, string scalar tvv, string scalar touse)
{
    real colvector e, id, t, uid, ut, a, b
    real rowvector ok
    real matrix E
    real scalar N, k, i, j, S, Tij, rho, npairs, CD
    e  = st_data(., ev, touse)
    id = st_data(., idv, touse)
    t  = st_data(., tvv, touse)
    uid = uniqrows(id)
    ut  = uniqrows(t)
    E = J(rows(uid), rows(ut), .)
    for (k = 1; k <= rows(e); k++) {
        E[selectindex(uid :== id[k]), selectindex(ut :== t[k])] = e[k]
    }
    N = rows(uid); S = 0; npairs = 0
    for (i = 1; i < N; i++) {
        for (j = i + 1; j <= N; j++) {
            ok = selectindex((E[i, .] :< .) :& (E[j, .] :< .))
            Tij = cols(ok)
            if (Tij > 2) {
                a = E[i, ok]'; b = E[j, ok]'
                a = a :- mean(a); b = b :- mean(b)
                if (sum(a:^2) > 0 & sum(b:^2) > 0) {
                    rho = sum(a :* b) / sqrt(sum(a:^2) * sum(b:^2))
                    S = S + sqrt(Tij) * rho
                    npairs++
                }
            }
        }
    }
    CD = sqrt(2 / (N * (N - 1))) * S
    st_numscalar("CD_stat", CD)
    st_numscalar("CD_p", 2 * (1 - normal(abs(CD))))
    st_numscalar("CD_N", N)
}

// randomly permute x within groups g (placebo); writes to outv
void permute_within(string scalar xv, string scalar gv, string scalar outv, string scalar tv)
{
    real colvector x, g, ug, sel, out
    real scalar k
    x = st_data(., xv, tv)
    g = st_data(., gv, tv)
    out = x
    ug = uniqrows(g)
    for (k = 1; k <= rows(ug); k++) {
        sel = selectindex(g :== ug[k])
        out[sel] = x[sel[jumble(1::rows(sel))]]
    }
    st_store(., outv, tv, out)
}
end

*------------------------------------------------------------------------------
* rebuild: reload the raw panel and rebuild every variable with new options
*------------------------------------------------------------------------------
cap program drop rebuild
program define rebuild
    syntax [, *]
    qui use "$OUT/raw_panel.dta", clear
    qui xtset FirmID Year
    buildpanel, `options'
end

*------------------------------------------------------------------------------
* runkey: re-estimate Eqs. (6)-(12) and post the key coefficient of each
*         hypothesis to the open postfile "keyres".
*   static : two-way FE (reghdfe) instead of System GMM
*   other options are passed to rungmm (lage, lagp, nocollapse, nolevel, cond)
*------------------------------------------------------------------------------
cap program drop runkey
program define runkey
    syntax , TEST(string) [STATIC LAGE(string) LAGP(string) NOCOLLAPSE NOLEVEL COND(string)]
    local K6a "CSDP"
    local K6b "CSDN"
    local K6  ""
    local K7  "CSDP_GROW CSDP_DEC"
    local K8  "CSDN_MAT"
    local K9  "CSDP_MA"
    local K10 "CSDP_MA_GD"
    local K11 "CSDN_MA"
    local K12 "CSDN_MA_MAT"
    if `"`cond'"' == "" local cond "1"
    foreach m of global KEYMODELS {
        if "`static'" != "" {
            cap qui reghdfe InvEff ${E`m'} ${P`m'} $XCTRL if EST & (`cond'), ///
                absorb(FirmID Year) vce(cluster FirmID)
        }
        else {
            cap rungmm, dep(InvEff) endog(${E`m'}) pred(${P`m'}) lage(`lage') ///
                lagp(`lagp') `nocollapse' `nolevel' cond(`cond') quiet
        }
        if _rc {
            di as err "  `test', Eq. (`m'): estimation failed (rc = " _rc ")"
            continue
        }
        foreach k of local K`m' {
            local b  = _b[`k']
            local se = _se[`k']
            lcw `k' 1
            local p = 2 * ttail(r(df), abs(`b' / `se'))
            local ar2 = cond("`static'" == "", e(ar2p), .)
            local hp  = cond("`static'" == "", e(hansenp), .)
            local nj  = cond("`static'" == "", e(j), .)
            post keyres ("`test'") ("`m'") ("`k'") (`b') (`se') (`p') (`ar2') (`hp') (`nj') (e(N))
        }
    }
    di as txt "  done: `test'"
end

*------------------------------------------------------------------------------
* keytable: wide summary (rows = tests, columns = key coefficients) to Excel
*------------------------------------------------------------------------------
cap program drop keytable
program define keytable
    args dtafile sheet
    preserve
    qui use "`dtafile'", clear
    qui gen str3 stars = cond(p < 0.01, "***", cond(p < 0.05, "**", cond(p < 0.10, "*", "")))
    qui gen str24 cellv = strtrim(string(b, "%9.4f")) + stars + " (" + strtrim(string(se, "%9.4f")) + ")"
    qui gen int col = .
    local i = 0
    foreach k in CSDP CSDN CSDP_GROW CSDP_DEC CSDN_MAT CSDP_MA CSDP_MA_GD CSDN_MA CSDN_MA_MAT {
        local ++i
        qui replace col = `i' if term == "`k'"
    }
    qui gen int order = _n
    qui bys test: egen int ord = min(order)
    keep test ord col cellv
    qui reshape wide cellv, i(test ord) j(col)
    sort ord
    drop ord
    cap rename cellv1 b1_H1a_CSDP
    cap rename cellv2 b2_H1b_CSDN
    cap rename cellv3 b3_H2a_CSDPxGROW
    cap rename cellv4 b4_H2a_CSDPxDEC
    cap rename cellv5 b5_H2b_CSDNxMAT
    cap rename cellv6 b4_H3a_CSDPxMA
    cap rename cellv7 b7_H3a_CSDPxMAxGD
    cap rename cellv8 b8_H3b_CSDNxMA
    cap rename cellv9 b11_H3b_CSDNxMAxMAT
    list, noobs sep(0) abbrev(20)
    qui export excel using "$OUT/Tables.xlsx", sheet("`sheet'", replace) firstrow(variables)
    restore
end
