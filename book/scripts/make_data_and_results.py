"""Simulated 20 firms x 10 years dataset (1392-1401) + every number quoted in the book.
Run: python3 make_data_and_results.py  -> writes ../data/thesis_sample.csv, ../data/results.txt, ../figures/*.png"""
import numpy as np, pandas as pd, statsmodels.api as sm, statsmodels.formula.api as smf
import statsmodels.stats.api as sms
from statsmodels.stats.outliers_influence import OLSInfluence
from statsmodels.stats.diagnostic import linear_reset, acorr_breusch_godfrey, het_white, het_breuschpagan
from statsmodels.stats.stattools import jarque_bera, durbin_watson
from statsmodels.stats.diagnostic import breaks_cusumolsresid
from scipy import stats
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt, os
rng = np.random.default_rng(1402)
here = os.path.dirname(__file__); D = os.path.join(here, "..", "data"); F = os.path.join(here, "..", "figures")
inds = ["Auto","Pharma","Food","Metal","Chem"]
rows=[]
for i in range(20):
    ind = inds[i%5]; fe = rng.normal(0,0.012)
    size0 = rng.normal(14.2,1.0)           # ln(total assets, million rials)
    lev0 = rng.uniform(0.35,0.75)
    for t,yr in enumerate(range(1392,1402)):
        size = size0 + 0.07*t + rng.normal(0,0.08)
        lev  = np.clip(lev0 + rng.normal(0,0.04),0.15,0.92)
        growth = rng.normal(0.18,0.15)
        cfo = np.clip(rng.normal(0.10,0.06),-0.1,0.35)
        covid = 1 if yr>=1399 else 0
        sd = 0.025*np.exp(0.25*(size-14.2))
        roa = (-0.14+0.016*size-0.10*lev+0.035*growth+0.30*cfo - 0.06*lev*covid + 0.0*covid + fe + rng.normal(0,sd))
        rows.append(dict(firm=i+1,industry=ind,year=yr,ROA=roa,SIZE=size,LEV=lev,GROWTH=growth,CFO=cfo,COVID=covid))
df=pd.DataFrame(rows)
df["ASSETS"]=np.exp(df.SIZE)           # million rials
df["SALES"]=df.ASSETS*np.exp(rng.normal(-0.1,0.25,len(df)))
df["LN_SALES"]=np.log(df.SALES)
df["LEV_COVID"]=df.LEV*df.COVID
df["ROA_LAG"]=df.groupby("firm").ROA.shift(1)
df.round(5).to_csv(os.path.join(D,"thesis_sample.csv"),index=False)
out=[]
def P(*a): out.append(" ".join(str(x) for x in a))
P("N=",len(df)); P(df[["ROA","SIZE","LEV","GROWTH","CFO"]].describe().T.round(4).to_string())
for c in ["ROA","SIZE","LEV","GROWTH","CFO"]:
    P(c,"skew",round(stats.skew(df[c]),3),"kurt",round(stats.kurtosis(df[c],fisher=False),3),"JB p",round(stats.jarque_bera(df[c])[1],4))
f="ROA ~ SIZE + LEV + GROWTH + CFO"
m=smf.ols(f,df).fit(); P("\n=== OLS ===\n",m.summary().as_text())
P("AIC",m.aic,"BIC",m.bic,"llf",m.llf,"DW",durbin_watson(m.resid))
n=m.nobs; k=int(m.df_model)
# SIC/AIC EViews style (per obs)
P("EViews AIC",(-2*m.llf+2*(k+1))/n,"SIC",(-2*m.llf+np.log(n)*(k+1))/n,"HQ",(-2*m.llf+2*np.log(np.log(n))*(k+1))/n)
P("S.E. of regression",np.sqrt(m.scale),"SSR",m.ssr,"Mean dep",df.ROA.mean(),"SD dep",df.ROA.std())
# standardized beta
sb={v:m.params[v]*df[v].std()/df.ROA.std() for v in ["SIZE","LEV","GROWTH","CFO"]}; P("std beta",sb)
# RESET
for p in [2,3]:
    r=linear_reset(m,power=p,test_type="fitted",use_f=True); P("RESET power",p,r.fvalue,r.pvalue)
