---
title: "Research Methodology"
subtitle: "The Asymmetric Impact of Managerial Ability on Investment Efficiency under Capital Structure Deviation: Evidence from Emerging Markets"
---

# 3. Research Methodology

## 3.1 Sample Selection and Data Sources

The population comprises all firms listed on the Tehran Stock Exchange (TSE) over the Iranian fiscal years 1393–1403 (11 years, approximately March 2014 to March 2025). Data for fiscal year 1392 are also collected as a base year, used only to compute variables that need prior-year values (lagged total assets, sales growth and lagged determinants). A purposive (screening) sample is drawn using the following criteria:

1. The fiscal year ends in March (end of Esfand), and the firm did not change its fiscal year during the sample period, so that all firm-years share the same macroeconomic window.
2. Banks, credit institutions, investment companies, holdings and leasing companies are excluded because their capital structure, asset composition and regulatory reporting differ fundamentally from non-financial firms (Fama & French, 1992).
3. The firm is continuously listed and has the financial and market data required to compute every model variable. Delisted firms and firms with missing data in consecutive years are removed.

Financial statement data are collected from the Codal disclosure system and the Rahavard Novin database. Market data (market value of equity) and the annual inflation rate are taken from the TSE and the Central Bank of the Islamic Republic of Iran, respectively. The final sample is a balanced panel of 299 firms: 3,289 firm-years in 1393–1403, plus 299 base-year observations from 1392 (3,588 records in total).

The raw data items are: firm age; inflation (INF); inventory (INV); intangible assets (IA); net property, plant and equipment (PPE); total assets (TA); total debt (TD); book value of equity (BV); sales; cost of goods sold (COGS); selling, general and administrative expenses (SGA); operating income (OI); financial expense (FinExp); operating, investing and financing cash flows (CFO, CFI, CFF); and market value of equity (MV). Firms are classified into industries by the TSE industry code (IndID).

Because the models use lags, the first usable year differs by step:

| Step | Needs | First usable year |
|---|---|---|
| Target leverage model (determinants at t−1) | 1392 values | 1393 |
| Invest and SalesGrowth (t) | Total assets and sales at t−1 | 1393 |
| Biddle model (SalesGrowth at t−1) and InvEff | Sales at t−2 | 1394 |
| System GMM (InvEff at t−1 plus lagged instruments) | InvEff at t−1 | 1395 |

All continuous variables are winsorized at the 1st and 99th percentiles. Winsorization is applied to ratios after they are constructed, not to raw accounting levels, so that the ratios themselves are not distorted. Estimations are performed in Stata 17.

## 3.2 Variable Measurement

### 3.2.1 Dependent variable: Investment Inefficiency (InvEff)

Following Biddle, Hilary and Verdi (2009), expected investment is modeled as a function of prior sales growth:

$$Invest_{i,t} = \alpha_0 + \alpha_1\, SalesGrowth_{i,t-1} + \varepsilon_{i,t}$$

Invest is the net increase in tangible and intangible assets scaled by lagged total assets. SalesGrowth is the percentage change in sales. The model is estimated separately for each industry-year with at least 10 observations. Cells with fewer observations are estimated by industry over all years with year dummies, so the residual does not absorb industry investment cycles or macroeconomic shocks.

InvEff is the **signed** residual. A positive value is over-investment and a negative value is under-investment; it is not converted to an absolute value. Because the dependent variable is signed, a lower InvEff means more under-investment and a higher InvEff means more over-investment. This determines the predicted signs in Section 3.3.

### 3.2.2 Independent variable: Capital Structure Deviation (CSDev)

Target leverage is estimated with the target leverage model of Synn and Williams (2015):

$$TDA_{i,t} = \beta_0 + \beta_1 IOB_{i,t-1} + \beta_2 COL_{i,t-1} + \beta_3 LTA_{i,t-1} + \beta_4 MTB_{i,t-1} + \beta_5 PROFIT_{i,t-1} + \beta_6 INDLEV_{i,t-1} + \beta_7 INF_{t-1} + \lambda_j + \mu_{i,t}$$

