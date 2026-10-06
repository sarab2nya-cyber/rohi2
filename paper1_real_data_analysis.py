# %% [markdown]
# # تحلیل کامل داده‌های واقعی پژوهش (SEM مبتنی بر کوواریانس)
# مدل: SME → FOMO → HRD → IDQ با تعدیل‌گری AIU روی مسیر FOMO → HRD
# ورودی: فایل اکسل با ستون‌های `ID gender age edu exp portfolio SME1-5 FOMO1-6 HRD1-5 AIU1-5 IDQ1-5`
# همهٔ اعداد از فایل شما محاسبه می‌شوند. همهٔ آماره‌ها در جدول‌های آمادهٔ مقاله (Excel + PNG) و نمودارها (PNG) ذخیره می‌شوند.

# %% [code]
# --- ۱) نصب (فقط یک‌بار). اگر قبلاً نصب ناموفق بوده: Runtime ▸ Disconnect and delete runtime ---
import os, sys, subprocess, importlib.util
os.environ["OMP_NUM_THREADS"] = "1"
def pip(*a):
    r = subprocess.run([sys.executable, "-m", "pip", "install", "-q", *a], capture_output=True, text=True)
    if r.returncode: print("خطای pip برای", a, "\n", r.stderr[-1500:])
    return r.returncode
pip("-U", "setuptools>=65", "wheel")
pip("numpy", "pandas", "scipy", "statsmodels", "scikit-learn", "matplotlib", "openpyxl", "joblib")
if pip("semopy"): pip("--no-build-isolation", "semopy")
ok = importlib.util.find_spec("semopy") is not None
print("semopy آماده است:", ok); assert ok, "semopy نصب نشد؛ متن خطای بالا را بفرستید."

# %% [code]
# --- ۲) تنظیمات، بارگذاری و ابزارهای کمکی ---
import json, shutil, warnings
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, Rectangle, FancyArrowPatch
from scipy import stats
import statsmodels.api as sm
from statsmodels.stats.diagnostic import lilliefors
from statsmodels.stats.outliers_influence import variance_inflation_factor
from joblib import Parallel, delayed
from IPython.display import display
from semopy import Model, calc_stats
warnings.filterwarnings("ignore")
pd.set_option("display.width", 200, "display.max_columns", 50)
plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 110})

DATA_PATH = "1.xlsx"       # نام فایل اکسل (در Colab آپلود می‌شود)
SHEET, B, SEED, N_JOBS = 0, 2000, 14031, -1     # B=2000 بازنمونه (برای آزمایش سریع 200)
MALE_CODE = 1              # gender: مرد = 1 ، زن = 0
EDU_LABELS = {}            # مثال: {1: "Diploma", 2: "Bachelor", 3: "Master", 4: "PhD"}
OUT = "output"; PNG = f"{OUT}/png"; os.makedirs(PNG, exist_ok=True)

if not os.path.exists(DATA_PATH):
    from google.colab import files
    DATA_PATH = list(files.upload().keys())[0]
df = pd.read_excel(DATA_PATH, sheet_name=SHEET); df.columns = [str(c).strip() for c in df.columns]
FAC = dict(SME=5, FOMO=6, HRD=5, AIU=5, IDQ=5)
FULL = dict(SME="Social Media Exposure", FOMO="Fear of Missing Out", HRD="Herd Behavior", AIU="Accounting Information Use", IDQ="Investment Decision Quality")
ITEMS = [f"{f}{j}" for f, k in FAC.items() for j in range(1, k + 1)]
miss = [c for c in ["gender", "age", "edu", "exp", "portfolio"] + ITEMS if c not in df.columns]
assert not miss, f"ستون‌های ناموجود: {miss}"
for c in ITEMS + ["gender", "age", "edu", "exp", "portfolio"]: df[c] = pd.to_numeric(df[c], errors="coerce")
n_raw = len(df)
bad = df[ITEMS].isna().any(axis=1) | ~df[ITEMS].isin([1, 2, 3, 4, 5]).all(axis=1) | df[["gender", "age", "exp"]].isna().any(axis=1)
df = df.loc[~bad].reset_index(drop=True)
if "ID" in df.columns: df = df.drop_duplicates("ID").reset_index(drop=True)
assert set(df.gender.unique()) <= {0, 1}, f"مقادیر غیرمنتظره در gender: {df.gender.unique()}"
print(f"ردیف‌های اولیه {n_raw} | حذف‌شده {n_raw - len(df)} | نمونهٔ نهایی N = {len(df)}")
X = df[ITEMS].astype(float)
comp = pd.DataFrame({f: X[[f"{f}{j}" for j in range(1, k + 1)]].mean(axis=1) for f, k in FAC.items()})
z = lambda x: (x - x.mean()) / x.std()

R, TABLES = {"n_raw": int(n_raw), "n": int(len(df))}, {}
def stars(p):
    return "" if pd.isna(p) else "***" if p < .001 else "**" if p < .01 else "*" if p < .05 else "ns"
def fmtp(p): return "<.001" if p < .001 else f"{p:.3f}"

def table(df_, key, title, heat=False):
    """نمایش جدول زیبا + ذخیره در Excel و PNG."""
    TABLES[key] = df_
    d = df_.copy()
    sty = d.style.format(precision=3, na_rep="–").set_caption(title).set_table_styles([
        {"selector": "caption", "props": "font-size:14px;font-weight:bold;text-align:left;margin-bottom:6px"},
        {"selector": "th", "props": "background-color:#2f4b7c;color:white;text-align:center;font-weight:600"},
        {"selector": "td", "props": "text-align:center"}])
    if heat: sty = sty.background_gradient(cmap="Blues", axis=None)
    display(sty)
    nr, nc = d.shape; fig, ax = plt.subplots(figsize=(max(5, 1.15 * (nc + 1)), 0.34 * (nr + 3))); ax.axis("off")
    cell = d.reset_index() if not isinstance(d.index, pd.RangeIndex) else d
    if "index" in cell.columns: cell = cell.rename(columns={"index": ""})
    txt = cell.map(lambda v: f"{v:.3f}" if isinstance(v, (float, np.floating)) else str(v)).values if hasattr(cell, "map") else cell.applymap(lambda v: f"{v:.3f}" if isinstance(v, (float, np.floating)) else str(v)).values
    t = ax.table(cellText=txt, colLabels=[str(c) for c in cell.columns], loc="center", cellLoc="center")
    t.auto_set_font_size(False); t.set_fontsize(8); t.auto_set_column_width(list(range(len(cell.columns)))); t.scale(1, 1.25)
    for (r_, c_), cl in t.get_celld().items():
        cl.set_edgecolor("#d0d7e2")
        if r_ == 0: cl.set_facecolor("#2f4b7c"); cl.set_text_props(color="white", weight="bold")
        elif r_ % 2 == 0: cl.set_facecolor("#f1f5fb")
    ax.set_title(title, fontsize=10, weight="bold", loc="left")
    fig.savefig(f"{PNG}/table_{key}.png", dpi=200, bbox_inches="tight"); plt.close(fig)

