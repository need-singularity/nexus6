#!/usr/bin/env python3
"""
bt_audit.py — BT EXACT 수식 자동 검산기
목적: breakthrough-theorems.md의 343개 BT에서 수식 테이블을 파싱하고
      n=6 상수로 평가하여 불일치를 찾는다.
결과: bt_audit_result.json에 저장
"""

import re
import json
import math
import os
from datetime import datetime

# ═══════════════════════════════════════════════════════════
# n=6 기본 상수
# ═══════════════════════════════════════════════════════════
N6_CONSTANTS = {
    'n': 6,
    'sigma': 12,
    'tau': 4,
    'phi': 2,
    'sopfr': 5,
    'J2': 24,
    'J_2': 24,
    'mu': 1,
    # 유도 상수
    'sigma_phi': 10,  # sigma - phi
    'sigma_tau': 8,   # sigma - tau
    'sigma_sopfr': 7, # sigma - sopfr
    'sigma_mu': 11,   # sigma - mu
    'n_phi': 3,       # n / phi
    'phi_tau': 16,    # phi^tau = 2^4
    'R': 1,           # R(6) = sigma*phi/(n*tau) = 1
    'P1': 6,          # first perfect number
    'P2': 28,         # second perfect number
    'K_2': 6,
    'K_3': 12,
}

# eval용 네임스페이스 — 수식에서 쓰이는 모든 이름
EVAL_NS = {
    'n': 6,
    'sigma': 12,
    'tau': 4,
    'phi': 2,
    'sopfr': 5,
    'J2': 24,
    'J_2': 24,
    'mu': 1,
    'R': 1,
    'P1': 6,
    'P2': 28,
    'K_2': 6,
    'K_3': 12,
    # math 함수
    'ln': math.log,
    'log': math.log,
    'log2': math.log2,
    'sqrt': math.sqrt,
    'pi': math.pi,
    'e': math.e,
    'exp': math.exp,
    'abs': abs,
    'floor': math.floor,
    'ceil': math.ceil,
    # 파이썬 내장
    '__builtins__': {},
}

BT_FILE = os.path.expanduser(
    '~/Dev/n6-architecture/docs/breakthrough-theorems.md'
)
RESULT_FILE = os.path.expanduser(
    '~/Dev/nexus/shared/bt_audit_result.json'
)