r=linear_reset(m,power=3,test_type="fitted",use_f=True)
# BP & White
bp=het_breuschpagan(m.resid,m.model.exog); P("BP LM,p,F,pF",bp)
wh=het_white(m.resid,m.model.exog); P("White LM,p,F,pF",wh)
# Harvey/Glejser quick
# robust
mr=smf.ols(f,df).fit(cov_type="HC1"); P("\n=== HC1 ===\n",mr.summary().as_text())
P(pd.DataFrame({"coef":m.params,"se_ols":m.bse,"t_ols":m.tvalues,"se_hc1":mr.bse,"t_hc1":mr.tvalues,"p_hc1":mr.pvalues}).round(4).to_string())
# WLS-type fix: log ROA not possible (neg). GLS weights
w=1/np.exp(0.25*(df.SIZE-14.2))**2
mw=smf.wls(f,df,weights=w).fit(); P("WLS\n",pd.DataFrame({"coef":mw.params,"se":mw.bse,"t":mw.tvalues}).round(4).to_string())
# BG
for L in [1,2,3]:
    b=acorr_breusch_godfrey(m,nlags=L); P("BG lag",L,b)
# panel-aware: cluster
mc=smf.ols(f,df).fit(cov_type="cluster",cov_kwds={"groups":df.firm}); P("cluster\n",pd.DataFrame({"se":mc.bse,"t":mc.tvalues,"p":mc.pvalues}).round(4).to_string())
mhac=smf.ols(f,df).fit(cov_type="HAC",cov_kwds={"maxlags":2}); P("HAC\n",pd.DataFrame({"se":mhac.bse,"t":mhac.tvalues,"p":mhac.pvalues}).round(4).to_string())
# JB
jb=jarque_bera(m.resid); P("JB",jb)
infl=OLSInfluence(m); sr=infl.resid_studentized_external; P("outliers |r|>3:",int((abs(sr)>3).sum()),"max",abs(sr).max(), "|r|>2.5:",int((abs(sr)>2.5).sum()))
# VIF centered
X=df[["SIZE","LEV","GROWTH","CFO"]]
for v in X:
    others=sm.add_constant(X.drop(columns=v)); r2=sm.OLS(X[v],others).fit().rsquared; P("VIF",v,round(1/(1-r2),3),"tol",round(1-r2,3))
