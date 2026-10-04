# -*- coding: utf-8 -*-
"""
Paper 3 — Generative-AI use, competence illusion, uncritical reliance, verification and investment decision quality:
moderation by financial knowledge and AI literacy (fully latent CB-SEM; no item-mean composites).
Colab:  !pip -q install "setuptools<58" wheel && pip -q install --no-build-isolation semopy==2.3.11
        !pip -q install pandas numpy scipy statsmodels matplotlib openpyxl
        %run paper3_analysis.py          (simlib.py next to this file; for real data set DATA_PATH)
"""
import os, sys, json, warnings
import numpy as np, pandas as pd
from scipy import stats
import statsmodels.api as sm
from semopy import Model, calc_stats
warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else "."
sys.path.insert(0, HERE)
# ---- simlib.py (inlined) ----
"""توابع مشترک شبیه‌سازی (واقع‌نما): بارهای عاملی متفاوت، بارگذاری متقاطع کوچک،
همبستگی خطای مجاور، عامل روش مشترک ضعیف و آستانه‌های نامتقارن لیکرت."""
import numpy as np, pandas as pd

def likert(z, thresholds):
    return np.digitize(z, thresholds) + 1

def gen_items(rng, lat, spec, cross=None, resid_corr=None, method_sd=0.10, loc=None, spread=0.22, dif=None):
    """lat: dict نام عامل -> بردار استاندارد؛ spec: dict عامل -> فهرست بارها.
    cross: فهرست (گویه, عامل, بار)؛ resid_corr: فهرست (گویه۱, گویه۲, همبستگی خطا)"""
    n = len(next(iter(lat.values())))
    names, load_rows = [], {}
    for f, ls in spec.items():
        for j, l in enumerate(ls, 1):
            nm = f"{f}{j}"; names.append(nm); load_rows[nm] = {f: l}
    for it, f, l in (cross or []):
        load_rows[it][f] = l
    meth = rng.normal(size=n)
    E = rng.normal(size=(n, len(names)))
    idx = {nm: i for i, nm in enumerate(names)}
    for a, b, r in (resid_corr or []):
        E[:, idx[b]] = r*E[:, idx[a]] + np.sqrt(1-r**2)*E[:, idx[b]]
    out = {}
    base = np.array([-1.40, -0.50, 0.40, 1.25])
    for nm in names:
        sig = sum(l*lat[f] for f, l in load_rows[nm].items())
        expl = sum(l**2 for l in load_rows[nm].values()) + method_sd**2
        res = np.sqrt(max(1e-6, 1-expl))
        y = sig + method_sd*meth + res*E[:, idx[nm]]
        y = (y - y.mean())/y.std()
        if dif and nm in dif: y = y + dif[nm]          # کارکرد افتراقی گویه (DIF) بین گروه‌ها
        f0 = nm.rstrip("0123456789")
        sh = (loc or {}).get(f0, 0.0) + rng.normal(0, spread)
        out[nm] = likert(y, base - sh)
    return pd.DataFrame(out)

def demographics(rng, n, age_mu=38, age_sd=9, p_male=.70, exp_shape=2.4, exp_scale=2.8, edu_p=(.10,.47,.34,.09)):
    age = np.clip(rng.normal(age_mu, age_sd, n).round(), 20, 68).astype(int)
    gender = (rng.random(n) < p_male).astype(int)       # 1 = مرد
    edu = rng.choice([1,2,3,4], n, p=edu_p)              # 1 دیپلم .. 4 دکتری
    exp = np.clip(rng.gamma(exp_shape, exp_scale, n).round(), 1, 30).astype(int)
    port = np.round(np.exp(rng.normal(5.3, 1.05, n))).astype(int)
    return pd.DataFrame(dict(gender=gender, age=age, edu=edu, exp=exp, portfolio=port))

# ---- end simlib.py ----

SEED, N = 31415, 428
DATA_PATH = None
OUT = os.path.join(HERE, "output"); os.makedirs(OUT, exist_ok=True)
DATA_DIR = os.path.join(HERE, "output"); os.makedirs(DATA_DIR, exist_ok=True)
B = int(os.environ.get("BOOT", 2000))
z = lambda x: (x-x.mean())/x.std()