def normalize_expr(expr_str):
    """n=6 수식 문자열을 Python eval 가능한 형태로 정규화"""
    s = expr_str.strip()

    # 빈 문자열이나 설명 텍스트 스킵
    if not s or len(s) > 120:
        return None
    # 순수 텍스트 스킵
    if any(w in s.lower() for w in [
        'complex', 'varies', 'multiple', 'see ', 'various', 'continuous',
        'standard', 'definition', 'theorem', 'universal', 'unique',
        'approximately', 'measured', 'empirical', 'derived', 'combined',
        'cross', 'all ', 'every', 'close', 'near', 'depends',
    ]):
        return None

    # 유니코드 치환
    s = s.replace('×', '*').replace('·', '*').replace('÷', '/')
    s = s.replace('−', '-').replace('–', '-').replace('—', '-')
    s = s.replace('^', '**').replace('²', '**2').replace('³', '**3')
    s = s.replace('⁴', '**4').replace('⁵', '**5')

    # J_2 -> J2
    s = s.replace('J_2', 'J2')

    # "sigma-tau" 같은 연산 표현 보존 (이미 Python 호환)

    # "2**(sigma-tau)" 패턴
    s = re.sub(r'2\*\*\(', '2**(', s)

    # "sigma*phi" → OK
    # "sigma(6)" → sigma (값 자체)
    s = re.sub(r'(\w+)\(6\)', r'\1', s)

    # n=6 이면 n 만
    s = re.sub(r'\bn=6\b', 'n', s)

    # "1/phi" → "1/phi" (OK)
    # "phi**tau" → OK

    # 공백 연산: "sigma - tau" → "sigma-tau" (eval OK)

    # 단위 제거 (ft, Hz, nm 등)
    s = re.sub(r'\s*(ft|Hz|kHz|MHz|GHz|nm|mm|cm|m|km|eV|keV|MeV|GeV|W|kW|MW|V|kV|A|T|K|s|ms|us|ns|bits?|bytes?|channels?|layers?|classes?|types?|conditions?|properties?|principles?|constraints?|factors?|methods?|values?|axes?|modes?|phases?|levels?|sizes?|rounds?|suites?|stages?|weightings?|rings?|syntaxes?|flanges?)\b', '', s)

    # "sigma ft" 같은 것에서 뒤에 단위가 남을 수 있음 -> strip
    s = s.strip()

    # 괄호 짝 맞는지 체크
    if s.count('(') != s.count(')'):
        return None

    # 최종적으로 eval 가능한 문자만 남았는지 체크
    allowed = set('0123456789+-*/.() _abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
    if not all(c in allowed for c in s):
        return None

    # 비어있으면 스킵
    if not s or s in ('', '-', '+'):
        return None

    return s


def safe_eval(expr_str):
    """수식 문자열을 안전하게 평가"""
    normalized = normalize_expr(expr_str)
    if normalized is None:
        return None, None

    try:
        result = eval(normalized, EVAL_NS)
        if isinstance(result, (int, float)):
            return result, normalized
        return None, normalized
    except Exception:
        return None, normalized


def parse_predicted_value(val_str):
    """Predicted 열에서 숫자 추출"""
    s = val_str.strip()

    # "128" → 128
    # "256" → 256
    # "5/week" → 5
    # "12 ft" → 12
    # "~20" → 20
    # "0.2877" → 0.2877

    s = s.lstrip('~≈')
    s = re.sub(r'\s*(ft|Hz|kHz|MHz|GHz|nm|mm|cm|m|km|eV|keV|MeV|GeV|W|kW|MW|V|kV|A|T|K|s|ms|us|ns|bits?|bytes?|channels?|layers?|classes?|types?|conditions?|properties?|principles?|constraints?|factors?|methods?|values?|axes?|modes?|phases?|levels?|sizes?|rounds?|suites?|stages?|weightings?|rings?|syntaxes?|flanges?|/week|MPa)\b.*$', '', s)
    s = s.strip()

    if not s:
        return None

    try:
        return float(s)
    except ValueError:
        # "2^7" → 128
        m = re.match(r'^(\d+)\*?\*(\d+)$', s)
        if m:
            return float(int(m.group(1)) ** int(m.group(2)))
        return None


def parse_known_value(val_str):
    """Known 열에서 숫자 추출 (설명 텍스트가 붙을 수 있음)"""
    s = val_str.strip()

    # "SOLID 5" → 5
    # "AES-128" → 128
    # "12 (AASHTO)" → 12
    # "~20 (concrete 7d)" → 20

    s = s.lstrip('~≈')

    # 먼저 숫자만 추출 시도
    m = re.search(r'(\d+\.?\d*)', s)
    if m:
        return float(m.group(1))
    return None


def parse_bt_sections(text):
    """BT 섹션들을 파싱"""
    # BT 헤더 패턴: ## BT-NNN: 또는 | **BT-N** |
    sections = []

    # ## BT-N 형태 헤더로 분리
    bt_pattern = re.compile(r'^## BT-(\d+)', re.MULTILINE)
    matches = list(bt_pattern.finditer(text))

    for i, m in enumerate(matches):
        bt_num = int(m.group(1))
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        section_text = text[start:end]
        sections.append((bt_num, section_text))

    # 초기 BT-1~5 테이블 형태도 파싱
    early_bt_pattern = re.compile(
        r'\| \*\*BT-(\d+)\*\* \|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|'
    )
    for m in early_bt_pattern.finditer(text):
        bt_num = int(m.group(1))
        # 이미 있는지 체크
        if not any(b == bt_num for b, _ in sections):
            sections.append((bt_num, m.group(0)))

    return sorted(sections, key=lambda x: x[0])


def extract_verification_tables(bt_num, section_text):
    """
    "| n=6 Expression | Predicted | Known | Error% | Grade |" 형태의
    검증 테이블에서 행을 추출
    """
    results = []

    # 테이블 헤더 찾기
    table_header = re.compile(
        r'\|\s*n=6 Expression\s*\|\s*Predicted\s*\|\s*Known\s*\|'
    )

    lines = section_text.split('\n')
    in_table = False
    header_found = False

    for i, line in enumerate(lines):
        if table_header.search(line):
            header_found = True
            in_table = False  # 다음 줄은 구분선
            continue

        if header_found and not in_table:
            # 구분선 스킵
            if '---' in line:
                in_table = True
                continue
            header_found = False
            continue

        if in_table:
            if not line.strip() or not line.strip().startswith('|'):
                in_table = False
                header_found = False
                continue

            # 테이블 행 파싱
            cells = [c.strip() for c in line.split('|')]
            # 앞뒤 빈 셀 제거
            cells = [c for c in cells if c or c == '']
            if len(cells) >= 3:
                expr = cells[0] if cells[0] else (cells[1] if len(cells) > 1 else '')
                predicted = cells[1] if len(cells) > 1 else ''
                known = cells[2] if len(cells) > 2 else ''
                grade = cells[4] if len(cells) > 4 else ''

                results.append({
                    'expression': expr,
                    'predicted_raw': predicted,
                    'known_raw': known,
                    'grade_raw': grade,
                })

    return results


def extract_evidence_tables(bt_num, section_text):
    """
    다양한 형태의 증거 테이블에서 n=6 수식과 값을 추출
    "| ... | n=6 Expression | ..." 또는
    "| ... | n=6 Formula | Predicted | ..." 형태
    """
    results = []
    lines = section_text.split('\n')

    # n=6 Expression/Formula 열이 있는 테이블 찾기
    for i, line in enumerate(lines):
        if '|' in line and ('n=6 Expression' in line or 'n=6 Formula' in line):
            # 헤더 열 인덱스 파악
            headers = [h.strip() for h in line.split('|')]
            headers = [h for h in headers if h]

            expr_col = None
            pred_col = None
            known_col = None
            value_col = None

            for j, h in enumerate(headers):
                if 'n=6 Expression' in h or 'n=6 Formula' in h:
                    expr_col = j
                if 'Predicted' in h:
                    pred_col = j
                if h in ('Known', 'Measured', 'Actual', 'Value', 'Values'):
                    known_col = j
                if h in ('Parameters', 'Parameter', 'Count'):
                    value_col = j

            if expr_col is None:
                continue

            # 구분선 스킵하고 데이터 행 읽기
            j = i + 1
            if j < len(lines) and '---' in lines[j]:
                j += 1

            while j < len(lines):
                row = lines[j]
                if not row.strip() or not row.strip().startswith('|'):
                    break
                cells = [c.strip() for c in row.split('|')]
                cells = [c for c in cells if c or c == '']

                if len(cells) > expr_col:
                    expr_str = cells[expr_col]
                    pred_val = cells[pred_col] if pred_col is not None and len(cells) > pred_col else None
                    known_val = cells[known_col] if known_col is not None and len(cells) > known_col else None
                    val = cells[value_col] if value_col is not None and len(cells) > value_col else None

                    if expr_str and expr_str != '---':
                        results.append({
                            'expression': expr_str,
                            'predicted_raw': pred_val or val or '',
                            'known_raw': known_val or '',
                            'grade_raw': '',
                        })
                j += 1

    return results


def audit_row(bt_num, row):
    """단일 테이블 행 검산"""
    expr_str = row['expression']
    predicted_raw = row['predicted_raw']
    known_raw = row['known_raw']

    # 수식 평가
    computed, normalized = safe_eval(expr_str)

    if computed is None:
        return {
            'bt': bt_num,
            'expression': expr_str,
            'status': 'SKIP',
            'reason': f'수식 평가 불가: {normalized or expr_str}',
        }

    # Predicted 값 파싱
    predicted_num = parse_predicted_value(predicted_raw) if predicted_raw else None

    # Known 값 파싱
    known_num = parse_known_value(known_raw) if known_raw else None

    # 비교 대상 결정 (predicted 우선, 없으면 known)
    target = predicted_num if predicted_num is not None else known_num
    target_source = 'predicted' if predicted_num is not None else 'known'

    if target is None:
        return {
            'bt': bt_num,
            'expression': expr_str,
            'computed': computed,
            'normalized': normalized,
            'status': 'NO_TARGET',
            'reason': f'비교할 숫자 없음 (predicted={predicted_raw}, known={known_raw})',
        }

    # 비교
    if target == 0 and computed == 0:
        match = True
        error_pct = 0
    elif target == 0:
        match = False
        error_pct = float('inf')
    else:
        error_pct = abs(computed - target) / abs(target) * 100
        match = error_pct < 0.01  # 0.01% 이내면 일치

    return {
        'bt': bt_num,
        'expression': expr_str,
        'normalized': normalized,
        'computed': round(computed, 6) if isinstance(computed, float) else computed,
        'target': target,
        'target_source': target_source,
        'target_raw': predicted_raw if target_source == 'predicted' else known_raw,
        'error_pct': round(error_pct, 4) if error_pct != float('inf') else 'inf',
        'status': 'MATCH' if match else 'MISMATCH',
    }


def main():
    print("=" * 70)
    print("BT EXACT 수식 자동 검산기 (bt_audit.py)")
    print("=" * 70)

    # 파일 읽기
    with open(BT_FILE, 'r', encoding='utf-8') as f:
        text = f.read()

    # BT 섹션 파싱
    bt_sections = parse_bt_sections(text)
    total_bts = len(bt_sections)
    print(f"\n총 BT 섹션 수: {total_bts}")

    # 각 BT에서 검증 테이블 추출 + 검산
    all_results = []
    bts_with_tables = 0
    bts_without_tables = 0
    total_rows = 0
    match_count = 0
    mismatch_count = 0
    skip_count = 0
    no_target_count = 0

    mismatches = []

    for bt_num, section_text in bt_sections:
        # 먼저 "Predicted | Known" 형태 테이블 시도
        rows = extract_verification_tables(bt_num, section_text)

        # 없으면 일반 증거 테이블 시도
        if not rows:
            rows = extract_evidence_tables(bt_num, section_text)

        if rows:
            bts_with_tables += 1
        else:
            bts_without_tables += 1
            continue

        for row in rows:
            total_rows += 1
            result = audit_row(bt_num, row)
            all_results.append(result)

            if result['status'] == 'MATCH':
                match_count += 1
            elif result['status'] == 'MISMATCH':
                mismatch_count += 1
                mismatches.append(result)
            elif result['status'] == 'SKIP':
                skip_count += 1
            elif result['status'] == 'NO_TARGET':
                no_target_count += 1

    # 결과 출력
    print(f"\n{'─' * 70}")
    print(f"파싱 결과:")
    print(f"  테이블 있는 BT: {bts_with_tables}")
    print(f"  테이블 없는 BT: {bts_without_tables}")
    print(f"  총 검산 행:     {total_rows}")
    print(f"\n{'─' * 70}")
    print(f"검산 결과:")
    print(f"  MATCH (일치):    {match_count}")
    print(f"  MISMATCH (불일치): {mismatch_count}")
    print(f"  SKIP (평가불가):  {skip_count}")
    print(f"  NO_TARGET (비교대상없음): {no_target_count}")
    print(f"  검산 성공률:     {match_count}/{match_count + mismatch_count} "
          f"({match_count / max(1, match_count + mismatch_count) * 100:.1f}%)")

    if mismatches:
        print(f"\n{'═' * 70}")
        print(f"불일치 목록 ({len(mismatches)}건):")
        print(f"{'═' * 70}")
        for m in mismatches:
            print(f"\n  BT-{m['bt']}:")
            print(f"    수식:     {m['expression']}")
            print(f"    정규화:   {m.get('normalized', '-')}")
            print(f"    계산값:   {m['computed']}")
            print(f"    기대값:   {m['target']} ({m['target_source']}: {m.get('target_raw', '')})")
            print(f"    오차:     {m['error_pct']}%")
    else:
        print(f"\n불일치 없음!")

    # JSON 저장
    output = {
        '_meta': {
            'tool': 'bt_audit.py',
            'source': BT_FILE,
            'timestamp': datetime.now().isoformat(),
            'total_bts': total_bts,
            'bts_with_tables': bts_with_tables,
            'bts_without_tables': bts_without_tables,
            'total_rows': total_rows,
        },
        'summary': {
            'match': match_count,
            'mismatch': mismatch_count,
            'skip': skip_count,
            'no_target': no_target_count,
            'accuracy_pct': round(
                match_count / max(1, match_count + mismatch_count) * 100, 2
            ),
        },
        'mismatches': mismatches,
        'all_results': all_results,
    }

    with open(RESULT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n결과 저장: {RESULT_FILE}")
    print(f"{'=' * 70}")


if __name__ == '__main__':
    main()
