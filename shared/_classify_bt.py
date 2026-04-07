#!/usr/bin/env python3
import json, re
from collections import Counter, defaultdict

d=json.load(open('/Users/ghost/Dev/nexus/shared/bt_audit_result.json'))
ms=d['mismatches']

def classify(m):
    expr=m['expression']; raw=(m['target_raw'] or '').strip()
    comp=m['computed']; tgt=m['target']; norm=m['normalized']
    raw_clean=re.sub(r'[*`]','',raw).strip()
    if re.search(r'10[\^\u2070-\u2079]|\u00d710|\*10\^', raw):
        return '3', 'power-of-10 표기 (10^k)'
    if re.fullmatch(r'\d{1,2}', raw_clean) and m['bt']==89:
        return '2', '행번호 컬럼 오인 (BT-89 # column)'
    if re.fullmatch(r'[-+]?\d+(\.\d+)?', norm or '') and re.search(r'[A-Za-z\uac00-\ud7a3]{3,}', raw_clean):
        return '2','리터럴 Expression + 설명 Known'
    if re.search(r'\d+/\d+|ln\(|\u03c0|\u03c6|\u03c3|\u03c4|\u221a|\^|[\u00b2\u00b3\u2074]', raw_clean):
        return '2','분수/기호식 Known 셀'
    if '=' in raw_clean:
        return '2','Known 셀 등식형'
    if re.search(r'\b(eV|keV|MeV|GeV|V|Hz|kHz|MHz|GHz|K|nm|mm|cm|kg|MW|W|ms|ns|Wh|kWh|J|T|%)\b', raw):
        return '2','단위 포함 Known'
    if re.search(r'[\u2080-\u2089]', expr):
        return '2','첨자 기호 Expression'
    if re.search(r'[A-Za-z\uac00-\ud7a3]', raw_clean):
        return '2','서술형 Known 셀'
    try:
        if tgt and comp and abs(comp/tgt - round(comp/tgt))<0.01 and round(comp/tgt) in (10,100,1000,10000):
            return '3','스케일 10^k 차이'
    except: pass
    return '1','진짜 오류 후보'

cats=Counter(); by_cat=defaultdict(list); reasons=Counter()
for m in ms:
    c,r=classify(m); cats[c]+=1; reasons[(c,r)]+=1; by_cat[c].append(m)

lines=[f"total={len(ms)} cats={dict(cats)}"]
for k,v in reasons.most_common():
    lines.append(f"  {k[0]}-{k[1]} {v}")
lines.append("=== cat1 ===")
for m in by_cat['1']:
    lines.append(f"BT-{m['bt']}: {m['expression']!r} comp={m['computed']} tgt={m['target']} raw={m['target_raw']!r}")
lines.append("=== cat3 ===")
for m in by_cat['3']:
    lines.append(f"BT-{m['bt']}: {m['expression']!r} comp={m['computed']} tgt={m['target']} raw={m['target_raw']!r}")

open('/tmp/classify_out.txt','w').write('\n'.join(lines))

out=[{**m,'category':c,'reason':r} for m in ms for c,r in [classify(m)]]
json.dump(out, open('/Users/ghost/Dev/nexus/shared/bt_audit_classification.json','w'), ensure_ascii=False, indent=1)
print("done", len(ms), dict(cats))
