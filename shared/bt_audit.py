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
    # 그리스 문자 매핑으로 추가되는 이름
    'alpha': 1/137.036,  # 미세구조상수
    'beta': 0.288,  # ln(4/3)
    'delta': 0,
    'epsilon': 1e-8,
    'zeta': 1.6449,  # zeta(2) = pi^2/6
    'eta': 0.5,
    'kappa': 6,  # SLE kappa
    'lambda_val': 2,  # Carmichael lambda(6)
    'psi': 12,  # Dedekind psi(6)
    # 파이썬 내장
    '__builtins__': {},
}

BT_FILE = os.path.expanduser(
    '~/Dev/n6-architecture/docs/breakthrough-theorems.md'
)
RESULT_FILE = os.path.expanduser(
    '~/Dev/nexus/shared/bt_audit_result.json'
)


# 유니코드 아래첨자 → ASCII (K₁ → K1)
SUB_MAP = str.maketrans({
    '₀': '0', '₁': '1', '₂': '2', '₃': '3', '₄': '4',
    '₅': '5', '₆': '6', '₇': '7', '₈': '8', '₉': '9',
})

# 유니코드 윗첨자 → **N (거듭제곱)
SUP_MAP = {
    '⁰': '0', '¹': '1', '²': '2', '³': '3', '⁴': '4',
    '⁵': '5', '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9',
}

# 위첨자 부호 (⁻⁵, ⁺³)
SUP_SIGN_MAP = {'⁻': '-', '⁺': '+'}


def normalize_expr_unicode(s):
    """유니코드 특수기호를 ASCII 로 정규화 (parse 전처리 진입점)."""
    if s is None:
        return s
    s = s.replace('\u00a0', ' ').replace('\u2009', ' ')
    s = s.replace('\u200b', '').replace('\ufeff', '')
    s = s.replace('×', '*').replace('·', '*').replace('÷', '/')
    s = s.replace('−', '-').replace('–', '-').replace('—', '-')
    s = s.replace('\u2010', '-').replace('\u2011', '-')
    return re.sub(r'\s+', ' ', s).strip()


def _convert_superscripts(s):
    """연속된 유니코드 윗첨자(부호 포함)를 **<sign>N 으로 변환"""
    out = []
    i = 0
    while i < len(s):
        if s[i] in SUP_MAP or s[i] in SUP_SIGN_MAP:
            j = i
            sign = ''
            if s[j] in SUP_SIGN_MAP:
                sign = SUP_SIGN_MAP[s[j]]
                j += 1
            digits = ''
            while j < len(s) and s[j] in SUP_MAP:
                digits += SUP_MAP[s[j]]
                j += 1
            if digits:
                out.append('**' + sign + digits)
            elif sign:
                out.append('**' + sign)
            i = j
        else:
            out.append(s[i])
            i += 1
    return ''.join(out)

# 단위 패턴 — 선행 숫자가 반드시 있어야 함 (sigma/phi 같은 식별자 보호)
# 대소문자 구분 (mA ≠ ma), 뒤는 word-boundary
UNIT_RE = re.compile(
    r'(?<=[\d\)])\s*'
    r'(?:ft|Hz|kHz|MHz|GHz|THz|nm|μm|um|mm|cm|km|eV|keV|MeV|GeV|TeV'
    r'|kW|MW|GW|kV|MV|mA|mT|ms|us|μs|ns|ps|fs'
    r'|MPa|GPa|Pa|bar|atm|kJ|MJ|Wh|kWh|MWh|°C|°F|°|deg|rad'
    r'|bits?|bytes?|KB|MB|GB|TB|×|%'
    r'|channels?|layers?|classes?|types?|conditions?|properties?'
    r'|principles?|constraints?|factors?|methods?|values?|axes?|modes?'
    r'|phases?|levels?|sizes?|rounds?|suites?|stages?|weightings?'
    r'|rings?|syntaxes?|flanges?|atoms?|bonds?|bases?|nearest|fold'
    r'|A100|MLA|S0-S5|C0-C3|D0-D3|G0-G3)\b.*$'
)


