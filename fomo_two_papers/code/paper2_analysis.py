# -*- coding: utf-8 -*-
"""
مقالهٔ ۲ — پیش‌برنده‌های FOMO، رقابت منبع اطلاعات (شبکهٔ اجتماعی در برابر اطلاعات حسابداری)،
ناوردایی اندازه‌گیری و تفاوت مسیرها بر پایهٔ تجربهٔ زیان در ریزش بورس، و تحلیل تکمیلی یادگیری ماشین (RF/GBM + SHAP)
Colab:  !pip -q install "setuptools<58" wheel && pip -q install --no-build-isolation semopy==2.3.11
        !pip -q install pandas numpy scipy statsmodels scikit-learn shap matplotlib arabic-reshaper python-bidi openpyxl
        %run paper2_analysis.py     (فایل‌های simlib.py و mgcfa.py در کنار این فایل باشند)
"""
import os, sys, json, warnings
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats
import statsmodels.api as sm
from semopy import Model, calc_stats
warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else "."
sys.path.insert(0, HERE)
from simlib import gen_items, demographics
from mgcfa import MGCFA

SEED, N = 24071, 442
DATA_PATH = None
OUT = os.path.join(HERE, "..", "paper2", "output"); os.makedirs(OUT, exist_ok=True)
DATA_DIR = os.path.join(HERE, "..", "data"); os.makedirs(DATA_DIR, exist_ok=True)
B = int(os.environ.get("BOOT", 2000)); BG = int(os.environ.get("BOOT_G", 1000))
z = lambda x: (x-x.mean())/x.std()

# ------------------------------------------------------------ ۱) شبیه‌سازی
def simulate(seed=SEED, n=N):
    rng = np.random.default_rng(seed)
    d = demographics(rng, n, age_mu=41, age_sd=10, p_male=.66, exp_shape=2.8, exp_scale=3.1, edu_p=(.08,.44,.37,.11))
    age_z, exp_z = z(d.age.values.astype(float)), z(d.exp.values.astype(float))
    pl = 1/(1+np.exp(-(-.15 + .35*exp_z - .10*age_z)))
    LE = (rng.random(n) < pl*.95).astype(int)
    C = np.array([[1,.30,.22,.05],[.30,1,.18,.04],[.22,.18,1,-.08],[.05,.04,-.08,1]])
    SC, AR, SME, AL = rng.multivariate_normal(np.zeros(4), C, n).T
    AR = AR + .30*LE; 
    bAR = np.where(LE==1, .40, .20); bSC = .30; bF_idq = np.where(LE==1, -.34, -.20); bA_idq = np.where(LE==1, .40, .25)
    FOMO = z(bSC*SC + bAR*AR + .24*SME + .18*LE + .75*rng.normal(size=n))
    AIU = z(.46*AL - .25*SME - .05*LE + .85*rng.normal(size=n))
    IDQ = z(bF_idq*FOMO + bA_idq*AIU + .12*AL - 1.00*np.maximum(FOMO-.2, 0) + .55*FOMO*AIU + .10*exp_z + .78*rng.normal(size=n))
    HRD = z(.45*FOMO + .10*SME - .15*AIU + .80*rng.normal(size=n))
    lat = dict(SC=z(SC), AR=z(AR), SME=z(SME), FOMO=FOMO, AL=z(AL), AIU=AIU, IDQ=IDQ, HRD=HRD)
    spec = dict(SC=[.79,.76,.72,.67], AR=[.80,.76,.73,.66], SME=[.78,.74,.70,.66,.61], FOMO=[.81,.77,.73,.70,.67,.63],
                AL=[.82,.78,.74,.69], AIU=[.80,.76,.73,.69,.65], IDQ=[.80,.76,.72,.68,.64], HRD=[.78,.75,.72,.68,.64])
    dif = {"FOMO5": .32*LE, "AR3": .28*LE}
    items = gen_items(rng, lat, spec,
        cross=[("SME4","FOMO",.18),("FOMO6","AR",.16),("AIU5","IDQ",.15),("SC4","AR",.17),("AL4","AIU",.14),("IDQ5","FOMO",-.12)],
        resid_corr=[("FOMO1","FOMO2",.26),("AIU1","AIU2",.24),("SC1","SC2",.22),("AR1","AR2",.22),("AL1","AL2",.20),("IDQ2","IDQ3",.22)],
        method_sd=.16, loc=dict(SC=-.1, AR=-.05, SME=.1, FOMO=-.05, AL=.05, AIU=-.2, IDQ=-.25, HRD=-.25), dif=dif)
    d["LE"] = LE
    return pd.concat([d, items], axis=1)