TDA is total debt to total assets. IOB is financial expense to total assets. COL is (inventory + net fixed assets) to total assets. LTA is the natural logarithm of total assets. MTB is market value to book value of equity. PROFIT is operating income to total assets. INDLEV is the industry median leverage, computed excluding the firm itself. INF is the annual inflation rate. λ~j~ are industry dummies.

Year dummies are deliberately not included. INF has the same value for all firms in a given year, so year dummies would absorb it completely and its coefficient could not be estimated. The equation is estimated by pooled OLS with standard errors clustered by firm. The fitted value is target leverage, constrained to [0, 1]:

$$CSDev_{i,t} = TDA_{i,t} - \widehat{TDA}^{*}_{i,t}$$

Positive CSDev denotes over-leverage and negative CSDev denotes under-leverage. To test the two directions separately, CSDev is decomposed into two non-negative magnitudes:

$$CSD^{+}_{i,t} = \max(CSDev_{i,t},\, 0) \qquad CSD^{-}_{i,t} = \max(-CSDev_{i,t},\, 0)$$

CSD⁺ measures how far an over-leveraged firm is above its target, and is zero otherwise. CSD⁻ measures how far an under-leveraged firm is below its target, and is zero otherwise. A single CSDev coefficient would force the two effects to be equal in size and opposite in sign, which is exactly what the asymmetry argument of this study questions.

### 3.2.3 Moderating variable: Firm Life Cycle (FLC)

Following Dickinson (2011), firm-years are classified by the signs of operating (CFO), investing (CFI) and financing (CFF) cash flows. Few early-stage firms are listed on the TSE, and the shake-out stage is theoretically ambiguous, so Dickinson's five stages are consolidated into three:

| Consolidated stage | Dickinson stage | CFO | CFI | CFF |
|---|---|---|---|---|
| Growth | Introduction | − | − | + |
| Growth | Growth | + | − | + |
| Maturity | Maturity | + | − | − |
| Decline | Shake-out | mixed | mixed | mixed |
| Decline | Decline | − | + | + or − |

The shake-out row covers its three patterns: (−,−,−), (+,+,+) and (+,+,−). The frequency of each original stage is reported to support the consolidation. Stage is measured at **t−1**: the classification uses the sign of CFI, which reflects investment itself, so a contemporaneous stage would be mechanically related to the dependent variable. Three indicators are created (GROW, MAT, DEC). In every model one stage is the omitted reference category, to avoid perfect collinearity with the intercept.

### 3.2.4 Moderating variable: Managerial Ability (MA)

Managerial ability follows the two-stage approach of Demerjian, Lev and McVay (2012).

1. **Stage 1, DEA.** An input-oriented, variable-returns-to-scale DEA model is estimated within each industry-year. Industry-years with fewer than 15 firms (three times the number of inputs plus outputs) are pooled within the industry across years, with values deflated by the CPI. The output is sales. The inputs are cost of goods sold, SG&A expenses, net PP&E at t−1 and intangible assets at t−1. The efficiency score (FE) lies in (0, 1].
2. **Stage 2, Tobit.** Firm efficiency is regressed on characteristics that help or hinder efficiency regardless of the manager. The model is censored from above at 1:

$$FE_{i,t} = \theta_0 + \theta_1 LTA_{i,t} + \theta_2 MarketShare_{i,t} + \theta_3 FCF^{+}_{i,t} + \theta_4 \ln(Age_{i,t}) + \nu_t + \lambda_j + \omega_{i,t}$$

FCF⁺ equals 1 when free cash flow is positive. MA is the Tobit residual ω. MA is mean-centered before it enters any interaction, so that the main effects of CSD⁺ and CSD⁻ are evaluated at the average manager.

### 3.2.5 Control variables

