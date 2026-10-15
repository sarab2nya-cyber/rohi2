# -*- coding: utf-8 -*-
"""
Institutional pressures -> substantive adoption vs. symbolic compliance -> perceived usefulness of reported information -> financial accountability
(public-sector executive agencies); moderation by financial-information-system maturity.
Fully latent CB-SEM (semopy): every item is an indicator of its own latent variable; no item sums/means are used.
Colab:  !pip -q install "setuptools<58" wheel && pip -q install --no-build-isolation semopy==2.3.11
        !pip -q install pandas numpy scipy statsmodels matplotlib openpyxl
        %run gov_analysis.py        (simlib.py next to this file; for the real survey set DATA_PATH to the CSV)
"""
import os, sys, json, warnings
import numpy as np, pandas as pd
from scipy import stats
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

SEED, N = 52817, 336
DATA_PATH = None
OUT = os.path.join(HERE, "output"); os.makedirs(OUT, exist_ok=True)
B = int(os.environ.get("BOOT", 2000))
z = lambda x: (x-x.mean())/x.std()

# ------------------------------------------------------------ 1) data generation (demonstration data for code testing)
def simulate(seed=SEED, n=N):
    rng = np.random.default_rng(seed)
    org = rng.choice(4, n, p=[.34, .26, .22, .18])                 # 1 ministry/agency, 2 university/health, 3 municipality/local, 4 provincial offices
    role = rng.choice(4, n, p=[.27, .24, .25, .24])                # 1 financial manager, 2 comptroller, 3 budget expert, 4 accountant/auditor
    exp = np.clip(rng.gamma(4.0, 3.4, n), 1, 33).round().astype(int)
    age = np.clip(34 + .85*exp + rng.normal(0, 4.5, n), 25, 63).round().astype(int)
    edu = rng.choice(4, n, p=[.07, .55, .30, .08])                  # diploma / bachelor / master / doctorate
    exp_z = z(exp.astype(float))
    COE = rng.normal(size=n)
    NOR = z(.28*COE + .96*rng.normal(size=n))
    MIM = z(.34*COE + .22*NOR + .90*rng.normal(size=n))
    DIG = z(.14*NOR - .12*(org == 2) + .12*(org == 0) + .97*rng.normal(size=n))
    SUB = z(.22*COE + .36*NOR + .10*MIM + .10*DIG + .88*rng.normal(size=n))
    cd = z(COE*DIG)
    SYM = z(.34*COE - .24*NOR + .28*MIM - .10*DIG - .22*cd + .76*rng.normal(size=n))
    sd_ = z(SUB*DIG)
    USE = z(.36*SUB - .26*SYM + .10*DIG + .20*sd_ + .80*rng.normal(size=n))
    ACC = z(.26*SUB - .20*SYM + .32*USE + .06*exp_z + .80*rng.normal(size=n))
    lat = dict(COE=COE, NOR=NOR, MIM=MIM, SUB=SUB, SYM=SYM, DIG=DIG, USE=USE, ACC=ACC)
    spec = dict(COE=[.80,.77,.73,.68], NOR=[.81,.78,.74,.69], MIM=[.79,.76,.72,.67], SUB=[.80,.77,.74,.71,.67],
                SYM=[.80,.76,.73,.68], DIG=[.82,.79,.75,.70], USE=[.81,.77,.74,.69], ACC=[.80,.78,.75,.72,.67])
    items = gen_items(rng, lat, spec,
        cross=[("SUB4","USE",.13),("SYM2","COE",.12),("USE3","DIG",.13),("ACC4","SUB",.12),("MIM3","DIG",.12),("NOR2","SUB",.12)],
        resid_corr=[("COE1","COE2",.22),("NOR1","NOR2",.20),("MIM1","MIM2",.22),("SUB1","SUB2",.20),("SYM1","SYM2",.22),("DIG1","DIG2",.20),("USE1","USE2",.22),("ACC1","ACC2",.20),("ACC4","ACC5",.18)],
        method_sd=.15, loc=dict(COE=.30, NOR=.15, MIM=.0, SUB=-.15, SYM=-.10, DIG=-.25, USE=.0, ACC=-.10))
    d = pd.DataFrame(dict(org=org+1, role=role+1, exp=exp, age=age, edu=edu+1))
    return pd.concat([d, items], axis=1)

