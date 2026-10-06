' =====================================================================
' thesis_sample.prg  -  EViews program accompanying the book
' Reproduces the book's sample analysis (20 firms x 10 years, 1392-1401).
' NOTE: written from EViews documentation without access to the software;
'       test on your version and adjust paths. Menu equivalents are in Ch.2-3.
' =====================================================================
%path = "C:\thesis\"                       ' <-- change to your folder

' 1) open data and set the panel structure
wfopen(wf=thesis) %path + "thesis_sample.csv" ftype=ascii delim=comma colhead=1
pagestruct firm @date(year)                ' if this fails: Proc > Structure/Resize Current Page
smpl @all

' 2) descriptive statistics (Table 2-1)
group g1 roa size lev growth cfo
freeze(t_desc) g1.stats
freeze(t_corr) g1.cor

' 3) reference model (Section 3-2)
equation eq01.ls roa c size lev growth cfo
eq01.makeresids res01

' 4) classical assumption tests (Section B of Ch.3)
freeze(t_reset) eq01.reset(1)              ' 1 linearity
freeze(t_omit)  eq01.testadd covid         ' 2 omitted variable
freeze(t_bpg)   eq01.hettest(type=bpg)     ' 4 heteroskedasticity
freeze(t_white) eq01.hettest(type=white)
freeze(t_bg1)   eq01.auto(1)               ' 5 serial correlation
freeze(t_bg2)   eq01.auto(2)
freeze(t_bg3)   eq01.auto(3)
freeze(t_jb)    res01.hist                 ' 6 normality
' 7 VIF: View > Coefficient Diagnostics > Variance Inflation Factors
' 8 Chow/CUSUM: see Section "Assumption 8" (panel workaround via dummies)

' 5) treatments
equation eq_white.ls(cov=white) roa c size lev growth cfo
equation eq_hac.ls(cov=hac, covlag=2) roa c size lev growth cfo
genr lev_covid = lev*covid
equation eq_final.ls(cov=white) roa c size lev growth cfo covid
equation eq_dummy_inter.ls(cov=white) roa c size lev growth cfo covid lev_covid

' 6) robustness: lagged regressors (Assumption 3)
equation eq_lag.ls(cov=white) roa c size(-1) lev(-1) growth(-1) cfo(-1)

' 7) through-the-origin comparison (Section 3-8)
equation eq_origin.ls roa size lev growth cfo

save %path + "thesis.wf1"