df = pd.read_csv(DATA_PATH) if DATA_PATH else simulate()
if not DATA_PATH:
    df.to_csv(os.path.join(DATA_DIR, "paper2_data.csv"), index=False, encoding="utf-8-sig")
    df.to_excel(os.path.join(DATA_DIR, "paper2_data.xlsx"), index=False)
FAC = dict(SC=4, AR=4, SME=5, FOMO=6, AL=4, AIU=5, IDQ=5)
ITEMS = [f"{f}{j}" for f, k in FAC.items() for j in range(1, k+1)]
X = df[ITEMS]; R = {"n": len(df)}
grp = [df[df.LE==0].reset_index(drop=True), df[df.LE==1].reset_index(drop=True)]
R["groups"] = dict(n0=len(grp[0]), n1=len(grp[1]), pct1=float(df.LE.mean()*100))

# ------------------------------------------------------------ ۲) توصیفی
R["demo"] = dict(male=float((df.gender==1).mean()*100), age_m=float(df.age.mean()), age_sd=float(df.age.std()),
    exp_m=float(df.exp.mean()), exp_sd=float(df.exp.std()),
    edu={int(k): float(v*100) for k, v in df.edu.value_counts(normalize=True).sort_index().items()},
    port_med=float(df.portfolio.median()), port_q1=float(df.portfolio.quantile(.25)), port_q3=float(df.portfolio.quantile(.75)))
it = pd.DataFrame({"mean": X.mean(), "sd": X.std(), "skew": X.apply(stats.skew), "kurt": X.apply(stats.kurtosis)})
R["items"] = it.round(3).to_dict("index")
R["skew_range"] = [float(it["skew"].min()), float(it["skew"].max())]; R["kurt_range"] = [float(it["kurt"].min()), float(it["kurt"].max())]
Zc = (X - X.mean()).values; S = np.cov(Zc.T, bias=True); d2 = np.einsum("ij,jk,ik->i", Zc, np.linalg.inv(S), Zc)
p = X.shape[1]; mk = (d2**2).mean(); R["mardia"] = dict(k=float(mk), expected=float(p*(p+2)), z=float((mk-p*(p+2))/np.sqrt(8*p*(p+2)/len(df))))

def srmr(m, data):
    sig = m.calc_sigma()[0]; names = m.vars["observed"]; Sx = data[names].cov().values; sd = np.sqrt(np.diag(Sx))
    res = (Sx - sig)/np.outer(sd, sd); tri = np.tril_indices(len(names)); return float(np.sqrt((res[tri]**2).mean()))
def fitstats(m, data):
    s = calc_stats(m).T["Value"]
    return dict(chi2=float(s["chi2"]), df=float(s["DoF"]), p=float(s["chi2 p-value"]), cfi=float(s["CFI"]), tli=float(s["TLI"]),
                rmsea=float(s["RMSEA"]), gfi=float(s["GFI"]), srmr=srmr(m, data), aic=float(s["AIC"]), bic=float(s["BIC"]))
def row(ins, l, o, r):
    q = ins[(ins.lval==l) & (ins.op==o) & (ins.rval==r)].iloc[0]
    g = lambda c: float(q[c]) if str(q[c]) not in ("-", "nan") else np.nan
    return dict(b=g("Estimate"), beta=g("Est. Std"), se=g("Std. Err"), z=g("z-value"), p=g("p-value"))
CFA = "".join(f"{k} =~ " + "+".join(f"{k}{j}" for j in range(1, n+1)) + "\n" for k, n in FAC.items())

