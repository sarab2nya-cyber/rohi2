---
title: "3. Research Methodology"
subtitle: "The Asymmetric Impact of Managerial Ability on Investment Efficiency under Capital Structure Deviation: Evidence from Emerging Markets"
---

## 3.1 Sample Selection and Data

The empirical analysis uses an unbalanced panel of non-financial firms listed on the Tehran Stock Exchange (TSE) over the Iranian fiscal years 1380–1403 (approximately March 2001 to March 2025). Iran is a useful emerging-market setting for this question for three reasons. Firms rely heavily on bank debt. Inflation is high and volatile. External equity financing is costly. Together, these conditions make deviations from target leverage both frequent and costly, which gives the tests statistical power. The 24-year window covers several distinct macroeconomic regimes, including the expansion of the 1380s, the sanctions of 1390–1392 and 1397 onward, and the period of the nuclear agreement.

The sample is constructed in the following steps:

1. Start from all firm-years in the database for 1380–1403, on both the TSE and Farabourse.
2. Exclude Farabourse firms and firms whose market is not recorded, so that the sample consists of firms traded on the main exchange.
3. Exclude banks, credit institutions, insurance, leasing, investment, holding, brokerage and fund companies. Their leverage reflects regulatory capital requirements and intermediation activity rather than financing choices, and their asset structure is not comparable (Fama & French, 1992).
4. Exclude printing, retail, utilities (electricity, gas, steam and hot water) and activities auxiliary to financial intermediation, whose regulated pricing or business model makes investment and leverage not comparable with manufacturing and mining firms.
5. Exclude firm-years without financial statements in the database (before listing, after delisting, or not reported).
6. Exclude firm-years with zero or negative book equity. Leverage above one and a negative market-to-book ratio make a target capital structure undefined for these firm-years, and their investment reflects financial distress rather than financing choices.

All firms have a fiscal year ending in Esfand (March), so every firm-year shares the same macroeconomic window.

| Step | Screening criterion | Firms | Firm-years |
|---|---|---|---|
| 1 | All firm-years in the database (TSE and Farabourse), 1380–1403 | [n] | [n] |
| 2 | Less: Farabourse firms and firms with no market in the database | [−n] | [−n] |
| 3 | Less: banks, insurance, leasing, investment, holding, brokerage and fund companies | [−n] | [−n] |
| 4 | Less: printing, retail, utilities and auxiliary financial activities | [−n] | [−n] |
| | TSE non-financial firms: full panel (firms × 24 years) | [n] | [n] |
| 5 | Less: firm-years without financial statements | — | [−n] |
| 6 | Less: firm-years with zero or negative book equity | — | [−n] |
| = | Final sample (unbalanced panel, including base year 1380) | [n] | [n] |

No minimum number of years is imposed. A firm-year enters an estimation when the lagged data that the estimation requires exist; firms with a short history therefore contribute only the years for which their lags are observed. An unbalanced panel is used because requiring every firm to report in all 24 years would keep only the firms that survived the whole period. Over-leveraged firms that fell into distress or left the exchange, exactly the firms at the centre of H1a, would be removed, and so would every firm listed after 1380, including the large wave of listings after the privatisations of the late 1380s. Such a sample would be biased toward survivors (survivorship bias) and would be too small for System GMM. The forward orthogonal deviation used in the GMM estimator (Section 3.8.2) is designed for panels with gaps. As a sensitivity test (S8), the models are re-estimated on the balanced subsample of firms with usable data in every year 1393–1403.

Industries with fewer than two firms in the final sample are pooled into one category ("other industries"). Accounting data are collected from the Rahavard Novin database and cross-checked against the original filings in the Codal disclosure system. Market values of equity are computed as the year-end closing price times the number of shares, and the annual consumer-price inflation rate is obtained from the Central Bank of the Islamic Republic of Iran.

Fiscal year 1380 serves only as a base year for variables that require prior-year values. Because the investment-expectation model uses lagged sales growth and the dynamic models use the lagged dependent variable, the first year of each estimation is: target leverage model, Eq. (2), 1381; investment-expectation model, Eq. (1), 1382; dynamic models, Eqs. (6)–(12), 1383. The firm-year counts of each estimation are reported with the results.

All continuous ratios are winsorized at the 1st and 99th percentiles of their pooled distributions after construction. Raw accounting levels are not winsorized, because doing so would distort the ratios built from them. The generated measures InvEff, CSDev and MA are winsorized at the same percentiles. Expense items (cost of goods sold, SG&A and financial expense) are used in absolute value, because some databases record them with a negative sign. All estimations are performed in Stata 17.

## 3.2 Dependent Variable: Investment Inefficiency

Investment inefficiency is measured as the deviation of actual investment from the level predicted by the firm's growth opportunities (Biddle, Hilary & Verdi, 2009). Expected investment is estimated with:

$$Invest_{i,t} = \alpha_0 + \alpha_1\, SalesGrowth_{i,t-1} + \varepsilon_{i,t} \qquad (1)$$

Invest is cash investment: net cash paid in investing activities (−CFI) scaled by total assets at t−1. SalesGrowth is the annual percentage change in sales. A cash-based measure is used because TSE firms revalued property, plant and equipment on a large scale in 1398–1401. Under the accrual measure, the increase in net PPE and intangible assets, these revaluations would appear as investment although no resources were spent.

Equation (1) is estimated cross-sectionally for each industry-year with at least 10 observations, so each industry-year has its own intercept and growth sensitivity. Industry-years with fewer than 10 observations are estimated within the industry over all years with year dummies. Estimating by industry-year prevents industry investment cycles and economy-wide shocks, such as the currency crises of 1397 and 1401, from being classified as firm-level inefficiency.

The residual ε̂ is the measure of investment inefficiency, **InvEff**, and it is kept **signed**. A positive residual indicates over-investment (investment above the level justified by growth opportunities). A negative residual indicates under-investment. Unlike the absolute residual commonly used in prior work, the signed measure preserves the direction of the distortion, which is required to separate H1a from H1b. Under this convention, a regressor with a negative coefficient moves the firm toward under-investment and one with a positive coefficient moves it toward over-investment.

