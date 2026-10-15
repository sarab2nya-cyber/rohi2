# -*- coding: utf-8 -*-
"""
Why do auditors stay silent? Time-budget pressure, ethical climate, moral disengagement, professional conscience and silence about a detected irregularity.
Fully latent CB-SEM (semopy); no item sums/means; latent interactions via matched-pair product indicators.
Colab:  !pip -q install "setuptools<58" wheel && pip -q install --no-build-isolation semopy==2.3.11
        !pip -q install pandas numpy scipy statsmodels matplotlib openpyxl ; %run eth_analysis.py    (set DATA_PATH for the real survey)
"""
import os, sys, json, warnings
import numpy as np, pandas as pd
from scipy import stats
import statsmodels.api as sm
from semopy import Model, calc_stats
warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else "."
sys.path.insert(0, HERE)
from simlib import gen_items
SEED, N = 90417, 364
DATA_PATH = None
OUT = os.path.join(HERE, "..", "output"); os.makedirs(OUT, exist_ok=True)
B = int(os.environ.get("BOOT", 2000))
z = lambda x: (x-x.mean())/x.std()

def simulate(seed=SEED, n=N):
    rng = np.random.default_rng(seed)
    rank = rng.choice(4, n, p=[.34, .30, .21, .15])                    # 0 assistant, 1 senior, 2 supervisor, 3 manager/partner
    emp = rng.choice(3, n, p=[.28, .50, .22])                         # 0 Audit Organization, 1 private institutes, 2 other
    exp = np.clip(np.where(rank == 0, rng.gamma(2.2, 1.0, n), rng.gamma(4.0, 2.2, n)) + rank, 0.5, 30).round().astype(int)
    age = np.clip(24 + 1.0*exp + rng.normal(0, 3.5, n), 22, 62).round().astype(int)
    gender = (rng.random(n) < .63).astype(int); edu = rng.choice(3, n, p=[.57, .36, .07]); cert = (rng.random(n) < .22 + .12*(rank >= 2)).astype(int)
    senior = (rank >= 2).astype(int)
    TBP = rng.normal(size=n); ECL = z(-.20*TBP + .98*rng.normal(size=n)); CON = z(.25*ECL + .10*senior + .96*rng.normal(size=n))
    tc = z(TBP*CON)
    MD = z(.42*TBP - .30*ECL - .20*CON - .24*tc + .76*rng.normal(size=n))
    bMD = np.where(senior == 1, .24, .52)
    mc = z(MD*CON)
    SIL = z(bMD*MD - .22*ECL - .14*CON - .36*mc + .06*TBP + .70*rng.normal(size=n))
    lat = dict(TBP=TBP, ECL=ECL, CON=CON, MD=MD, SIL=SIL)
    spec = dict(TBP=[.80,.77,.74,.69], ECL=[.81,.78,.75,.70], CON=[.80,.78,.74,.70], MD=[.80,.77,.75,.72,.68], SIL=[.81,.79,.76,.73,.68])
    items = gen_items(rng, lat, spec, cross=[("MD3","TBP",.12),("SIL2","ECL",.12),("CON4","ECL",.12),("TBP2","MD",.12),("MD5","CON",-.10)],
        resid_corr=[("TBP1","TBP2",.22),("ECL1","ECL2",.20),("CON1","CON2",.22),("MD1","MD2",.20),("SIL1","SIL2",.22),("MD4","MD5",.18)],
        method_sd=.15, loc=dict(TBP=.25, ECL=-.05, CON=.35, MD=-.35, SIL=-.20))
    d = pd.DataFrame(dict(rank=rank+1, emp=emp+1, exp=exp, age=age, gender=gender, edu=edu+1, cert=cert, senior=senior))
    return pd.concat([d, items], axis=1)

df = pd.read_csv(DATA_PATH) if DATA_PATH else simulate()
if not DATA_PATH:
    df.to_csv(os.path.join(OUT, "eth_data.csv"), index=False, encoding="utf-8-sig"); df.to_excel(os.path.join(OUT, "eth_data.xlsx"), index=False)