# ------------------------------------------------------------ ۳) CFA
cfa = Model(CFA); cfa.fit(X); R["cfa"] = fitstats(cfa, X)
ins = cfa.inspect(std_est=True)
lo = ins[(ins.op=="~") & (ins.rval.isin(FAC.keys()))].copy(); lo["Est. Std"] = lo["Est. Std"].astype(float)
rel = {}
for f, k in FAC.items():
    l = lo[lo.rval==f]["Est. Std"].values; cols = [f"{f}{j}" for j in range(1, k+1)]
    ave = float((l**2).mean()); cr = float(l.sum()**2/(l.sum()**2 + (1-l**2).sum()))
    alpha = float(k/(k-1)*(1 - X[cols].var().sum()/X[cols].sum(axis=1).var()))
    rel[f] = dict(items=k, alpha=alpha, cr=cr, ave=ave, sqrt_ave=ave**.5, lmin=float(l.min()), lmax=float(l.max()))
R["rel"] = rel
lc = ins[(ins.op=="~~") & (ins.lval.isin(FAC)) & (ins.rval.isin(FAC)) & (ins.lval!=ins.rval)]
latcorr = pd.DataFrame(np.eye(len(FAC)), index=FAC, columns=FAC)
for _, r in lc.iterrows(): latcorr.loc[r.lval, r.rval] = latcorr.loc[r.rval, r.lval] = float(r["Est. Std"])
R["latcorr"] = latcorr.round(3).to_dict()
C = X.corr()
def htmt(a, b):
    ia = [f"{a}{j}" for j in range(1, FAC[a]+1)]; ib = [f"{b}{j}" for j in range(1, FAC[b]+1)]
    h = C.loc[ia, ib].abs().values.mean(); ma = C.loc[ia, ia].values[np.triu_indices(len(ia), 1)].mean(); mb = C.loc[ib, ib].values[np.triu_indices(len(ib), 1)].mean()
    return float(h/np.sqrt(ma*mb))
R["htmt"] = {a: {b: htmt(a, b) for b in FAC if b != a} for a in FAC}; R["htmt_max"] = max(v for a in R["htmt"].values() for v in a.values())
ev = np.sort(np.linalg.eigvalsh(X.corr().values))[::-1]
one = Model("G =~ " + "+".join(ITEMS)); one.fit(X)
R["cmb"] = dict(harman=float(ev[0]/ev.sum()*100), one_factor=fitstats(one, X))

# ------------------------------------------------------------ ۴) مدل ساختاری کل نمونه
dfc = X.copy()
dfc["LE"] = df.LE.values.astype(float); dfc["exp"] = z(df.exp.astype(float)).values
SEM = CFA + "FOMO ~ SC + AR + SME + LE\nAIU ~ AL + SME + LE\nIDQ ~ FOMO + AIU + AL + LE + exp\n" + \
      "SC ~~ AR\nSC ~~ SME\nSC ~~ AL\nAR ~~ SME\nAR ~~ AL\nSME ~~ AL\n"
sem = Model(SEM); sem.fit(dfc); R["sem"] = fitstats(sem, dfc)
si = sem.inspect(std_est=True)
PAIRS = [("FOMO","SC"),("FOMO","AR"),("FOMO","SME"),("FOMO","LE"),("AIU","AL"),("AIU","SME"),("AIU","LE"),
         ("IDQ","FOMO"),("IDQ","AIU"),("IDQ","AL"),("IDQ","LE"),("IDQ","exp")]
R["paths"] = {f"{l}~{r}": row(si, l, "~", r) for l, r in PAIRS}
def latent_r2(ins_std, dvs=("FOMO", "AIU", "IDQ")):
    out = {}
    for dv in dvs:
        q = ins_std[(ins_std.lval == dv) & (ins_std.op == "~~") & (ins_std.rval == dv)].iloc[0]; out[dv] = float(1 - float(q["Est. Std"]))
    return out
R["r2"] = latent_r2(si)
R["sem_loadings"] = {r.lval: float(r["Est. Std"]) for _, r in si[(si.op == "~") & (si.rval.isin(list(FAC)))].iterrows()}
# مدل رقیب: بدون مسیر مستقیم AL→IDQ و بدون SME→AIU
alt = Model(CFA + "FOMO ~ SC + AR + SME + LE\nAIU ~ AL + LE\nIDQ ~ FOMO + AIU + LE + exp\nSC ~~ AR\nSC ~~ SME\nSC ~~ AL\nAR ~~ SME\nAR ~~ AL\nSME ~~ AL\n")
alt.fit(dfc); R["alt"] = fitstats(alt, dfc)

