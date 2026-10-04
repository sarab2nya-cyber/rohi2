# -*- coding: utf-8 -*-
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
        return dict(chi2=chi2, df=df, cfi=cfi, rmsea=rmsea, srmr=float(np.mean(srs)), npar=self.npar, x=r.x, ok=r.success)

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