# ------------------------------------------------------------ 1) simulation
def simulate(seed=SEED, n=N):
    rng = np.random.default_rng(seed)
    d = demographics(rng, n, age_mu=36, age_sd=8.5, p_male=.69, exp_shape=2.5, exp_scale=2.7, edu_p=(.08,.45,.36,.11))
    age_z, exp_z, gen_z = z(d.age.values.astype(float)), z(d.exp.values.astype(float)), z(d.gender.values.astype(float))
    AIL = rng.normal(size=n)
    ability = z(.35*AIL + .94*rng.normal(size=n))
    GUI = z(.15*AIL + .10*ability - .18*age_z + .08*gen_z + .95*rng.normal(size=n))
    # objective 8-item knowledge test (binary)
    diff = np.array([-1.0, -.6, -.2, .1, .3, .6, .9, 1.2])
    pc = 1/(1+np.exp(-(1.1*ability[:, None] - diff[None, :])))
    FK = (rng.random((n, 8)) < pc).astype(int); score = FK.sum(1); FKz = z(score.astype(float))
    gf = z(GUI*FKz); ga = z(GUI*AIL)
    PCA = z(.42*GUI - .10*FKz - .20*gf + .82*rng.normal(size=n))
    CGl = z(.36*GUI - .26*FKz - .30*gf - .10*AIL + .82*rng.normal(size=n))
    pred = np.clip(np.round(score + 1.15*CGl + rng.normal(0, .7, n)), 0, 8).astype(int)
    CG = pred - score
    UR = z(.38*GUI - .22*AIL - .32*ga + .82*rng.normal(size=n))
    VER = z(.15*GUI + .34*AIL + .20*ga + .82*rng.normal(size=n))
    IDQ = z(-.22*PCA - .28*UR + .24*VER - .18*z(CG.astype(float)) - .05*GUI + .12*FKz + .08*exp_z + .74*rng.normal(size=n))
    p_wrong = 1/(1+np.exp(-(-.2 + .9*UR - .6*VER)))
    VIG = rng.binomial(2, p_wrong)
    lat = dict(GUI=GUI, PCA=PCA, UR=UR, VER=VER, AIL=AIL, IDQ=IDQ)
    spec = dict(GUI=[.82,.80,.76,.72], PCA=[.80,.77,.74,.70], UR=[.79,.76,.72,.68], VER=[.78,.75,.72,.68],
                AIL=[.80,.78,.75,.72,.69,.66], IDQ=[.79,.76,.72,.69,.64])
    items = gen_items(rng, lat, spec,
        cross=[("PCA3","UR",.14),("UR2","GUI",.12),("VER4","AIL",.14),("GUI3","PCA",.14),("IDQ5","VER",.12),("AIL6","VER",.13)],
        resid_corr=[("GUI1","GUI2",.22),("PCA1","PCA2",.24),("UR1","UR2",.22),("VER1","VER2",.22),("AIL1","AIL2",.20),("IDQ2","IDQ3",.22),("AIL5","AIL6",.18)],
        method_sd=.16, loc=dict(GUI=-.20, PCA=.10, UR=.0, VER=-.10, AIL=-.10, IDQ=-.25))
    fk = pd.DataFrame(FK, columns=[f"FK{i}" for i in range(1, 9)])
    extra = pd.DataFrame(dict(FKscore=score, PredScore=pred, CG=CG, VIGERR=VIG))
    return pd.concat([d, items, fk, extra], axis=1)

df = pd.read_csv(DATA_PATH) if DATA_PATH else simulate()
if not DATA_PATH:
    df.to_csv(os.path.join(DATA_DIR, "paper3_data.csv"), index=False, encoding="utf-8-sig")
    df.to_excel(os.path.join(DATA_DIR, "paper3_data.xlsx"), index=False)
FAC = dict(GUI=4, PCA=4, UR=4, VER=4, AIL=6, IDQ=5)
ITEMS = [f"{f}{j}" for f, k in FAC.items() for j in range(1, k+1)]
X = df[ITEMS]; R = {"n": len(df)}

