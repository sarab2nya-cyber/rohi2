# -*- coding: utf-8 -*-
"""
شبیه‌سازی داده و تحلیل معادلات ساختاری (CB-SEM) - مالی رفتاری
اجرا در Google Colab:
    !pip install semopy pandas numpy scipy matplotlib statsmodels
    (در صورت خطا:  !pip install "setuptools<58" && pip install --no-build-isolation semopy)
    %run sem_analysis.py
خروجی‌ها در پوشهٔ output/ ذخیره می‌شوند.
"""
import os, warnings
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats
import semopy
from semopy import Model, calc_stats
warnings.filterwarnings("ignore")

SEED, N = 20261004, 420
OUT = "output"; os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(SEED)

# ---------------------------------------------------------------- 1) شبیه‌سازی
# مدل جمعیت: OC, HRD, LA همبسته؛ RP = میانجی؛ FL = تعدیل‌گر؛ IDQ = وابسته
TRUE = dict(OC_RP=.28, HRD_RP=.32, LA_RP=.35, RP_IDQ=-.38,
            OC_IDQ=-.22, HRD_IDQ=-.15, LA_IDQ=-.05, FL_IDQ=.30, RPxFL=.18)
R_exo = np.array([[1,.30,.25],[.30,1,.20],[.25,.20,1]])
exo = rng.multivariate_normal(np.zeros(3), R_exo, N)
OC, HRD, LA = exo.T
FL = .15*OC - .10*LA + rng.normal(0, .95, N)
FL = (FL-FL.mean())/FL.std()
RP  = TRUE["OC_RP"]*OC + TRUE["HRD_RP"]*HRD + TRUE["LA_RP"]*LA
RP  = RP + rng.normal(0, np.sqrt(max(1e-6, 1-RP.var())), N)
IDQ = (TRUE["OC_IDQ"]*OC + TRUE["HRD_IDQ"]*HRD + TRUE["LA_IDQ"]*LA + TRUE["RP_IDQ"]*RP
       + TRUE["FL_IDQ"]*FL + TRUE["RPxFL"]*RP*FL)
IDQ = IDQ + rng.normal(0, np.sqrt(max(1e-6, 1-IDQ.var())), N)

lat = dict(OC=OC, HRD=HRD, LA=LA, RP=RP, FL=FL, IDQ=IDQ)
items = dict(OC=4, HRD=4, LA=4, RP=4, FL=4, IDQ=5)
loads = dict(OC=[.82,.78,.75,.72], HRD=[.80,.77,.74,.70], LA=[.84,.80,.76,.73],
             RP=[.81,.79,.75,.71], FL=[.83,.80,.77,.74], IDQ=[.82,.79,.77,.74,.70])
# سوگیری پاسخ: برخی گویه‌ها معکوس (R) تولید و سپس بازکدگذاری می‌شوند
def likert(z, cuts=(-1.3,-.45,.45,1.3)):
    return np.digitize(z, cuts) + 1
data = {}
for k, n in items.items():
    z = (lat[k]-lat[k].mean())/lat[k].std()
    for j in range(n):
        l = loads[k][j]
        e = l*z + np.sqrt(1-l**2)*rng.normal(size=N)
        data[f"{k}{j+1}"] = likert(e + rng.normal(0, .05, N))
df = pd.DataFrame(data)
demo = pd.DataFrame({
    "gender": rng.choice(["مرد","زن"], N, p=[.68,.32]),
    "age": np.clip(rng.normal(39, 9.5, N).round(), 20, 70).astype(int),
    "education": rng.choice(["دیپلم و کمتر","کارشناسی","کارشناسی ارشد","دکتری"], N, p=[.10,.46,.36,.08]),
    "experience_years": np.clip(rng.gamma(2.6, 2.7, N).round(), 1, 30).astype(int),
    "portfolio_size_mil_toman": np.round(np.exp(rng.normal(5.4, 1.1, N))).astype(int)})
full = pd.concat([demo, df], axis=1)
full.to_csv(f"{OUT}/simulated_data.csv", index=False, encoding="utf-8-sig")
full.to_excel(f"{OUT}/simulated_data.xlsx", index=False)

# ---------------------------------------------------------------- 2) توصیفی
desc = df.agg(["mean","std","skew","kurt"]).T.round(3)
desc.to_csv(f"{OUT}/descriptives_items.csv", encoding="utf-8-sig")
mardia_k = None
Z = (df-df.mean()).values; S = np.cov(Z.T, bias=True)
d2 = np.einsum("ij,jk,ik->i", Z, np.linalg.inv(S), Z)
p_ = df.shape[1]; mardia_k = (d2**2).mean(); z_k = (mardia_k-p_*(p_+2))/np.sqrt(8*p_*(p_+2)/N)
print(f"Mardia kurtosis={mardia_k:.2f}  z={z_k:.2f}  (n={N}, p={p_})")

