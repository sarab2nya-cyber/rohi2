# -*- coding: utf-8 -*-
"""Force Print Layout view (not Draft/Web) in a .docx by adding <w:view w:val="print"/> to word/settings.xml."""
import sys, zipfile, re, os, shutil
def fix(path):
    tmp = path + ".tmp"; zin = zipfile.ZipFile(path); changed = False
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for it in zin.infolist():
            d = zin.read(it.filename)
            if it.filename == "word/settings.xml":
                s = d.decode("utf8")
                s = re.sub(r'<w:view [^>]*/>', '', s)
                if "<w:zoom" in s: s = s.replace("<w:zoom", '<w:view w:val="print"/><w:zoom', 1)
                else: s = re.sub(r'(<w:settings[^>]*>)', r'\1<w:view w:val="print"/>', s, 1)
                s = re.sub(r'(w:name="compatibilityMode"[^>]*w:val=)"\d+"', r'\1"15"', s)
                d = s.encode("utf8"); changed = True
            if it.filename == "word/document.xml":
                s = d.decode("utf8")
                def mv(m):
                    inner = m.group(1); sp = re.search(r'<w:sectPr>.*?</w:sectPr>', inner, re.S)
                    if not sp: return m.group(0)
                    rest = inner.replace(sp.group(0), '', 1)
                    return '<w:pPr>' + rest + sp.group(0) + '</w:pPr>'
                s = re.sub(r'<w:pPr>((?:(?!</w:pPr>).)*?<w:sectPr>.*?</w:sectPr>(?:(?!</w:pPr>).)*?)</w:pPr>', mv, s, flags=re.S)
                s = s.replace('w:charSpace="4294963199"', 'w:charSpace="-4097"')
                d = s.encode("utf8")
            zout.writestr(it, d)
    zin.close(); shutil.move(tmp, path); return changed
if __name__ == "__main__":
    for p in sys.argv[1:]: print(os.path.basename(p), fix(p))
