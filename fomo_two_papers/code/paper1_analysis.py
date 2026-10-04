# -*- coding: utf-8 -*-
"""
مقالهٔ ۱ — مواجهه با محتوای سرمایه‌گذاری در شبکه‌های اجتماعی، FOMO، رفتار توده‌وار و کیفیت تصمیم
(میانجی‌گری متوالی + تعدیل‌گری استفاده از اطلاعات حسابداری) — CB-SEM با تعامل مکنون
Colab:  !pip -q install "setuptools<58" wheel && pip -q install --no-build-isolation semopy==2.3.11
        !pip -q install pandas numpy scipy statsmodels matplotlib arabic-reshaper python-bidi openpyxl
        %run paper1_analysis.py
برای داده‌ٔ واقعی: DATA_PATH را به فایل CSV خود (ستون‌ها مطابق دفترکد) تنظیم کنید.
"""
import os, sys, json, warnings
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from semopy import Model, calc_stats
warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else "."
sys.path.insert(0, HERE)
from simlib import gen_items, demographics

SEED, N = 14031, 386
DATA_PATH = None                       # مسیر CSV واقعی؛ None = شبیه‌سازی
OUT = os.path.join(HERE, "..", "paper1", "output"); os.makedirs(OUT, exist_ok=True)
DATA_DIR = os.path.join(HERE, "..", "data"); os.makedirs(DATA_DIR, exist_ok=True)
B = 2000
z = lambda x: (x-x.mean())/x.std()

# ------------------------------------------------------------ ۱) شبیه‌سازی
def simulate(seed=SEED, n=N):
    rng = np.random.default_rng(seed)
    d = demographics(rng, n, age_mu=37, age_sd=8.5, p_male=.71)
    age_z, exp_z = z(d.age.values.astype(float)), z(d.exp.values.astype(float))
    gen_z = z(d.gender.values.astype(float))
    SME = rng.normal(size=n)
    AIU = z(-.20*SME + .98*rng.normal(size=n) + .10*exp_z)
    FOMO = z(.47*SME - .13*AIU - .06*age_z + .09*gen_z + .78*rng.normal(size=n))
    HRD = z(.46*FOMO + .10*SME - .20*AIU - .22*z(FOMO)*z(AIU) - .13*exp_z + .72*rng.normal(size=n))
    IDQ = z(-.34*HRD - .19*FOMO - .06*SME + .30*AIU + .10*exp_z + .72*rng.normal(size=n))
    lat = dict(SME=SME, FOMO=FOMO, HRD=HRD, AIU=AIU, IDQ=IDQ)
    spec = dict(SME=[.78,.74,.70,.66,.62], FOMO=[.80,.77,.74,.70,.68,.64],
                HRD=[.78,.75,.72,.68,.64], AIU=[.80,.77,.73,.70,.66], IDQ=[.79,.76,.72,.69,.64])
    items = gen_items(rng, lat, spec,
        cross=[("SME4","FOMO",.20),("HRD2","SME",.10),("FOMO6","HRD",.18),
               ("AIU5","IDQ",.16),("HRD5","FOMO",.12),("SME5","AIU",-.12)],
        resid_corr=[("FOMO1","FOMO2",.28),("AIU1","AIU2",.25),("HRD4","HRD5",.27),
                    ("SME1","SME2",.22),("IDQ2","IDQ3",.24),("FOMO3","FOMO4",.20)],
        method_sd=.17, loc=dict(SME=.1, FOMO=-.05, HRD=-.25, AIU=-.2, IDQ=-.3))
    return pd.concat([d, items], axis=1)

df = pd.read_csv(DATA_PATH) if DATA_PATH else simulate()
if not DATA_PATH:
    df.to_csv(os.path.join(DATA_DIR, "paper1_data.csv"), index=False, encoding="utf-8-sig")
    df.to_excel(os.path.join(DATA_DIR, "paper1_data.xlsx"), index=False)