FAC = dict(TBP=4, ECL=4, CON=4, MD=5, SIL=5)
ITEMS = [f"{f}{j}" for f, k in FAC.items() for j in range(1, k+1)]
X = df[ITEMS]; R = {"n": len(df)}
R["demo"] = dict(rank={int(k): float(v*100) for k, v in df["rank"].value_counts(normalize=True).sort_index().items()}, emp={int(k): float(v*100) for k, v in df.emp.value_counts(normalize=True).sort_index().items()},
                 edu={int(k): float(v*100) for k, v in df.edu.value_counts(normalize=True).sort_index().items()}, male=float(df.gender.mean()*100), cert=float(df.cert.mean()*100),
                 exp_m=float(df.exp.mean()), exp_sd=float(df.exp.std()), age_m=float(df.age.mean()), age_sd=float(df.age.std()), senior_n=int(df.senior.sum()))
it = pd.DataFrame({"mean": X.mean(), "sd": X.std(), "skew": X.apply(stats.skew), "kurt": X.apply(stats.kurtosis)}); R["items"] = it.round(3).to_dict("index")
R["skew_range"] = [float(it["skew"].min()), float(it["skew"].max())]; R["kurt_range"] = [float(it["kurt"].min()), float(it["kurt"].max())]
Zc = (X - X.mean()).values; S_ = np.cov(Zc.T, bias=True); d2 = np.einsum("ij,jk,ik->i", Zc, np.linalg.inv(S_), Zc); p_ = X.shape[1]; mk = (d2**2).mean()
R["mardia"] = dict(k=float(mk), expected=float(p_*(p_+2)))
def srmr(m, data):
    sig = m.calc_sigma()[0]; names = m.vars["observed"]; Sx = data[names].cov().values; sd = np.sqrt(np.diag(Sx))
    res = (Sx - sig)/np.outer(sd, sd); tri = np.tril_indices(len(names)); return float(np.sqrt((res[tri]**2).mean()))
def fitstats(m, data):
    s = calc_stats(m).T["Value"]
    return dict(chi2=float(s["chi2"]), df=float(s["DoF"]), p=float(s["chi2 p-value"]), cfi=float(s["CFI"]), tli=float(s["TLI"]), rmsea=float(s["RMSEA"]), srmr=srmr(m, data), aic=float(s["AIC"]), bic=float(s["BIC"]))
def row(ins, l, o, r):
    q = ins[(ins.lval==l) & (ins.op==o) & (ins.rval==r)].iloc[0]
    g = lambda c: float(q[c]) if str(q[c]) not in ("-", "nan") else np.nan
    return dict(b=g("Estimate"), beta=g("Est. Std"), se=g("Std. Err"), z=g("z-value"), p=g("p-value"))
CFA = "".join(f"{k} =~ " + "+".join(f"{k}{j}" for j in range(1, n+1)) + "\n" for k, n in FAC.items())
cfa = Model(CFA); cfa.fit(X); R["cfa"] = fitstats(cfa, X); ins = cfa.inspect(std_est=True)
lo = ins[(ins.op=="~") & (ins.rval.isin(FAC.keys()))].copy(); lo["Est. Std"] = lo["Est. Std"].astype(float)
R["loadings"] = {r.lval: float(r["Est. Std"]) for _, r in lo.iterrows()}
rel = {}
for f, k in FAC.items():
    l = lo[lo.rval==f]["Est. Std"].values; cols = [f"{f}{j}" for j in range(1, k+1)]
    ave = float((l**2).mean()); cr = float(l.sum()**2/(l.sum()**2 + (1-l**2).sum())); alpha = float(k/(k-1)*(1 - X[cols].var().sum()/X[cols].sum(axis=1).var()))
    rel[f] = dict(items=k, alpha=alpha, cr=cr, ave=ave, sqrt_ave=ave**.5, lmin=float(l.min()), lmax=float(l.max()))
R["rel"] = rel
lc = ins[(ins.op=="~~") & (ins.lval.isin(FAC)) & (ins.rval.isin(FAC)) & (ins.lval!=ins.rval)]
latcorr = pd.DataFrame(np.eye(len(FAC)), index=FAC, columns=FAC)
for _, r in lc.iterrows(): latcorr.loc[r.lval, r.rval] = latcorr.loc[r.rval, r.lval] = float(r["Est. Std"])
R["latcorr"] = latcorr.round(3).to_dict(); C = X.corr()
def htmt(a, b):
    ia = [f"{a}{j}" for j in range(1, FAC[a]+1)]; ib = [f"{b}{j}" for j in range(1, FAC[b]+1)]
    h = C.loc[ia, ib].abs().values.mean(); ma = C.loc[ia, ia].values[np.triu_indices(len(ia), 1)].mean(); mb = C.loc[ib, ib].values[np.triu_indices(len(ib), 1)].mean(); return float(h/np.sqrt(ma*mb))
