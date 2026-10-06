# %% [markdown]
# # تحلیل داده‌های واقعی پیمایش (SEM مبتنی بر کوواریانس)
# مدل: SME → FOMO → HRD → IDQ با تعدیل‌گری AIU روی مسیر FOMO → HRD
# ورودی: فایل اکسل `1.xlsx` با ستون‌های
# `ID gender age edu exp portfolio SME1-5 FOMO1-6 HRD1-5 AIU1-5 IDQ1-5`
# هیچ داده‌ای شبیه‌سازی نمی‌شود؛ همهٔ اعداد از فایل شما محاسبه می‌شوند.

# %% [code]
# --- ۱) نصب (فقط یک‌بار). اگر پس از نصب باز هم semopy پیدا نشد: Runtime ▸ Restart session و دوباره اجرا ---
import os, sys, subprocess, importlib.util
os.environ["OMP_NUM_THREADS"] = "1"
pip = lambda *a: subprocess.run([sys.executable, "-m", "pip", "-q", "install", *a])
pip("numpy", "pandas", "scipy", "statsmodels", "scikit-learn", "matplotlib", "openpyxl", "joblib")
pip("semopy")                                    # روش عادی؛ در نسخه‌های جدید Colab درست کار می‌کند
if importlib.util.find_spec("semopy") is None:   # راه جایگزین (برای محیط‌های قدیمی)
    pip("setuptools<58", "wheel"); pip("--no-build-isolation", "semopy==2.3.11")
print("semopy آماده است:", importlib.util.find_spec("semopy") is not None)

# %% [code]
# --- ۲) تنظیمات و بارگذاری فایل اکسل ---
import sys, json, warnings
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
from scipy import stats
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from joblib import Parallel, delayed
from semopy import Model, calc_stats
warnings.filterwarnings("ignore")

DATA_PATH = "1.xlsx"      # نام فایل اکسل (در Colab آن را آپلود کنید)
SHEET     = 0             # نام یا شمارهٔ شیت
B         = 2000          # تعداد بازنمونهٔ خودگردان (برای آزمایش سریع مثلاً 200)
SEED      = 14031         # فقط برای تکرارپذیری بازنمونه‌گیری
N_JOBS    = -1            # همهٔ هسته‌ها
MALE_CODE = 1             # gender: مرد = 1 ، زن = 0
OUT = "output"; os.makedirs(OUT, exist_ok=True)

if not os.path.exists(DATA_PATH):
    try:
        from google.colab import files
        up = files.upload()                      # فایل اکسل را انتخاب کنید
        DATA_PATH = list(up.keys())[0]
    except ImportError:
        raise FileNotFoundError(f"{DATA_PATH} پیدا نشد")

df = pd.read_excel(DATA_PATH, sheet_name=SHEET)
df.columns = [str(c).strip() for c in df.columns]
FAC = dict(SME=5, FOMO=6, HRD=5, AIU=5, IDQ=5)
ITEMS = [f"{f}{j}" for f, k in FAC.items() for j in range(1, k + 1)]
need = ["gender", "age", "edu", "exp", "portfolio"] + ITEMS
missing_cols = [c for c in need if c not in df.columns]
assert not missing_cols, f"ستون‌های ناموجود: {missing_cols}"

