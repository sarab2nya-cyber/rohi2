# -*- coding: utf-8 -*-
"""Data-generation script (demonstration data with the structure of the questionnaire; use it to test the analysis code and replace it by the real survey CSV with the same column names)."""
import os, numpy as np, pandas as pd


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

SEED, N = 90417, 364
OUT = "."
z = lambda x: (x-x.mean())/x.std()

def simulate(seed=SEED, n=N):
    rng = np.random.default_rng(seed)
    rank = rng.choice(4, n, p=[.34, .30, .21, .15])                    # 0 assistant, 1 senior, 2 supervisor, 3 manager/partner
    emp = rng.choice(3, n, p=[.28, .50, .22])                         # 0 Audit Organization, 1 private institutes, 2 other
    exp = np.clip(np.where(rank == 0, rng.gamma(2.2, 1.0, n), rng.gamma(4.0, 2.2, n)) + rank, 0.5, 30).round().astype(int)
    age = np.clip(24 + 1.0*exp + rng.normal(0, 3.5, n), 22, 62).round().astype(int)
    gender = (rng.random(n) < .63).astype(int); edu = rng.choice(3, n, p=[.57, .36, .07]); cert = (rng.random(n) < .22 + .12*(rank >= 2)).astype(int)
    senior = (rank >= 2).astype(int)
    TBP = rng.normal(size=n); ECL = z(-.20*TBP + .98*rng.normal(size=n)); CON = z(.25*ECL + .10*senior + .96*rng.normal(size=n))
    tc = z(TBP*CON)
    MD = z(.42*TBP - .30*ECL - .20*CON - .24*tc + .76*rng.normal(size=n))
    bMD = np.where(senior == 1, .24, .52)
    mc = z(MD*CON)
    SIL = z(bMD*MD - .22*ECL - .14*CON - .36*mc + .06*TBP + .70*rng.normal(size=n))
    lat = dict(TBP=TBP, ECL=ECL, CON=CON, MD=MD, SIL=SIL)
    spec = dict(TBP=[.80,.77,.74,.69], ECL=[.81,.78,.75,.70], CON=[.80,.78,.74,.70], MD=[.80,.77,.75,.72,.68], SIL=[.81,.79,.76,.73,.68])
    items = gen_items(rng, lat, spec, cross=[("MD3","TBP",.12),("SIL2","ECL",.12),("CON4","ECL",.12),("TBP2","MD",.12),("MD5","CON",-.10)],
        resid_corr=[("TBP1","TBP2",.22),("ECL1","ECL2",.20),("CON1","CON2",.22),("MD1","MD2",.20),("SIL1","SIL2",.22),("MD4","MD5",.18)],
        method_sd=.15, loc=dict(TBP=.25, ECL=-.05, CON=.35, MD=-.35, SIL=-.20))
    d = pd.DataFrame(dict(rank=rank+1, emp=emp+1, exp=exp, age=age, gender=gender, edu=edu+1, cert=cert, senior=senior))
    return pd.concat([d, items], axis=1)


if __name__ == "__main__":
    df = simulate(); df.to_csv("eth_data.csv", index=False, encoding="utf-8-sig"); df.to_excel("eth_data.xlsx", index=False); print(df.shape)