Two alternatives are used in the robustness tests (Section 3.11): the expectation model of Chen, Hope, Li and Wang (2011), which allows investment to respond differently to sales declines, and the accrual investment measure, [(PPE + IA)~t~ − (PPE + IA)~t−1~] / TA~t−1~.

## 3.3 Independent Variable: Capital Structure Deviation

Capital structure deviation is the distance between a firm's actual leverage and its target leverage. Trade-off theory implies that firms have a target, and the dynamic trade-off literature shows that firms drift from it and adjust only partially because adjustment is costly (Flannery & Rangan, 2006). Deviation is measured in two steps: estimating the target, then decomposing the deviation by direction.

Target leverage is estimated with the target leverage model of Synn and Williams (2015):

$$TDA_{i,t} = \beta_0 + \beta_1 IOB_{i,t-1} + \beta_2 COL_{i,t-1} + \beta_3 LTA_{i,t-1} + \beta_4 MTB_{i,t-1} + \beta_5 PROFIT_{i,t-1} + \beta_6 INDLEV_{j,t-1} + \beta_7 INF_{t-1} + \lambda_j + \mu_{i,t} \qquad (2)$$

TDA is total debt divided by total assets. The determinants are measured at t−1 so that the target is formed from information available at the start of the year:

- **IOB**: financial expense / total assets (interest burden).
- **COL**: (inventory + net PP&E) / total assets (collateral value of assets).
- **LTA**: natural logarithm of total assets in 1392 prices (size). Deflation is necessary because nominal assets grow mechanically with inflation of 30–40% a year.
- **MTB**: market value / book value of equity (growth opportunities).
- **PROFIT**: operating income / total assets (profitability).
- **INDLEV**: median TDA of the firm's industry in the same year, excluding the firm itself (industry leverage norm). Industries with fewer than five firms are pooled into one group, so that the median never rests on one or two peers.
- **INF**: annual consumer-price inflation rate.
- **λ~j~**: industry dummies.

Year dummies are not included in Eq. (2). INF takes one value per year, so year dummies would absorb it completely and make its coefficient unidentified; INF therefore carries the time variation in the target. Eq. (2) is estimated by pooled OLS with standard errors clustered by firm (Petersen, 2009). The fitted value is the target leverage, bounded to [0, 1], and the deviation is:

$$CSDev_{i,t} = TDA_{i,t} - \widehat{TDA}^{*}_{i,t} \qquad (3)$$

A positive CSDev indicates over-leverage and a negative CSDev indicates under-leverage. The hypotheses predict effects of opposite direction and possibly different size on the two sides of the target, so CSDev is decomposed into two non-negative magnitudes:

$$CSD^{+}_{i,t} = \max(CSDev_{i,t},\, 0), \qquad CSD^{-}_{i,t} = \max(-CSDev_{i,t},\, 0) \qquad (4)$$

CSD⁺ measures how far an over-leveraged firm lies above its target and is zero for under-leveraged firms. CSD⁻ measures how far an under-leveraged firm lies below its target and is zero for over-leveraged firms. This piecewise-linear specification lets the slope differ on each side of the target. A single CSDev regressor would impose equal and opposite effects, which is the restriction the asymmetry argument of this study rejects.

## 3.4 Moderating Variable: Corporate Life Cycle

Life-cycle stage is classified with the cash-flow pattern approach of Dickinson (2011). The signs of operating (CFO), investing (CFI) and financing (CFF) cash flows jointly reflect a firm's profitability, growth and financing needs, and the classification does not depend on age or size cut-offs. Dickinson's five stages are consolidated into the three stages named in the hypotheses:

| Consolidated stage | Dickinson (2011) stage | CFO | CFI | CFF |
|---|---|---|---|---|
| Growth (GROW) | Introduction | − | − | + |
| Growth (GROW) | Growth | + | − | + |
| Maturity (MAT) | Mature | + | − | − |
| Decline (DEC) | Shake-out | − − −, + + +, or + + − | | |
| Decline (DEC) | Decline | − | + | + or − |

Two features of the TSE motivate the consolidation. Few introduction-stage firms meet listing requirements, so the introduction stage is too thin to estimate separately, and introduction and growth firms share the defining feature relevant here: financing needs exceed internal cash flow. The shake-out stage has no consistent cash-flow signature (Dickinson, 2011), and its firms share the declining investment opportunities of decline-stage firms. The frequency of each original stage is reported in the descriptive statistics, and the results are re-estimated with Dickinson's original five stages (Section 3.11).

Stage is measured at **t−1**. Dickinson's classification uses the sign of CFI, and investing cash flow is a component of investment itself. A stage measured in year t would therefore be mechanically related to the dependent variable; the lagged stage is predetermined with respect to investment in year t. Three indicators are formed (GROW, MAT, DEC), and one is omitted as the reference category in each model.

## 3.5 Moderating Variable: Managerial Ability

Managerial ability is measured with the two-stage approach of Demerjian, Lev and McVay (2012). The approach separates the efficiency with which a firm converts resources into revenue into a part attributable to the firm and a part attributable to its managers.

**Stage 1: firm efficiency.** Data envelopment analysis (DEA) estimates the efficiency with which each firm converts inputs into sales, relative to the efficient frontier of its peers. The model is input-oriented with variable returns to scale. The output is sales. The inputs are cost of goods sold, selling, general and administrative expenses, net PP&E at t−1 and intangible assets at t−1. Lagged capital stocks are used because they are the resources available to managers during the year. The frontier is estimated for each industry over all sample years, with monetary values deflated to 1392 prices with the consumer price index; industries with fewer than five firms are pooled into one group. Industry-year frontiers are too small in this sample: with four inputs and few firms per industry-year, more than half of the firm-years lie on the frontier, so efficiency does not discriminate between firms. The industry frontier provides many more units than the rule of thumb of three times the number of inputs and outputs (Cooper, Seiford & Tone, 2007). Deflation makes values comparable across years under high inflation. Industry-year frontiers are reported as a sensitivity test. The efficiency score FE lies in (0, 1].

