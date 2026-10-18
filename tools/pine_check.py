"""Crude Pine v5 checker: identifiers used before declaration / never declared,
:= on undeclared names, and history refs. Not a compiler."""
import re, sys
src = open(sys.argv[1], encoding='utf8').read().split('\n')
BUILTIN = set('''and or not if else for to by while true false na var varip int float bool string color line box label
array table switch break continue import export method type series simple const input math ta str request syminfo
open high low close volume time bar_index barstate timeframe location shape size text yloc xloc extend format
plot plotshape plotchar bgcolor barcolor fill hline alert alertcondition indicator strategy nz na runtime
display position font chart matrix map ticker session dayofweek last_bar_index linefill polyline order currency
max_bars_back plot_style hl2 hlc3 ohlc4 timenow year month hour minute second'''.split())
decl = {}            # name -> first line declared
uses = []
strip_str = lambda l: re.sub(r'"(?:[^"\\]|\\.)*"', '""', l)
for i, raw in enumerate(src, 1):
    l = strip_str(raw.split('//')[0]) if '"' in raw.split('//')[0] or '//' in raw else raw
    l = strip_str(raw)
    l = l.split('//')[0]
    m = re.match(r'^\s*(\w+)\s*\((.*)\)\s*=>', l)
    if m:
        decl.setdefault(m.group(1), i)
        for p in m.group(2).split(','):
            toks = re.findall(r'\w+', p.split('=')[0])
            if toks: decl.setdefault(toks[-1], i)
        continue
    m = re.match(r'^\s*for\s+(\w+)\s*=', l)
    if m: decl.setdefault(m.group(1), i)
    m = re.match(r'^\s*(?:var\s+|varip\s+)?(?:(?:int|float|bool|string|color|line|box|label|table|linefill)(?:\[\])?\s+|(?:int|float|bool|string|color|line|box|label)\[\]\s+)?(\w+)\s*=(?!=)', l)
    if m and m.group(1) not in BUILTIN:
        decl.setdefault(m.group(1), i)
    m = re.match(r'^\s*\[([\w\s,]+)\]\s*=(?!=)', l)
    if m:
        for n in re.findall(r'\w+', m.group(1)): decl.setdefault(n, i)
for i, raw in enumerate(src, 1):
    l = strip_str(raw).split('//')[0]
    if re.match(r'^\s*\w+\s*\(.*\)\s*=>', l): l = l.split('=>', 1)[1]
    for m in re.finditer(r'(?<![\.\w])([A-Za-z_]\w*)', l):
        n = m.group(1); rest = l[m.end():]
        if n in BUILTIN or n.isupper() and len(n) < 3: continue
        if re.match(r'\s*=(?!=)', rest) and l[:m.start()].count('(') > l[:m.start()].count(')'): continue   # named argument
        if re.match(r'\s*\.', rest) and n in ('color','line','box','label','array','math','ta','str','request','syminfo','text','shape','size','location','yloc','xloc','extend','format','display','barstate','timeframe','position','font','plot','hline','alert','runtime','chart','table','linefill','order','currency','session','dayofweek','strategy','matrix','map','ticker','polyline'): continue
        if n in ('int','float','bool','string'): continue
        uses.append((i, n))
bad = {}
for i, n in uses:
    d = decl.get(n)
    if d is None or d > i:
        bad.setdefault(n, []).append(i)
for n, ls in sorted(bad.items(), key=lambda x: x[1][0]):
    print(f'{n}: used at {ls[:6]}' + (f', declared at {decl[n]}' if n in decl else ', NEVER declared'))
print('identifiers flagged:', len(bad))
