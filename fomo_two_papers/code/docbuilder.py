# -*- coding: utf-8 -*-
"""ساخت DOCX فارسی راست‌به‌چین با پاورقی واقعی (شمارهٔ فارسی)، جدول و شکل — بدون وابستگی خارجی."""
import re, zipfile, struct
from xml.sax.saxutils import escape

PD = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
LRI, PDI, LRM = "⁦", "⁩", "‎"

def fa(s):
    """تبدیل ارقام لاتین به فارسی و ممیز اعشار به «٫»"""
    s = re.sub(r"(?<=\d)\.(?=\d)", "٫", s)
    return s.translate(PD)

def num(x, nd=2, plus=False):
    """عدد فارسی با نشانهٔ منفی صحیح (درون ایزوله LTR)"""
    t = f"{abs(x):.{nd}f}"
    sign = "−" if x < 0 else ("+" if plus else "")
    return LRI + fa(sign + t) + PDI if sign else fa(t)

def pval(p):
    if p < .001: return LRI + fa("p < 0.001") + PDI
    return LRI + fa(f"p = {p:.3f}") + PDI

def S(expr):
    """عبارت آماری (مثل β = −0.47, z = 8.4) درون ایزولهٔ LTR با ارقام فارسی"""
    return LRI + fa(expr.replace("-", "−")) + PDI