R["htmt"] = {a: {b: htmt(a, b) for b in FAC if b != a} for a in FAC}; R["htmt_max"] = max(v for a in R["htmt"].values() for v in a.values())
ev = np.sort(np.linalg.eigvalsh(X.corr().values))[::-1]; one = Model("G =~ " + "+".join(ITEMS)); one.fit(X)
clf = Model(CFA + "M =~ " + "+".join(ITEMS) + "\n" + "\n".join(f"M ~~ 0*{f}" for f in FAC) + "\n"); clf.fit(X)
cm_ = clf.inspect(std_est=True); mm_ = cm_[(cm_.op=="~") & (cm_.rval=="M")]["Est. Std"].astype(float)
R["cmb"] = dict(harman=float(ev[0]/ev.sum()*100), one_factor=fitstats(one, X), clf=fitstats(clf, X), clf_var=float((mm_**2).mean()*100))
# ---------------- structural model with two latent interactions
dfc = X - X.mean()
for i in range(1, 5):
    dfc[f"IT{i}"] = dfc[f"TBP{i}"]*dfc[f"CON{i}"]; dfc[f"IM{i}"] = dfc[f"MD{i}"]*dfc[f"CON{i}"]
MEAS = CFA + "INTT =~ IT1+IT2+IT3+IT4\nINTM =~ IM1+IM2+IM3+IM4\n"
EXO = ["TBP", "ECL", "CON", "INTT"]
COV = "".join(f"{a} ~~ {b}\n" for i, a in enumerate(EXO) for b in EXO[i+1:]) + "INTM ~~ TBP\nINTM ~~ ECL\nINTM ~~ CON\nINTM ~~ INTT\n"
BODY = "MD ~ TBP + ECL + CON + INTT\nSIL ~ MD + ECL + CON + TBP + INTM\n"
M_FULL = MEAS + BODY + COV
sem = Model(M_FULL); sem.fit(dfc); R["sem"] = fitstats(sem, dfc); si = sem.inspect(std_est=True)
PAIRS = [("MD","TBP"),("MD","ECL"),("MD","CON"),("MD","INTT"),("SIL","MD"),("SIL","ECL"),("SIL","CON"),("SIL","TBP"),("SIL","INTM")]
R["paths"] = {f"{l}~{r}": row(si, l, "~", r) for l, r in PAIRS}
def latent_r2(ii, dvs):
    out = {}
    for dv in dvs:
        q = ii[(ii.lval == dv) & (ii.op == "~~") & (ii.rval == dv)].iloc[0]; out[dv] = float(1 - float(q["Est. Std"]))
    return out
R["r2"] = latent_r2(si, ["MD", "SIL"])
iu = sem.inspect(); psi = lambda dv: float(iu[(iu.lval == dv) & (iu.op == "~~") & (iu.rval == dv)]["Estimate"].iloc[0])
R["sd_latent"] = {"CON": psi("CON")**.5}
R["n_obs_vars"] = len(sem.vars["observed"]); R["n_params_sem"] = int(R["n_obs_vars"]*(R["n_obs_vars"]+1)/2 - R["sem"]["df"])
NOI = MEAS + "MD ~ TBP + ECL + CON\nSIL ~ MD + ECL + CON + TBP\n" + COV
m_ni = Model(NOI); m_ni.fit(dfc); R["fit_noint"] = fitstats(m_ni, dfc); r2n = latent_r2(m_ni.inspect(std_est=True), ["MD", "SIL"]); R["r2_noint"] = r2n
R["f2_int"] = {k: float((R["r2"][k]-r2n[k])/(1-R["r2"][k])) for k in ["MD", "SIL"]}
# ---------------- bootstrap: conditional indirect effects and moderated mediation
sC = R["sd_latent"]["CON"]
def eff(ii, sc):
    g = lambda l, r: float(ii[(ii.lval==l)&(ii.rval==r)&(ii.op=="~")]["Estimate"].iloc[0]); o = {}
    aT, aE, wT, b, wM, dT = g("MD","TBP"), g("MD","ECL"), g("MD","INTT"), g("SIL","MD"), g("SIL","INTM"), g("SIL","TBP")
    for tag, k in [("low", -1), ("mean", 0), ("high", 1)]:
        o[f"TBP_MD_SIL_{tag}"] = (aT + wT*sc*k)*(b + wM*sc*k); o[f"ECL_MD_SIL_{tag}"] = aE*(b + wM*sc*k)
        o[f"TBP_total_{tag}"] = o[f"TBP_MD_SIL_{tag}"] + dT; o[f"a_TBP_{tag}"] = aT + wT*sc*k; o[f"b_MD_{tag}"] = b + wM*sc*k
    o["imm_TBP"] = (o["TBP_MD_SIL_high"] - o["TBP_MD_SIL_low"])/2; o["imm_ECL"] = (o["ECL_MD_SIL_high"] - o["ECL_MD_SIL_low"])/2
    return o