df = pd.read_csv(DATA_PATH) if DATA_PATH else simulate()
if not DATA_PATH:
    df.to_csv(os.path.join(OUT, "gov_data.csv"), index=False, encoding="utf-8-sig")
    df.to_excel(os.path.join(OUT, "gov_data.xlsx"), index=False)
FAC = dict(COE=4, NOR=4, MIM=4, SUB=5, SYM=4, DIG=4, USE=4, ACC=5)
ITEMS = [f"{f}{j}" for f, k in FAC.items() for j in range(1, k+1)]
X = df[ITEMS]; R = {"n": len(df)}

# ------------------------------------------------------------ 2) descriptives
R["demo"] = dict(org={int(k): float(v*100) for k, v in df.org.value_counts(normalize=True).sort_index().items()},
                 role={int(k): float(v*100) for k, v in df.role.value_counts(normalize=True).sort_index().items()},
                 edu={int(k): float(v*100) for k, v in df.edu.value_counts(normalize=True).sort_index().items()},
                 exp_m=float(df.exp.mean()), exp_sd=float(df.exp.std()), age_m=float(df.age.mean()), age_sd=float(df.age.std()))
it = pd.DataFrame({"mean": X.mean(), "sd": X.std(), "skew": X.apply(stats.skew), "kurt": X.apply(stats.kurtosis)}); R["items"] = it.round(3).to_dict("index")
R["skew_range"] = [float(it["skew"].min()), float(it["skew"].max())]; R["kurt_range"] = [float(it["kurt"].min()), float(it["kurt"].max())]
Zc = (X - X.mean()).values; S_ = np.cov(Zc.T, bias=True); d2 = np.einsum("ij,jk,ik->i", Zc, np.linalg.inv(S_), Zc); p_ = X.shape[1]; mk = (d2**2).mean()
R["mardia"] = dict(k=float(mk), expected=float(p_*(p_+2)), z=float((mk-p_*(p_+2))/np.sqrt(8*p_*(p_+2)/len(df))))

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

# ------------------------------------------------------------ 3) CFA, reliability, validity, common-method checks
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
R["vif"] = {"SUB": vif_latent(["COE", "NOR", "MIM", "DIG"]), "SYM": vif_latent(["COE", "NOR", "MIM", "DIG"]), "USE": vif_latent(["SUB", "SYM", "DIG"]), "ACC": vif_latent(["SUB", "SYM", "USE"])}

# ------------------------------------------------------------ 4) structural model with two latent interactions
dfc = X - X.mean()
for i in range(1, 5):
    dfc[f"IS{i}"] = dfc[f"SUB{i}"]*dfc[f"DIG{i}"]            # SUB x DIG (matched pairs)
    dfc[f"IC{i}"] = dfc[f"COE{i}"]*dfc[f"DIG{i}"]            # COE x DIG (matched pairs)
dfc["exp"] = z(df.exp.astype(float)).values
MEAS = CFA + "INTS =~ IS1+IS2+IS3+IS4\nINTC =~ IC1+IC2+IC3+IC4\n"
EXO = ["COE", "NOR", "MIM", "DIG", "INTS", "INTC"]
COV = "".join(f"{a} ~~ {b}\n" for i, a in enumerate(EXO) for b in EXO[i+1:])
BODY = "SUB ~ COE + NOR + MIM + DIG\nSYM ~ COE + NOR + MIM + DIG + INTC\nUSE ~ SUB + SYM + DIG + INTS\nACC ~ SUB + SYM + USE + exp\n"
M_FULL = MEAS + BODY + COV
sem = Model(M_FULL); sem.fit(dfc); R["sem"] = fitstats(sem, dfc); si = sem.inspect(std_est=True)
PAIRS = [("SUB","COE"),("SUB","NOR"),("SUB","MIM"),("SUB","DIG"),("SYM","COE"),("SYM","NOR"),("SYM","MIM"),("SYM","DIG"),("SYM","INTC"),
         ("USE","SUB"),("USE","SYM"),("USE","DIG"),("USE","INTS"),("ACC","SUB"),("ACC","SYM"),("ACC","USE"),("ACC","exp")]
