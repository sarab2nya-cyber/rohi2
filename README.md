# rohi2

## PLS-SEM analysis (`pls_sem_analysis.py`)

Complete PLS-SEM pipeline for the study of financial control (Control Activities,
Financial Management) and four dimensions of public accountability.

### Run

```bash
pip install -r requirements.txt      # python-docx and plotly are optional
python pls_sem_analysis.py           # reads Desktop/1.xlsx
python pls_sem_analysis.py "C:/path/to/1.xlsx"
```

Expected columns: `Gender Age Degree Experience Q1..Q13 Z1..Z24` (first sheet).

Results are written next to the input file in `PLS_SEM_Results/`:

- `PLS_SEM_All_Results.xlsx`: every table (an INDEX sheet lists them all)
- `PLS_SEM_Report.docx`: manuscript tables and all figures
- `Summary.txt`: key diagnostics and quality checklist
- `figures/`: 300-dpi PNG figures, including 3D response surfaces, 3D path map, 3D HTMT
- `Interactive_3D_figures.html`: rotatable 3D figures (needs plotly)
- `semopy_report/`: semopy's HTML report of the CB-SEM structural model

Table 8 (structural model fit: X2/df, GFI, SRMR, IFI, NFI, PGFI, PNFI, RMSEA, CFI) is
estimated with semopy (maximum likelihood). semopy's own "GFI" equals 1 - chi2/chi2_baseline
(the NFI formula), so GFI/AGFI/PGFI are recomputed with the Joreskog-Sorbom formula from
semopy's implied covariance matrix.

### Test data

`simulate_data.py` writes `simulated_data_200.xlsx`: 200 respondents with the same
variables, generated from a known population model (true paths and loadings are in the
sheet `True_population_model`). Use it only to test the code:

```bash
python simulate_data.py
python pls_sem_analysis.py simulated_data_200.xlsx
```

Edit the configuration block at the top of the script to change construct
items, hypotheses, items to drop (`DROP_ITEMS`), resample counts or groups for
multigroup analysis. Set the environment variable `PLS_FAST=1` for a quick test run.

The PLS engine was checked against the `plspm` package (identical path
coefficients, loadings and R² to 1e-15 on standardized data).