| Variable | Definition | Enters the InvEff models? |
|---|---|---|
| LTA | ln(total assets) | Yes |
| MTB | Market value / book value of equity | Yes |
| PROFIT | Operating income / total assets | Yes |
| FCF | Operating cash flow / total assets | Yes |
| AGE | ln(1 + firm age) | Levels equation only (see 3.6) |
| INF | Annual inflation rate | No: collinear with year dummies; enters through target leverage |
| Year, industry | Dummies | Yes |

## 3.3 Empirical Models

Each hypothesis category has its own dynamic panel model, and each hypothesis is tested on a named coefficient with a predicted sign. Because InvEff is signed, a negative coefficient means the variable pushes the firm toward under-investment and a positive coefficient means it pushes the firm toward over-investment. In all models, Controls = {LTA, MTB, PROFIT, FCF}, ν~t~ are year dummies and λ~j~ are industry dummies; Section 3.4 explains how each equation includes them.

### Model 1 — Direct effects (H1a, H1b)

$$InvEff_{i,t} = \gamma_0 + \gamma_1 InvEff_{i,t-1} + \beta_1 CSD^{+}_{i,t} + \beta_2 CSD^{-}_{i,t} + \sum_k \delta_k Controls_{k,i,t} + \nu_t + \lambda_j + \varepsilon_{i,t}$$

- **H1a:** β₁ < 0. The further a firm is above its target, the lower its investment relative to the expected level.
- **H1b:** β₂ > 0. The further a firm is below its target, the higher its investment relative to the expected level.
- **Asymmetry:** a Wald test of β₁ + β₂ = 0. Rejection means the two effects differ in size.

H1a and H1b are tested in one equation on purpose. CSD⁺ and CSD⁻ are complementary parts of the same deviation. A model containing only one of them would load the omitted part onto the intercept and the included coefficient, which is omitted-variable bias. Each hypothesis still has its own coefficient and its own test.

### Model 2a — Life cycle and over-leverage (H2a); reference stage = Maturity

$$InvEff_{i,t} = \gamma_0 + \gamma_1 InvEff_{i,t-1} + \beta_1 CSD^{+}_{i,t} + \beta_2 CSD^{-}_{i,t} + \phi_1 GROW_{i,t-1} + \phi_2 DEC_{i,t-1} + \beta_3 (CSD^{+}_{i,t} \times GROW_{i,t-1}) + \beta_4 (CSD^{+}_{i,t} \times DEC_{i,t-1}) + \sum_k \delta_k Controls_{k,i,t} + \nu_t + \lambda_j + \varepsilon_{i,t}$$

- β₁ is the effect of over-leverage in the maturity stage (expected < 0).
- **H2a:** β₃ < 0 and β₄ < 0, meaning the effect is more negative in growth and decline than in maturity. A joint Wald test of β₃ = β₄ = 0 is also reported.
- Stage-specific effects are β₁ + β₃ (growth) and β₁ + β₄ (decline), each reported with its standard error.

### Model 2b — Life cycle and under-leverage (H2b); reference stage = Growth and Decline

$$InvEff_{i,t} = \gamma_0 + \gamma_1 InvEff_{i,t-1} + \beta_1 CSD^{+}_{i,t} + \beta_2 CSD^{-}_{i,t} + \phi_1 MAT_{i,t-1} + \beta_5 (CSD^{-}_{i,t} \times MAT_{i,t-1}) + \sum_k \delta_k Controls_{k,i,t} + \nu_t + \lambda_j + \varepsilon_{i,t}$$

- β₂ is the effect of under-leverage outside maturity (expected > 0).
- **H2b:** β₅ > 0, meaning the over-investment effect is stronger in maturity. The maturity-stage effect is β₂ + β₅.

### Model 3a — Managerial ability and over-leverage (H3a)

Two-way interaction (mitigation):

$$InvEff_{i,t} = \gamma_0 + \gamma_1 InvEff_{i,t-1} + \beta_1 CSD^{+}_{i,t} + \beta_2 CSD^{-}_{i,t} + \beta_3 MA_{i,t} + \beta_4 (CSD^{+}_{i,t} \times MA_{i,t}) + \sum_k \delta_k Controls_{k,i,t} + \nu_t + \lambda_j + \varepsilon_{i,t}$$