def savefig(fig, name):
    fig.savefig(f"{PNG}/{name}.png", dpi=300, bbox_inches="tight"); plt.show()

def describe(d):
    return pd.DataFrame({"N": d.count(), "Mean": d.mean(), "SD": d.std(), "SE": d.sem(), "Median": d.median(), "Q1": d.quantile(.25), "Q3": d.quantile(.75),
                         "Min": d.min(), "Max": d.max(), "Skewness": d.apply(stats.skew), "Kurtosis": d.apply(stats.kurtosis)})

# %% [code]
# --- ۳) جدول‌های جمعیت‌شناختی ---
g = df.gender.map({MALE_CODE: "Male"}).fillna("Female").value_counts()
cats = [pd.DataFrame({"Variable": "Gender", "Category": g.index, "Frequency": g.values, "Percent": g.values / len(df) * 100})]
e = df.edu.value_counts().sort_index()
cats.append(pd.DataFrame({"Variable": "Education", "Category": [EDU_LABELS.get(int(k), f"code {int(k)}") for k in e.index], "Frequency": e.values, "Percent": e.values / len(df) * 100}))
cat = pd.concat(cats, ignore_index=True); cat["Cumulative %"] = cat.groupby("Variable")["Percent"].cumsum()
table(cat, "T01_demo_categorical", "Table 1. Demographic characteristics (categorical)")
dn = describe(df[["age", "exp", "portfolio"]].astype(float))
dn["CI95 low"], dn["CI95 high"] = dn.Mean - 1.96 * dn.SE, dn.Mean + 1.96 * dn.SE
table(dn, "T02_demo_numeric", "Table 2. Demographic characteristics (numeric)")
R["demo"] = dict(male=float((df.gender == MALE_CODE).mean() * 100), age_m=float(df.age.mean()), age_sd=float(df.age.std()),
                 exp_m=float(df.exp.mean()), exp_sd=float(df.exp.std()), port_med=float(df.portfolio.median()))

# %% [code]
# --- ۴) آمار توصیفی متغیرهای پژوهش ---
it = describe(X); it.insert(0, "Construct", [i.rstrip("0123456789") for i in it.index])
table(it, "T03_items_descriptive", "Table 3. Descriptive statistics of research items")
cd = describe(comp); cd["Cronbach alpha"] = [0.0] * len(cd)
for f, k in FAC.items():
    c = X[[f"{f}{j}" for j in range(1, k + 1)]]; cd.loc[f, "Cronbach alpha"] = k / (k - 1) * (1 - c.var().sum() / c.sum(axis=1).var())
table(cd, "T04_constructs_descriptive", "Table 4. Descriptive statistics of constructs (item means)")
cc = comp.corr(); pv = comp.corr(method=lambda a, b: stats.pearsonr(a, b)[1])
cm = cc.round(3).astype(str) + pv.map(lambda p: stars(p) if p < .05 else "")
for i in range(len(cm)): cm.iloc[i, i] = "1"
table(cm, "T05_construct_correlations", "Table 5. Pearson correlations between constructs")
R["items"] = it.round(3).to_dict("index")

# %% [code]
# --- ۵) آزمون‌های نرمال بودن (تک‌متغیره و چندمتغیره) ---
nv = pd.concat([X, comp, df[["age", "exp", "portfolio"]].astype(float)], axis=1)
rows = []
for c in nv.columns:
    x = nv[c].dropna().values; ks_l = lilliefors(x, dist="norm"); ks = stats.kstest((x - x.mean()) / x.std(), "norm"); sw = stats.shapiro(x)
    sk, ku = stats.skew(x), stats.kurtosis(x)
    rows.append(dict(Variable=c, KS_stat=ks.statistic, KS_p=ks.pvalue, Lilliefors_stat=ks_l[0], Lilliefors_p=ks_l[1], SW_stat=sw.statistic, SW_p=sw.pvalue,
                     Skewness=sk, z_skew=sk / np.sqrt(6 / len(x)), Kurtosis=ku, z_kurt=ku / np.sqrt(24 / len(x)),
                     Normal=("Yes" if min(ks_l[1], sw.pvalue) >= .05 else "No")))
table(pd.DataFrame(rows).set_index("Variable"), "T06_normality", "Table 6. Normality tests (Kolmogorov–Smirnov, Lilliefors, Shapiro–Wilk)")
Zc = (X - X.mean()).values; S = np.cov(Zc.T, bias=True); Si = np.linalg.inv(S); n_, p_ = Zc.shape
G = Zc @ Si @ Zc.T; b1 = (G ** 3).sum() / n_ ** 2; d2 = np.diag(G); b2 = (d2 ** 2).mean()
sk_stat = n_ * b1 / 6; sk_df = p_ * (p_ + 1) * (p_ + 2) / 6; ku_z = (b2 - p_ * (p_ + 2)) / np.sqrt(8 * p_ * (p_ + 2) / n_)
R["mardia"] = dict(skew=float(b1), skew_chi2=float(sk_stat), skew_df=float(sk_df), skew_p=float(stats.chi2.sf(sk_stat, sk_df)),
                   kurt=float(b2), kurt_expected=float(p_ * (p_ + 2)), kurt_z=float(ku_z), kurt_p=float(2 * stats.norm.sf(abs(ku_z))))
mt = pd.DataFrame({"Statistic": [b1, b2], "Expected/df": [sk_df, p_ * (p_ + 2)], "Test value": [sk_stat, ku_z], "p": [R["mardia"]["skew_p"], R["mardia"]["kurt_p"]]},
                  index=["Mardia skewness (chi2)", "Mardia kurtosis (z)"])
table(mt, "T07_mardia", "Table 7. Multivariate normality (Mardia)")
fig, ax = plt.subplots(2, 5, figsize=(17, 6))
for i, f in enumerate(FAC):
    ax[0, i].hist(comp[f], bins=14, color="#2f4b7c", alpha=.85, edgecolor="white", density=True)
    xs = np.linspace(comp[f].min(), comp[f].max(), 100); ax[0, i].plot(xs, stats.norm.pdf(xs, comp[f].mean(), comp[f].std()), color="#d45087", lw=2)
    ax[0, i].set_title(f); stats.probplot(comp[f], plot=ax[1, i]); ax[1, i].set_title(""); ax[1, i].get_lines()[0].set_color("#2f4b7c"); ax[1, i].get_lines()[1].set_color("#d45087")