**Stage 2: removing firm-level drivers.** Firm efficiency is regressed on characteristics that make efficiency easier or harder to achieve regardless of who manages the firm:

$$FE_{i,t} = \theta_0 + \theta_1 LTA_{i,t} + \theta_2 MktShare_{i,t} + \theta_3 FCF^{+}_{i,t} + \theta_4 \ln(Age_{i,t}) + \nu_t + \lambda_j + \omega_{i,t} \qquad (5)$$

MktShare is the firm's share of industry sales. FCF⁺ equals 1 if free cash flow is positive and 0 otherwise. Eq. (5) is estimated as a Tobit model censored from above at 1, because DEA scores have a mass at the efficient frontier. Segment diversification and foreign-operations indicators in the original specification are omitted because they are not available for TSE firms. Managerial ability, **MA**, is the residual ω̂: the part of efficiency not explained by firm characteristics. MA is mean-centered before entering any interaction.

## 3.6 Control Variables

Following Biddle et al. (2009), the models control for firm characteristics that are associated with investment levels and with the accuracy of the investment-expectation model:

- **LTA**: firm size. Larger firms have better access to finance and more stable investment.
- **MTB**: growth opportunities not captured by past sales growth.
- **PROFIT**: operating income / total assets. More profitable firms can fund investment internally.
- **FCF**: operating cash flow / total assets, which captures internal funds available for investment (Jensen, 1986). Operating rather than post-investment free cash flow is used because investing cash flow is part of the dependent variable.
- **TANG**: net PP&E / total assets. Asset tangibility determines the scope for collateralised financing and the share of investment that is lumpy and irreversible.
- **LOSS**: 1 if operating income is negative, 0 otherwise. Loss firms face tighter financing constraints and are more likely to cut investment.
- **σ(CFO)**: standard deviation of CFO / TA over t−3 to t−1. Volatile operating cash flows raise the cost of external finance and make investment harder to plan.
- **σ(Sales)**: standard deviation of Sales / TA over t−3 to t−1. Volatile demand reduces the accuracy of the expectation model, Eq. (1), and therefore the size of the residual.

The control set reproduces the firm-level controls of Biddle et al. (2009) that can be built from the data available for TSE firms; Z-score, dividend payout, slack and operating cycle are not included because the required items are not available. All controls are measured at t−1, as in Biddle et al. (2009); the volatility measures use the three years ending at t−1. Current-year size and profitability are mechanically affected by the investment being explained (new assets raise total assets in the same year), so contemporaneous controls would be endogenous. All models include year dummies (ν~t~) and industry dummies (λ~j~); Section 3.8 explains how each is identified. Firm age and inflation are not used as controls in the investment models. Inflation is constant across firms within a year and is perfectly collinear with the year dummies. Age increases by exactly one each year, so its first difference is collinear with the year dummies in the differenced GMM equation. Age enters only the levels equation of the GMM system (Section 3.8), and inflation enters the analysis through the target leverage model, Eq. (2). Appendix A defines every variable.

## 3.7 Empirical Models

Each hypothesis is tested with its own dynamic panel model, and each prediction is stated as a sign restriction on a named coefficient. Because InvEff is signed, a negative coefficient indicates a shift toward under-investment and a positive coefficient a shift toward over-investment. In all equations, X is the vector of controls (LTA, MTB, PROFIT, FCF, TANG, LOSS, σ(CFO), σ(Sales)) measured at t−1, η~i~ is the unobserved firm effect, ν~t~ are year dummies, λ~j~ are industry dummies and ε is the idiosyncratic error.

**Timing.** Capital structure deviation and managerial ability enter every model at t−1, the start of the year in which the investment is made. The hypotheses concern the effect of a firm's position relative to its target on the investment decisions that follow: debt overhang (Myers, 1977) constrains the investment of a firm that is already over-leveraged, and free cash flow (Jensen, 1986) is available to the managers of a firm that is already under-leveraged. Measured in year t, the deviation would partly reflect the financing of the investment being explained: investment financed with new debt raises TDA~t~ and therefore CSD⁺~t~ in the same year, which creates a positive mechanical relation that works against H1a. The same argument applies to MA, whose DEA inputs and output (cost of goods sold, SG&A and sales) move with current-year investment. Measuring both at t−1 matches the timing of the life-cycle stage (Section 3.4) and of the controls (Section 3.6), so every explanatory variable is observed before the investment year begins. The contemporaneous specification is reported as robustness test R4.

### 3.7.1 Direct effects of capital structure deviation (H1a, H1b)

Each direct-effect hypothesis is tested in its own model. H1a is tested with:

$$InvEff_{i,t} = \gamma_0 + \gamma_1 InvEff_{i,t-1} + \beta_1 CSD^{+}_{i,t-1} + \phi\, UNDER_{i,t-1} + \delta' X_{i,t-1} + \eta_i + \nu_t + \lambda_j + \varepsilon_{i,t} \qquad (6a)$$

H1b is tested with:

$$InvEff_{i,t} = \gamma_0 + \gamma_1 InvEff_{i,t-1} + \beta_2 CSD^{-}_{i,t-1} + \phi\, OVER_{i,t-1} + \delta' X_{i,t-1} + \eta_i + \nu_t + \lambda_j + \varepsilon_{i,t} \qquad (6b)$$

UNDER (OVER) equals 1 for under-leveraged (over-leveraged) firm-years. The indicator absorbs the mean investment of firms on the other side of the target, so the slope on CSD⁺ in Eq. (6a) is identified only from over-leveraged firms, and the slope on CSD⁻ in Eq. (6b) only from under-leveraged firms. Because CSD⁺ is zero for every firm with UNDER = 1 and CSD⁻ is zero for every firm with UNDER = 0, omitting the other side's slope does not bias the tested coefficient.

