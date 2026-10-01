# Revised Empirical Methodology

**"The Asymmetric Impact of Managerial Ability on Investment Efficiency under Capital Structure Deviation: Evidence from Emerging Markets"**

Code: `stata/01_master_CSD_MA_InvEff.do` (main) and `python/csd_ma_pipeline.py` (Python version of the same steps, with a simulator for validation). Section numbers below match the do-file.

---

## 0. Hypotheses (unchanged)

| | Hypothesis |
|---|---|
| **H1a** | Over-leverage (positive CSD) → under-investment |
| **H1b** | Under-leverage (negative CSD) → over-investment |
| **H2a** | Over-leverage's effect on under-investment is intensified in growth and decline stages |
| **H2b** | Under-leverage's effect on over-investment is intensified in maturity stage |
| **H3a** | High managerial ability mitigates under-investment from over-leverage (especially growth/decline stages) |
| **H3b** | High managerial ability limits over-investment from under-leverage (especially maturity stage) |

---

## 1. Why the original script gives insignificant results

The problems are ordered by how much they are likely to matter. Items 1–4 alone can remove a true effect.

| # | Problem in the original code | Why it kills or biases the result | Fix |
|---|---|---|---|
| 1 | **The hypotheses are never actually tested.** The only regression is `InvEff_Abs` on `CSDev_Abs`. | H1a and H1b predict opposite-signed effects (over-leverage pushes investment **down**, under-leverage pushes it **up**). Regressing an absolute value on an absolute value pools both into one slope that cannot test either. H2 and H3 have no interaction terms anywhere. | Split CSD into two magnitudes, `CSD+ = max(CSD,0)` and `|CSD−| = max(−CSD,0)`, and use the **signed** investment residual as the DV. Each hypothesis then maps to one coefficient or one linear combination (§4). |
| 2 | **Contemporaneous CSD.** | Debt-financed investment in year *t* raises leverage in year *t*. This creates a *positive* mechanical link between over-leverage and over-investment, which is the opposite of H1a and H1b. | Measure all moderators at **t−1**: CSD, life-cycle stage, MA and controls. |
| 3 | **`IOB = FinExp/TA` in the target-leverage model.** | Interest expense ≈ rate × debt, so IOB nearly reproduces actual leverage. The fitted "target" then tracks actual leverage and the residual (CSD) is mostly noise. | Remove it. Use lagged determinants (profitability, size, MTB, tangibility, collateral, leave-one-out industry leverage) plus industry and country×year FE. |
| 4 | **Firm fixed effects in the main model.** | CSD is persistent (and highly persistent in real data). Firm FE throw away the between-firm variation, which is where "chronically over-levered" firms sit. The legacy specification also includes Age, which is perfectly collinear with firm + year FE. | Main model: industry×year FE with SEs clustered by firm. Firm FE, and a Mundlak test of within vs between, are reported as robustness. |
| 5 | **Biddle model estimated once on the pooled sample.** | The residual then contains industry and macro investment cycles, which is pure measurement error in the DV. | Estimate it by industry-year (with a minimum cell size and an industry-pooled fallback). Primary specification is the **one-step** model of Chen, Hribar & Melessa (2018, *JAR*), since a residual used as the DV is biased toward zero when the regressors are correlated with first-stage variables. |
| 6 | **Life cycle drops Introduction and Shake-out.** `drop if missing(LifeCycle)` | This loses roughly 25–40% of firm-years and widens the confidence intervals. Also, Dickinson stages use the sign of CFI, and −CFI is investment, so a contemporaneous stage is mechanically related to the DV. | Use all five Dickinson stages, measured at t−1. Robustness: an Anthony–Ramesh-type composite that does not use cash-flow signs. |
| 7 | **DEA problems.** One frontier for all industries and years. Ratio inputs scaled by TA (violates DEA convexity). Output orientation instead of input orientation. `svmat r(dearslt)` maps results back by row position, and column 1 of that matrix (in Ji & Lee's `dea`) is not θ. Tobit is censored at **0** instead of **1**. | The efficiency score may not correspond to the firm-year it is merged to, and it compares firms that do not share a technology. | Input-oriented VRS DEA in levels (CPI-deflated), solved with Mata `LinearProgram()` by industry-year and written back by observation. Tobit with `ul(1)`. MA is the industry-year percentile rank, centred. |
| 8 | **Raw levels winsorized at 5/95** (TA, Sales, CFO …) | This distorts every ratio built from those levels and cuts off the tails, which is where large deviations live. Winsorizing CFO/CFI/CFF also changes the life-cycle classification. | Winsorize **ratios** only, at 1/99. |
| 9 | **Nominal values under high inflation.** | Nominal size, sales growth and DEA inputs mix inflation with real activity across years. | Build a CPI index from `INF`; use real sales growth, real size, and real DEA inputs. |
| 10 | `INF` in the target-leverage model alongside year effects | INF is constant within country-year, so in a single-country panel it is the same as year FE. | Absorb it with country×year FE. |
| 11 | `destring _all, force` | This silently turns `Symbol` into missing. Harmless here only because `encode` ran first. | Destring numeric columns only. |
| 12 | `OverLev = CSD > 0` dummies | Firms just above or just below zero are classified by noise. | Use continuous magnitudes. A materiality band (drop \|CSD\| < 0.25 SD) is a robustness check. |

### Evidence from simulation (`python csd_ma_pipeline.py --simulate`)

I generated a 450-firm × 14-year panel with high inflation and small industry-year cells, and built in the effects that H1–H3 predict:

* The revised design **recovers H1a and H1b** (t > 10), with H2 contrasts significant in most columns.
* The **legacy specification** (contemporaneous |CSD| on |residual| with firm FE) returns b = 0.026 (p = 0.038). That is roughly a tenth of the true effect, and it would be insignificant in a smaller real sample.
* With **no effects built in** (`--null`, three seeds, 99 tests), 4.0% are significant at 5% and 10.1% at 10%. The tests have the correct size, so the redesign does not manufacture significance.
* **H3a is the weak link even when it is true.** Estimated MA correlates only 0.57 with true ability, and Dickinson stages match the true stage in 67% of firm-years. Together these shrink the CSD+ × MA interaction from 0.29 (using true MA) to 0.07 (using estimated MA). If H3a is insignificant in the real data, this measurement problem is the first explanation to rule out (see §6).

---

## 2. Variable definitions

### 2.1 Capital structure deviation (CSD)

Target: TDA<sub>it</sub> = β′X<sub>i,t−1</sub> + γ<sub>industry</sub> + δ<sub>country×year</sub> + ε<sub>it</sub>.

X = {ROA, ln real TA, (MV+TD)/TA, PPE/TA, (INV+PPE)/TA, leave-one-out industry-year mean leverage}. This is the Synn & Williams / Flannery & Rangan set without the interest-expense term.

* TDA\* = fitted value **including the fixed effects**, clipped to [0,1].
* CSD<sub>it</sub> = TDA<sub>it</sub> − TDA\*<sub>it</sub>, winsorized at 1/99.
* **POS** = max(CSD<sub>i,t−1</sub>, 0) = degree of over-leverage. **NEG** = max(−CSD<sub>i,t−1</sub>, 0) = degree of under-leverage. Both are ≥ 0.
* Robustness: (a) target with firm FE, which isolates transitory deviation; (b) market leverage TD/(TD+MV).

### 2.2 Investment inefficiency

* INVEST<sub>t</sub> = −CFI<sub>t</sub> / TA<sub>t−1</sub> by default. It is cash-based, so asset revaluations (common under emerging-market accounting rules) do not count as investment. `$INVDEF="accrual"` switches to Δ(PPE+IA)/TA<sub>t−1</sub>. `Capex` is used if present.
* Expectation model (Biddle et al. 2009), by industry-year: INVEST<sub>t</sub> = a + b·SG<sub>t−1</sub> + e. Robustness: Chen et al. (2011), which allows a different response to sales declines and was designed for emerging markets, and Richardson (2006) **without leverage**, since keeping leverage would partial out the CSD effect.
* **INVRES** = e (signed). **UnderInvest** = −e if e<0. **OverInvest** = e if e>0. **InvEff_Abs** = |e|. **INVCAT** = bottom, middle and top quartiles (Biddle classification) for the mlogit.

### 2.3 Managerial ability (Demerjian, Lev & McVay 2012)

1. DEA, input-oriented VRS, by industry-year (industry-pooled if fewer than `$MIN_DEA` firms). Output: real Sales. Inputs: real COGS, SG&A, PPE<sub>t−1</sub>, intangibles<sub>t−1</sub>.
2. Tobit (right-censored at 1): θ on ln TA, market share, positive-FCF indicator, ln(1+Age), with year and industry FE. MA = θ − fitted value.
3. **MA** = industry-year percentile rank of the residual, centred (−0.5 … +0.5), lagged one year. The rank is bounded and outlier-proof, and centring means the main effects of POS and NEG are evaluated at the median manager.
4. Robustness: z-score, two-year average rank (less noise), top-tercile dummy.

> **Data limitation:** DLM's second stage also includes segment concentration and a foreign-operations indicator. If you can get them, add them, because MA otherwise absorbs firm complexity. In thin markets, report the share of θ = 1. Above about 30% means the frontier discriminates poorly; then raise `$MIN_DEA` or pool by industry.

### 2.4 Life cycle (Dickinson 2011), measured at t−1

| CFO | CFI | CFF | Stage |
|---|---|---|---|
| − | − | + | Introduction |
| + | − | + | Growth |
| + | − | − | Maturity |
| − − − / + + + / + + − | | | Shake-out |
| − | + | ± | Decline |

H2 uses all five stages with **Maturity as the base**. H3 restricts the sample to the three stages named in the hypothesis (growth, maturity, decline) and uses GD = 1 for growth or decline, 0 for maturity.

Robustness: a composite (percentile ranks of 3-year real sales growth, firm youth, and low payout if `Div` exists), with terciles labelled growth, maturity and decline.

### 2.5 Controls (all at t−1 unless noted)
Size, MTB, ROA, CFO/TA, tangibility, loss dummy, ln(1+Age) (dropped automatically in firm-FE models), σ(CFO/TA) and σ(sales growth) over the last 5 years (at least 3 observations required). Leverage itself is **not** a control, because it is a component of CSD.

---

## 3. Panel structure, fixed effects, inference

* **Main FE:** industry×year (plus country×year in multi-country panels). This removes industry investment cycles and macro shocks while keeping the cross-firm leverage variation the theory is about.
* **One-step models** also absorb industry-specific slopes on SG<sub>t−1</sub> (`absorb(IndID#Year IndID#c.L_SG)`), which reproduces the Biddle first stage inside one regression.
* **SEs** are clustered by firm. Robustness: two-way clustering (firm and year). With fewer than 50 firms, the script runs a wild-cluster bootstrap (`boottest`, Webb weights).
* **Directional hypotheses** use one-sided p-values. State this in the paper *before* reporting, and also report the two-sided stars in the tables.
* **Sample** is held fixed across H1–H3 (`SAMPLE` flag), except that H3 restricts to growth, maturity and decline.

---

## 4. Hypothesis → model → test

DV *signed* = INVEST (one-step, primary) or INVRES (two-step). *Under* = UnderInvest subsample. *Over* = OverInvest subsample.

| Hyp | Model | Coefficient test |
|---|---|---|
| H1a | INV = β₁POS + β₂NEG + Γ′X + FE | signed: β₁ < 0; Under: β₁ > 0; mlogit: ∂Pr(Under)/∂POS > 0 |
| H1b | same | signed: β₂ > 0; Over: β₂ > 0; mlogit: ∂Pr(Over)/∂NEG > 0 |
| Asymmetry (title) | same | β₁ + β₂ = 0 (two-sided) |
| H2a | + POS×{Intro, Growth, Shake, Decline} + NEG×{…} + stage dummies (Maturity base) | signed: POS×Growth < 0, POS×Decline < 0; Under: both > 0; joint Wald |
| H2b | same | signed: NEG > 0 and NEG×Growth < 0, NEG×Decline < 0 (strongest effect in maturity); Over: same signs |
| H3a | sample G/M/D: POS, NEG, MA, GD and all two-way and three-way products | signed: POS×MA > 0; POS×MA + POS×MA×GD > 0; POS×MA×GD > 0. Under: opposite signs |
| H3b | same | signed: NEG×MA < 0 (maturity); NEG×MA×GD > 0 (mitigation weaker outside maturity). Over: same |

Interaction terms are built as explicit variables (`buildint`), so every test is a named linear combination (`lcw`). POS and NEG are not centred because 0 means "on target", which is a meaningful zero. MA is centred. VIFs are reported only for main effects; collinearity with product terms is expected and does not bias them (Brambor, Clark & Golder 2006).

**Staged approach:** Table 3 (H1) → Table 4 (H2) → Table 5 (H3) and 5b (H3 by stage), all on the same sample, so readers can see each layer separately.

---

## 5. Robustness and identification (Table 6)

| Tag | Check |
|---|---|
| CSDFE / CSDMKT | firm-FE target; market-leverage target |
| BAND | drop \|CSD<sub>t−1</sub>\| < 0.25 SD (sign-noise zone) |
| CHEN / RICH / ACCR | alternative expectation models; accrual-based investment |
| MAZ / MAAV / MAHI | z-score MA; two-year average MA; top-tercile MA dummy |
| LCAR | composite life cycle (no cash-flow signs) |
| FIRMFE / MUND | within-firm identification; Mundlak firm means (within vs between) |
| CL2 | two-way clustering |
| System GMM | `xtabond2`, POS/NEG predetermined, collapsed instruments; report AR(2), Hansen, #instruments < #groups |
| boottest / psacalc | few-cluster inference; Oster (2019) δ for omitted-variable robustness |
| Country leave-one-out | multi-country panels only |

**Economic significance** (Table 7): the effect of a 1-SD change in POS or NEG (SD computed among firms with POS>0 or NEG>0), expressed in investment units, per SD of the DV, and as a percentage of mean |InvRes|. For H3, the CSD slope is compared at the p25 and p75 manager within each stage group. In the simulation: +1 SD over-leverage reduces investment by 0.019 of assets (33% of mean inefficiency), and moving from a p25 to a p75 manager cuts the under-leverage effect in maturity by half.

**Figures:** Fig 1 shows CSD slopes by stage (H2). Fig 2 shows the marginal effect of CSD as a function of MA, comparing growth/decline with maturity (H3). Fig 3 shows predicted investment along the full CSD axis for low and high MA, which is the headline asymmetric picture.

---

## 6. Reading the results honestly: decision guide

Run `stata/01_master_CSD_MA_InvEff.do` and read section 9 (diagnostics) **before** the tables.

| Diagnostic | Red flag | Implication / action |
|---|---|---|
| D1 `xtsum CSD`: within share | < 0.3 | Firm-FE results will be weak by construction; rely on industry×year FE plus Mundlak. |
| D1 `corr(CSD, L.CSD)` | > 0.9 | CSD is close to a firm trait. Frame the paper as *persistent* deviation, or use the firm-FE target for the transitory part. |
| D2 `corr(CSD_t, ΔDebt_t)` | large positive | This confirms the contemporaneous bias; lagging is essential. |
| D3 share of fallback residuals | > 30% | Cells are too thin. Lower the industry granularity or `$MIN_CELL`. |
| D4 stage × direction cells | any cell < ~100 obs | H2/H3 contrasts are underpowered. Merge Intro into Growth and Shake-out into Maturity as a sensitivity check, or rely on the pooled GD test. |
| D5 share θ = 1 | > 30% | MA is badly measured. Use MAAV, pool frontiers by industry, or add Tobit covariates. |

**If H1 holds but H2/H3 do not**, the simulation shows this is the *expected* pattern under realistic measurement error. Before revising the theory:
1. Check power. The interaction SE is roughly the main-effect SE divided by SD(moderator) and adjusted for cell sizes. If the H3 interaction CIs include economically large values, the result is "not detected", not "rejected". Report the CIs and the economic magnitudes.
2. Reduce noise in MA: MAAV, a decile-rank version, or an alternative proxy such as an ability fixed effect for CEOs who move between firms, where data exist.
3. Use the pooled GD contrast (one interaction) instead of five stage-specific ones.

**If H1 fails in the lagged, signed, one-step design**, the leverage–investment link in your market may run through something the model does not capture, such as state-bank soft budget constraints or related-party debt. That calls for theoretical revision, for example conditioning on state ownership or bank-dependence, rather than a search for a specification that works.

**What not to do:** add specifications until something is significant. Pre-commit to the one-step signed model as primary (state this in the paper) and report every robustness column, whatever the outcome.

---

## 7. Data assumptions and limitations

* Panel: listed non-financial firms in one or more emerging markets. At least 5 consecutive years per firm are needed for the volatility controls and lags; the first usable year is a firm's 3rd. Dropping `SD_*` from `$CTRL` gains observations.
* `INF` is assumed to be a country-year CPI inflation rate. Set `$INF_SCALE` to 100 if it is in percent, 1 if in decimals.
* `IndID` should be about 10–20 industries. If industry-year cells are typically below 10 firms, use coarser industries.
* Negative-equity firms (BV ≤ 0) are excluded from estimation because the target leverage is undefined for them.
* Generated regressors (CSD, MA, INVRES) make the second-stage SEs slightly too small. For the final version, bootstrap the full pipeline by firm (wrap sections 3–13 in a `bootstrap` program), or at least report that the one-step model removes the residual-DV problem for the investment equation.
