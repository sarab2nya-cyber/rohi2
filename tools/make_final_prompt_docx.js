const fs = require('fs');
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow, TableCell,
  WidthType, ShadingType, BorderStyle, LevelFormat, Footer, PageNumber,
} = require('docx');

const FONT = 'Tahoma';
const SZ = 22; // 11pt

// ---- inline markup: **bold** segments ----
function runs(text, opts = {}) {
  const out = [];
  const parts = text.split(/(\*\*[^*]+\*\*)/);
  for (const p of parts) {
    if (!p) continue;
    const bold = p.startsWith('**');
    const t = bold ? p.slice(2, -2) : p;
    out.push(new TextRun({
      text: t, rightToLeft: true, font: { ascii: FONT, hAnsi: FONT, cs: FONT },
      size: opts.size || SZ, sizeComplexScript: opts.size || SZ,
      bold: bold || opts.bold, boldComplexScript: bold || opts.bold,
      color: opts.color,
    }));
  }
  return out;
}

const P = (text, opts = {}) => new Paragraph({
  bidirectional: true, alignment: opts.align || AlignmentType.BOTH,
  spacing: { after: opts.after ?? 120, line: 320 },
  children: runs(text, opts),
});

const H1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, bidirectional: true, alignment: AlignmentType.RIGHT,
  spacing: { before: 360, after: 160 }, children: runs(t, { size: 32, bold: true, color: '1F3864' }) });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, bidirectional: true, alignment: AlignmentType.RIGHT,
  spacing: { before: 240, after: 120 }, children: runs(t, { size: 26, bold: true, color: '2E5597' }) });
const H3 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_3, bidirectional: true, alignment: AlignmentType.RIGHT,
  spacing: { before: 180, after: 80 }, children: runs(t, { size: 23, bold: true, color: '385723' }) });

let numInstance = 0;
const bullets = (items, level = 0) => items.map((t) => new Paragraph({
  bidirectional: true, alignment: AlignmentType.BOTH, numbering: { reference: 'bul', level },
  spacing: { after: 80, line: 300 }, children: runs(t),
}));
const numbered = (items) => {
  const inst = ++numInstance;
  return items.map((t) => new Paragraph({
    bidirectional: true, alignment: AlignmentType.BOTH, numbering: { reference: 'num', level: 0, instance: inst },
    spacing: { after: 80, line: 300 }, children: runs(t),
  }));
};

// note box: shaded single-cell table
const NOTE_W = 9026;
const note = (lines, fill = 'FFF4E5') => new Table({
  width: { size: NOTE_W, type: WidthType.DXA }, columnWidths: [NOTE_W], visuallyRightToLeft: true,
  rows: [new TableRow({ children: [new TableCell({
    width: { size: NOTE_W, type: WidthType.DXA }, shading: { fill, type: ShadingType.CLEAR, color: 'auto' },
    margins: { top: 100, bottom: 100, left: 160, right: 160 },
    children: lines.map((l) => P(l, { after: 60 })),
  })] })],
});

const border = { style: BorderStyle.SINGLE, size: 4, color: 'A6A6A6' };
const borders = { top: border, bottom: border, left: border, right: border };
// columns given in reading order (right to left)
function table(widths, header, rows) {
  const total = widths.reduce((a, b) => a + b, 0);
  const mk = (cells, head) => new TableRow({ tableHeader: head, children: cells.map((c, i) => new TableCell({
    width: { size: widths[i], type: WidthType.DXA }, borders,
    shading: head ? { fill: 'D9E2F3', type: ShadingType.CLEAR, color: 'auto' } : undefined,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children: [].concat(c).map((t) => new Paragraph({ bidirectional: true, alignment: AlignmentType.RIGHT,
      spacing: { after: 40, line: 280 }, children: runs(t, { size: 20, bold: head }) })),
  })) });
  return new Table({ width: { size: total, type: WidthType.DXA }, columnWidths: widths, visuallyRightToLeft: true,
    rows: [mk(header, true), ...rows.map((r) => mk(r, false))] });
}
const gap = () => new Paragraph({ children: [], spacing: { after: 80 } });

