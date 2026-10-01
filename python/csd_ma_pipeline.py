"""
Python version of stata/01_master_CSD_MA_InvEff.do (same variables, same models).

    python csd_ma_pipeline.py --data Final_Master_Data.xlsx --out output
    python csd_ma_pipeline.py --simulate --out output_sim         # planted effects
    python csd_ma_pipeline.py --simulate --null --out output_null # no effects (test size)

The simulator plants the effects predicted by H1a-H3b in a panel that looks like an
emerging-market sample (high inflation, small industry-year cells, persistent
leverage deviations). It is used to check that the pipeline recovers known effects
and that the original ("legacy") specification can miss them.

Requires: numpy pandas scipy statsmodels matplotlib openpyxl (for .xlsx).
"""
from __future__ import annotations

import argparse
import os
import warnings

import numpy as np
import pandas as pd
from scipy import optimize, stats
from scipy.optimize import linprog

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*fragmented.*")
warnings.filterwarnings("ignore", message=".*keyword-only.*")

CFG = dict(
    wcut=(0.01, 0.99),
    min_cell=10,
    min_dea=20,
    dea_vrs=True,
    inf_scale=100.0,
    invdef="cash",
)
CTRL = ["L_SIZE", "L_MTB", "L_ROA", "L_CFO_TA", "L_TANG", "L_LOSS", "LNAGE", "SD_CFO_TA", "SD_SG"]


# ----------------------------------------------------------------------------
# Utilities
# ----------------------------------------------------------------------------
def lag(df: pd.DataFrame, col: str, k: int = 1) -> pd.Series:
    """Panel lag that respects gaps (like Stata's L.), keyed on FirmID/Year."""
    src = df[["FirmID", "Year", col]].copy()
    src["Year"] = src["Year"] + k
    out = df[["FirmID", "Year"]].merge(src, on=["FirmID", "Year"], how="left")
    return pd.Series(out[col].to_numpy(), index=df.index)


def winsor(s: pd.Series, cuts=CFG["wcut"]) -> pd.Series:
    lo, hi = s.quantile(cuts[0]), s.quantile(cuts[1])
    return s.clip(lo, hi)


def pctrank(s: pd.Series, by: pd.Series) -> pd.Series:
    def f(x):
        r = x.rank(method="average")
        n = x.notna().sum()
        return (r - 1) / (n - 1) if n > 1 else x * 0 + 0.5
    return s.groupby(by).transform(f)


def demean(M: np.ndarray, groups: list[np.ndarray], tol=1e-10, maxit=2000) -> np.ndarray:
    """Alternating projections: partial out several sets of fixed effects."""
    M = M.astype(float).copy()
    if not groups:
        return M
    for _ in range(maxit):
        old = M.copy()
        for g in groups:
            cnt = np.bincount(g)
            for j in range(M.shape[1]):
                M[:, j] -= (np.bincount(g, weights=M[:, j]) / cnt)[g]
        if np.max(np.abs(M - old)) < tol:
            break
    return M


class FE:
    """OLS with absorbed fixed effects and firm-clustered SEs (reghdfe analogue)."""

    def __init__(self, df, y, xs, fe=("IndYr",), cluster="FirmID", slopes=None, cond=None):
        d = df if cond is None else df[cond]
        cols = [y] + list(xs)
        extra = []
        if slopes is not None:  # industry-specific slopes on L_SG (one-step model)
            grp, var = slopes
            for k in sorted(d[grp].dropna().unique()):
                name = f"_sl_{k}"
                extra.append(name)
        need = list(dict.fromkeys(cols + list(fe) + [cluster] + ([slopes[1], slopes[0]] if slopes else [])))
        d = d[need].dropna().copy()
        if slopes is not None:
            grp, var = slopes
            for k in sorted(d[grp].unique()):
                d[f"_sl_{k}"] = d[var] * (d[grp] == k)
            extra = [f"_sl_{k}" for k in sorted(d[grp].unique())]
        groups = [pd.factorize(d[f])[0] for f in fe]
        M = demean(d[[y] + list(xs) + extra].to_numpy(), groups)
        Y, X = M[:, 0], M[:, 1:]
        keep = np.ones(X.shape[1], bool)
        # drop columns with no within variation (collinear with FE), like reghdfe "omitted"
        for j in range(X.shape[1]):
            if np.std(X[:, j]) < 1e-12:
                keep[j] = False
        names = (list(xs) + extra)
        X = X[:, keep]
        names = [n for n, k in zip(names, keep) if k]
        XtX_inv = np.linalg.pinv(X.T @ X)
        b = XtX_inv @ X.T @ Y
        u = Y - X @ b
        cl = pd.factorize(d[cluster])[0]
        G, N, K = cl.max() + 1, len(Y), X.shape[1]
        S = np.zeros((K, K))
        Xu = X * u[:, None]
        sums = np.zeros((G, K))
        np.add.at(sums, cl, Xu)
        S = sums.T @ sums
        c = G / (G - 1) * (N - 1) / (N - K)
        V = c * XtX_inv @ S @ XtX_inv
        self.names = names
        self.b = pd.Series(b, index=names)
        self.V = pd.DataFrame(V, index=names, columns=names)
        self.se = pd.Series(np.sqrt(np.diag(V)), index=names)
        self.N, self.G, self.df = N, G, G - 1
        self.r2_within = 1 - (u @ u) / (Y @ Y)
        self.sample = d.index

    def lc(self, w: dict) -> tuple[float, float]:
        v = pd.Series(0.0, index=self.names)
        for k, x in w.items():
            v[k] = x
        return float(v @ self.b), float(np.sqrt(v @ self.V @ v))

    def onesided(self, w: dict, direction: str) -> tuple[float, float, float]:
        est, se = self.lc(w)
        t = est / se
        p = stats.t.cdf(t, self.df) if direction == "neg" else stats.t.sf(t, self.df)
        return est, se, p

    def twosided(self, k):
        t = self.b[k] / self.se[k]
        return 2 * stats.t.sf(abs(t), self.df)