fig.suptitle("Distribution and Q–Q plots of constructs", weight="bold"); fig.tight_layout(); savefig(fig, "fig01_distributions")

# %% [code]
# --- ۶) CFA: بارها، پایایی، روایی همگرا و واگرا (Fornell–Larcker, HTMT, HTMT2) ---
CFA = "".join(f"{k} =~ " + "+".join(f"{k}{j}" for j in range(1, n + 1)) + "\n" for k, n in FAC.items())
cfa = Model(CFA); cfa.fit(X); ins = cfa.inspect(std_est=True)
lo = ins[(ins.op == "~") & (ins.rval.isin(FAC))].copy()
num = lambda s: pd.to_numeric(s, errors="coerce")
lo["Est. Std"] = num(lo["Est. Std"])
rows = []
for _, r in lo.iterrows():
    f = r.rval; cols = [f"{f}{j}" for j in range(1, FAC[f] + 1)]; own = r.lval
    rest = [c for c in cols if c != own]
    rows.append({"Item": own, "Construct": f, "Std loading (λ)": r["Est. Std"], "Unstd loading": num(pd.Series([r["Estimate"]])).iloc[0],
                 "SE": num(pd.Series([r["Std. Err"]])).iloc[0], "t / z": num(pd.Series([r["z-value"]])).iloc[0], "p": num(pd.Series([r["p-value"]])).iloc[0],
                 "Sig.": stars(num(pd.Series([r["p-value"]])).iloc[0]) if str(r["p-value"]) != "-" else "fixed", "λ²": r["Est. Std"] ** 2, "Error var (1−λ²)": 1 - r["Est. Std"] ** 2,
                 "Item-total r (corrected)": X[own].corr(X[rest].sum(axis=1)),
                 "Alpha if deleted": len(rest) / (len(rest) - 1) * (1 - X[rest].var().sum() / X[rest].sum(axis=1).var()) if len(rest) > 1 else np.nan})
LD = pd.DataFrame(rows).set_index("Item")
table(LD, "T08_item_loadings", "Table 8. Measurement model: item loadings and coefficients (CFA)")
phi = pd.DataFrame(np.eye(len(FAC)), index=list(FAC), columns=list(FAC))
for _, r in ins[(ins.op == "~~") & (ins.lval.isin(FAC)) & (ins.rval.isin(FAC)) & (ins.lval != ins.rval)].iterrows():
    phi.loc[r.lval, r.rval] = phi.loc[r.rval, r.lval] = float(r["Est. Std"])
rel = {}
for f, k in FAC.items():
    l = LD[LD.Construct == f]["Std loading (λ)"].values; cols = [f"{f}{j}" for j in range(1, k + 1)]
    ave = (l ** 2).mean(); cr = l.sum() ** 2 / (l.sum() ** 2 + (1 - l ** 2).sum()); others = [o for o in FAC if o != f]
    msv = (phi.loc[f, others] ** 2).max(); asv = (phi.loc[f, others] ** 2).mean()
    rel[f] = {"Items": k, "Min λ": l.min(), "Max λ": l.max(), "Cronbach α": k / (k - 1) * (1 - X[cols].var().sum() / X[cols].sum(axis=1).var()),
              "CR (rho_c)": cr, "AVE": ave, "√AVE": np.sqrt(ave), "MSV": msv, "ASV": asv,
              "Convergent (CR>.7, AVE>.5)": "Yes" if cr > .7 and ave >= .5 else "Borderline" if cr > .7 and ave > .45 else "No",
              "Discriminant (AVE>MSV)": "Yes" if ave > msv else "No"}
REL = pd.DataFrame(rel).T
table(REL, "T09_reliability_validity", "Table 9. Reliability and convergent validity (α, CR, AVE, MSV, ASV)")
FL = phi.round(3).astype(object).copy()
for f in FAC: FL.loc[f, f] = f"{REL.loc[f, '√AVE']:.3f}"
for i, a in enumerate(FAC):
    for j, b_ in enumerate(FAC):
        if j > i: FL.loc[a, b_] = ""
table(FL, "T10_fornell_larcker", "Table 10. Fornell–Larcker criterion (diagonal = √AVE; below = latent correlations)")
C = X.corr().abs()
def block(a, b_): return C.loc[[f"{a}{j}" for j in range(1, FAC[a] + 1)], [f"{b_}{j}" for j in range(1, FAC[b_] + 1)]].values
def mono(a):
    m = block(a, a); return m[np.triu_indices(len(m), 1)]
def htmt(a, b_): return block(a, b_).mean() / np.sqrt(mono(a).mean() * mono(b_).mean())
def htmt2(a, b_): gm = lambda v: np.exp(np.log(v).mean()); return gm(block(a, b_).ravel()) / np.sqrt(gm(mono(a)) * gm(mono(b_)))
H1 = pd.DataFrame({b_: {a: htmt(a, b_) if a != b_ else np.nan for a in FAC} for b_ in FAC})
H2 = pd.DataFrame({b_: {a: htmt2(a, b_) if a != b_ else np.nan for a in FAC} for b_ in FAC})
table(H1, "T11_HTMT", "Table 11. HTMT ratio (threshold < 0.85 strict / 0.90 liberal)", heat=True)
table(H2, "T12_HTMT2", "Table 12. HTMT2 ratio (geometric-mean version; threshold < 0.85 / 0.90)", heat=True)
cl = pd.DataFrame({f: {i: (X[i].corr(X[[c for c in X.columns if c.startswith(f) and c != i]].mean(axis=1)) if i.startswith(f) else X[i].corr(comp[f])) for i in ITEMS} for f in FAC})
table(cl, "T13_cross_loadings", "Table 13. Item–construct correlations (own item removed from own construct)", heat=True)
R["rel"] = {f: {k: (float(v) if not isinstance(v, str) else v) for k, v in d.items()} for f, d in REL.T.to_dict().items()}
R["htmt_max"] = float(np.nanmax(H1.values)); R["htmt2_max"] = float(np.nanmax(H2.values)); R["latcorr"] = phi.round(3).to_dict()
# نمودارها
fig, ax = plt.subplots(1, 3, figsize=(17, 4.6))
w = .26; xs = np.arange(len(FAC))
for k, (col, c) in enumerate([("Cronbach α", "#2f4b7c"), ("CR (rho_c)", "#a05195"), ("AVE", "#f95d6a")]): ax[0].bar(xs + (k - 1) * w, REL[col].astype(float), w, label=col, color=c)
ax[0].axhline(.7, ls="--", c="grey", lw=1); ax[0].axhline(.5, ls=":", c="grey", lw=1); ax[0].set_xticks(xs, list(FAC)); ax[0].set_ylim(0, 1); ax[0].legend(frameon=False); ax[0].set_title("Reliability and AVE")
for a_, M, t_ in [(ax[1], H1, "HTMT"), (ax[2], H2, "HTMT2")]:
    im = a_.imshow(M.values.astype(float), cmap="Blues", vmin=0, vmax=1); a_.set_xticks(range(len(FAC)), list(FAC)); a_.set_yticks(range(len(FAC)), list(FAC)); a_.set_title(t_)
    for i in range(len(FAC)):
        for j in range(len(FAC)):
            if i != j: a_.text(j, i, f"{M.values[i, j]:.2f}", ha="center", va="center", fontsize=9)
    a_.spines[:].set_visible(False)