H1a predicts β₁ < 0: the further a firm lies above its target, the further its investment falls below the expected level, consistent with debt overhang (Myers, 1977). H1b predicts β₂ > 0: the further a firm lies below its target, the further its investment rises above the expected level, consistent with free-cash-flow problems when debt discipline is weak (Jensen, 1986).

Asymmetry, the central claim of the study, compares the two slopes and therefore requires both in one equation:

$$InvEff_{i,t} = \gamma_0 + \gamma_1 InvEff_{i,t-1} + \beta_1 CSD^{+}_{i,t-1} + \beta_2 CSD^{-}_{i,t-1} + \delta' X_{i,t-1} + \eta_i + \nu_t + \lambda_j + \varepsilon_{i,t} \qquad (6)$$

Asymmetry is tested with a Wald test of β₁ + β₂ = 0 in Eq. (6).

### 3.7.2 Life-cycle moderation (H2a, H2b)

H2a is tested with maturity as the reference stage:

$$InvEff_{i,t} = \gamma_0 + \gamma_1 InvEff_{i,t-1} + \beta_1 CSD^{+}_{i,t-1} + \beta_2 CSD^{-}_{i,t-1} + \phi_1 GROW_{i,t-1} + \phi_2 DEC_{i,t-1} + \beta_3\, CSD^{+}_{i,t-1} \times GROW_{i,t-1} + \beta_4\, CSD^{+}_{i,t-1} \times DEC_{i,t-1} + \delta' X_{i,t-1} + \eta_i + \nu_t + \lambda_j + \varepsilon_{i,t} \qquad (7)$$

Here β₁ is the effect of over-leverage in maturity. H2a predicts β₃ < 0 and β₄ < 0, so that the effect is more negative in growth (β₁ + β₃) and in decline (β₁ + β₄) than in maturity. A joint Wald test of β₃ = β₄ = 0 is also reported.

H2b is tested with growth and decline together as the reference:

$$InvEff_{i,t} = \gamma_0 + \gamma_1 InvEff_{i,t-1} + \beta_1 CSD^{+}_{i,t-1} + \beta_2 CSD^{-}_{i,t-1} + \phi_1 MAT_{i,t-1} + \beta_5\, CSD^{-}_{i,t-1} \times MAT_{i,t-1} + \delta' X_{i,t-1} + \eta_i + \nu_t + \lambda_j + \varepsilon_{i,t} \qquad (8)$$

H2b predicts β₅ > 0: the over-investment effect of under-leverage is stronger in maturity (β₂ + β₅) than in growth and decline (β₂).

### 3.7.3 Managerial ability within the life cycle (H3a, H3b)

H3a is tested first with a two-way interaction:

$$InvEff_{i,t} = \gamma_0 + \gamma_1 InvEff_{i,t-1} + \beta_1 CSD^{+}_{i,t-1} + \beta_2 CSD^{-}_{i,t-1} + \beta_3 MA_{i,t-1} + \beta_4\, CSD^{+}_{i,t-1} \times MA_{i,t-1} + \delta' X_{i,t-1} + \eta_i + \nu_t + \lambda_j + \varepsilon_{i,t} \qquad (9)$$

The marginal effect of over-leverage is β₁ + β₄·MA. H3a predicts β₄ > 0: higher ability makes the negative effect smaller. To test "especially in growth and decline", GD (= 1 for growth or decline at t−1, 0 for maturity) is added with all lower-order terms:

$$InvEff_{i,t} = \ldots + \beta_4\, CSD^{+} \times MA + \phi\, GD + \beta_5\, CSD^{+} \times GD + \beta_6\, MA \times GD + \beta_7\, CSD^{+} \times MA \times GD + \ldots \qquad (10)$$

H3a predicts β₇ > 0: mitigation is stronger in growth and decline (β₄ + β₇) than in maturity (β₄).

H3b is tested in the same way for under-leverage:

$$InvEff_{i,t} = \gamma_0 + \gamma_1 InvEff_{i,t-1} + \beta_1 CSD^{+}_{i,t-1} + \beta_2 CSD^{-}_{i,t-1} + \beta_3 MA_{i,t-1} + \beta_8\, CSD^{-}_{i,t-1} \times MA_{i,t-1} + \delta' X_{i,t-1} + \eta_i + \nu_t + \lambda_j + \varepsilon_{i,t} \qquad (11)$$

$$InvEff_{i,t} = \ldots + \beta_8\, CSD^{-} \times MA + \phi\, MAT + \beta_9\, CSD^{-} \times MAT + \beta_{10}\, MA \times MAT + \beta_{11}\, CSD^{-} \times MA \times MAT + \ldots \qquad (12)$$

H3b predicts β₈ < 0 (higher ability reduces over-investment from under-leverage) and β₁₁ < 0 (the reduction is stronger in maturity).

### 3.7.4 Summary of predictions

| Hypothesis | Equation | Coefficient | Predicted sign |
|---|---|---|---|
| H1a | (6a) | β₁: CSD⁺ | − |
| H1b | (6b) | β₂: CSD⁻ | + |
| Asymmetry | (6) | β₁ + β₂ | ≠ 0 |
| H2a | (7) | β₃: CSD⁺ × GROW; β₄: CSD⁺ × DEC | −; − |
| H2b | (8) | β₅: CSD⁻ × MAT | + |
| H3a | (9), (10) | β₄: CSD⁺ × MA; β₇: CSD⁺ × MA × GD | +; + |
| H3b | (11), (12) | β₈: CSD⁻ × MA; β₁₁: CSD⁻ × MA × MAT | −; − |

Stage differences are inferred only from the interaction terms above. As a descriptive complement, Eqs. (6), (9) and (11) are also estimated within each stage, but these subsample estimates are not used to test H2 or H3: a difference in significance between separate regressions is not a test of a difference in effects (Gelman & Stern, 2006).

## 3.8 Identification and Estimation

### 3.8.1 Sources of endogeneity

Three sources of endogeneity make static panel estimators inconsistent in this setting (Wintoki, Linck & Netter, 2012):