def eff_std(ii):
    g = lambda l, r: float(ii[(ii.lval==l)&(ii.rval==r)&(ii.op=="~")]["Est. Std"].iloc[0]); return {"std_TBP_ind": g("MD","TBP")*g("SIL","MD"), "std_ECL_ind": g("MD","ECL")*g("SIL","MD")}
point = {**eff(iu, sC), **eff_std(si)}; rng = np.random.default_rng(SEED); bt = []
for bi in range(B):
    ix = rng.integers(0, len(dfc), len(dfc)); bd = dfc.iloc[ix].reset_index(drop=True)
    try:
        mb = Model(M_FULL); mb.fit(bd); ib = mb.inspect(); sb = float(ib[(ib.lval=="CON")&(ib.op=="~~")&(ib.rval=="CON")]["Estimate"].iloc[0])**.5
        bt.append({**eff(ib, sb), **eff_std(mb.inspect(std_est=True))})
    except Exception: pass
bt = pd.DataFrame(bt); R["boot_n"] = int(len(bt))
R["indirect"] = {k: dict(est=float(point[k]), lo=float(bt[k].quantile(.025)), hi=float(bt[k].quantile(.975)), sig=bool(bt[k].quantile(.025)*bt[k].quantile(.975) > 0)) for k in point}
# ---------------- competing models and robustness
def mk(body): return Model(MEAS + body + COV)
cand = {"M1": ("مدل پیشنهادی", BODY), "M2": ("بدون تعدیل‌گری", "MD ~ TBP + ECL + CON\nSIL ~ MD + ECL + CON + TBP\n"),
        "M3": ("میانجی‌گری کامل (بدون اثر مستقیم فشار زمانی و جو)", "MD ~ TBP + ECL + CON + INTT\nSIL ~ MD + CON + INTM\n"),
        "M4": ("بدون مسیر رفع تعهد اخلاقی", "MD ~ TBP + ECL + CON + INTT\nSIL ~ ECL + CON + TBP\n"),
        "M5": ("مسیر معکوس (سکوت ← رفع تعهد)", "SIL ~ TBP + ECL + CON + INTT\nMD ~ SIL + ECL + CON + TBP + INTM\n")}
R["models"] = {}
for k, (nm, body) in cand.items():
    mm = mk(body); mm.fit(dfc); R["models"][k] = dict(name=nm, **fitstats(mm, dfc))
keyp = [("MD","TBP"),("MD","ECL"),("MD","CON"),("SIL","MD"),("SIL","ECL"),("SIL","CON"),("SIL","TBP")]; EX = [("MD","INTT"),("SIL","INTM")]
def keyrow(ii): return {f"{l}~{r}": row(ii, l, "~", r) for l, r in keyp + EX}
NOI2 = CFA + "MD ~ TBP + ECL + CON\nSIL ~ MD + ECL + CON + TBP\nTBP ~~ ECL\nTBP ~~ CON\nECL ~~ CON\n"
md = Model(NOI2); md.fit(dfc[ITEMS], obj="DWLS"); R["dwls"] = {f"{l}~{r}": row(md.inspect(std_est=True), l, "~", r) for l, r in keyp}; R["dwls_fit"] = fitstats(md, dfc[ITEMS])
dfr = dfc.copy(); Xf = sm.add_constant(dfc[[f"TBP{i}" for i in range(1, 5)] + [f"CON{i}" for i in range(1, 5)] + [f"MD{i}" for i in range(1, 5)]].values)
for pre in ("IT", "IM"):
    for i in range(1, 5):
        pr = dfc[f"{pre}{i}"].values; dfr[f"{pre}{i}"] = pr - Xf @ np.linalg.lstsq(Xf, pr, rcond=None)[0]