Three-way interaction ("especially in growth and decline"), where GD = 1 for growth or decline at t−1 and 0 for maturity:

$$InvEff_{i,t} = \ldots + \beta_4 (CSD^{+} \times MA) + \phi_1 GD + \beta_5 (CSD^{+} \times GD) + \beta_6 (MA \times GD) + \beta_7 (CSD^{+} \times MA \times GD) + \ldots$$

- **H3a:** β₄ > 0. Higher ability makes the negative effect of over-leverage smaller; the effect of CSD⁺ is β₁ + β₄·MA.
- **H3a (stage):** β₇ > 0, meaning mitigation is stronger in growth and decline. Mitigation within growth and decline is β₄ + β₇.

### Model 3b — Managerial ability and under-leverage (H3b)

$$InvEff_{i,t} = \gamma_0 + \gamma_1 InvEff_{i,t-1} + \beta_1 CSD^{+}_{i,t} + \beta_2 CSD^{-}_{i,t} + \beta_3 MA_{i,t} + \beta_5 (CSD^{-}_{i,t} \times MA_{i,t}) + \sum_k \delta_k Controls_{k,i,t} + \nu_t + \lambda_j + \varepsilon_{i,t}$$

Three-way version with MAT (maturity = 1, growth/decline = 0): add MAT, CSD⁻ × MAT, MA × MAT and CSD⁻ × MA × MAT (coefficient β₈).

- **H3b:** β₅ < 0. Higher ability reduces the over-investment caused by under-leverage.
- **H3b (stage):** β₈ < 0, meaning the limiting effect is stronger in maturity.

### Summary: hypothesis → test

| Hypothesis | Model | Coefficient | Predicted sign |
|---|---|---|---|
| H1a | 1 | β₁ (CSD⁺) | − |
| H1b | 1 | β₂ (CSD⁻) | + |
| Asymmetry | 1 | β₁ + β₂ | ≠ 0 |
| H2a | 2a | β₃ (CSD⁺×GROW), β₄ (CSD⁺×DEC) | −, − |
| H2b | 2b | β₅ (CSD⁻×MAT) | + |
| H3a | 3a | β₄ (CSD⁺×MA); β₇ (CSD⁺×MA×GD) | +; + |
| H3b | 3b | β₅ (CSD⁻×MA); β₈ (CSD⁻×MA×MAT) | −; − |

As a supplementary, descriptive analysis, Models 1, 3a and 3b are also estimated separately for the growth, maturity and decline subsamples. Formal inference on stage differences comes only from the interaction terms in Models 2a, 2b, 3a and 3b. A difference between coefficients from separately estimated GMM models is not a statistical test, and stage subsamples break the panel continuity that GMM instruments require.

## 3.4 Estimation Strategy: Two-step System GMM

All models are estimated with the two-step System GMM estimator (Arellano & Bover, 1995; Blundell & Bond, 1998), implemented with xtabond2 (Roodman, 2009), with Windmeijer (2005) finite-sample corrected standard errors. Three features of the setting make static estimators inconsistent:

1. **Dynamics.** Investment behavior persists, so InvEff at t−1 enters the model. With unobserved firm effects, pooled OLS biases γ₁ upward and the within (fixed-effects) estimator biases it downward (Nickell, 1981), because T is short (about 10 effective years).
2. **Simultaneity.** Investment financed with new debt raises leverage in the same year, so CSD⁺ and CSD⁻ are jointly determined with InvEff.
3. **Endogeneity of ability.** MA is derived from same-year sales efficiency, which is itself related to investment outcomes.

System GMM stacks the first-differenced equation, instrumented with lagged levels, and the levels equation, instrumented with lagged differences. This removes the firm effect and handles the endogenous regressors.

### Treatment of each regressor