1. **Dynamic dependence.** Investment distortions persist, so InvEff~t−1~ belongs in the model. With a firm effect η~i~, pooled OLS biases γ₁ upward and the within estimator biases it downward; the within bias is of order 1/T (Nickell, 1981) and is not negligible with about nine effective years.
2. **Simultaneity.** Investment financed with new debt raises leverage in the same year, so contemporaneous CSD⁺ and CSD⁻ would be jointly determined with InvEff. Measuring the deviation at t−1 removes this mechanical link (Section 3.7), but lagged deviation can still respond to past investment shocks, so it is not treated as exogenous.
3. **Unobserved heterogeneity and measurement error.** MA is constructed from sales efficiency, which shares shocks with investment, and both MA and CSDev are estimated regressors.

### 3.8.2 Two-step System GMM

Eqs. (6)–(12) are estimated with the two-step System GMM estimator (Arellano & Bover, 1995; Blundell & Bond, 1998), implemented with xtabond2 (Roodman, 2009b). Standard errors use the Windmeijer (2005) finite-sample correction. System GMM stacks a transformed equation, which removes η~i~ and is instrumented with lagged levels, and the levels equation, instrumented with lagged first differences. The transformation is the forward orthogonal deviation (Arellano & Bover, 1995): each observation is expressed as its deviation from the mean of all future observations of the same firm. The panel has gaps, because firm-years with non-positive book equity are excluded (Section 3.1). First-differencing loses two observations at every gap, while the forward orthogonal deviation loses only one and uses all available future information (Roodman, 2009b). First differences are reported as sensitivity test S9a. The levels equation is valid if changes in the instruments are uncorrelated with the firm effect. It adds information that is valuable when the series are persistent and the panel is short, in which case lagged levels are weak instruments for first differences (Blundell & Bond, 1998).

Lags in the table refer to the regressor as it enters the model; for example, the instruments of CSD⁺~t−1~ are its own values two and three periods earlier.

| Regressor | Assumption | Transformed equation: GMM-style instruments | Levels equation: instruments |
|---|---|---|---|
| InvEff~t−1~ | Endogenous | Lags 2 and 3 | Δ, lag 1 |
| CSD⁺, CSD⁻, UNDER, OVER, MA (at t−1) | Endogenous | Lags 2 and 3 | Δ, lag 1 |
| Products with CSD⁺, CSD⁻ or MA | Endogenous; instrumented by lags of the product itself | Lags 2 and 3 | Δ, lag 1 |
| Stage indicators (t−1) | Predetermined | Lags 1 and 2 | Δ, current |
| Controls (at t−1) | Endogenous | Lags 2 and 3 | Δ, lag 1 |
| Year dummies | Strictly exogenous | IV-style | IV-style |
| Industry dummies, ln(Age) | Time-invariant / deterministic trend | Not used | IV-style, levels only |

The controls are treated as endogenous rather than predetermined. Size, growth opportunities, profitability and cash flow respond to past investment shocks, so even their lagged values may be correlated with the error (Wintoki, Linck & Netter, 2012); in this sample the Hansen test also rejected the weaker predetermined assumption. The instrument matrix is collapsed and lag depth is restricted to two, so that the instrument count stays below the 299 cross-sectional units. Instrument proliferation overfits the endogenous regressors and weakens the Hansen test (Roodman, 2009a). The instrument count is reported for every model.

Restricting lag depth keeps the instrument count low but can leave the instruments weak, and weak instruments make GMM estimates imprecise and biased toward OLS (Bun & Windmeijer, 2010). Instrument strength is therefore checked before any hypothesis model is estimated. For each main regressor (CSD⁺, CSD⁻, MA), the cluster-robust first-stage F statistic of its collapsed lag instruments is computed for the transformed and levels equations. The lag window is fixed by a rule set in advance: lags 2–3 are kept unless the weakest first-stage F is below 10 (Staiger & Stock, 1997) and the window of lags 2–4 gives stronger instruments, in which case lags 2–4 are used. The F statistics and the window selected are reported in the Online Appendix (OA10). The rule depends only on the first stages, never on the hypothesis tests.

### 3.8.3 Year and industry effects

Year and industry effects enter every equation in which they are identified:

| Equation | Year effects | Industry effects |
|---|---|---|
| Expectation model, Eq. (1) | Absorbed: separate estimation for each industry-year | Absorbed: separate estimation for each industry-year |
| Target leverage, Eq. (2) | Captured by INF (year dummies would absorb INF) | Industry dummies |
| DEA frontier | Frontier per industry-year | Frontier per industry-year |
| Tobit, Eq. (5) | Year dummies | Industry dummies |
| GMM models, Eqs. (6)–(12) | Year dummies in both equations | Industry dummies in the levels equation only |

In the GMM models, year dummies absorb shocks common to all TSE firms, such as currency devaluations, sanctions and policy-rate changes. Without them, these shocks enter the error term as cross-sectional correlation, which invalidates the autocorrelation tests (Roodman, 2009b). Industry dummies are time-invariant: the forward orthogonal deviation removes them, so they enter only the levels equation. Industry × year dummies are not used because they would add more than a hundred instruments. Industries with fewer than five firms are pooled into one category for the industry dummies, because a dummy for a single-firm industry is not identified in the levels equation.

### 3.8.4 Specification tests

Every GMM model reports the following:

| Test | Requirement |
|---|---|
| Arellano–Bond AR(1) in first differences | Rejected (expected by construction) |
| Arellano–Bond AR(2) in first differences | Not rejected (p > 0.10) |
| Instrument strength (first-stage F of the main regressors) | Reported; lag window chosen by the rule in Section 3.8.2 |
| Hansen J test of over-identifying restrictions | Not rejected (p > 0.10) and not implausibly close to 1 |
| Difference-in-Hansen test of the levels-equation instruments | Not rejected |
| Instrument count | Below the number of firms |
| Bond (2002) bounds | γ̂₁ between the within and pooled-OLS estimates |
| Stability | \|γ̂₁\| < 1 |

Static two-way fixed-effects estimates of every model, with firm-clustered standard errors, are reported alongside the GMM estimates for transparency.

### 3.8.5 Reverse causality