def eff(ii, std=False):
    c = "Est. Std" if std else "Estimate"
    g = lambda l, r: float(ii[(ii.lval==l)&(ii.rval==r)&(ii.op=="~")][c].iloc[0])
    o = {"SC_FOMO_IDQ": g("FOMO","SC")*g("IDQ","FOMO"), "AR_FOMO_IDQ": g("FOMO","AR")*g("IDQ","FOMO"),
         "SME_FOMO_IDQ": g("FOMO","SME")*g("IDQ","FOMO"), "SME_AIU_IDQ": g("AIU","SME")*g("IDQ","AIU"), "AL_AIU_IDQ": g("AIU","AL")*g("IDQ","AIU")}
    o["SME_total"] = o["SME_FOMO_IDQ"] + o["SME_AIU_IDQ"]
    o["AL_total"] = o["AL_AIU_IDQ"] + g("IDQ","AL")
    return o
rng = np.random.default_rng(SEED); bts = []
pt = eff(sem.inspect(std_est=True), std=True)
for bi in range(B):
    ix = rng.integers(0, len(dfc), len(dfc)); bd = dfc.iloc[ix].reset_index(drop=True)
    try:
        mb = Model(SEM); mb.fit(bd); bts.append(eff(mb.inspect(std_est=True), std=True))
    except Exception: pass
bts = pd.DataFrame(bts)
R["boot_n"] = int(len(bts))
R["indirect"] = {k: dict(est=float(pt[k]), lo=float(bts[k].quantile(.025)), hi=float(bts[k].quantile(.975)),
                         sig=bool(bts[k].quantile(.025)*bts[k].quantile(.975) > 0)) for k in pt}

# ------------------------------------------------------------ ۵) ناوردایی اندازه‌گیری چندگروهی
pattern = {f: [f"{f}{j}" for j in range(1, k+1)] for f, k in FAC.items()}
mg = MGCFA(grp, pattern)
conf = mg.fit(); metr = mg.fit(inv_load=True); scal = mg.fit(inv_load=True, inv_int=True)
inv = {"configural": conf, "metric": metr, "scalar": scal}
gaps = mg.intercept_gaps(metr)
order = [mg.items[i] for i in np.argsort(-gaps)]
free = []; part = scal; steps = []
for it_name in order[:6]:
    if metr["cfi"] - part["cfi"] <= .010: break
    free.append(mg.items.index(it_name)); part = mg.fit(inv_load=True, inv_int=True, free_int=tuple(free)); steps.append(it_name)
inv["partial"] = part
R["invariance"] = {k: {a: float(b) for a, b in v.items() if a in ("chi2","df","cfi","rmsea","srmr","npar")} for k, v in inv.items()}
R["invariance_freed"] = steps
R["latent_mean_diff"] = mg.latent_mean_tests(inv["partial"])
# ------------------------------------------------------------ ۶) مقایسهٔ مسیرها بین گروه‌ها
GS = CFA + "FOMO ~ SC + AR + SME\nAIU ~ AL + SME\nIDQ ~ FOMO + AIU + AL + exp\nSC ~~ AR\nSC ~~ SME\nSC ~~ AL\nAR ~~ SME\nAR ~~ AL\nSME ~~ AL\n"
GP = [("FOMO","SC"),("FOMO","AR"),("FOMO","SME"),("AIU","AL"),("AIU","SME"),("IDQ","FOMO"),("IDQ","AIU")]
gres = []
for g in grp:
    gd = X.copy().loc[g.index.map(lambda _: True)] if False else None
gdat = [dfc[df.LE.values == v].reset_index(drop=True) for v in (0, 1)]
gfit = []
for gd in gdat:
    m_ = Model(GS); m_.fit(gd); gfit.append(m_)