fig.tight_layout(); savefig(fig, "fig02_reliability_validity")
fig, ax = plt.subplots(figsize=(7.5, 6.2)); im = ax.imshow(phi.values, cmap="RdBu_r", vmin=-1, vmax=1)
ax.set_xticks(range(5), list(FAC)); ax.set_yticks(range(5), list(FAC)); ax.spines[:].set_visible(False)
for i in range(5):
    for j in range(5): ax.text(j, i, f"{phi.values[i, j]:.2f}", ha="center", va="center", color="white" if abs(phi.values[i, j]) > .6 else "black")
ax.set_title("Latent correlations (CFA)", weight="bold"); fig.colorbar(im, shrink=.8); savefig(fig, "fig03_latent_correlations")

# %% [code]
# --- ۷) برازش مدل‌ها، سوگیری روش مشترک، هم‌خطی (VIF / 1/VIF / R²) ---
def srmr(m, data):
    sig = m.calc_sigma()[0]; names = m.vars["observed"]; Sx = data[names].cov().values; sd = np.sqrt(np.diag(Sx))
    res = (Sx - sig) / np.outer(sd, sd); tri = np.tril_indices(len(names)); return float(np.sqrt((res[tri] ** 2).mean()))
def fitstats(m, data):
    s = calc_stats(m).T["Value"]; g = lambda k: float(s[k]) if k in s.index else np.nan
    return {"chi2": g("chi2"), "df": g("DoF"), "p": g("chi2 p-value"), "chi2/df": g("chi2") / g("DoF"), "CFI": g("CFI"), "TLI": g("TLI"), "NFI": g("NFI"),
            "GFI": g("GFI"), "AGFI": g("AGFI"), "RMSEA": g("RMSEA"), "SRMR": srmr(m, data), "AIC": g("AIC"), "BIC": g("BIC"), "LogLik": g("LogLik")}
def row(ii, l, o, r):
    q = ii[(ii.lval == l) & (ii.op == o) & (ii.rval == r)].iloc[0]; g = lambda c: float(q[c]) if str(q[c]) not in ("-", "nan") else np.nan
    return dict(b=g("Estimate"), beta=g("Est. Std"), se=g("Std. Err"), z=g("z-value"), p=g("p-value"))
FIT = {"CFA (5-factor)": fitstats(cfa, X)}
one = Model("G =~ " + "+".join(ITEMS)); one.fit(X); FIT["One-factor (Harman)"] = fitstats(one, X)
try:
    clf = Model(CFA + "M =~ " + "+".join(ITEMS) + "\n" + "\n".join(f"M ~~ 0*{f}" for f in FAC) + "\n"); clf.fit(X); FIT["Common latent factor (CLF)"] = fitstats(clf, X)
    cci = clf.inspect(std_est=True); R["clf_var"] = float((num(cci[(cci.op == "~") & (cci.rval == "M")]["Est. Std"]) ** 2).mean() * 100)
except Exception as ex: print("CLF اجرا نشد:", ex); R["clf_var"] = np.nan
ev = np.sort(np.linalg.eigvalsh(X.corr().values))[::-1]; R["harman"] = float(ev[0] / ev.sum() * 100)
cmb = pd.DataFrame({"Value": [R["harman"], FIT["One-factor (Harman)"]["CFI"], R.get("clf_var", np.nan)],
                    "Criterion": ["< 50 %", "poor fit expected", "< 25 %"]},
                   index=["Harman first factor (% variance)", "One-factor model CFI", "CLF shared method variance (%)"])
table(cmb, "T14_common_method_bias", "Table 14. Common method bias diagnostics")
# VIF بیرونی (گویه‌ها) و درونی (پیش‌بینی‌های هر معادله)
vo = []
for f, k in FAC.items():
    cols = [f"{f}{j}" for j in range(1, k + 1)]; Xc = sm.add_constant(X[cols])
    for i, c in enumerate(cols, 1):
        v = variance_inflation_factor(Xc.values, i); vo.append(dict(Item=c, Construct=f, VIF=v, **{"1/VIF (Tolerance)": 1 / v}, R2=1 - 1 / v))
table(pd.DataFrame(vo).set_index("Item"), "T15_outer_VIF", "Table 15. Outer VIF of indicators (VIF, 1/VIF, R²)")
cz = z(comp); cz["INT"] = cz.FOMO * cz.AIU
cz["age"], cz["gender"], cz["exp"] = z(df.age.astype(float)).values, z((df.gender == MALE_CODE).astype(float)).values, z(df.exp.astype(float)).values
EQ = {"FOMO": ["SME", "AIU", "age", "gender"], "HRD": ["FOMO", "SME", "AIU", "INT", "exp"], "IDQ": ["HRD", "FOMO", "SME", "AIU", "exp"]}
vi, r2 = [], []
for y, xs_ in EQ.items():
    Xc = sm.add_constant(cz[xs_]); m_ = sm.OLS(cz[y], Xc).fit()
    for i, c in enumerate(xs_, 1):
        v = variance_inflation_factor(Xc.values, i); sub = [a for a in xs_ if a != c]
        f2 = (m_.rsquared - sm.OLS(cz[y], sm.add_constant(cz[sub])).fit().rsquared) / (1 - m_.rsquared)
        vi.append({"Equation": y, "Predictor": c, "VIF": v, "1/VIF (Tolerance)": 1 / v, "R² (predictor | others)": 1 - 1 / v, "f² (effect size)": f2})
    r2.append({"Endogenous": y, "R² (composite OLS)": m_.rsquared, "Adj. R²": m_.rsquared_adj, "F": m_.fvalue, "p (F)": m_.f_pvalue})
