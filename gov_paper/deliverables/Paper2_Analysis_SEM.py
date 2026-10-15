# -*- coding: utf-8 -*-
"""
Paper 2: configuration of institutional pressures (coercive, normative, mimetic) and the two organisational responses
(substantive implementation, symbolic compliance): synergy/substitution among pressures, agency-type comparison, latent profiles.
Fully latent CB-SEM (semopy); no item sums/means; latent interactions via matched-pair product indicators.
Colab:  !pip -q install "setuptools<58" wheel && pip -q install --no-build-isolation semopy==2.3.11
        !pip -q install pandas numpy scipy statsmodels scikit-learn matplotlib openpyxl ; %run gov2_analysis.py
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
# ---- mgcfa.py (inlined) ----
"""CFA چندگروهی با ساختار میانگین (ML) برای آزمون ناوردایی اندازه‌گیری (پیکربندی، متریک، اسکالر، اسکالر جزئی).
گرادیان تحلیلی؛ شناسایی با گویهٔ نشانگر (بار ۱). مستقل از semopy."""
import numpy as np
from scipy.optimize import minimize

class MGCFA:
    def __init__(self, groups, pattern):
        """groups: فهرست DataFrame؛ pattern: dict عامل -> فهرست نام گویه‌ها"""
        self.G = len(groups); self.items = [i for v in pattern.values() for i in v]; self.p = len(self.items)
        self.k = len(pattern); self.fac = list(pattern)
        self.data = [g[self.items].values.astype(float) for g in groups]
        self.n = [len(d) for d in self.data]
        self.xbar = [d.mean(0) for d in self.data]; self.S = [np.cov(d.T, bias=True) for d in self.data]
        self.mask = np.zeros((self.p, self.k), bool); self.marker = []
        for j, (f, its) in enumerate(pattern.items()):
            for t, it in enumerate(its):
                self.mask[self.items.index(it), j] = True
                if t == 0: self.marker.append((self.items.index(it), j))
        self.free_load = [(i, j) for i in range(self.p) for j in range(self.k) if self.mask[i, j] and (i, j) not in self.marker]
        self.tril = np.tril_indices(self.k)

    # --- نقشهٔ پارامترها
    def _layout(self, inv_load, inv_int, free_int=(), free_means=False):
        idx = 0; L = {}; 
        def alloc(n): 
            nonlocal idx; r = np.arange(idx, idx+n); idx += n; return r
        nl = len(self.free_load); npsi = len(self.tril[0])
        shared_l = alloc(nl) if inv_load else None
        shared_nu = alloc(self.p) if inv_int else None
        self.map = []
        extra_nu = {}
        for g in range(self.G):
            m = {}
            m["lam"] = shared_l if inv_load else alloc(nl)
            m["psi"] = alloc(npsi); m["theta"] = alloc(self.p)
            if inv_int:
                nu = shared_nu.copy()
                for it in free_int: nu[it] = alloc(1)[0] if g > 0 else shared_nu[it]
                if g > 0:
                    pass
                m["nu"] = nu
                m["kappa"] = alloc(self.k) if (g > 0) else None
            else:
                m["nu"] = alloc(self.p); m["kappa"] = None
            self.map.append(m)
        self.npar = idx
        # گروه ۱ پیش از تخصیص free_int: اصلاح ترتیب برای free_int (intercept آزاد در گروه‌های دیگر)
    def start(self):
        th = np.zeros(self.npar)
        for g in range(self.G):
            m = self.map[g]
            lam0 = 0.8*np.ones(len(self.free_load)); th[m["lam"]] = lam0
            th[m["psi"]] = [1.0 if a == b else 0.2 for a, b in zip(*self.tril)]
            th[m["theta"]] = 0.5*np.diag(self.S[g])
            th[m["nu"]] = self.xbar[g]
            if m["kappa"] is not None: th[m["kappa"]] = 0.0
        return th

    def _unpack(self, th, g):
        m = self.map[g]
        Lam = np.zeros((self.p, self.k))
        for (i, j) in self.marker: Lam[i, j] = 1.0
        for t, (i, j) in enumerate(self.free_load): Lam[i, j] = th[m["lam"][t]]
        Psi = np.zeros((self.k, self.k)); Psi[self.tril] = th[m["psi"]]; Psi = Psi + Psi.T - np.diag(np.diag(Psi))
        Theta = th[m["theta"]]; nu = th[m["nu"]]
        kap = th[m["kappa"]] if m["kappa"] is not None else np.zeros(self.k)
        return Lam, Psi, Theta, nu, kap

    def fun(self, th):
        F = 0.0; grad = np.zeros_like(th)
        for g in range(self.G):
            Lam, Psi, Theta, nu, kap = self._unpack(th, g); m = self.map[g]
            Sig = Lam @ Psi @ Lam.T + np.diag(Theta); mu = nu + Lam @ kap
            try: L = np.linalg.cholesky(Sig)
            except np.linalg.LinAlgError: return 1e10, grad
            Si = np.linalg.inv(Sig); logd = 2*np.log(np.diag(L)).sum()
            d = self.xbar[g] - mu; S = self.S[g]
            Fg = logd + np.trace(S @ Si) + d @ Si @ d - np.linalg.slogdet(S)[1] - self.p
            w = self.n[g]/sum(self.n)
            F += w*Fg
            Gm = Si - Si @ (S + np.outer(d, d)) @ Si          # dF/dSigma
            gmu = -2*Si @ d                                    # dF/dmu
            dLam = 2*Gm @ Lam @ Psi + np.outer(gmu, kap)
            dPsi = Lam.T @ Gm @ Lam; dPsi = dPsi + dPsi.T - np.diag(np.diag(dPsi))
            grad[m["lam"]] += w*np.array([dLam[i, j] for (i, j) in self.free_load])
            grad[m["psi"]] += w*dPsi[self.tril]
            grad[m["theta"]] += w*np.diag(Gm)
            np.add.at(grad, m["nu"], w*gmu)
            if m["kappa"] is not None: grad[m["kappa"]] += w*(Lam.T @ gmu)
        return F, grad

    def fit(self, inv_load=False, inv_int=False, free_int=()):
        self._layout_custom(inv_load, inv_int, free_int)
        th0 = self.start()
        r = minimize(self.fun, th0, jac=True, method="L-BFGS-B", options=dict(maxiter=5000, maxfun=20000, ftol=1e-13, gtol=1e-7))
        N = sum(self.n); chi2 = N*r.fun
        mom = self.G*(self.p*(self.p+1)/2 + self.p)
        # پارامترهای شمارش‌شده (در حالت اسکالر: میانگین گروه ۱ ثابت)
        df = mom - self.npar
        base = sum(self.n[g]*(np.log(np.diag(self.S[g])).sum() - np.linalg.slogdet(self.S[g])[1]) for g in range(self.G))
        dfb = self.G*self.p*(self.p-1)/2
        cfi = 1 - max(chi2-df, 0)/max(chi2-df, base-dfb, 1e-9)
        rmsea = np.sqrt(self.G)*np.sqrt(max((chi2-df)/(N*df), 0))
        # SRMR
        srs = []
        for g in range(self.G):
            Lam, Psi, Theta, nu, kap = self._unpack(r.x, g); Sig = Lam@Psi@Lam.T + np.diag(Theta)
            sd = np.sqrt(np.diag(self.S[g])); res = (self.S[g]-Sig)/np.outer(sd, sd)
            srs.append(np.sqrt((res[np.tril_indices(self.p)]**2).mean()))
        return dict(chi2=chi2, df=df, cfi=cfi, rmsea=rmsea, srmr=float(np.mean(srs)), npar=self.npar, x=r.x, ok=r.success, cfg=(inv_load, inv_int, tuple(free_int)))

    def _layout_custom(self, inv_load, inv_int, free_int):
        free_int = set(free_int)
        idx = 0
        def alloc(n):
            nonlocal idx; r = np.arange(idx, idx+n); idx += n; return r
        nl = len(self.free_load); npsi = len(self.tril[0])
        sl = alloc(nl) if inv_load else None
        snu = alloc(self.p) if inv_int else None
        self.map = []
        for g in range(self.G):
            m = {"lam": sl if inv_load else alloc(nl)}
            m["psi"] = alloc(npsi); m["theta"] = alloc(self.p)
            if inv_int:
                nu = snu.copy()
                if g > 0:
                    for it in free_int: nu[it] = alloc(1)[0]
                m["nu"] = nu; m["kappa"] = alloc(self.k) if g > 0 else None
            else:
                m["nu"] = alloc(self.p); m["kappa"] = None
            self.map.append(m)
        self.npar = idx

    def latent_means(self, res):
        out = []
        for g in range(self.G):
            _, _, _, _, kap = self._unpack(res["x"], g); out.append(kap)
        return dict(zip(self.fac, out[-1]))

    def intercept_gaps(self, res_metric, ):
        """فاصلهٔ استاندارد‌شدهٔ برش‌ها بین گروه‌ها (برای انتخاب گویهٔ نابرابر)."""
        gaps = []
        for i in range(self.p):
            pooled = np.sqrt(np.mean([self.S[g][i, i] for g in range(self.G)]))
            gaps.append(abs(self.xbar[0][i]-self.xbar[1][i])/pooled)
        return np.array(gaps)


    def latent_mean_tests(self, res, h=1e-5):
        """آزمون میانگین‌های پنهان گروه دوم نسبت به گروه اول (مدل اسکالر): κ، خطای معیار والد از هسین عددی، z، p و d استاندارد"""
        from scipy import stats
        self._layout_custom(*res["cfg"]); x = res["x"]; n = len(x); N = sum(self.n)
        Hm = np.zeros((n, n))
        for j in range(n):
            xp = x.copy(); xm = x.copy(); xp[j] += h; xm[j] -= h
            Hm[:, j] = (self.fun(xp)[1] - self.fun(xm)[1])/(2*h)
        Hm = (Hm + Hm.T)/2
        cov = (2.0/N)*np.linalg.pinv(Hm)
        out = {}
        g = self.G - 1
        for k, f in enumerate(self.fac):
            idx = self.map[g]["kappa"][k]; kap = x[idx]; se = float(np.sqrt(max(cov[idx, idx], 1e-12)))
            ph = [self._unpack(x, gg)[1][k, k] for gg in range(self.G)]
            d = kap/np.sqrt(np.mean(ph)); z = kap/se
            out[f] = dict(kappa=float(kap), se=se, z=float(z), p=float(2*(1 - stats.norm.cdf(abs(z)))), d=float(d))
        return out

# ---- end mgcfa.py ----
SEED, N = 73190, 412
DATA_PATH = None
OUT = os.path.join(HERE, "output"); os.makedirs(OUT, exist_ok=True)
B = int(os.environ.get("BOOT", 1000))
z = lambda x: (x-x.mean())/x.std()

def simulate(seed=SEED, n=N):
    rng = np.random.default_rng(seed)
    org = rng.choice(4, n, p=[.30, .27, .25, .18])            # 0 ministry/national, 1 university/health, 2 municipality/local, 3 provincial offices
    grp = np.isin(org, [1, 2]).astype(int)                    # 0 administrative/governmental, 1 service/local bodies
    exp = np.clip(rng.gamma(4.2, 3.2, n), 1, 33).round().astype(int)
    age = np.clip(35 + .8*exp + rng.normal(0, 4.5, n), 25, 63).round().astype(int)
    role = rng.choice(4, n, p=[.26, .25, .25, .24]); edu = rng.choice(4, n, p=[.06, .52, .33, .09])
    pcl = np.where(grp[:, None] == 1, np.array([.44, .26, .30])[None, :], np.array([.28, .42, .30])[None, :])
    cls = (rng.random(n)[:, None] > np.cumsum(pcl, 1)).sum(1)                     # latent configurations of pressures
    mu = np.array([[0.0, 1.20, -0.45], [1.20, -0.70, 1.00], [-1.00, -0.30, -0.60]])  # (COE, NOR, MIM) means per configuration
    P3 = mu[cls] + .62*rng.normal(size=(n, 3))
    COE, NOR, MIM = z(P3[:, 0]), z(P3[:, 1]), z(P3[:, 2])
    common = rng.normal(size=n)
    bN = np.where(grp == 1, .44, .22); bM = np.where(grp == 1, .40, .12)
    cn = z(COE*NOR); cm = z(COE*MIM)
    SUB = z(.26*COE + bN*NOR + .04*MIM + .30*cn + .30*common + .70*rng.normal(size=n))
    SYM = z(.30*COE - .22*NOR + bM*MIM + .27*cm + .30*common + .70*rng.normal(size=n))
    lat = dict(COE=COE, NOR=NOR, MIM=MIM, SUB=SUB, SYM=SYM)
    spec = dict(COE=[.80,.77,.73,.68], NOR=[.81,.78,.74,.69], MIM=[.79,.76,.72,.67], SUB=[.80,.77,.74,.71,.67], SYM=[.80,.76,.73,.68])
    items = gen_items(rng, lat, spec, cross=[("SUB4","COE",.12),("SYM2","MIM",.12),("NOR2","SUB",.12),("MIM3","SYM",.12)],
        resid_corr=[("COE1","COE2",.22),("NOR1","NOR2",.20),("MIM1","MIM2",.22),("SUB1","SUB2",.20),("SYM1","SYM2",.22),("SUB4","SUB5",.18)],
        method_sd=.15, loc=dict(COE=.30, NOR=.15, MIM=.0, SUB=-.15, SYM=-.10))
    d = pd.DataFrame(dict(org=org+1, grp=grp, role=role+1, exp=exp, age=age, edu=edu+1))
    return pd.concat([d, items], axis=1)

df = pd.read_csv(DATA_PATH) if DATA_PATH else simulate()
if not DATA_PATH:
    df.to_csv(os.path.join(OUT, "gov2_data.csv"), index=False, encoding="utf-8-sig"); df.to_excel(os.path.join(OUT, "gov2_data.xlsx"), index=False)
FAC = dict(COE=4, NOR=4, MIM=4, SUB=5, SYM=4)
ITEMS = [f"{f}{j}" for f, k in FAC.items() for j in range(1, k+1)]
X = df[ITEMS]; R = {"n": len(df)}
R["demo"] = dict(org={int(k): float(v*100) for k, v in df.org.value_counts(normalize=True).sort_index().items()}, grp={int(k): int(v) for k, v in df.grp.value_counts().sort_index().items()},
                 exp_m=float(df.exp.mean()), exp_sd=float(df.exp.std()), age_m=float(df.age.mean()), age_sd=float(df.age.std()),
                 role={int(k): float(v*100) for k, v in df.role.value_counts(normalize=True).sort_index().items()})
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
    dfc[f"IN{i}"] = dfc[f"COE{i}"]*dfc[f"NOR{i}"]; dfc[f"IM{i}"] = dfc[f"COE{i}"]*dfc[f"MIM{i}"]
MEAS = CFA + "INCN =~ IN1+IN2+IN3+IN4\nINCM =~ IM1+IM2+IM3+IM4\n"
EXO = ["COE", "NOR", "MIM", "INCN", "INCM"]
COV = "".join(f"{a} ~~ {b}\n" for i, a in enumerate(EXO) for b in EXO[i+1:]) + "SUB ~~ SYM\n"
BODY = "SUB ~ COE + NOR + MIM + INCN\nSYM ~ COE + NOR + MIM + INCM\n"
M_FULL = MEAS + BODY + COV
sem = Model(M_FULL); sem.fit(dfc); R["sem"] = fitstats(sem, dfc); si = sem.inspect(std_est=True)
PAIRS = [("SUB","COE"),("SUB","NOR"),("SUB","MIM"),("SUB","INCN"),("SYM","COE"),("SYM","NOR"),("SYM","MIM"),("SYM","INCM")]
R["paths"] = {f"{l}~{r}": row(si, l, "~", r) for l, r in PAIRS}
R["resid_cov"] = row(si, "SUB", "~~", "SYM")
def latent_r2(ii, dvs):
    out = {}
    for dv in dvs:
        q = ii[(ii.lval == dv) & (ii.op == "~~") & (ii.rval == dv)].iloc[0]; out[dv] = float(1 - float(q["Est. Std"]))
    return out
R["r2"] = latent_r2(si, ["SUB", "SYM"])
iu = sem.inspect(); psi = lambda dv: float(iu[(iu.lval == dv) & (iu.op == "~~") & (iu.rval == dv)]["Estimate"].iloc[0])
R["sd_latent"] = {"COE": psi("COE")**.5, "NOR": psi("NOR")**.5, "MIM": psi("MIM")**.5}
R["n_obs_vars"] = len(sem.vars["observed"]); R["n_params_sem"] = int(R["n_obs_vars"]*(R["n_obs_vars"]+1)/2 - R["sem"]["df"])
NOI = MEAS + "SUB ~ COE + NOR + MIM\nSYM ~ COE + NOR + MIM\n" + COV
m_ni = Model(NOI); m_ni.fit(dfc); R["fit_noint"] = fitstats(m_ni, dfc); r2n = latent_r2(m_ni.inspect(std_est=True), ["SUB", "SYM"]); R["r2_noint"] = r2n
R["f2_int"] = {"SUB": float((R["r2"]["SUB"]-r2n["SUB"])/(1-R["r2"]["SUB"])), "SYM": float((R["r2"]["SYM"]-r2n["SYM"])/(1-R["r2"]["SYM"]))}
# conditional (simple-slope) effects with bootstrap
sC, sN, sM = R["sd_latent"]["COE"], R["sd_latent"]["NOR"], R["sd_latent"]["MIM"]
def eff(ii, sc, sn, sm):
    g = lambda l, r: float(ii[(ii.lval==l)&(ii.rval==r)&(ii.op=="~")]["Estimate"].iloc[0]); o = {}
    for tag, k in [("low", -1), ("mean", 0), ("high", 1)]:
        o[f"COE_SUB_atNOR_{tag}"] = g("SUB","COE") + g("SUB","INCN")*sn*k; o[f"NOR_SUB_atCOE_{tag}"] = g("SUB","NOR") + g("SUB","INCN")*sc*k
        o[f"COE_SYM_atMIM_{tag}"] = g("SYM","COE") + g("SYM","INCM")*sm*k; o[f"MIM_SYM_atCOE_{tag}"] = g("SYM","MIM") + g("SYM","INCM")*sc*k
    return o
point = eff(iu, sC, sN, sM); rng = np.random.default_rng(SEED); bt = []
for bi in range(B):
    ix = rng.integers(0, len(dfc), len(dfc)); bd = dfc.iloc[ix].reset_index(drop=True)
    try:
        mb = Model(M_FULL); mb.fit(bd); ib = mb.inspect(); sd_ = lambda v: float(ib[(ib.lval==v)&(ib.op=="~~")&(ib.rval==v)]["Estimate"].iloc[0])**.5
        bt.append(eff(ib, sd_("COE"), sd_("NOR"), sd_("MIM")))
    except Exception: pass
bt = pd.DataFrame(bt); R["boot_n"] = int(len(bt))
R["cond"] = {k: dict(est=float(point[k]), lo=float(bt[k].quantile(.025)), hi=float(bt[k].quantile(.975)), sig=bool(bt[k].quantile(.025)*bt[k].quantile(.975) > 0)) for k in point}
# ---------------- competing models and robustness
def mk(body): return Model(MEAS + body + COV)
cand = {"M1": ("two interactions + residual covariance", BODY), "M2": ("no interactions", "SUB ~ COE + NOR + MIM\nSYM ~ COE + NOR + MIM\n"),
        "M3": ("COE×NOR only", "SUB ~ COE + NOR + MIM + INCN\nSYM ~ COE + NOR + MIM\n"), "M4": ("COE×MIM only", "SUB ~ COE + NOR + MIM\nSYM ~ COE + NOR + MIM + INCM\n")}
R["models"] = {}
for k, (nm, body) in cand.items():
    mm = mk(body); mm.fit(dfc); R["models"][k] = dict(name=nm, **fitstats(mm, dfc))
m5 = Model(MEAS + BODY + COV.replace("SUB ~~ SYM\n", "")); m5.fit(dfc); R["models"]["M5"] = dict(name="two interactions, no residual covariance", **fitstats(m5, dfc))
keyp = [("SUB","COE"),("SUB","NOR"),("SUB","MIM"),("SYM","COE"),("SYM","NOR"),("SYM","MIM")]; EX = [("SUB","INCN"),("SYM","INCM")]
def keyrow(ii): return {f"{l}~{r}": row(ii, l, "~", r) for l, r in keyp + EX}
NOI2 = CFA + "SUB ~ COE + NOR + MIM\nSYM ~ COE + NOR + MIM\n" + "".join(f"{a} ~~ {b}\n" for i, a in enumerate(EXO[:3]) for b in EXO[:3][i+1:]) + "SUB ~~ SYM\n"
md = Model(NOI2); md.fit(dfc[ITEMS], obj="DWLS"); R["dwls"] = {f"{l}~{r}": row(md.inspect(std_est=True), l, "~", r) for l, r in keyp}; R["dwls_fit"] = fitstats(md, dfc[ITEMS])
import statsmodels.api as sm
dfr = dfc.copy(); Xf = sm.add_constant(dfc[[f"COE{i}" for i in range(1, 5)] + [f"NOR{i}" for i in range(1, 5)] + [f"MIM{i}" for i in range(1, 5)]].values)
for pre in ("IN", "IM"):
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
# ---------------- multi-group: invariance + path comparison by agency type
grp = [df[df.grp == g].reset_index(drop=True) for g in (0, 1)]
pattern = {f: [f"{f}{j}" for j in range(1, k+1)] for f, k in FAC.items()}
mg = MGCFA(grp, pattern)
conf = mg.fit(); metr = mg.fit(inv_load=True); scal = mg.fit(inv_load=True, inv_int=True)
inv = {"configural": conf, "metric": metr, "scalar": scal}; gaps = mg.intercept_gaps(metr); order = [mg.items[i] for i in np.argsort(-gaps)]
free = []; part = scal; steps = []
for it_name in order[:6]:
    if metr["cfi"] - part["cfi"] <= .010: break
    free.append(mg.items.index(it_name)); part = mg.fit(inv_load=True, inv_int=True, free_int=tuple(free)); steps.append(it_name)
inv["partial"] = part
R["invariance"] = {k: {a: float(b) for a, b in v.items() if a in ("chi2", "df", "cfi", "rmsea", "srmr", "npar")} for k, v in inv.items()}; R["invariance_freed"] = steps
R["latent_mean_diff"] = mg.latent_mean_tests(inv["partial"])
GS = CFA + "SUB ~ COE + NOR + MIM\nSYM ~ COE + NOR + MIM\nSUB ~~ SYM\nCOE ~~ NOR\nCOE ~~ MIM\nNOR ~~ MIM\n"
gres = []
for g in (0, 1):
    mg_ = Model(GS); mg_.fit(df[df.grp == g][ITEMS].reset_index(drop=True)); gi = mg_.inspect(std_est=True)
    gres.append({f"{l}~{r}": row(gi, l, "~", r) for l, r in keyp})
R["group_paths"] = {"g0": gres[0], "g1": gres[1]}
R["group_diff"] = {k: dict(dz=float((gres[1][k]["b"]-gres[0][k]["b"])/np.sqrt(gres[0][k]["se"]**2 + gres[1][k]["se"]**2))) for k in gres[0]}
for k in R["group_diff"]: R["group_diff"][k]["p"] = float(2*(1-stats.norm.cdf(abs(R["group_diff"][k]["dz"]))))
# ---------------- latent profiles on regression-method factor scores of the three pressures
def factor_scores(m, data):
    ii = m.inspect(); items_ = m.vars["observed"]; facs_ = list(FAC)
    Lam = np.zeros((len(items_), len(facs_))); Th = np.zeros(len(items_)); Ph = np.eye(len(facs_))
    for _, r in ii.iterrows():
        if r.op == "~" and r.rval in facs_ and r.lval in items_: Lam[items_.index(r.lval), facs_.index(r.rval)] = float(r.Estimate)
        if r.op == "~~" and r.lval in items_ and r.lval == r.rval: Th[items_.index(r.lval)] = float(r.Estimate)
        if r.op == "~~" and r.lval in facs_ and r.rval in facs_: Ph[facs_.index(r.lval), facs_.index(r.rval)] = Ph[facs_.index(r.rval), facs_.index(r.lval)] = float(r.Estimate)
    Sg = Lam @ Ph @ Lam.T + np.diag(Th); W = Ph @ Lam.T @ np.linalg.inv(Sg); Z = (data[items_] - data[items_].mean()).values; F = Z @ W.T
    return pd.DataFrame((F - F.mean(0))/F.std(0), columns=facs_)
fs_ = factor_scores(cfa, X)
from sklearn.mixture import GaussianMixture
bic = {}; gms = {}
for k in range(1, 6):
    gm = GaussianMixture(k, covariance_type="full", n_init=10, random_state=SEED).fit(fs_[["COE", "NOR", "MIM"]]); bic[k] = float(gm.bic(fs_[["COE", "NOR", "MIM"]])); gms[k] = gm
kbest = min(bic, key=bic.get); R["profile_bic"] = bic; R["profile_k"] = int(kbest); gm = gms[kbest]
post = gm.predict_proba(fs_[["COE", "NOR", "MIM"]]); lab = post.argmax(1)
ent = 1 - (-(post*np.log(np.clip(post, 1e-12, 1))).sum()/(len(post)*np.log(kbest))) if kbest > 1 else 1.0
R["profile_entropy"] = float(ent)
prof = []
for c in range(kbest):
    mk_ = lab == c; prof.append(dict(n=int(mk_.sum()), pct=float(mk_.mean()*100), **{v: float(fs_.loc[mk_, v].mean()) for v in FAC}, grp1=float((df.grp.values[mk_] == 1).mean()*100)))
R["profiles"] = prof
fv = {v: stats.f_oneway(*[fs_.loc[lab == c, v] for c in range(max(kbest, 2)) if (lab == c).sum() > 1]) for v in ("SUB", "SYM")} if len(set(lab)) > 1 else {}
R["profile_anova"] = {v: dict(F=float(r.statistic), p=float(r.pvalue)) for v, r in fv.items()}
ct = pd.crosstab(lab, df.grp.values); chi = stats.chi2_contingency(ct); R["profile_chi"] = dict(chi2=float(chi[0]), p=float(chi[1]), df=int(chi[2]))
json.dump(R, open(os.path.join(OUT, "results_gov2.json"), "w"), ensure_ascii=False, indent=1)
bt.describe().T.round(4).to_csv(os.path.join(OUT, "bootstrap_summary.csv"))
fs_.assign(profile=lab).to_csv(os.path.join(OUT, "factor_scores_profiles.csv"), index=False)
print("N", R["n"], "groups", R["demo"]["grp"]); print("CFA", {k: round(v, 3) for k, v in R["cfa"].items()}); print("SEM", {k: round(v, 3) for k, v in R["sem"].items()})
for f, v in R["rel"].items(): print(f, {k: round(x, 3) for k, x in v.items()})
for k, v in R["paths"].items(): print(k, {a: round(b, 3) for a, b in v.items()})
print("resid cov", R["resid_cov"]); print("R2", R["r2"], "f2", R["f2_int"])
for k, v in R["cond"].items(): print(k, {a: (round(b, 3) if not isinstance(b, bool) else b) for a, b in v.items()})
for k, v in R["models"].items(): print(k, v["name"], round(v["chi2"], 1), v["df"], round(v["cfi"], 3), round(v["rmsea"], 3), round(v["bic"], 1))
print("inv", R["invariance"], R["invariance_freed"]); print("latent mean", R["latent_mean_diff"])
print("group diff", {k: (round(v["dz"], 2), round(v["p"], 3)) for k, v in R["group_diff"].items()})
print("profiles k", kbest, bic, "entropy", round(ent, 2)); [print(p) for p in prof]; print(R["profile_anova"], R["profile_chi"]); print("HTMT", R["htmt_max"])
