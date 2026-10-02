#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simulated survey data for testing ``pls_sem_analysis.py``
=========================================================

Generates 200 respondents with exactly the questionnaire's variables:

    Gender  Age  Degree  Experience  Q1..Q13  Z1..Z24

The data follow a known population model, so the analysis output can be
checked against the true values (written to the sheet ``True_population_model``):

* six latent constructs: CA (Q1-Q9), FM (Q10-Q13), ORG (Z1-Z7), LEG (Z8-Z13),
  PRO (Z14-Z20), POL (Z21-Z24);
* standardised structural model  CA, FM -> ORG, LEG, PRO, POL  (H1-H8);
* reflective indicators with loadings 0.76-0.88 on a continuous scale,
  converted to a 1-5 Likert scale with realistic, slightly negatively skewed
  thresholds;
* demographic variables with plausible distributions (experience is
  consistent with age).

Usage:
    python simulate_data.py                       # writes simulated_data_200.xlsx
    python simulate_data.py my_file.xlsx 200 42   # file name, sample size, seed
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

N = int(sys.argv[2]) if len(sys.argv) > 2 else 200
SEED = int(sys.argv[3]) if len(sys.argv) > 3 else 2024
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent / "simulated_data_200.xlsx"

ITEMS = {
    "CA": [f"Q{i}" for i in range(1, 10)],
    "FM": [f"Q{i}" for i in range(10, 14)],
    "ORG": [f"Z{i}" for i in range(1, 8)],
    "LEG": [f"Z{i}" for i in range(8, 14)],
    "PRO": [f"Z{i}" for i in range(14, 21)],
    "POL": [f"Z{i}" for i in range(21, 25)],
}

# True standardised structural model
CORR_CA_FM = 0.50
PATHS = {  # (source, target): beta
    ("CA", "ORG"): 0.30, ("CA", "LEG"): 0.25, ("CA", "PRO"): 0.50, ("CA", "POL"): 0.20,
    ("FM", "ORG"): 0.40, ("FM", "LEG"): 0.35, ("FM", "PRO"): 0.20, ("FM", "POL"): 0.45,
}
HYP = {("CA", "ORG"): "H1", ("CA", "LEG"): "H2", ("CA", "PRO"): "H3", ("CA", "POL"): "H4",
       ("FM", "ORG"): "H5", ("FM", "LEG"): "H6", ("FM", "PRO"): "H7", ("FM", "POL"): "H8"}

# Likert thresholds on the continuous (standard normal) response scale
THRESHOLDS = np.array([-1.75, -0.95, -0.05, 0.95])


def main() -> None:
    rng = np.random.default_rng(SEED)

    # exogenous constructs
    cov = np.array([[1.0, CORR_CA_FM], [CORR_CA_FM, 1.0]])
    exo = rng.multivariate_normal([0, 0], cov, size=N)
    eta = {"CA": exo[:, 0], "FM": exo[:, 1]}

    # endogenous constructs with unit total variance
    r2 = {}
    for t in ("ORG", "LEG", "PRO", "POL"):
        b1, b2 = PATHS[("CA", t)], PATHS[("FM", t)]
        explained = b1 ** 2 + b2 ** 2 + 2 * b1 * b2 * CORR_CA_FM
        r2[t] = explained
        eta[t] = b1 * eta["CA"] + b2 * eta["FM"] + np.sqrt(1 - explained) * rng.standard_normal(N)

    # indicators
    data, loadings = {}, []
    for c, items in ITEMS.items():
        for it in items:
            lam = rng.uniform(0.76, 0.88)
            shift = rng.normal(0, 0.12)  # small item-specific difficulty
            ystar = lam * eta[c] + np.sqrt(1 - lam ** 2) * rng.standard_normal(N)
            data[it] = 1 + np.searchsorted(THRESHOLDS + shift, ystar)
            loadings.append([c, it, round(lam, 3)])

    # demographics
    gender = rng.choice([1, 2], size=N, p=[0.64, 0.36])
    age = rng.choice([1, 2, 3, 4], size=N, p=[0.10, 0.24, 0.31, 0.35])
    degree = rng.choice([1, 2, 3, 4], size=N, p=[0.04, 0.10, 0.50, 0.36])
    exp_probs = {1: [0.85, 0.15, 0.00, 0.00], 2: [0.45, 0.50, 0.05, 0.00],
                 3: [0.15, 0.45, 0.35, 0.05], 4: [0.05, 0.20, 0.35, 0.40]}
    experience = np.array([rng.choice([1, 2, 3, 4], p=exp_probs[a]) for a in age])

    df = pd.DataFrame({"Gender": gender, "Age": age, "Degree": degree, "Experience": experience})
    for c, items in ITEMS.items():
        for it in items:
            df[it] = data[it].astype(int)
    order = ["Gender", "Age", "Degree", "Experience"] + [f"Q{i}" for i in range(1, 14)] + \
            [f"Z{i}" for i in range(1, 25)]
    df = df[order]

    truth_paths = pd.DataFrame([[HYP[k], f"{k[0]} -> {k[1]}", v] for k, v in PATHS.items()],
                               columns=["Hypothesis", "Path", "True_beta"])
    truth_r2 = pd.DataFrame([[t, round(v, 4)] for t, v in r2.items()], columns=["Construct", "True_R2"])
    truth_load = pd.DataFrame(loadings, columns=["Construct", "Item", "True_loading_(continuous_scale)"])
    notes = pd.DataFrame({"Note": [
        f"Simulated data: N = {N}, random seed = {SEED}.",
        f"Exogenous constructs CA and FM correlate {CORR_CA_FM}.",
        "Continuous responses are cut at thresholds -1.75, -0.95, -0.05, 0.95 (plus a small item shift) "
        "to obtain 1-5 Likert codes; categorisation attenuates loadings and paths slightly.",
        "Demographic codes: Gender 1=Male 2=Female; Age 1=20-25 2=26-30 3=31-35 4=>35; "
        "Degree 1=diploma or lower 2=associate 3=bachelor 4=master+; Experience 1=<5 2=6-10 3=11-15 4=>15.",
        "Use only for testing the analysis code - never as research data."]})

    with pd.ExcelWriter(OUT, engine="openpyxl") as xw:
        df.to_excel(xw, sheet_name="Data", index=False)
        truth_paths.to_excel(xw, sheet_name="True_population_model", index=False)
        truth_r2.to_excel(xw, sheet_name="True_population_model", index=False, startcol=4)
        truth_load.to_excel(xw, sheet_name="True_population_model", index=False, startcol=7)
        notes.to_excel(xw, sheet_name="Notes", index=False)
    print(f"Wrote {OUT} ({N} respondents, {df.shape[1]} variables)")


if __name__ == "__main__":
    main()