R["group_paths"] = {}
for l, r in GP:
    a = row(gfit[0].inspect(std_est=True), l, "~", r); b = row(gfit[1].inspect(std_est=True), l, "~", r)
    zd = (b["b"]-a["b"])/np.sqrt(a["se"]**2 + b["se"]**2)
    R["group_paths"][f"{l}~{r}"] = dict(g0=a, g1=b, diff=b["b"]-a["b"], z=float(zd), p=float(2*(1-stats.norm.cdf(abs(zd)))))
R["group_fit"] = [fitstats(m_, d_) for m_, d_ in zip(gfit, gdat)]
rngb = np.random.default_rng(SEED+1); bd_diff = {f"{l}~{r}": [] for l, r in GP}
for bi in range(BG):
    est = []
    for gd in gdat:
        bdx = gd.iloc[rngb.integers(0, len(gd), len(gd))].reset_index(drop=True)
        try:
            mb = Model(GS); mb.fit(bdx); est.append(mb.inspect())
        except Exception: est.append(None)
    if est[0] is None or est[1] is None: continue
    for l, r in GP:
        g_ = lambda ii: float(ii[(ii.lval==l)&(ii.rval==r)&(ii.op=="~")]["Estimate"].iloc[0])
        bd_diff[f"{l}~{r}"].append(g_(est[1]) - g_(est[0]))
for k, v in bd_diff.items():
    v = np.array(v); R["group_paths"][k]["boot_lo"] = float(np.quantile(v, .025)); R["group_paths"][k]["boot_hi"] = float(np.quantile(v, .975))

# ------------------------------------------------------------ ۷) یادگیری ماشین
from sklearn.model_selection import RepeatedKFold, cross_val_predict
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
def factor_scores(m, data):
    """نمرات عاملی روش رگرسیونی از برآوردهای CFA (وزن‌دهی بر پایهٔ بارها؛ نه میانگین ساده)"""
    ii = m.inspect(); items_ = m.vars["observed"]; facs_ = list(FAC)
    Lam = np.zeros((len(items_), len(facs_))); Th = np.zeros(len(items_)); Ph = np.eye(len(facs_))
    for _, r in ii.iterrows():
        if r.op == "~" and r.rval in facs_ and r.lval in items_: Lam[items_.index(r.lval), facs_.index(r.rval)] = float(r.Estimate)
        if r.op == "~~" and r.lval in items_ and r.lval == r.rval: Th[items_.index(r.lval)] = float(r.Estimate)
        if r.op == "~~" and r.lval in facs_ and r.rval in facs_: Ph[facs_.index(r.lval), facs_.index(r.rval)] = Ph[facs_.index(r.rval), facs_.index(r.lval)] = float(r.Estimate)
    Sg = Lam @ Ph @ Lam.T + np.diag(Th); W = Ph @ Lam.T @ np.linalg.inv(Sg)
    Z = (data[items_] - data[items_].mean()).values
    F = Z @ W.T
    return pd.DataFrame((F - F.mean(0))/F.std(0), columns=facs_)
fs_ = factor_scores(cfa, X)
feat = fs_[["SC", "AR", "SME", "FOMO", "AL", "AIU"]].copy()
feat["LE"] = df.LE.values; feat["exp"] = df.exp.values; feat["age"] = df.age.values; feat["gender"] = df.gender.values; feat["edu"] = df.edu.values
feat["logport"] = np.log(df.portfolio.values)
y = fs_["IDQ"].values
models = {"OLS": LinearRegression(),
          "RF": RandomForestRegressor(n_estimators=500, min_samples_leaf=6, max_features=.5, random_state=SEED, n_jobs=-1),
          "GBM": GradientBoostingRegressor(n_estimators=150, learning_rate=.04, max_depth=2, subsample=.8, min_samples_leaf=10, random_state=SEED)}
rkf = RepeatedKFold(n_splits=5, n_repeats=10, random_state=SEED)
folds = list(rkf.split(feat)); sc = {k: {"r2": [], "rmse": [], "mae": []} for k in models}
for tr, te in folds:
    for k, m_ in models.items():
        m_.fit(feat.iloc[tr], y[tr]); pr = m_.predict(feat.iloc[te])
        sc[k]["r2"].append(r2_score(y[te], pr)); sc[k]["rmse"].append(mean_squared_error(y[te], pr)**.5); sc[k]["mae"].append(mean_absolute_error(y[te], pr))
