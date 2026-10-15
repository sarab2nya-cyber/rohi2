# -*- coding: utf-8 -*-
"""Round-trip each docx through LibreOffice (normalises package), then force Print Layout; make PDF copy."""
import sys, os, subprocess, shutil, tempfile
sys.path.insert(0, os.path.dirname(__file__))
from fix_view import fix
for p in sys.argv[1:]:
    t = tempfile.mkdtemp(); out = os.path.join(t, "o"); os.makedirs(out)
    subprocess.run(["soffice","--headless","--convert-to","docx:MS Word 2007 XML","--outdir",out,p],capture_output=True,timeout=300)
    r = os.path.join(out, os.path.basename(p))
    if not os.path.exists(r): print("FAIL", p); continue
    shutil.copy(r, p); fix(p)
    subprocess.run(["soffice","--headless","--convert-to","pdf","--outdir",os.path.dirname(p),p],capture_output=True,timeout=300)
    print("ok", os.path.basename(p))