# ----------------------------------------------------------------------------
# Simulated emerging-market panel with planted effects
# ----------------------------------------------------------------------------
def simulate(n_firms=450, T=14, n_ind=8, null=False, seed=7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    years = np.arange(2008, 2008 + T)
    INF = rng.uniform(8, 40, T)                     # % per year
    ind = rng.integers(1, n_ind + 1, n_firms)
    ind_lev = rng.normal(0, 0.06, n_ind + 1)
    ind_inv = rng.normal(0, 0.02, n_ind + 1)
    ind_sg = rng.uniform(0.05, 0.25, n_ind + 1)
    a_i = rng.normal(0, 1, n_firms)                 # persistent managerial talent
    mu_dev = rng.normal(0, 0.06, n_firms)           # persistent leverage deviation
    tang_i = rng.uniform(0.15, 0.6, n_firms)
    age0 = rng.integers(1, 35, n_firms)
    # stages: 1 intro 2 growth 3 mature 4 shake 5 decline
    P = np.array([[.55, .35, .05, .03, .02],
                  [.04, .62, .28, .03, .03],
                  [.01, .08, .78, .07, .06],
                  [.03, .12, .30, .45, .10],
                  [.03, .05, .15, .07, .70]])
    rows = []
    for i in range(n_firms):
        s = rng.choice(5, p=[.1, .3, .4, .1, .1]) + 1
        TA = np.exp(rng.normal(14, 1.2))
        dev = mu_dev[i]
        inv_prev, SGprev, pos_prev, neg_prev, st_prev, ma_prev = 0.05, 0.1, 0, 0, s, 0.0
        for t, y in enumerate(years):
            a = a_i[i] + rng.normal(0, 0.35)
            ma_c = stats.norm.cdf(a) - 0.5          # true ability, rank-centred
            infl = INF[t] / 100
            # --- investment planted on lagged true deviation / stage / ability
            gd = st_prev in (2, 5)
            mat = st_prev == 3
            stage_mu = {1: 0.06, 2: 0.08, 3: 0.04, 4: 0.01, 5: -0.04}[st_prev]
            base = 0.03 + ind_inv[ind[i]] + 0.15 * SGprev + stage_mu
            eff = 0.0
            if not null:
                eff += pos_prev * (-0.30 - 0.30 * gd) * (1 - 1.2 * ma_prev * (1 + 0.6 * gd))
                eff += neg_prev * (0.15 + 0.20 * mat) * (1 - 1.2 * ma_prev * (1 + 0.6 * mat))
            INVEST = base + eff + rng.normal(0, 0.05)
            # --- real growth & balance sheet
            g_real = ind_sg[ind[i]] * {1: 1.2, 2: 1.3, 3: .5, 4: 0.1, 5: -.6}[s] + rng.normal(0, .08)
            TA_new = TA * (1 + infl) * (1 + 0.5 * g_real + 0.3 * INVEST)
            COGS = 0.55 * TA_new * np.exp(rng.normal(0, .15))
            SGA = 0.10 * TA_new * np.exp(rng.normal(0, .2))
            PPE = tang_i[i] * TA_new * np.exp(rng.normal(0, .05))
            IA = 0.04 * TA_new * np.exp(rng.normal(0, .3))
            Sales = 1.6 * COGS ** .55 * SGA ** .15 * PPE ** .2 * IA ** .1 * np.exp(0.25 * a + rng.normal(0, .12))
            ROA = 0.05 + 0.02 * a + {1: -.06, 2: .02, 3: .04, 4: -.01, 5: -.05}[s] + rng.normal(0, .03)
            OI = ROA * TA_new
            MTB = np.exp(rng.normal(0.1 + 0.1 * (s == 2), 0.3))
            size = np.log(TA_new / np.prod(1 + INF[: t + 1] / 100))
            target = np.clip(0.45 + ind_lev[ind[i]] - 0.8 * ROA + 0.015 * (size - 14)
                             + 0.25 * (tang_i[i] - .35) - 0.05 * (MTB - 1.2), .05, .9)
            dev = 0.6 * (dev - mu_dev[i]) + mu_dev[i] + rng.normal(0, 0.06)
            TDA = np.clip(target + dev, 0.01, 0.97)
            TD = TDA * TA_new
            BV = TA_new - TD
            MV = BV * MTB
            cfo_mu = {1: -.04, 2: .06, 3: .09, 4: .01, 5: -.04}[s]
            cff_mu = {1: .08, 2: .05, 3: -.06, 4: -.01, 5: .0}[s]
            CFO = TA_new * (cfo_mu + 0.5 * (ROA - .05) + rng.normal(0, .03))
            CFI = -INVEST * TA
            CFF = TA_new * (cff_mu + rng.normal(0, .04))
            rows.append(dict(Symbol=f"F{i:04d}", Year=y, IndID=ind[i], TA=TA_new, TD=TD, BV=BV, PPE=PPE,
                             IA=IA, INV=0.1 * TA_new, Sales=Sales, COGS=COGS, SGA=SGA, OI=OI,
                             FinExp=0.12 * TD, CFO=CFO, CFI=CFI, CFF=CFF, MV=MV, Age=age0[i] + t,
                             INF=INF[t]))
            # state for next year (lagged drivers): use realised deviation from true target
            SGprev = g_real
            pos_prev, neg_prev = max(TDA - target, 0), max(target - TDA, 0)
            st_prev, ma_prev = s, ma_c
            s = rng.choice(5, p=P[s - 1]) + 1
            TA = TA_new
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------
# DEA (input-oriented, VRS) and Tobit (right-censored at 1)
# ----------------------------------------------------------------------------
def dea_input(X: np.ndarray, Y: np.ndarray, vrs=True) -> np.ndarray:
    X = X / np.where(X.mean(0) == 0, 1, X.mean(0))
    Y = Y / np.where(Y.mean(0) == 0, 1, Y.mean(0))
    n, m = X.shape
    s = Y.shape[1]
    out = np.full(n, np.nan)
    c = np.r_[1.0, np.zeros(n)]
    A_eq = np.r_[0.0, np.ones(n)][None, :] if vrs else None
    b_eq = np.array([1.0]) if vrs else None
    for o in range(n):
        A = np.vstack([np.c_[-X[o][:, None], X.T], np.c_[np.zeros((s, 1)), -Y.T]])
        b = np.r_[np.zeros(m), -Y[o]]
        r = linprog(c, A_ub=A, b_ub=b, A_eq=A_eq, b_eq=b_eq, bounds=(0, None), method="highs")
        if r.status == 0:
            out[o] = r.fun
    return np.minimum(out, 1.0)


def tobit_ul1(y: np.ndarray, X: np.ndarray) -> np.ndarray:
    cens = y >= 1 - 1e-9
    b0 = np.linalg.lstsq(X, y, rcond=None)[0]
    s0 = np.log(np.std(y - X @ b0) + 1e-6)

    def nll(p):
        b, ls = p[:-1], p[-1]
        sg = np.exp(ls)
        xb = X @ b
        ll = np.where(cens, stats.norm.logsf((1 - xb) / sg),
                      stats.norm.logpdf((y - xb) / sg) - ls)
        return -ll.sum()

    r = optimize.minimize(nll, np.r_[b0, s0], method="L-BFGS-B")
    return r.x[:-1]


# ----------------------------------------------------------------------------
# Pipeline
# ----------------------------------------------------------------------------
def cellresid(d: pd.DataFrame, y: str, xs: list[str], cell="IndYr", fallback="IndID") -> pd.Series:
    out = pd.Series(np.nan, index=d.index)
    ok = d[[y] + xs + [cell, fallback]].notna().all(axis=1)
    n = ok.groupby(d[cell]).transform("sum")
    for c, g in d[ok & (n >= CFG["min_cell"])].groupby(cell):
        X = np.c_[np.ones(len(g)), g[xs].to_numpy()]
        b = np.linalg.lstsq(X, g[y].to_numpy(), rcond=None)[0]
        out[g.index] = g[y].to_numpy() - X @ b
    small = ok & (n < CFG["min_cell"])
    for k in d.loc[small, fallback].unique():
        g = d[ok & (d[fallback] == k)]
        X = np.c_[np.ones(len(g)), g[xs].to_numpy(), pd.get_dummies(g["Year"], drop_first=True).to_numpy(float)]
        b = np.linalg.lstsq(X, g[y].to_numpy(), rcond=None)[0]
        res = pd.Series(g[y].to_numpy() - X @ b, index=g.index)
        idx = res.index.intersection(d.index[small])
        out[idx] = res[idx]
    return out


def build(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    d["FirmID"] = pd.factorize(d["Symbol"])[0] + 1
    if "CountryID" not in d:
        d["CountryID"] = 1
    d = d.drop_duplicates(["FirmID", "Year"]).sort_values(["FirmID", "Year"]).reset_index(drop=True)
    d = d[(d.TA > 0) & (d.Sales >= 0) & (d.TD >= 0)].reset_index(drop=True)

    cpi = (d.groupby(["CountryID", "Year"])["INF"].mean().reset_index().sort_values(["CountryID", "Year"]))
    cpi["CPI"] = cpi.groupby("CountryID")["INF"].transform(lambda x: np.exp(np.log1p(x / CFG["inf_scale"]).cumsum()))
    d = d.merge(cpi[["CountryID", "Year", "CPI"]], on=["CountryID", "Year"], how="left")
    for v in ["TA", "Sales", "COGS", "SGA", "PPE", "IA"]:
        d["r_" + v] = d[v] / d["CPI"]

    d["TDA"] = d.TD / d.TA
    d["MLEV"] = d.TD / (d.TD + d.MV)
    d["SIZE"] = np.log(d.r_TA)
    d["MTB"] = (d.MV + d.TD) / d.TA
    d["ROA"] = d.OI / d.TA
    d["TANG"] = d.PPE / d.TA
    d["COL"] = (d.INV + d.PPE) / d.TA
    d["CFO_TA"] = d.CFO / d.TA
    d["LOSS"] = (d.OI < 0).astype(float)
    d["LNAGE"] = np.log1p(d.Age)
    d["SG"] = d.r_Sales / lag(d, "r_Sales") - 1
    d["INV_CASH"] = -d.CFI / lag(d, "TA")
    d["INV_ACC"] = ((d.PPE + d.IA) - (lag(d, "PPE") + lag(d, "IA"))) / lag(d, "TA")
    d["INVEST"] = d["INV_CASH"] if CFG["invdef"] == "cash" else d["INV_ACC"]
    for v in ["CFO_TA", "SG"]:
        L = pd.concat([d[v]] + [lag(d, v, k) for k in range(1, 5)], axis=1)
        d["SD_" + v] = L.std(axis=1).where(L.notna().sum(axis=1) >= 3)
    for v in ["TDA", "MLEV", "MTB", "ROA", "TANG", "COL", "CFO_TA", "SG", "INV_CASH", "INV_ACC",
              "INVEST", "SD_CFO_TA", "SD_SG"]:
        d[v] = winsor(d[v])
    g = d.groupby(["IndID", "Year"])["TDA"]
    s, c = g.transform("sum"), g.transform("count")
    d["INDLEV"] = (s - d.TDA.fillna(0)) / (c - d.TDA.notna())
    for v in ["ROA", "SIZE", "MTB", "TANG", "COL", "INDLEV", "CFO_TA", "LOSS", "SG", "INVEST"]:
        d["L_" + v] = lag(d, v)
    d["IndYr"] = d.groupby(["IndID", "Year"]).ngroup()
    d["CtyYr"] = d.groupby(["CountryID", "Year"]).ngroup()

    # --- 3. CSD: target with lagged determinants + industry & country-year FE
    xs = ["L_ROA", "L_SIZE", "L_MTB", "L_TANG", "L_COL", "L_INDLEV"]

    def target(dep, fe):
        dd = d[[dep] + xs + fe].dropna()
        groups = [pd.factorize(dd[f])[0] for f in fe]
        M = demean(dd[[dep] + xs].to_numpy(), groups)
        b = np.linalg.lstsq(M[:, 1:], M[:, 0], rcond=None)[0]
        fitted = dd[dep].to_numpy() - (M[:, 0] - M[:, 1:] @ b)  # xb + FE
        return pd.Series(np.clip(fitted, 0, 1), index=dd.index)

    d["TDA_HAT"] = target("TDA", ["IndID", "CtyYr"])
    d["CSD"] = winsor(d.TDA - d.TDA_HAT)
    d["CSD_FE"] = winsor(d.TDA - target("TDA", ["FirmID", "CtyYr"]))
    d["CSD_MKT"] = winsor(d.MLEV - target("MLEV", ["IndID", "CtyYr"]))
    for sfx in ["", "_FE", "_MKT"]:
        d["CSDPOS" + sfx] = d["CSD" + sfx].clip(lower=0)
        d["CSDNEG" + sfx] = (-d["CSD" + sfx]).clip(lower=0)
        d["POS" + sfx] = lag(d, "CSDPOS" + sfx)
        d["NEG" + sfx] = lag(d, "CSDNEG" + sfx)
    d["CSD_L"] = lag(d, "CSD")
    d["OVERLEV_L"] = (d.CSD_L > 0).where(d.CSD_L.notna())

    # --- 4. investment residuals
    d["L_SG"] = lag(d, "SG")
    d["RES_B"] = winsor(cellresid(d, "INVEST", ["L_SG"]))
    d["NEGSG"] = (d.L_SG < 0).astype(float).where(d.L_SG.notna())
    d["NEGxSG"] = d.NEGSG * d.L_SG
    d["RES_C"] = winsor(cellresid(d, "INVEST", ["NEGSG", "L_SG", "NEGxSG"]))
    d["RES_R"] = winsor(cellresid(d, "INVEST", ["L_MTB", "L_SIZE", "L_CFO_TA", "L_INVEST", "LNAGE"]))
    d["INVRES"] = d.RES_B
    d["INVEFF_ABS"] = d.INVRES.abs()
    d["UNDERINV"] = (-d.INVRES).where(d.INVRES < 0)
    d["OVERINV"] = d.INVRES.where(d.INVRES > 0)
    q = d.INVRES.quantile([.25, .75])
    d["INVCAT"] = np.select([d.INVRES <= q[.25], d.INVRES >= q[.75]], [1, 2], 0)
    d.loc[d.INVRES.isna(), "INVCAT"] = np.nan

    # --- 5. Dickinson life cycle (all 8 patterns), at t-1
    o, i_, f = d.CFO > 0, d.CFI > 0, d.CFF > 0
    d["LC"] = np.select(
        [~o & ~i_ & f, o & ~i_ & f, o & ~i_ & ~f, (~o & ~i_ & ~f) | (o & i_), ~o & i_],
        [1, 2, 3, 4, 5], np.nan)
    d.loc[d[["CFO", "CFI", "CFF"]].isna().any(axis=1), "LC"] = np.nan
    d["LC_L"] = lag(d, "LC")
    for k, nm in zip([1, 2, 3, 4, 5], ["INTRO", "GROW", "MATU", "SHAKE", "DECL"]):
        d[nm] = (d.LC_L == k).astype(float).where(d.LC_L.notna())
    d["GD"] = ((d.GROW == 1) | (d.DECL == 1)).astype(float).where(d.LC_L.notna())
    d["GMD"] = d.LC_L.isin([2, 3, 5])

    # --- 6. managerial ability (DEA by industry-year, Tobit, rank)
    d["DEA_X3"], d["DEA_X4"] = lag(d, "r_PPE"), lag(d, "r_IA")
    inp = ["r_COGS", "r_SGA", "DEA_X3", "DEA_X4"]
    ok = d[inp + ["r_Sales"]].notna().all(axis=1) & (d.r_Sales > 0) & (d[inp] >= 0).all(axis=1)
    n = ok.groupby(d.IndYr).transform("sum")
    d["DEA_CELL"] = np.where(n >= CFG["min_dea"], d.IndYr, -d.IndID)
    d["FE_SCORE"] = np.nan
    for c, g in d[ok].groupby("DEA_CELL"):
        d.loc[g.index, "FE_SCORE"] = dea_input(g[inp].to_numpy(), g[["r_Sales"]].to_numpy(), CFG["dea_vrs"])
    d["MKTSH"] = d.r_Sales / d.groupby("IndYr").r_Sales.transform("sum")
    d["POSFCF"] = ((d.CFO + d.CFI) > 0).astype(float)
    tv = ["SIZE", "MKTSH", "POSFCF", "LNAGE"]
    tt = d[["FE_SCORE"] + tv + ["Year", "IndID"]].dropna()
    Xt = np.c_[np.ones(len(tt)), tt[tv].to_numpy(),
               pd.get_dummies(tt.Year, drop_first=True).to_numpy(float),
               pd.get_dummies(tt.IndID, drop_first=True).to_numpy(float)]
    bt = tobit_ul1(tt.FE_SCORE.to_numpy(), Xt)
    d.loc[tt.index, "MA_RAW"] = tt.FE_SCORE.to_numpy() - Xt @ bt
    d["MA_RANK"] = pctrank(d.MA_RAW, d.IndYr)
    d["MA_C"] = d.MA_RANK - 0.5
    d["MA_Z"] = (d.MA_RAW - d.MA_RAW.mean()) / d.MA_RAW.std()
    d["MA"] = lag(d, "MA_C")
    d["MA_ZL"] = lag(d, "MA_Z")
    d["MA_AV"] = (lag(d, "MA_C") + lag(d, "MA_C", 2)) / 2
    d["L_LOSS"] = lag(d, "LOSS")
    buildint(d)
    d["SAMPLE"] = d[["INVEST", "INVRES", "POS", "NEG", "LC_L", "MA", "L_SG"] + CTRL].notna().all(axis=1) & (d.BV > 0)
    return d


def buildint(d):
    for s in ["INTRO", "GROW", "SHAKE", "DECL"]:
        d["POS_" + s] = d.POS * d[s]
        d["NEG_" + s] = d.NEG * d[s]
    d["POS_MA"], d["NEG_MA"] = d.POS * d.MA, d.NEG * d.MA
    d["POS_GD"], d["NEG_GD"], d["MA_GD"] = d.POS * d.GD, d.NEG * d.GD, d.MA * d.GD
    d["POS_MA_GD"], d["NEG_MA_GD"] = d.POS * d.MA * d.GD, d.NEG * d.MA * d.GD


H2X = ["POS", "NEG", "POS_INTRO", "POS_GROW", "POS_SHAKE", "POS_DECL",
       "NEG_INTRO", "NEG_GROW", "NEG_SHAKE", "NEG_DECL", "INTRO", "GROW", "SHAKE", "DECL"]
H3X = ["POS", "NEG", "MA", "GD", "POS_MA", "NEG_MA", "POS_GD", "NEG_GD", "MA_GD", "POS_MA_GD", "NEG_MA_GD"]
FE1 = ("IndYr", "CtyYr")


def star(p):
    return "***" if p < .01 else "**" if p < .05 else "*" if p < .10 else ""


def run_all(d: pd.DataFrame, out: str) -> pd.DataFrame:
    os.makedirs(out, exist_ok=True)
    S = d.SAMPLE
    rows = []

    def rec(h, model, m, w, direction, label):
        est, se, p = m.onesided(w, direction)
        rows.append(dict(hyp=h, model=model, test=label, predicted=("<0" if direction == "neg" else ">0"),
                         est=est, se=se, p_one_sided=p, sig=star(p), N=m.N, firms=m.G))

    # ---------------- H1
    m1 = FE(d, "INVEST", ["POS", "NEG"] + CTRL, fe=FE1, slopes=("IndID", "L_SG"), cond=S)
    m2 = FE(d, "INVRES", ["POS", "NEG"] + CTRL, fe=FE1, cond=S)
    m3 = FE(d, "UNDERINV", ["POS", "NEG"] + CTRL, fe=FE1, cond=S & (d.INVRES < 0))
    m4 = FE(d, "OVERINV", ["POS", "NEG"] + CTRL, fe=FE1, cond=S & (d.INVRES > 0))
    for nm, m in [("1-step INVEST", m1), ("2-step INVRES", m2)]:
        rec("H1a", nm, m, {"POS": 1}, "neg", "b(CSD+)")
        rec("H1b", nm, m, {"NEG": 1}, "pos", "b(|CSD-|)")
    rec("H1a", "UnderInv subsample", m3, {"POS": 1}, "pos", "b(CSD+)")
    rec("H1b", "OverInv subsample", m4, {"NEG": 1}, "pos", "b(|CSD-|)")
    est, se = m2.lc({"POS": 1, "NEG": 1})
    rows.append(dict(hyp="Asym", model="2-step INVRES", test="b(CSD+)+b(|CSD-|)=0 (two-sided)",
                     predicted="!=0", est=est, se=se, p_one_sided=2 * stats.t.sf(abs(est / se), m2.df),
                     sig=star(2 * stats.t.sf(abs(est / se), m2.df)), N=m2.N, firms=m2.G))

    # ---------------- H2
    h2 = {}
    for nm, dv, cond, sl in [("1-step INVEST", "INVEST", S, ("IndID", "L_SG")),
                             ("2-step INVRES", "INVRES", S, None),
                             ("UnderInv subsample", "UNDERINV", S & (d.INVRES < 0), None),
                             ("OverInv subsample", "OVERINV", S & (d.INVRES > 0), None)]:
        m = FE(d, dv, H2X + CTRL, fe=FE1, cond=cond, slopes=sl)
        h2[nm] = m
        if dv in ("INVEST", "INVRES"):
            rec("H2a", nm, m, {"POS_GROW": 1}, "neg", "CSD+ x Growth (vs Maturity)")
            rec("H2a", nm, m, {"POS_DECL": 1}, "neg", "CSD+ x Decline (vs Maturity)")
            rec("H2b", nm, m, {"NEG_GROW": 1}, "neg", "|CSD-| x Growth (Maturity stronger)")
            rec("H2b", nm, m, {"NEG_DECL": 1}, "neg", "|CSD-| x Decline (Maturity stronger)")
        elif dv == "UNDERINV":
            rec("H2a", nm, m, {"POS_GROW": 1}, "pos", "CSD+ x Growth (vs Maturity)")
            rec("H2a", nm, m, {"POS_DECL": 1}, "pos", "CSD+ x Decline (vs Maturity)")
        else:
            rec("H2b", nm, m, {"NEG_GROW": 1}, "neg", "|CSD-| x Growth (Maturity stronger)")
            rec("H2b", nm, m, {"NEG_DECL": 1}, "neg", "|CSD-| x Decline (Maturity stronger)")

    # ---------------- H3 (growth, maturity, decline firm-years)
    G3 = S & d.GMD
    h3 = {}
    for nm, dv, cond, sl in [("1-step INVEST", "INVEST", G3, ("IndID", "L_SG")),
                             ("2-step INVRES", "INVRES", G3, None),
                             ("UnderInv subsample", "UNDERINV", G3 & (d.INVRES < 0), None),
                             ("OverInv subsample", "OVERINV", G3 & (d.INVRES > 0), None)]:
        m = FE(d, dv, H3X + CTRL, fe=FE1, cond=cond, slopes=sl)
        h3[nm] = m
        if dv in ("INVEST", "INVRES"):
            rec("H3a", nm, m, {"POS_MA": 1}, "pos", "CSD+ x MA (maturity)")
            rec("H3a", nm, m, {"POS_MA": 1, "POS_MA_GD": 1}, "pos", "CSD+ x MA (growth/decline)")
            rec("H3a", nm, m, {"POS_MA_GD": 1}, "pos", "CSD+ x MA x GD (G/D stronger)")
            rec("H3b", nm, m, {"NEG_MA": 1}, "neg", "|CSD-| x MA (maturity)")
            rec("H3b", nm, m, {"NEG_MA_GD": 1}, "pos", "|CSD-| x MA x GD (maturity stronger)")
        elif dv == "UNDERINV":
            rec("H3a", nm, m, {"POS_MA": 1}, "neg", "CSD+ x MA (maturity)")
            rec("H3a", nm, m, {"POS_MA": 1, "POS_MA_GD": 1}, "neg", "CSD+ x MA (growth/decline)")
            rec("H3a", nm, m, {"POS_MA_GD": 1}, "neg", "CSD+ x MA x GD (G/D stronger)")
        else:
            rec("H3b", nm, m, {"NEG_MA": 1}, "neg", "|CSD-| x MA (maturity)")
            rec("H3b", nm, m, {"NEG_MA_GD": 1}, "pos", "|CSD-| x MA x GD (maturity stronger)")

    res = pd.DataFrame(rows)
    res.to_csv(os.path.join(out, "hypothesis_tests.csv"), index=False)

    # ---------------- economic significance (two-step signed model)
    econ = []
    mabs = d.loc[S, "INVEFF_ABS"].mean()
    sd_pos = d.loc[S & (d.POS > 0), "POS"].std()
    sd_neg = d.loc[S & (d.NEG > 0), "NEG"].std()
    for lab, m, w, sdx in [("H1a: +1SD CSD+", m2, {"POS": 1}, sd_pos),
                           ("H1b: +1SD |CSD-|", m2, {"NEG": 1}, sd_neg),
                           ("H3a G/D, MA p25", h3["2-step INVRES"], {"POS": 1, "POS_GD": 1, "POS_MA": -.25, "POS_MA_GD": -.25}, sd_pos),
                           ("H3a G/D, MA p75", h3["2-step INVRES"], {"POS": 1, "POS_GD": 1, "POS_MA": .25, "POS_MA_GD": .25}, sd_pos),
                           ("H3b Mat, MA p25", h3["2-step INVRES"], {"NEG": 1, "NEG_MA": -.25}, sd_neg),
                           ("H3b Mat, MA p75", h3["2-step INVRES"], {"NEG": 1, "NEG_MA": .25}, sd_neg)]:
        est, se = m.lc(w)
        econ.append(dict(effect=lab, slope=est, se=se, sd_x=sdx, change_in_INVRES=est * sdx,
                         pct_of_mean_abs_ineff=100 * est * sdx / mabs))
    pd.DataFrame(econ).to_csv(os.path.join(out, "economic_significance.csv"), index=False)

    # ---------------- legacy specification (original script logic, for comparison)
    d["CSD_ABS_t"] = d.CSD.abs()
    leg = FE(d, "INVEFF_ABS", ["CSD_ABS_t", "MA"] + CTRL, fe=("FirmID", "Year"), cond=S)
    legacy = dict(b=leg.b["CSD_ABS_t"], se=leg.se["CSD_ABS_t"], p=leg.twosided("CSD_ABS_t"))
    pd.DataFrame([legacy]).to_csv(os.path.join(out, "legacy_spec.csv"), index=False)

    diag = dict(
        N_sample=int(S.sum()), firms=int(d.loc[S, "FirmID"].nunique()),
        corr_CSD_LCSD=float(d.loc[S, ["CSD", "CSD_L"]].corr().iloc[0, 1]),
        within_share_CSD=float(
            (d.loc[S, "CSD"] - d.loc[S].groupby("FirmID").CSD.transform("mean")).var() / d.loc[S, "CSD"].var()),
        share_DEA_eff1=float((d.FE_SCORE >= 1 - 1e-6).mean()),
        stage_shares=d.loc[S, "LC_L"].value_counts(normalize=True).sort_index().round(3).to_dict(),
    )
    pd.Series(diag).to_csv(os.path.join(out, "diagnostics.csv"))
    figures(d, h2["2-step INVRES"], h3["2-step INVRES"], out)
    return res, pd.DataFrame(econ), legacy, diag


def figures(d, m2, m3, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "serif", "font.size": 9, "axes.spines.top": False,
                         "axes.spines.right": False})
    red, blue = "#9b2226", "#1d3557"
    cv = stats.t.ppf(.975, m2.df)

    # Fig 1: stage-specific slopes (H2)
    fig, ax = plt.subplots(figsize=(6.5, 3.6))
    stages = ["INTRO", "GROW", "MATU", "SHAKE", "DECL"]
    for side, col, off, lab in [("POS", red, -.12, "Over-leverage CSD+ (H1a/H2a: <0)"),
                                ("NEG", blue, .12, "Under-leverage |CSD-| (H1b/H2b: >0)")]:
        for k, s in enumerate(stages):
            w = {side: 1} if s == "MATU" else {side: 1, f"{side}_{s}": 1}
            e, se = m2.lc(w)
            ax.errorbar(k + 1 + off, e, yerr=cv * se, fmt="o" if side == "POS" else "D", color=col,
                        capsize=3, label=lab if k == 0 else None)
    ax.axhline(0, color="grey", ls="--", lw=.8)
    ax.set_xticks(range(1, 6), ["Intro", "Growth", "Maturity", "Shake-out", "Decline"])
    ax.set_ylabel("dInvestment residual / dDeviation")
    ax.set_title("Effect of capital structure deviation on investment, by life-cycle stage (t-1)")
    ax.legend(frameon=False, loc="lower center", bbox_to_anchor=(.5, -.32), ncol=2)
    fig.tight_layout()
    fig.savefig(os.path.join(out, "Fig1_H2_stage_slopes.png"), dpi=300)
    plt.close(fig)

    # Fig 2: marginal effect conditional on MA
    grid = np.linspace(-.5, .5, 41)
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.6), sharey=True)
    for ax, side, ttl in [(axes[0], "POS", "Over-leverage (CSD+): H3a"),
                          (axes[1], "NEG", "Under-leverage (|CSD-|): H3b")]:
        for g, col, ls, lab in [(1, red, "-", "Growth / Decline"), (0, blue, "--", "Maturity")]:
            est = np.array([m3.lc({side: 1, f"{side}_GD": g, f"{side}_MA": m, f"{side}_MA_GD": m * g}) for m in grid])
            ax.fill_between(grid + .5, est[:, 0] - cv * est[:, 1], est[:, 0] + cv * est[:, 1], color=col, alpha=.15, lw=0)
            ax.plot(grid + .5, est[:, 0], color=col, ls=ls, label=lab)
        ax.axhline(0, color="grey", ls=":", lw=.8)
        ax.set_title(ttl)
        ax.set_xlabel("Managerial ability (industry-year percentile, t-1)")
    axes[0].set_ylabel("Marginal effect on investment residual")
    axes[1].legend(frameon=False)
    fig.tight_layout()
    fig.savefig(os.path.join(out, "Fig2_H3_marginal_effects.png"), dpi=300)
    plt.close(fig)

    # Fig 3: predicted residual along the full CSD axis
    S = d.SAMPLE & d.GMD
    lo, hi = d.loc[S, "CSD_L"].quantile([.05, .95])
    xs = np.linspace(lo, hi, 61)
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.6), sharey=True)
    for ax, g, ttl in [(axes[0], 1, "Growth / Decline"), (axes[1], 0, "Maturity")]:
        for m, col, ls, lab in [(-.4, red, "-", "Low ability (p10)"), (.4, blue, "--", "High ability (p90)")]:
            vals = []
            for x in xs:
                if x >= 0:
                    w = {"POS": x, "POS_GD": x * g, "POS_MA": x * m, "POS_MA_GD": x * m * g}
                else:
                    w = {"NEG": -x, "NEG_GD": -x * g, "NEG_MA": -x * m, "NEG_MA_GD": -x * m * g}
                vals.append(m3.lc(w))
            vals = np.array(vals)
            ax.fill_between(xs, vals[:, 0] - cv * vals[:, 1], vals[:, 0] + cv * vals[:, 1], color=col, alpha=.15, lw=0)
            ax.plot(xs, vals[:, 0], color=col, ls=ls, label=lab)
        ax.axvline(0, color="grey", lw=.8)
        ax.axhline(0, color="grey", ls=":", lw=.8)
        ax.set_title(ttl)
        ax.set_xlabel("Capital structure deviation at t-1 (actual - target)")
    axes[0].set_ylabel("Predicted investment residual vs on-target firm")
    axes[1].legend(frameon=False)
    fig.tight_layout()
    fig.savefig(os.path.join(out, "Fig3_H3_prediction_CSD_axis.png"), dpi=300)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data")
    ap.add_argument("--out", default="output")
    ap.add_argument("--simulate", action="store_true")
    ap.add_argument("--null", action="store_true", help="simulate with all planted effects = 0")
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    if a.simulate:
        raw = simulate(null=a.null, seed=a.seed)
    else:
        raw = pd.read_excel(a.data) if a.data.endswith(("xlsx", "xls")) else pd.read_csv(a.data)
        for c in raw.columns:
            if c not in ("Symbol", "Country") and raw[c].dtype == object:
                raw[c] = pd.to_numeric(raw[c].astype(str).str.replace(",", ""), errors="coerce")
    d = build(raw)
    res, econ, legacy, diag = run_all(d, a.out)
    pd.set_option("display.width", 200)
    print("\nDIAGNOSTICS\n", pd.Series(diag).to_string())
    print("\nHYPOTHESIS TESTS (one-sided p for the predicted sign)\n",
          res.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
    print("\nECONOMIC SIGNIFICANCE\n", econ.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
    print("\nLEGACY SPEC (|CSD_t| -> |InvRes_t|, firm+year FE):", {k: round(v, 4) for k, v in legacy.items()})


if __name__ == "__main__":
    main()