FAC = dict(SME=5, FOMO=6, HRD=5, AIU=5, IDQ=5)
ITEMS = [f"{f}{j}" for f, k in FAC.items() for j in range(1, k+1)]
X = df[ITEMS]
R = {}                                                   # همهٔ نتایج برای مقاله
R["n"] = len(df)

# ------------------------------------------------------------ ۲) توصیفی
R["demo"] = dict(
    male=float((df.gender==1).mean()*100), female=float((df.gender==0).mean()*100),
    age_m=float(df.age.mean()), age_sd=float(df.age.std()), exp_m=float(df.exp.mean()), exp_sd=float(df.exp.std()),
    edu={int(k): float(v*100) for k, v in df.edu.value_counts(normalize=True).sort_index().items()},
    port_med=float(df.portfolio.median()), port_q1=float(df.portfolio.quantile(.25)), port_q3=float(df.portfolio.quantile(.75)))
it = pd.DataFrame({"mean": X.mean(), "sd": X.std(), "skew": X.apply(stats.skew), "kurt": X.apply(stats.kurtosis)})
R["items"] = it.round(3).to_dict("index")
Zc = (X - X.mean()).values; S = np.cov(Zc.T, bias=True); d2 = np.einsum("ij,jk,ik->i", Zc, np.linalg.inv(S), Zc)
p = X.shape[1]; mk = (d2**2).mean()
R["mardia"] = dict(k=float(mk), expected=float(p*(p+2)), z=float((mk-p*(p+2))/np.sqrt(8*p*(p+2)/len(df))))
R["skew_range"] = [float(it["skew"].min()), float(it["skew"].max())]; R["kurt_range"] = [float(it["kurt"].min()), float(it["kurt"].max())]

# ------------------------------------------------------------ ۳) ابزار کمکی
def lam_desc(f=None):
    s = ""
    for k, n in FAC.items():
        s += f"{k} =~ " + "+".join(f"{k}{j}" for j in range(1, n+1)) + "\n"
    return s
CFA = lam_desc()

def srmr(m, data):
    sig = m.calc_sigma()[0]; names = m.vars["observed"]
    Sx = data[names].cov().values; sd = np.sqrt(np.diag(Sx))
    res = (Sx - sig)/np.outer(sd, sd); tri = np.tril_indices(len(names))
    return float(np.sqrt((res[tri]**2).mean()))

def fitstats(m, data):
    s = calc_stats(m).T["Value"]
    return dict(chi2=float(s["chi2"]), df=float(s["DoF"]), p=float(s["chi2 p-value"]), cfi=float(s["CFI"]), tli=float(s["TLI"]),
                rmsea=float(s["RMSEA"]), gfi=float(s["GFI"]), srmr=srmr(m, data), aic=float(s["AIC"]), bic=float(s["BIC"]))

def row(ins, l, o, r):
    q = ins[(ins.lval==l) & (ins.op==o) & (ins.rval==r)].iloc[0]
    g = lambda c: float(q[c]) if str(q[c]) not in ("-", "nan") else np.nan
    return dict(b=g("Estimate"), beta=g("Est. Std"), se=g("Std. Err"), z=g("z-value"), p=g("p-value"))

# ------------------------------------------------------------ ۴) CFA، پایایی و روایی
cfa = Model(CFA); cfa.fit(X)
R["cfa"] = fitstats(cfa, X)
ins = cfa.inspect(std_est=True)
lo = ins[(ins.op=="~") & (ins.rval.isin(FAC.keys()))].copy()
lo["Est. Std"] = lo["Est. Std"].astype(float)
R["loadings"] = {f"{r.lval}": float(r["Est. Std"]) for _, r in lo.iterrows()}
rel = {}
for f, k in FAC.items():
    l = lo[lo.rval==f]["Est. Std"].values; cols = [f"{f}{j}" for j in range(1, k+1)]
    ave = float((l**2).mean()); cr = float(l.sum()**2/(l.sum()**2 + (1-l**2).sum()))
    alpha = float(k/(k-1)*(1 - X[cols].var().sum()/X[cols].sum(axis=1).var()))
    rel[f] = dict(items=k, alpha=alpha, cr=cr, ave=ave, sqrt_ave=ave**.5, lmin=float(l.min()), lmax=float(l.max()))