class Doc:
    def __init__(self, body_pt=13, body_font="B Nazanin", title_font="B Zar", latin="Times New Roman"):
        self.body, self.bf, self.tf, self.lat = body_pt*2, body_font, title_font, latin
        self.parts, self.footnotes, self.media, self.seen = [], [], [], set()
        self.fn_count = 0

    # ---- اجزای متنی
    def _rpr(self, size=None, bold=False, italic=False, font=None, latin=None, hl=None, sup=False):
        size = size or self.body; f = font or self.bf; l = latin or self.lat
        x = f'<w:rFonts w:ascii="{l}" w:hAnsi="{l}" w:cs="{f}" w:eastAsia="{l}"/>'
        if bold: x += '<w:b/><w:bCs/>'
        if italic: x += '<w:i/><w:iCs/>'
        x += f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>'
        if hl: x += '<w:highlight w:val="yellow"/>'
        if sup: x += '<w:vertAlign w:val="superscript"/>'
        x += '<w:lang w:val="en-US" w:bidi="fa-IR"/>'
        return f"<w:rPr>{x}</w:rPr>"

    def _run(self, text, **kw):
        return f'<w:r>{self._rpr(**kw)}<w:t xml:space="preserve">{escape(text)}</w:t></w:r>'

    def _fnref(self, en):
        self.fn_count += 1; n = self.fn_count; mark = fa(str(n))
        self.footnotes.append((n, mark, en))
        return (f'<w:r><w:rPr><w:rStyle w:val="FootnoteReference"/>{self._rpr(size=self.body, sup=True)[7:-8]}</w:rPr>'
                f'<w:footnoteReference w:customMarkFollows="1" w:id="{n}"/></w:r>'
                f'<w:r>{self._rpr(size=self.body, sup=True)}<w:t>{mark}</w:t></w:r>')

    def runs(self, text, persian=True, **kw):
        """نشانه‌گذاری: [[fn:English]] پاورقی؛ **bold**؛ ==highlight=="""
        if persian: text = fa(text)
        out, pos = [], 0
        for m in re.finditer(r"\[\[fn:(.+?)\]\]|\*\*(.+?)\*\*|==(.+?)==", text):
            if m.start() > pos: out.append(self._run(text[pos:m.start()], **kw))
            if m.group(1) is not None: out.append(self._fnref(m.group(1)))
            elif m.group(2) is not None: out.append(self._run(m.group(2), **{**kw, "bold": True}))
            else: out.append(self._run(m.group(3), **{**kw, "hl": True}))
            pos = m.end()
        if pos < len(text): out.append(self._run(text[pos:], **kw))
        return "".join(out)

    def para(self, text, jc="both", indent=True, size=None, bold=False, rtl=True, font=None, after=80, before=0, keep=False, persian=True, **kw):
        ppr = ('<w:keepNext/>' if keep else '') + ('<w:bidi/>' if rtl else '')
        ppr += f'<w:spacing w:before="{before}" w:after="{after}" w:line="240" w:lineRule="auto"/>'
        if indent: ppr += '<w:ind w:firstLine="360"/>'
        # در پاراگراف راست‌به‌چپ، «left» در Word یعنی ابتدای خط (سمت راست)
        j = {"both": "both", "center": "center", "right": "left", "start": "left", "left": "left"}[jc]
        ppr += f'<w:jc w:val="{j}"/>'
        self.parts.append(f"<w:p><w:pPr>{ppr}</w:pPr>{self.runs(text, persian=persian, size=size, bold=bold, font=font, **kw)}</w:p>")

    def heading(self, text, level=1):
        self.para(text, jc="right", indent=False, size=self.body-2 if self.body > 24 else 24, bold=True, before=160, after=80, keep=True, italic=(level == 3))

    def title(self, text):
        self.para(text, jc="center", indent=False, size=24, bold=True, font=self.tf, after=200)

    def latin_para(self, text, size=24, after=60, jc="left", bold=False):
        self.para(text, jc="left", indent=False, size=size, rtl=False, persian=False, font=self.lat, after=after, bold=bold)

    def page_break(self):
        self.parts.append('<w:p><w:r><w:br w:type="page"/></w:r></w:p>')

    def caption(self, text, size=20):
        self.para(text, jc="center", indent=False, size=size, bold=True, font=self.tf, after=60, before=120, keep=True)

    def reference(self, text, latin=False):
        if latin: self.para(text, jc="left", indent=False, size=24, rtl=False, persian=False, font=self.lat, after=60)
        else:
            self.para(text, jc="both", indent=False, size=24, after=60)

    # ---- جدول
    def table(self, caption, header, rows, widths=None, note=None, size=24, first_col_left=False):
        self.caption(caption)
        n = len(header); widths = widths or [int(9000/n)]*n
        def cell(t, w, bold=False, jc="center", top=False, bottom=False, shade=False):
            b = ""
            if top: b += '<w:top w:val="single" w:sz="8" w:space="0" w:color="000000"/>'
            if bottom: b += '<w:bottom w:val="single" w:sz="8" w:space="0" w:color="000000"/>'
            tcpr = f'<w:tcW w:w="{w}" w:type="dxa"/>' + (f"<w:tcBorders>{b}</w:tcBorders>" if b else "") + '<w:vAlign w:val="center"/>'
            return (f'<w:tc><w:tcPr>{tcpr}</w:tcPr><w:p><w:pPr><w:bidi/><w:spacing w:before="40" w:after="40" w:line="240" w:lineRule="auto"/>'
                    f'<w:jc w:val="{jc}"/></w:pPr>{self.runs(str(t), size=size, bold=bold)}</w:p></w:tc>')
        x = (f'<w:tbl><w:tblPr><w:bidiVisual/><w:tblW w:w="{sum(widths)}" w:type="dxa"/><w:jc w:val="center"/>'
             '<w:tblLayout w:type="fixed"/><w:tblCellMar><w:left w:w="60" w:type="dxa"/><w:right w:w="60" w:type="dxa"/></w:tblCellMar></w:tblPr>'
             "<w:tblGrid>" + "".join(f'<w:gridCol w:w="{w}"/>' for w in widths) + "</w:tblGrid>")
        x += '<w:tr><w:trPr><w:tblHeader/></w:trPr>' + "".join(cell(h, w, True, top=True, bottom=True) for h, w in zip(header, widths)) + "</w:tr>"
        for i, r in enumerate(rows):
            last = i == len(rows)-1
            x += "<w:tr><w:trPr><w:cantSplit/></w:trPr>" + "".join(cell(c, w, jc="center", bottom=last) for c, w in zip(r, widths)) + "</w:tr>"
        x += "</w:tbl>"
        self.parts.append(x)
        if note: self.para(note, jc="both", indent=False, size=20, after=120, before=40)
        else: self.para("", after=100)

    # ---- شکل
    def figure(self, path, caption, width_cm=14):
        with open(path, "rb") as f: data = f.read()
        w, h = struct.unpack(">II", data[16:24])
        idx = len(self.media)+1; self.media.append((f"image{idx}.png", data))
        cx = int(width_cm*360000); cy = int(cx*h/w)
        rid = f"rIdImg{idx}"
        d = (f'<w:p><w:pPr><w:keepNext/><w:jc w:val="center"/></w:pPr><w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0">'
             f'<wp:extent cx="{cx}" cy="{cy}"/><wp:docPr id="{idx}" name="Figure {idx}"/>'
             '<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
             f'<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:nvPicPr><pic:cNvPr id="{idx}" name="image{idx}.png"/><pic:cNvPicPr/></pic:nvPicPr>'
             f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
             f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic>'
             '</a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>')
        self.parts.append(d)
        self.para(caption, jc="center", indent=False, size=20, bold=True, font=self.tf, after=160, before=40)

    # ---- ذخیره
    def save(self, path):
        NS = ('xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
              'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
              'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"')
        sect = ('<w:sectPr><w:footerReference w:type="default" r:id="rIdFooter"/><w:pgSz w:w="11906" w:h="16838"/>'
                '<w:pgMar w:top="1417" w:right="1417" w:bottom="1417" w:left="1417" w:header="708" w:footer="708" w:gutter="0"/><w:bidi/></w:sectPr>')
        document = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document {NS}><w:body>{"".join(self.parts)}{sect}</w:body></w:document>'
        fn = [f'<w:footnote w:type="separator" w:id="-1"><w:p><w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/></w:pPr><w:r><w:separator/></w:r></w:p></w:footnote>',
              f'<w:footnote w:type="continuationSeparator" w:id="0"><w:p><w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/></w:pPr><w:r><w:continuationSeparator/></w:r></w:p></w:footnote>']
        for n, mark, en in self.footnotes:
            rp = f'<w:rPr><w:rFonts w:ascii="{self.lat}" w:hAnsi="{self.lat}" w:cs="{self.lat}"/><w:sz w:val="22"/><w:szCs w:val="22"/>'
            fn.append(f'<w:footnote w:id="{n}"><w:p><w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/><w:jc w:val="left"/></w:pPr>'
                      f'<w:r>{rp}<w:vertAlign w:val="superscript"/></w:rPr><w:t xml:space="preserve">{mark} </w:t></w:r>'
                      f'<w:r>{rp}</w:rPr><w:t xml:space="preserve">{escape(en)}</w:t></w:r></w:p></w:footnote>')
        footnotes = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:footnotes {NS}>{"".join(fn)}</w:footnotes>'
        styles = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                  f'<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="{self.lat}" w:hAnsi="{self.lat}" w:cs="{self.bf}"/><w:sz w:val="{self.body}"/><w:szCs w:val="{self.body}"/>'
                  '<w:lang w:val="en-US" w:bidi="fa-IR"/></w:rPr></w:rPrDefault><w:pPrDefault><w:pPr><w:bidi/></w:pPr></w:pPrDefault></w:docDefaults>'
                  '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>'
                  '<w:style w:type="character" w:styleId="FootnoteReference"><w:name w:val="footnote reference"/><w:rPr><w:vertAlign w:val="superscript"/></w:rPr></w:style></w:styles>')
        settings = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:settings xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                    '<w:footnotePr><w:footnote w:id="-1"/><w:footnote w:id="0"/></w:footnotePr><w:themeFontLang w:val="en-US" w:bidi="fa-IR"/></w:settings>')
        footer = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:ftr {NS}><w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:rPr><w:sz w:val="20"/></w:rPr><w:fldChar w:fldCharType="begin"/></w:r>'
                  '<w:r><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r><w:r><w:fldChar w:fldCharType="end"/></w:r></w:p></w:ftr>')
        ct = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
              '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Default Extension="png" ContentType="image/png"/>'
              '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
              '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
              '<Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>'
              '<Override PartName="/word/footnotes.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footnotes+xml"/>'
              '<Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/></Types>')
        rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
        drels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                 '<Relationship Id="rIdSt" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
                 '<Relationship Id="rIdSe" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/>'
                 '<Relationship Id="rIdFn" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footnotes" Target="footnotes.xml"/>'
                 '<Relationship Id="rIdFooter" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>'
                 + "".join(f'<Relationship Id="rIdImg{i+1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/{n}"/>' for i, (n, _) in enumerate(self.media))
                 + '</Relationships>')
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("[Content_Types].xml", ct); z.writestr("_rels/.rels", rels)
            z.writestr("word/document.xml", document); z.writestr("word/styles.xml", styles); z.writestr("word/settings.xml", settings)
            z.writestr("word/footnotes.xml", footnotes); z.writestr("word/footer1.xml", footer); z.writestr("word/_rels/document.xml.rels", drels)
            for n, d in self.media: z.writestr(f"word/media/{n}", d)

    # ---- ارجاع‌دهی با پاورقی در نخستین استفاده
    def c(self, fa_name, en_name, year, paren=False):
        mark = "" if en_name in self.seen else f"[[fn:{en_name}]]"; self.seen.add(en_name)
        return f"({fa_name}{mark}، {year})" if paren else f"{fa_name}{mark} ({year})"
    def t(self, fa_term, en_term):
        mark = "" if en_term in self.seen else f"[[fn:{en_term}]]"; self.seen.add(en_term)
        return f"{fa_term}{mark}"
