# -*- coding: utf-8 -*-
"""English (LTR) DOCX builder derived from docbuilder.Doc: Times New Roman 12, double-ish spacing, APA-style tables."""
import zipfile, io, re, os
from docbuilder import Doc

class DocEN(Doc):
    def __init__(self, body_pt=12):
        super().__init__(body_pt=body_pt, body_font="Times New Roman", title_font="Times New Roman")
    def runs(self, text, persian=False, **kw):
        parts = text.split("//"); out = []
        for i, p in enumerate(parts):
            if p: out.append(Doc.runs(self, p, persian=False, **{**kw, "italic": (i % 2 == 1) or kw.get("italic", False)}))
        return "".join(out)
    def para(self, text, jc="both", indent=True, size=None, bold=False, rtl=False, font=None, after=80, before=0, keep=False, persian=False, **kw):
        ppr = ('<w:keepNext/>' if keep else '') + f'<w:spacing w:before="{before}" w:after="{after}" w:line="276" w:lineRule="auto"/>'
        if indent: ppr += '<w:ind w:firstLine="425"/>'
        ppr += f'<w:jc w:val="{ {"both":"both","center":"center"}.get(jc,"left") }"/>'
        self.parts.append(f"<w:p><w:pPr>{ppr}</w:pPr>{self.runs(text, size=size, bold=bold, **kw)}</w:p>")
    def heading(self, text, level=1):
        if level == 1: self.para(text, jc="left", indent=False, size=26, bold=True, before=200, after=80, keep=True)
        elif level == 2: self.para(text, jc="left", indent=False, size=24, bold=True, before=140, after=60, keep=True)
        else: self.para(text, jc="left", indent=False, size=24, italic=True, before=100, after=40, keep=True)
    def title(self, text): self.para(text, jc="center", indent=False, size=32, bold=True, after=160)
    def caption(self, text, size=22): self.para(text, jc="left", indent=False, size=size, bold=True, after=60, before=140, keep=True)
    def reference(self, text, latin=True):
        self.parts.append(f'<w:p><w:pPr><w:spacing w:before="0" w:after="60" w:line="240" w:lineRule="auto"/><w:ind w:left="567" w:hanging="567"/><w:jc w:val="left"/></w:pPr>{self.runs(self._ital(text), size=22)}</w:p>')
    def _ital(self, t): return t  # italics marked with *..* handled below
    def table(self, caption, header, rows, widths=None, note=None, size=20, first_col_left=True):
        self.caption(caption)
        n = len(header); widths = widths or [int(9300/n)]*n
        def cell(t, w, bold=False, jc="center", top=False, bottom=False):
            b = ""
            if top: b += '<w:top w:val="single" w:sz="8" w:space="0" w:color="000000"/>'
            if bottom: b += '<w:bottom w:val="single" w:sz="8" w:space="0" w:color="000000"/>'
            tcpr = f'<w:tcW w:w="{w}" w:type="dxa"/>' + (f"<w:tcBorders>{b}</w:tcBorders>" if b else "") + '<w:vAlign w:val="center"/>'
            return (f'<w:tc><w:tcPr>{tcpr}</w:tcPr><w:p><w:pPr><w:spacing w:before="30" w:after="30" w:line="240" w:lineRule="auto"/><w:jc w:val="{jc}"/></w:pPr>{self.runs(str(t), size=size, bold=bold)}</w:p></w:tc>')
        x = (f'<w:tbl><w:tblPr><w:tblW w:w="{sum(widths)}" w:type="dxa"/><w:jc w:val="center"/><w:tblLayout w:type="fixed"/>'
             '<w:tblCellMar><w:left w:w="60" w:type="dxa"/><w:right w:w="60" w:type="dxa"/></w:tblCellMar></w:tblPr><w:tblGrid>' + "".join(f'<w:gridCol w:w="{w}"/>' for w in widths) + "</w:tblGrid>")
        x += '<w:tr><w:trPr><w:tblHeader/></w:trPr>' + "".join(cell(h, w, True, "left" if (i==0 and first_col_left) else "center", True, True) for i, (h, w) in enumerate(zip(header, widths))) + "</w:tr>"
        for i, r in enumerate(rows):
            x += "<w:tr><w:trPr><w:cantSplit/></w:trPr>" + "".join(cell(c, w, jc="left" if (j==0 and first_col_left) else "center", bottom=(i==len(rows)-1)) for j, (c, w) in enumerate(zip(r, widths))) + "</w:tr>"
        x += "</w:tbl>"; self.parts.append(x)
        if note: self.para(note, jc="both", indent=False, size=20, after=120, before=40)
        else: self.para("", after=100)
    def figure(self, path, caption, width_cm=15.5):
        super().figure(path, caption, width_cm)
        # replace the Persian-style caption paragraph by an English one
        self.parts.pop(); self.para(caption, jc="left", indent=False, size=22, bold=True, after=160, before=40)
    def save(self, path, title="Article", lang="en-US"):
        buf = path + ".tmp"; super().save(buf)
        zin = zipfile.ZipFile(buf); zout = zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED)
        for it in zin.infolist():
            d = zin.read(it.filename)
            if it.filename in ("word/styles.xml", "word/document.xml"):
                s = d.decode("utf8").replace("<w:pPrDefault><w:pPr><w:bidi/></w:pPr></w:pPrDefault>", "<w:pPrDefault><w:pPr/></w:pPrDefault>").replace("<w:bidi/></w:sectPr>", "</w:sectPr>")
                d = s.encode("utf8")
            if it.filename == "docProps/core.xml":
                d = d.decode("utf8").replace("<dc:title>Article</dc:title>", f"<dc:title>{title}</dc:title>").replace("fa-IR", lang).encode("utf8")
            zout.writestr(it, d)
        zout.close(); zin.close(); os.remove(buf)