# ------------------------------------------------------------ 2) descriptives
R["demo"] = dict(male=float((df.gender==1).mean()*100), age_m=float(df.age.mean()), age_sd=float(df.age.std()), exp_m=float(df.exp.mean()), exp_sd=float(df.exp.std()),
    edu={int(k): float(v*100) for k, v in df.edu.value_counts(normalize=True).sort_index().items()}, port_med=float(df.portfolio.median()),
    users_pct=float((df.GUI1 >= 3).mean()*100))
it = pd.DataFrame({"mean": X.mean(), "sd": X.std(), "skew": X.apply(stats.skew), "kurt": X.apply(stats.kurtosis)}); R["items"] = it.round(3).to_dict("index")
R["skew_range"] = [float(it["skew"].min()), float(it["kurt"].max())]; R["skew_range"] = [float(it["skew"].min()), float(it["skew"].max())]; R["kurt_range"] = [float(it["kurt"].min()), float(it["kurt"].max())]
Zc = (X - X.mean()).values; S_ = np.cov(Zc.T, bias=True); d2 = np.einsum("ij,jk,ik->i", Zc, np.linalg.inv(S_), Zc); p_ = X.shape[1]; mk = (d2**2).mean()
R["mardia"] = dict(k=float(mk), expected=float(p_*(p_+2)), z=float((mk-p_*(p_+2))/np.sqrt(8*p_*(p_+2)/len(df))))
# objective test
fkc = [f"FK{i}" for i in range(1, 9)]; pq = (df[fkc].mean()*(1-df[fkc].mean())).sum()
R["fk"] = dict(p_correct={c: float(df[c].mean()) for c in fkc}, kr20=float(8/7*(1 - pq/df[fkc].sum(axis=1).var())), mean=float(df.FKscore.mean()), sd=float(df.FKscore.std()),
               pred_mean=float(df.PredScore.mean()), cg_mean=float(df.CG.mean()), cg_sd=float(df.CG.std()), cg_pos_pct=float((df.CG > 0).mean()*100))
r_, p_r = stats.pearsonr(df.CG, X.GUI1)    # descriptive check only (not used in models)
R["cg_gui_r"] = dict(r=float(r_), p=float(p_r))

def srmr(m, data):
    sig = m.calc_sigma()[0]; names = m.vars["observed"]; Sx = data[names].cov().values; sd = np.sqrt(np.diag(Sx))
    res = (Sx - sig)/np.outer(sd, sd); tri = np.tril_indices(len(names)); return float(np.sqrt((res[tri]**2).mean()))
def fitstats(m, data):
    s = calc_stats(m).T["Value"]
    return dict(chi2=float(s["chi2"]), df=float(s["DoF"]), p=float(s["chi2 p-value"]), cfi=float(s["CFI"]), tli=float(s["TLI"]), rmsea=float(s["RMSEA"]), gfi=float(s["GFI"]), srmr=srmr(m, data), aic=float(s["AIC"]), bic=float(s["BIC"]))
def row(ins, l, o, r):
    q = ins[(ins.lval==l) & (ins.op==o) & (ins.rval==r)].iloc[0]
    g = lambda c: float(q[c]) if str(q[c]) not in ("-", "nan") else np.nan
    return dict(b=g("Estimate"), beta=g("Est. Std"), se=g("Std. Err"), z=g("z-value"), p=g("p-value"))
CFA = "".join(f"{k} =~ " + "+".join(f"{k}{j}" for j in range(1, n+1)) + "\n" for k, n in FAC.items())

# ------------------------------------------------------------ 3) CFA
cfa = Model(CFA); cfa.fit(X); R["cfa"] = fitstats(cfa, X)
ins = cfa.inspect(std_est=True)
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
def vif_latent(preds):
    iv = np.linalg.inv(latcorr.loc[preds, preds].values); return {p: float(iv[i, i]) for i, p in enumerate(preds)}
R["vif"] = {"IDQ": vif_latent(["PCA", "UR", "VER", "GUI", "AIL"]), "all_max_corr": float(max(abs(latcorr.loc[a, b]) for a in FAC for b in FAC if a != b))}