R["ml"] = {k: {a: dict(m=float(np.mean(b)), sd=float(np.std(b))) for a, b in v.items()} for k, v in sc.items()}
def nb_test(a, b, ntr, nte):                       # آزمون t اصلاح‌شدهٔ Nadeau–Bengio
    d = np.array(a) - np.array(b); n = len(d); v = d.var(ddof=1)
    t = d.mean()/np.sqrt((1/n + nte/ntr)*v); return float(t), float(2*(1-stats.t.cdf(abs(t), n-1))), float(d.mean())
ntr, nte = len(folds[0][0]), len(folds[0][1])
R["ml_tests"] = {k: dict(zip(("t","p","diff_r2"), nb_test(sc[k]["r2"], sc["OLS"]["r2"], ntr, nte))) for k in ("RF","GBM")}
# SHAP
import shap
best = "GBM" if R["ml"]["GBM"]["r2"]["m"] >= R["ml"]["RF"]["r2"]["m"] else "RF"
mb_ = models[best].fit(feat, y); expl = shap.TreeExplainer(mb_); sv = expl.shap_values(feat)
imp = pd.Series(np.abs(sv).mean(0), index=feat.columns).sort_values(ascending=False)
R["shap"] = dict(model=best, importance={k: float(v) for k, v in imp.items()})
tot = {"SC": pt["SC_FOMO_IDQ"], "AR": pt["AR_FOMO_IDQ"], "SME": pt["SME_total"], "FOMO": R["paths"]["IDQ~FOMO"]["beta"], "AL": pt["AL_total"], "AIU": R["paths"]["IDQ~AIU"]["beta"]}
common = list(tot)
rho, prho = stats.spearmanr([abs(tot[k]) for k in common], [imp[k] for k in common])
R["shap"]["spearman"] = float(rho); R["shap"]["spearman_p"] = float(prho); R["shap"]["sem_total"] = {k: float(v) for k, v in tot.items()}
# اثر تعاملی FOMO×AIU در SHAP
ii = shap.TreeExplainer(mb_).shap_interaction_values(feat)
R["shap"]["interaction_FOMO_AIU"] = float(np.abs(ii[:, list(feat.columns).index("FOMO"), list(feat.columns).index("AIU")]).mean()*2)
# پیش‌بینی خارج‌از‌نمونه برای نمودار
pred = cross_val_predict(models[best], feat, y, cv=5); R["ml_oof_r2"] = float(r2_score(y, pred))
np.save(os.path.join(OUT, "shap_values.npy"), sv); feat.to_csv(os.path.join(OUT, "features.csv"), index=False)
pd.Series({"best": best}).to_json(os.path.join(OUT, "best_model.json"))

json.dump(R, open(os.path.join(OUT, "results_paper2.json"), "w"), ensure_ascii=False, indent=1)

# ------------------------------------------------------------ ۸) خلاصه
print("N", R["n"], R["groups"]); print("CFA", {k: round(v, 3) for k, v in R["cfa"].items()}); print("SEM", {k: round(v, 3) for k, v in R["sem"].items()})
for f, v in R["rel"].items(): print(f, {k: round(x, 3) for k, x in v.items()})
for k, v in R["paths"].items(): print(k, {a: round(b, 3) for a, b in v.items()})
for k, v in R["indirect"].items(): print(k, {a: (round(b, 3) if not isinstance(b, bool) else b) for a, b in v.items()})
print("INV", {k: {a: round(b, 3) for a, b in v.items()} for k, v in R["invariance"].items()}, R["invariance_freed"])
for k, v in R["group_paths"].items(): print(k, round(v["g0"]["b"], 3), round(v["g1"]["b"], 3), "diff", round(v["diff"], 3), "z", round(v["z"], 2), "p", round(v["p"], 4), "boot", round(v["boot_lo"], 3), round(v["boot_hi"], 3))
print("ML", R["ml"], R["ml_tests"]); print("SHAP", R["shap"]); print("R2", R["r2"], "latent means", {k: (round(v["d"], 2), round(v["p"], 4)) for k, v in R["latent_mean_diff"].items()})