m_rc = Model(M_FULL); m_rc.fit(dfr); R["resid_centered"] = keyrow(m_rc.inspect(std_est=True)); R["resid_centered_fit"] = fitstats(m_rc, dfr)
keep = d2 < np.quantile(d2, .95); R["outliers_removed"] = int((~keep).sum())
m_o = Model(M_FULL); m_o.fit(dfc[keep].reset_index(drop=True)); R["trimmed"] = keyrow(m_o.inspect(std_est=True)); R["trimmed_fit"] = fitstats(m_o, dfc[keep].reset_index(drop=True))
sg = cfa.calc_sigma()[0]; nm_ = cfa.vars["observed"]; Sx = X[nm_].cov().values; sdv = np.sqrt(np.diag(Sx)); res_ = (Sx - sg)/np.outer(sdv, sdv); pairs = []
for i_ in range(len(nm_)):
    for j_ in range(i_):
        if nm_[i_].rstrip("0123456789") == nm_[j_].rstrip("0123456789"): pairs.append((abs(res_[i_, j_]), nm_[j_], nm_[i_]))
pairs = sorted(pairs, reverse=True)[:4]; add_ = "".join(f"{a} ~~ {b}\n" for _, a, b in pairs)
m_rs = Model(M_FULL + add_); m_rs.fit(dfc); R["respec"] = dict(pairs=[(a, b) for _, a, b in pairs], fit=fitstats(m_rs, dfc), paths=keyrow(m_rs.inspect(std_est=True)))
# ---------------- exploratory comparison by rank (junior: assistant/senior; senior staff: supervisor/manager-partner)
GS = CFA + "MD ~ TBP + ECL + CON\nSIL ~ MD + ECL + CON + TBP\nTBP ~~ ECL\nTBP ~~ CON\nECL ~~ CON\n"
gres = []
for g in (0, 1):
    mg_ = Model(GS); mg_.fit(df[df.senior == g][ITEMS].reset_index(drop=True)); gi = mg_.inspect(std_est=True); gres.append({f"{l}~{r}": row(gi, l, "~", r) for l, r in keyp})
R["group_paths"] = {"junior": gres[0], "senior": gres[1]}
R["group_diff"] = {k: dict(dz=float((gres[1][k]["b"]-gres[0][k]["b"])/np.sqrt(gres[0][k]["se"]**2 + gres[1][k]["se"]**2))) for k in gres[0]}
for k in R["group_diff"]: R["group_diff"][k]["p"] = float(2*(1-stats.norm.cdf(abs(R["group_diff"][k]["dz"]))))
R["group_n"] = [int((df.senior == 0).sum()), int((df.senior == 1).sum())]
json.dump(R, open(os.path.join(OUT, "results_eth.json"), "w"), ensure_ascii=False, indent=1)
bt.describe().T.round(4).to_csv(os.path.join(OUT, "bootstrap_summary.csv"))
print("N", R["n"]); print("CFA", {k: round(v, 3) for k, v in R["cfa"].items()}); print("SEM", {k: round(v, 3) for k, v in R["sem"].items()})
for f, v in R["rel"].items(): print(f, {k: round(x, 3) for k, x in v.items()})
for k, v in R["paths"].items(): print(k, {a: round(b, 3) for a, b in v.items()})
print("R2", R["r2"], "f2", R["f2_int"])
for k, v in R["indirect"].items(): print(k, {a: (round(b, 3) if not isinstance(b, bool) else b) for a, b in v.items()})
for k, v in R["models"].items(): print(k, v["name"], round(v["chi2"], 1), v["df"], round(v["cfi"], 3), round(v["rmsea"], 3), round(v["bic"], 1))
print("group n", R["group_n"], {k: (round(v["dz"], 2), round(v["p"], 3)) for k, v in R["group_diff"].items()}); print("HTMT", R["htmt_max"])