VI = pd.DataFrame(vi); table(VI.set_index(["Equation", "Predictor"]), "T16_inner_VIF_f2", "Table 16. Inner VIF, tolerance (1/VIF), R² and f² per predictor")
R["vif"] = {f"{a}|{b_}": float(v) for a, b_, v in zip(VI.Equation, VI.Predictor, VI.VIF)}

# %% [code]
# --- ۸) مدل ساختاری مکنون با تعامل پنهان ---
dfc = X - X.mean()
for i in range(1, 6): dfc[f"INT{i}"] = dfc[f"FOMO{i}"] * dfc[f"AIU{i}"]
dfc["age"], dfc["gender"], dfc["exp"] = cz["age"].values, cz["gender"].values, cz["exp"].values
MEAS = CFA + "INT =~ INT1+INT2+INT3+INT4+INT5\n"
ORTH = "SME ~~ AIU\nSME ~~ INT\nAIU ~~ INT\nFOMO ~~ INT\n"
M_FULL = MEAS + "FOMO ~ SME + AIU + age + gender\nHRD ~ FOMO + SME + AIU + INT + exp\nIDQ ~ HRD + FOMO + SME + AIU + exp\n" + ORTH
sem = Model(M_FULL); sem.fit(dfc); si = sem.inspect(std_est=True); FIT["Structural model (with latent interaction)"] = fitstats(sem, dfc)
fit_tab = pd.DataFrame(FIT).T
thr = pd.DataFrame([{"chi2": np.nan, "df": np.nan, "p": "> .05", "chi2/df": "< 3", "CFI": "≥ .95", "TLI": "≥ .95", "NFI": "≥ .90", "GFI": "≥ .90", "AGFI": "≥ .90",
                     "RMSEA": "≤ .06", "SRMR": "≤ .08", "AIC": "lower", "BIC": "lower", "LogLik": ""}], index=["Recommended threshold"])
table(pd.concat([thr, fit_tab]), "T17_model_fit", "Table 17. Model fit indices (CFA, structural model and alternatives)")
HYP = {"FOMO~SME": ("H1", "+"), "HRD~FOMO": ("H2", "+"), "HRD~SME": ("H3", "+"), "IDQ~HRD": ("H4", "−"), "HRD~INT": ("H6 (FOMO×AIU)", "−"), "IDQ~AIU": ("H8", "+")}
PATHS = [("FOMO", "SME"), ("HRD", "FOMO"), ("HRD", "SME"), ("IDQ", "HRD"), ("HRD", "INT"), ("IDQ", "AIU"),
         ("IDQ", "FOMO"), ("IDQ", "SME"), ("FOMO", "AIU"), ("HRD", "AIU"), ("FOMO", "age"), ("FOMO", "gender"), ("HRD", "exp"), ("IDQ", "exp")]
pr = []
for l, r_ in PATHS:
    d = row(si, l, "~", r_); h, sg = HYP.get(f"{l}~{r_}", ("control / extra", ""))
    ok_ = (d["p"] < .05) and ((sg == "+" and d["beta"] > 0) or (sg == "−" and d["beta"] < 0)) if sg else None
    pr.append({"Path": f"{r_} → {l}", "Hypothesis": h, "Expected": sg, "b": d["b"], "SE": d["se"], "t (z)": d["z"], "p": d["p"], "Sig.": stars(d["p"]), "β": d["beta"],
               "Decision": "" if ok_ is None else ("Supported" if ok_ else "Not supported")})
PT = pd.DataFrame(pr).set_index("Path"); table(PT, "T18_path_coefficients", "Table 18. Structural path coefficients (b, SE, t, p, β)")
R["paths"] = {f"{l}~{r_}": row(si, l, "~", r_) for l, r_ in PATHS}
rl = {}
for f in ("FOMO", "HRD", "IDQ"):
    q_ = si[(si.lval == f) & (si.op == "~~") & (si.rval == f)]; rl[f] = 1 - float(q_["Est. Std"].iloc[0])
R["r2_latent"] = rl
r2t = pd.DataFrame(r2).set_index("Endogenous"); r2t.insert(0, "R² (latent, SEM)", pd.Series(rl))
table(r2t, "T19_R2", "Table 19. Explained variance (R²) of endogenous constructs")

# %% [code]
# --- ۹) نمودار معادلات ساختاری: (الف) ضرایب استاندارد (ب) آماره t و ستارهٔ معناداری ---
POS = {"SME": (3.0, 5.0), "FOMO": (6.9, 5.0), "HRD": (10.8, 5.0), "IDQ": (14.9, 5.0), "AIU": (12.6, 1.2)}
NAME = {"SME": "Social Media\nExposure\n(SME)", "FOMO": "Fear of\nMissing Out\n(FOMO)", "HRD": "Herd\nBehavior\n(HRD)", "IDQ": "Investment\nDecision Quality\n(IDQ)", "AIU": "Accounting\nInformation Use\n(AIU)"}
BOX = {"SME": [(0.5, 7.0 - i * 1.35) for i in range(5)], "HRD": [(10.8 + (i - 2) * 1.05, 7.7) for i in range(5)], "IDQ": [(17.0, 7.0 - i * 1.35) for i in range(5)],
       "FOMO": [(6.9 + (i - 2.5) * 1.05, 2.3) for i in range(6)], "AIU": [(12.6 + (i - 2) * 1.05, -0.2) for i in range(5)]}
def arrow(ax, p, q_, lw=1.2, ls="-", rad=0, ms=10, c="black"):
    ax.add_patch(FancyArrowPatch(p, q_, arrowstyle="-|>", mutation_scale=ms, lw=lw, ls=ls, color=c, connectionstyle=f"arc3,rad={rad}", zorder=2))