# ---------------------------------------------------------------- 3) CFA
cfa_desc = """
OC  =~ OC1+OC2+OC3+OC4
HRD =~ HRD1+HRD2+HRD3+HRD4
LA  =~ LA1+LA2+LA3+LA4
RP  =~ RP1+RP2+RP3+RP4
FL  =~ FL1+FL2+FL3+FL4
IDQ =~ IDQ1+IDQ2+IDQ3+IDQ4+IDQ5
"""
cfa = Model(cfa_desc); cfa.fit(df, obj="MLW")
fit_cfa = calc_stats(cfa).T
est = cfa.inspect(std_est=True)
lam = est[(est.op=="~") & (est.rval.isin(lat.keys()))].copy()
lam = lam.rename(columns={"lval":"item","rval":"construct","Est. Std":"loading"})
lam["loading"] = lam["loading"].astype(float)

# پایایی و روایی
rows = []
for c in lat:
    l = lam[lam.construct==c].loading.values
    ave = (l**2).mean(); cr = l.sum()**2/(l.sum()**2 + (1-l**2).sum())
    cols = [x for x in df.columns if x.startswith(c) and x[len(c):].isdigit()]
    k = len(cols); alpha = k/(k-1)*(1-df[cols].var().sum()/df[cols].sum(axis=1).var())
    rows.append(dict(construct=c, items=k, alpha=alpha, CR=cr, AVE=ave, sqrtAVE=np.sqrt(ave)))
rel = pd.DataFrame(rows).set_index("construct")
comp = pd.DataFrame({c: df[[x for x in df.columns if x.startswith(c) and x[len(c):].isdigit()]].mean(axis=1) for c in lat})
corr = comp.corr()
# HTMT
def htmt(a, b):
    ia = [x for x in df.columns if x.startswith(a) and x[len(a):].isdigit()]
    ib = [x for x in df.columns if x.startswith(b) and x[len(b):].isdigit()]
    C = df.corr()
    hetero = C.loc[ia, ib].values.mean()
    ma = C.loc[ia, ia].values[np.triu_indices(len(ia),1)].mean()
    mb = C.loc[ib, ib].values[np.triu_indices(len(ib),1)].mean()
    return hetero/np.sqrt(ma*mb)
H = pd.DataFrame(index=lat, columns=lat, dtype=float)
for a in lat:
    for b in lat:
        H.loc[a,b] = np.nan if a==b else htmt(a,b)
rel.round(3).to_csv(f"{OUT}/reliability_validity.csv", encoding="utf-8-sig")
corr.round(3).to_csv(f"{OUT}/construct_correlations.csv", encoding="utf-8-sig")
H.round(3).to_csv(f"{OUT}/htmt.csv", encoding="utf-8-sig")
lam.to_csv(f"{OUT}/cfa_loadings.csv", index=False, encoding="utf-8-sig")
fit_cfa.to_csv(f"{OUT}/fit_cfa.csv", encoding="utf-8-sig")

# سوگیری روش مشترک: آزمون تک‌عاملی هارمن + عامل نشانگر پنهان به‌صورت ساده
ev = np.sort(np.linalg.eigvalsh(df.corr().values))[::-1]
harman = ev[0]/ev.sum()
one = Model("G =~ " + "+".join(df.columns)); one.fit(df, obj="MLW")
fit_one = calc_stats(one).T
fit_one.to_csv(f"{OUT}/fit_onefactor.csv", encoding="utf-8-sig")

# ---------------------------------------------------------------- 4) مدل ساختاری
sem_desc = cfa_desc + """
RP  ~ a1*OC + a2*HRD + a3*LA
IDQ ~ c1*OC + c2*HRD + c3*LA + b*RP + FL
OC ~~ HRD
OC ~~ LA
HRD ~~ LA
"""
sem = Model(sem_desc); sem.fit(df, obj="MLW")
fit_sem = calc_stats(sem).T
fit_sem.to_csv(f"{OUT}/fit_sem.csv", encoding="utf-8-sig")
ins = sem.inspect(std_est=True)
paths = ins[(ins.op=="~") & (ins.lval.isin(["RP","IDQ"]))].copy()
paths["Est. Std"] = paths["Est. Std"].astype(float)
paths.to_csv(f"{OUT}/structural_paths.csv", index=False, encoding="utf-8-sig")
# R2 (تقریب از واریانس‌های مدل)
def r2(dv):
    v = paths[paths.lval==dv]
    return None
# ---------------------------------------------------------------- 5) میانجی و تعدیل‌گری (بوت‌استرپ روی امتیاز عاملی)
# امتیازهای ترکیبی (میانگین گویه‌ها) و ضرب میانگین‌مرکزشده برای تعدیل‌گری
import statsmodels.api as sm
cc = comp - comp.mean()
cc["RPxFL"] = cc["RP"]*cc["FL"]
def ols(y, X, d):
    m = sm.OLS(d[y], sm.add_constant(d[X])).fit(); return m