| Regressor | Treatment | Instruments in the differenced equation | Instruments in the levels equation |
|---|---|---|---|
| InvEff at t−1 | Endogenous | Levels at t−2 and t−3 | Δ at t−1 |
| CSD⁺, CSD⁻, MA | Endogenous | Levels at t−2 and t−3 | Δ at t−1 |
| All interactions containing CSD⁺, CSD⁻ or MA | Endogenous; instrumented by lags of the interaction itself | Levels at t−2 and t−3 | Δ at t−1 |
| Stage indicators (t−1) | Predetermined | Levels at t−1 and t−2 | Δ at t |
| LTA, MTB, PROFIT, FCF | Predetermined | Levels at t−1 and t−2 | Δ at t |
| Year dummies | Exogenous | Standard (IV-style) instruments | Standard instruments |
| Industry dummies, AGE | Time-invariant or deterministic | Not used | Levels equation only |

The instrument matrix is collapsed and lag depth is limited to two lags. This keeps the number of instruments below the number of firms (299), because instrument proliferation weakens the Hansen test and overfits the endogenous variables (Roodman, 2009).

### Year and industry effects

Year and industry effects are included in every equation where they can be identified. The table states how each equation handles them:

| Equation | Year effects | Industry effects | Reason |
|---|---|---|---|
| Biddle expectation model (3.2.1) | Absorbed by design | Absorbed by design | Estimated separately for each industry-year, so each cell has its own intercept and slope. Small cells, pooled by industry, include year dummies. |
| Target leverage model (3.2.2) | Not included; INF captures time variation | Industry dummies λ~j~ | INF is constant across firms within a year, so year dummies would absorb it and its coefficient could not be estimated. |
| DEA (3.2.4, stage 1) | Frontier per industry-year | Frontier per industry-year | Firms are compared only with peers in the same industry and year. |
| Tobit (3.2.4, stage 2) | Year dummies ν~t~ | Industry dummies λ~j~ | Removes efficiency differences common to a year or an industry, so MA reflects the manager rather than the setting. |
| Models 1–3b (System GMM) | Year dummies ν~t~, in both the differenced and levels equations | Industry dummies λ~j~, in the levels equation only | See below |

In the System GMM models, both sets of effects are needed for three reasons:

1. **Common shocks.** Year dummies absorb shocks that hit all TSE firms in the same year, such as currency devaluations, inflation surges, sanctions and interest-rate changes. Without them, these shocks would load onto the error, create cross-sectional correlation, and invalidate the Arellano–Bond AR(2) test (Roodman, 2009).
2. **Industry heterogeneity.** Industry dummies capture persistent industry differences in investment intensity and leverage. They are time-invariant, so the first-difference transformation removes them; they therefore enter only the levels equation, as their own instruments.
3. **Firm effects.** The firm effect η~i~, which includes the industry effect, is eliminated by differencing. The industry dummies in the levels equation make the industry part explicit.

Industry × year interaction dummies are not used. With 299 firms they would add more than a hundred instruments, which would violate the instrument-count rule in this section. Year dummies are also the reason INF and AGE cannot be GMM controls (Section 3.6).

### Specification tests reported for every model

| Test | Requirement for a valid model |
|---|---|
| Arellano–Bond AR(1) in differences | Significant (expected by construction) |
| Arellano–Bond AR(2) in differences | Not significant (p > 0.10) |
| Hansen J test of overidentifying restrictions | Not rejected (p > 0.10), and not implausibly close to 1.000 |
| Difference-in-Hansen for the levels-equation instruments | Not rejected (validates the extra System GMM moment conditions) |
| Number of instruments vs number of firms | Instruments < 299 |
| Bond (2002) bounds check | γ̂₁ lies between the fixed-effects and pooled OLS estimates of γ₁ |
| Steady-state condition | \|γ̂₁\| < 1 |

A Wald test of joint significance is reported for each model. Static fixed-effects estimates of the same models are reported alongside for transparency.

## 3.5 Econometric Treatment of Moderation

The moderation tests follow Brambor, Clark and Golder (2006) and Aiken and West (1991). In practice this means seven rules:

1. **All constituent terms are included.** Every model with A × B also contains A and B, and every three-way model contains all three main effects and all three two-way products. Omitting a constituent term biases the interaction coefficient.
2. **Centering.** MA is mean-centered before the products are formed, so β₁ and β₂ are the effects for a firm with average managerial ability. CSD⁺ and CSD⁻ are not centered, because zero has a substantive meaning: the firm is at its target.
3. **Reference categories.** Stage indicators always omit one category. The reference is stated for each model: maturity in Model 2a, growth and decline in Model 2b.
4. **Interpretation through marginal effects.** An interaction coefficient alone does not show where the effect is significant. For Models 3a and 3b, the marginal effect of CSD⁺ (or CSD⁻) on InvEff is computed over the observed range of MA, as β₁ + β₄·MA, with 95% confidence intervals from the full covariance matrix. It is plotted against MA, separately for growth/decline and maturity in the three-way models. The Johnson–Neyman region (the MA values where the effect is significant) is reported.
5. **Simple slopes.** The effect of CSD⁺ and CSD⁻ is also reported at low MA (mean − 1 SD) and high MA (mean + 1 SD).
6. **Testing differences directly.** Stage differences are tested with interaction coefficients and joint Wald tests in one pooled model, not by comparing significance across subsamples.
7. **Endogeneity of products.** Because CSD and MA are endogenous, their products are endogenous too and are instrumented with lags of the product itself (Section 3.4).

Economic significance is reported alongside statistical significance: the change in InvEff from a one-standard-deviation increase in CSD⁺ or CSD⁻, expressed as a percentage of the mean absolute investment residual, at low and high MA.

## 3.6 Pre-estimation Diagnostics, Multicollinearity and Classical Assumptions

The pre-estimation diagnostics are descriptive statistics, the Pearson correlation matrix, and the frequency of each life-cycle stage, cross-tabulated with over- versus under-leverage. The cross-tabulation shows whether each stage × direction cell has enough observations to identify the interaction terms.

### Multicollinearity

| Source | Diagnosis | Treatment |
|---|---|---|
| General | VIF on the static, main-effects version of each model | Acceptable if every VIF < 10 and the mean VIF < 5 |
| Interaction terms | High VIF between a product and its components is structural and does not bias estimates (Brambor et al., 2006) | MA centered; VIF of products not used as a criterion |
| INF in the InvEff models | Identical for all firms in a year, so perfectly collinear with year dummies | Excluded from the InvEff models; enters through target leverage |
| AGE under differencing | ΔAGE = 1 for every firm-year, so collinear with year dummies in the differenced equation | Used in the levels equation only |
| Stage indicators | Three exhaustive categories | One reference category omitted in each model |
| CSDev and its determinants | CSDev is an OLS residual, so it is orthogonal to LTA, MTB and PROFIT by construction | These variables can be controls without collinearity |
| CSD⁺ and CSD⁻ | At most one is non-zero for a firm-year, but each varies independently | Both are included; not collinear |

### Classical assumptions in the GMM setting

GMM does not assume normal or homoskedastic errors, so the relevant assumptions are the moment conditions:

| Assumption | Test | Remedy |
|---|---|---|
| No second-order serial correlation in differenced errors | Arellano–Bond AR(2) | Deeper lags as instruments |
| Instrument exogeneity | Hansen J; Difference-in-Hansen | Revise lag structure or treatment of regressors |
| Heteroskedasticity | Not required | Two-step robust estimator with Windmeijer correction |
| Cross-sectional dependence (market-wide shocks) | Pesaran CD test on static residuals | Year dummies absorb common shocks |
| Stationarity | Large N, short T (about 10 years): panel unit-root tests are not required; a Fisher-type ADF test on InvEff and CSDev is reported for completeness | — |
| Outliers | Distribution checks | 1/99 winsorization of ratios |

### Static benchmark tests

For the static fixed-effects benchmarks, the standard panel selection tests are reported: the F test (pooled vs fixed effects) and the Hausman test (fixed vs random effects). These benchmarks also provide the bounds for the Bond (2002) check on γ₁.