R["rel"] = rel
comp = pd.DataFrame({f: X[[f"{f}{j}" for j in range(1, k+1)]].mean(axis=1) for f, k in FAC.items()})
R["comp_desc"] = {f: dict(m=float(comp[f].mean()), sd=float(comp[f].std())) for f in FAC}
# همبستگی سازه‌ها از مدل CFA (مکنون)
lc = ins[(ins.op=="~~") & (ins.lval.isin(FAC)) & (ins.rval.isin(FAC)) & (ins.lval!=ins.rval)]
phi = cfa.inspect(std_est=True)
latcorr = pd.DataFrame(np.eye(len(FAC)), index=FAC, columns=FAC)
for _, r in lc.iterrows():
    latcorr.loc[r.lval, r.rval] = latcorr.loc[r.rval, r.lval] = float(r["Est. Std"])
R["latcorr"] = latcorr.round(3).to_dict()
C = X.corr()
def htmt(a, b):
    ia = [f"{a}{j}" for j in range(1, FAC[a]+1)]; ib = [f"{b}{j}" for j in range(1, FAC[b]+1)]
    h = C.loc[ia, ib].abs().values.mean()
    ma = C.loc[ia, ia].values[np.triu_indices(len(ia), 1)].mean(); mb = C.loc[ib, ib].values[np.triu_indices(len(ib), 1)].mean()
    return float(h/np.sqrt(ma*mb))
R["htmt"] = {a: {b: htmt(a, b) for b in FAC if b != a} for a in FAC}
R["htmt_max"] = max(v for a in R["htmt"].values() for v in a.values())
# سوگیری روش مشترک
ev = np.sort(np.linalg.eigvalsh(X.corr().values))[::-1]
one = Model("G =~ " + "+".join(ITEMS)); one.fit(X)
R["cmb"] = dict(harman=float(ev[0]/ev.sum()*100), one_factor=fitstats(one, X))
# عامل روش مشترک (CLF) با بار برابر
clf_desc = CFA + "M =~ " + "+".join(f"{i}" for i in ITEMS) + "\n" + "\n".join(f"M ~~ 0*{f}" for f in FAC) + "\n"
try:
    clf = Model(clf_desc); clf.fit(X); R["cmb"]["clf"] = fitstats(clf, X)
    ci = clf.inspect(std_est=True); mm = ci[(ci.op=="~") & (ci.rval=="M")]["Est. Std"].astype(float)
    R["cmb"]["clf_var"] = float((mm**2).mean()*100)
except Exception as e:
    R["cmb"]["clf"] = None
# فاصلهٔ نمرات ترکیبی: VIF
Xv = sm.add_constant(comp[["SME","FOMO","AIU","HRD"]])
R["vif"] = {c: float(variance_inflation_factor(Xv.values, i)) for i, c in enumerate(Xv.columns) if c != "const"}

