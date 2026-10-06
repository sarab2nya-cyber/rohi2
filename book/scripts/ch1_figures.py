import numpy as np, pandas as pd, os, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import statsmodels.api as sm
here=os.path.dirname(os.path.abspath(__file__)); F=os.path.join(here,"..","chapter1","figures")
plt.rcParams.update({"font.size":10,"axes.spines.top":False,"axes.spines.right":False})
# --- Anscombe's quartet (Anscombe 1973)
x123=[10,8,13,9,11,14,6,4,12,7,5]
y1=[8.04,6.95,7.58,8.81,8.33,9.96,7.24,4.26,10.84,4.82,5.68]
y2=[9.14,8.14,8.74,8.77,9.26,8.10,6.13,3.10,9.13,7.26,4.74]
y3=[7.46,6.77,12.74,7.11,7.81,8.84,6.08,5.39,8.15,6.42,5.73]
x4=[8,8,8,8,8,8,8,19,8,8,8]; y4=[6.58,5.76,7.71,8.84,8.47,7.04,5.25,12.50,5.56,7.91,6.89]
fig,ax=plt.subplots(2,2,figsize=(7,5.2),sharex=True,sharey=True)
for a,(x,y,t) in zip(ax.ravel(),[(x123,y1,"I"),(x123,y2,"II"),(x123,y3,"III"),(x4,y4,"IV")]):
    r=sm.OLS(y,sm.add_constant(x)).fit(); a.scatter(x,y,color="#2b6cb0"); xs=np.array([3,20]); a.plot(xs,r.params[0]+r.params[1]*xs,color="#c53030")
    a.set_title(f"Dataset {t}: y = {r.params[0]:.2f} + {r.params[1]:.2f}x,  R2 = {r.rsquared:.2f}",fontsize=9)
fig.tight_layout(); fig.savefig(os.path.join(F,"fig1_anscombe.png"),dpi=160); plt.close()
# --- sampling variation: 100 samples of 30 firms
rng=np.random.default_rng(7); b0,b1=0.20,-0.25
fig,ax=plt.subplots(figsize=(5.8,3.8)); bs=[]
xs=np.linspace(0.2,0.9,10)
for i in range(100):
    x=rng.uniform(0.2,0.9,30); y=b0+b1*x+rng.normal(0,0.04,30); r=sm.OLS(y,sm.add_constant(x)).fit(); bs.append(r.params[1])
    ax.plot(xs,r.params[0]+r.params[1]*xs,color="#90cdf4",lw=.8)
ax.plot(xs,b0+b1*xs,color="#c53030",lw=2.5,label="true line (unknown in practice)"); ax.set_xlabel("LEV"); ax.set_ylabel("ROA"); ax.legend(fontsize=8)
ax.set_title("100 samples of 30 firms -> 100 different OLS lines"); fig.tight_layout(); fig.savefig(os.path.join(F,"fig2_sampling.png"),dpi=160); plt.close()
print("sampling: mean b1 %.4f sd %.4f"%(np.mean(bs),np.std(bs)))
# --- omitted variable simulation (1000 samples, n=200)
rng=np.random.default_rng(11); naive=[];ctrl=[]
for i in range(1000):
    n=200; q=rng.normal(0,1,n)                      # management quality (unobserved/omitted)
    lev=0.55-0.04*q+rng.normal(0,0.08,n)            # better managers borrow less
    roa=0.05-0.10*lev+0.02*q+rng.normal(0,0.03,n)   # true effect of lev = -0.10
    naive.append(sm.OLS(roa,sm.add_constant(lev)).fit().params[1])
    ctrl.append(sm.OLS(roa,sm.add_constant(np.column_stack([lev,q]))).fit().params[1])
print("omitted var: naive mean %.4f ; with control mean %.4f ; true -0.10"%(np.mean(naive),np.mean(ctrl)))
fig,ax=plt.subplots(figsize=(5.8,3.4)); ax.hist(naive,bins=30,alpha=.8,color="#dd6b20",label="without quality (omitted)"); ax.hist(ctrl,bins=30,alpha=.8,color="#2b6cb0",label="with quality (controlled)"); ax.axvline(-0.10,color="k",ls="--"); ax.legend(fontsize=8); ax.set_xlabel("estimated effect of LEV on ROA (true = -0.10)")
ax.set_title("1000 simulated studies: omitting a key variable misses the truth"); fig.tight_layout(); fig.savefig(os.path.join(F,"fig3_omitted.png"),dpi=160); plt.close()
# --- 5 firm hand example
x=np.array([30,40,50,60,70]);y=np.array([12,10,9,6,3]); r=sm.OLS(y,sm.add_constant(x)).fit()
print(r.params,r.rsquared,r.bse,r.tvalues,r.resid,(r.resid**2).sum())
fig,ax=plt.subplots(figsize=(5.2,3.6)); ax.scatter(x,y,color="#2b6cb0",zorder=3); xs=np.array([25,75]); ax.plot(xs,r.params[0]+r.params[1]*xs,color="#c53030")
for xi,yi,fi in zip(x,y,r.fittedvalues): ax.vlines(xi,fi,yi,color="#2f855a",lw=2)
ax.axhline(y.mean(),color="gray",ls=":"); ax.set_xlabel("debt ratio (%)"); ax.set_ylabel("ROA (%)"); ax.set_title("5 firms: line, residuals (green), mean of Y (dotted)"); fig.tight_layout(); fig.savefig(os.path.join(F,"fig4_five_firms.png"),dpi=160); plt.close()
# --- Galton-style regression to the mean in ROA
rng=np.random.default_rng(3); n=300; ability=rng.normal(0,1,n); r1=0.06+0.03*ability+rng.normal(0,0.03,n); r2=0.06+0.03*ability+rng.normal(0,0.03,n)
r=sm.OLS(r2,sm.add_constant(r1)).fit(); print("persistence slope",r.params[1])
fig,ax=plt.subplots(figsize=(5.2,3.8)); ax.scatter(r1*100,r2*100,s=10,alpha=.5,color="#2b6cb0"); lo,hi=r1.min()*100,r1.max()*100; ax.plot([lo,hi],[lo,hi],color="gray",ls="--",label="45-degree line (no change)"); xs=np.array([lo,hi]); ax.plot(xs,(r.params[0]+r.params[1]*xs/100)*100,color="#c53030",label=f"regression line (slope {r.params[1]:.2f})")
ax.set_xlabel("ROA this year (%)"); ax.set_ylabel("ROA next year (%)"); ax.legend(fontsize=8); ax.set_title("Regression to the mean"); fig.tight_layout(); fig.savefig(os.path.join(F,"fig5_mean_reversion.png"),dpi=160); plt.close()
