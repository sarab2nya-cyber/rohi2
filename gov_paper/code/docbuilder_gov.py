# -*- coding: utf-8 -*-
"""DOCX builder following the journal's Persian template: B Mitra 13 body, TNR 11 Latin, B Titr headings, 4.5 cm side margins,
journal banner header (odd) / page number header (even), unnumbered headings, true footnotes (marks in Persian digits)."""
import re, os, zipfile
from xml.sax.saxutils import escape
from docbuilder import Doc, fa, num, pval, S, LRI, PDI

HERE = os.path.dirname(os.path.abspath(__file__)); TPL = os.path.join(HERE, "tpl")
LATIN = re.compile(r"([A-Za-z][A-Za-z0-9\-\.\&'’/ ]*[A-Za-z0-9]|[A-Za-z])")

class DocJ(Doc):
    def __init__(self):
        super().__init__(body_pt=13, body_font="B Mitra", title_font="B Mitra", latin="Times New Roman")
        self.hf = "B Titr"
    def _run(self, text, **kw):
        out = []
        for tok in LATIN.split(text):
            if not tok: continue
            if LATIN.fullmatch(tok):
                k = dict(kw); sz = (k.get("size") or self.body); k["size"] = max(16, sz - 4); k["font"] = self.lat
                out.append(super()._run(tok, **k))
            else: out.append(super()._run(tok, **kw))
        return "".join(out)
    def heading(self, text, level=1):
        if level == 1: self.para(text, jc="right", indent=False, size=25, bold=True, font=self.hf, before=240, after=60, keep=True)
        else: self.para(text, jc="right", indent=False, size=23, bold=True, font=self.hf, before=160, after=40, keep=True)
    def title(self, text): self.para(text, jc="center", indent=False, size=28, bold=True, font=self.hf, after=120)
    def caption(self, text, size=20): self.para(text, jc="center", indent=False, size=size, bold=True, font=self.bf, after=60, before=120, keep=True)
    def bodyp(self, text, **kw): self.para(text, jc="both", indent=True, size=26, after=0, **kw)
    def blank(self, size=22): self.para("", jc="center", indent=False, size=size, after=0)
    def reference(self, text, latin=False):
        if latin:
            runs = "".join(Doc.runs(self, p, persian=False, size=22, font=self.lat, italic=(i % 2 == 1)) for i, p in enumerate(re.split(r"(?<!:)//", text)) if p)
            self.parts.append(f'<w:p><w:pPr><w:spacing w:before="0" w:after="40" w:line="240" w:lineRule="auto"/><w:ind w:left="567" w:hanging="567"/><w:jc w:val="left"/></w:pPr>{runs}</w:p>')
        else: self.para(text, jc="both", indent=False, size=24, after=40)
    def save(self, path, title="Article"):
        W = ('xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
             'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"')
        sect = ('<w:sectPr><w:headerReference w:type="even" r:id="rIdHe"/><w:headerReference w:type="default" r:id="rIdHd"/>'
                '<w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="450" w:right="2552" w:bottom="3033" w:left="2552" w:header="0" w:footer="0" w:gutter="0"/>'
                '<w:pgNumType w:start="1"/><w:bidi/></w:sectPr>')
        document = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document {W}><w:body>{"".join(self.parts)}{sect}</w:body></w:document>'
        fn = ['<w:footnote w:type="separator" w:id="-1"><w:p><w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/></w:pPr><w:r><w:separator/></w:r></w:p></w:footnote>',
              '<w:footnote w:type="continuationSeparator" w:id="0"><w:p><w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/></w:pPr><w:r><w:continuationSeparator/></w:r></w:p></w:footnote>']
        for n, mark, en in self.footnotes:
            rp = f'<w:rPr><w:rFonts w:ascii="{self.lat}" w:hAnsi="{self.lat}" w:cs="{self.lat}"/><w:sz w:val="18"/><w:szCs w:val="18"/>'
            fn.append(f'<w:footnote w:id="{n}"><w:p><w:pPr><w:bidi w:val="0"/><w:spacing w:after="0" w:line="240" w:lineRule="auto"/><w:jc w:val="left"/></w:pPr>'
                      f'<w:r>{rp}</w:rPr><w:t xml:space="preserve">{mark}. </w:t></w:r><w:r>{rp}</w:rPr><w:t xml:space="preserve">{escape(en)}</w:t></w:r></w:p></w:footnote>')
        footnotes = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:footnotes {W}>{"".join(fn)}</w:footnotes>'
        styles = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                  f'<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="{self.lat}" w:hAnsi="{self.lat}" w:cs="{self.bf}"/><w:sz w:val="{self.body}"/><w:szCs w:val="{self.body}"/>'
                  '<w:lang w:val="en-US" w:bidi="fa-IR"/></w:rPr></w:rPrDefault><w:pPrDefault><w:pPr><w:bidi/></w:pPr></w:pPrDefault></w:docDefaults>'
                  '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>'
                  '<w:style w:type="paragraph" w:styleId="Header"><w:name w:val="header"/><w:basedOn w:val="Normal"/></w:style>'
                  '<w:style w:type="character" w:styleId="FootnoteReference"><w:name w:val="footnote reference"/><w:rPr><w:vertAlign w:val="superscript"/></w:rPr></w:style></w:styles>')
        settings = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:settings xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                    '<w:zoom w:percent="100"/><w:defaultTabStop w:val="709"/><w:evenAndOddHeaders/><w:characterSpacingControl w:val="doNotCompress"/>'
                    '<w:footnotePr><w:footnote w:id="-1"/><w:footnote w:id="0"/></w:footnotePr><w:themeFontLang w:val="en-US" w:bidi="fa-IR"/></w:settings>')
        ct = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
              '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Default Extension="png" ContentType="image/png"/>'
              '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
              '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
              '<Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>'
              '<Override PartName="/word/footnotes.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footnotes+xml"/>'
              '<Override PartName="/word/header1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"/>'
              '<Override PartName="/word/header2.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"/>'
              '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
              '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/></Types>')
        rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
                '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
                '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/></Relationships>')
        RT = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
        drels = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                 f'<Relationship Id="rIdSt" Type="{RT}/styles" Target="styles.xml"/><Relationship Id="rIdSe" Type="{RT}/settings" Target="settings.xml"/>'
                 f'<Relationship Id="rIdFn" Type="{RT}/footnotes" Target="footnotes.xml"/><Relationship Id="rIdHe" Type="{RT}/header" Target="header1.xml"/><Relationship Id="rIdHd" Type="{RT}/header" Target="header2.xml"/>'
                 + "".join(f'<Relationship Id="rIdImg{i+1}" Type="{RT}/image" Target="media/{n}"/>' for i, (n, _) in enumerate(self.media)) + '</Relationships>')
        hrels = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="{RT}/image" Target="media/banner.png"/></Relationships>'
        core = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" '
                f'xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><dc:title>{escape(title)}</dc:title><dc:language>fa-IR</dc:language></cp:coreProperties>')
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("[Content_Types].xml", ct); z.writestr("_rels/.rels", rels); z.writestr("docProps/core.xml", core)
            z.writestr("docProps/app.xml", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"><Application>Microsoft Office Word</Application></Properties>')
            z.writestr("word/document.xml", document); z.writestr("word/styles.xml", styles); z.writestr("word/settings.xml", settings)
            z.writestr("word/footnotes.xml", footnotes); z.writestr("word/_rels/document.xml.rels", drels)
            for h in ("header1.xml", "header2.xml"): z.writestr(f"word/{h}", open(os.path.join(TPL, h), encoding="utf-8").read())
            z.writestr("word/_rels/header2.xml.rels", hrels); z.writestr("word/media/banner.png", open(os.path.join(TPL, "banner.png"), "rb").read())
            for n, d in self.media: z.writestr(f"word/media/{n}", d)