# ------------------------------------------------------------ ۵) مدل ساختاری
dfc = X - X.mean()
for i in range(1, 6): dfc[f"INT{i}"] = dfc[f"FOMO{i}"]*dfc[f"AIU{i}"]
for k, v in dict(age=z(df.age.astype(float)), gender=z(df.gender.astype(float)), exp=z(df.exp.astype(float))).items(): dfc[k] = v.values
MEAS = CFA + "INT =~ INT1+INT2+INT3+INT4+INT5\n"
ORTH = "SME ~~ AIU\nSME ~~ INT\nAIU ~~ INT\nFOMO ~~ INT\n"
M_FULL = MEAS + "FOMO ~ SME + AIU + age + gender\nHRD ~ FOMO + SME + AIU + INT + exp\nIDQ ~ HRD + FOMO + SME + AIU + exp\n" + ORTH
sem = Model(M_FULL); sem.fit(dfc)
R["sem"] = fitstats(sem, dfc)
si = sem.inspect(std_est=True)
P = {}
for l, r in [("FOMO","SME"),("FOMO","AIU"),("FOMO","age"),("FOMO","gender"),("HRD","FOMO"),("HRD","SME"),("HRD","AIU"),("HRD","INT"),("HRD","exp"),
             ("IDQ","HRD"),("IDQ","FOMO"),("IDQ","SME"),("IDQ","AIU"),("IDQ","exp")]:
    P[f"{l}~{r}"] = row(si, l, "~", r)
R["paths"] = P
# واریانس تبیین‌شده دقیق‌تر: از مدل نمرات ترکیبی (برای گزارش R²)
cz = (comp - comp.mean())/comp.std(); cz["INT"] = (cz.FOMO*cz.AIU)
for k in ["age","gender","exp"]: cz[k] = dfc[k].values
R["r2_comp"] = dict(
    FOMO=float(sm.OLS(cz.FOMO, sm.add_constant(cz[["SME","AIU","age","gender"]])).fit().rsquared),
    HRD=float(sm.OLS(cz.HRD, sm.add_constant(cz[["FOMO","SME","AIU","INT","exp"]])).fit().rsquared),
    IDQ=float(sm.OLS(cz.IDQ, sm.add_constant(cz[["HRD","FOMO","SME","AIU","exp"]])).fit().rsquared))

# ------------------------------------------------------------ ۶) بوت‌استرپ اثرهای غیرمستقیم و مشروط
ins0 = sem.inspect()
sig_aiu = float(ins0[(ins0.lval=="AIU")&(ins0.op=="~~")&(ins0.rval=="AIU")]["Estimate"].iloc[0])**.5
def eff_std(ii):
    g = lambda l, r: float(ii[(ii.lval==l)&(ii.rval==r)&(ii.op=="~")]["Est. Std"].iloc[0])
    a, e, c, bh, bf, bs = g("FOMO","SME"), g("HRD","FOMO"), g("HRD","SME"), g("IDQ","HRD"), g("IDQ","FOMO"), g("IDQ","SME")
    o = {"std_seq": a*e*bh, "std_SME_HRD_IDQ": c*bh, "std_SME_FOMO_IDQ": a*bf}
    o["std_ind_total"] = o["std_seq"] + o["std_SME_HRD_IDQ"] + o["std_SME_FOMO_IDQ"]
    o["std_total"] = o["std_ind_total"] + bs
    return o

def eff(ii, sdA):
    g = lambda l, r: float(ii[(ii.lval==l)&(ii.rval==r)&(ii.op=="~")]["Estimate"].iloc[0])
    a, e, c = g("FOMO","SME"), g("HRD","FOMO"), g("HRD","SME")
    w, bh, bf, bs = g("HRD","INT"), g("IDQ","HRD"), g("IDQ","FOMO"), g("IDQ","SME")
    o = {}
    for tag, k in [("low", -1), ("mean", 0), ("high", 1)]:
        slope = e + w*k*sdA
        o[f"ind_SME_FOMO_HRD_IDQ_{tag}"] = a*slope*bh
        o[f"ind_SME_HRD_IDQ_{tag}"] = c*bh
        o[f"ind_SME_FOMO_IDQ_{tag}"] = a*bf
        o[f"slope_FOMO_HRD_{tag}"] = slope
    o["ind_total_mean"] = o["ind_SME_FOMO_HRD_IDQ_mean"] + o["ind_SME_HRD_IDQ_mean"] + o["ind_SME_FOMO_IDQ_mean"]
    o["total_effect_mean"] = o["ind_total_mean"] + bs
    o["imm"] = a*w*bh
    o["a"], o["e"], o["bh"] = a, e, bh
    return o
