# Capital structure deviation, managerial ability & investment efficiency (emerging markets)

| Path | What it is |
|---|---|
| `docs/METHODOLOGY.md` | Diagnosis of the original script, variable definitions, hypothesis → model map, robustness plan, decision guide |
| `stata/01_master_CSD_MA_InvEff.do` | Main Stata 16+ script (edit the paths in section 0, then run) |
| `stata_pkgs/` | Offline copies of required Stata packages (no internet/Java needed); see `stata/INSTALL_PACKAGES.md` |
| `python/csd_ma_pipeline.py` | Python version of the same steps; `--simulate` / `--null` run it on simulated data |

Quick start (Python):

```bash
pip install -r python/requirements.txt
python python/csd_ma_pipeline.py --data Final_Master_Data.xlsx --out output
python python/csd_ma_pipeline.py --simulate --out output_sim      # validation with known effects
```