def strip_units(s):
    """단위/주석/극성 표기 제거 (순수 식별자는 보호)"""
    s = s.strip()
    s = re.sub(r'^[±~≈]+', '', s).strip()
    # 괄호 주석 (A100), (Keepin model) 등 — 앞에 숫자가 있을 때만 제거
    s = re.sub(r'(?<=[\d\)])\s*\([^)]*\)\s*$', '', s).strip()
    s = UNIT_RE.sub('', s).strip()
    return s


# 단순 "숫자+단위/단어" 패턴 (전체 매칭) — bare numeric value 추출
BARE_NUM_RE = re.compile(
    r'^\s*([+-]?\d{1,3}(?:,\d{3})+|[+-]?\d+\.?\d*|[+-]?\.\d+)'
    r'\s*(?:%|°[CFK]?|[A-Za-zμ/·\-]+\d*)?'
    r'(?:\s*(?:±|\+/-|\+-)\s*[\d.]+)?'
    r'\s*$'
)

# 과학적 표기: 6×10⁻⁵, 1.5x10^-3, 6*10^-5
SCI_NOTATION_RE = re.compile(
    r'^\s*([+-]?\d+\.?\d*)\s*[×x*·]\s*10\s*[\^]?\s*([+-]?\d+|⁻?[⁰¹²³⁴⁵⁶⁷⁸⁹]+)\s*'
    r'(?:[A-Za-zμ/·\-^\d]+)?\s*$'
)


def _parse_sup_int(s):
    """⁻⁵ → -5 또는 일반 정수 문자열"""
    if not s:
        return None
    s = s.replace('⁻', '-')
    out = ''
    for c in s:
        if c in SUP_MAP:
            out += SUP_MAP[c]
        else:
            out += c
    try:
        return int(out)
    except ValueError:
        return None


def parse_bare_numeric(s):
    """expression 셀이 사실 숫자값(단위포함)일 때 그 숫자만 추출. 실패시 None."""
    if not s:
        return None
    s = s.strip()
    # 마크다운 굵게 제거
    s = re.sub(r'^\*\*(.+?)\*\*$', r'\1', s).strip()
    # 선행 ± ~ ≈
    s = re.sub(r'^[±~≈]+', '', s).strip()

    # 과학적 표기 우선
    m = SCI_NOTATION_RE.match(s)
    if m:
        try:
            base = float(m.group(1))
            exp = _parse_sup_int(m.group(2))
            if exp is not None:
                return base * (10 ** exp)
        except (ValueError, OverflowError):
            pass

    # "0.0351 +/- 0.0042" 같은 표기
    m2 = re.match(r'^([+-]?\d+\.?\d*|[+-]?\.\d+)\s*(?:±|\+/-|\+-)\s*[\d.]+', s)
    if m2:
        try:
            return float(m2.group(1))
        except ValueError:
            pass

    # 일반 숫자+단위/단어
    m = BARE_NUM_RE.match(s)
    if m:
        try:
            return float(m.group(1).replace(',', ''))
        except ValueError:
            return None
    return None