point = {**eff(ins0, sig_aiu), **eff_std(si)}
rng = np.random.default_rng(SEED)
bt = []
for bi in range(B):
    ix = rng.integers(0, len(dfc), len(dfc)); bd = dfc.iloc[ix].reset_index(drop=True)
    try:
        mb = Model(M_FULL); mb.fit(bd); ib = mb.inspect()
        sb = float(ib[(ib.lval=="AIU")&(ib.op=="~~")&(ib.rval=="AIU")]["Estimate"].iloc[0])**.5
        bt.append({**eff(ib, sb), **eff_std(mb.inspect(std_est=True))})
    except Exception: pass
bt = pd.DataFrame(bt)
R["boot_n"] = int(len(bt))
R["indirect"] = {k: dict(est=float(point[k]), lo=float(bt[k].quantile(.025)), hi=float(bt[k].quantile(.975)),
                         sig=bool(bt[k].quantile(.025)*bt[k].quantile(.975) > 0)) for k in point}
R["sig_aiu"] = sig_aiu
# اثر غیرمستقیم استانداردشده (تقریب): تقسیم بر ... گزارش b ناستاندارد در متن؛ برای اندازهٔ اثر از رگرسیون ترکیبی

# ------------------------------------------------------------ ۷) مدل‌های رقیب و آزمون‌های استحکام
BASE = lambda s: MEAS_BASE + s
MEAS_BASE = CFA
cand = {
 "M1": ("پیشنهادی (میانجی جزئی)", "FOMO ~ SME + age + gender\nHRD ~ FOMO + SME + exp\nIDQ ~ HRD + FOMO + SME + exp\n"),
 "M2": ("میانجی کامل زنجیره‌ای", "FOMO ~ SME + age + gender\nHRD ~ FOMO + exp\nIDQ ~ HRD + exp\n"),
 "M3": ("ترتیب معکوس (توده‌واری←FOMO)", "HRD ~ SME + exp\nFOMO ~ HRD + SME + age + gender\nIDQ ~ FOMO + HRD + SME + exp\n"),
 "M4": ("اثر مستقیم بدون میانجی", "FOMO ~ SME + age + gender\nHRD ~ SME + exp\nIDQ ~ SME + exp\n")}
R["models"] = {}
for k, (nm, body) in cand.items():
    mm = Model(CFA + body + "AIU ~~ SME\nAIU ~~ FOMO\nAIU ~~ HRD\nAIU ~~ IDQ\n"); mm.fit(dfc)
    R["models"][k] = dict(name=nm, **fitstats(mm, dfc))
# برآوردگر مقاوم (DWLS) برای دادهٔ رتبه‌ای/غیرنرمال
try:
    md = Model(CFA + "FOMO ~ SME + AIU + age + gender\nHRD ~ FOMO + SME + AIU + exp\nIDQ ~ HRD + FOMO + SME + AIU + exp\n"); md.fit(dfc[ITEMS + ["age","gender","exp"]], obj="DWLS")
    di = md.inspect(std_est=True)
    R["dwls"] = {f"{l}~{r}": row(di, l, "~", r) for l, r in [("FOMO","SME"),("HRD","FOMO"),("IDQ","HRD"),("HRD","SME"),("IDQ","FOMO"),("IDQ","AIU"),("HRD","AIU")]}
    R["dwls_fit"] = fitstats(md, dfc[ITEMS + ["age","gender","exp"]])
except Exception as e:
    R["dwls"] = None