R["paths"] = {f"{l}~{r}": row(si, l, "~", r) for l, r in PAIRS}
def latent_r2(ii, dvs):
    out = {}
    for dv in dvs:
        q = ii[(ii.lval == dv) & (ii.op == "~~") & (ii.rval == dv)].iloc[0]; out[dv] = float(1 - float(q["Est. Std"]))
    return out
R["r2"] = latent_r2(si, ["SUB", "SYM", "USE", "ACC"])
iu = sem.inspect(); psi = lambda dv: float(iu[(iu.lval == dv) & (iu.op == "~~") & (iu.rval == dv)]["Estimate"].iloc[0])
R["sd_latent"] = {"DIG": psi("DIG")**.5}
R["n_obs_vars"] = len(sem.vars["observed"]); R["n_params_sem"] = int(R["n_obs_vars"]*(R["n_obs_vars"]+1)/2 - R["sem"]["df"]); R["n_params_cfa"] = int(len(ITEMS)*(len(ITEMS)+1)/2 - R["cfa"]["df"])
NOI = MEAS + "SUB ~ COE + NOR + MIM + DIG\nSYM ~ COE + NOR + MIM + DIG\nUSE ~ SUB + SYM + DIG\nACC ~ SUB + SYM + USE + exp\n" + COV
m_ni = Model(NOI); m_ni.fit(dfc); R["fit_noint"] = fitstats(m_ni, dfc); r2n = latent_r2(m_ni.inspect(std_est=True), ["SUB", "SYM", "USE", "ACC"]); R["r2_noint"] = r2n
R["f2_int"] = {k: float((R["r2"][k]-r2n[k])/(1-R["r2"][k])) for k in ["SYM", "USE"]}

# ------------------------------------------------------------ 5) bootstrap: indirect and conditional indirect effects
sD = R["sd_latent"]["DIG"]
def eff(ii, sd):
    g = lambda l, r: float(ii[(ii.lval==l)&(ii.rval==r)&(ii.op=="~")]["Estimate"].iloc[0])
    o = {}
    bSA, bYA, bUA = g("ACC","SUB"), g("ACC","SYM"), g("ACC","USE"); bSU, bYU, wSU = g("USE","SUB"), g("USE","SYM"), g("USE","INTS"); wCY = g("SYM","INTC")
    for tag, k in [("low", -1), ("mean", 0), ("high", 1)]:
        bsu = bSU + wSU*sd*k
        for X_ in ["COE", "NOR", "MIM"]:
            aS = g("SUB", X_); aY = g("SYM", X_) + (wCY*sd*k if X_ == "COE" else 0)
            o[f"{X_}_SUB_{tag}"] = aS*(bSA + bsu*bUA); o[f"{X_}_SYM_{tag}"] = aY*(bYA + bYU*bUA)
            o[f"{X_}_tot_{tag}"] = o[f"{X_}_SUB_{tag}"] + o[f"{X_}_SYM_{tag}"]
        o[f"SUB_USE_ACC_{tag}"] = bsu*bUA; o[f"SUB_all_{tag}"] = bSA + bsu*bUA
    o["imm_COE_SYM"] = wCY*sd*(bYA + bYU*bUA)
    for X_ in ["COE", "NOR", "MIM"]: o[f"imm_{X_}_SUB"] = g("SUB", X_)*wSU*sd*bUA
    o["imm_SUB_ACC"] = wSU*sd*bUA
    return o