# ------------------------------------------------------------ 4) structural model with two latent interactions
dfc = X - X.mean()
FKz = z(df.FKscore.astype(float)).values; CGz = z(df.CG.astype(float)).values
for i in range(1, 5):
    dfc[f"IA{i}"] = dfc[f"GUI{i}"]*dfc[f"AIL{i}"]            # GUI x AIL (matched pairs)
    dfc[f"IF{i}"] = dfc[f"GUI{i}"]*FKz                        # GUI x FK (observed, standardized)
dfc["FKz"] = FKz; dfc["CGz"] = CGz; dfc["VIGERR"] = df.VIGERR.values.astype(float)
for k, v in dict(age=z(df.age.astype(float)), gender=z(df.gender.astype(float)), exp=z(df.exp.astype(float))).items(): dfc[k] = v.values
MEAS = CFA + "INTA =~ IA1+IA2+IA3+IA4\nINTF =~ IF1+IF2+IF3+IF4\n"
COV = "GUI ~~ AIL\nGUI ~~ FKz\nAIL ~~ FKz\nGUI ~~ INTA\nGUI ~~ INTF\nAIL ~~ INTA\nAIL ~~ INTF\nFKz ~~ INTA\nFKz ~~ INTF\nINTA ~~ INTF\n"
BODY = "PCA ~ GUI + FKz + INTF\nCGz ~ GUI + FKz + AIL + INTF\nUR ~ GUI + AIL + INTA\nVER ~ GUI + AIL + INTA\nIDQ ~ PCA + UR + VER + CGz + GUI + FKz + AIL + exp + age + gender\n"
M_FULL = MEAS + BODY + COV
sem = Model(M_FULL); sem.fit(dfc); R["sem"] = fitstats(sem, dfc); si = sem.inspect(std_est=True)
PAIRS = [("PCA","GUI"),("PCA","FKz"),("PCA","INTF"),("CGz","GUI"),("CGz","FKz"),("CGz","AIL"),("CGz","INTF"),("UR","GUI"),("UR","AIL"),("UR","INTA"),("VER","GUI"),("VER","AIL"),("VER","INTA"),
         ("IDQ","PCA"),("IDQ","UR"),("IDQ","VER"),("IDQ","CGz"),("IDQ","GUI"),("IDQ","FKz"),("IDQ","AIL"),("IDQ","exp"),("IDQ","age"),("IDQ","gender")]
R["paths"] = {f"{l}~{r}": row(si, l, "~", r) for l, r in PAIRS}
def latent_r2(ii, dvs):
    out = {}
    for dv in dvs:
        q = ii[(ii.lval == dv) & (ii.op == "~~") & (ii.rval == dv)].iloc[0]; out[dv] = float(1 - float(q["Est. Std"]))
    return out
R["r2"] = latent_r2(si, ["PCA", "CGz", "UR", "VER", "IDQ"])
iu = sem.inspect(); psi = lambda dv: float(iu[(iu.lval == dv) & (iu.op == "~~") & (iu.rval == dv)]["Estimate"].iloc[0])
R["sd_latent"] = {"GUI": psi("GUI")**.5, "AIL": psi("AIL")**.5, **{k: (psi(k)/(1-R["r2"][k]))**.5 for k in ["PCA", "UR", "VER", "IDQ"]}}
R["sem_loadings"] = {r.lval: float(r["Est. Std"]) for _, r in si[(si.op == "~") & (si.rval.isin(list(FAC)))].iterrows()}
R["n_obs_vars"] = len(sem.vars["observed"]); R["n_params_sem"] = int(R["n_obs_vars"]*(R["n_obs_vars"]+1)/2 - R["sem"]["df"]); R["n_params_cfa"] = int(len(ITEMS)*(len(ITEMS)+1)/2 - R["cfa"]["df"])
# interaction effect sizes: R2 with vs without the interaction paths (same variable set)
NOI = MEAS + "PCA ~ GUI + FKz\nCGz ~ GUI + FKz + AIL\nUR ~ GUI + AIL\nVER ~ GUI + AIL\nIDQ ~ PCA + UR + VER + CGz + GUI + FKz + AIL + exp + age + gender\n" + COV
m_ni = Model(NOI); m_ni.fit(dfc); R["fit_noint"] = fitstats(m_ni, dfc); r2n = latent_r2(m_ni.inspect(std_est=True), ["PCA", "CGz", "UR", "VER", "IDQ"]); R["r2_noint"] = r2n
R["f2_int"] = {k: float((R["r2"][k]-r2n[k])/(1-R["r2"][k])) for k in ["PCA", "CGz", "UR", "VER"]}