def sem_diagram(mode, fname):
    fig, ax = plt.subplots(figsize=(16.5, 7.8)); ax.set_xlim(-.3, 17.8); ax.set_ylim(-.9, 8.4); ax.axis("off")
    for k, (x, y) in POS.items():
        ax.add_patch(Ellipse((x, y), 2.5, 1.7, fc="white", ec="black", lw=1.4, zorder=3)); ax.text(x, y, NAME[k], ha="center", va="center", fontsize=10.5, weight="bold", zorder=4)
        for i, (bx, by) in enumerate(BOX[k]):
            item = f"{k}{i + 1}"; ax.add_patch(Rectangle((bx - .48, by - .25), .96, .5, fc="#f3f3f3", ec="black", lw=1, zorder=3)); ax.text(bx, by, item, ha="center", va="center", fontsize=9, zorder=4)
            dx, dy = bx - x, by - y; d = np.hypot(dx, dy); r_ = 1 / np.sqrt((dx / d / 1.25) ** 2 + (dy / d / .85) ** 2)
            s = (x + dx / d * r_, y + dy / d * r_); e = (bx, by - (.27 if dy > 0 else -.27)) if abs(dy / d) > .5 else (bx - (.5 if dx > 0 else -.5), by)
            arrow(ax, s, e, lw=.9, ms=7, c="#333333")
            rr = LD.loc[item]; lab = f"{rr['Std loading (λ)']:.2f}" if mode == "std" else ("fixed" if rr["Sig."] == "fixed" else f"{rr['t / z']:.1f}{rr['Sig.'] if rr['Sig.'] != 'ns' else ''}")
            ax.text((s[0] + e[0]) / 2, (s[1] + e[1]) / 2, lab, fontsize=7.5, ha="center", va="center", bbox=dict(fc="white", ec="none", pad=.5), zorder=5)
    def lab(l, r_):
        d = R["paths"][f"{l}~{r_}"]; return f"{d['beta']:.2f}{stars(d['p']).replace('ns', '')}" if mode == "std" else f"t={d['z']:.2f}{stars(d['p']).replace('ns', '')}"
    box_ = dict(fc="white", ec="none", pad=.8)
    def put(x, y, tag, l, r_): ax.text(x, y, f"{tag}\n" + lab(l, r_), ha="center", va="bottom", fontsize=9.5, weight="bold", bbox=box_, zorder=5)
    arrow(ax, (4.35, 5), (5.55, 5), lw=2.2, ms=13); put(4.95, 5.15, "H1", "FOMO", "SME")
    arrow(ax, (8.25, 5), (9.45, 5), lw=2.2, ms=13); put(8.85, 5.15, "H2", "HRD", "FOMO")
    arrow(ax, (12.15, 5), (13.55, 5), lw=2.2, ms=13); put(12.85, 5.15, "H4", "IDQ", "HRD")
    arrow(ax, (3.3, 5.85), (10.5, 5.87), lw=2.2, ms=13, rad=-.28); put(6.9, 7.0, "H3", "HRD", "SME")
    arrow(ax, (13.3, 2.05), (14.6, 4.1), lw=2.2, ms=13); put(14.9, 2.6, "H8", "IDQ", "AIU")
    arrow(ax, (11.8, 1.9), (10.6, 4.3), lw=2.0, ms=12, ls=(0, (5, 3))); put(9.9, 0.9, "H6  (FOMO × AIU)", "HRD", "INT")
    ttl = "Estimated structural equation model — standardized coefficients (β)" if mode == "std" else "Estimated structural equation model — t-values with significance"
    ax.set_title(ttl, weight="bold", fontsize=13)
    ax.text(0, -.75, "*** p<.001   ** p<.01   * p<.05   (no star = not significant). Controls, product indicators and non-hypothesized direct paths (FOMO→IDQ, SME→IDQ) are in Table 18.", fontsize=8.5, color="#444")
    savefig(fig, fname)
sem_diagram("std", "fig04_SEM_standardized"); sem_diagram("t", "fig05_SEM_tvalues")

# %% [code]
# --- ۱۰) اثرهای غیرمستقیم، شرطی و میانجی‌گری تعدیل‌شده (خودگردان) ---
ins0 = sem.inspect()
sig_aiu = float(ins0[(ins0.lval == "AIU") & (ins0.op == "~~") & (ins0.rval == "AIU")]["Estimate"].iloc[0]) ** .5
def eff_std(ii):
    g = lambda l, r: float(ii[(ii.lval == l) & (ii.rval == r) & (ii.op == "~")]["Est. Std"].iloc[0])
    a, e_, c, bh, bf, bs = g("FOMO", "SME"), g("HRD", "FOMO"), g("HRD", "SME"), g("IDQ", "HRD"), g("IDQ", "FOMO"), g("IDQ", "SME")
    o = {"std_seq": a * e_ * bh, "std_SME_HRD_IDQ": c * bh, "std_SME_FOMO_IDQ": a * bf}
    o["std_ind_total"] = o["std_seq"] + o["std_SME_HRD_IDQ"] + o["std_SME_FOMO_IDQ"]; o["std_total"] = o["std_ind_total"] + bs; return o
def eff(ii, sdA):
    g = lambda l, r: float(ii[(ii.lval == l) & (ii.rval == r) & (ii.op == "~")]["Estimate"].iloc[0])
    a, e_, c = g("FOMO", "SME"), g("HRD", "FOMO"), g("HRD", "SME"); w, bh, bf, bs = g("HRD", "INT"), g("IDQ", "HRD"), g("IDQ", "FOMO"), g("IDQ", "SME"); o = {}
    for tag, k in [("low", -1), ("mean", 0), ("high", 1)]:
        sl = e_ + w * k * sdA
        o[f"ind_SME_FOMO_HRD_IDQ_{tag}"] = a * sl * bh; o[f"ind_SME_HRD_IDQ_{tag}"] = c * bh; o[f"ind_SME_FOMO_IDQ_{tag}"] = a * bf; o[f"slope_FOMO_HRD_{tag}"] = sl
    o["ind_total_mean"] = o["ind_SME_FOMO_HRD_IDQ_mean"] + o["ind_SME_HRD_IDQ_mean"] + o["ind_SME_FOMO_IDQ_mean"]
    o["total_effect_mean"] = o["ind_total_mean"] + bs; o["imm"] = a * w * bh; return o
point = {**eff(ins0, sig_aiu), **eff_std(si)}
def boot_once(seed):
    rs = np.random.default_rng(seed); bd = dfc.iloc[rs.integers(0, len(dfc), len(dfc))].reset_index(drop=True)
    try:
        mb = Model(M_FULL); mb.fit(bd); ib = mb.inspect()
        sb = float(ib[(ib.lval == "AIU") & (ib.op == "~~") & (ib.rval == "AIU")]["Estimate"].iloc[0]) ** .5
        return {**eff(ib, sb), **eff_std(mb.inspect(std_est=True))}
    except Exception: return None