def eff_std(ii):
    g = lambda l, r: float(ii[(ii.lval==l)&(ii.rval==r)&(ii.op=="~")]["Est. Std"].iloc[0])
    return {f"std_{X_}_tot": g("SUB", X_)*(g("ACC","SUB") + g("USE","SUB")*g("ACC","USE")) + g("SYM", X_)*(g("ACC","SYM") + g("USE","SYM")*g("ACC","USE")) for X_ in ["COE","NOR","MIM"]}
point = {**eff(iu, sD), **eff_std(si)}
rng = np.random.default_rng(SEED); bt = []
for bi in range(B):
    ix = rng.integers(0, len(dfc), len(dfc)); bd = dfc.iloc[ix].reset_index(drop=True)
    try:
        mb = Model(M_FULL); mb.fit(bd); ib = mb.inspect(); sb = float(ib[(ib.lval=="DIG")&(ib.op=="~~")&(ib.rval=="DIG")]["Estimate"].iloc[0])**.5
        bt.append({**eff(ib, sb), **eff_std(mb.inspect(std_est=True))})
    except Exception: pass
bt = pd.DataFrame(bt); R["boot_n"] = int(len(bt))
R["indirect"] = {k: dict(est=float(point[k]), lo=float(bt[k].quantile(.025)), hi=float(bt[k].quantile(.975)), sig=bool(bt[k].quantile(.025)*bt[k].quantile(.975) > 0)) for k in point}

# ------------------------------------------------------------ 6) competing models and robustness
def mk(body): return Model(MEAS + body + COV)
cand = {
 "M1": ("مدل پیشنهادی (دو میانجی، سودمندی و دو تعدیل‌گری)", BODY),
 "M2": ("بدون تعدیل‌گری", "SUB ~ COE + NOR + MIM + DIG\nSYM ~ COE + NOR + MIM + DIG\nUSE ~ SUB + SYM + DIG\nACC ~ SUB + SYM + USE + exp\n"),
 "M3": ("بدون مسیر سودمندی", "SUB ~ COE + NOR + MIM + DIG\nSYM ~ COE + NOR + MIM + DIG + INTC\nUSE ~ SUB + SYM + DIG + INTS\nACC ~ SUB + SYM + exp\n"),
 "M4": ("فقط اجرای ماهوی (بدون انطباق نمادین)", "SUB ~ COE + NOR + MIM + DIG\nUSE ~ SUB + DIG + INTS\nACC ~ SUB + USE + exp\n"),
 "M5": ("اثر مستقیم فشارها بر پاسخگویی", "SUB ~ COE + NOR + MIM + DIG\nSYM ~ COE + NOR + MIM + DIG + INTC\nUSE ~ SUB + SYM + DIG + INTS\nACC ~ SUB + SYM + USE + COE + NOR + MIM + exp\n")}
R["models"] = {}
for k, (nm, body) in cand.items():
    mm = mk(body); mm.fit(dfc); R["models"][k] = dict(name=nm, **fitstats(mm, dfc))
keyp = [("SUB","COE"),("SUB","NOR"),("SYM","COE"),("SYM","NOR"),("SYM","MIM"),("USE","SUB"),("USE","SYM"),("ACC","SUB"),("ACC","SYM"),("ACC","USE")]
EXTRA = [("SYM","INTC"),("USE","INTS")]
def keyrow(ii): return {f"{l}~{r}": row(ii, l, "~", r) for l, r in keyp + EXTRA}
try:
    md = Model(CFA + NOI.split(CFA)[1].split("INTC =~ IC1+IC2+IC3+IC4\n")[1].split("EXO")[0]) if False else None
    NOI2 = CFA + "SUB ~ COE + NOR + MIM + DIG\nSYM ~ COE + NOR + MIM + DIG\nUSE ~ SUB + SYM + DIG\nACC ~ SUB + SYM + USE + exp\n" + "".join(f"{a} ~~ {b}\n" for i, a in enumerate(EXO[:4]) for b in EXO[:4][i+1:])
    md = Model(NOI2); cols_ = ITEMS + ["exp"]; md.fit(dfc[cols_], obj="DWLS"); R["dwls"] = {f"{l}~{r}": row(md.inspect(std_est=True), l, "~", r) for l, r in keyp}; R["dwls_fit"] = fitstats(md, dfc[cols_])