If investment distortions move leverage away from target, rather than the reverse, the estimated β₁ and β₂ could reflect reverse causality. This is tested directly by reversing the roles of the two constructs:

$$CSDev_{i,t} = \rho_0 + \rho_1 CSDev_{i,t-1} + \theta\, InvEff_{i,t-1} + \delta' X_{i,t-1} + \eta_i + \nu_t + \varepsilon_{i,t} \qquad (13)$$

Eq. (13) is estimated with the same System GMM design. A significant θ indicates feedback from investment to leverage deviation. In that case the GMM treatment of CSD⁺ and CSD⁻ as endogenous in Eqs. (6)–(12) is necessary, and Granger-type evidence on the direction of the relation (Eq. 6 versus Eq. 13) is reported.

## 3.9 Inference on Moderation Effects

The moderation tests follow Aiken and West (1991) and Brambor, Clark and Golder (2006):

1. **Constituent terms.** Every product term is accompanied by all of its lower-order terms. In the three-way models this means all three main effects and all three two-way products.
2. **Scaling.** MA is mean-centered, so the coefficients on CSD⁺ and CSD⁻ are the effects at average managerial ability. CSD⁺ and CSD⁻ are not centered, because zero is a meaningful value: the firm is at its target.
3. **Reference categories.** One stage is omitted in every model, and the omitted stage is stated with each equation.
4. **Marginal effects.** Interaction coefficients are not interpreted in isolation. The marginal effect of CSD⁺ (or CSD⁻) on InvEff is computed across the observed range of MA, for example β₁ + β₄·MA in Eq. (9), with 95% confidence intervals from the full covariance matrix of the estimates. It is plotted against MA, separately for growth/decline and maturity in Eqs. (10) and (12). The Johnson–Neyman interval, the range of MA over which the marginal effect is significant, is reported.
5. **Common support.** Marginal effects are evaluated only within the observed range of MA in each stage, and a binned estimator is reported to check that the interaction is approximately linear (Hainmueller, Mummolo & Xu, 2019).
6. **Direct tests of differences.** Differences across stages are tested with interaction coefficients and joint Wald tests within one model, not by comparing significance across subsamples.
7. **Endogenous products.** Products of endogenous variables are endogenous; each is instrumented with lags of the product itself (Section 3.8.2).

Economic magnitude is reported alongside statistical significance: the change in InvEff associated with a one-standard-deviation increase in CSD⁺ or CSD⁻, computed at low MA (mean − 1 SD) and high MA (mean + 1 SD) and expressed as a percentage of the mean absolute investment residual.

## 3.10 Diagnostics, Multicollinearity and Model Assumptions

The descriptive analysis reports summary statistics, the Pearson and Spearman correlation matrices, the frequency of each original Dickinson stage, and a cross-tabulation of stage by deviation direction (over- versus under-leveraged). The cross-tabulation shows whether every stage × direction cell contains enough observations to identify the interaction terms.

### 3.10.1 Multicollinearity

| Source | Diagnosis | Treatment |
|---|---|---|
| Main effects | Variance inflation factors from the static, main-effects version of each model | Maximum VIF < 10 and mean VIF < 5 |
| Product terms | High VIF between a product and its components is structural and does not bias the estimates (Brambor et al., 2006) | MA centered; VIF of product terms not used as a criterion |
| INF in investment models | Perfectly collinear with year dummies | Excluded; enters through Eq. (2) |
| Age in differenced equation | ΔAge = 1 for every firm-year | Levels equation only |
| Stage indicators | Exhaustive categories | One reference category omitted |
| CSDev and controls | CSDev is an OLS residual from Eq. (2), orthogonal by construction to its determinants | LTA, MTB and PROFIT can be controls without collinearity |
| CSD⁺ and CSD⁻ | At most one is non-zero per firm-year, but each varies independently | Not collinear; both included |

### 3.10.2 Assumptions of the GMM estimator

GMM does not require normally distributed or homoskedastic errors. Its validity rests on the moment conditions, which are tested as follows:

| Assumption | Test | Response if violated |
|---|---|---|
| No second-order serial correlation in differenced errors | Arellano–Bond AR(2) | Start instruments at deeper lags |
| Instrument exogeneity | Hansen J; Difference-in-Hansen | Revise the instrument set or the assumed timing of regressors |
| Heteroskedasticity and within-firm correlation | Not required | Two-step robust covariance with Windmeijer correction |
| Cross-sectional dependence | Pesaran (2015) CD test on residuals | Year dummies absorb common shocks |
| Stationarity | With N = 299 and T ≈ 9, asymptotics run in N; Fisher-type panel unit-root tests on InvEff and CSDev are reported for completeness | — |
| Influential observations | Distribution checks | 1/99 winsorization; trimming in sensitivity tests |

### 3.10.3 Static benchmarks

For the static fixed-effects benchmarks, the F test (pooled OLS against fixed effects) and the Hausman (1978) test (random against fixed effects) are reported. The classical assumptions of the static model are also documented with the modified Wald test for groupwise heteroskedasticity, the Wooldridge (2002) test for serial correlation and the skewness–kurtosis test for normality of residuals. Violations motivate the robust two-step GMM covariance and are not required assumptions of the GMM estimator. These estimates also supply the bounds for the Bond (2002) check on γ̂₁.

### 3.10.4 Generated regressors

InvEff, CSDev and MA are estimated in first-stage models, so conventional second-stage standard errors understate sampling uncertainty (Pagan, 1984). For the main coefficients, standard errors are also computed by a firm-level cluster bootstrap that repeats the entire procedure, from Eqs. (1), (2) and (5) to the GMM models, in each replication.

## 3.11 Robustness and Sensitivity Analyses

The robustness tests replace one element of the design at a time with an accepted alternative. The sensitivity tests vary the researcher-chosen parameters of the main design. The main text reports the key coefficients (β₁, β₂, β₃, β₄, β₅, β₇, β₈, β₁₁) of every test in one summary table; the full estimates are in the Online Appendix.