// ======================================================================
// Markdown (headings #/##/###, tables, '-' bullets, '1.' lists, paragraphs) -> docx
const IN = process.argv[2] || '/home/user/rohi2/Final_Prompt_V19_FA.md';
const OUT = process.argv[3] || '/home/user/rohi2/Final_Prompt_V19_FA.docx';
const md = fs.readFileSync(IN, 'utf8').split('\n');
const body = [];
const cells = (l) => l.trim().replace(/^\|/, '').replace(/\|$/, '').split('|').map((c) => c.trim());
const splitSent = (c) => c.split(/(?<=\.)\s+(?=\S)/).filter((x) => x.length);
let i = 0;
while (i < md.length) {
  const l = md[i];
  if (!l.trim()) { i++; continue; }
  if (l.startsWith('# ')) {
    body.push(new Paragraph({ heading: HeadingLevel.TITLE, bidirectional: true, alignment: AlignmentType.CENTER, spacing: { after: 240 },
      children: runs(l.slice(2), { size: 36, bold: true, color: '1F3864' }) }));
    i++; continue;
  }
  if (l.startsWith('## ')) { body.push(H1(l.slice(3))); i++; continue; }
  if (l.startsWith('### ')) { body.push(H2(l.slice(4))); i++; continue; }
  if (l.startsWith('|')) {
    const rows = [];
    while (i < md.length && md[i].startsWith('|')) { rows.push(cells(md[i])); i++; }
    const header = rows[0]; const data = rows.slice(2);
    const n = header.length;
    const widths = n === 2 ? [2400, 6626] : [1500, 4826, 2700];
    body.push(table(widths, header, data.map((r) => r.map((c) => splitSent(c).length ? splitSent(c) : [''])))); body.push(gap());
    continue;
  }
  if (/^- /.test(l)) {
    const items = [];
    while (i < md.length && /^- /.test(md[i])) { items.push(md[i].slice(2)); i++; }
    body.push(...bullets(items)); continue;
  }
  if (/^\d+\. /.test(l)) {
    const items = [];
    while (i < md.length && /^\d+\. /.test(md[i])) { items.push(md[i].replace(/^\d+\. /, '')); i++; }
    body.push(...numbered(items)); continue;
  }
  body.push(P(l)); i++;
}

const doc = new Document({
  styles: {
    default: { document: { run: { font: FONT, size: SZ }, paragraph: { bidirectional: true } } },
    paragraphStyles: [
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { size: 32, bold: true, font: FONT }, paragraph: { outlineLevel: 0 } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { size: 26, bold: true, font: FONT }, paragraph: { outlineLevel: 1 } },
      { id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { size: 23, bold: true, font: FONT }, paragraph: { outlineLevel: 2 } },
    ],
  },
  numbering: { config: [
    { reference: 'bul', levels: [
      { level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.RIGHT, style: { paragraph: { indent: { left: 540, hanging: 300 } } } },
      { level: 1, format: LevelFormat.BULLET, text: '◦', alignment: AlignmentType.RIGHT, style: { paragraph: { indent: { left: 1080, hanging: 300 } } } },
    ] },
    { reference: 'num', levels: [
      { level: 0, format: LevelFormat.DECIMAL, text: '%1.', alignment: AlignmentType.RIGHT, style: { paragraph: { indent: { left: 540, hanging: 360 } } } },
    ] },
  ] },
  sections: [{
    properties: { page: { margin: { top: 1200, bottom: 1200, left: 1440, right: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ children: [PageNumber.CURRENT], size: 18, color: '808080' })] })] }) },
    children: body,
  }],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(OUT, buf);
  console.log('written', buf.length);
});