except Exception as e: R["dwls"] = None
dfr = dfc.copy(); import statsmodels.api as sm
Xf = sm.add_constant(dfc[[f"SUB{i}" for i in range(1, 5)] + [f"DIG{i}" for i in range(1, 5)] + [f"COE{i}" for i in range(1, 5)]].values)
for pre in ("IS", "IC"):
    for i in range(1, 5):
        pr = dfc[f"{pre}{i}"].values; dfr[f"{pre}{i}"] = pr - Xf @ np.linalg.lstsq(Xf, pr, rcond=None)[0]
m_rc = Model(M_FULL); m_rc.fit(dfr); rci = m_rc.inspect(std_est=True); R["resid_centered"] = keyrow(rci); R["resid_centered_fit"] = fitstats(m_rc, dfr)
sg = cfa.calc_sigma()[0]; nm_ = cfa.vars["observed"]; Sx = X[nm_].cov().values; sdv = np.sqrt(np.diag(Sx)); res_ = (Sx - sg)/np.outer(sdv, sdv); pairs = []
for i_ in range(len(nm_)):
    for j_ in range(i_):
        if nm_[i_].rstrip("0123456789") == nm_[j_].rstrip("0123456789"): pairs.append((abs(res_[i_, j_]), nm_[j_], nm_[i_]))
pairs = sorted(pairs, reverse=True)[:4]; add_ = "".join(f"{a} ~~ {b}\n" for _, a, b in pairs)
m_rs = Model(M_FULL + add_); m_rs.fit(dfc); rsi = m_rs.inspect(std_est=True); R["respec"] = dict(pairs=[(a, b) for _, a, b in pairs], fit=fitstats(m_rs, dfc), paths=keyrow(rsi))
keep = d2 < np.quantile(d2, .95); R["outliers_removed"] = int((~keep).sum())
m_o = Model(M_FULL); m_o.fit(dfc[keep].reset_index(drop=True)); oi = m_o.inspect(std_est=True); R["trimmed"] = keyrow(oi); R["trimmed_fit"] = fitstats(m_o, dfc[keep].reset_index(drop=True))
# subsample: units with >= 10 years of professional experience in the public sector (experienced respondents)
us = (df.exp >= 10).values; R["senior_n"] = int(us.sum())
try:
    m_u = Model(M_FULL); m_u.fit(dfc[us].reset_index(drop=True)); ui = m_u.inspect(std_est=True); R["senior"] = keyrow(ui); R["senior_fit"] = fitstats(m_u, dfc[us].reset_index(drop=True))
except Exception as e: R["senior"] = None
json.dump(R, open(os.path.join(OUT, "results_gov.json"), "w"), ensure_ascii=False, indent=1)
bt.describe().T.round(4).to_csv(os.path.join(OUT, "bootstrap_summary.csv"))

# ------------------------------------------------------------ 7) summary
print("N", R["n"]); print("CFA", {k: round(v, 3) for k, v in R["cfa"].items()}); print("SEM", {k: round(v, 3) for k, v in R["sem"].items()})
for f, v in R["rel"].items(): print(f, {k: round(x, 3) for k, x in v.items()})
for k, v in R["paths"].items(): print(k, {a: round(b, 3) for a, b in v.items()})
for k, v in R["indirect"].items(): print(k, {a: (round(b, 3) if not isinstance(b, bool) else b) for a, b in v.items()})
print("R2", R["r2"], "f2", R["f2_int"])
for k, v in R["models"].items(): print(k, v["name"], round(v["chi2"], 1), v["df"], round(v["cfi"], 3), round(v["rmsea"], 3), round(v["bic"], 1))
print("HTMT max", R["htmt_max"], "VIF", R["vif"])