### 3.11.1 Robustness: alternative measures and estimators

| # | Element replaced | Alternative |
|---|---|---|
| R1 | Target leverage | Eq. (2) without IOB, because financial expense is approximately the interest rate times debt and may mechanically absorb part of actual leverage |
| R2 | Leverage definition | Market leverage, TD / (TD + MV) |
| R3 | Target-leverage estimator | Eq. (2) with firm fixed effects, isolating transitory deviation from a firm-specific target |
| R4 | Timing of deviation and ability | CSD⁺, CSD⁻ and MA measured at t (contemporaneous) instead of t−1 |
| R5 | Expectation model | Chen et al. (2011), with an asymmetric response to sales declines |
| R6 | Investment measure | Accrual investment, [(PPE + IA)~t~ − (PPE + IA)~t−1~] / TA~t−1~, which includes asset revaluations |
| R7 | Managerial ability | Industry-year percentile rank of MA; two-year average of MA to reduce measurement error |
| R8 | Life cycle | Dickinson's original five stages; age- and growth-based classification (Anthony & Ramesh, 1992) |
| R9 | Dependent variable | Multinomial logit on the Biddle et al. (2009) quartile classes: under-investment, benchmark, over-investment |
| R10 | Estimator | Static two-way fixed effects; difference GMM |

### 3.11.2 Sensitivity: researcher-chosen parameters

| # | Parameter | Values tested |
|---|---|---|
| S1 | Winsorization | 1/99 (main); 2.5/97.5; 5/95; trimming at 1/99 |
| S2 | Minimum industry-year cell in Eq. (1) | 8, 10 (main), 15 |
| S3 | DEA specification | VRS (main) vs CRS; industry-year frontiers (at least 15 or 20 firms) instead of industry frontiers |
| S4 | GMM instrument depth | Window selected by the instrument-strength rule (main) against the other of lags 2–3 and 2–4; lags 3–4; collapsed vs uncollapsed where the count allows |
| S5 | Near-target firms | Exclude firm-years with \|CSDev\| < 0.25 SD, whose direction is mostly estimation noise |
| S6 | Crisis years | Exclude 1397–1398 (sanctions and currency crisis) and 1399 (COVID-19) |
| S7 | Industry composition | Re-estimate excluding one industry at a time |
| S8 | Sample composition | Balanced subsample: firms with usable data in every year 1393–1403, to assess survivorship effects |
| S9 | Elements of the original design | S9a: first differences instead of forward orthogonal deviations; S9b: original four controls (LTA, MTB, PROFIT, FCF); S9c: original specification as a whole (CSD and MA at t, first differences, four controls, lags 2–3) |

### 3.11.3 Additional identification checks

- **Coefficient stability.** Oster's (2019) δ is computed for β₁ and β₂, with R²max = 1.3 × R²: how strong selection on unobservables would have to be, relative to observables, to explain away the effect.
- **Placebo test.** CSDev is randomly reassigned across firms within each industry-year 1,000 times. The distribution of placebo coefficients is compared with the actual estimates.
- **Generated-regressor inference.** Firm-level cluster bootstrap of the full procedure (Section 3.10.4).

### 3.11.4 Online Appendix

| Table | Content |
|---|---|
| OA1 | Sample construction by year and industry |
| OA2 | First-stage estimates: Eq. (1) by industry-year (distribution of coefficients and R²), Eq. (2), and the Tobit model, Eq. (5) |
| OA3 | Frequency of Dickinson's five stages and stage transitions |
| OA4 | Static fixed-effects estimates of Eqs. (6)–(12), with F and Hausman tests |
| OA5 | Full estimates for R1–R10 |
| OA6 | Full estimates for S1–S9 |
| OA7 | Reverse-causality model, Eq. (13) |
| OA8 | Oster bounds, placebo distribution and bootstrap standard errors |
| OA9 | Within-stage estimates of Eqs. (6), (9) and (11) |
| OA10 | Instrument strength: first-stage F statistics of the GMM instruments and the lag window selected |

## Appendix A. Variable Definitions

Data items refer to the columns of the research dataset. Subscript t−1 denotes the prior fiscal year.

| Variable | Definition | Data items |
|---|---|---|
| Invest | −CFI~t~ / TA~t−1~ (cash investment) | CFI, TA |
| SalesGrowth | (Sales~t~ − Sales~t−1~) / Sales~t−1~ | Sales |
| InvEff | Signed residual of Eq. (1), estimated by industry-year | Invest, SalesGrowth, IndID |
| TDA | TD / TA | TD, TA |
| IOB | FinExp / TA | FinExp, TA |
| COL | (INV + PPE) / TA | INV, PPE, TA |
| LTA | ln(TA / CPI), total assets in 1392 prices | TA, INF |
| MTB | MV / BV | MV, BV |
| PROFIT | OI / TA | OI, TA |
| INDLEV | Median TDA of the industry-year, excluding the firm | TD, TA, IndID |
| INF | Annual consumer-price inflation rate | INF |
| CSDev | TDA minus fitted target leverage from Eq. (2) | — |
| CSD⁺ | max(CSDev, 0) | — |
| CSD⁻ | max(−CSDev, 0); CSD⁺ and CSD⁻ enter Eqs. (6)–(12) at t−1 | — |
| GROW, MAT, DEC | Life-cycle indicators at t−1 (Section 3.4) | CFO, CFI, CFF |
| GD | 1 if GROW or DEC at t−1, 0 if MAT | CFO, CFI, CFF |
| FE | DEA efficiency score; output Sales; inputs COGS, SGA, PPE~t−1~, IA~t−1~ | Sales, COGS, SGA, PPE, IA |
| MktShare | Sales / total industry-year sales | Sales, IndID |
| FCF⁺ | 1 if (CFO + CFI) > 0, else 0 | CFO, CFI |
| MA | Residual of the Tobit model, Eq. (5), mean-centered; enters Eqs. (9)–(12) at t−1 | — |
| FCF | CFO / TA | CFO, TA |
| TANG | PPE / TA | PPE, TA |
| LOSS | 1 if OI < 0, else 0 | OI |
| σ(CFO) | Standard deviation of CFO / TA over t−3 to t−1 | CFO, TA |
| σ(Sales) | Standard deviation of Sales / TA over t−3 to t−1 | Sales, TA |
| Age | ln(1 + firm age in years) | Age |
| CPI | Price index built from INF, base year 1392 = 1 | INF |