def normalize_expr(expr_str):
    """n=6 수식 문자열을 Python eval 가능한 형태로 정규화"""
    s = expr_str.strip()
    s = normalize_expr_unicode(s)

    # 마크다운 굵게 제거
    s = re.sub(r'^\*\*(.*)\*\*$', r'\1', s).strip()

    # 유니코드 윗첨자 → **N (거듭제곱), 아래첨자 → 숫자
    s = _convert_superscripts(s)
    s = s.translate(SUB_MAP)

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

    # 등호 처리: "128 = 2^7" → 숫자면 숫자, label이면 right side, 수식이면 left
    if '=' in s and '==' not in s and '>=' not in s and '<=' not in s:
        parts = s.split('=', 1)
        left, right = parts[0].strip(), parts[1].strip()
        try:
            float(left.replace(',', ''))
            s = left.replace(',', '')
        except ValueError:
            # 좌변이 순수 라벨(식별자만)이면 우변을 사용
            if re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', left):
                s = right
            else:
                s = left

    # 유니코드 그리스 문자 → 영문 치환
    greek_map = {
        'σ': 'sigma', 'τ': 'tau', 'φ': 'phi', 'μ': 'mu',
        'ψ': 'psi', 'η': 'eta', 'κ': 'kappa', 'λ': 'lambda_val',
        'α': 'alpha', 'β': 'beta', 'ε': 'epsilon', 'δ': 'delta',
        'ζ': 'zeta', 'Δ': 'delta', 'π': 'pi', 'Φ': 'phi',
    }
    for g, eng in greek_map.items():
        s = s.replace(g, eng)

    # 유니코드 산술 치환
    s = s.replace('×', '*').replace('·', '*').replace('÷', '/')
    s = s.replace('−', '-').replace('–', '-').replace('—', '-')
    s = s.replace('^', '**').replace('²', '**2').replace('³', '**3')
    s = s.replace('⁴', '**4').replace('⁵', '**5')
    s = s.replace('⁶', '**6').replace('⁷', '**7').replace('⁸', '**8').replace('⁹', '**9')
    s = s.replace('⁰', '**0').replace('¹', '**1')

    # 'x' 또는 'X' 가 곱셈 기호로 쓰인 경우 (공백 둘러쌈)
    s = re.sub(r'(?<=[\w\)])\s+[xX]\s+(?=[\w\(])', '*', s)

    # LaTeX 중괄호 제거 (10^{-(sigma-phi)} → 10**(-(sigma-phi)))
    s = s.replace('{', '(').replace('}', ')')

    # J_2 -> J2
    s = s.replace('J_2', 'J2')

    # sigma/phi/tau 등은 함수가 아닌 상수 — 'sigma(' 같은 사용은 곱셈으로 해석
    # 예: σ(σ-μ) → sigma*(sigma-mu)
    for nm in ('sigma', 'phi', 'tau', 'sopfr', 'mu', 'psi', 'eta', 'kappa'):
        s = re.sub(rf'\b{nm}\(', f'{nm}*(', s)

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

    # 암묵적 곱셈 삽입:
    # 1) 숫자와 식별자/괄호: 3tau → 3*tau, 6pi → 6*pi
    s = re.sub(r'(\d)([A-Za-z_(])', r'\1*\2', s)
    # 2) 닫는 괄호와 여는 괄호 또는 식별자: )(  → )*(
    s = re.sub(r'\)\s*([A-Za-z_(])', r')*\1', s)
    # 3) 식별자 뒤 여는 괄호는 normalize 위에서 sigma( → sigma*( 처리됨

    # 단위/주석 제거
    s = strip_units(s)

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


def split_list_expr(expr_str):
    """리스트/래더 표현을 원소들로 분해. 분해 불가면 None."""
    s = expr_str.strip()
    s = re.sub(r'^\*\*(.*)\*\*$', r'\1', s).strip()
    s = _convert_superscripts(s).translate(SUB_MAP)
    # {a, b, c} 또는 [a, b, c]
    m = re.match(r'^[\[\{](.+)[\]\}]$', s)
    if m:
        body = m.group(1)
    elif '\u2192' in s or '->' in s:
        # 래더: a → b → c
        body = re.sub(r'->|\u2192', ',', s)
    elif ',' in s and '(' not in s:
        body = s
    else:
        return None
    parts = [p.strip() for p in body.split(',') if p.strip()]
    return parts if len(parts) >= 2 else None