### Generated regressors

InvEff, CSDev and MA are estimated in first-stage regressions, so second-stage standard errors understate the true sampling uncertainty. This is acknowledged as a limitation. A firm-level bootstrap of the full procedure is reported for the main coefficients.

## 3.7 Robustness Checks

The main results are re-estimated under the following alternatives, each of which changes one element of the design:

| # | Element changed | Alternative |
|---|---|---|
| R1 | Target leverage | Synn & Williams model without IOB. Financial expense is roughly the interest rate times debt, so IOB may mechanically absorb part of actual leverage. |
| R2 | Target leverage | Market leverage, TD / (TD + market value of equity) |
| R3 | Timing of deviation | CSD⁺ and CSD⁻ at t−1 instead of t |
| R4 | Expectation model | Chen, Hope, Li and Wang (2011), which allows a different response to sales declines |
| R5 | Investment measure | Cash-based investment: −CFI / lagged total assets. This is immune to asset revaluations, which are common among TSE firms. |
| R6 | Managerial ability | Industry-year percentile rank of MA; MA averaged over t−1 and t−2 to reduce measurement noise |
| R7 | Life cycle | Dickinson's original five stages, without consolidation |
| R8 | Near-target firms | Excluding firm-years with \|CSDev\| below 0.25 standard deviations, whose over/under sign is mostly noise |
| R9 | GMM instruments | Lag depth 2–4; uncollapsed instruments where the instrument count allows |
| R10 | Estimator | Static fixed effects with firm-clustered standard errors |
| R11 | Alternative dependent variable | Multinomial logit on Biddle et al. (2009) quartile classes: under-investment, benchmark, over-investment |

# Notes for the author (remove before submission)

## Changes from the original draft

| Original draft | Revised | Reason |
|---|---|---|
| One model containing CSDev × MA | Six models (1, 2a, 2b, 3a, 3b + three-way versions) mapped to H1a–H3b | H1 and H2 had no model, and H3 could not separate H3a from H3b |
| Single CSDev term | CSD⁺ and CSD⁻ | A single slope assumes the two effects are equal and opposite, which contradicts the asymmetry argument |
| DV = Invest (raw) in the GMM equation | DV = InvEff (signed Biddle residual), as defined in 3.2.1 | The draft defined InvEff but estimated a model of raw Invest |
| "Partial adjustment model" | "Target leverage model" | The equation has no lagged leverage or adjustment speed |
| Error term μ(i, t−1) | μ(i, t) | Typo |
| INF and AGE as GMM controls | INF only in target leverage; AGE in the levels equation only | Perfect collinearity with year dummies |
| η~i~ called industry fixed effect | Firm effect (removed by GMM); industry dummies λ~j~ shown separately | Notation |
| γ₃ and γ₄ both called "primary metric" | Each coefficient has one stated role | Duplicate paragraph in the draft |
| Life cycle at t | Life cycle at t−1 | CFI enters both the stage definition and investment |
| Intangible assets in the Tobit | Removed; FCF as a positive-FCF indicator | Follows Demerjian et al. (2012); intangibles are already a DEA input |
| Subsample GMM as the test of stage effects | Pooled interaction models; subsamples descriptive only | Coefficients from separate models cannot be tested against each other, and subsamples break the panel |

## Open points to confirm

- Sample period: 1393–1403 with base year 1392. Because of lags, InvEff starts in 1394 and GMM in 1395. Sales and total assets for 1391 would let InvEff cover the full 1393–1403 period; otherwise state the effective estimation window in the text.
- The dataset has no separate capital-expenditure item, so R5 uses −CFI. Add payments for fixed assets from the cash flow statement if it can be collected.
- How many industries are there, and how many firms per industry-year? This decides whether the Biddle model and DEA are estimated per industry-year or pooled by industry.
- Frequency of Dickinson's five original stages, to justify the consolidation.
- Is MA measured at t (as written) or at t−1? Both are defensible because MA is treated as endogenous; t−1 is the safer choice.