print(f"اجرای {B} بازنمونه ... (با ۲ هستهٔ Colab حدود ده تا بیست دقیقه)")
bt = pd.DataFrame([r for r in Parallel(n_jobs=N_JOBS)(delayed(boot_once)(int(s)) for s in np.random.SeedSequence(SEED).generate_state(B)) if r])
R["boot_n"] = int(len(bt))
LAB = {"std_seq": "SME → FOMO → HRD → IDQ (sequential, std)", "std_SME_HRD_IDQ": "SME → HRD → IDQ (std)", "std_SME_FOMO_IDQ": "SME → FOMO → IDQ (std)",
       "std_ind_total": "Total indirect (std)", "std_total": "Total effect (std)", "imm": "Index of moderated mediation (unstd)",
       "ind_SME_FOMO_HRD_IDQ_low": "Sequential | AIU low (−1 SD)", "ind_SME_FOMO_HRD_IDQ_mean": "Sequential | AIU mean", "ind_SME_FOMO_HRD_IDQ_high": "Sequential | AIU high (+1 SD)",
       "slope_FOMO_HRD_low": "Slope FOMO→HRD | AIU low", "slope_FOMO_HRD_mean": "Slope FOMO→HRD | AIU mean", "slope_FOMO_HRD_high": "Slope FOMO→HRD | AIU high",
       "ind_total_mean": "Total indirect (unstd)", "total_effect_mean": "Total effect (unstd)"}
IE = pd.DataFrame([{"Effect": LAB.get(k, k), "Estimate": point[k], "Boot SE": bt[k].std(), "CI95 low": bt[k].quantile(.025), "CI95 high": bt[k].quantile(.975),
                    "Sig. (CI excludes 0)": "Yes ***" if bt[k].quantile(.025) * bt[k].quantile(.975) > 0 else "No"} for k in point]).set_index("Effect")
table(IE, "T20_indirect_conditional", f"Table 20. Indirect, conditional and moderated-mediation effects (bootstrap, B={R['boot_n']})")
R["indirect"] = {k: dict(est=float(point[k]), lo=float(bt[k].quantile(.025)), hi=float(bt[k].quantile(.975))) for k in point}
bt.describe().T.round(4).to_csv(f"{OUT}/bootstrap_summary.csv", encoding="utf-8-sig")
sel = ["std_seq", "std_SME_HRD_IDQ", "std_SME_FOMO_IDQ", "std_ind_total", "std_total"]
fig, ax = plt.subplots(1, 3, figsize=(17, 4.8), gridspec_kw={"width_ratios": [1.3, 1, 1]})
for i, k in enumerate(sel[::-1]):
    lo_, hi_ = bt[k].quantile([.025, .975]); ax[0].plot([lo_, hi_], [i, i], c="#2f4b7c", lw=3); ax[0].scatter(point[k], i, c="#d45087", zorder=3, s=55)
ax[0].axvline(0, c="grey", ls="--"); ax[0].set_yticks(range(len(sel)), [LAB[k].replace(" (std)", "") for k in sel[::-1]]); ax[0].set_title("Standardized indirect effects (95% bootstrap CI)")
for a_, k, t_ in [(ax[1], "std_seq", "Sequential indirect effect"), (ax[2], "imm", "Index of moderated mediation")]:
    a_.hist(bt[k], bins=40, color="#2f4b7c", alpha=.85, edgecolor="white"); a_.axvline(0, c="grey", ls="--"); a_.axvline(point[k], c="#d45087", lw=2)
    a_.axvspan(bt[k].quantile(.025), bt[k].quantile(.975), color="#ffa600", alpha=.2); a_.set_title(t_)
fig.tight_layout(); savefig(fig, "fig06_indirect_effects")

# %% [code]
# --- ۱۱) تعدیل‌گری: شیب‌های ساده و نمودار تعامل ---
mod = sm.OLS(cz.HRD, sm.add_constant(cz[EQ["HRD"]])).fit(cov_type="HC3")
ols = pd.DataFrame({"b": mod.params, "SE (HC3)": mod.bse, "t": mod.tvalues, "p": mod.pvalues}); ols["Sig."] = ols.p.map(stars)
table(ols, "T21_OLS_HRD_HC3", "Table 21. Robust (HC3) regression of HRD on composites (moderation check)")
ss = {}
for tag, k in [("AIU low (−1 SD)", -1), ("AIU mean", 0), ("AIU high (+1 SD)", 1)]:
    Xs = cz[EQ["HRD"]].copy(); Xs["AIU"] = cz.AIU - k; Xs["INT"] = cz.FOMO * (cz.AIU - k); m_ = sm.OLS(cz.HRD, sm.add_constant(Xs)).fit(cov_type="HC3")
    ss[tag] = dict(b=m_.params["FOMO"], SE=m_.bse["FOMO"], t=m_.tvalues["FOMO"], p=m_.pvalues["FOMO"], Sig=stars(m_.pvalues["FOMO"]),
                   **{"CI95 low": m_.conf_int().loc["FOMO", 0], "CI95 high": m_.conf_int().loc["FOMO", 1]})
SS = pd.DataFrame(ss).T; table(SS, "T22_simple_slopes", "Table 22. Simple slopes of FOMO → HRD at levels of AIU (composites, HC3)")
R["simple_slopes"] = {k: {a: (float(b_) if not isinstance(b_, str) else b_) for a, b_ in v.items()} for k, v in ss.items()}
fig, ax = plt.subplots(figsize=(7.4, 5)); xx = np.linspace(-2, 2, 50)
for (tag, v), c, ls in zip(ss.items(), ["#d45087", "#555555", "#2f4b7c"], ["-", "--", "-"]):
    ax.plot(xx, v["b"] * xx, c=c, ls=ls, lw=2.6, label=f"{tag}: slope = {v['b']:.2f}{v['Sig'] if v['Sig'] != 'ns' else ''}")
ax.set_xlabel("FOMO (standardized)"); ax.set_ylabel("Herd behavior (predicted, standardized)"); ax.legend(frameon=False); ax.set_title("Moderating role of accounting information use", weight="bold")
savefig(fig, "fig07_interaction")

# %% [code]
# --- ۱۲) مدل‌های رقیب و تحلیل حساسیت (DWLS، مرکزسازی باقی‌مانده، خطاهای همبسته، حذف پرت) ---
cand = {"M1": ("Proposed (partial mediation)", "FOMO ~ SME + age + gender\nHRD ~ FOMO + SME + exp\nIDQ ~ HRD + FOMO + SME + exp\n"),
        "M2": ("Full sequential mediation", "FOMO ~ SME + age + gender\nHRD ~ FOMO + exp\nIDQ ~ HRD + exp\n"),
        "M3": ("Reversed order (HRD → FOMO)", "HRD ~ SME + exp\nFOMO ~ HRD + SME + age + gender\nIDQ ~ FOMO + HRD + SME + exp\n"),
        "M4": ("Direct effect only (no mediators)", "FOMO ~ SME + age + gender\nHRD ~ SME + exp\nIDQ ~ SME + exp\n")}