for c in ITEMS + ["age", "exp", "portfolio", "gender", "edu"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")
n_raw = len(df)
bad_rows = df[ITEMS].isna().any(axis=1) | ~df[ITEMS].isin([1, 2, 3, 4, 5]).all(axis=1)
print(f"ردیف‌های اولیه: {n_raw} | ردیف‌های ناقص یا خارج از دامنهٔ ۱ تا ۵: {int(bad_rows.sum())}")
df = df.loc[~bad_rows & df[["age", "exp", "gender"]].notna().all(axis=1)].reset_index(drop=True)
if "ID" in df.columns:
    dup = int(df["ID"].duplicated().sum()); print("ID تکراری:", dup)
    df = df.drop_duplicates("ID").reset_index(drop=True)
assert set(df.gender.unique()) <= {0, 1}, f"مقادیر غیرمنتظره در gender: {df.gender.unique()}"
print("نمونهٔ نهایی N =", len(df))
# پاسخ‌های یکنواخت (straight-lining) فقط گزارش می‌شود و حذف نمی‌شود
R = {"n_raw": int(n_raw), "n": int(len(df)), "straightliners": int((df[ITEMS].std(axis=1) == 0).sum())}
print("پاسخ‌دهندگان با پاسخ یکنواخت:", R["straightliners"])
X = df[ITEMS].astype(float)
z = lambda x: (x - x.mean()) / x.std()

# %% [code]
# --- ۳) آمار توصیفی و جمعیت‌شناختی ---
R["demo"] = dict(
    male=float((df.gender == MALE_CODE).mean() * 100), female=float((df.gender != MALE_CODE).mean() * 100),
    age_m=float(df.age.mean()), age_sd=float(df.age.std()), exp_m=float(df.exp.mean()), exp_sd=float(df.exp.std()),
    edu={str(k): float(v * 100) for k, v in df.edu.value_counts(normalize=True).sort_index().items()},
    port_med=float(df.portfolio.median()), port_q1=float(df.portfolio.quantile(.25)), port_q3=float(df.portfolio.quantile(.75)))
it = pd.DataFrame({"mean": X.mean(), "sd": X.std(), "skew": X.apply(stats.skew), "kurt": X.apply(stats.kurtosis)})
R["items"] = it.round(3).to_dict("index")
Zc = (X - X.mean()).values; S = np.cov(Zc.T, bias=True); d2 = np.einsum("ij,jk,ik->i", Zc, np.linalg.inv(S), Zc)
p = X.shape[1]; mk = (d2 ** 2).mean()
R["mardia"] = dict(k=float(mk), expected=float(p * (p + 2)), z=float((mk - p * (p + 2)) / np.sqrt(8 * p * (p + 2) / len(df))))
R["skew_range"] = [float(it["skew"].min()), float(it["skew"].max())]; R["kurt_range"] = [float(it["kurt"].min()), float(it["kurt"].max())]
print(it.round(2)); print("Mardia:", R["mardia"])

# %% [code]
# --- ۴) توابع کمکی ---
def lam_desc():
    return "".join(f"{k} =~ " + "+".join(f"{k}{j}" for j in range(1, n + 1)) + "\n" for k, n in FAC.items())
CFA = lam_desc()

def srmr(m, data):
    sig = m.calc_sigma()[0]; names = m.vars["observed"]
    Sx = data[names].cov().values; sd = np.sqrt(np.diag(Sx))
    res = (Sx - sig) / np.outer(sd, sd); tri = np.tril_indices(len(names))
    return float(np.sqrt((res[tri] ** 2).mean()))

def fitstats(m, data):
    s = calc_stats(m).T["Value"]
    return dict(chi2=float(s["chi2"]), df=float(s["DoF"]), p=float(s["chi2 p-value"]), cfi=float(s["CFI"]), tli=float(s["TLI"]),
                rmsea=float(s["RMSEA"]), gfi=float(s["GFI"]), srmr=srmr(m, data), aic=float(s["AIC"]), bic=float(s["BIC"]))

def row(ins, l, o, r):
    q = ins[(ins.lval == l) & (ins.op == o) & (ins.rval == r)].iloc[0]
    g = lambda c: float(q[c]) if str(q[c]) not in ("-", "nan") else np.nan
    return dict(b=g("Estimate"), beta=g("Est. Std"), se=g("Std. Err"), z=g("z-value"), p=g("p-value"))

# %% [code]
# --- ۵) CFA: برازش، پایایی، روایی همگرا و واگرا، سوگیری روش مشترک ---
cfa = Model(CFA); cfa.fit(X)
R["cfa"] = fitstats(cfa, X)
ins = cfa.inspect(std_est=True)
lo = ins[(ins.op == "~") & (ins.rval.isin(FAC.keys()))].copy()
lo["Est. Std"] = lo["Est. Std"].astype(float)
R["loadings"] = {r.lval: float(r["Est. Std"]) for _, r in lo.iterrows()}
rel = {}
for f, k in FAC.items():
    l = lo[lo.rval == f]["Est. Std"].values; cols = [f"{f}{j}" for j in range(1, k + 1)]
    ave = float((l ** 2).mean()); cr = float(l.sum() ** 2 / (l.sum() ** 2 + (1 - l ** 2).sum()))
    alpha = float(k / (k - 1) * (1 - X[cols].var().sum() / X[cols].sum(axis=1).var()))
    rel[f] = dict(items=k, alpha=alpha, cr=cr, ave=ave, sqrt_ave=ave ** .5, lmin=float(l.min()), lmax=float(l.max()))
R["rel"] = rel
lc = ins[(ins.op == "~~") & (ins.lval.isin(FAC)) & (ins.rval.isin(FAC)) & (ins.lval != ins.rval)]
latcorr = pd.DataFrame(np.eye(len(FAC)), index=list(FAC), columns=list(FAC))
for _, r in lc.iterrows():
    latcorr.loc[r.lval, r.rval] = latcorr.loc[r.rval, r.lval] = float(r["Est. Std"])
R["latcorr"] = latcorr.round(3).to_dict()
C = X.corr()
def htmt(a, b):
    ia = [f"{a}{j}" for j in range(1, FAC[a] + 1)]; ib = [f"{b}{j}" for j in range(1, FAC[b] + 1)]
    h = C.loc[ia, ib].abs().values.mean()
    ma = C.loc[ia, ia].values[np.triu_indices(len(ia), 1)].mean(); mb = C.loc[ib, ib].values[np.triu_indices(len(ib), 1)].mean()
    return float(h / np.sqrt(ma * mb))
R["htmt"] = {a: {b: htmt(a, b) for b in FAC if b != a} for a in FAC}
R["htmt_max"] = max(v for a in R["htmt"].values() for v in a.values())
ev = np.sort(np.linalg.eigvalsh(X.corr().values))[::-1]
one = Model("G =~ " + "+".join(ITEMS)); one.fit(X)
R["cmb"] = dict(harman=float(ev[0] / ev.sum() * 100), one_factor=fitstats(one, X))
try:   # مدل عامل روش مشترک (CLF)
    clf_desc = CFA + "M =~ " + "+".join(ITEMS) + "\n" + "\n".join(f"M ~~ 0*{f}" for f in FAC) + "\n"
    clf = Model(clf_desc); clf.fit(X); R["cmb"]["clf"] = fitstats(clf, X)
    ci = clf.inspect(std_est=True); mm = ci[(ci.op == "~") & (ci.rval == "M")]["Est. Std"].astype(float)
    R["cmb"]["clf_var"] = float((mm ** 2).mean() * 100)
except Exception as e:
    print("CLF اجرا نشد:", e); R["cmb"]["clf"] = None
comp = pd.DataFrame({f: X[[f"{f}{j}" for j in range(1, k + 1)]].mean(axis=1) for f, k in FAC.items()})
Xv = sm.add_constant(comp[["SME", "FOMO", "AIU", "HRD"]])    # فقط برای VIF
R["vif"] = {c: float(variance_inflation_factor(Xv.values, i)) for i, c in enumerate(Xv.columns) if c != "const"}
print("CFA:", {k: round(v, 3) for k, v in R["cfa"].items()})
for f, v in rel.items(): print(f, {k: round(x, 3) for k, x in v.items()})
print("HTMT max:", round(R["htmt_max"], 3), "| Harman:", round(R["cmb"]["harman"], 1), "| VIF:", {k: round(v, 2) for k, v in R["vif"].items()})

# %% [code]
# --- ۶) مدل ساختاری مکنون با تعامل پنهان (شاخص‌های حاصل‌ضرب جفت‌شدهٔ میانگین‌مرکزشده) ---
dfc = X - X.mean()
for i in range(1, 6): dfc[f"INT{i}"] = dfc[f"FOMO{i}"] * dfc[f"AIU{i}"]
dfc["age"] = z(df.age.astype(float)).values
dfc["gender"] = z((df.gender == MALE_CODE).astype(float)).values
dfc["exp"] = z(df.exp.astype(float)).values
MEAS = CFA + "INT =~ INT1+INT2+INT3+INT4+INT5\n"
ORTH = "SME ~~ AIU\nSME ~~ INT\nAIU ~~ INT\nFOMO ~~ INT\n"
M_FULL = MEAS + "FOMO ~ SME + AIU + age + gender\nHRD ~ FOMO + SME + AIU + INT + exp\nIDQ ~ HRD + FOMO + SME + AIU + exp\n" + ORTH
sem = Model(M_FULL); sem.fit(dfc)
R["sem"] = fitstats(sem, dfc)
si = sem.inspect(std_est=True)
PATHS = [("FOMO", "SME"), ("FOMO", "AIU"), ("FOMO", "age"), ("FOMO", "gender"), ("HRD", "FOMO"), ("HRD", "SME"), ("HRD", "AIU"),
         ("HRD", "INT"), ("HRD", "exp"), ("IDQ", "HRD"), ("IDQ", "FOMO"), ("IDQ", "SME"), ("IDQ", "AIU"), ("IDQ", "exp")]
R["paths"] = {f"{l}~{r}": row(si, l, "~", r) for l, r in PATHS}
R["r2_latent"] = {}
for f in ("FOMO", "HRD", "IDQ"):     # R² مکنون = 1 − واریانس باقی‌ماندهٔ استاندارد
    q_ = si[(si.lval == f) & (si.op == "~~") & (si.rval == f)]
    R["r2_latent"][f] = float(1 - float(q_["Est. Std"].iloc[0]))
cz = (comp - comp.mean()) / comp.std(); cz["INT"] = cz.FOMO * cz.AIU
for k in ["age", "gender", "exp"]: cz[k] = dfc[k].values
R["r2_comp"] = dict(
    FOMO=float(sm.OLS(cz.FOMO, sm.add_constant(cz[["SME", "AIU", "age", "gender"]])).fit().rsquared),
    HRD=float(sm.OLS(cz.HRD, sm.add_constant(cz[["FOMO", "SME", "AIU", "INT", "exp"]])).fit().rsquared),
    IDQ=float(sm.OLS(cz.IDQ, sm.add_constant(cz[["HRD", "FOMO", "SME", "AIU", "exp"]])).fit().rsquared))
r2_noint = float(sm.OLS(cz.HRD, sm.add_constant(cz[["FOMO", "SME", "AIU", "exp"]])).fit().rsquared)
R["f2_int"] = float((R["r2_comp"]["HRD"] - r2_noint) / (1 - R["r2_comp"]["HRD"]))
print("SEM:", {k: round(v, 3) for k, v in R["sem"].items()})
for k, v in R["paths"].items(): print(k, {a: round(b, 3) for a, b in v.items()})
print("R2 مکنون:", {k: round(v, 3) for k, v in R["r2_latent"].items()}, "| R2 نمرات ترکیبی (تقریبی):", R["r2_comp"], "| f2 تعامل:", round(R["f2_int"], 3))

# %% [code]
# --- ۷) اثرهای غیرمستقیم، شرطی و شاخص میانجی‌گری تعدیل‌شده (خودگردان) ---
ins0 = sem.inspect()
sig_aiu = float(ins0[(ins0.lval == "AIU") & (ins0.op == "~~") & (ins0.rval == "AIU")]["Estimate"].iloc[0]) ** .5

def eff_std(ii):
    g = lambda l, r: float(ii[(ii.lval == l) & (ii.rval == r) & (ii.op == "~")]["Est. Std"].iloc[0])
    a, e, c, bh, bf, bs = g("FOMO", "SME"), g("HRD", "FOMO"), g("HRD", "SME"), g("IDQ", "HRD"), g("IDQ", "FOMO"), g("IDQ", "SME")
    o = {"std_seq": a * e * bh, "std_SME_HRD_IDQ": c * bh, "std_SME_FOMO_IDQ": a * bf}
    o["std_ind_total"] = o["std_seq"] + o["std_SME_HRD_IDQ"] + o["std_SME_FOMO_IDQ"]
    o["std_total"] = o["std_ind_total"] + bs
    return o

def eff(ii, sdA):
    g = lambda l, r: float(ii[(ii.lval == l) & (ii.rval == r) & (ii.op == "~")]["Estimate"].iloc[0])
    a, e, c = g("FOMO", "SME"), g("HRD", "FOMO"), g("HRD", "SME")
    w, bh, bf, bs = g("HRD", "INT"), g("IDQ", "HRD"), g("IDQ", "FOMO"), g("IDQ", "SME")
    o = {}
    for tag, k in [("low", -1), ("mean", 0), ("high", 1)]:
        slope = e + w * k * sdA
        o[f"ind_SME_FOMO_HRD_IDQ_{tag}"] = a * slope * bh
        o[f"ind_SME_HRD_IDQ_{tag}"] = c * bh
        o[f"ind_SME_FOMO_IDQ_{tag}"] = a * bf
        o[f"slope_FOMO_HRD_{tag}"] = slope
    o["ind_total_mean"] = o["ind_SME_FOMO_HRD_IDQ_mean"] + o["ind_SME_HRD_IDQ_mean"] + o["ind_SME_FOMO_IDQ_mean"]
    o["total_effect_mean"] = o["ind_total_mean"] + bs
    o["imm"] = a * w * bh
    return o

point = {**eff(ins0, sig_aiu), **eff_std(si)}

def boot_once(seed):
    rs = np.random.default_rng(seed)
    ix = rs.integers(0, len(dfc), len(dfc)); bd = dfc.iloc[ix].reset_index(drop=True)
    try:
        mb = Model(M_FULL); mb.fit(bd); ib = mb.inspect()
        sb = float(ib[(ib.lval == "AIU") & (ib.op == "~~") & (ib.rval == "AIU")]["Estimate"].iloc[0]) ** .5
        return {**eff(ib, sb), **eff_std(mb.inspect(std_est=True))}
    except Exception:
        return None

seeds = np.random.SeedSequence(SEED).generate_state(B)
print(f"اجرای {B} بازنمونه ... (ممکن است ده‌ها دقیقه طول بکشد)")
bt = pd.DataFrame([r for r in Parallel(n_jobs=N_JOBS)(delayed(boot_once)(int(s)) for s in seeds) if r])
R["boot_n"] = int(len(bt))
R["indirect"] = {k: dict(est=float(point[k]), lo=float(bt[k].quantile(.025)), hi=float(bt[k].quantile(.975)),
                         sig=bool(bt[k].quantile(.025) * bt[k].quantile(.975) > 0)) for k in point}
R["sig_aiu"] = sig_aiu
for k, v in R["indirect"].items(): print(k, {a: (round(b, 3) if not isinstance(b, bool) else b) for a, b in v.items()})
print("بازنمونه‌های موفق:", R["boot_n"], "از", B)

# %% [code]
# --- ۸) مدل‌های رقیب و تحلیل‌های استحکام ---
cand = {
 "M1": ("پیشنهادی (میانجی جزئی)", "FOMO ~ SME + age + gender\nHRD ~ FOMO + SME + exp\nIDQ ~ HRD + FOMO + SME + exp\n"),
 "M2": ("میانجی کامل زنجیره‌ای", "FOMO ~ SME + age + gender\nHRD ~ FOMO + exp\nIDQ ~ HRD + exp\n"),
 "M3": ("ترتیب معکوس (توده‌واری←FOMO)", "HRD ~ SME + exp\nFOMO ~ HRD + SME + age + gender\nIDQ ~ FOMO + HRD + SME + exp\n"),
 "M4": ("اثر مستقیم بدون میانجی", "FOMO ~ SME + age + gender\nHRD ~ SME + exp\nIDQ ~ SME + exp\n")}
R["models"] = {}
for k, (nm, body) in cand.items():
    mm = Model(CFA + body + "AIU ~~ SME\nAIU ~~ FOMO\nAIU ~~ HRD\nAIU ~~ IDQ\n"); mm.fit(dfc)
    R["models"][k] = dict(name=nm, **fitstats(mm, dfc))
R["delta_chi2_M1_M2"] = dict(d_chi2=R["models"]["M2"]["chi2"] - R["models"]["M1"]["chi2"], d_df=R["models"]["M2"]["df"] - R["models"]["M1"]["df"])
R["delta_chi2_M1_M2"]["p"] = float(stats.chi2.sf(R["delta_chi2_M1_M2"]["d_chi2"], R["delta_chi2_M1_M2"]["d_df"]))
try:   # برآوردگر DWLS
    cols = ITEMS + ["age", "gender", "exp"]
    md = Model(CFA + "FOMO ~ SME + AIU + age + gender\nHRD ~ FOMO + SME + AIU + exp\nIDQ ~ HRD + FOMO + SME + AIU + exp\n")
    md.fit(dfc[cols], obj="DWLS"); di = md.inspect(std_est=True)
    R["dwls"] = {f"{l}~{r}": row(di, l, "~", r) for l, r in [("FOMO", "SME"), ("HRD", "FOMO"), ("IDQ", "HRD"), ("HRD", "SME"), ("IDQ", "FOMO"), ("IDQ", "AIU"), ("HRD", "AIU")]}
    R["dwls_fit"] = fitstats(md, dfc[cols])
except Exception as e:
    print("DWLS اجرا نشد:", e); R["dwls"] = None
# تعامل با روش مرکزسازی باقی‌مانده
try:
    dres = dfc.copy()
    for i in range(1, 6):
        Z = sm.add_constant(dfc[[f"FOMO{i}", f"AIU{i}"]]); dres[f"INT{i}"] = sm.OLS(dfc[f"INT{i}"], Z).fit().resid.values
    mr = Model(M_FULL); mr.fit(dres); ri = mr.inspect(std_est=True)
    R["resid_centering"] = {f"{l}~{r}": row(ri, l, "~", r) for l, r in [("FOMO", "SME"), ("HRD", "FOMO"), ("IDQ", "HRD"), ("HRD", "INT")]}
    R["resid_centering_fit"] = fitstats(mr, dres)
except Exception as e:
    print("مرکزسازی باقی‌مانده اجرا نشد:", e); R["resid_centering"] = None
# رگرسیون نمرات ترکیبی با خطای معیار مقاوم (HC3) و شیب‌های ساده
mod = sm.OLS(cz.HRD, sm.add_constant(cz[["FOMO", "SME", "AIU", "INT", "exp"]])).fit(cov_type="HC3")
R["ols_hrd"] = {k: dict(b=float(mod.params[k]), se=float(mod.bse[k]), t=float(mod.tvalues[k]), p=float(mod.pvalues[k])) for k in mod.params.index}
R["simple_slopes"] = {}
for tag, k in [("low", -1), ("mean", 0), ("high", 1)]:
    Xs = cz[["FOMO", "SME", "AIU", "INT", "exp"]].copy(); Xs["AIU"] = cz.AIU - k; Xs["INT"] = cz.FOMO * (cz.AIU - k)
    m_ = sm.OLS(cz.HRD, sm.add_constant(Xs)).fit(cov_type="HC3")
    R["simple_slopes"][tag] = dict(b=float(m_.params["FOMO"]), se=float(m_.bse["FOMO"]), t=float(m_.tvalues["FOMO"]), p=float(m_.pvalues["FOMO"]))
# حذف ۵٪ دورترین مشاهدات (ماهالانوبیس)
keep = d2 < np.quantile(d2, .95); R["outliers_removed"] = int((~keep).sum())
try:
    m_o = Model(M_FULL); m_o.fit(dfc[keep].reset_index(drop=True)); oi = m_o.inspect(std_est=True)
    R["no_outliers"] = {f"{l}~{r}": row(oi, l, "~", r) for l, r in [("FOMO", "SME"), ("HRD", "FOMO"), ("IDQ", "HRD"), ("HRD", "INT"), ("IDQ", "FOMO")]}
except Exception as e:
    print("حذف پرت اجرا نشد:", e); R["no_outliers"] = None
for k, v in R["models"].items(): print(k, v["name"], round(v["chi2"], 1), v["df"], round(v["cfi"], 3), round(v["rmsea"], 3), round(v["bic"], 1))
print("Δχ² (M1 vs M2):", R["delta_chi2_M1_M2"]); print("شیب‌های ساده:", R["simple_slopes"])

# %% [code]
# --- ۹) ذخیرهٔ نتایج و جدول‌های آمادهٔ مقاله ---
json.dump(R, open(os.path.join(OUT, "results_paper1.json"), "w"), ensure_ascii=False, indent=1)
bt.describe().T.round(4).to_csv(os.path.join(OUT, "bootstrap_summary.csv"), encoding="utf-8-sig")
r3 = lambda x: round(float(x), 3)
with pd.ExcelWriter(os.path.join(OUT, "paper1_tables.xlsx")) as xw:
    pd.DataFrame(R["items"]).T.assign(loading=pd.Series(R["loadings"])).round(3).to_excel(xw, sheet_name="T_items")
    pd.DataFrame(R["rel"]).T.round(3).to_excel(xw, sheet_name="T_reliability")
    pd.DataFrame(R["latcorr"]).round(3).to_excel(xw, sheet_name="T_latent_corr")
    pd.DataFrame(R["htmt"]).round(3).to_excel(xw, sheet_name="T_HTMT")
    pd.DataFrame({"CFA": R["cfa"], "SEM": R["sem"], "one_factor": R["cmb"]["one_factor"]}).round(3).to_excel(xw, sheet_name="T_fit")
    pd.DataFrame(R["paths"]).T.round(3).to_excel(xw, sheet_name="T_paths")
    pd.DataFrame(R["indirect"]).T.round(3).to_excel(xw, sheet_name="T_indirect")
    pd.DataFrame(R["models"]).T.round(3).to_excel(xw, sheet_name="T_models")
    pd.DataFrame(R["simple_slopes"]).T.round(3).to_excel(xw, sheet_name="T_simple_slopes")
    pd.json_normalize(R["demo"]).T.round(3).to_excel(xw, sheet_name="T_demographics")
print("ذخیره شد:", os.listdir(OUT))

# %% [code]
# --- ۱۰) دانلود همهٔ خروجی‌ها ---
import shutil
shutil.make_archive("output_results", "zip", OUT)
try:
    from google.colab import files
    files.download("output_results.zip")
except ImportError:
    pass