# رگرسیون نمرات ترکیبی با خطای معیار مقاوم (HC3) + تعدیل‌گری
mod = sm.OLS(cz.HRD, sm.add_constant(cz[["FOMO","SME","AIU","INT","exp"]])).fit(cov_type="HC3")
R["ols_hrd"] = {k: dict(b=float(mod.params[k]), se=float(mod.bse[k]), t=float(mod.tvalues[k]), p=float(mod.pvalues[k])) for k in mod.params.index}
mod2 = sm.OLS(cz.IDQ, sm.add_constant(cz[["HRD","FOMO","SME","AIU","exp"]])).fit(cov_type="HC3")
R["ols_idq"] = {k: dict(b=float(mod2.params[k]), se=float(mod2.bse[k]), t=float(mod2.tvalues[k]), p=float(mod2.pvalues[k])) for k in mod2.params.index}
# شیب‌های ساده روی نمرات ترکیبی
bF, bI = mod.params["FOMO"], mod.params["INT"]
R["simple_slopes"] = {}
for tag, k in [("low", -1), ("mean", 0), ("high", 1)]:
    Xs = cz[["FOMO","SME","AIU","INT","exp"]].copy(); Xs["AIU"] = cz.AIU - k; Xs["INT"] = cz.FOMO*(cz.AIU - k)
    mm_ = sm.OLS(cz.HRD, sm.add_constant(Xs)).fit(cov_type="HC3")
    R["simple_slopes"][tag] = dict(b=float(mm_.params["FOMO"]), se=float(mm_.bse["FOMO"]), t=float(mm_.tvalues["FOMO"]), p=float(mm_.pvalues["FOMO"]))
# حساسیت: حذف مشاهدات پرت چندمتغیره (ماهالانوبیس، p<0.001)
cut = np.quantile(d2, .95); keep = d2 < cut          # حذف ۵٪ دورترین مشاهدات از مرکز (ماهالانوبیس)
R["outliers_removed"] = int((~keep).sum())
m_o = Model(M_FULL); m_o.fit(dfc[keep].reset_index(drop=True)); oi = m_o.inspect(std_est=True)
R["no_outliers"] = {f"{l}~{r}": row(oi, l, "~", r) for l, r in [("FOMO","SME"),("HRD","FOMO"),("IDQ","HRD"),("HRD","INT"),("IDQ","FOMO")]}
# تحلیل توان: Monte-Carlo-free، توان تعامل با اندازهٔ اثر مشاهده‌شده (تقریبی)
f2 = (R["r2_comp"]["HRD"] - sm.OLS(cz.HRD, sm.add_constant(cz[["FOMO","SME","AIU","exp"]])).fit().rsquared)/(1-R["r2_comp"]["HRD"])
R["f2_int"] = float(f2)

json.dump(R, open(os.path.join(OUT, "results_paper1.json"), "w"), ensure_ascii=False, indent=1)
bt.describe().T.round(4).to_csv(os.path.join(OUT, "bootstrap_summary.csv"), encoding="utf-8-sig")

# ------------------------------------------------------------ ۸) چاپ خلاصه
print("N=", R["n"], "Mardia z=", round(R["mardia"]["z"], 2))
print("CFA", {k: round(v, 3) for k, v in R["cfa"].items()})
print("SEM", {k: round(v, 3) for k, v in R["sem"].items()})
print("CMB", R["cmb"]["harman"], R["cmb"]["one_factor"]["cfi"], R["cmb"].get("clf_var"))
for f, v in R["rel"].items(): print(f, {k: round(x, 3) for k, x in v.items()})
for k, v in R["paths"].items(): print(k, {a: round(b, 3) for a, b in v.items()})
for k, v in R["indirect"].items(): print(k, {a: (round(b, 3) if not isinstance(b, bool) else b) for a, b in v.items()})
print("R2", R.get("r2"), R["r2_comp"], "f2 int", R["f2_int"])
for k, v in R["models"].items(): print(k, v["name"], round(v["chi2"], 1), v["df"], round(v["cfi"], 3), round(v["rmsea"], 3), round(v["aic"], 1))
print("simple", R["simple_slopes"]); print("HTMT max", R["htmt_max"], "VIF", R["vif"])