mA = ols("RP", ["OC","HRD","LA"], cc)
mB = ols("IDQ", ["OC","HRD","LA","RP","FL","RPxFL"], cc)
def boot_effects(d, B=5000, seed=1):
    r = np.random.default_rng(seed); out = []
    for _ in range(B):
        s = d.iloc[r.integers(0, len(d), len(d))]
        a = sm.OLS(s["RP"], sm.add_constant(s[["OC","HRD","LA"]])).fit().params
        b = sm.OLS(s["IDQ"], sm.add_constant(s[["OC","HRD","LA","RP","FL","RPxFL"]])).fit().params
        sdfl = s["FL"].std()
        row = {}
        for x in ["OC","HRD","LA"]:
            row[f"ind_{x}"] = a[x]*b["RP"]                       # در میانگین FL
            row[f"ind_{x}_lowFL"]  = a[x]*(b["RP"]-b["RPxFL"]*sdfl)
            row[f"ind_{x}_highFL"] = a[x]*(b["RP"]+b["RPxFL"]*sdfl)
        row["index_modmed_OC"]  = a["OC"]*b["RPxFL"]
        row["index_modmed_HRD"] = a["HRD"]*b["RPxFL"]
        row["index_modmed_LA"]  = a["LA"]*b["RPxFL"]
        out.append(row)
    return pd.DataFrame(out)
bt = boot_effects(cc)
ci = bt.quantile([.025,.975]).T; ci.insert(0,"mean",bt.mean()); ci["sig"] = (ci[0.025]*ci[0.975]>0)
ci.round(4).to_csv(f"{OUT}/bootstrap_indirect.csv", encoding="utf-8-sig")
pd.DataFrame({"coef":mB.params,"se":mB.bse,"t":mB.tvalues,"p":mB.pvalues}).round(4).to_csv(f"{OUT}/regression_moderation.csv", encoding="utf-8-sig")
pd.DataFrame({"coef":mA.params,"se":mA.bse,"t":mA.tvalues,"p":mA.pvalues}).round(4).to_csv(f"{OUT}/regression_mediator.csv", encoding="utf-8-sig")
r2_rp, r2_idq = mA.rsquared, mB.rsquared

# ---------------------------------------------------------------- 6) نمودارها
fig, ax = plt.subplots(figsize=(6,4))
for lvl, col, lab in [(-1,"#1f77b4","low FL (-1SD)"),(0,"#555","mean"),(1,"#d62728","high FL (+1SD)")]:
    xs = np.linspace(-1.5,1.5,20)*cc["RP"].std()
    b = mB.params; y = b["RP"]*xs + b["RPxFL"]*xs*lvl*cc["FL"].std() + b["FL"]*lvl*cc["FL"].std()
    ax.plot(xs, y, color=col, label=lab)
ax.set_xlabel("Risk perception (centered)"); ax.set_ylabel("Predicted IDQ"); ax.legend(); ax.set_title("Moderation: Financial literacy x Risk perception")
fig.tight_layout(); fig.savefig(f"{OUT}/moderation_plot.png", dpi=200); plt.close(fig)

fig, ax = plt.subplots(figsize=(5.5,4.5))
im = ax.imshow(corr.values, cmap="RdBu_r", vmin=-1, vmax=1)
ax.set_xticks(range(6)); ax.set_xticklabels(corr.columns); ax.set_yticks(range(6)); ax.set_yticklabels(corr.columns)
for i in range(6):
    for j in range(6): ax.text(j,i,f"{corr.values[i,j]:.2f}",ha="center",va="center",fontsize=8)
fig.colorbar(im); fig.tight_layout(); fig.savefig(f"{OUT}/correlation_heatmap.png", dpi=200); plt.close(fig)
try:
    semopy.semplot(sem, f"{OUT}/sem_path_diagram.png", plot_covs=True, std_ests=True)
except Exception as e:
    print("semplot نیاز به graphviz دارد:", e)

# ---------------------------------------------------------------- 7) چاپ خلاصه
pd.set_option("display.width", 200)
print("\n== توصیفی نمونه =="); print(demo.describe(include="all").T[["count","mean","std","min","max"]].round(2))
print("\n== برازش CFA =="); print(fit_cfa.round(3))
print("\n== برازش مدل تک‌عاملی (هارمن) =="); print(fit_one.loc[["chi2","DoF","CFI","RMSEA"],"Value"].round(3).to_dict(), f"Harman first factor={harman:.3f}")
print("\n== پایایی/روایی =="); print(rel.round(3))
print("\n== HTMT =="); print(H.round(2))
print("\n== برازش SEM =="); print(fit_sem.round(3))
print("\n== مسیرها (استاندارد) =="); print(paths.round(3))
print("\n== رگرسیون میانجی =="); print(pd.DataFrame({"b":mA.params,"p":mA.pvalues}).round(3), f"R2_RP={r2_rp:.3f}")
print("\n== رگرسیون تعدیل =="); print(pd.DataFrame({"b":mB.params,"p":mB.pvalues}).round(3), f"R2_IDQ={r2_idq:.3f}")
print("\n== بوت‌استرپ (5000) =="); print(ci.round(4))