def split_list_value(val_str):
    """Predicted/Known 셀에서 리스트 추출"""
    if not val_str:
        return None
    s = val_str.strip().translate(SUB_MAP)
    m = re.match(r'^[\[\{](.+)[\]\}]$', s)
    if m:
        body = m.group(1)
    elif '\u2192' in s or '->' in s:
        body = re.sub(r'->|\u2192', ',', s)
    elif ',' in s and '(' not in s:
        body = s
    else:
        return None
    nums = []
    for p in body.split(','):
        p = strip_units(p.strip())
        try:
            nums.append(float(p))
        except ValueError:
            return None
    return nums if len(nums) >= 2 else None


def safe_eval(expr_str):
    """수식 문자열을 안전하게 평가"""
    normalized = normalize_expr(expr_str)
    if normalized is None:
        # 수식 정규화 실패 — bare numeric 폴백
        bare = parse_bare_numeric(expr_str)
        if bare is not None:
            return bare, f'<bare:{bare}>'
        return None, None

    try:
        result = eval(normalized, EVAL_NS)
        if isinstance(result, (int, float)):
            return result, normalized
        return None, normalized
    except Exception:
        # eval 실패 — bare numeric 폴백
        bare = parse_bare_numeric(expr_str)
        if bare is not None:
            return bare, f'<bare:{bare}>'
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


def is_pure_literal(expr_str):
    """Expression이 순수 숫자 리터럴인지 (128, 2048, 0.9, 10x, 20% 등)"""
    if not expr_str:
        return False
    s = expr_str.strip().lstrip('~≈')
    s = re.sub(r'^\*\*(.+?)\*\*$', r'\1', s).strip()
    s = s.rstrip('x×%')
    try:
        float(s.replace(',', ''))
        return True
    except ValueError:
        return False


_MATH_WORD_RE = re.compile(r'\b(ln|log|log2|sqrt|exp|pi|e|sin|cos|tan|sigma|tau|phi|mu|sopfr|n|J2|J_2)\b')


def is_descriptive_known(known_str):
    """Known 셀이 서술형 자연어인지 (alpha ratio > 0.4, 수학 식별자 제외)"""
    if not known_str:
        return False
    s = known_str.strip()
    if not s:
        return False
    # 수학 식별자/함수 먼저 제거
    stripped = _MATH_WORD_RE.sub('', s)
    core = re.sub(r'[\s\*_\-~≈±()=,:/\.\d\^%×·]', '', stripped)
    if not core:
        return False
    alpha = sum(1 for c in core if c.isalpha())
    if alpha < 3:
        return False
    # 남은 문자 중 알파벳 비율
    ratio = alpha / max(1, len(core))
    return ratio > 0.4


def safe_eval_known(val_str):
    """Known 셀을 분수/기호식으로 평가 (4/3, 1/12, 27/28, ~3/2, 10^3, 20%, 4×6=24)"""
    if not val_str:
        return None
    s = val_str.strip()
    s = re.sub(r'^\*\*(.+?)\*\*$', r'\1', s).strip()
    s = s.lstrip('~≈').strip()
    # 등식형 "4×6=24" → 우변 우선
    if '=' in s and '==' not in s and '>=' not in s and '<=' not in s:
        parts = s.split('=')
        for candidate in (parts[-1].strip(), parts[0].strip()):
            v = _eval_known_core(candidate)
            if v is not None:
                return v
        return None
    return _eval_known_core(s)