cm_ = {}
for k, (nm, body) in cand.items():
    mm = Model(CFA + body + "AIU ~~ SME\nAIU ~~ FOMO\nAIU ~~ HRD\nAIU ~~ IDQ\n"); mm.fit(dfc); cm_[k] = {"Model": nm, **fitstats(mm, dfc)}
CM = pd.DataFrame(cm_).T.set_index("Model"); CM = CM.astype(float)
CM["Δχ² vs M1"] = CM["chi2"] - CM["chi2"].iloc[0]; CM["Δdf vs M1"] = CM["df"] - CM["df"].iloc[0]
CM["p(Δχ²)"] = [np.nan if d == 0 else float(stats.chi2.sf(abs(c), abs(d))) for c, d in zip(CM["Δχ² vs M1"], CM["Δdf vs M1"])]
CM["ΔBIC vs M1"] = CM["BIC"] - CM["BIC"].iloc[0]
table(CM[["chi2", "df", "CFI", "TLI", "RMSEA", "SRMR", "AIC", "BIC", "Δχ² vs M1", "Δdf vs M1", "p(Δχ²)", "ΔBIC vs M1"]], "T23_competing_models", "Table 23. Competing models")
R["models"] = CM.round(4).to_dict("index")
sens = {"Base model (ML)": (FIT["Structural model (with latent interaction)"], si, len(dfc))}
try:   # DWLS
    cols = ITEMS + ["age", "gender", "exp"]; md = Model(CFA + "FOMO ~ SME + AIU + age + gender\nHRD ~ FOMO + SME + AIU + exp\nIDQ ~ HRD + FOMO + SME + AIU + exp\n")
    md.fit(dfc[cols], obj="DWLS"); sens["DWLS (no interaction)"] = (fitstats(md, dfc[cols]), md.inspect(std_est=True), len(dfc))
except Exception as ex: print("DWLS اجرا نشد:", ex)
try:   # مرکزسازی باقی‌مانده
    dres = dfc.copy()
    for i in range(1, 6): dres[f"INT{i}"] = sm.OLS(dfc[f"INT{i}"], sm.add_constant(dfc[[f"FOMO{i}", f"AIU{i}"]])).fit().resid.values
    mr = Model(M_FULL); mr.fit(dres); sens["Residual-centering interaction"] = (fitstats(mr, dres), mr.inspect(std_est=True), len(dres))
except Exception as ex: print("مرکزسازی باقی‌مانده اجرا نشد:", ex)
try:   # آزادسازی ۴ بزرگ‌ترین خطای همبستهٔ درون‌سازه‌ای
    names = cfa.vars["observed"]; Sx = X[names].cov().values; res = (Sx - cfa.calc_sigma()[0]) / np.sqrt(np.outer(np.diag(Sx), np.diag(Sx)))
    pairs = sorted([(abs(res[i, j]), names[i], names[j]) for i in range(len(names)) for j in range(i) if names[i].rstrip("0123456789") == names[j].rstrip("0123456789")], reverse=True)[:4]
    R["freed_errors"] = [f"{a} ~~ {b_}" for _, a, b_ in pairs]
    mp = Model(M_FULL + "\n".join(f"{a} ~~ {b_}" for _, a, b_ in pairs) + "\n"); mp.fit(dfc); sens["Re-specified (4 correlated errors)"] = (fitstats(mp, dfc), mp.inspect(std_est=True), len(dfc))
except Exception as ex: print("بازمشخص‌سازی اجرا نشد:", ex)
try:   # حذف ۵٪ دورترین مشاهدات (فاصلهٔ ماهالانوبیس)
    keep = d2 < np.quantile(d2, .95); mo = Model(M_FULL); mo.fit(dfc[keep].reset_index(drop=True)); sens["Outliers removed (5% Mahalanobis)"] = (fitstats(mo, dfc[keep]), mo.inspect(std_est=True), int(keep.sum()))
except Exception as ex: print("حذف پرت اجرا نشد:", ex)
sr = []
for nm, (ft, ii, nn) in sens.items():
    def g(l, r_):
        try: d = row(ii, l, "~", r_); return f"{d['beta']:.3f}{stars(d['p']).replace('ns', '')}"
        except Exception: return "–"
    sr.append({"Specification": nm, "N": nn, "CFI": ft["CFI"], "RMSEA": ft["RMSEA"], "SRMR": ft["SRMR"], "FOMO → HRD (β)": g("HRD", "FOMO"), "HRD → IDQ (β)": g("IDQ", "HRD"), "SME → FOMO (β)": g("FOMO", "SME"), "FOMO×AIU → HRD (β)": g("HRD", "INT")})
SR = pd.DataFrame(sr).set_index("Specification"); table(SR, "T24_sensitivity", "Table 24. Sensitivity analysis: key standardized coefficients across specifications")
R["sensitivity"] = SR.to_dict("index")
fig, ax = plt.subplots(figsize=(10, 4.6)); xs = np.arange(len(SR)); w = .26
for k, (col, c) in enumerate([("SME → FOMO (β)", "#2f4b7c"), ("FOMO → HRD (β)", "#a05195"), ("HRD → IDQ (β)", "#f95d6a")]):
    ax.bar(xs + (k - 1) * w, [float(str(v).rstrip("*")) if v != "–" else np.nan for v in SR[col]], w, label=col.replace(" (β)", ""), color=c)
ax.axhline(0, c="k", lw=.8); ax.set_xticks(xs, [s.split(" (")[0] for s in SR.index], rotation=15); ax.set_ylabel("Standardized β"); ax.legend(frameon=False); ax.set_title("Stability of key paths across specifications", weight="bold")
savefig(fig, "fig08_sensitivity")

# %% [code]
# --- ۱۳) ذخیرهٔ همهٔ جدول‌ها و نتایج + دانلود ---
json.dump(R, open(f"{OUT}/results_paper1.json", "w"), ensure_ascii=False, indent=1, default=lambda o: None if isinstance(o, float) and np.isnan(o) else str(o))
with pd.ExcelWriter(f"{OUT}/paper1_all_tables.xlsx") as xw:
    for k, t_ in TABLES.items(): t_.to_excel(xw, sheet_name=k[:31])
shutil.make_archive("output_results", "zip", OUT)
print("جدول‌ها:", len(TABLES), "| نمودارها:", len([f for f in os.listdir(PNG) if f.startswith("fig")]), "| پوشهٔ", OUT)
try:
    from google.colab import files; files.download("output_results.zip")
except ImportError: pass