# ------------------------------------------------------------ 5) bootstrap: indirect and conditional indirect effects
sA = R["sd_latent"]["AIL"]
def eff(ii, sdA):
    g = lambda l, r: float(ii[(ii.lval==l)&(ii.rval==r)&(ii.op=="~")]["Estimate"].iloc[0])
    o = {}
    aP, wP, bP = g("PCA","GUI"), g("PCA","INTF"), g("IDQ","PCA"); aC, wC, bC = g("CGz","GUI"), g("CGz","INTF"), g("IDQ","CGz")
    aU, wU, bU = g("UR","GUI"), g("UR","INTA"), g("IDQ","UR"); aV, wV, bV = g("VER","GUI"), g("VER","INTA"), g("IDQ","VER"); c = g("IDQ","GUI")
    for tag, k in [("low", -1), ("mean", 0), ("high", 1)]:
        o[f"ind_PCA_{tag}"] = (aP + wP*k)*bP; o[f"ind_CG_{tag}"] = (aC + wC*k)*bC
        o[f"ind_UR_{tag}"] = (aU + wU*sdA*k)*bU; o[f"ind_VER_{tag}"] = (aV + wV*sdA*k)*bV
        o[f"slope_PCA_{tag}"] = aP + wP*k; o[f"slope_CG_{tag}"] = aC + wC*k; o[f"slope_UR_{tag}"] = aU + wU*sdA*k; o[f"slope_VER_{tag}"] = aV + wV*sdA*k
        o[f"ind_illusion_{tag}"] = o[f"ind_PCA_{tag}"] + o[f"ind_CG_{tag}"]
    o["imm_PCA"] = wP*bP; o["imm_CG"] = wC*bC; o["imm_UR"] = wU*sdA*bU; o["imm_VER"] = wV*sdA*bV
    o["total_ind_mean"] = o["ind_PCA_mean"] + o["ind_CG_mean"] + o["ind_UR_mean"] + o["ind_VER_mean"]; o["total_mean"] = o["total_ind_mean"] + c
    o["ind_reliance_mean"] = o["ind_UR_mean"]; o["ind_calib_mean"] = o["ind_VER_mean"]
    return o
def eff_std(ii):
    g = lambda l, r: float(ii[(ii.lval==l)&(ii.rval==r)&(ii.op=="~")]["Est. Std"].iloc[0])
    o = {"std_PCA": g("PCA","GUI")*g("IDQ","PCA"), "std_CG": g("CGz","GUI")*g("IDQ","CGz"), "std_UR": g("UR","GUI")*g("IDQ","UR"), "std_VER": g("VER","GUI")*g("IDQ","VER")}
    o["std_ind_total"] = sum(o.values()); o["std_total"] = o["std_ind_total"] + g("IDQ","GUI"); return o
point = {**eff(iu, sA), **eff_std(si)}
rng = np.random.default_rng(SEED); bt = []
for bi in range(B):
    ix = rng.integers(0, len(dfc), len(dfc)); bd = dfc.iloc[ix].reset_index(drop=True)
    try:
        mb = Model(M_FULL); mb.fit(bd); ib = mb.inspect(); sb = float(ib[(ib.lval=="AIL")&(ib.op=="~~")&(ib.rval=="AIL")]["Estimate"].iloc[0])**.5
        bt.append({**eff(ib, sb), **eff_std(mb.inspect(std_est=True))})
    except Exception: pass
bt = pd.DataFrame(bt); R["boot_n"] = int(len(bt))
R["indirect"] = {k: dict(est=float(point[k]), lo=float(bt[k].quantile(.025)), hi=float(bt[k].quantile(.975)), sig=bool(bt[k].quantile(.025)*bt[k].quantile(.975) > 0)) for k in point}