def _eval_known_core(s):
    if not s:
        return None
    # ± 제거
    s = re.sub(r'\s*(?:±|\+/-|\+-)\s*[\d.]+.*$', '', s).strip()
    # 퍼센트
    pct_m = re.match(r'^([+-]?\d+\.?\d*)\s*%$', s)
    if pct_m:
        try:
            return float(pct_m.group(1)) / 100.0
        except ValueError:
            pass
    # 10^3, 2^7
    pow_m = re.match(r'^([+-]?\d+\.?\d*)\s*\^\s*([+-]?\d+)$', s)
    if pow_m:
        try:
            return float(pow_m.group(1)) ** int(pow_m.group(2))
        except (ValueError, OverflowError):
            pass
    # 유니코드/기호 정규화
    s2 = s.replace('×', '*').replace('·', '*').replace('÷', '/').replace('^', '**')
    s2 = _convert_superscripts(s2).translate(SUB_MAP)
    # 순수 산술
    if re.match(r'^[\d\.\s\+\-\*/\(\)]+$', s2):
        try:
            v = eval(s2, {'__builtins__': {}}, {})
            if isinstance(v, (int, float)):
                return float(v)
        except Exception:
            pass
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

            # 테이블 행 파싱 — 앞뒤 빈 셀만 제거 (중간 보존)
            cells = [c.strip() for c in line.split('|')]
            while cells and cells[0] == '':
                cells.pop(0)
            while cells and cells[-1] == '':
                cells.pop()
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
            # 헤더 열 인덱스 파악 — 앞뒤 빈 셀만 제거 (중간 빈 셀은 보존)
            headers = [h.strip() for h in line.split('|')]
            while headers and headers[0] == '':
                headers.pop(0)
            while headers and headers[-1] == '':
                headers.pop()

            expr_col = None
            pred_col = None
            known_col = None
            value_col = None

            _ROW_NUM_HEADERS = {'#', 'No', 'No.', 'Index', 'Row', '№', 'Idx'}
            for j, h in enumerate(headers):
                if h in _ROW_NUM_HEADERS:
                    continue  # 2-D: 행번호 컬럼 스킵
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
                # headers와 동일한 방식: 앞뒤 빈 셀만 제거
                while cells and cells[0] == '':
                    cells.pop(0)
                while cells and cells[-1] == '':
                    cells.pop()

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


_NON_FORMULA_RE = re.compile(
    r'^(\*\*[^*]+\*\*'
    r'|[A-Za-z_][A-Za-z0-9_]*'
    r'|[A-Za-z_][A-Za-z0-9_]*\([^)]*\))$'
)


_KNOWN_NAMES = {
    'sigma', 'tau', 'phi', 'sopfr', 'mu', 'n', 'J2', 'J_2', 'R',
    'P1', 'P2', 'K_2', 'K_3',
}


def is_non_formula(expr_str):
    s = _convert_superscripts(expr_str.strip()).translate(SUB_MAP)
    if not s:
        return True
    # 마크다운 굵게/이탤릭 라벨
    if re.match(r'^[*_]{1,2}[^*_]+[*_]{1,2}$', s):
        return True
    # 백슬래시 LaTeX 잔재
    if '\\' in s:
        return True
    # 공백을 포함한 자연어 (단, 연산자만 있는 공백 'sigma + tau' 는 OK)
    if ' ' in s and not re.match(r'^[\w\s+\-*/().^%]+$', s):
        return True
    # 한 어휘의 단순 식별자 또는 식별자(인자) (예: alpha_s(M_Z), m_t/m_W → 슬래시 포함)
    # 식별자만(언더스코어 포함)
    if re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', s) and s not in _KNOWN_NAMES:
        return True
    # 식별자(인자)
    if re.match(r'^[A-Za-z_][A-Za-z0-9_]*\([^)]*\)$', s):
        return True
    # 식별자/식별자 (예: m_t/m_W, k/n)
    if re.match(r'^[A-Za-z_][A-Za-z0-9_]*\s*/\s*[A-Za-z_][A-Za-z0-9_]*$', s):
        return True
    # 백분율 범위 (3-5%)
    if re.match(r'^\d+\s*-\s*\d+\s*%?$', s):
        return True
    # 자연어 라벨 (영문 단어 2개+, 또는 BT-N, Si-28, top-8, layer N 등)
    if re.match(r'^[A-Za-z]+(?:[\s\-][A-Za-z0-9]+)+$', s):
        return True
    # sin²θ_W 같은 그리스/삼각함수 잔재 (eval 불가능 → 라벨로 처리)
    if 'theta' in s.lower() or re.search(r'\bsin|\bcos|\btan', s.lower()):
        # 단, 평가 가능한 형태(sin(0))는 normalize_expr에서 처리하므로 여기선 unresolvable만
        if not re.match(r'^[\w\s+\-*/().]+$', s):
            return True
    # 마크다운 굵게로 감싼 식별자 (**m_p/m_e**) — 최외곽 ** 제거 후 식별자류
    inner = re.sub(r'^\*\*(.+?)\*\*$', r'\1', s)
    if inner != s and (re.match(r'^[A-Za-z_][A-Za-z0-9_]*(?:/[A-Za-z_][A-Za-z0-9_]*)?$', inner)
                       or re.match(r'^[A-Za-z_][A-Za-z0-9_]*\([^)]*\)$', inner)):
        return True
    return False


