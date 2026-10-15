# -*- coding: utf-8 -*-
"""Data-generation script (demonstration data with the structure of the questionnaire: 8 constructs, 34 items + 5 background variables).
Use it to test the analysis code; replace the CSV by the real survey data (same column names) before any substantive use."""
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

SEED, N = 52817, 336
OUT = "."
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


if __name__ == "__main__":
    df = simulate()
    df.to_csv("gov_data.csv", index=False, encoding="utf-8-sig"); df.to_excel("gov_data.xlsx", index=False)
    print(df.shape, "columns:", list(df.columns)[:8], "...")