P("corr\n",df[["ROA","SIZE","LEV","GROWTH","CFO"]].corr().round(3).to_string())
# Chow by year split (>=1399) via interaction F
fi="ROA ~ (SIZE + LEV + GROWTH + CFO)*COVID"
mi=smf.ols(fi,df).fit(); 
rest=[c for c in mi.params.index if ":" in c or c=="COVID"]
ft=mi.f_test(", ".join(f"{c}=0" for c in rest)); P("Chow(split 1399) F",ft.fvalue,"p",ft.pvalue,"df",ft.df_num,ft.df_denom)
# Chow at 1397
df["D97"]=(df.year>=1397).astype(int)
mi2=smf.ols("ROA ~ (SIZE + LEV + GROWTH + CFO)*D97",df).fit(); rest2=[c for c in mi2.params.index if ":" in c or c=="D97"]
ft2=mi2.f_test(", ".join(f"{c}=0" for c in rest2)); P("Chow(split 1397) F",ft2.fvalue,"p",ft2.pvalue)
# CUSUM
cs=breaks_cusumolsresid(m.resid,ddof=int(k+1)); P("CUSUM-OLS stat/p",cs[:2])
# recursive-ish plots after sorting by year
ds=df.sort_values(["year","firm"]).reset_index(drop=True)
ms=smf.ols(f,ds).fit()
# interaction model & robust
mm=smf.ols("ROA ~ SIZE + LEV + GROWTH + CFO + COVID + LEV_COVID",df).fit(cov_type="HC1"); P("\n=== with COVID & interaction (HC1) ===\n",mm.summary().as_text())
# dummy & industry/year controls
mfe=smf.ols("ROA ~ SIZE + LEV + GROWTH + CFO + C(industry) + C(year)",df).fit(cov_type="HC1")
P("with controls:\n",pd.DataFrame({"coef":mfe.params,"se":mfe.bse,"p":mfe.pvalues}).round(4).head(8).to_string(),"\nR2",mfe.rsquared,mfe.rsquared_adj)
# endogeneity quick: lagged regressors
df["SIZE_L"]=df.groupby("firm").SIZE.shift(1); df["LEV_L"]=df.groupby("firm").LEV.shift(1); df["GROWTH_L"]=df.groupby("firm").GROWTH.shift(1); df["CFO_L"]=df.groupby("firm").CFO.shift(1)
ml=smf.ols("ROA ~ SIZE_L + LEV_L + GROWTH_L + CFO_L",df.dropna()).fit(cov_type="HC1"); P("lagged X:\n",pd.DataFrame({"coef":ml.params,"se":ml.bse,"p":ml.pvalues}).round(4).to_string(),"R2adj",ml.rsquared_adj,"n",ml.nobs)
# log-log elasticity example
df["LN_ROA_SALES"]=np.log(df.SALES); 
ml2=smf.ols("LN_SALES ~ SIZE",df).fit(); P("loglog LN_SALES~SIZE\n",ml2.params.round(4).to_string())
df["LN_ASSETS"]=df.SIZE
ml3=smf.ols("LN_SALES ~ LN_ASSETS",df).fit(); P("ln-ln",ml3.params.round(4).to_dict(),ml3.rsquared)
# through the origin
mo=smf.ols("ROA ~ 0 + SIZE + LEV + GROWTH + CFO",df).fit(); P("origin R2 (uncentered)",mo.rsquared,"coefs",mo.params.round(4).to_dict(),"mean resid",mo.resid.mean())
# simple regression for Ch1 figures + 8-firm numeric example
simp=smf.ols("ROA ~ LEV",df).fit(); P("simple ROA~LEV",simp.params.round(4).to_dict(),simp.rsquared,simp.tvalues.round(3).to_dict(), "corr",df.ROA.corr(df.LEV))
sub=df[(df.year==1401)].head(8)[["firm","ROA","LEV","SIZE","GROWTH","CFO"]]; P("8 firms 1401\n",sub.round(4).to_string())
s8=smf.ols("ROA ~ LEV",sub).fit(); P("8-firm simple",s8.params.round(4).to_dict(),s8.rsquared)
# dummy example: industry Pharma vs rest
md=smf.ols("ROA ~ SIZE + LEV + GROWTH + CFO + C(industry, Treatment('Auto'))",df).fit(cov_type="HC1"); P("industry dummy\n",pd.DataFrame({"coef":md.params,"p":md.pvalues}).round(4).to_string())
# interaction SIZExLEV
mx=smf.ols("ROA ~ SIZE + LEV + SIZE:LEV + GROWTH + CFO",df).fit(cov_type="HC1"); P("SIZE*LEV\n",pd.DataFrame({"coef":mx.params,"se":mx.bse,"p":mx.pvalues}).round(4).to_string())
# AR(1) (Cochrane-Orcutt style on pooled data sorted by firm-year)
P("rho of residuals within firm:",np.corrcoef(m.resid[:-1],m.resid[1:])[0,1])
open(os.path.join(D,"results.txt"),"w").write("\n".join(out))
# ---------- figures ----------
plt.rcParams.update({"font.size":10,"axes.spines.top":False,"axes.spines.right":False})
fig,ax=plt.subplots(figsize=(5.5,3.8)); ax.scatter(df.LEV,df.ROA,s=12,alpha=.6,color="#2b6cb0"); xs=np.linspace(df.LEV.min(),df.LEV.max(),50); ax.plot(xs,simp.params["Intercept"]+simp.params["LEV"]*xs,color="#c53030",lw=2)
ax.set_xlabel("LEV (debt ratio)"); ax.set_ylabel("ROA"); ax.set_title("Fig 1-1: simple regression ROA on LEV (200 firm-years)"); fig.tight_layout(); fig.savefig(os.path.join(F,"fig1_1_scatter.png"),dpi=160); plt.close()
fig,ax=plt.subplots(figsize=(5.5,3.8)); ax.scatter(df.LEV,df.ROA,s=10,alpha=.35,color="#718096"); ax.plot(xs,simp.params["Intercept"]+simp.params["LEV"]*xs,color="#c53030"); 
i=df.index[5]; ax.vlines(df.LEV[i],simp.params["Intercept"]+simp.params["LEV"]*df.LEV[i],df.ROA[i],color="#2f855a",lw=2); ax.scatter([df.LEV[i]],[df.ROA[i]],color="#2f855a",zorder=3)
ax.set_title("Fig 1-2: residual e = Y - Yhat (green line); OLS minimizes sum e^2"); ax.set_xlabel("LEV"); ax.set_ylabel("ROA"); fig.tight_layout(); fig.savefig(os.path.join(F,"fig1_2_ols_residual.png"),dpi=160); plt.close()
fig,ax=plt.subplots(1,2,figsize=(8,3.4)); ax[0].scatter(m.fittedvalues,m.resid,s=10,alpha=.6,color="#2b6cb0"); ax[0].axhline(0,color="k",lw=.8); ax[0].set_title("Residuals vs fitted (funnel = heteroskedasticity)"); ax[0].set_xlabel("Fitted"); ax[0].set_ylabel("Residual")
ax[1].hist(m.resid,bins=25,color="#2b6cb0",edgecolor="w"); ax[1].set_title("Residual histogram (Jarque-Bera)"); fig.tight_layout(); fig.savefig(os.path.join(F,"fig3_1_resid.png"),dpi=160); plt.close()
# CUSUM plot on year-sorted data
from statsmodels.stats.diagnostic import recursive_olsresiduals
Xs=sm.add_constant(ds[["SIZE","LEV","GROWTH","CFO"]]); rr=recursive_olsresiduals(sm.OLS(ds.ROA,Xs).fit(),alpha=0.95)
cus=rr[5][1:]; ci=rr[6]; 
fig,ax=plt.subplots(figsize=(5.5,3.6)); ax.plot(cus,color="#2b6cb0",label="CUSUM"); ax.plot(ci[0],color="#c53030",ls="--",label="5% band"); ax.plot(ci[1],color="#c53030",ls="--"); ax.set_title("Fig 3-2: CUSUM (recursive residuals, data sorted by year)"); ax.set_xlabel("observation"); ax.legend(fontsize=8); fig.tight_layout(); fig.savefig(os.path.join(F,"fig3_2_cusum.png"),dpi=160); plt.close()
out_=bool(((cus>ci[1])|(cus<ci[0])).any()) if False else bool(((cus>ci[1])|(cus<ci[0])).any())
P2=f"CUSUM recursive: outside band = {out_}; max|cus|={abs(cus).max():.2f}"; open(os.path.join(D,"results.txt"),"a").write("\n"+P2)
from statsmodels.graphics.gofplots import qqplot
fig=qqplot(m.resid,line="s"); fig.set_size_inches(4.5,3.6); plt.title("Q-Q plot of residuals"); plt.tight_layout(); plt.savefig(os.path.join(F,"fig3_3_qq.png"),dpi=160); plt.close()
# data types figure
fig,ax=plt.subplots(1,3,figsize=(9,2.8))
ax[0].bar(["F1","F2","F3","F4","F5"],df[df.year==1401].ROA.head(5)); ax[0].set_title("Cross-section: 5 firms, 1401")
y=df[df.firm==1]; ax[1].plot(y.year,y.ROA,marker="o"); ax[1].set_title("Time series: firm 1, 1392-1401")
for fm in range(1,4): y=df[df.firm==fm]; ax[2].plot(y.year,y.ROA,marker=".",label=f"F{fm}")
ax[2].set_title("Panel: 3 firms x 10 yrs"); ax[2].legend(fontsize=7); fig.tight_layout(); fig.savefig(os.path.join(F,"fig1_3_datatypes.png"),dpi=160); plt.close()
print("\n".join(out)[:200]); print(P2)