# ------------------------------------------------------------ 6) competing models and robustness
def mk(body): return Model(MEAS + body + COV)
cand = {
 "M1": ("Full model (illusion + reliance paths, two moderators)", BODY),
 "M2": ("No moderation (interaction paths removed)", "PCA ~ GUI + FKz\nCGz ~ GUI + FKz + AIL\nUR ~ GUI + AIL\nVER ~ GUI + AIL\nIDQ ~ PCA + UR + VER + CGz + GUI + FKz + AIL + exp + age + gender\n"),
 "M3": ("Illusion paths only (UR, VER do not predict IDQ)", "PCA ~ GUI + FKz + INTF\nCGz ~ GUI + FKz + AIL + INTF\nUR ~ GUI + AIL + INTA\nVER ~ GUI + AIL + INTA\nIDQ ~ PCA + CGz + GUI + FKz + AIL + exp + age + gender\n"),
 "M4": ("Reliance/verification paths only (PCA, CG do not predict IDQ)", "PCA ~ GUI + FKz + INTF\nCGz ~ GUI + FKz + AIL + INTF\nUR ~ GUI + AIL + INTA\nVER ~ GUI + AIL + INTA\nIDQ ~ UR + VER + GUI + FKz + AIL + exp + age + gender\n"),
 "M5": ("Direct effect only (no mediators)", "PCA ~ GUI + FKz + INTF\nCGz ~ GUI + FKz + AIL + INTF\nUR ~ GUI + AIL + INTA\nVER ~ GUI + AIL + INTA\nIDQ ~ GUI + FKz + AIL + exp + age + gender\n")}
R["models"] = {}
for k, (nm, body) in cand.items():
    mm = mk(body); mm.fit(dfc); R["models"][k] = dict(name=nm, **fitstats(mm, dfc))
keyp = [("PCA","GUI"),("CGz","GUI"),("UR","GUI"),("VER","GUI"),("IDQ","PCA"),("IDQ","UR"),("IDQ","VER"),("IDQ","CGz")]
def keyrow(ii): return {f"{l}~{r}": row(ii, l, "~", r) for l, r in keyp}
# (a) DWLS, no interactions
try:
    md = Model(CFA + "PCA ~ GUI + FKz\nCGz ~ GUI + FKz + AIL\nUR ~ GUI + AIL\nVER ~ GUI + AIL\nIDQ ~ PCA + UR + VER + CGz + GUI + FKz + AIL + exp + age + gender\nGUI ~~ AIL\nGUI ~~ FKz\nAIL ~~ FKz\n")
    cols_ = ITEMS + ["FKz", "CGz", "exp", "age", "gender"]; md.fit(dfc[cols_], obj="DWLS"); R["dwls"] = keyrow(md.inspect(std_est=True)); R["dwls_fit"] = fitstats(md, dfc[cols_])
except Exception as e: R["dwls"] = None
# (b) residual-centred product indicators
dfr = dfc.copy(); Xf = sm.add_constant(dfc[[f"GUI{i}" for i in range(1, 5)] + [f"AIL{i}" for i in range(1, 7)]].assign(FKz=FKz).values)
for pre in ("IA", "IF"):
    for i in range(1, 5):
        pr = dfc[f"{pre}{i}"].values; dfr[f"{pre}{i}"] = pr - Xf @ np.linalg.lstsq(Xf, pr, rcond=None)[0]
m_rc = Model(M_FULL); m_rc.fit(dfr); rci = m_rc.inspect(std_est=True); R["resid_centered"] = {**keyrow(rci), **{f"{l}~{r}": row(rci, l, "~", r) for l, r in [("PCA","INTF"),("CGz","INTF"),("UR","INTA"),("VER","INTA")]}}; R["resid_centered_fit"] = fitstats(m_rc, dfr)
# (c) respecified with the four largest within-factor residual correlations
sg = cfa.calc_sigma()[0]; nm_ = cfa.vars["observed"]; Sx = X[nm_].cov().values; sdv = np.sqrt(np.diag(Sx)); res_ = (Sx - sg)/np.outer(sdv, sdv); pairs = []
for i_ in range(len(nm_)):
    for j_ in range(i_):
        if nm_[i_].rstrip("0123456789") == nm_[j_].rstrip("0123456789"): pairs.append((abs(res_[i_, j_]), nm_[j_], nm_[i_]))
