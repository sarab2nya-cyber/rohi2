# -*- coding: utf-8 -*-
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
