import pandas as pd, numpy as np, os, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from scipy import stats
here=os.path.dirname(__file__); df=pd.read_csv(os.path.join(here,"..","data","thesis_sample.csv")); F=os.path.join(here,"..","figures")
plt.rcParams.update({"font.size":10,"axes.spines.top":False,"axes.spines.right":False})
fig,ax=plt.subplots(1,2,figsize=(8.5,3.5),gridspec_kw={"width_ratios":[1.6,1]})
ax[0].hist(df.ROA,bins=18,color="#2b6cb0",edgecolor="w"); ax[0].set_title("Series: ROA  (Histogram, EViews-style)"); ax[0].set_xlabel("ROA")
s=df.ROA; txt="\n".join([f"Sample 1392 1401 (n=200)",f"Mean      {s.mean():.4f}",f"Median    {s.median():.4f}",f"Maximum   {s.max():.4f}",f"Minimum   {s.min():.4f}",f"Std. Dev. {s.std():.4f}",f"Skewness  {stats.skew(s):.4f}",f"Kurtosis  {stats.kurtosis(s,fisher=False):.4f}",f"Jarque-Bera {stats.jarque_bera(s)[0]:.4f}",f"Probability {stats.jarque_bera(s)[1]:.4f}"])
ax[1].axis("off"); ax[1].text(0,.95,txt,va="top",family="monospace",fontsize=9)
fig.tight_layout(); fig.savefig(os.path.join(F,"fig2_1_hist_roa.png"),dpi=160); plt.close()
fig,ax=plt.subplots(figsize=(6,3.6)); 
for f in range(1,21): d=df[df.firm==f]; ax.plot(d.year,d.ROA,lw=.8,alpha=.55,color="#718096")
ax.plot(sorted(df.year.unique()),df.groupby("year").ROA.mean(),color="#c53030",lw=2.4,label="mean of 20 firms"); ax.axvline(1398.5,ls=":",color="k"); ax.legend(fontsize=8)
ax.set_title("ROA of 20 firms, 1392-1401 (panel line graph)"); ax.set_xlabel("year"); fig.tight_layout(); fig.savefig(os.path.join(F,"fig2_2_roa_panel.png"),dpi=160); plt.close()