pairs = sorted(pairs, reverse=True)[:4]; add_ = "".join(f"{a} ~~ {b}\n" for _, a, b in pairs)
m_rs = Model(M_FULL + add_); m_rs.fit(dfc); rsi = m_rs.inspect(std_est=True); R["respec"] = dict(pairs=[(a, b) for _, a, b in pairs], fit=fitstats(m_rs, dfc), paths={**keyrow(rsi), **{f"{l}~{r}": row(rsi, l, "~", r) for l, r in [("PCA","INTF"),("CGz","INTF"),("UR","INTA"),("VER","INTA")]}})
# (d) trimmed 5 % (Mahalanobis)
keep = d2 < np.quantile(d2, .95); R["outliers_removed"] = int((~keep).sum())
m_o = Model(M_FULL); m_o.fit(dfc[keep].reset_index(drop=True)); oi = m_o.inspect(std_est=True); R["trimmed"] = {**keyrow(oi), **{f"{l}~{r}": row(oi, l, "~", r) for l, r in [("PCA","INTF"),("CGz","INTF"),("UR","INTA"),("VER","INTA")]}}; R["trimmed_fit"] = fitstats(m_o, dfc[keep].reset_index(drop=True))
# (e) users-only subsample (regular AI use for investing: GUI1 >= 3)
us = (df.GUI1 >= 3).values; R["users_n"] = int(us.sum())
try:
    m_u = Model(M_FULL); m_u.fit(dfc[us].reset_index(drop=True)); ui = m_u.inspect(std_est=True); R["users_only"] = {**keyrow(ui), **{f"{l}~{r}": row(ui, l, "~", r) for l, r in [("PCA","INTF"),("CGz","INTF"),("UR","INTA"),("VER","INTA")]}}; R["users_fit"] = fitstats(m_u, dfc[us].reset_index(drop=True))
except Exception as e: R["users_only"] = None
# (f) alternative illusion indicator: over-placement (self-rated rank minus actual rank)
# (not simulated; reserved for real data)  --  behavioural criterion validity with vignettes
m_v = Model(CFA + "VIGERR ~ UR + VER + GUI\nGUI ~~ AIL\nUR ~~ VER\n"); m_v.fit(dfc[ITEMS + ["VIGERR"]]); vi = m_v.inspect(std_est=True)
R["vignette"] = {f"VIGERR~{r}": row(vi, "VIGERR", "~", r) for r in ["UR", "VER", "GUI"]}; R["vignette_fit"] = fitstats(m_v, dfc[ITEMS + ["VIGERR"]])
json.dump(R, open(os.path.join(OUT, "results_paper3.json"), "w"), ensure_ascii=False, indent=1)
bt.describe().T.round(4).to_csv(os.path.join(OUT, "bootstrap_summary.csv"))

# ------------------------------------------------------------ 7) summary
print("N", R["n"], "users%", round(R["demo"]["users_pct"], 1), "KR20", round(R["fk"]["kr20"], 3), "CG mean", round(R["fk"]["cg_mean"], 2), "CG>0 %", round(R["fk"]["cg_pos_pct"], 1))
print("CFA", {k: round(v, 3) for k, v in R["cfa"].items()}); print("SEM", {k: round(v, 3) for k, v in R["sem"].items()})
for f, v in R["rel"].items(): print(f, {k: round(x, 3) for k, x in v.items()})
for k, v in R["paths"].items(): print(k, {a: round(b, 3) for a, b in v.items()})
for k, v in R["indirect"].items():
    if not k.startswith("slope"): print(k, {a: (round(b, 3) if not isinstance(b, bool) else b) for a, b in v.items()})
print("R2", R["r2"], "f2", R["f2_int"]); print("vignette", {k: round(v["beta"], 3) for k, v in R["vignette"].items()})
for k, v in R["models"].items(): print(k, v["name"], round(v["chi2"], 1), v["df"], round(v["cfi"], 3), round(v["rmsea"], 3), round(v["bic"], 1))
print("HTMT max", R["htmt_max"], "VIF", R["vif"])