## References

- Aiken, L. S., & West, S. G. (1991). *Multiple regression: Testing and interpreting interactions*. Sage.
- Anthony, J. H., & Ramesh, K. (1992). Association between accounting performance measures and stock prices: A test of the life cycle hypothesis. *Journal of Accounting and Economics, 15*(2–3), 203–227.
- Arellano, M., & Bond, S. (1991). Some tests of specification for panel data: Monte Carlo evidence and an application to employment equations. *Review of Economic Studies, 58*(2), 277–297.
- Arellano, M., & Bover, O. (1995). Another look at the instrumental variable estimation of error-components models. *Journal of Econometrics, 68*(1), 29–51.
- Biddle, G. C., Hilary, G., & Verdi, R. S. (2009). How does financial reporting quality relate to investment efficiency? *Journal of Accounting and Economics, 48*(2–3), 112–131.
- Blundell, R., & Bond, S. (1998). Initial conditions and moment restrictions in dynamic panel data models. *Journal of Econometrics, 87*(1), 115–143.
- Bond, S. R. (2002). Dynamic panel data models: A guide to micro data methods and practice. *Portuguese Economic Journal, 1*(2), 141–162.
- Brambor, T., Clark, W. R., & Golder, M. (2006). Understanding interaction models: Improving empirical analyses. *Political Analysis, 14*(1), 63–82.
- Bun, M. J. G., & Windmeijer, F. (2010). The weak instrument problem of the system GMM estimator in dynamic panel data models. *Econometrics Journal, 13*(1), 95–126.
- Chen, F., Hope, O.-K., Li, Q., & Wang, X. (2011). Financial reporting quality and investment efficiency of private firms in emerging markets. *The Accounting Review, 86*(4), 1255–1288.
- Cooper, W. W., Seiford, L. M., & Tone, K. (2007). *Data envelopment analysis: A comprehensive text with models, applications, references and DEA-Solver software* (2nd ed.). Springer.
- Demerjian, P., Lev, B., & McVay, S. (2012). Quantifying managerial ability: A new measure and validity tests. *Management Science, 58*(7), 1229–1248.
- Dickinson, V. (2011). Cash flow patterns as a proxy for firm life cycle. *The Accounting Review, 86*(6), 1969–1994.
- Fama, E. F., & French, K. R. (1992). The cross-section of expected stock returns. *Journal of Finance, 47*(2), 427–465.
- Flannery, M. J., & Rangan, K. P. (2006). Partial adjustment toward target capital structures. *Journal of Financial Economics, 79*(3), 469–506.
- Gelman, A., & Stern, H. (2006). The difference between "significant" and "not significant" is not itself statistically significant. *The American Statistician, 60*(4), 328–331.
- Hainmueller, J., Mummolo, J., & Xu, Y. (2019). How much should we trust estimates from multiplicative interaction models? Simple tools to improve empirical practice. *Political Analysis, 27*(2), 163–192.
- Hausman, J. A. (1978). Specification tests in econometrics. *Econometrica, 46*(6), 1251–1271.
- Jensen, M. C. (1986). Agency costs of free cash flow, corporate finance, and takeovers. *American Economic Review, 76*(2), 323–329.
- Myers, S. C. (1977). Determinants of corporate borrowing. *Journal of Financial Economics, 5*(2), 147–175.
- Nickell, S. (1981). Biases in dynamic models with fixed effects. *Econometrica, 49*(6), 1417–1426.
- Oster, E. (2019). Unobservable selection and coefficient stability: Theory and evidence. *Journal of Business & Economic Statistics, 37*(2), 187–204.
- Pagan, A. (1984). Econometric issues in the analysis of regressions with generated regressors. *International Economic Review, 25*(1), 221–247.
- Pesaran, M. H. (2015). Testing weak cross-sectional dependence in large panels. *Econometric Reviews, 34*(6–10), 1089–1117.
- Petersen, M. A. (2009). Estimating standard errors in finance panel data sets: Comparing approaches. *Review of Financial Studies, 22*(1), 435–480.
- Roodman, D. (2009a). A note on the theme of too many instruments. *Oxford Bulletin of Economics and Statistics, 71*(1), 135–158.
- Roodman, D. (2009b). How to do xtabond2: An introduction to difference and system GMM in Stata. *Stata Journal, 9*(1), 86–136.
- Staiger, D., & Stock, J. H. (1997). Instrumental variables regression with weak instruments. *Econometrica, 65*(3), 557–586.
- Synn, C., & Williams, C. (2015). [Complete title, journal, volume and pages from your source.]
- Windmeijer, F. (2005). A finite sample correction for the variance of linear efficient two-step GMM estimators. *Journal of Econometrics, 126*(1), 25–51.
- Wintoki, M. B., Linck, J. S., & Netter, J. M. (2012). Endogeneity and the dynamics of internal corporate governance. *Journal of Financial Economics, 105*(3), 581–606.
- Wooldridge, J. M. (2002). *Econometric analysis of cross section and panel data*. MIT Press.

## Notes for the Author (remove before submission)

- Fill in the [n] counts in the sample-construction table in 3.1 from the Screening sheet of Research_Data_1380_1403.xlsx.
- Complete the Synn and Williams (2015) reference, and check every reference against the published version before submission.
- The design changes of this version (CSD and MA at t−1, forward orthogonal deviations, extended controls) were fixed before the final estimation; the earlier specification is reported in S9c. State this in the cover letter if a reviewer asks how the specification was chosen.
- Report the frequency of Dickinson's five original stages to support the consolidation in 3.4.
- Check the number of industries and firms per industry-year. This determines how many industry-years use the pooled fallback in Eq. (1) and in the DEA.