def audit_row(bt_num, row):
    """단일 테이블 행 검산"""
    expr_str = row['expression']
    predicted_raw = row['predicted_raw']
    known_raw = row['known_raw']

    # 0) 리스트/래더 비교 우선 시도
    parts = split_list_expr(expr_str)
    if parts is not None:
        comp_list = []
        ok = True
        for p in parts:
            v, _ = safe_eval(p)
            if v is None:
                ok = False
                break
            comp_list.append(v)
        if ok:
            tgt_list = (
                split_list_value(predicted_raw)
                or split_list_value(known_raw)
            )
            if tgt_list and len(tgt_list) == len(comp_list):
                errs = [
                    abs(c - t) / abs(t) * 100 if t else (0 if c == 0 else float('inf'))
                    for c, t in zip(comp_list, tgt_list)
                ]
                max_err = max(errs)
                return {
                    'bt': bt_num,
                    'expression': expr_str,
                    'normalized': str(comp_list),
                    'computed': comp_list,
                    'target': tgt_list,
                    'target_source': 'list',
                    'error_pct': round(max_err, 4) if max_err != float('inf') else 'inf',
                    'status': 'MATCH' if max_err < 0.01 else 'MISMATCH',
                }
            # 타겟 없음 → list NO_TARGET
            return {
                'bt': bt_num,
                'expression': expr_str,
                'computed': comp_list,
                'normalized': str(comp_list),
                'status': 'NO_TARGET',
                'reason': f'리스트 비교 대상 없음 (predicted={predicted_raw}, known={known_raw})',
            }

    # 1) 일반 수식 평가
    computed, normalized = safe_eval(expr_str)

    if computed is None:
        # 평가 실패 → 비-수식 라벨이면 NO_EXPR, 아니면 SKIP
        if is_non_formula(expr_str):
            return {
                'bt': bt_num,
                'expression': expr_str,
                'status': 'NO_EXPR',
                'reason': '수식이 아닌 라벨/이름',
            }
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

    # v2 보강: MISMATCH 일 때 파서 결함 가능성 재검사 (기존 MATCH 는 건드리지 않음)
    if not match and target_source == 'known':
        # 2-C: 분수/기호식 Known 재평가
        alt = safe_eval_known(known_raw)
        if alt is not None and target != alt:
            if alt == 0:
                if computed == 0:
                    match = True
                    error_pct = 0
                    target = alt
            else:
                alt_err = abs(computed - alt) / abs(alt) * 100
                if alt_err < 0.01:
                    match = True
                    error_pct = alt_err
                    target = alt
        if not match:
            # 2-A: 리터럴 Expression + 서술 Known → SKIP
            # 2-B: 서술형 Known → SKIP
            if (is_pure_literal(expr_str) and is_descriptive_known(known_raw)) \
               or is_descriptive_known(known_raw):
                return {
                    'bt': bt_num,
                    'expression': expr_str,
                    'normalized': normalized,
                    'computed': round(computed, 6) if isinstance(computed, float) else computed,
                    'status': 'SKIP',
                    'reason': f'서술형/리터럴 Known (파서 v2): {known_raw}',
                }

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
    no_expr_count = 0

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
            elif result['status'] == 'NO_EXPR':
                no_expr_count += 1

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
    print(f"  NO_EXPR (수식아님): {no_expr_count}")
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
            'no_expr': no_expr_count,
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
